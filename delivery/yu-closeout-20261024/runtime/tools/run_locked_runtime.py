"""Validate the runtime code and exact data manifest before importing query services."""
import argparse,hashlib,json,sys
from pathlib import Path

def validate(root,manifest):
    root=Path(root).resolve();lock=json.loads((root/'runtime-lock.json').read_text(encoding='utf8'))
    for name,expected in lock['code_sha256'].items():
        p=(root/name).resolve()
        if not p.is_relative_to(root) or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise ValueError('Runtime code fingerprint mismatch: '+name)
    data=json.loads(Path(manifest).read_text(encoding='utf8'))
    if data!=lock['required_external_data']:raise ValueError('Different data manifest')
    identity=hashlib.sha256(json.dumps(dict(code=lock['code_sha256'],data=data['artifacts']),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if lock['delivery_id']!='oh-evidence-'+identity[:20]:raise ValueError('Runtime/data identity mismatch')
    return lock

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--verify',action='store_true');p.add_argument('--preview',action='store_true');p.add_argument('--member-chat',action='store_true');p.add_argument('--port',type=int,default=8547)
    p.add_argument('--harness');p.add_argument('--home');p.add_argument('--node',default='node');p.add_argument('--model-output');a=p.parse_args()
    root=Path(__file__).resolve().parents[1];lock=validate(root,a.manifest)
    # Python -I removes the script directory from imports. Use only this verified package.
    sys.path.insert(0,str(root/'tools'))
    from evidence_tools import EvidenceTools
    tools=EvidenceTools(a.manifest)
    if a.verify:print(json.dumps(dict(passed=True,delivery_id=lock['delivery_id'],artifact_count=len(tools.paths))))
    else:
        if a.member_chat:
            if not all((a.harness,a.home,a.model_output)):p.error('--member-chat requires --harness, --home and --model-output')
            from serve_member_evidence_chat import create
            server=create(tools,root/'data/delivery/six-stage-20261019/member-chat-v6',a.port,a.harness,a.home,a.node,a.model_output)
        elif a.preview:
            from serve_evidence_preview import create
            server=create(tools,a.port)
        else:
            from serve_evidence_tools import create_server
            server=create_server(tools,a.port)
        print(json.dumps(dict(url='http://127.0.0.1:'+str(server.server_port),delivery_id=lock['delivery_id'])),flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()
