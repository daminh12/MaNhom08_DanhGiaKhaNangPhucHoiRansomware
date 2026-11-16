"""Read one newly sealed controller run, without Docker or historical assumptions."""
import csv
import hashlib
import json
from pathlib import Path
import re

from evidence import (EvidenceError, artifact_check, close_number, decode, full_snapshot,
                      git_bytes, membership, one, ordered, safe_path, seconds, sha, timeline, utc)
from protocol import AUTOMATED, GUIDED, CODE_FILES, EVIDENCE_FILES
from export_metrics import FIELDS, csv_cell

EXTRA_FIELDS = ['measurement_version', 'host_os', 'os_release', 'os_version',
                'execution_commit', 'observer_id', 'operator_confirmation',
                'containment_status', 'containment_seconds']


def load_trial(directory):
    directory=safe_path(Path(directory).absolute()).resolve()
    seal_path=safe_path(directory/'evidence-manifest.json')
    seal_raw=seal_path.read_bytes();seal=decode(seal_raw)
    if not isinstance(seal,dict) or seal.get('schema_version')!=1 or not isinstance(seal.get('files'),dict):
        raise EvidenceError('Missing/unsupported evidence manifest; incomplete runs cannot be certified')
    if not {'result.json','events.jsonl'}<=set(seal['files']) or not set(seal['files'])<=set(EVIDENCE_FILES):
        raise EvidenceError('Evidence manifest has missing or unsafe file names')
    raw={};inputs={}
    for name,record in seal['files'].items():
        path=safe_path(directory/name);data=path.read_bytes()
        digest=hashlib.sha256(data).hexdigest()
        if record!={'sha256':digest,'size_bytes':len(data)}:
            raise EvidenceError('Evidence hash/size mismatch: '+name)
        raw[name]=data;inputs[name]=record
    inputs['evidence-manifest.json']={'sha256':hashlib.sha256(seal_raw).hexdigest(),'size_bytes':len(seal_raw)}
    result=decode(raw['result.json'])
    events=[decode(line) for line in raw['events.jsonl'].splitlines()]
    if not isinstance(result,dict) or result.get('schema_version')!=2 or result.get('run_id')!=seal.get('run_id') or directory.name!=result.get('run_id'):
        raise EvidenceError('Result/seal identity or schema mismatch')
    names={'drill':'main','web-outage':'web-control','reject-corrupt':'corrupt',
           'restore':'restore','backup':'backup','preflight':'preflight'}
    if result.get('scenario') not in names:raise EvidenceError('Unsupported trial scenario')
    bundle={'name':names[result['scenario']],'scenario':result['scenario'],'result':result,
            'events':events,'inputs':inputs,'directory':directory}
    timeline(bundle)
    prepared=events[0];version=result.get('measurement_version')
    if version not in (AUTOMATED,GUIDED) or prepared.get('measurement_version')!=version:
        raise EvidenceError('Unsupported/inconsistent measurement version')
    if version==GUIDED and result['scenario']!='drill':raise EvidenceError('Guided protocol only supports drill')
    runtime=result.get('runtime')
    if not isinstance(runtime,dict) or prepared.get('runtime')!=runtime or any(
            not isinstance(runtime.get(k),str) or not runtime[k] for k in ['host_os','os_release','os_version','python']):
        raise EvidenceError('Runtime metadata missing or inconsistent')
    if re.fullmatch('[a-f0-9]{32}',prepared.get('observer_id','')) is None:
        raise EvidenceError('Missing observer session identity')
    hashes=prepared.get('working_source_sha256')
    if not isinstance(hashes,dict) or set(hashes)!=set(CODE_FILES):
        raise EvidenceError('Incomplete execution fingerprint')
    for name,digest in hashes.items():
        if hashlib.sha256(git_bytes(prepared.get('commit',''),name)).hexdigest()!=digest:
            raise EvidenceError('Execution source differs from recorded Git commit: '+name+'; commit source before rehearsal')
    if 'acknowledgements.json' in raw:bundle['acks']=decode(raw['acknowledgements.json'])
    if result.get('status')=='PASS' and bundle['name'] in ('main','restore','corrupt'):
        required={'backup-receipt.json','extracted/manifest.json','extracted/payload/metadata.json','extracted/verified.json'}
        if bundle['name']!='corrupt':required.add('observed-baseline.json')
        if bundle['name']=='main':required.add('acknowledgements.json')
        if not required<=set(raw):raise EvidenceError('Successful recovery is missing required evidence files')
        receipt=result.get('backup')
        if not isinstance(receipt,dict) or decode(raw['backup-receipt.json'])!=receipt or receipt.get('status')!='PASS':
            raise EvidenceError('Selected receipt differs from result')
        full_snapshot(receipt['snapshot_id'])
        if inputs['extracted/manifest.json']['sha256']!=receipt['manifest_sha256']:
            raise EvidenceError('Selected manifest digest mismatch')
        manifest=decode(raw['extracted/manifest.json'])
        # Reuse the existing Phase 2 manifest contract, including exact paths.
        import importlib.util
        from evidence import ROOT
        spec=importlib.util.spec_from_file_location('trial_backup_verifier',ROOT/'SOURCE/backup/backup.py')
        verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
        verifier.validate_manifest(manifest)
        entries={entry['path']:entry for entry in manifest['files']}
        metadata=decode(raw['extracted/payload/metadata.json'])
        if not isinstance(metadata,dict) or metadata!=receipt['dump_metadata'] or metadata.get('baseline_sql_sha256')!=entries['database.sql']['sha256']:
            raise EvidenceError('Baseline metadata is not bound to selected SQL')
        meta_bytes=raw['extracted/payload/metadata.json']
        if entries['metadata.json']['sha256']!=hashlib.sha256(meta_bytes).hexdigest() or entries['metadata.json']['size_bytes']!=len(meta_bytes):
            raise EvidenceError('Metadata is not bound to the selected manifest')
        verified=decode(raw['extracted/verified.json'])
        if verified!={'snapshot_id':receipt['snapshot_id'],'manifest_sha256':receipt['manifest_sha256'],'status':'PASS'}:
            raise EvidenceError('Archive verification disagrees with selected receipt')
        if one(events,'ARTIFACT_VERIFIED')['snapshot_id']!=receipt['snapshot_id']:
            raise EvidenceError('Archive event selected a different snapshot')
        if bundle['name']!='corrupt' and decode(raw['observed-baseline.json'])!=metadata['business_baseline']:
            raise EvidenceError('Full observed baseline differs from selected backup')
    return bundle


def confirmations(events):
    confirmed=[e for e in events if e['event']=='OPERATOR_CONFIRMED']
    prompts=[e for e in events if e['event']=='OPERATOR_PROMPT']
    contract=[('INJECT','Đa Minh'),('RECOVER','Minh Quân'),('WEB_OK','Minh Quân')]
    for values in (confirmed,prompts):
        if [(e.get('action'),e.get('operator')) for e in values]!=contract:
            raise EvidenceError('Guided run lacks the three operator confirmations')
    if any(e['event']=='OPERATOR_CONFIRMATION_REJECTED' for e in events):
        raise EvidenceError('Rejected operator input cannot be a successful guided run')
    for prompt,confirmation in zip(prompts,confirmed):
        if prompt['monotonic_ns']>confirmation['monotonic_ns']:raise EvidenceError('Confirmation precedes prompt')
    fault=one(events,'FAULT_REQUESTED')['monotonic_ns'];detected=one(events,'FAULT_DETECTED')['monotonic_ns']
    archive=one(events,'ARTIFACT_VERIFIED')['monotonic_ns'];compared=one(events,'REQUEST_COMPARISON_FINISHED')['monotonic_ns']
    final=one(events,'FINAL_DATA_VERIFIED')['monotonic_ns'];ready=one(events,'SERVICE_VERIFIED')['monotonic_ns']
    if not (confirmed[0]['monotonic_ns']<=fault<=detected<=prompts[1]['monotonic_ns']<=confirmed[1]['monotonic_ns']<=archive<=compared
            <=prompts[2]['monotonic_ns']<=confirmed[2]['monotonic_ns']<=final<=ready):
        raise EvidenceError('Guided handover/URL confirmation order is invalid')
    return final


def analyze_trial(bundle):
    r=bundle['result'];events=bundle['events'];prepared=events[0];name=bundle['name']
    row={key:None for key in FIELDS+EXTRA_FIELDS}
    sent={e.get('request_id') for e in events if e['event']=='REQUEST_SENT'}
    acknowledged={e.get('request_id') for e in events if e['event']=='REQUEST_ACKNOWLEDGED'}
    uncertain={e.get('request_id') for e in events if e['event']=='REQUEST_UNCERTAIN'}
    if any(not isinstance(x,str) or not x for x in sent|acknowledged|uncertain):
        raise EvidenceError('Request journal is missing request identity')
    row.update(run_id=r['run_id'],scenario=r['scenario'],trial_status=r['status'],evidence_validation='PASS',
               source_fingerprint_status='PASS',measurement_version=r['measurement_version'],
               **{key:r['runtime'][key] for key in ['host_os','os_release','os_version']},
               execution_commit=prepared['commit'],observer_id=prepared['observer_id'],
               rto_status='NOT APPLICABLE',rpo_status='NOT APPLICABLE',
               rto_target_result='NOT TESTED',rpo_target_result='NOT TESTED',
               historical_data_integrity=r.get('integrity',r.get('data_unchanged','NOT TESTED')),
               fresh_artifact_integrity='NOT TESTED',fresh_restic_integrity='NOT TESTED',fresh_retained_db_integrity='NOT TESTED',
               return_source_status=r.get('return_source_status','NOT APPLICABLE'),
               operator_confirmation='NOT APPLICABLE',containment_status='NOT APPLICABLE; no separately defined containment action',
               clock_basis='same observer monotonic_ns; UTC retained for cross-reference',
               uncertain_requests=len(uncertain|(sent-acknowledged)),
               notes='New run; recorded runtime and source pin. Local hashes are not signatures; no independent storage/SLA claim.')
    if r['status'] not in ('PASS','FAILED','ABORTED'):raise EvidenceError('Unsupported trial status')
    ended=one(events,'TRIAL_ENDED');returned=one(events,'POST_TRIAL_RETURN_SOURCE_STARTED',False)
    if returned and returned['monotonic_ns']<ended['monotonic_ns']:raise EvidenceError('Return-source occurred inside trial')
    if r.get('return_source_requested') and r.get('source_touched') and (not returned or r.get('return_source_status') not in ('PASS','FAILED')):
        raise EvidenceError('Missing requested return-source outcome')
    if r.get('return_source_status')=='FAILED':one(events,'POST_TRIAL_RETURN_SOURCE_FAILED')
    if r.get('return_source_status')=='PASS':
        finished=one(events,'POST_TRIAL_RETURN_SOURCE_FINISHED')
        if not returned or finished['monotonic_ns']<returned['monotonic_ns'] or finished.get('health')!=r.get('source_after_return'):
            raise EvidenceError('Return-source success lacks matching health evidence')
    integrity={'status':'NOT TESTED','reason':'No fresh artifact/DB/Restic check performed by default'}
    if r['status']!='PASS':
        fault=one(events,'FAULT_REQUESTED',False)
        if fault:row.update(fault_at_utc=fault['utc'],rto_status='NOT TESTED (censored)',rpo_status='NOT TESTED')
        row['notes']+=' Failed/aborted attempt retained: '+r.get('error','')
        return row,integrity
    if row['uncertain_requests']:raise EvidenceError('Uncertain write cannot be a successful measured profile')
    if name in ('preflight','backup'):
        if name=='preflight':
            if r.get('preflight',{}).get('status')!='PASS':raise EvidenceError('Preflight result missing')
            one(events,'PREFLIGHT_PASSED')
        else:
            selected=one(events,'SNAPSHOT_VERIFIED');full_snapshot(selected['snapshot_id'])
            if r['backup']['status']!='PASS' or selected['snapshot_id']!=r['backup']['snapshot_id']:
                raise EvidenceError('Backup selection mismatch')
            row.update(snapshot_id=selected['snapshot_id'],manifest_sha256=selected['manifest_sha256'])
        return row,integrity
    if name in ('main','restore','corrupt'):
        # SQL stays private/optional on a review clone. Partial payloads fail closed.
        payload=bundle['directory']/'extracted/payload'
        if (payload/'database.sql').exists():
            integrity=artifact_check(bundle,bundle['directory'].parent)
            row['fresh_artifact_integrity']=integrity['status']
        row.update(snapshot_id=r['backup']['snapshot_id'],manifest_sha256=r['backup']['manifest_sha256'])
    if name=='corrupt':
        rejection=one(events,'CORRUPT_INPUT_REJECTED')
        if r.get('rejection')!='PASS' or r.get('import_attempted') is not False or rejection.get('import_attempted') is not False:
            raise EvidenceError('Invalid corruption rejection')
        if any(e['event'] in ('FAULT_REQUESTED','IMPORT_STARTED') for e in events):raise EvidenceError('Corrupt check caused outage/import')
        row.update(negative_test_result='PASS',candidate_integrity=integrity.get('candidate_integrity','NOT TESTED'))
        return row,integrity
    ready=one(events,'SERVICE_VERIFIED')
    if ready['monotonic_ns']>ended['monotonic_ns']:raise EvidenceError('Ready after trial end')
    if name in ('main','web-control'):
        start,detected,ready,ended=ordered(events,['FAULT_REQUESTED','FAULT_DETECTED','SERVICE_VERIFIED','TRIAL_ENDED'])
        if detected['http_status']==200:raise EvidenceError('Outage not observed')
        row.update(fault_at_utc=start['utc'],ready_at_utc=ready['utc'],rto_status='MEASURED',
                   observed_rto_seconds=seconds(ready['monotonic_ns'],start['monotonic_ns']),
                   observed_mttd_seconds=seconds(detected['monotonic_ns'],start['monotonic_ns']))
        close_number(r['observed_rto_seconds'],row['observed_rto_seconds'])
    elif one(events,'FAULT_REQUESTED',False):raise EvidenceError('Phase 3 restore unexpectedly declares an outage trial')
    stable=[e for e in events if e['event']=='STABILITY_PROBE']
    if len(stable)!=3 or [e.get('sample') for e in stable]!=[1,2,3]:raise EvidenceError('Missing stable health samples')
    for i,e in enumerate(stable):
        if e.get('http_status')!=200 or e.get('health',{}).get('orders_count')!=ready['row_count'] or e['monotonic_ns']>ready['monotonic_ns']:
            raise EvidenceError('Invalid stable health gate')
        if i and e['monotonic_ns']-stable[i-1]['monotonic_ns']<1_000_000_000:raise EvidenceError('Stable probes too close')
    if name=='web-control':
        if stable[0]['monotonic_ns']<detected['monotonic_ns'] or r.get('data_unchanged')!='PASS' or ready['row_count']!=r['source_before']['orders_count']:
            raise EvidenceError('Web control data/stability mismatch')
        return row,integrity
    stages=['ARTIFACT_VERIFIED','TARGET_READY','IMPORT_STARTED','IMPORT_FINISHED','DATA_VERIFIED',
            'URL_READ_VERIFIED','RESTART_VERIFIED','TARGET_CLEANUP']
    if name=='main':
        stages=['FAULT_REQUESTED','FAULT_DETECTED']+stages
        stages+=['REQUEST_COMPARISON_FINISHED','FINAL_DATA_VERIFIED','SERVICE_VERIFIED'] if r['measurement_version']==GUIDED else ['SERVICE_VERIFIED','REQUEST_COMPARISON_FINISHED']
    else:stages+=['SERVICE_VERIFIED']
    ordered(events,stages+['TRIAL_ENDED'])
    receipt=r['backup'];meta=receipt['dump_metadata'];baseline=meta['business_baseline']
    data=one(events,'DATA_VERIFIED');target=one(events,'TARGET_READY')
    project='group08-restore-'+r['run_id'];volume=project+'_restore_data'
    if r.get('target_project')!=project or r.get('target_volume')!=volume or target.get('volume')!=volume or r.get('source_volume')!='group08-lab_db_data':
        raise EvidenceError('Target/source volume ownership mismatch')
    read_url=one(events,'URL_READ_VERIFIED').get('url')
    if ready.get('url')!=read_url or (name=='main' and read_url!=r.get('source_url')):
        raise EvidenceError('Restored serving URL mismatch')
    if baseline['row_count']!=r['restored_snapshot_rows'] or any(data[k]!=baseline[k] for k in ('row_count','rows_sha256','schema_sha256')):
        raise EvidenceError('Full data/schema baseline mismatch')
    if target.get('seed_tables')!=0 or ready['row_count']!=baseline['row_count']+1:
        raise EvidenceError('Seed/probe counts invalid')
    if any(r.get(k)!='PASS' for k in ('integrity','schema','grants','api_read_write','persistence')) or one(events,'TARGET_CLEANUP').get('status')!='PASS':
        raise EvidenceError('Incomplete recovery gates')
    if stable[0]['monotonic_ns']<one(events,'TARGET_CLEANUP')['monotonic_ns']:raise EvidenceError('Stable gate before cleanup')
    probe=[e for e in events if e['event']=='REQUEST_ACKNOWLEDGED' and e.get('request_id')=='recovery-write-probe']
    if len(probe)!=1 or probe[0]['row']!=r['write_probe'] or not one(events,'URL_READ_VERIFIED')['monotonic_ns']<=probe[0]['monotonic_ns']<=one(events,'RESTART_VERIFIED')['monotonic_ns']:
        raise EvidenceError('Invalid read-before-write probe')
    if utc(meta['dump_finished_at_utc'])<utc(meta['dump_started_at_utc']):raise EvidenceError('Dump clock reversed')
    row.update(dump_started_at_utc=meta['dump_started_at_utc'],dump_finished_at_utc=meta['dump_finished_at_utc'],
               sql_import_seconds=seconds(one(events,'IMPORT_FINISHED')['monotonic_ns'],one(events,'IMPORT_STARTED')['monotonic_ns']),
               restored_snapshot_rows=baseline['row_count'],write_probe_rows=1)
    if name=='main':
        snapshot=one(events,'SNAPSHOT_VERIFIED')
        if snapshot['snapshot_id']!=receipt['snapshot_id'] or snapshot['manifest_sha256']!=receipt['manifest_sha256']:
            raise EvidenceError('Snapshot event differs from selected receipt')
        if r['measurement_version']==GUIDED:
            final=confirmations(events)
            if stable[0]['monotonic_ns']<final or one(events,'FINAL_DATA_VERIFIED')['row_count']!=ready['row_count']:
                raise EvidenceError('Final stable/data gate mismatch')
            row['operator_confirmation']='RECORDED; human confirmations are not identity authentication'
        comparison,lower,upper,provenance=membership(bundle,start['monotonic_ns'])
        row.update(backup_verified_at_utc=snapshot['utc'],backup_age_since_verified_seconds=seconds(start['monotonic_ns'],snapshot['monotonic_ns']),
                   acknowledged_requests=len(bundle['acks']),recovered_requests=len(comparison['recovered_requests']),
                   unrecovered_acknowledged_requests=len(comparison['unrecovered_acknowledged']),duplicate_requests=len(comparison['duplicates']),
                   rpo_status='BOUNDED OBSERVATION' if lower is not None else 'NOT TESTED',
                   recovered_commit_lag_lower_seconds=lower,recovered_commit_lag_upper_seconds=upper,membership_provenance=provenance)
    return row,integrity


def export_trial(directory, output):
    bundle=load_trial(directory);row,check=analyze_trial(bundle)
    output=safe_path(Path(output).absolute()).resolve()
    # An export must never become part of the evidence it analyzes.
    if output==bundle['directory'] or bundle['directory'] in output.parents:
        raise EvidenceError('Output directory must be outside the input trial')
    output.mkdir(parents=True)
    for name in ('metrics.csv','Đo_lường_RPO_RTO.csv'):
        with (output/name).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=FIELDS+EXTRA_FIELDS,lineterminator='\n');writer.writeheader()
            writer.writerow({key:csv_cell(value) for key,value in row.items()})
    summary={'schema_version':2,'input_kind':'sealed-controller-run','samples':[row],
             'main_trial_count':int(row['scenario']=='drill' and row['trial_status']=='PASS'),
             'rto_rpo_targets':'NOT TESTED; no objectives selected','independent_storage':'NOT TESTED',
             'runtime':bundle['result']['runtime'],'measurement_version':row['measurement_version']}
    (output/'metrics.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'integrity.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    from evidence import ROOT
    processor_files=list(Path(__file__).parent.glob('*.py'))+[ROOT/'SOURCE/recovery/common.py',ROOT/'SOURCE/recovery/protocol.py',ROOT/'SOURCE/backup/backup.py']
    manifest={'schema_version':2,'run_id':row['run_id'],'execution_commit':row['execution_commit'],
              'inputs':bundle['inputs'],'processor_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in processor_files},
              'outputs':{p.name:sha(p) for p in output.iterdir() if p.is_file()},
              'trust':'Review/pin input manifest separately. This is not a cryptographic signature.'}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return summary
