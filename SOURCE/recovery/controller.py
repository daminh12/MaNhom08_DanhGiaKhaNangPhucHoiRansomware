"""Group08 clean recovery and benign service drills. Host Python 3.10+, Docker.

No volume removal, SQL deletion, repository reset, or malware operation exists.
All destructive-looking lifecycle operations remove stopped lab containers ONLY.
"""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

from common import (acknowledged_comparison, baseline_for, canonical_api, compare,
                    full_snapshot, run_id, sha, utc)

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'work/recovery'
SOURCE_PROJECT = 'group08-lab'
SOURCE_VOLUME = 'group08-lab_db_data'
BASE = ['docker', 'compose', '-p', SOURCE_PROJECT, '-f', str(ROOT/'compose.yaml')]
TOOLS = BASE + ['-f', str(ROOT/'compose.backup.yaml'), '-f', str(ROOT/'compose.recovery-tools.yaml')]
ROWS_SQL = "SELECT JSON_ARRAY(id,customer_alias,product_name,quantity,unit_price_vnd,DATE_FORMAT(created_at_utc,'%Y-%m-%dT%H:%i:%s.%fZ')) FROM lab_config.orders ORDER BY id;"
MYSQL = 'export MYSQL_PWD="$(cat /run/secrets/db_root_password)"; exec mysql -u root --default-character-set=utf8mb4 --batch --raw --skip-column-names'


def write_json(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temp.replace(path)


def reject_symlinks(path):
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError('Symlink components are forbidden in recovery paths')


@contextmanager
def controller_lock(daemon_id):
    # Common to multiple checkouts on the same host/user and Docker daemon.
    import hashlib
    key = hashlib.sha256((daemon_id+SOURCE_PROJECT).encode()).hexdigest()[:20]
    path = Path(tempfile.gettempdir())/('group08-recovery-'+key+'.lock')
    reject_symlinks(path)
    with path.open('x') as f:
        f.write(str(os.getpid()))
    try:
        yield
    finally:
        path.unlink()


class Lab:
    def __init__(self, args):
        self.a = args
        self.rid = run_id(args.run_id)
        self.token = hashlib.sha256(self.rid.encode()).hexdigest()[:10].upper()
        self.project = 'group08-restore-'+self.rid
        reject_symlinks(WORK)
        WORK.mkdir(parents=True, exist_ok=True)
        self.work = WORK/self.rid
        self.work.mkdir()  # refusal is intentional, including interrupted runs
        self.env = os.environ.copy()
        if os.name != 'nt':
            self.env.update(BACKUP_UID=str(os.getuid()), BACKUP_GID=str(os.getgid()))
        self.env.update(RESTORE_SECRET_DIR=(ROOT/'secrets/restore'/self.rid).as_posix(),
                        RESTORE_WEB_PORT=str(args.port), PYTHONDONTWRITEBYTECODE='1')
        self.dc = ['docker','compose','-p',self.project,'-f',str(ROOT/'compose.restore.yaml')]
        self.source_touched = False
        self.target_created = False
        self.t0 = None
        self.result = {'schema_version':1,'run_id':self.rid,'scenario':args.action,'status':'FAILED',
                       'started_at_utc':utc(),'windows_execution':'NOT TESTED' if os.name!='nt' else 'native host',
                       'source_volume':SOURCE_VOLUME,'target_project':self.project,
                       'release_source_containers':args.release_source_containers,
                       'rto_rpo_objectives':'NOT TESTED; no numeric objectives configured'}

    def event(self, name, **data):
        value={'utc':utc(),'monotonic_ns':time.monotonic_ns(),'event':name,'run_id':self.rid,**data}
        with (self.work/'events.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps(value,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
        return value

    def call(self, command, label, data=None, timeout=180):
        self.event('COMMAND_STARTED',label=label)
        p=subprocess.run(command,cwd=ROOT,env=self.env,input=data,capture_output=True,timeout=timeout)
        self.event('COMMAND_FINISHED',label=label,exit_code=p.returncode)
        if p.returncode:
            # SQL stdin and Docker inspect environment are deliberately never logged.
            message=p.stderr.decode('utf-8',errors='replace')[-1800:]
            raise RuntimeError(label+' failed (exit '+str(p.returncode)+'): '+message)
        return p.stdout.decode('utf-8')

    def source(self, *args, **kwargs):
        return self.call(BASE+list(args),kwargs.pop('label','source '+args[0]),**kwargs)

    def target(self, *args, **kwargs):
        return self.call(self.dc+list(args),kwargs.pop('label','target '+args[0]),**kwargs)

    def sql(self, sql, target=False, label='read DB metadata'):
        command=(self.dc if target else BASE)+['exec','-T','db','sh','-c',MYSQL]
        return self.call(command,label,data=("SET time_zone='+00:00';\n"+sql+'\n').encode())

    def capture(self, target=False):
        columns=self.sql("SELECT GROUP_CONCAT(COLUMN_NAME ORDER BY ORDINAL_POSITION) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='lab_config' AND TABLE_NAME='orders';",target,label='verify fixed six-column scope').strip()
        if columns!='id,customer_alias,product_name,quantity,unit_price_vnd,created_at_utc':
            raise ValueError('Schema columns differ from the fixed Group08 lab contract')
        rows=[json.loads(line) for line in self.sql(ROWS_SQL,target,label='capture every orders row').splitlines()]
        create=self.sql('SHOW CREATE TABLE lab_config.orders;',target,label='capture orders schema')
        if not create.startswith('orders\t'):
            raise ValueError('Unexpected SHOW CREATE TABLE output')
        schema=create.split('\t',1)[1].strip()
        return schema,rows

    def source_port(self):
        port='8080'
        p=ROOT/'.env'
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith('WEB_PORT='):port=line.split('=',1)[1].strip()
        port=os.environ.get('WEB_PORT',port)
        if not port.isdecimal() or not 1024<=int(port)<=65535:raise ValueError('Invalid lab port')
        return int(port)

    def http(self, path='/health', port=None, payload=None):
        url='http://127.0.0.1:'+str(port or self.source_port())+path
        req=urllib.request.Request(url,data=None if payload is None else json.dumps(payload).encode(),
                                   headers={'Content-Type':'application/json','Cache-Control':'no-cache'})
        try:
            with urllib.request.urlopen(req,timeout=5) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as e:
            return e.code,json.loads(e.read().decode())

    def wait_health(self, port, count=None, timeout=180):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            try:
                code,body=self.http(port=port)
                if code==200 and (count is None or body['orders_count']==count):return body
            except (OSError,ValueError):pass
            time.sleep(1)
        raise TimeoutError('Application did not become healthy with expected count')

    def stable_health(self, port, count):
        for i in range(3):
            health=self.wait_health(port,count,timeout=10)
            self.event('STABILITY_PROBE',sample=i+1,http_status=200,health=health)
            if i<2:time.sleep(1)

    def inspect(self, name):
        return json.loads(self.call(['docker','inspect',name],'inspect lab resource'))[0]

    def validate_source(self):
        db=self.inspect('group08-lab-db-1');web=self.inspect('group08-lab-web-1')
        for obj,service in [(db,'db'),(web,'web')]:
            if obj['Config']['Labels'].get('com.docker.compose.project')!=SOURCE_PROJECT or obj['Config']['Labels'].get('com.docker.compose.service')!=service or not obj['State']['Running']:
                raise ValueError('Expected running Group08 source services only')
        mounts=[m for m in db['Mounts'] if m['Destination']=='/var/lib/mysql']
        if len(mounts)!=1 or mounts[0].get('Name')!=SOURCE_VOLUME:raise ValueError('Unexpected source data volume')
        bindings=web['NetworkSettings']['Ports'].get('8000/tcp',[])
        if not any(b['HostIp']=='127.0.0.1' and b['HostPort']==str(self.source_port()) for b in bindings):
            raise ValueError('Source URL must be owned by the expected localhost lab web')
        code,health=self.http()
        if code!=200:raise ValueError('Source health precondition failed')
        self.event('SOURCE_VALIDATED',db_id=db['Id'],web_id=web['Id'],health=health,volume=SOURCE_VOLUME)
        self.result['source_before']=health
        for image in ['mysql:8.4.7','group08-lab-web','group08-lab-backup']:
            self.call(['docker','image','inspect',image],'require preinstalled '+image)
        if self.a.action in ['restore','drill']:
            self.resource_check(allow_release_credit=self.a.release_source_containers)

    def preflight_target(self):
        if self.project==SOURCE_PROJECT or not self.project.startswith('group08-restore-p'):
            raise ValueError('Unsafe target project')
        containers=self.call(['docker','ps','-aq','--filter','label=com.docker.compose.project='+self.project],'guard existing target containers').strip()
        volumes=self.call(['docker','volume','ls','-q','--filter','label=com.docker.compose.project='+self.project],'guard existing target volumes').strip()
        # Names must also be checked: manually created volumes may have no labels.
        volume_names=self.call(['docker','volume','ls','--format','{{.Name}}'],'guard unlabelled target volume').splitlines()
        network_names=self.call(['docker','network','ls','--format','{{.Name}}'],'guard pre-existing target networks').splitlines()
        container_names=self.call(['docker','ps','-a','--format','{{.Names}}'],'guard unlabelled target containers').splitlines()
        names_collide=(self.project+'_restore_data' in volume_names or
                       any(self.project+'_'+n in network_names for n in ['lab','frontend']) or
                       any(self.project+'-'+n+'-1' in container_names for n in ['db','web']))
        if containers or volumes or names_collide:raise ValueError('Target already exists; partial targets cannot be reused')
        self.event('TARGET_PREFLIGHT_PASSED',project=self.project)

    def backup(self):
        bid='p2-'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+secrets.token_hex(6)
        folder=ROOT/'backups/runs'/bid
        reject_symlinks(folder)
        (folder/'payload').mkdir(parents=True)
        script='/tmp/group08-'+bid+'.sh'
        self.source_touched=True
        self.source('stop','web')
        primary=None;cleanup_errors=[]
        try:
            if self.sql('SELECT COUNT(*) FROM information_schema.innodb_trx;',label='confirm drained source transactions').strip()!='0':
                raise ValueError('Source still has active InnoDB transactions')
            before_schema,before_rows=self.capture()
            before=baseline_for(before_schema,before_rows)
            self.event('CAPTURE_STARTED',row_count=before['row_count'])
            self.source('cp','SOURCE/backup/db_dump.sh','db:'+script)
            self.source('cp','secrets/db_backup_password.txt','db:/tmp/group08-'+bid+'.secret')
            self.source('exec','-T','db','sh',script,'dump',bid,label='consistent Phase 2 mysqldump')
            for name in ['database.sql','metadata.json']:
                self.source('cp','db:/tmp/group08-'+bid+'/'+name,str(folder/'payload'/name))
            schema,rows=self.capture()
            if baseline_for(schema,rows)!=before:raise ValueError('Source changed during baseline/dump window')
            meta_path=folder/'payload/metadata.json'
            meta=json.loads(meta_path.read_text())
            meta.update(business_baseline=before,baseline_sql_sha256=sha(folder/'payload/database.sql'),
                        baseline_capture='web stopped; no admin writers/DDL; full before/after comparison')
            write_json(meta_path,meta)
            self.event('CAPTURE_FINISHED',row_count=len(rows),baseline=before)
        except BaseException as e:primary=e
        finally:
            for args,label in [(['exec','-T','db','sh',script,'cleanup',bid],'dump cleanup'),
                               (['exec','-T','db','rm','-f',script],'remove run script'),
                               (['start','web'],'resume source web')]:
                try:self.source(*args,label=label)
                except Exception as e:cleanup_errors.append(str(e))
            self.event('BACKUP_CLEANUP',status='FAILED' if cleanup_errors else 'PASS',errors=cleanup_errors)
        if primary is not None:raise primary
        if cleanup_errors:raise RuntimeError('Backup cleanup/resume failed; see journal')
        self.wait_health(self.source_port(),before['row_count'])
        try:
            self.call(TOOLS+['run','--rm','--no-deps','backup','snapshot','--run-id',bid],
                      'Phase 2 Restic snapshot/check/readback',timeout=660)
        except BaseException:
            if not (folder/'result.json').exists():
                write_json(folder/'result.json',{'run_id':bid,'status':'FAILED','phase':'backup_container','snapshot_id':None})
            raise
        receipt=json.loads((folder/'result.json').read_text())
        if receipt.get('status')!='PASS':raise ValueError('Backup did not produce a verified receipt')
        receipt['business_baseline']=before
        self.result['backup']=receipt
        write_json(self.work/'backup-receipt.json',receipt)
        self.event('SNAPSHOT_VERIFIED',backup_id=bid,snapshot_id=receipt['snapshot_id'],manifest_sha256=receipt['manifest_sha256'])
        return receipt

    def receipt(self):
        if not re.fullmatch(r'p2-[A-Za-z0-9_-]{1,76}',self.a.backup_id or ''):raise ValueError('Explicit --backup-id required')
        full_snapshot(self.a.snapshot_id or '')
        if not re.fullmatch('[0-9a-f]{64}',self.a.manifest_sha256 or ''):raise ValueError('Explicit trusted --manifest-sha256 required')
        p=ROOT/'backups/runs'/self.a.backup_id/'result.json'
        reject_symlinks(p)
        receipt=json.loads(p.read_text())
        if receipt.get('status')!='PASS' or receipt['snapshot_id']!=self.a.snapshot_id or receipt['manifest_sha256']!=self.a.manifest_sha256:
            raise ValueError('Selected snapshot/digest differs from trusted backup receipt')
        return receipt

    def archive(self, receipt):
        self.call(TOOLS+['run','--rm','--no-deps','--entrypoint','python','backup','/recovery-code/archive.py',
                        '--backup-id',receipt['run_id'],'--snapshot-id',receipt['snapshot_id'],
                        '--manifest-sha256',receipt['manifest_sha256'],'--restore-id',self.rid],
                  'extract and verify selected Restic snapshot',timeout=660)
        directory=self.work/'extracted'
        reject_symlinks(directory)
        metadata=json.loads((directory/'payload/metadata.json').read_text())
        self.event('ARTIFACT_VERIFIED',snapshot_id=receipt['snapshot_id'])
        return directory,metadata['business_baseline']

    def stop_source(self, fault=False):
        self.source_touched=True
        if fault:
            code,health=self.http()
            if code!=200:raise ValueError('Source unavailable before fault injection')
            self.event('LAST_HEALTHY',http_status=code,health=health)
            self.t0=self.event('FAULT_REQUESTED',service='db')['monotonic_ns']
        self.source('stop','db')
        if fault:
            code,body=self.http()
            if code!=503:raise ValueError('DB outage did not produce expected HTTP 503')
            self.event('FAULT_DETECTED',http_status=code,health=body)
        self.source('stop','web')
        for service in ['db','web']:
            logs=self.source('logs','--no-color','--timestamps',service)
            (self.work/('source-'+service+'.log')).write_text(logs)
        if self.a.release_source_containers:
            for service in ['db','web']:
                if self.inspect('group08-lab-'+service+'-1')['State']['Running']:
                    raise ValueError('Refusing to remove a running source container')
            self.source('rm','-f','db','web',label='release stopped source containers; preserve volumes')
            self.call(['docker','volume','inspect',SOURCE_VOLUME],'confirm source volume retained')
            self.event('SOURCE_CONTAINERS_RELEASED',volume_preserved=SOURCE_VOLUME)

    def resource_check(self, allow_release_credit=False):
        driver=self.call(['docker','info','--format','{{.Driver}}'],'inspect storage driver').strip()
        db_size=int(self.call(['docker','image','inspect','mysql:8.4.7','--format','{{.Size}}'],'inspect DB image size'))
        web_size=int(self.call(['docker','image','inspect','group08-lab-web','--format','{{.Size}}'],'inspect web image size'))
        needed=2*(db_size+web_size)+256*1024**2 if driver=='vfs' else 512*1024**2
        free=shutil.disk_usage(ROOT).free
        credit=2*(db_size+web_size) if driver=='vfs' and allow_release_credit else 0
        self.event('RESOURCE_CHECK',driver=driver,host_free_bytes=free,estimated_required_bytes=needed,
                   estimated_stopped_container_release_bytes=credit)
        if free+credit<needed:raise RuntimeError('Insufficient host space for clean recovery; do not remove data volumes/snapshots')

    def create_target(self):
        self.preflight_target()
        self.resource_check()
        secret_dir=ROOT/'secrets/restore'/self.rid
        reject_symlinks(secret_dir)
        secret_dir.mkdir(parents=True,mode=0o700)
        for name in ['root.txt','app.txt']:
            p=secret_dir/name
            with p.open('x') as f:f.write(secrets.token_hex(32))
            p.chmod(0o600 if name=='root.txt' else 0o644)
        self.target_created=True
        self.target('up','-d','--wait','--wait-timeout','180','db',timeout=210)
        db=self.inspect(self.project+'-db-1')
        data=[m for m in db['Mounts'] if m['Destination']=='/var/lib/mysql']
        if len(data)!=1 or data[0].get('Name')!=self.project+'_restore_data' or data[0].get('Name')==SOURCE_VOLUME:
            raise ValueError('Unsafe target database mount')
        volume=json.loads(self.call(['docker','volume','inspect',data[0]['Name']],'inspect target volume'))[0]
        if volume['Labels'].get('com.docker.compose.project')!=self.project:raise ValueError('Target ownership mismatch')
        if any(m['Destination']=='/docker-entrypoint-initdb.d' for m in db['Mounts']):raise ValueError('Seed mount forbidden')
        tables=self.sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='lab_config';",True).strip()
        if tables!='0':raise ValueError('Target schema is not empty')
        self.result['target_volume']=data[0]['Name']
        self.event('TARGET_READY',volume=data[0]['Name'],seed_tables=0)

    def create_order(self, alias, port, request_id):
        payload={'customer_alias':alias,'product_name':'Pen','quantity':1,'unit_price_vnd':25000}
        sent=self.event('REQUEST_SENT',request_id=request_id,alias=alias,payload=payload)
        try:code,body=self.http('/api/orders',port,payload)
        except (OSError,ValueError) as e:
            self.event('REQUEST_UNCERTAIN',request_id=request_id,error=type(e).__name__)
            raise RuntimeError('Uncertain write outcome; no automatic retry') from e
        if code!=201:
            self.event('REQUEST_UNCERTAIN',request_id=request_id,http_status=code)
            raise RuntimeError('Write not confirmed; no automatic retry')
        row=canonical_api(body['order'])
        if row[1:5]!=[alias,'Pen',1,25000]:raise ValueError('API write response mismatch')
        ack=self.event('REQUEST_ACKNOWLEDGED',request_id=request_id,row=row)
        return {'request_id':request_id,'alias':alias,'row':row,'sent_ns':sent['monotonic_ns'],'ack_ns':ack['monotonic_ns']}

    def verify_api(self, rows):
        self.wait_health(self.a.port,len(rows))
        code,body=self.http('/api/orders',self.a.port)
        if code!=200 or body['total']!=len(rows) or [canonical_api(r) for r in body['orders']]!=list(reversed(rows))[:100]:
            raise ValueError('API read does not match independently verified target rows')
        web=self.inspect(self.project+'-web-1')
        binding=web['NetworkSettings']['Ports'].get('8000/tcp',[])
        if not any(x['HostIp']=='127.0.0.1' and x['HostPort']==str(self.a.port) for x in binding):raise ValueError('Target URL not owned by restored web')

    def recover(self, receipt):
        directory,baseline=self.archive(receipt)
        self.create_target()
        self.target('cp',str(directory/'payload/database.sql'),'db:/tmp/group08-import.sql')
        self.event('IMPORT_STARTED',target_state='DIRTY until all checks succeed')
        self.target('exec','-T','db','sh','-c',MYSQL+' lab_config < /tmp/group08-import.sql',label='SQL import; every nonzero exit is failure')
        self.event('IMPORT_FINISHED')
        password=(ROOT/'secrets/restore'/self.rid/'app.txt').read_text()
        if not re.fullmatch('[a-f0-9]{64}',password):raise ValueError('Unexpected target credential format')
        self.sql("CREATE USER 'group08_app'@'%' IDENTIFIED BY '"+password+"'; GRANT SELECT, INSERT ON lab_config.orders TO 'group08_app'@'%';",True,label='provision target app role')
        grants=self.sql("SHOW GRANTS FOR 'group08_app'@'%';",True,label='verify target app grants')
        expected='GRANT SELECT, INSERT ON `lab_config`.`orders` TO `group08_app`@`%`'
        if [g for g in grants.splitlines() if not g.startswith('GRANT USAGE ON ')]!=[expected]:raise ValueError('Unexpected application privileges')
        (self.work/'target-grants.txt').write_text(grants)
        schema,rows=self.capture(True)
        write_json(self.work/'observed-baseline.json',baseline_for(schema,rows))
        compare(schema,rows,baseline)
        self.event('DATA_VERIFIED',row_count=len(rows),rows_sha256=baseline['rows_sha256'],schema_sha256=baseline['schema_sha256'])
        self.result['restored_snapshot_rows']=len(rows)
        self.target('up','-d','web')
        self.verify_api(rows)
        self.event('URL_READ_VERIFIED',url='http://127.0.0.1:'+str(self.a.port))
        probe=self.create_order('LAB-P3-PROBE-'+self.token,self.a.port,'recovery-write-probe')['row']
        schema,after=self.capture(True);compare(schema,after,baseline,probe)
        self.result['write_probe']=probe
        self.target('restart','db','web')
        self.wait_health(self.a.port,len(rows)+1)
        schema,after=self.capture(True);compare(schema,after,baseline,probe)
        self.verify_api(after)
        self.event('RESTART_VERIFIED',row_count=len(after))
        self.target('exec','-T','db','rm','-f','/tmp/group08-import.sql',label='cleanup target SQL staging')
        self.event('TARGET_CLEANUP',status='PASS')
        self.stable_health(self.a.port,len(after))
        ready=self.event('SERVICE_VERIFIED',url='http://127.0.0.1:'+str(self.a.port),row_count=len(after))
        if self.t0 is not None:self.result['observed_rto_seconds']=(ready['monotonic_ns']-self.t0)/1e9
        self.result.update(integrity='PASS',schema='PASS',grants='PASS',api_read_write='PASS',persistence='PASS')
        return rows

    def return_source(self):
        self.event('POST_TRIAL_RETURN_SOURCE_STARTED')
        if self.target_created:
            for service in ['db','web']:
                ids=self.target('ps','-a','-q',service).strip()
                if ids:
                    obj=self.inspect(ids)
                    if obj['Config']['Labels'].get('com.docker.compose.project')!=self.project:raise ValueError('Target ownership guard failed')
                    logs=self.target('logs','--no-color','--timestamps',service)
                    (self.work/('target-'+service+'.log')).write_text(logs)
            self.target('stop','web','db')
            self.target('rm','-f','web','db',label='release stopped target containers; preserve target volume')
        self.source('up','-d','--no-build','--wait','--wait-timeout','180','db','web',timeout=210)
        health=self.wait_health(self.source_port())
        self.result['source_after_return']=health
        self.event('POST_TRIAL_RETURN_SOURCE_FINISHED',health=health)

    def web_outage(self):
        schema,rows=self.capture();baseline=baseline_for(schema,rows)
        self.source_touched=True
        self.t0=self.event('FAULT_REQUESTED',service='web')['monotonic_ns']
        self.source('stop','web')
        try:
            try:code,_=self.http()
            except (OSError,ValueError):code=0
            if code==200:raise ValueError('Web outage was not observed')
            self.event('FAULT_DETECTED',http_status=code)
        finally:self.source('start','web')
        self.wait_health(self.source_port(),len(rows))
        schema,after=self.capture();compare(schema,after,baseline)
        self.stable_health(self.source_port(),len(rows))
        end=self.event('SERVICE_VERIFIED',scenario='web-only control',row_count=len(rows))
        self.result.update(observed_rto_seconds=(end['monotonic_ns']-self.t0)/1e9,
                           data_unchanged='PASS',rpo='NOT APPLICABLE; no snapshot recovery')

    def reject_corrupt(self, receipt):
        directory,_=self.archive(receipt)
        candidate=self.work/'corrupt-candidate'
        shutil.copytree(directory/'payload',candidate)
        path=candidate/'database.sql';data=bytearray(path.read_bytes());data[len(data)//2]^=1;path.write_bytes(data)
        spec=importlib.util.spec_from_file_location('phase2_verifier',ROOT/'SOURCE/backup/backup.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        manifest=json.loads((directory/'manifest.json').read_text())
        try:module.verify_payload(candidate,manifest)
        except ValueError as e:
            self.event('CORRUPT_INPUT_REJECTED',error=str(e),import_attempted=False)
            self.result.update(rejection='PASS',import_attempted=False,rto='NOT APPLICABLE',rpo='NOT APPLICABLE')
        else:raise ValueError('Corrupt candidate was accepted')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['backup','restore','drill','web-outage','reject-corrupt'])
    p.add_argument('--run-id',required=True)
    p.add_argument('--backup-id');p.add_argument('--snapshot-id');p.add_argument('--manifest-sha256')
    p.add_argument('--port',type=int,default=8081)
    p.add_argument('--post-orders',type=int,default=3)
    p.add_argument('--release-source-containers',action='store_true')
    p.add_argument('--return-source',action='store_true')
    args=p.parse_args()
    if not 1024<=args.port<=65535 or not 1<=args.post_orders<=20:p.error('Invalid lab port/order bound')
    run_id(args.run_id)
    daemon=subprocess.check_output(['docker','info','--format','{{.ID}}'],text=True).strip()
    with controller_lock(daemon):
        lab=Lab(args)
        try:
            code_files=['SOURCE/recovery/controller.py','SOURCE/recovery/archive.py','SOURCE/recovery/common.py','compose.restore.yaml','compose.recovery-tools.yaml','SOURCE/backup/backup.py','SOURCE/backup/db_dump.sh']
            lab.event('TRIAL_PREPARED',commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),python=sys.version.split()[0],
                      working_source_sha256={f:sha(ROOT/f) for f in code_files})
            lab.validate_source()
            if args.action=='backup':lab.backup()
            elif args.action=='web-outage':lab.web_outage()
            elif args.action=='reject-corrupt':lab.reject_corrupt(lab.receipt())
            elif args.action=='restore':
                receipt=lab.receipt();lab.preflight_target();lab.stop_source();lab.result['backup']=receipt
                lab.recover(receipt)
            else:
                if args.port!=lab.source_port():raise ValueError('Main drill must restore the original serving URL')
                acknowledgements=[lab.create_order('LAB-P4-PRE-'+lab.token,lab.source_port(),'pre-backup-checkpoint')]
                receipt=lab.backup()
                for i in range(args.post_orders):
                    acknowledgements.append(lab.create_order('LAB-P4-POST-'+lab.token+'-'+str(i),lab.source_port(),'post-backup-'+str(i)))
                write_json(lab.work/'acknowledgements.json',acknowledgements)
                lab.event('WORKLOAD_DRAINED',acknowledged_requests=len(acknowledgements),uncertain_requests=0)
                lab.preflight_target();lab.stop_source(fault=True)
                rows=lab.recover(receipt)
                comparison=acknowledged_comparison(acknowledgements,rows,lab.t0)
                if comparison['duplicates'] or not comparison['recovered_prefix'] or len(comparison['unrecovered_acknowledged'])!=args.post_orders:
                    raise ValueError('Unexpected acknowledged request recovery/duplicate result')
                lab.result['request_comparison']=comparison
                lab.event('REQUEST_COMPARISON_FINISHED',**comparison)
            lab.result['status']='PASS'
            lab.event('TRIAL_ENDED',status='PASS')
        except BaseException as e:
            lab.result.update(status='ABORTED' if isinstance(e,KeyboardInterrupt) else 'FAILED',error_type=type(e).__name__,error=str(e),target_state='do not reuse for import')
            lab.event('TRIAL_ENDED',status=lab.result['status'],error_type=type(e).__name__,error=str(e))
        finally:
            if args.return_source and lab.source_touched:
                try:lab.return_source();lab.result['return_source_status']='PASS'
                except Exception as e:
                    lab.result['return_source_status']='FAILED';lab.result['return_source_error']=str(e)
                    lab.event('POST_TRIAL_RETURN_SOURCE_FAILED',error=str(e))
            lab.result['finished_at_utc']=utc()
            write_json(lab.work/'result.json',lab.result)
        print(json.dumps(lab.result,ensure_ascii=False,indent=2))
        return 0 if lab.result['status']=='PASS' and lab.result.get('return_source_status')!='FAILED' else 1


if __name__=='__main__':raise SystemExit(main())
