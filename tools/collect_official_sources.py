"""Lock each official repository independently, collect immutable archives and file fingerprints."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
GIT = shutil.which('git')
RELEASES = [('4.1',11),('5.0.3',15),('5.1.0',18),('6.0',20),('6.1',23)]
REPOS = {'docs':'docs', 'samples':'applications_app_samples', 'arkts_api':'interface_sdk-js', 'native_api':'interface_sdk_c'}

def identity(*values):
    return hashlib.sha256(json.dumps(values,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def filesystem_path(path):
    """Use extended Windows paths without changing portable manifest paths."""
    absolute = str(path.resolve())
    return Path('\\\\?\\' + absolute) if os.name == 'nt' else path

def write_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    for attempt in range(20):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt==19: raise
            time.sleep(0.2)

def resolve_repo(kind, repo):
    result = subprocess.run([GIT,'ls-remote','--heads','--tags',f'https://github.com/openharmony/{repo}.git'],capture_output=True,text=True,timeout=120,check=True)
    refs = dict(line.split()[::-1] for line in result.stdout.splitlines() if len(line.split())==2)
    records=[]
    for version,level in RELEASES:
        candidates=[f'refs/tags/OpenHarmony-v{version}-Release',f'refs/heads/OpenHarmony-{version}-Release']
        selected=next((ref for ref in candidates if ref in refs),None)
        if selected is None:
            records.append({'kind':kind,'repository':f'https://github.com/openharmony/{repo}',
                            'release_id':f'OpenHarmony-{version}-Release','api_level':level,
                            'status':'source_ref_unavailable','checked_candidates':candidates})
            continue
        commit=refs.get(selected+'^{}',refs[selected])
        records.append({'source_id':identity('OpenHarmony',repo,commit,kind), 'kind':kind,
                        'platform':'OpenHarmony','release_id':f'OpenHarmony-{version}-Release',
                        'official_release_name':f'OpenHarmony {version} Release', 'api_level':level,
                        'repository':f'https://github.com/openharmony/{repo}','repository_name':repo,
                        'ref':selected,'commit':commit, 'snapshot_kind':'release_tag' if '/tags/' in selected else 'maintenance_branch_snapshot',
                        'sdk_package_version':None, 'mapping_status':'official_named_release_candidate',
                        'status':'locked','resolved_at':datetime.now(timezone.utc).isoformat()})
    return records

def included(kind, relative):
    first=relative.split('/')[0]
    license_file=first.lower().startswith(('license','notice','copying','copyright','dco','readme'))
    return kind!='docs' or first=='zh-cn' or license_file

class GitBlobReader:
    def __init__(self, checkout):
        self.process=subprocess.Popen([GIT,'-C',str(checkout),'cat-file','--batch'],stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                      env={**os.environ,'GIT_NO_LAZY_FETCH':'1'})
    def read(self, sha):
        p=self.process; p.stdin.write((sha+'\n').encode('ascii')); p.stdin.flush()
        header=p.stdout.readline().decode('ascii').strip().split()
        if len(header)!=3 or header[0]!=sha or header[1]!='blob': raise ValueError('Git blob unavailable: '+sha)
        size=int(header[2]); raw=p.stdout.read(size)
        if len(raw)!=size or p.stdout.read(1)!=b'\n': raise ValueError('Incomplete Git blob: '+sha)
        if hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest()!=sha: raise ValueError('Invalid Git blob: '+sha)
        return raw
    def close(self):
        p=self.process
        if p.poll() is None:
            p.stdin.close(); p.stdin=None
            try: p.communicate(timeout=30)
            except subprocess.TimeoutExpired: p.kill(); p.wait()

def lfs_payload_matches(pointer, payload):
    if not pointer.startswith(b'version https://git-lfs.github.com/spec/v1\n'): return False
    oid=re.search(rb'^oid sha256:([0-9a-f]{64})$',pointer,re.M)
    size=re.search(rb'^size ([0-9]+)$',pointer,re.M)
    return bool(oid and size and len(payload)==int(size[1]) and hashlib.sha256(payload).hexdigest()==oid[1].decode('ascii'))

def import_source_lock(path, kinds):
    sources=json.loads(path.read_text(encoding='utf-8'))['sources']
    records=[]
    for s in sources:
        if s['kind'] not in kinds: continue
        record={**s,'repository_name':s['repository'].rstrip('/').split('/')[-1].removesuffix('.git'),
                'status':'locked','body_status':'unavailable'}
        if s.get('archive_sha256'): record['expected_archive_sha256']=s['archive_sha256']
        if s.get('file_count') is not None: record['expected_file_count']=s['file_count']
        records.append(record)
    if set(kinds)-{s['kind'] for s in records}: raise ValueError('Pinned source lock lacks requested kinds')
    return records

def file_sha256(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        while raw:=stream.read(1024*1024): digest.update(raw)
    return digest.hexdigest()

def reusable_collection(record, root):
    """Trust a previous full verification only while all its input bytes match."""
    if record.get('status')!='collected' or record.get('body_status')!='complete' or record.get('body_storage')!='verified_archive':
        return False
    folder=root/'sources'/record['source_id']
    receipt=folder/'verification-receipt.json'
    if not receipt.exists(): return False
    try:
        saved=json.loads(receipt.read_text(encoding='utf-8'))
        provenance={key:record.get(key) for key in ('source_id','kind','repository','release_id','commit','archive_normalization','file_count','archive_sha256')}
        if saved.get('schema_version')!=1 or saved.get('provenance')!=provenance: return False
        if record.get('expected_archive_sha256',record['archive_sha256'])!=record['archive_sha256']: return False
        if record.get('expected_file_count',record['file_count'])!=record['file_count']: return False
        paths={'archive':root/'archives'/f"{record['source_id']}.zip",'inventory':folder/'inventory.json','ledger':folder/'files.jsonl'}
        return all(path.is_file() and file_sha256(path)==saved['sha256'][name] for name,path in paths.items())
    except (OSError,ValueError,KeyError):
        return False

def save_collection_receipt(record, root):
    if record.get('body_status')!='complete' or record.get('body_storage')!='verified_archive': return
    folder=root/'sources'/record['source_id']
    write_json(folder/'verification-receipt.json',{
        'schema_version':1,
        'provenance':{key:record.get(key) for key in ('source_id','kind','repository','release_id','commit','archive_normalization','file_count','archive_sha256')},
        'sha256':{'archive':record['archive_sha256'],'inventory':file_sha256(folder/'inventory.json'),'ledger':file_sha256(folder/'files.jsonl')}})

def recover_collection_record(record, root):
    """Recover a worker's result if the aggregate progress file was not updated."""
    if record.get('status')=='collected': return record
    path=root/'verified-results'/f"{record['source_id']}.json"
    if not path.exists(): return record
    try:
        saved=json.loads(path.read_text(encoding='utf-8'))
        keys=('source_id','kind','repository','release_id','commit')
        if saved.get('status')!='collected' or any(saved.get(k)!=record.get(k) for k in keys): return record
        merged={**record,**saved}
        for key in ('ref','expected_archive_sha256','expected_file_count'):
            if key in record: merged[key]=record[key]
        # collect still validates the receipt and all input hashes before reuse.
        return merged
    except (OSError,ValueError,KeyError): return record

def acquire_blob_batch(git, batch):
    check=git('cat-file','--batch-check',input=''.join(h+'\n' for h in batch),env={**os.environ,'GIT_NO_LAZY_FETCH':'1'})
    batch=[line.split()[0] for line in check.stdout.splitlines() if line.endswith(' missing')]
    if not batch: return
    try:
        git('fetch','--no-tags','--no-write-fetch-head','--no-filter','origin',*batch,timeout=180)
    except subprocess.CalledProcessError as exc:
        # Splitting a connectivity failure repeats the same failure for every object.
        object_error=re.search(r'not our ref|unadvertised object|couldn.t find remote ref|does not allow request for unadvertised',exc.stderr or '',re.I)
        if not object_error or len(batch)==1: raise
        middle=len(batch)//2
        acquire_blob_batch(git,batch[:middle]); acquire_blob_batch(git,batch[middle:])

def collect(record, root, transport='archive', reverify=False):
    started=time.perf_counter()
    if record['status']=='source_ref_unavailable': return record
    if not reverify and transport=='git-batches' and reusable_collection(record,root):
        return {**record,'performance':{'elapsed_seconds':round(time.perf_counter()-started,3),'verified_archive_reused':True}}
    source_id=record['source_id']
    folder=root/'sources'/source_id
    archive=root/'archives'/f'{source_id}.zip'
    materialize = not (transport=='git-batches' and record['kind'] in ('docs','samples'))
    checkout=None; blob_reader=None
    archive.parent.mkdir(parents=True,exist_ok=True)
    url=f"https://codeload.github.com/openharmony/{record['repository_name']}/zip/{record['commit']}"
    try:
        if transport in ('git','git-batches'):
            checkout = root/('git-cache-v3' if transport=='git-batches' else 'git-cache-v2')/source_id
            checkout.mkdir(parents=True, exist_ok=True)
            def git(*args, **options):
                timeout=options.pop('timeout',600)
                return subprocess.run([GIT, '-C', str(checkout), '-c', 'http.sslBackend=openssl', '-c', 'core.quotepath=false', '-c', 'core.autocrlf=false', '-c', 'fetch.unpackLimit=1', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
                                       *args], capture_output=True, text=True, encoding='utf-8', check=True, timeout=timeout, **options)
            if not (checkout/'.git').exists():
                git('init')
                previous = [root/cache/source_id/'.git/objects' for cache in ('git-cache','git-cache-v2')]
                if transport=='git-batches':
                    sources = json.loads((root/'sources.json').read_text(encoding='utf-8'))['sources'] if (root/'sources.json').exists() else [record]
                    previous += [root/'git-cache-v2'/s['source_id']/'.git/objects' for s in sources
                                 if s.get('repository')==record['repository'] and s.get('status')=='collected']
                    earlier=sources[:next(i for i,s in enumerate(sources) if s['source_id']==source_id)]
                    previous += [root/'git-cache-v3'/s['source_id']/'.git/objects' for s in earlier
                                 if s.get('repository')==record['repository']]
                previous = list(dict.fromkeys(p for p in previous if p.exists()))
                if previous:
                    (checkout/'.git/objects/info/alternates').write_text(''.join(p.resolve().as_posix()+'\n' for p in previous),encoding='utf-8',newline='\n')
            if transport=='git-batches':
                sources=json.loads((root/'sources.json').read_text(encoding='utf-8'))['sources'] if (root/'sources.json').exists() else [record]
                earlier=sources[:next(i for i,s in enumerate(sources) if s['source_id']==source_id)]
                alternate_path=checkout/'.git/objects/info/alternates'
                existing=alternate_path.read_text(encoding='utf-8').splitlines() if alternate_path.exists() else []
                existing += [(root/'git-cache-v3'/s['source_id']/'.git/objects').resolve().as_posix() for s in earlier
                             if s.get('repository')==record['repository'] and (root/'git-cache-v3'/s['source_id']/'.git/objects').exists()]
                alternate_path.write_text(''.join(p+'\n' for p in dict.fromkeys(existing)),encoding='utf-8',newline='\n')
                git('config','remote.origin.url',record['repository']+'.git')
                git('config','remote.origin.promisor','true')
                git('config','remote.origin.partialclonefilter','blob:none')
            try:
                git('cat-file', '-e', record['commit']+'^{commit}', env={**os.environ,'GIT_NO_LAZY_FETCH':'1'})
            except subprocess.CalledProcessError:
                for attempt in range(2):
                    try:
                        if transport=='git-batches':
                            git('fetch','--depth=1','--filter=blob:none','origin',record['ref'],timeout=180)
                        else:
                            git('fetch', '--depth=1', record['repository']+'.git', record['ref'],timeout=180)
                        if git('rev-parse','FETCH_HEAD^{commit}').stdout.strip() != record['commit']:
                            raise ValueError('Remote release ref moved; source lock retained')
                        break
                    except subprocess.CalledProcessError:
                        if attempt: raise
                        time.sleep(2)
            if git('rev-parse', record['commit']+'^{commit}').stdout.strip() != record['commit']:
                raise ValueError('Fetched commit does not match source lock')
            tree = git('ls-tree', '-r', '--full-tree', record['commit']).stdout
            inventory = []
            submodules = []
            for line in tree.splitlines():
                metadata, relative = line.split('\t', 1)
                mode, kind, sha = metadata.split()
                if kind == 'commit': submodules.append({'path': relative, 'commit': sha})
                if kind == 'blob' and included(record['kind'], relative):
                    inventory.append({'path':relative, 'git_blob_sha':sha, 'mode':mode})
            folder.mkdir(parents=True, exist_ok=True)
            write_json(folder/'inventory.json', {'commit':record['commit'], 'complete':True,
                                                'files':inventory, 'submodules':submodules})
            if transport=='git-batches':
                hashes=list(dict.fromkeys(f['git_blob_sha'] for f in inventory))
                result=git('cat-file','--batch-check',input=''.join(h+'\n' for h in hashes),
                           env={**os.environ,'GIT_NO_LAZY_FETCH':'1'})
                missing=[line.split()[0] for line in result.stdout.splitlines() if line.endswith(' missing')]
                print(record['kind'],record['release_id'],'directory_complete',len(inventory),'missing_blobs',len(missing),flush=True)
                for offset in range(0,len(missing),200):
                    acquire_blob_batch(git,missing[offset:offset+200])
                    if offset%1000==0: print(record['kind'],record['release_id'],'blob_progress',min(offset+200,len(missing)),len(missing),flush=True)
            normalization='git_bytes_autocrlf_false_v1'
            if record.get('archive_normalization') != normalization or not (archive.exists() and zipfile.is_zipfile(archive)):
                partial = archive.with_suffix('.git.part')
                if record['kind']=='docs':
                    archive_args=['archive','--format=zip','--prefix=snapshot/','--output='+str(partial.resolve()),record['commit']]
                    archive_args += sorted({f['path'].split('/')[0] for f in inventory})
                    git(*archive_args)
                else:
                    git('archive','--format=zip','--prefix=snapshot/','--output='+str(partial.resolve()),record['commit'])
                if not zipfile.is_zipfile(partial): raise ValueError('Git archive is invalid')
                partial.replace(archive)
            record = {**record, 'archive_transport':'git_archive', 'inventory_status':'complete',
                      'archive_normalization':normalization,
                      'inventory_file_count':len(inventory), 'submodules':submodules}
        if not archive.exists() or not zipfile.is_zipfile(archive):
            partial=archive.with_suffix('.part')
            for attempt in range(2):
                try:
                    curl = shutil.which('curl.exe') or shutil.which('curl')
                    if curl and transport != 'urllib':
                        subprocess.run([curl,'--fail','--location','--http1.1','--retry','0',
                                        '--connect-timeout','10','--max-time','180','--speed-time','30','--speed-limit','1024',
                                        '--silent','--show-error','--output',str(partial),url],
                                       check=True,timeout=200)
                    else:
                        request=urllib.request.Request(url,headers={'User-Agent':'OpenHarmony-Verified-Delivery'})
                        deadline=time.monotonic()+180
                        with urllib.request.urlopen(request,timeout=30) as response, partial.open('wb') as output:
                            while raw:=response.read(1024*1024):
                                output.write(raw)
                                if time.monotonic()>deadline: raise TimeoutError('Archive download exceeded 180 seconds')
                    if not zipfile.is_zipfile(partial): raise ValueError('Downloaded response is not a ZIP archive')
                    partial.replace(archive)
                    break
                except Exception:
                    if attempt==1: raise
                    time.sleep(2+attempt)
        digest=hashlib.sha256()
        with archive.open('rb') as stream:
            while raw:=stream.read(1024*1024): digest.update(raw)
        folder.mkdir(parents=True,exist_ok=True)
        inventory_path = folder/'inventory.json'
        expected = {f['path']:f['git_blob_sha'] for f in json.loads(inventory_path.read_text(encoding='utf-8'))['files']} if inventory_path.exists() else None
        seen = set()
        ledger=folder/'files.jsonl'
        count, excluded, pointers=0,0,[]
        lfs_expanded=0
        license_evidence=[]
        with zipfile.ZipFile(archive) as zip_file, ledger.with_suffix('.tmp').open('w',encoding='utf-8',newline='\n') as output:
            for member in zip_file.infolist():
                if member.is_dir(): continue
                parts=PurePosixPath(member.filename).parts
                if len(parts)<2 or '..' in parts or PurePosixPath(member.filename).is_absolute(): raise ValueError('Unsafe archive path')
                relative='/'.join(parts[1:])
                if not included(record['kind'],relative): excluded+=1; continue
                if relative in seen: raise ValueError('Duplicate archive member: '+relative)
                seen.add(relative)
                if (member.external_attr >> 16) & 0o170000 == 0o120000:
                    output.write(json.dumps({'path':relative,'status':'symlink_not_materialized'},ensure_ascii=False)+'\n'); continue
                with zip_file.open(member) as input_file:
                    raw=input_file.read()
                if materialize:
                    target=filesystem_path(folder/'content'/Path(*parts[1:]))
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(raw)
                if raw.startswith(b'version https://git-lfs.github.com/spec/v1'): pointers.append(relative)
                blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
                lfs_pointer=None
                if expected is not None and expected.get(relative) != blob:
                    if checkout is not None and relative in expected:
                        if blob_reader is None: blob_reader=GitBlobReader(checkout)
                        candidate=blob_reader.read(expected[relative])
                        if lfs_payload_matches(candidate,raw): lfs_pointer=candidate.decode('ascii'); lfs_expanded+=1
                    if lfs_pointer is None: raise ValueError('Archive differs from fixed Git tree: '+relative)
                if '/' not in relative and relative.lower().startswith(('license','copying','notice')):
                    license_evidence.append({'path':relative,'sha256':hashlib.sha256(raw).hexdigest()})
                output.write(json.dumps({'path':relative,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                                          'git_blob_sha':expected[relative] if lfs_pointer is not None else blob,
                                          'payload_git_blob_sha':blob if lfs_pointer is not None else None,
                                          'lfs_pointer_text':lfs_pointer,'status':'lfs_pointer' if relative in pointers else 'collected'},ensure_ascii=False)+'\n')
                count+=1
        if expected is not None and seen != set(expected): raise ValueError('Archive file coverage differs from fixed Git tree')
        ledger.with_suffix('.tmp').replace(ledger)
        licenses=[x['path'] for x in license_evidence]
        clean_record = {k:v for k,v in record.items() if k != 'error'}
        result={**clean_record,'status':'collected','body_status':'complete_with_unresolved_dependencies' if pointers or record.get('submodules') else 'complete',
                'archive_url':url,'archive_sha256':digest.hexdigest(),
                'archive_size':archive.stat().st_size,'content_root':str(folder/'content') if materialize else None,
                'body_storage':'archive_and_files' if materialize else 'verified_archive',
                'ledger':str(ledger),'file_count':count,'excluded_files':excluded,
                'lfs_pointers':pointers,'lfs_expanded_files_verified':lfs_expanded,'license_files':licenses,'license_evidence':license_evidence,
                'collected_at':datetime.now(timezone.utc).isoformat(),
                'performance':{'elapsed_seconds':round(time.perf_counter()-started,3),'verified_archive_reused':False}}
        save_collection_receipt(result,root)
        write_json(root/'verified-results'/f'{source_id}.json',result)
        return result
    except Exception as exc:
        error = (exc.stderr or str(exc)) if isinstance(exc,subprocess.CalledProcessError) else str(exc)
        inventory_path=folder/'inventory.json'
        directory = json.loads(inventory_path.read_text(encoding='utf-8')) if inventory_path.exists() else None
        return {**record,'status':'collection_failed','body_status':'verification_failed' if archive.exists() else 'unavailable',
                'inventory_status':'complete' if directory and directory.get('commit')==record['commit'] else 'unavailable',
                'inventory_file_count':len(directory['files']) if directory else None,
                'error':error,'archive_url':url,
                'performance':{'elapsed_seconds':round(time.perf_counter()-started,3),'verified_archive_reused':False}}
    finally:
        if blob_reader is not None: blob_reader.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT/'data/delivery')
    parser.add_argument('--lock-only',action='store_true')
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--kinds', nargs='+', choices=list(REPOS), default=list(REPOS))
    parser.add_argument('--transport', choices=['auto','archive','git','git-batches','urllib'], default='auto')
    parser.add_argument('--reverify',action='store_true',help='Force full Git-tree and per-file validation even with a matching verification receipt')
    parser.add_argument('--releases', nargs='+', help='Optional exact release_id filter for resuming one source group')
    parser.add_argument('--lock',type=Path,help='Import the published fixed source lock in a fresh data root')
    args=parser.parse_args(); manifest=args.root/'sources.json'
    if manifest.exists():
        records=json.loads(manifest.read_text(encoding='utf-8'))['sources']
        if args.lock:
            pinned=import_source_lock(args.lock,args.kinds)
            existing={r.get('source_id'):r for r in records}
            if any(r['source_id'] not in existing or existing[r['source_id']]['commit']!=r['commit'] for r in pinned):
                raise ValueError('Existing data root differs from source lock; choose a new --root')
    else:
        records=[]
        if args.lock: records=import_source_lock(args.lock,args.kinds)
        else:
            with ThreadPoolExecutor(max_workers=4) as pool:
                for future in as_completed([pool.submit(resolve_repo,k,r) for k,r in REPOS.items() if k in args.kinds]):
                    records.extend(future.result())
        write_json(manifest,{'schema_version':1,'sources':records})
    print('Locked sources:',len(records),flush=True)
    if args.lock_only:return
    records=[recover_collection_record(r,args.root) if r['kind'] in args.kinds and r.get('source_id') else r for r in records]
    with ThreadPoolExecutor(max_workers=max(1,min(args.workers,4))) as pool:
        futures={pool.submit(collect,r,args.root,('git-batches' if r['kind'] in ('docs','samples') else 'archive') if args.transport=='auto' else args.transport,args.reverify):i for i,r in enumerate(records) if r['kind'] in args.kinds and (not args.releases or r['release_id'] in args.releases)}
        for future in as_completed(futures):
            record=future.result(); records[futures[future]]=record
            write_json(manifest,{'schema_version':1,'sources':records})
            print(record['kind'],record['release_id'],record['status'],record.get('file_count',record.get('error','')),flush=True)
    failures=[r for r in records if r['kind'] in args.kinds and (not args.releases or r['release_id'] in args.releases) and r['status']!='collected']
    print('Collection finished; unresolved/failed:',len(failures),flush=True)
    if failures: raise SystemExit(2)

if __name__=='__main__': main()
