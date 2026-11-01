"""Serve existing routes using only the verified private test database."""
import json
from pathlib import Path
import runpy
import socket
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'data/delivery/isolated-neo4j/packages'))
from neo4j import GraphDatabase
from flask import jsonify,request
from werkzeug.serving import BaseWSGIServer

private=json.loads(Path('C:/Windows/Temp/openharmony-neo4j-test-v4/connection-private.json').read_text(encoding='utf-8'))
if private['uri']!='bolt://127.0.0.1:17687':raise ValueError('Wrong test target')
driver=GraphDatabase.driver(private['uri'],auth=(private['username'],private['password']))
driver.verify_connectivity()
with patch.object(GraphDatabase,'driver',return_value=driver):web=runpy.run_path(str(ROOT/'app.py'))
app=web['app']
app.config['TEMPLATES_AUTO_RELOAD']=True
@app.context_processor
def isolated_banner():return {'isolated_test':True}
@app.before_request
def readonly_test_routes():
    if request.path=='/api/graph' and request.args.get('keyword')=='__ISOLATED_QUERY_FAILURE__':
        return jsonify({'error':'Expected private HTTP failure probe'}),503
    if request.method not in ['GET','HEAD'] or request.path=='/api/chat':
        return jsonify({'error':'Isolated test environment permits read-only browsing only'}),405
class ExclusiveTestServer(BaseWSGIServer):
    allow_reuse_address=False
    def server_bind(self):
        if hasattr(socket,'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        return super().server_bind()
server=ExclusiveTestServer('127.0.0.1',15051,app)
print('Isolated existing website ready at http://127.0.0.1:15051',flush=True)
try:server.serve_forever()
finally:driver.close();server.server_close()
