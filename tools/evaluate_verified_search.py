"""Run fixed development cases against the real, read-only sample search."""
import hashlib
import json
import platform
from pathlib import Path

from query_verified_samples import DIRECTORY, MANIFEST, SPECS
from search_verified_samples import search_requirements


def evaluate():
    inputs = [DIRECTORY/MANIFEST, DIRECTORY/'verified-search-dev-cases.json']
    inputs += [DIRECTORY/name for name in sorted({n for spec in SPECS.values() for n in spec[-2:]})]
    def hashes():
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    before = hashes()
    cases = json.loads(inputs[1].read_bytes().decode('utf-8'))['cases']
    rows = []
    for case in cases:
        result = search_requirements(case['message'], case['release'], case.get('compare_with'))
        checks = {'status': result['status'] == case['status'],
                  'names': [c['name'] for c in result['candidates']] == case['names'],
                  'no_absence_claim': result['absence_in_sdk_proven'] is False}
        for candidate in result['candidates']:
            evidence = candidate['evidence']
            checks[candidate['name']+'_provenance'] = (
                evidence['release'] == case['release'] and bool(evidence['sdk_evidence'])
                and evidence['device_runtime_verified'] is False)
        if 'changed_fields' in case:
            comparisons = result['comparisons']
            checks['comparison'] = len(comparisons) == 1 and (
                sorted(comparisons[0]['differences']) == sorted(case['changed_fields'])
                and comparisons[0]['old']['release'] == case['release']
                and comparisons[0]['new']['release'] == case['compare_with'])
        rows.append({'id': case['id'], 'checks': checks, 'passed': all(checks.values()), 'actual': result})
    return {'schema_version': 1, 'scope': 'Development retrieval only; no AI answer, HTTP, device, or overall acceptance claim',
            'python': platform.python_version(), 'input_sha256': before,
            'inputs_unchanged': before == hashes(), 'case_count': len(rows),
            'passed': all(row['passed'] for row in rows) and before == hashes(), 'cases': rows}


if __name__ == '__main__':
    report = evaluate()
    target = DIRECTORY/'verified-search-dev-results.json'
    target.write_text(json.dumps(report, ensure_ascii=True, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'case_count': report['case_count'],
                      'inputs_unchanged': report['inputs_unchanged']}, ensure_ascii=True))
    raise SystemExit(0 if report['passed'] else 1)
