"""Actual corpus through member loop; scripted caller, explicitly not a model acceptance."""
import argparse,hashlib,json
from pathlib import Path
from evidence_agent import run
from evidence_tools import EvidenceTools

def verify(manifest,agent_path,output):
    tools=EvidenceTools(manifest);cases=[]
    for query,version in [('createHttp','5.0.3'),('ohos.test.__NonexistentApiForEvaluation__','6.1')]:
        messages_seen=[]
        def caller(messages,tools):
            messages_seen.append(messages.copy())
            if len(messages_seen)==1:return dict(choices=[dict(message=dict(role='assistant',tool_calls=[dict(id='query',type='function',function=dict(name='search',arguments=json.dumps(dict(query=query,version=version,limit=2))))]))])
            body=json.loads(messages[-1]['content']);assert body['source_release']=='OpenHarmony-'+version+'-Release';assert body['coverage'];assert 'unknown_conditions' in body
            return dict(choices=[dict(message=dict(role='assistant',content='脚本回传检查占位，不是真实模型回答'))])
        result=run(query,version,tools,caller,agent_path,hashlib.sha256(Path(agent_path).read_bytes()).hexdigest())
        Path(str(output)+'.latest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        assert len(messages_seen)==2
        if 'Nonexistent' in query:assert result['status']=='no_matching_evidence'
        else:assert result['results'] and result['evidence'][0]['results']
        cases.append(dict(query=query,version=version,result=result,tool_result_received_by_next_call=True))
    result=dict(passed=True,real_corpus=True,member_loop_reused=True,caller='scripted_test_double',real_model_verified=False,page_verified=False,independent_acceptance=False,cases=cases)
    Path(output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(dict(passed=True,cases=len(cases),real_model_verified=False)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--agent',required=True);p.add_argument('--output',required=True);a=p.parse_args();verify(a.manifest,a.agent,a.output)
