"""Strict Phase 4 evidence validation; no Docker calls or service mutations."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'SOURCE/recovery'))
from common import acknowledged_comparison, full_snapshot, rows_hash, run_id, sha

EVIDENCE_REF='258ebc8b7bddb7b5fd4ce9562a37889bf1c2a36a'
EXECUTION_REF='dde61a2241de9bfd2b9f8138433b60f63d140cdd'
CASES={'main':('phase4','main','drill'), 'web-control':('phase4','web-control','web-outage'),
       'corrupt':('phase4','corrupt','reject-corrupt'), 'failed-restore':('phase3','first-failed','restore')}


class EvidenceError(ValueError):pass


def _pairs(items):
    result={}
    for key,value in items:
        if key in result:raise EvidenceError('Duplicate JSON key: '+key)
        result[key]=value
    return result


def decode(value):
    def reject(value):raise EvidenceError('Nonfinite JSON number: '+value)
    return json.loads(value,object_pairs_hook=_pairs,parse_constant=reject)


def load(path):return decode(Path(path).read_text(encoding='utf-8'))


def safe_path(path):
    path=Path(path)
    if any(p.is_symlink() for p in [path,*path.parents]):raise EvidenceError('Symlink evidence path forbidden')
    return path


def git_bytes(ref,path):
    if not re.fullmatch('[0-9a-f]{40}',ref):raise EvidenceError('A full trusted Git commit is required')
    if path.startswith('/') or '..' in Path(path).parts:raise EvidenceError('Unsafe evidence path')
    p=subprocess.run(['git','show',ref+':'+path],cwd=ROOT,capture_output=True)
    if p.returncode:raise EvidenceError('Pinned evidence object unavailable: '+path)
    return p.stdout


def pinned(path,ref,inputs):
    file=safe_path(ROOT/path)
    data=file.read_bytes();expected=git_bytes(ref,path)
    digest=hashlib.sha256(data).hexdigest()
    if data!=expected:raise EvidenceError('Evidence differs from pinned Git commit: '+path)
    inputs[path]={'sha256':digest,'size_bytes':len(data),'git_ref':ref}
    return data.decode('utf-8')


def load_case(name,ref=EVIDENCE_REF):
    phase,prefix,scenario=CASES[name];inputs={};base='docs/evidence/'+phase+'/'
    result=decode(pinned(base+prefix+'-result.json',ref,inputs))
    events=[decode(s) for s in pinned(base+prefix+'-events.jsonl',ref,inputs).splitlines()]
    extra={}
    if name=='main':
        extra['acks']=decode(pinned(base+'acknowledgements.json',ref,inputs))
        extra['manifest']=decode(pinned(base+'main-manifest.json',ref,inputs))
    if name=='corrupt':
        extra['receipt']=decode(pinned('docs/evidence/phase3/baseline-result.json',ref,inputs))['backup']
    return {'name':name,'scenario':scenario,'result':result,'events':events,'inputs':inputs,**extra}


def utc(value):
    if not isinstance(value,str):raise EvidenceError('UTC timestamp must be text')
    try:d=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as e:raise EvidenceError('Invalid UTC timestamp') from e
    if d.tzinfo is None or d.utcoffset()!=timezone.utc.utcoffset(d):raise EvidenceError('Expected UTC timestamp')
    return d


def seconds(a,b):
    if type(a) is not int or type(b) is not int or a<b:raise EvidenceError('Invalid monotonic duration')
    return format(Decimal(a-b)/Decimal(1_000_000_000),'.9f')


def one(events,name,required=True):
    found=[e for e in events if e['event']==name]
    if len(found)>1 or (required and not found):raise EvidenceError('Missing/ambiguous event: '+name)
    return found[0] if found else None


def timeline(bundle):
    result=bundle['result'];events=bundle['events'];previous=-1
    run_id(result['run_id'])
    if result['scenario']!=bundle['scenario'] or not events:raise EvidenceError('Scenario/timeline mismatch')
    for e in events:
        if not isinstance(e,dict) or e.get('run_id')!=result['run_id'] or not isinstance(e.get('event'),str):raise EvidenceError('Mixed or invalid event identity')
        n=e.get('monotonic_ns')
        if type(n) is not int or n<0 or n<previous:raise EvidenceError('Non-monotonic event stream')
        previous=n;utc(e.get('utc'))
    if events[0]['event']!='TRIAL_PREPARED':raise EvidenceError('Timeline has no preparation record')
    ended=one(events,'TRIAL_ENDED')
    if ended.get('status')!=result['status']:raise EvidenceError('Result/trial status disagreement')
    return events


def ordered(events,names):
    values=[one(events,n) for n in names]
    if any(a['monotonic_ns']>b['monotonic_ns'] for a,b in zip(values,values[1:])):raise EvidenceError('Invalid recovery event order')
    return values


def source_pin(bundle):
    hashes=bundle['events'][0].get('working_source_sha256')
    if bundle['name']!='main':return 'NOT TESTED' if not hashes else 'RECORDED; see original journal'
    required={'SOURCE/recovery/controller.py','SOURCE/recovery/archive.py','SOURCE/recovery/common.py',
              'compose.restore.yaml','compose.recovery-tools.yaml','SOURCE/backup/backup.py','SOURCE/backup/db_dump.sh'}
    if not isinstance(hashes,dict) or set(hashes)!=required:raise EvidenceError('Main trial execution fingerprint incomplete')
    for path,digest in hashes.items():
        if hashlib.sha256(git_bytes(EXECUTION_REF,path)).hexdigest()!=digest:raise EvidenceError('Execution source fingerprint mismatch')
    return 'PASS'


def close_number(value,expected):
    try:actual=Decimal(str(value))
    except Exception as e:raise EvidenceError('Invalid numeric summary') from e
    if not actual.is_finite() or abs(actual-Decimal(expected))>Decimal('0.000000001'):raise EvidenceError('Summary differs from raw monotonic calculation')


def ack_events(bundle,t0):
    acks=bundle['acks'];events=bundle['events'];ids=set()
    for a in acks:
        rid=a['request_id']
        if rid in ids:raise EvidenceError('Duplicate business request ID')
        ids.add(rid)
        sent=[e for e in events if e['event']=='REQUEST_SENT' and e.get('request_id')==rid]
        received=[e for e in events if e['event']=='REQUEST_ACKNOWLEDGED' and e.get('request_id')==rid]
        if len(sent)!=1 or len(received)!=1:raise EvidenceError('Missing/ambiguous request events')
        s,r=sent[0],received[0]
        if s['monotonic_ns']!=a['sent_ns'] or r['monotonic_ns']!=a['ack_ns'] or r['row']!=a['row'] or s['alias']!=a['alias']:
            raise EvidenceError('ACK file disagrees with request journal')
        payload=s['payload']
        if [payload[k] for k in ['customer_alias','product_name','quantity','unit_price_vnd']]!=a['row'][1:5]:raise EvidenceError('Sent payload differs from confirmed order')
    uncertain=[e for e in events if e['event']=='REQUEST_UNCERTAIN']
    if uncertain:raise EvidenceError('Uncertain writes are outside this measured sequential profile')
    drained=one(events,'WORKLOAD_DRAINED')
    if drained['acknowledged_requests']!=len(acks) or drained['uncertain_requests']!=0 or drained['monotonic_ns']>t0:raise EvidenceError('Invalid workload drain evidence')
    # Validate clocks/identities without assuming recovered membership.
    try:acknowledged_comparison(acks,[],t0)
    except (KeyError,ValueError,TypeError) as e:raise EvidenceError('Invalid ACK chronology/identity: '+str(e)) from e
    return acks


def membership(bundle,t0,fresh=None):
    acks=ack_events(bundle,t0)
    reported=bundle['result']['request_comparison']
    event=one(bundle['events'],'REQUEST_COMPARISON_FINISHED')
    for k in ['recovered_requests','unrecovered_acknowledged','duplicates','recovered_prefix','recovered_commit_age_bounds']:
        if event.get(k)!=reported.get(k):raise EvidenceError('Comparison result disagrees with raw journal')
    if fresh:
        if fresh['trial_run_id']!=bundle['result']['run_id'] or fresh['snapshot_id']!=bundle['result']['backup']['snapshot_id']:
            raise EvidenceError('Fresh verification belongs to another trial/snapshot')
        observations=fresh['request_observations']
        if [o['request_id'] for o in observations]!=[a['request_id'] for a in acks]:raise EvidenceError('Fresh membership coverage mismatch')
        rows=sorted([r for o in observations for r in o['matching_rows']],key=lambda r:r[0])
        provenance='post-trial DB recheck plus pinned historical full-data verification'
    else:
        known={a['request_id']:a for a in acks}
        if not isinstance(reported['recovered_requests'],list) or any(x not in known for x in reported['recovered_requests']):raise EvidenceError('Unknown recovered request')
        rows=sorted([known[x]['row'] for x in reported['recovered_requests']],key=lambda r:r[0])
        provenance='recorded trial comparison; no fresh membership check'
    try:computed=acknowledged_comparison(acks,rows,t0)
    except (KeyError,ValueError,TypeError) as e:raise EvidenceError(str(e)) from e
    for k in ['recovered_requests','unrecovered_acknowledged','duplicates','recovered_prefix']:
        if computed[k]!=reported[k]:raise EvidenceError('Recomputed request membership mismatch')
    if computed['duplicates'] or not computed['recovered_prefix']:raise EvidenceError('Cannot assign one recovery frontier to this sample')
    recovered=[a for a in acks if a['request_id'] in computed['recovered_requests']]
    lower=upper=None
    if recovered:
        last=recovered[-1];lower=seconds(t0,last['ack_ns']);upper=seconds(t0,last['sent_ns'])
        close_number(reported['recovered_commit_age_bounds']['lower_seconds'],lower)
        close_number(reported['recovered_commit_age_bounds']['upper_seconds'],upper)
    return computed,lower,upper,provenance


def artifact_check(bundle,artifact_root):
    if artifact_root is None or bundle['name']=='web-control':return {'status':'NOT TESTED' if artifact_root is None else 'NOT APPLICABLE'}
    result=bundle['result'];receipt=bundle.get('receipt',result.get('backup'))
    if receipt is None:raise EvidenceError('Missing selected archive receipt')
    full_snapshot(receipt['snapshot_id'])
    directory=safe_path(Path(artifact_root)/result['run_id']/'extracted')
    manifest_path=safe_path(directory/'manifest.json')
    if sha(manifest_path)!=receipt['manifest_sha256']:raise EvidenceError('Extracted manifest digest mismatch')
    spec=importlib.util.spec_from_file_location('phase2_metrics_verifier',ROOT/'SOURCE/backup/backup.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    manifest=load(manifest_path)
    try:module.verify_payload(directory/'payload',manifest)
    except ValueError as e:raise EvidenceError(str(e)) from e
    meta=module.validate_dump(directory/'payload',receipt['run_id'])
    if meta!=receipt['dump_metadata'] or meta.get('baseline_sql_sha256')!=sha(directory/'payload/database.sql'):
        raise EvidenceError('Metadata/baseline differs from pinned receipt')
    answer={'status':'PASS','manifest_sha256':sha(manifest_path),
            'files':[{**entry,'actual_sha256':sha(directory/'payload'/entry['path'])} for entry in manifest['files']]}
    if bundle['name']=='corrupt':
        candidate=safe_path(Path(artifact_root)/result['run_id']/'corrupt-candidate')
        try:module.verify_payload(candidate,manifest)
        except ValueError:answer['candidate_rejection']='PASS';answer['candidate_integrity']='FAIL (expected)'
        else:raise EvidenceError('Corrupt candidate is no longer rejected')
    return answer
