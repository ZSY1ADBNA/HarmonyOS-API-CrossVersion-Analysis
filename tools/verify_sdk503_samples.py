"""Verify two API15 published declarations and rehearse a two-release comparison."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import zipfile
import time
from collect_public_sdk import digest
from collect_official_sources import write_json
from verify_sample_declarations import inspect, match_declaration, read_file, git_blob
from verify_isolated_graph import ROOT, BASE, load, samples, GraphDatabase
from rehearse_sample_bridge import graph_snapshot

EXPECTED = '17cabf4aa94b02d9ee7366f49988eee549edbf6666a0743974aa5e1562f4cf88'
SIZE = 4563988878
MEMBER = 'ohos-sdk/windows/ets-windows-x64-5.0.3.135-Release.zip'
TARGETS = [('fontSize','ButtonAttribute','ets/component/button.d.ts','api/@internal/component/ets/button.d.ts','ArkUI globals'),
           ('channelLayout','AudioStreamInfo','ets/api/@ohos.multimedia.audio.d.ts','api/@ohos.multimedia.audio.d.ts','@ohos.multimedia.audio')]
BATCH = 'YU-SDK503-20261014'


def published_component(archive, timings=None):
    timings = timings if timings is not None else {}
    started = time.monotonic()
    if archive.stat().st_size != SIZE or digest(archive) != EXPECTED:
        raise ValueError('API15 official archive fingerprint differs')
    timings['archive_fingerprint_seconds']=round(time.monotonic()-started,3)
    cache=archive.parent/'windows-5.0.3-ets.zip'
    receipt_path=archive.parent/'windows-5.0.3-ets-cache.json'
    if cache.exists() or receipt_path.exists():
        if not cache.exists() or not receipt_path.exists():
            raise ValueError('Incomplete component cache; existing files preserved')
        receipt=load(receipt_path)
        if receipt.get('archive_sha256')!=EXPECTED or receipt.get('member')!=MEMBER or digest(cache)!=receipt.get('component_sha256'):
            raise ValueError('Component cache differs; preserved without overwrite')
        timings['component_cache_reused']=True
        return cache.read_bytes()
    payload = None
    started=time.monotonic()
    with tarfile.open(archive,'r|gz',bufsize=1024*1024) as tar:
        for member in tar:
            if member.name == MEMBER:
                if payload is not None or not member.isfile() or not 0 < member.size <= 128*1024*1024:
                    raise ValueError('Unexpected or duplicate API15 ETS component')
                payload = tar.extractfile(member).read()
    if payload is None:
        raise ValueError('API15 Windows ETS component missing')
    with cache.open('xb') as f:f.write(payload)
    write_json(receipt_path,{'archive_sha256':EXPECTED,'member':MEMBER,'component_sha256':hashlib.sha256(payload).hexdigest()})
    timings['component_scan_seconds']=round(time.monotonic()-started,3)
    timings['component_cache_reused']=False
    return payload


def declarations(payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if len(z.namelist()) != len(set(z.namelist())):
            raise ValueError('Duplicate ETS ZIP entry')
        meta = json.loads(z.read('ets/oh-uni-package.json'))
        if meta.get('version') != '5.0.3.135' or str(meta.get('apiVersion')) != '15' or meta.get('releaseType') != 'Release':
            raise ValueError('API15 published metadata differs')
        files = [{'id':p,'path':p,'text':z.read(p).decode('utf-8-sig')} for p in dict.fromkeys(t[2] for t in TARGETS)]
        parsed = inspect(files)
        if any(v['diagnostics'] for v in parsed.values()):
            raise ValueError('Selected API15 published files have parse diagnostics')
        results = []
        for name,owner,path,_,module in TARGETS:
            evidence = {'platform':'OpenHarmony','release_id':'OpenHarmony-5.0.3-Release','api_level':15,
                        'sdk_version':'5.0.3.135','archive_sha256':EXPECTED,'component_member':MEMBER,
                        'component_sha256':hashlib.sha256(payload).hexdigest(),'path':path,
                        'file_sha256':hashlib.sha256(z.read(path)).hexdigest()}
            d = match_declaration(parsed[path],owner,name,evidence)
            if d is None:
                raise ValueError('Target published API15 declaration missing')
            d['sdk_public_status']='present_in_verified_public_sdk_package'
            d['scope']='Two declarations in verified Windows Public SDK 5.0.3.135/API15; no compile or device claim'
            results.append({'name':name,'owner':owner,'module':module,'declaration':d})
        audio = next(f['text'] for f in files if f['path']==TARGETS[1][2])
        if 'declare namespace audio' not in audio or 'export default audio;' not in audio:
            raise ValueError('Published audio export scope differs')
    return meta, results


def source_checks(results):
    lock = load(ROOT/'docs/official-data-delivery/sample-declaration-source-lock.json')
    source = next(s for s in lock['sources'] if s['kind']=='arkts_api' and s['release_id']=='OpenHarmony-5.0.3-Release')
    archive = ROOT/'data/delivery/archives'/(source['source_id']+'.zip')
    if digest(archive) != source['archive_sha256']:
        raise ValueError('Fixed API15 source archive differs')
    ledger = {e['path']:e for e in map(json.loads,(ROOT/'data/delivery/sources'/source['source_id']/'files.jsonl').read_text(encoding='utf-8').splitlines())}
    files=[];proofs={}
    for _,_,_,path,_ in TARGETS:
        text,proof=read_file(source,ledger,archive,path)
        files.append({'id':path,'path':path,'text':text});proofs[path]=proof
    parsed=inspect(files);checks={}
    for item,(_,owner,_,path,_) in zip(results,TARGETS):
        d=match_declaration(parsed[path],owner,item['name'],proofs[path])
        item['fixed_source_declaration']=d
        checks[item['name']+'_fixed_source_signature_matches']=bool(d and all(d[k]==item['declaration'][k] for k in ['signature','optional','kind','declared_type','parameters']))
    return checks


def comparison(old,new):
    keys=['signature','optional','kind','declared_type','parameters','metadata','ancestor_metadata']
    return {k:{'old':old[k],'new':new[k],'equal':old[k]==new[k]} for k in keys}


def database_probe(old,new):
    private=load(Path('C:/Windows/Temp/openharmony-neo4j-test-v4/connection-private.json'))
    if private['uri']!='bolt://127.0.0.1:17687' or private['version']!='5.26.32':
        raise ValueError('Wrong isolated target')
    checks={}
    with GraphDatabase.driver(private['uri'],auth=(private['username'],private['password']),max_transaction_retry_time=0) as driver:
        with driver.session(database='neo4j') as session:
            if session.run('CALL dbms.components() YIELD versions RETURN versions').single()['versions']!=['5.26.32']:
                raise ValueError('Wrong database version')
            before=graph_snapshot(session)
            with session.begin_transaction() as tx:
                for version,items in [('API4.1',old),('API5.0',new)]:
                    for item in items:
                        d=item['declaration'];uid=BATCH+':'+version+':'+item['name']
                        props={'sdk_version':version,'release_id':'OpenHarmony-4.1-Release' if version=='API4.1' else 'OpenHarmony-5.0.3-Release',
                               'api_level':11 if version=='API4.1' else 15,'name':item['name'],'owner':d['owner'],
                               'signature':d['signature'],'optional':d['optional'],'module':item['module'],
                               'sdk_package_version':d['evidence']['sdk_version'],'batch_id':BATCH}
                        tx.run('MERGE (n:DeliverySDKComparisonProbe {uid:$uid}) SET n += $props',uid=uid,props=props).consume()
                        tx.run('MERGE (n:DeliverySDKComparisonProbe {uid:$uid}) SET n += $props',uid=uid,props=props).consume()
                checks['repeat_probe_four_nodes']=tx.run('MATCH (n:DeliverySDKComparisonProbe {batch_id:$batch}) RETURN count(n) AS count',batch=BATCH).single()['count']==4
                for version in ['API4.1','API5.0']:
                    rows=tx.run('MATCH (n:DeliverySDKComparisonProbe {batch_id:$batch,sdk_version:$version}) RETURN n.name AS name,n.api_level AS level,n.sdk_package_version AS sdk',batch=BATCH,version=version).data()
                    checks[version+'_version_filter']=len(rows)==2 and all(r['level']==(11 if version=='API4.1' else 15) for r in rows)
                rows=tx.run('MATCH (a:DeliverySDKComparisonProbe {batch_id:$batch,sdk_version:"API4.1"}),(b:DeliverySDKComparisonProbe {batch_id:$batch,sdk_version:"API5.0"}) WHERE a.name=b.name AND a.owner=b.owner AND a.module=b.module RETURN a.name AS name,a.signature AS old,b.signature AS new,a.optional AS old_optional,b.optional AS new_optional',batch=BATCH).data()
                checks['both_signature_pairs_queryable']=len(rows)==2 and {r['name'] for r in rows}=={'fontSize','channelLayout'}
                checks['unknown_release_empty']=tx.run('MATCH (n:DeliverySDKComparisonProbe {batch_id:$batch,sdk_version:"API6.1"}) RETURN count(n) AS count',batch=BATCH).single()['count']==0
                tx.rollback()
            checks['entire_existing_graph_preserved']=graph_snapshot(session)==before
    return checks


def main():
    base=ROOT/'data/delivery/sdk-packages'
    note=(base/'release-notes-5.0.3-original.md').read_bytes()
    if git_blob(note)!='efc2fa98c712936b537919148f740369a9e5ff2d':
        raise ValueError('Pinned official release note differs')
    if not all(x in note.decode('utf-8') for x in ['5.0.3.135','API Version 15','ohos-sdk-windows_linux-public.tar.gz']):
        raise ValueError('Release note mapping differs')
    timings={}
    meta,new=declarations(published_component(base/'ohos-5.0.3-public.tar.gz',timings))
    checks=source_checks(new)
    old=[{'name':i['sdk']['name'],'module':'ArkUI globals' if i['sdk']['name']=='fontSize' else '@ohos.multimedia.audio','declaration':i['sdk']} for i in samples()]
    differences=[{'name':n['name'],'fields':comparison(o['declaration'],n['declaration'])} for o,n in zip(old,new)]
    checks.update(database_probe(old,new))
    report={'batch_id':BATCH,'component_metadata':meta,'release_note':{'repository':'https://github.com/openharmony/docs',
            'commit':'f3686c4ca417af4ca8f8e44f64f44d99da50dc69','path':'zh-cn/release-notes/OpenHarmony-v5.0.3-release.md',
            'git_blob_sha':git_blob(note),'sha256':hashlib.sha256(note).hexdigest(),
            'scope':'Separately pinned release mapping evidence, not the historical API docs snapshot'},
            'archive_sha256':EXPECTED,'archive_size':SIZE,'facts':new,'comparisons':differences,'timings':timings,
            'checks':checks,'passed':all(checks.values()),'sdk503_compiled':False,'device_runtime_verified':False,
            'shared_database_updated':False,'browser_ui_retested':False,'probe_writes_rolled_back':True}
    (ROOT/'docs/official-data-delivery/public-sdk-5.0.3-samples.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'passed':report['passed'],'checks':checks,'comparison_equal':[{d['name']:{k:v['equal'] for k,v in d['fields'].items()}} for d in differences]}))
    if not report['passed']:raise SystemExit(2)


if __name__=='__main__':main()
