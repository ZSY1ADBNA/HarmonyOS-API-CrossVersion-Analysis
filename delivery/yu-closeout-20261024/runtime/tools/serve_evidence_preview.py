"""Local isolated evidence preview; keeps the existing application and database untouched."""
import argparse,json
from pathlib import Path
from http.server import ThreadingHTTPServer
from serve_evidence_tools import handler
from evidence_tools import EvidenceTools

def create(tools,port=0):
    base=handler(tools)
    class Preview(base):
        def do_GET(self):
            if self.path=='/':
                raw=Path(__file__).with_name('evidence_preview.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
            else:super().do_GET()
    return ThreadingHTTPServer(('127.0.0.1',port),Preview)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--port',type=int,default=8548);a=p.parse_args();server=create(EvidenceTools(a.manifest),a.port);print(json.dumps(dict(url='http://127.0.0.1:'+str(server.server_port))),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
