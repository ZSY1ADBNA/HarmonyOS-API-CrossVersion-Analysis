"""Verify owned sample imports and existing web routes against a real isolated database."""
import hashlib
import json
from pathlib import Path
import runpy
import sys
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/delivery/isolated-neo4j'
sys.path.insert(0,str(BASE/'packages'))
from neo4j import GraphDatabase


def load(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def samples():
    batch=ROOT/'data/delivery/structured/yu-declaration-check';manifest=load(batch/'current.json')
    item=manifest['candidates'];path=(batch/item['path']).resolve()
    if not path.is_relative_to(batch.resolve()) or sha(path)!=item['sha256']:raise ValueError('Candidate generation mismatch')
    candidates=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    sdk=load(ROOT/'docs/official-data-delivery/public-sdk-4.1-verification.json')
    compiled=load(ROOT/'docs/official-data-delivery/sdk-build-probe.json')
    if not sdk['passed'] or not compiled['compile_task_succeeded'] or compiled['sdk_version']!='4.1.7.5':raise ValueError('Sample build evidence not verified')
    project=Path('C:/Windows/Temp/openharmony-sdk-probe-v4')
    if not all(sha(project/x['path'])==x['sha256'] for x in compiled['source_files']+compiled['compiled_artifacts']):raise ValueError('Actual build evidence differs')
    lock=load(ROOT/'docs/official-data-delivery/sample-declaration-source-lock.json')
    origin=next(x for x in lock['sources'] if x['kind']=='docs' and x['release_id']=='OpenHarmony-4.1-Release')
    checked_archives=set()
    selected=[]
    for name in ['fontSize','channelLayout']:
        hits=[x for x in candidates if x['name']==name and x['evidence']['release_id']=='OpenHarmony-4.1-Release']
        if len(hits)!=1:raise ValueError('Ambiguous documentary sample')
        fact=hits[0];e=fact['evidence']
        if any(e.get(k)!=origin[k] for k in ['source_id','platform','release_id','repository','commit']):raise ValueError('Document origin identity mismatch')
        proof=next(x for x in sdk['facts'] if x['name']==name and x['present'])['declaration']
        archive=ROOT/'data/delivery/archives'/(e['source_id']+'.zip')
        if e['source_id'] not in checked_archives:
            if sha(archive)!=origin['archive_sha256']:raise ValueError('Pinned document archive differs')
            checked_archives.add(e['source_id'])
        expected_path={'fontSize':'ets/component/button.d.ts','channelLayout':'ets/api/@ohos.multimedia.audio.d.ts'}[name]
        if proof['evidence']['path']!=expected_path or sha(Path('C:/Windows/Temp/openharmony-sdk-4.1/11')/expected_path)!=proof['evidence']['file_sha256']:raise ValueError('Installed public declaration differs')
        with zipfile.ZipFile(archive) as z:
            members=[n for n in z.namelist() if n.endswith('/'+e['path'])]
            if len(members)!=1 or hashlib.sha256(z.read(members[0])).hexdigest()!=e['source_sha256']:raise ValueError('Original document differs')
        selected.append({'fact':fact,'sdk':proof})
    return selected


def import_samples(tx,items):
    for item in items:
        f=item['fact'];e=f['evidence'];s=item['sdk']
        if e['release_id']!='OpenHarmony-4.1-Release' or s['name']!=f['name'] or s['sdk_public_status']!='present_in_verified_public_sdk_package':raise ValueError('Invalid sample version or declaration')
    for item in items:
        f=item['fact'];e=f['evidence'];s=item['sdk'];owner=s['owner']
        module='@ohos.multimedia.audio' if f['name']=='channelLayout' else 'ArkUI globals'
        module_id='delivery:API4.1:module:'+module
        parent_id='delivery:API4.1:'+module+':'+owner
        member_id='delivery:'+f['record_id']
        common={'sdk_version':'API4.1','release_id':e['release_id'],'api_level':11,'module':module,
                'source_url':e['repository']+'/blob/'+e['commit']+'/'+e['path']+'#L'+str(f['line']),
                'source_commit':e['commit'],'source_path':e['path'],'source_line':f['line'],
                'sdk_package_version':'4.1.7.5','sdk_verification_status':'sample_verified','compile_verification_status':'sample_passed',
                'api_identity_status':'documentary_candidate','since':'','batch_id':'YU-ISOLATE-20261013',
                'source_sha256':e['source_sha256'],'source_correction_status':'history_verified' if f.get('correction') else 'not_required',
                'evidence_json':json.dumps({'document_candidate':f,'published_sdk_declaration':s},ensure_ascii=False)}
        nodes=[('Module',module_id,{**common,'name':module,'type':'module'}),
               ('Class' if owner=='ButtonAttribute' else 'Interface',parent_id,{**common,'name':owner,'type':'class' if owner=='ButtonAttribute' else 'interface','description':owner}),
               ('Method' if f['name']=='fontSize' else 'Property',member_id,{**common,'name':f['name'],'type':'method' if f['name']=='fontSize' else 'property','description':f.get('description',''),'parent_name':owner,'document_owner':f['owner'],'signature':s['signature'],'return_type':s['declared_type'] if f['name']=='fontSize' else None,'property_type':s['declared_type'] if f['name']=='channelLayout' else None})]
        for label,uid,props in nodes:
            if label not in ['Module','Class','Interface','Method','Property']:raise ValueError('Unexpected test label')
            tx.run('MERGE (n:DeliveryCandidate:'+label+' {uid:$uid}) SET n += $props',uid=uid,props=props).consume()
        tx.run('MATCH (m:DeliveryCandidate {uid:$member}), (p:DeliveryCandidate {uid:$parent}) MERGE (m)-[:HAS_PARENT]->(p)',member=member_id,parent=parent_id).consume()
        tx.run('MATCH (p:DeliveryCandidate {uid:$parent}), (m:DeliveryCandidate {uid:$module}) MERGE (p)-[:BELONGS_TO_MODULE]->(m)',parent=parent_id,module=module_id).consume()


def main():
    private=load(Path('C:/Windows/Temp/openharmony-neo4j-test-v4/connection-private.json'))
    if private['uri']!='bolt://127.0.0.1:17687' or private['version']!='5.26.32':raise ValueError('Isolation target mismatch')
    items=samples();checks={};issues=[]
    with GraphDatabase.driver(private['uri'],auth=(private['username'],private['password']),max_transaction_retry_time=0) as driver:
        with driver.session(database='neo4j') as session:
            versions=session.run('CALL dbms.components() YIELD versions RETURN versions').single()['versions']
            if '5.26.32' not in versions:raise ValueError('Unexpected database version')
            unrelated=session.run('MATCH (n) WHERE NOT n:DeliveryCandidate AND NOT n:DeliverySentinel RETURN count(n) AS total').single()['total']
            if unrelated:raise ValueError('Non-test data found; no import performed')
            session.run('CREATE CONSTRAINT yu_delivery_candidate_uid IF NOT EXISTS FOR (n:DeliveryCandidate) REQUIRE n.uid IS UNIQUE').consume()
            session.run('CREATE CONSTRAINT yu_delivery_sentinel_uid IF NOT EXISTS FOR (n:DeliverySentinel) REQUIRE n.uid IS UNIQUE').consume()
            session.run("MERGE (n:DeliverySentinel {uid:'delivery:sentinel'}) ON CREATE SET n.value='preserve-me'").consume()
            session.execute_write(import_samples,items)
            count=session.run('MATCH (n:DeliveryCandidate) RETURN count(n) AS total').single()['total']
            session.execute_write(import_samples,items)
            checks['repeat_import_same_count']=count==6 and session.run('MATCH (n:DeliveryCandidate) RETURN count(n) AS total').single()['total']==count
            checks['sentinel_preserved']=session.run("MATCH (n:DeliverySentinel {uid:'delivery:sentinel'}) RETURN n.value AS value").single()['value']=='preserve-me'
            wrong=json.loads(json.dumps(items));wrong[0]['fact']['evidence']['release_id']='wrong-release'
            try:session.execute_write(import_samples,wrong)
            except ValueError:checks['wrong_version_rejected']=True
            else:checks['wrong_version_rejected']=False
            checks['failed_import_preserves_count']=session.run('MATCH (n:DeliveryCandidate) RETURN count(n) AS total').single()['total']==count
            def injected_failure(tx):
                tx.run("MERGE (n:DeliveryCandidate {uid:'delivery:rollback-probe'}) SET n.batch_id='YU-ISOLATE-20261013'").consume()
                raise RuntimeError('Expected isolated rollback probe')
            try:session.execute_write(injected_failure)
            except RuntimeError:pass
            checks['transaction_rollback_verified']=session.run("MATCH (n {uid:'delivery:rollback-probe'}) RETURN count(n) AS total").single()['total']==0

        with patch.object(GraphDatabase,'driver',return_value=driver):web=runpy.run_path(str(ROOT/'app.py'))
        client=web['app'].test_client()
        page=client.get('/');checks['existing_page_rendered']=page.status_code==200
        overview=client.get('/api/overview').get_json()['API4.1']
        checks['overview_types_match']=overview['types'].get('Class')==1 and overview['types'].get('Interface')==1 and overview['types'].get('Method')==1 and overview['types'].get('Property')==1
        payload=client.get('/api/graph?version=API4.1&keyword=ButtonAttribute').get_json()
        checks['known_field_returned']=any(n['label']=='fontSize' for n in payload['nodes'])
        child=next(n for n in payload['nodes'] if n['label']=='fontSize')
        checks['source_returned_by_existing_route']=bool(child.get('source_url'))
        unknown=client.get('/api/graph?version=API4.1&keyword=NO_SUCH_SAMPLE_7e21').get_json()
        checks['unknown_keyword_returns_no_nodes']=not unknown['nodes']
        member=client.get('/api/graph?version=API4.1&keyword=fontSize').get_json()
        checks['member_keyword_returned']=any(n['label']=='fontSize' for n in member['nodes'])
        missing_module=client.get('/api/graph?version=API4.1&module=NO_SUCH_MODULE_7e21').get_json()
        checks['unknown_module_returns_no_nodes']=not missing_module['nodes']
        checks['invalid_limit_rejected']=client.get('/api/graph?version=API4.1&max_parents=wrong').status_code==400
        checks['sample_verification_status_retained']=child.get('api_identity_status')=='documentary_candidate' and child.get('compile_verification_status')=='sample_passed'
        other=client.get('/api/graph?version=API5.1').get_json()
        checks['version_filter_no_cross_release']=not other['nodes']
    for key,value in checks.items():
        if not value:issues.append(key)
    report={'scope':'Real isolated Neo4j imports and existing Flask HTTP route tests; browser JavaScript not executed',
            'database_version':'5.26.32','driver_version':'5.28.2','flask_version':'3.1.2','sample_count':2,
            'checks':checks,'passed':all(checks.values()),'issues':issues,'browser_ui_verified':False,
            'shared_database_updated':False,'formal_api_identity_verified':False}
    (ROOT/'docs/official-data-delivery/isolated-graph-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report))
    if not report['passed']:raise SystemExit(2)


if __name__=='__main__':main()
