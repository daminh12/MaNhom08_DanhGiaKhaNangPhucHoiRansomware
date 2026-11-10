"""Post-trial integrity recheck of the OWNED retained target, never an import.

Cloud low-space option releases only stopped lab containers, preserving volumes.
The verification window is not another RTO/RPO trial or performance sample.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import types

from evidence import EVIDENCE_REF,ROOT,EvidenceError,load,load_case,sha,safe_path
sys.path.insert(0,str(ROOT/'SOURCE/recovery'))
import controller
from common import baseline_for,compare,run_id,utc


def verify(verification_id,output,release=False):
    run_id(verification_id)
    safe_path(output)
    if output.exists():raise EvidenceError('Verification output already exists')
    bundle=load_case('main',EVIDENCE_REF);r=bundle['result']
    if r['status']!='PASS' or r['integrity']!='PASS':raise EvidenceError('Only a successfully verified retained target may be checked')
    expected_project='group08-restore-'+run_id(r['run_id'])
    expected_volume=expected_project+'_restore_data'
    if r['target_project']!=expected_project or r['target_volume']!=expected_volume or expected_volume==controller.SOURCE_VOLUME:
        raise EvidenceError('Unexpected target ownership')
    secret=ROOT/'secrets/restore'/r['run_id'];safe_path(secret)
    if not (secret/'root.txt').is_file():raise EvidenceError('Existing target credential required; never rotate/init')
    local_dir=safe_path(ROOT/'backups/runs'/r['backup']['run_id'])
    local_receipt=load(local_dir/'result.json')
    if any(local_receipt.get(k)!=r['backup'].get(k) for k in ['run_id','status','snapshot_id','manifest_sha256','dump_metadata']):
        raise EvidenceError('Local Restic receipt differs from pinned historical evidence')
    if sha(local_dir/'manifest.json')!=r['backup']['manifest_sha256']:raise EvidenceError('Local manifest digest changed')
    args=types.SimpleNamespace(run_id=verification_id,action='verify-retained',port=8081,
                              release_source_containers=release)
    daemon=subprocess.check_output(['docker','info','--format','{{.ID}}'],text=True).strip()
    with controller.controller_lock(daemon):
        lab=controller.Lab(args);lab.project=expected_project
        lab.dc=['docker','compose','-p',expected_project,'-f',str(ROOT/'compose.restore.yaml')]
        lab.env['RESTORE_SECRET_DIR']=secret.as_posix()
        answer={'status':'FAILED','trial_run_id':r['run_id'],'not_new_rto_trial':True,
                'business_queries_read_only':True,'started_at_utc':utc(),
                'input_result_sha256':sha(ROOT/'docs/evidence/phase4/main-result.json'),
                'evidence_ref':EVIDENCE_REF,'snapshot_id':r['backup']['snapshot_id'],
                'target_volume':expected_volume,'request_observations':[]}
        try:
            lab.validate_source()
            answer['source_before']=lab.result['source_before']
            volume=json.loads(lab.call(['docker','volume','inspect',expected_volume],'validate retained target volume'))[0]
            if (volume.get('Labels') or {}).get('com.docker.compose.project')!=expected_project:raise EvidenceError('Target volume label mismatch')
            if lab.target('ps','-a','-q').strip():raise EvidenceError('Target containers already exist; inspect before verification')
            lab.stop_source()
            # Real Restic readback, every command with its own durable local log.
            readback=lab.call(controller.TOOLS+['run','--rm','--no-deps','backup','verify','--run-id',r['backup']['run_id']],
                     'fresh Restic check/readback of pinned main snapshot',timeout=660)
            checked=json.loads(readback)
            if checked.get('status')!='PASS' or checked.get('snapshot_id')!=r['backup']['snapshot_id']:
                raise EvidenceError('Restic verified another snapshot')
            answer['restic_verified_at_utc']=checked['verified_at_utc']
            log=ROOT/'backups/runs'/r['backup']['run_id']/'verify.log'
            shutil.copyfile(log,lab.work/'restic-readback.txt')
            code="import backup; from pathlib import Path; print(backup.restic('snapshots','--json',log=Path('/recovery-work/"+verification_id+"/snapshot-list.txt')))"
            raw=lab.call(controller.TOOLS+['run','--rm','--no-deps','--entrypoint','python','backup','-c',code],
                         'record retained snapshot inventory',timeout=660)
            snapshots=json.loads(raw)
            answer['snapshot_ids']=[s['id'] for s in snapshots]
            if r['backup']['snapshot_id'] not in answer['snapshot_ids']:raise EvidenceError('Selected snapshot missing')
            answer['restic_check']='PASS'
            driver=lab.call(['docker','info','--format','{{.Driver}}'],'verify storage profile').strip()
            size=int(lab.call(['docker','image','inspect','mysql:8.4.7','--format','{{.Size}}'],'verify DB image size'))
            required=2*size+128*1024**2 if driver=='vfs' else 256*1024**2
            if shutil.disk_usage(ROOT).free<required:raise EvidenceError('Not enough space to inspect retained DB')
            lab.target_created=True
            lab.target('up','-d','--wait','--wait-timeout','180','db',timeout=210)
            db=lab.inspect(expected_project+'-db-1')
            mounts=[m for m in db['Mounts'] if m['Destination']=='/var/lib/mysql']
            if len(mounts)!=1 or mounts[0].get('Name')!=expected_volume:raise EvidenceError('Retained mount mismatch')
            schema,rows=lab.capture(True)
            baseline=r['backup']['dump_metadata']['business_baseline']
            probe=r['write_probe'];compare(schema,rows,baseline,probe)
            observed=baseline_for(schema,[row for row in rows if row[0]!=probe[0]])
            acks=bundle['acks']
            for ack in acks:
                answer['request_observations'].append({'request_id':ack['request_id'],
                   'matching_rows':[row for row in rows if row[1]==ack['alias']]})
            grants=lab.sql("SHOW GRANTS FOR 'group08_app'@'%';",True,label='read retained application grants')
            if [g for g in grants.splitlines() if not g.startswith('GRANT USAGE ON ')]!=['GRANT SELECT, INSERT ON `lab_config`.`orders` TO `group08_app`@`%`']:
                raise EvidenceError('Retained application grants changed')
            answer.update(status='PASS',base_rows_sha256=observed['rows_sha256'],schema_sha256=observed['schema_sha256'],
                          base_row_count=observed['row_count'],total_rows=len(rows),probe_row=probe,grants='PASS',verified_at_utc=utc())
            lab.event('RETAINED_TARGET_VERIFIED',base_row_count=observed['row_count'],total_rows=len(rows),not_new_rto_trial=True)
        except BaseException as e:
            answer.update(status='ABORTED' if isinstance(e,KeyboardInterrupt) else 'FAILED',error=str(e))
        finally:
            if lab.source_touched:
                try:
                    lab.return_source();answer.update(return_source_status='PASS',source_after=lab.result['source_after_return'])
                except Exception as e:answer.update(return_source_status='FAILED',return_source_error=str(e))
            before=answer.get('source_before');after=answer.get('source_after')
            answer['source_unchanged']=before==after if before is not None and after is not None else None
            if answer['source_unchanged'] is False:answer['status']='FAILED'
            answer['finished_at_utc']=utc()
            output.parent.mkdir(parents=True,exist_ok=True)
            controller.write_json(output,answer)
        return answer,lab.work


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--verification-id',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--release-source-containers',action='store_true')
    a=p.parse_args()
    try:
        result,work=verify(a.verification_id,a.output,a.release_source_containers)
        print(json.dumps({'status':result['status'],'result':str(a.output),'journal':str(work)},indent=2))
        raise SystemExit(0 if result['status']=='PASS' and result.get('return_source_status')=='PASS' else 1)
    except (ValueError,OSError,KeyError) as e:p.exit(1,'Verification failed: '+str(e)+'\n')
