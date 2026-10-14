"""Audit only two pinned legacy records and enrich existing isolated candidates."""
import ast
import hashlib
import json
from pathlib import Path
import socket
import urllib.request
from verify_isolated_graph import ROOT, BASE, load, samples, GraphDatabase
from verify_sample_declarations import inspect, match_declaration

PINNED = {'button': 'e4bde4da520a6341fb671b25f4b28b5fde6511fb',
          'audio': 'fdde162a8d34efc2ef6c511649dda003b9a0f8a4'}


def blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def identity(module, declaration):
    # Local sample identity; not a proposed team-wide key migration.
    return json.dumps(['OpenHarmony', 'OpenHarmony-4.1-Release', 11,
                       '4.1.7.5', module, declaration['owner'],
                       declaration['kind'], declaration['name'],
                       declaration['signature']], ensure_ascii=False, separators=(',', ':'))


def audit():
    legacy = {}
    for key, expected in PINNED.items():
        raw = (BASE/'mapping-baseline'/f'{key}.json').read_bytes()
        if blob(raw) != expected:
            raise ValueError('Pinned legacy input differs: '+key)
        legacy[key] = json.loads(raw)['�ڵ�']
    tree = ast.parse((ROOT/'_run_import.py').read_text(encoding='utf-8'))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'make_uid')
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<pure make_uid>', 'exec'), namespace)
    uid = namespace['make_uid']
    checks = {
        'legacy_button_only_module': len(legacy['button']) == 1 and legacy['button'][0]['����'] == 'module',
        'legacy_type_collision_reproduced': uid('method', 'same', 'API4.1', 'Owner') == uid('property', 'same', 'API4.1', 'Owner'),
        'name_map_scope_loss_static': 'name_to_uid[props["name"]] = props["uid"]' in ast.get_source_segment((ROOT/'_run_import.py').read_text(encoding='utf-8'), next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'batch_import_file')),
    }
    selected = samples()
    records = []
    for item in selected:
        d = item['sdk']; name = d['name']
        module = 'ArkUI globals' if name == 'fontSize' else '@ohos.multimedia.audio'
        # Verify exact declaration and enclosing scope in the fingerprint-checked SDK.
        text = (Path('C:/Windows/Temp/openharmony-sdk-4.1/11')/d['evidence']['path']).read_text(encoding='utf-8')
        parsed = inspect([{'id':d['evidence']['path'], 'path':d['evidence']['path'], 'text':text}])
        actual = match_declaration(parsed[d['evidence']['path']], d['owner'], name, d['evidence'])
        checks[name+'_parsed_declaration'] = bool(actual and all(actual[k] == d[k] for k in ['signature','optional','kind','declared_type']))
        checks[name+'_exact_signature'] = text.splitlines()[d['line']-1].strip() == d['signature']
        checks[name+'_owner_scope'] = ('declare class ButtonAttribute' in text if name == 'fontSize' else 'declare namespace audio' in text and 'interface AudioStreamInfo' in text and 'export default audio' in text)
        old = [n for n in legacy['button' if name == 'fontSize' else 'audio'] if n.get('����') == name and n.get('�ϼ�') == d['owner']]
        if name == 'channelLayout':
            checks['legacy_audio_unique_match'] = len(old) == 1
            checks['legacy_audio_type_matches'] = len(old) == 1 and old[0].get('��������') == d['declared_type']
        records.append({'name': name, 'module': module, 'owner': d['owner'],
                        'signature': d['signature'], 'optional': d['optional'],
                        'sample_identity': identity(module, d), 'sdk_evidence': d['evidence'],
                        'legacy_matches': old, 'legacy_status': 'missing_declaration' if not old else 'incomplete_metadata',
                        'candidate_uid': 'delivery:'+item['fact']['record_id']})
    checks['module_sensitive_identity'] = identity('A', selected[0]['sdk']) != identity('B', selected[0]['sdk'])
    altered = dict(selected[0]['sdk'], signature='fontSize(value: number): ButtonAttribute;')
    checks['overload_sensitive_identity'] = identity('A', selected[0]['sdk']) != identity('A', altered)
    if not all(checks.values()):
        raise ValueError('Audit checks failed: '+str([k for k,v in checks.items() if not v]))
    return records, checks


def main():
    records, checks = audit()
    private = load(Path('C:/Windows/Temp/openharmony-neo4j-test-v4/connection-private.json'))
    if private['uri'] != 'bolt://127.0.0.1:17687' or private['version'] != '5.26.32':
        raise ValueError('Isolation target mismatch')
    with GraphDatabase.driver(private['uri'], auth=(private['username'],private['password']), max_transaction_retry_time=0) as driver:
        with driver.session(database='neo4j') as session:
            if session.run('CALL dbms.components() YIELD versions RETURN versions').single()['versions'] != ['5.26.32']:
                raise ValueError('Unexpected database version')
            before = session.run('MATCH (n) RETURN count(n) AS count').single()['count']
            snapshot = session.run('MATCH (n:DeliverySentinel) RETURN properties(n) AS props').data()
            def repair(tx):
                for r in records:
                    node = tx.run('MATCH (n:DeliveryCandidate {uid:$uid}) RETURN properties(n) AS props', uid=r['candidate_uid']).single()
                    if not node or node['props'].get('batch_id') != 'YU-ISOLATE-20261013' or node['props'].get('signature') != r['signature'] or node['props'].get('module') != r['module']:
                        raise ValueError('Owned candidate baseline differs')
                    tx.run('MATCH (n:DeliveryCandidate {uid:$uid}) SET n.sample_identity=$identity, n.optional=$optional, n.mapping_verification_status=$status', uid=r['candidate_uid'], identity=r['sample_identity'], optional=r['optional'], status='two_samples_verified_in_public_sdk_4.1.7.5').consume()
            session.execute_write(repair)
            session.execute_write(repair)
            checks['no_new_nodes_repeat_repair'] = session.run('MATCH (n) RETURN count(n) AS count').single()['count'] == before
            checks['sentinel_properties_preserved'] = snapshot == session.run('MATCH (n:DeliverySentinel) RETURN properties(n) AS props').data()
            for r in records:
                row = session.run('MATCH (n:DeliveryCandidate {uid:$uid})-[:HAS_PARENT]->(p)-[:BELONGS_TO_MODULE]->(m) RETURN properties(n) AS props,p.name AS owner,m.name AS module', uid=r['candidate_uid']).single()
                checks[r['name']+'_real_mapping'] = bool(row and row['props']['optional'] == r['optional'] and row['props']['sample_identity'] == r['sample_identity'] and row['owner'] == r['owner'] and row['module'] == r['module'])
    for port in [17687,17474,15051]:
        with socket.create_connection(('127.0.0.1',port), timeout=3):
            checks['existing_port_'+str(port)] = True
    with urllib.request.urlopen('http://127.0.0.1:15051/api/graph?version=API4.1&keyword=channelLayout', timeout=10) as response:
        payload = json.load(response)
        checks['existing_http_member_source'] = any(n['label'] == 'channelLayout' and n.get('source_url') for n in payload['nodes'])
    report = {'batch_id':'YU-MAPPING-20261014','scope':'Only two local sample identities; no global identity migration',
              'legacy_commit':'3ff52826efbf50becb47372d207929e42f4d9a13','legacy_blobs':PINNED,
              'records':records,'checks':checks,'passed':all(checks.values()),
              'shared_database_updated':False,'device_runtime_verified':False,'other_releases_verified':False,
              'browser_ui_retested':False,'candidate_status_preserved':True}
    (ROOT/'docs/official-data-delivery/sample-mapping-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'passed':report['passed'],'checks':checks}))
    if not report['passed']: raise SystemExit(2)


if __name__ == '__main__':
    main()
