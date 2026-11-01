"""Two-sample additive bridge rehearsal; all probe writes are rolled back."""
import copy
import hashlib
import json
from pathlib import Path
from verify_sample_mapping import audit, blob, PINNED
from verify_isolated_graph import ROOT, BASE, load, GraphDatabase

BATCH = 'YU-BRIDGE-20261014'
RELEASE = 'OpenHarmony-4.1-Release'


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def plan_bridge(records, legacy, release=RELEASE):
    """Refuse conflicting evidence; preserve old records via separate shadow nodes."""
    if release != RELEASE or {r['name'] for r in records} != {'fontSize','channelLayout'} or len(records) != 2:
        raise ValueError('Unsupported rehearsal scope')
    plan = []
    for record in records:
        kind = 'method' if record['name'] == 'fontSize' else 'property'
        expected_type = 'ButtonAttribute' if kind == 'method' else 'AudioChannelLayout'
        named = [n for n in legacy[record['name']] if n.get('名称') == record['name']]
        selected = [n for n in named if n.get('上级') == record['owner']]
        if named and not selected:
            raise ValueError('Legacy owner conflicts; absence not established')
        if len(selected) > 1:
            raise ValueError('Ambiguous legacy records')
        old = selected[0] if selected else None
        if old:
            if old.get('类型') != kind or old.get('版本') != 'API4.1':
                raise ValueError('Legacy kind or release conflicts')
            if old.get('所属模块') not in (None, '', '未知模块', record['module']):
                raise ValueError('Legacy module conflicts')
            if old.get('签名') not in (None, '', record['signature']):
                raise ValueError('Legacy signature conflicts')
            if 'optional' in old and (type(old['optional']) is not bool or old['optional'] != record['optional']):
                raise ValueError('Legacy optionality conflicts')
            type_key = '返回值' if kind == 'method' else '属性类型'
            if old.get(type_key) != expected_type:
                raise ValueError('Legacy declared type conflicts')
        plan.append({'name':record['name'], 'action':'add_shadow_and_link_legacy' if old else 'add_shadow_missing_legacy',
                     'identity':record['sample_identity'], 'candidate_uid':record['candidate_uid'],
                     'module':record['module'], 'owner':record['owner'], 'kind':kind,
                     'signature':record['signature'], 'optional':record['optional'],
                     'legacy':copy.deepcopy(old), 'legacy_fingerprint':fingerprint(old) if old else None})
    return plan


def graph_snapshot(session):
    nodes = session.run('MATCH (n) RETURN labels(n) AS labels,properties(n) AS props').data()
    edges = session.run('MATCH (a)-[r]->(b) RETURN a.uid AS start,type(r) AS type,b.uid AS end,properties(r) AS props').data()
    def stable(rows):
        return sorted(rows, key=lambda row:json.dumps(row,sort_keys=True,ensure_ascii=False))
    for n in nodes:
        n['labels'].sort()
    return fingerprint({'nodes':stable(nodes),'edges':stable(edges)})


def apply_probe(tx, plan, fail_after_first=False):
    # Probe label and keys are separate from existing candidates and all legacy UIDs.
    for index, p in enumerate(plan):
        uid = BATCH+':shadow:'+p['name']
        expected_uid = BATCH+':legacy:'+p['name']
        if p['legacy'] is not None:
            row = tx.run('MATCH (n:DeliveryBridgeProbe {uid:$uid}) RETURN n.legacy_json AS body', uid=expected_uid).single()
            if not row or fingerprint(json.loads(row['body'])) != p['legacy_fingerprint']:
                raise ValueError('Legacy baseline changed before write')
        source = tx.run('MATCH (n:DeliveryCandidate {uid:$uid}) RETURN properties(n) AS props', uid=p['candidate_uid']).single()
        if not source or any(source['props'].get(k) != p[v] for k,v in [('sample_identity','identity'),('signature','signature'),('optional','optional'),('module','module'),('parent_name','owner'),('type','kind')]):
            raise ValueError('Verified candidate baseline changed')
        props = {k:p[k] for k in ['name','module','owner','kind','signature','optional','identity']}
        props['batch_id'] = BATCH
        tx.run('MERGE (n:DeliveryBridgeProbe {uid:$uid}) SET n += $props', uid=uid,props=props).consume()
        if p['legacy'] is not None:
            tx.run('MATCH (s:DeliveryBridgeProbe {uid:$s}),(o:DeliveryBridgeProbe {uid:$o}) MERGE (s)-[:LEGACY_RECORD_EVIDENCE]->(o)', s=uid,o=expected_uid).consume()
        if fail_after_first and index == 0:
            raise RuntimeError('Injected failure after first real write')


def main():
    records, _ = audit()
    legacy = {}
    for name, key in [('fontSize','button'),('channelLayout','audio')]:
        raw = (BASE/'mapping-baseline'/f'{key}.json').read_bytes()
        if blob(raw) != PINNED[key]:
            raise ValueError('Legacy pinned file changed')
        legacy[name] = json.loads(raw)['节点']
    plan = plan_bridge(records,legacy)
    checks = {'fontSize_missing_legacy_additive':plan[0]['action']=='add_shadow_missing_legacy',
              'channelLayout_existing_legacy_additive':plan[1]['action']=='add_shadow_and_link_legacy'}
    private = load(Path('C:/Windows/Temp/openharmony-neo4j-test-v4/connection-private.json'))
    if private['uri'] != 'bolt://127.0.0.1:17687' or private['version'] != '5.26.32':
        raise ValueError('Wrong isolated target')
    with GraphDatabase.driver(private['uri'],auth=(private['username'],private['password']),max_transaction_retry_time=0) as driver:
        with driver.session(database='neo4j') as session:
            if session.run('CALL dbms.components() YIELD versions RETURN versions').single()['versions'] != ['5.26.32']:
                raise ValueError('Wrong database version')
            if session.run('MATCH (n:DeliveryBridgeProbe) RETURN count(n) AS count').single()['count']:
                raise ValueError('Pre-existing probe nodes; no writes')
            before = graph_snapshot(session)
            for scenario in ['success','injected_failure','changed_legacy']:
                with session.begin_transaction() as tx:
                    old = plan[1]['legacy']
                    tx.run('CREATE (n:DeliveryBridgeProbe {uid:$uid,legacy_json:$body})',uid=BATCH+':legacy:channelLayout',body=json.dumps(old,ensure_ascii=False)).consume()
                    if scenario == 'changed_legacy':
                        changed = dict(old,功能描述='Constructed concurrent edit')
                        tx.run('MATCH (n:DeliveryBridgeProbe {uid:$uid}) SET n.legacy_json=$body',uid=BATCH+':legacy:channelLayout',body=json.dumps(changed,ensure_ascii=False)).consume()
                    try:
                        apply_probe(tx,plan,fail_after_first=scenario=='injected_failure')
                        if scenario != 'success':
                            raise AssertionError('Expected failure was not rejected')
                        apply_probe(tx,plan)
                        rows = tx.run('MATCH (n:DeliveryBridgeProbe) RETURN properties(n) AS props').data()
                        checks['repeat_bridge_three_probe_nodes'] = len(rows)==3
                        checks['legacy_payload_unchanged'] = next(x['props']['legacy_json'] for x in rows if 'legacy_json' in x['props']) == json.dumps(old,ensure_ascii=False)
                        checks['both_complete_signatures_preserved'] = all(any(x['props'].get('signature')==p['signature'] and x['props'].get('optional')==p['optional'] for x in rows) for p in plan)
                        checks['legacy_link_exactly_one'] = tx.run('MATCH (:DeliveryBridgeProbe)-[r:LEGACY_RECORD_EVIDENCE]->(:DeliveryBridgeProbe) RETURN count(r) AS count').single()['count']==1
                    except RuntimeError:
                        if scenario != 'injected_failure': raise
                        checks['failure_after_real_write_rejected'] = tx.run('MATCH (n:DeliveryBridgeProbe) WHERE n.signature IS NOT NULL RETURN count(n) AS count').single()['count']==1
                    except ValueError:
                        if scenario != 'changed_legacy': raise
                        checks['changed_legacy_refused'] = True
                    finally:
                        tx.rollback()
                checks[scenario+'_full_graph_restored'] = graph_snapshot(session)==before
    report={'batch_id':BATCH,'scope':'Two sample additive bridge rehearsed in isolated database; every probe transaction rolled back',
            'plan':[{k:v for k,v in p.items() if k!='legacy'} for p in plan],
            'checks':checks,'passed':all(checks.values()),'shared_migration_executed':False,
            'team_schema_approved':False,'device_runtime_verified':False,'other_release_sdk_verified':False}
    (ROOT/'docs/official-data-delivery/sample-bridge-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'passed':report['passed'],'checks':checks}))
    if not report['passed']: raise SystemExit(2)


if __name__=='__main__':
    main()
