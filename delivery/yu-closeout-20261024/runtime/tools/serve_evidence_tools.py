"""Loopback-only HTTP transport for six read-only evidence tools."""
import argparse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
from urllib.parse import parse_qs,urlsplit
from evidence_tools import EvidenceTools,RequestError,EvidenceError,TOOL_SCHEMAS


def handler(tools):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send_json(self,status,payload):
            raw=json.dumps(payload,ensure_ascii=False).encode();self.send_response(status)
            self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
        def dispatch(self,tool,params):
            try:self.send_json(200,dict(ok=True,**tools.call(tool,params)))
            except (RequestError,ValueError) as exc:self.send_json(400,dict(ok=False,error=dict(code='invalid_request',message=str(exc))))
            except sqlite3.OperationalError as exc:self.send_json(503,dict(ok=False,error=dict(code='query_timeout' if 'interrupted' in str(exc) else 'evidence_unavailable',message='Evidence query could not complete')))
            except (EvidenceError,OSError,sqlite3.DatabaseError):self.send_json(503,dict(ok=False,error=dict(code='evidence_unavailable',message='Evidence integrity or availability check failed')))
            except Exception:self.send_json(503,dict(ok=False,error=dict(code='evidence_unavailable',message='Evidence schema or processing failure')))
        def do_GET(self):
            url=urlsplit(self.path)
            if url.path=='/health':
                try:tools.ensure_integrity();self.send_json(200,dict(ok=True,delivery_id=tools.manifest['delivery_id'],read_only=True,source_releases=sorted(tools.versions)))
                except Exception:self.send_json(503,dict(ok=False,error=dict(code='evidence_unavailable')))
                return
            if url.path in ('/tools','/v1/tools'):self.send_json(200,dict(tools=TOOL_SCHEMAS));return
            if not url.path.startswith(('/tools/','/v1/tools/')):self.send_json(404,dict(ok=False,error=dict(code='not_found')));return
            try:
                params={}
                for key,values in parse_qs(url.query,keep_blank_values=True).items():
                    if len(values)!=1:raise RequestError('Repeated query parameter: '+key)
                    value=values[0]
                    if key=='limit':
                        if not value.isascii() or not value.isdecimal():raise RequestError('Invalid limit')
                        value=int(value)
                    params[key]=value
            except (ValueError,RequestError) as exc:self.send_json(400,dict(ok=False,error=dict(code='invalid_request',message=str(exc))));return
            self.dispatch(url.path.rsplit('/',1)[-1],params)
        def do_POST(self):
            url=urlsplit(self.path)
            if not url.path.startswith(('/tools/','/v1/tools/')):self.send_json(404,dict(ok=False,error=dict(code='not_found')));return
            try:
                raw_length=self.headers.get('Content-Length','')
                if not raw_length.isdecimal() or not 0<int(raw_length)<=16384:raise RequestError('Invalid request size')
                if self.headers.get('Content-Type','').split(';',1)[0]!='application/json':raise RequestError('Expected JSON')
                def unique(pairs):
                    result={}
                    for key,value in pairs:
                        if key in result:raise RequestError('Duplicate JSON key: '+key)
                        result[key]=value
                    return result
                params=json.loads(self.rfile.read(int(raw_length)),object_pairs_hook=unique)
            except (ValueError,RequestError) as exc:self.send_json(400,dict(ok=False,error=dict(code='invalid_request',message=str(exc))));return
            self.dispatch(url.path.rsplit('/',1)[-1],params)
    return Handler


def create_server(tools,port=0):return ThreadingHTTPServer(('127.0.0.1',port),handler(tools))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--port',type=int,default=8547);p.add_argument('--ready-file',type=Path)
    a=p.parse_args();tools=EvidenceTools(a.manifest);server=create_server(tools,a.port)
    ready=dict(base_url='http://127.0.0.1:'+str(server.server_port),delivery_id=tools.manifest['delivery_id'],read_only=True)
    if a.ready_file:a.ready_file.write_text(json.dumps(ready)+'\n',encoding='utf8')
    print(json.dumps(ready),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
