"""Deterministic, cited facts after verified retrieval; not a model answer."""
import argparse
import hashlib
import json

from search_verified_samples import search_requirements


def explain(message, release=None, compare_with=None):
    return explain_result(search_requirements(message, release, compare_with))


def explain_result(result):
    """Summarize an internal verified result without reloading evidence."""
    output = {'status': result['status'], 'generation_mode': 'deterministic_evidence_summary',
              'scope': 'Selected candidate explanations; no AI answer or compatibility guarantee',
              'candidates': [], 'comparisons': [], 'sources': {},
              'unknowns': ['权限条件尚未核验', '默认值尚未核验', '设备运行尚未验证', '能否直接迁移替换尚未验证'],
              'retrieval_trace': result['trace']}
    if result['status'] != 'verified_candidates_found':
        output['message'] = {
            'needs_version': '请补充明确的发行版本。',
            'unsupported_release': '该发行尚未纳入当前核验范围。',
            'needs_intent_clarification': '请明确希望查询的功能，当前不能可靠解释否定条件。',
            'no_verified_match': '当前小样本未找到匹配证据，不能据此判断SDK不存在此API。',
            'evidence_unavailable': '证据暂时无法核验，不能给出可靠候选。'
        }.get(result['status'], '当前无法给出可靠候选。')
        return output

    def source(record):
        identity = [record['release'], record['owner'], record['name'], record['signature'], record['evidence_report_sha256']]
        key = hashlib.sha256(json.dumps(identity, ensure_ascii=True).encode('ascii')).hexdigest()[:24]
        output['sources'][key] = {
            'release': record['release'], 'sdk_version': record['sdk_version'],
            'report': record['evidence_report'], 'report_sha256': record['evidence_report_sha256'],
            'declaration_path': record['sdk_evidence']['path'],
            'file_sha256': record['sdk_evidence']['file_sha256'], 'sdk_url': record['sdk_archive_url']}
        return key

    def fact(record, field, text):
        return {'field': field, 'value': record[field], 'text': text, 'source_id': source(record)}

    for candidate in result['candidates']:
        record = candidate['evidence']
        output['candidates'].append({
            'name': record['owner']+'.'+record['name'],
            'selection_reason': '名称或已审阅中文别名与需求匹配；仍需核对实际业务条件。',
            'facts': [
                fact(record, 'release', '发行版本：'+record['release']),
                fact(record, 'signature', '正式SDK声明：'+record['signature']),
                fact(record, 'optional', '可选性：'+('可选，但不说明有默认值。' if record['optional'] else '非可选。')),
                fact(record, 'module', '所属模块：'+record['module']),
                fact(record, 'metadata', '保留成员原始版本与系统能力注释，不将多条since注释折算为单一可用版本。')
            ]})
    for comparison in result['comparisons']:
        old, new = comparison['old'], comparison['new']
        differences = comparison['differences']
        output['comparisons'].append({
            'name': comparison['name'], 'from_release': old['release'], 'to_release': new['release'],
            'source_ids': [source(old), source(new)],
            'from_signature': old['signature'], 'to_signature': new['signature'],
            'differences': differences,
            'explanation': ('所比较声明字段一致；不能据此推断设备行为相同或可直接替换。' if not differences else
                            '双方声明证据存在差异；成员注释与父级注释分别保留，不将注释差异推断为运行行为变化。')})
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--message', required=True)
    parser.add_argument('--release')
    parser.add_argument('--compare-with')
    args = parser.parse_args()
    try:
        result = explain(args.message, args.release, args.compare_with)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=True, indent=2))
