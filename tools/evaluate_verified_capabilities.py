"""Check adapted development probes without executing reserved acceptance questions."""
import hashlib
import json
import re
from pathlib import Path
from verified_query_session import handle_turn
from query_verified_samples import DIRECTORY

ROOT=Path(__file__).resolve().parents[1]
QUESTION_SOURCE=ROOT/'docs/openharmony-query-plan/02-用户问题与参考答案.md'
FIXTURE=DIRECTORY/'verified-capability-dev-cases.json'
DEV_IDS=set(range(1,15))|set(range(21,27))
RESERVED_IDS=set(range(15,21))|{27,28}


def evaluate():
    original=QUESTION_SOURCE.read_bytes()
    numbered={int(m.group(1)):m.group(2) for line in original.decode('utf-8').splitlines()
              if (m:=re.match(r'^(\d+)\.\s+(.+)$',line))}
    if set(numbered)!=set(range(1,29)):
        raise ValueError('Question source changed scope; review before evaluation')
    fixture=json.loads(FIXTURE.read_bytes().decode('utf-8'))
    ids=[c['original_id'] for c in fixture['cases']]
    if len(ids)!=20 or set(ids)!=DEV_IDS or len(set(ids))!=len(ids):
        raise ValueError('Only the 20 adapted development intents may be executed')
    rows=[]
    for case in fixture['cases']:
        result=handle_turn(case['message'],case['release'],case.get('compare_with'))
        checks={'expected_conservative_status':result['status']==case['expected'],
                'no_model_call':result['model_called'] is False}
        if result['status']=='needs_more_evidence':
            checks['explicit_gap']=bool(result['clarification']) and bool(result['result']['unknowns'])
        if result['status']=='verified_candidates_found':
            checks['selected_scope_only']=all(c['name'] in ('ButtonAttribute.fontSize','AudioStreamInfo.channelLayout')
                                             for c in result['result']['candidates'])
        rows.append({'original_id':case['original_id'],'adapted_message':case['message'],
                     'coverage':case['coverage'],'expected_status':case['expected'],'actual_status':result['status'],
                     'checks':checks,'passed':all(checks.values()),'original_question_passed':False})
    return {'scope':'Adapted development behavior only; original 28 questions are not acceptance-tested',
            'implementation_sha256':{name:hashlib.sha256((ROOT/'tools'/name).read_bytes()).hexdigest()
                                     for name in ('verified_query_session.py','search_verified_samples.py','explain_verified_samples.py','query_verified_samples.py')},
            'question_source_sha256':hashlib.sha256(original).hexdigest(),
            'fixture_sha256':hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
            'original_question_count':28,'original_questions_accepted':0,
            'reserved_ids_not_executed':sorted(RESERVED_IDS),
            'original_questions':[{'id':i,'group':'reserved_acceptance' if i in RESERVED_IDS else 'development',
                                   'status':'not_executed_as_original_question'} for i in sorted(numbered)],
            'passed':all(r['passed'] for r in rows),'development_probes':rows}


if __name__=='__main__':
    report=evaluate()
    (DIRECTORY/'verified-capability-evaluation.json').write_text(json.dumps(report,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'development_probe_count':len(report['development_probes']),'passed':report['passed'],
                      'original_questions_accepted':report['original_questions_accepted']}))
    raise SystemExit(0 if report['passed'] else 1)
