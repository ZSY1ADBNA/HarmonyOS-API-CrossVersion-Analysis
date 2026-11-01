"""Use the configured Harness CLI for structured model turns without exporting credentials.

The six evidence tools are executed by our controller. This is a JSON protocol
adapter, not registration of native provider function-calling or Harness tools.
"""
import argparse,json,os,subprocess,time
from pathlib import Path
from delivery_sources import ROOT,sha256
from evidence_tools import EvidenceTools
from evidence_agent import run,validate_model_response

class HarnessCaller:
    def __init__(self,harness,home,output,node='node',timeout=150):
        self.harness=Path(harness);self.home=Path(home);self.output=Path(output);self.turns=[]
        self.node=str(node);self.timeout=timeout
        self.output.mkdir(parents=True,exist_ok=False)
    def __call__(self,messages,tools):
        prompt=('你正在执行一个受控模型响应适配测试。禁止使用Harness自身的任何工具，禁止读写文件、执行命令或访问网络。'
            '只根据下面的会话和工具定义产生下一条模型消息。需要证据时选择给定工具，由外部控制器执行；不要自己执行。'
            '严格只输出一个JSON对象，格式为 {"choices":[{"message":{"role":"assistant","content":"中文回答或null","tool_calls":[{"id":"唯一调用编号","type":"function","function":{"name":"工具名","arguments":"参数JSON字符串"}}]}}]}。'
            '要调用工具时content为null；已经有充分证据时content为最终回答，省略tool_calls。不得将模拟工具结果编成事实。'
            '\n工具定义：'+json.dumps(tools,ensure_ascii=False)+'\n会话：'+json.dumps(messages,ensure_ascii=False))
        env={**os.environ,'DSH_HOME':str(self.home),'NO_PROXY':'localhost,127.0.0.1,::1,.deepseek.com,api.deepseek.com',
             'no_proxy':'localhost,127.0.0.1,::1,.deepseek.com,api.deepseek.com'}
        number=len(self.turns)+1;start=time.monotonic()
        request_path=self.output/f'turn-{number}.request.json'
        request_path.write_text(json.dumps(dict(messages=messages,tools=tools),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        try:
            result=subprocess.run([self.node,str(self.harness/'apps/cli/lib/bin.js'),'headless','--json','-'],
                input=prompt.encode('utf8'),cwd=self.output,env=env,capture_output=True,timeout=self.timeout)
        except subprocess.TimeoutExpired as exc:
            (self.output/f'turn-{number}.stdout.jsonl').write_bytes(exc.stdout or b'')
            (self.output/f'turn-{number}.stderr.log').write_bytes(exc.stderr or b'')
            self.turns.append(dict(turn=number,status='model_timeout',seconds=round(time.monotonic()-start,3)))
            raise
        (self.output/f'turn-{number}.stdout.jsonl').write_bytes(result.stdout)
        (self.output/f'turn-{number}.stderr.log').write_bytes(result.stderr)
        events=[]
        for line in result.stdout.decode('utf8',errors='replace').splitlines():
            try:events.append(json.loads(line))
            except ValueError:pass
        own_tools=[e for e in events if e.get('type')=='tool_call']
        finals=[e.get('text','') for e in events if e.get('type')=='final']
        receipt=dict(turn=number,returncode=result.returncode,seconds=round(time.monotonic()-start,3),harness_tool_calls=len(own_tools),messages_received=len(messages),tool_results_received=sum(m.get('role')=='tool' for m in messages),stdout_sha256=sha256(self.output/f'turn-{number}.stdout.jsonl'),request_sha256=sha256(request_path))
        self.turns.append(receipt)
        if result.returncode or own_tools or not finals:raise RuntimeError('Harness model response failed protocol boundary')
        text=finals[-1].strip()
        if text.startswith('```') and text.endswith('```'):text='\n'.join(text.splitlines()[1:-1])
        try:
            parsed=json.loads(text)
            validated=validate_model_response(parsed)
        except (ValueError,TypeError):
            receipt['status']='invalid_model_response'
            raise ValueError('Model response did not satisfy the JSON protocol') from None
        receipt['valid_model_response']=True
        return validated

def main(args):
    caller=HarnessCaller(args.harness,args.home,args.output,args.node,args.timeout);tools=EvidenceTools(args.manifest)
    agent=ROOT/'data/delivery/six-stage-20261019/integration/agent.py'
    previous=json.loads(Path(args.history).read_text(encoding='utf8')) if args.history else {}
    result=run(args.question,args.version,tools,caller,agent,sha256(agent),previous.get('messages'),previous.get('version'))
    confirmed=any(t.get('valid_model_response') for t in caller.turns)
    report=dict(date='2026-10-19',real_model_invoked=confirmed,model_invocation_status='valid_response_received' if confirmed else 'not_confirmed',bridge='Harness headless structured JSON adapter; not native provider tool registration',
         member_agent_loop_reused=True,controller_tools='six read-only evidence tools',turns=caller.turns,result=result,
         question=args.question,selected_version=args.version,history_file_sha256=sha256(args.history) if args.history else None,
         implementation_sha256={name:sha256(ROOT/'tools'/name) for name in ('evidence_agent.py','harness_model_bridge.py','evidence_tools.py')},
         retrieval_effectiveness_owner='黄宇鹏',this_run_scope='余镕熙交付链路自查',independent_acceptance=False,page_verified=False)
    (Path(args.output)/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(turns=len(caller.turns),status=result['status'],has_answer=bool(result.get('answer')),independent_acceptance=False)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--harness',required=True);p.add_argument('--home',required=True);p.add_argument('--manifest',required=True);p.add_argument('--output',required=True)
    p.add_argument('--node',default='node');p.add_argument('--timeout',type=float,default=150);p.add_argument('--version',default='5.0.3');p.add_argument('--history')
    p.add_argument('--question',default='OpenHarmony 5.0.3中HTTP请求的连接超时和读取超时分别控制什么？单位与官方默认值是什么？请查询同版本官方文档，给出原文出处；不要把示例数值当默认值。')
    main(p.parse_args())
