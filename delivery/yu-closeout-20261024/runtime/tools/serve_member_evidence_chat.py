"""Loopback adapter for the pinned member chat component and real evidence Agent."""
import argparse,json,threading,time,uuid
from http.server import ThreadingHTTPServer
from pathlib import Path
from delivery_sources import ROOT,sha256
from evidence_tools import EvidenceTools
from evidence_agent import run
from harness_model_bridge import HarnessCaller
from serve_evidence_tools import handler

def create(tools,page,port,harness,home,node,output):
    page=Path(page);provenance=json.loads((page/'provenance.json').read_text(encoding='utf8'))
    if sha256(page/'index.html')!=provenance['adapted_sha256']:raise ValueError('Member page changed')
    agent=ROOT/'data/delivery/six-stage-20261019/integration/agent.py'
    if sha256(agent)!=provenance['member_agent_sha256']:raise ValueError('Member Agent changed')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);gate=threading.BoundedSemaphore(1)
    base=handler(tools)
    class MemberChat(base):
        def do_GET(self):
            if self.path=='/':
                if sha256(page/'index.html')!=provenance['adapted_sha256']:
                    self.send_json(503,dict(error=dict(message='页面指纹不符，拒绝加载。')));return
                raw=(page/'index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
            else:super().do_GET()
        def do_POST(self):
            if self.path!='/api/chat':super().do_POST();return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=65536:raise ValueError('请求过大或为空。')
                body=json.loads(self.rfile.read(size))
                if not isinstance(body,dict) or set(body)-{'message','version','history','history_version'}:raise ValueError('请求字段不符合约定。')
                question=body.get('message');version=body.get('version');tools.version(version)
                if not isinstance(question,str) or not question.strip() or len(question)>3000:raise ValueError('请输入不超过3000字的问题。')
                history=body.get('history',[])
                if not isinstance(history,list) or len(history)>8 or any(not isinstance(m,dict) or m.get('role') not in ('user','assistant') or not isinstance(m.get('content'),str) or len(m['content'])>4000 for m in history):raise ValueError('对话历史不符合约定。')
            except (ValueError,TypeError) as exc:self.send_json(400,dict(error=dict(message=str(exc))));return
            if not gate.acquire(blocking=False):self.send_json(429,dict(error=dict(message='已有一轮回答进行中，请稍后重试。')));return
            try:
                run_dir=output/uuid.uuid4().hex;caller=HarnessCaller(harness,home,run_dir,node);deadline=time.monotonic()+120
                def bounded(messages,tools):
                    remaining=deadline-time.monotonic()
                    if remaining<=0:raise TimeoutError('Overall model deadline')
                    caller.timeout=min(120,remaining);return caller(messages,tools)
                result=run(question,version,tools,bounded,agent,provenance['member_agent_sha256'],history,body.get('history_version'))
                result['evidence_delivery_id']=tools.manifest['delivery_id'];result['model_test_run']=run_dir.name
                (run_dir/'result.json').write_text(json.dumps(dict(result=result,turns=caller.turns,member_source_commit=provenance['source_commit'],independent_acceptance=False),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
                self.send_json(200,result)
            finally:gate.release()
    return ThreadingHTTPServer(('127.0.0.1',port),MemberChat)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--page',required=True);p.add_argument('--port',type=int,default=8557);p.add_argument('--harness',required=True);p.add_argument('--home',required=True);p.add_argument('--node',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    server=create(EvidenceTools(a.manifest),a.page,a.port,a.harness,a.home,a.node,a.output);print(json.dumps(dict(url='http://127.0.0.1:'+str(server.server_port))),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
