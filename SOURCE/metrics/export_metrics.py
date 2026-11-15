"""Recompute Phase 5 metrics from pinned real evidence; no Docker mutation."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

from evidence import (CASES,EVIDENCE_REF,EXECUTION_REF,EvidenceError,ROOT,artifact_check,
                      close_number,full_snapshot,load,load_case,membership,one,ordered,pinned,safe_path,
                      seconds,sha,source_pin,timeline,utc)

FIELDS=['run_id','scenario','trial_status','evidence_validation','source_fingerprint_status',
        'fault_at_utc','ready_at_utc','rto_status','observed_rto_seconds','observed_mttd_seconds',
        'backup_verified_at_utc','backup_age_since_verified_seconds','dump_started_at_utc','dump_finished_at_utc',
        'sql_import_seconds','snapshot_id','manifest_sha256',
        'restored_snapshot_rows','write_probe_rows','acknowledged_requests','recovered_requests',
        'unrecovered_acknowledged_requests','duplicate_requests','uncertain_requests',
        'rpo_status','recovered_commit_lag_lower_seconds','recovered_commit_lag_upper_seconds',
        'exact_rpo_seconds','rto_target_seconds','rpo_target_seconds','rto_target_result','rpo_target_result',
        'historical_data_integrity','fresh_artifact_integrity','candidate_integrity','negative_test_result','fresh_restic_integrity',
        'fresh_retained_db_integrity','fresh_verification_at_utc','membership_provenance',
        'return_source_status','clock_basis','notes']


def base_row(bundle):
    r=bundle['result']
    row={k:None for k in FIELDS}
    row.update(run_id=r['run_id'],scenario=r['scenario'],trial_status=r['status'],
               evidence_validation='PASS',source_fingerprint_status=source_pin(bundle),
               rto_status='NOT APPLICABLE',rpo_status='NOT APPLICABLE',
               rto_target_result='NOT TESTED',rpo_target_result='NOT TESTED',
               historical_data_integrity=r.get('integrity',r.get('data_unchanged','NOT TESTED')),
               fresh_artifact_integrity='NOT TESTED',fresh_restic_integrity='NOT TESTED',
               fresh_retained_db_integrity='NOT TESTED',return_source_status=r.get('return_source_status','NOT APPLICABLE'),
               clock_basis='same observer monotonic_ns; UTC retained for cross-reference',notes='')
    return row


def analyze(bundle,artifact_root=None,fresh=None):
    events=timeline(bundle);r=bundle['result'];row=base_row(bundle)
    integrity=artifact_check(bundle,artifact_root)
    row['fresh_artifact_integrity']=integrity['status']
    if r['status'] not in ['PASS','FAILED','ABORTED']:raise EvidenceError('Unsupported trial status')
    if r['status']!='PASS':
        fault=one(events,'FAULT_REQUESTED',False)
        if fault:row.update(fault_at_utc=fault['utc'],rto_status='NOT TESTED (censored)',rpo_status='NOT TESTED')
        row['notes']='Failed attempt retained; no successful recovery duration assigned. '+r.get('error','')
        return row,integrity
    name=bundle['name']
    if name=='corrupt':
        rejected=one(events,'CORRUPT_INPUT_REJECTED')
        if r.get('rejection')!='PASS' or r.get('import_attempted') is not False or rejected.get('import_attempted') is not False:
            raise EvidenceError('Invalid corruption rejection evidence')
        if any(e['event'] in ['FAULT_REQUESTED','IMPORT_STARTED'] for e in events):raise EvidenceError('Integrity-only test unexpectedly caused outage/import')
        row.update(snapshot_id=one(events,'ARTIFACT_VERIFIED')['snapshot_id'],negative_test_result='PASS',
                   candidate_integrity=integrity.get('candidate_integrity','NOT TESTED'),
                   notes='Negative input test passed; candidate integrity FAIL expected, no outage/import and no RTO/RPO.')
        return row,integrity
    if name not in ['main','web-control']:raise EvidenceError('Unexpected successful metrics case')
    start,detected,ready,ended=ordered(events,['FAULT_REQUESTED','FAULT_DETECTED','SERVICE_VERIFIED','TRIAL_ENDED'])
    if detected['http_status']==200:raise EvidenceError('Outage was not observed')
    row.update(fault_at_utc=start['utc'],ready_at_utc=ready['utc'],rto_status='MEASURED',
               observed_rto_seconds=seconds(ready['monotonic_ns'],start['monotonic_ns']),
               observed_mttd_seconds=seconds(detected['monotonic_ns'],start['monotonic_ns']))
    close_number(r['observed_rto_seconds'],row['observed_rto_seconds'])
    stable=[e for e in events if e['event']=='STABILITY_PROBE']
    if len(stable)!=3 or [e.get('sample') for e in stable]!=[1,2,3]:raise EvidenceError('Missing stable-health samples')
    for e in stable:
        if e.get('http_status')!=200 or e['monotonic_ns']>ready['monotonic_ns'] or e['monotonic_ns']<detected['monotonic_ns']:
            raise EvidenceError('Invalid stable-health gate')
        if e.get('health',{}).get('orders_count')!=ready['row_count']:raise EvidenceError('Stable-health data count mismatch')
    returned=one(events,'POST_TRIAL_RETURN_SOURCE_STARTED',False)
    if returned and returned['monotonic_ns']<ended['monotonic_ns']:raise EvidenceError('Return-source occurred inside trial')
    if name=='web-control':
        if r.get('data_unchanged')!='PASS' or ready['row_count']!=r['source_before']['orders_count']:raise EvidenceError('Web-control data mismatch')
        row['notes']='Web-only control; source DB retained; not a backup restore and no RPO assigned.'
        return row,integrity
    stages=ordered(events,['FAULT_REQUESTED','FAULT_DETECTED','ARTIFACT_VERIFIED','TARGET_READY',
                           'IMPORT_STARTED','IMPORT_FINISHED','DATA_VERIFIED','URL_READ_VERIFIED',
                           'RESTART_VERIFIED','TARGET_CLEANUP','SERVICE_VERIFIED','REQUEST_COMPARISON_FINISHED','TRIAL_ENDED'])
    receipt=r['backup'];baseline=receipt['dump_metadata']['business_baseline']
    meta=receipt['dump_metadata']
    if utc(meta['dump_finished_at_utc'])<utc(meta['dump_started_at_utc']):raise EvidenceError('Dump capture clock is reversed')
    full_id=receipt['snapshot_id']
    full_snapshot(full_id)
    if bundle['inputs']['docs/evidence/phase4/main-manifest.json']['sha256']!=receipt['manifest_sha256']:
        raise EvidenceError('Committed manifest differs from selected receipt')
    snapshot=one(events,'SNAPSHOT_VERIFIED');data=one(events,'DATA_VERIFIED');cleanup=one(events,'TARGET_CLEANUP')
    if snapshot['monotonic_ns']>start['monotonic_ns'] or snapshot['snapshot_id']!=full_id or snapshot['manifest_sha256']!=receipt['manifest_sha256']:
        raise EvidenceError('Selected snapshot/digest/timing mismatch')
    if baseline['row_count']!=r['restored_snapshot_rows'] or data['row_count']!=baseline['row_count'] or data['rows_sha256']!=baseline['rows_sha256'] or data['schema_sha256']!=baseline['schema_sha256']:
        raise EvidenceError('Recorded DB integrity differs from source baseline')
    if cleanup['status']!='PASS' or any(r.get(k)!='PASS' for k in ['integrity','schema','grants','api_read_write','persistence']):raise EvidenceError('Recovery gate was not fully satisfied')
    if stages[3].get('seed_tables')!=0 or ready['row_count']!=baseline['row_count']+1:raise EvidenceError('Seed/probe data count mismatch')
    if stable[0]['monotonic_ns']<one(events,'RESTART_VERIFIED')['monotonic_ns']:raise EvidenceError('Stable gate precedes restart')
    probe=[e for e in events if e['event']=='REQUEST_ACKNOWLEDGED' and e.get('request_id')=='recovery-write-probe']
    if len(probe)!=1 or probe[0]['row']!=r['write_probe'] or not one(events,'URL_READ_VERIFIED')['monotonic_ns']<=probe[0]['monotonic_ns']<=one(events,'RESTART_VERIFIED')['monotonic_ns']:
        raise EvidenceError('Write probe violated read-before-write order')
    comparison,lower,upper,provenance=membership(bundle,start['monotonic_ns'],fresh)
    if fresh:
        if fresh.get('status')!='PASS' or fresh.get('business_queries_read_only') is not True or fresh.get('not_new_rto_trial') is not True:
            raise EvidenceError('Fresh verification is not an accepted read-only check')
        if fresh.get('return_source_status')!='PASS' or fresh.get('source_unchanged') is not True:
            raise EvidenceError('Fresh verification did not return the unchanged source to service')
        if fresh['target_volume']!=r['target_volume'] or fresh['base_rows_sha256']!=baseline['rows_sha256'] or fresh['schema_sha256']!=baseline['schema_sha256'] or fresh['total_rows']!=ready['row_count']:
            raise EvidenceError('Retained target verification mismatch')
        if fresh['input_result_sha256']!=sha(ROOT/'docs/evidence/phase4/main-result.json'):raise EvidenceError('Fresh check is bound to another result')
        row.update(fresh_restic_integrity=fresh['restic_check'],fresh_retained_db_integrity='PASS',fresh_verification_at_utc=fresh['verified_at_utc'])
    row.update(backup_verified_at_utc=snapshot['utc'],backup_age_since_verified_seconds=seconds(start['monotonic_ns'],snapshot['monotonic_ns']),
               dump_started_at_utc=meta['dump_started_at_utc'],dump_finished_at_utc=meta['dump_finished_at_utc'],
               sql_import_seconds=seconds(stages[5]['monotonic_ns'],stages[4]['monotonic_ns']),
               snapshot_id=full_id,manifest_sha256=receipt['manifest_sha256'],restored_snapshot_rows=baseline['row_count'],write_probe_rows=1,
               acknowledged_requests=len(bundle['acks']),recovered_requests=len(comparison['recovered_requests']),
               unrecovered_acknowledged_requests=len(comparison['unrecovered_acknowledged']),duplicate_requests=len(comparison['duplicates']),uncertain_requests=0,
               rpo_status='BOUNDED OBSERVATION' if lower is not None else 'NOT TESTED',
               recovered_commit_lag_lower_seconds=lower,recovered_commit_lag_upper_seconds=upper,membership_provenance=provenance,
               notes='One scripted Linux/VFS sample; images cached, stopped source containers released; send/ACK bounds are not exact commit timestamps or RPO target attainment.')
    return row,integrity


def csv_cell(value):
    if value is None:return ''
    value=str(value)
    return "'"+value if value.lstrip(' \t\r\n').startswith(('=','+','-','@')) or value.startswith(('\t','\r','\n')) else value


def export(output,ref,artifact_root=None,verification=None):
    fresh=load(verification) if verification else None
    rows=[];checks={};inputs={}
    for name in CASES:
        bundle=load_case(name,ref);inputs.update(bundle['inputs'])
        row,check=analyze(bundle,artifact_root,fresh if name=='main' else None)
        rows.append(row);checks[name]=check
    output=safe_path(output);output.mkdir(parents=True) # never overwrite a prior export
    with (output/'metrics.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n');writer.writeheader()
        writer.writerows({k:csv_cell(row[k]) for k in FIELDS} for row in rows)
    summary={'schema_version':1,'evidence_ref':ref,'execution_ref':EXECUTION_REF,'samples':rows,
             'main_trial_count':sum(r['scenario']=='drill' and r['trial_status']=='PASS' for r in rows),
             'rto_rpo_targets':'NOT TESTED; user has not selected targets',
             'exact_rpo':'NOT TESTED; only client send/ACK bounds available',
             'windows_10':'NOT TESTED','independent_storage':'NOT TESTED','three_trial_statistics':'NOT TESTED'}
    (output/'metrics.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'integrity.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    processor_files=list(Path(__file__).parent.glob('*.py'))+[ROOT/'SOURCE/recovery/common.py',ROOT/'SOURCE/recovery/controller.py',ROOT/'SOURCE/backup/backup.py']
    manifest={'schema_version':1,'created_at_utc':datetime.now(timezone.utc).isoformat(),'inputs':inputs,
              'verification_sha256':sha(verification) if verification else None,
              'processor_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in processor_files},
              'outputs':{p.name:sha(p) for p in output.iterdir() if p.is_file()}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence-ref',default=EVIDENCE_REF);p.add_argument('--artifact-root',type=Path)
    p.add_argument('--verification',type=Path);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    try:
        answer=export(a.output_dir,a.evidence_ref,a.artifact_root,a.verification)
        print(json.dumps({'output':str(a.output_dir),'main_trial_count':answer['main_trial_count'],'status':'PASS'},indent=2))
    except (ValueError,OSError,KeyError,TypeError) as e:
        p.exit(1,'Evidence/export failed: '+str(e)+'\n')
