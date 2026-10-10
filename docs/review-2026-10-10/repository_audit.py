"""Read-only repository scan and isolated function reproductions; no DB/network imports."""
import ast
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import tempfile
import traceback
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]


def functions(filename, names=None, **env):
    tree = ast.parse((ROOT / filename).read_text(encoding='utf-8'))
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                and (names is None or n.name in names)]
    for node in selected:
        node.decorator_list = []
    namespace = dict(re=re, json=json, Path=Path, **env)
    exec(compile(ast.Module(body=selected, type_ignores=[]), filename, 'exec'), namespace)
    return namespace


class Session:
    def __init__(self):
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query, params))
        return []


def main():
    extraction = functions('extract_api_info.py')
    importer = functions('_run_import.py', {'make_uid', 'make_label', 'batch_import_file'})
    counts = Counter()
    fields = Counter()
    groups = defaultdict(list)
    examples = {}
    files = sorted((ROOT / '03_extracted_json').rglob('*.json'))
    for i, path in enumerate(files, 1):
        data = json.loads(path.read_text(encoding='utf-8'))
        version = path.relative_to(ROOT / '03_extracted_json').parts[0]
        for node in data['节点']:
            counts['nodes'] += 1
            counts['unknown_module'] += node.get('所属模块') == '未知模块'
            counts['methods'] += node.get('类型') == 'method'
            counts['parameters'] += len(node.get('parameters', []))
            counts['optional_parameters'] += sum(p.get('必填') is False for p in node.get('parameters', []))
            counts['untyped_nodes'] += not node.get('类型')
            for field in ['parameters', 'error_codes', 'return_description', 'since_version', 'system_capability']:
                if node.get(field):
                    fields[field] += 1
            name = node.get('名称') or node.get('签名', 'unnamed')
            uid = importer['make_uid'](node.get('类型', 'Unknown'), name, version, node.get('上级', ''))
            label = importer['make_label'](node.get('类型', 'Unknown'))
            groups[(label, uid)].append((str(path.relative_to(ROOT)), node))
        if i % 1000 == 0:
            print(f'Scanned {i}/{len(files)} files', flush=True)
    duplicate_groups = [g for g in groups.values() if len(g) > 1]
    differing = [g for g in duplicate_groups if len({json.dumps(n, sort_keys=True, ensure_ascii=False) for _, n in g}) > 1]
    # These counts are JSON-key collisions, not all confirmed distinct declarations.
    for g in differing:
        if g[0][1].get('名称') == 'labelStyle':
            examples['labelStyle'] = g
            break

    probes = {}
    node = extraction['process_body']('fetch(value?: string): Promise<string>;',
        {'所属模块': '@kit.Test', '上级': 'Demo', '注释信息': ['@param {string} value - input']}, {'节点': []}, 1)['节点'][0]
    probes['optional_parameter'] = node
    probes['return_callback'] = extraction['extract_return_type']('watch(callback: (code: number) => void): Promise<string>;')
    probes['property_optional'] = extraction['process_body']('value?: string;',
        {'所属模块': '@kit.Test', '上级': 'Demo'}, {'节点': []}, 1)['节点'][0]
    probes['inner_module'] = extraction['extract_info']({'所属模块': '@kit.Test'}, 'child description', True)
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp) / 'api.d.ts'
        fixture.write_text('export declare function publicEntry(): string;\n', encoding='utf-8')
        probes['no_kit'] = extraction['simplify_api'](str(fixture))
        # Same name appears as a class and an interface, so relation MATCH(uid) is ambiguous.
        sample = {'节点': [
            {'类型': 'class', '名称': 'Owner', '所属模块': 'Kit'},
            {'类型': 'interface', '名称': 'Owner', '所属模块': 'Kit'},
            {'类型': 'method', '名称': 'run', '上级': 'Owner', '所属模块': 'Kit',
             'parameters': [{'名称': 'x', '类型': 'string', '必填': False}],
             'error_codes': [{'code': '401'}], 'return_description': 'result', '返回值': 'void'},
        ]}
        fixture = Path(tmp) / 'sample.json'
        fixture.write_text(json.dumps(sample), encoding='utf-8')
        session = Session()
        result = importer['batch_import_file'](session, str(fixture), 'TEST')
        props = [p['props'] for _, p in session.calls if 'props' in p]
        probes['import'] = {'status': result['status'], 'mapped_properties': props,
                            'relation_queries': [q.strip() for q, _ in session.calls if 'UNWIND' in q]}

    query_calls = []
    response = {'cypher': None, 'answer': 'hello'}
    request = SimpleNamespace(json={'message': 'test', 'history': []}, args={})
    def query(q, **params):
        query_calls.append({'query': q, 'params': params})
        return []
    env = functions('app.py', {'api_chat', 'api_graph', 'api_compare'}, request=request,
        jsonify=lambda x: x, SYSTEM_PROMPT='test', run_cypher=query,
        call_ai=lambda messages: {'choices': [{'message': {'content': json.dumps(response)}}]})
    probes['chat_null'] = env['api_chat']()
    response.update(cypher='MATCH (n) DETACH DELETE n', answer='unverified answer')
    probes['chat_write_query'] = env['api_chat']()
    probes['chat_executed_queries'] = query_calls.copy()
    query_calls.clear()
    request.args = {'keyword': '__NO_MATCH__', 'module': '__NO_MODULE__'}
    env['api_graph']()
    probes['graph_no_match_queries'] = query_calls.copy()
    query_calls.clear()
    request.args = {}
    env['run_cypher'] = lambda q, **p: [{'k': 'Same|Class|Owner', 'm': 'ModuleA' if p['ver']=='API5.0' else 'ModuleB', 'name': 'Same', 'type': 'Class'}]
    probes['compare_module_move'] = env['api_compare']()

    out = {'baseline': '35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c',
           'files': len(files), 'counts': dict(counts), 'nonempty_fields': dict(fields),
           'import_key_groups': len(groups), 'duplicate_key_groups': len(duplicate_groups),
           'different_record_key_groups': len(differing), 'examples': examples, 'probes': probes,
           'limits': 'AST-loaded actual functions; mock sessions only. No Neo4j, model or upstream SDK execution.'}
    target = Path(__file__).with_name('repository-audit-results.json')
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: out[k] for k in ['files','counts','nonempty_fields','duplicate_key_groups','different_record_key_groups']}, ensure_ascii=False), flush=True)
    print('Isolated reproductions completed; results saved.', flush=True)


def verify():
    """Check recorded reproductions and run small additional fixtures, without rescanning."""
    target = Path(__file__).with_name('repository-audit-results.json')
    out = json.loads(target.read_text(encoding='utf-8'))
    p = out['probes']
    assert p['optional_parameter']['parameters'][0]['必填'] is True
    assert '必填' not in p['property_optional'] and 'optional' not in p['property_optional']
    assert '所属模块' not in p['inner_module']
    assert p['no_kit'] is None
    assert 'NoneType' in p['chat_null']['answer']
    assert p['chat_executed_queries'][0]['query'] == 'MATCH (n) DETACH DELETE n'
    assert p['chat_write_query']['answer'] == 'unverified answer'
    assert len(p['graph_no_match_queries']) == 2
    assert 'ORDER BY rand()' in p['graph_no_match_queries'][1]['query']
    assert p['compare_module_move']['added_count'] == p['compare_module_move']['removed_count'] == 0
    method = p['import']['mapped_properties'][-1]
    assert not {'parameters', 'error_codes', 'return_description'} & method.keys()
    extraction = functions('extract_api_info.py')
    assert extraction['process_body']('fetch(value: string): void;',
        {'所属模块': '@kit.Test'}, {'节点': []}, 1)['节点'][0]['parameters'] == []
    assert extraction['process_body']('value: string;',
        {'所属模块': '@kit.Test', '上级': 'Demo'}, {'节点': []}, 1)['节点'][0] == p['property_optional']
    batch = functions('batch_extract.py', {'process_single_file'},
                      extract_api_info=SimpleNamespace(**extraction), traceback=traceback)
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / 'api.d.ts'
        f.write_text('export declare function publicEntry(): string;\n', encoding='utf-8')
        result = batch['process_single_file']({'path': str(f), 'version': 'TEST',
            'output_dir': tmp, 'output_name': 'out.json'})
        data = json.loads((Path(tmp) / 'out.json').read_text(encoding='utf-8'))
        assert result['success'] is True and len(data['节点']) == 1
        assert data['节点'][0]['类型'] == 'module'
        p['no_kit_batch'] = {'success': result['success'], 'nodes': data['节点']}
    p['generic_type_alias'] = extraction['process_body']('type Box<T> = T;',
        {'所属模块': '@kit.Test'}, {'节点': []}, 1)['节点'][0]
    assert '类型' not in p['generic_type_alias']
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PASS: recorded function probes and additional no-kit/generic-alias fixtures. No database/network calls.')


if __name__ == '__main__':
    if '--verify-only' in sys.argv:
        verify()
    else:
        main()
        verify()
