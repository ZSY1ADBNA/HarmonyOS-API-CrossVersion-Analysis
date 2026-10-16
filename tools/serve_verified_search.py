"""Loopback-only preview of the verified sample requirement search; no database."""
from pathlib import Path
import json
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'data/delivery/isolated-neo4j/packages'))
from flask import Flask, jsonify, render_template, request
from werkzeug.serving import BaseWSGIServer
from search_verified_samples import search_requirements
from explain_verified_samples import explain_result
from verified_model_contract import run_selection, unique_object
from verified_query_session import handle_turn


def create_app(provider=None, provider_kind='unconfigured'):
    app = Flask(__name__, template_folder=str(Path(__file__).parent/'templates'))
    app.config['MAX_CONTENT_LENGTH'] = 16000

    @app.before_request
    def boundaries():
        if request.remote_addr not in ('127.0.0.1', '::1'):
            return jsonify(error='Loopback preview only'), 403
        if request.host not in ('127.0.0.1:15052', 'localhost:15052'):
            return jsonify(error='Unexpected preview host'), 400
        if request.method not in ('GET', 'HEAD') and not (request.method=='POST' and request.path=='/api/verified-turn'):
            return jsonify(error='Read-only preview'), 405
        if len(request.query_string) > 16000:
            return jsonify(error='Request too long'), 414

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response

    @app.get('/')
    def index():
        return render_template('verified_search.html')

    @app.get('/search.js')
    def javascript():
        return app.response_class((Path(__file__).parent/'templates/verified_search.js').read_text(encoding='utf-8'), mimetype='application/javascript')

    @app.get('/search.css')
    def stylesheet():
        return app.response_class((Path(__file__).parent/'templates/verified_search.css').read_text(encoding='utf-8'), mimetype='text/css')

    @app.get('/api/verified-search')
    def search():
        allowed = {'message', 'release', 'compare_with'}
        if set(request.args)-allowed or any(len(request.args.getlist(k)) != 1 for k in request.args):
            return jsonify(error='Unknown or duplicate search parameters'), 400
        try:
            result = search_requirements(request.args.get('message'), request.args.get('release'), request.args.get('compare_with'))
            controlled = run_selection(explain_result(result), provider, provider_kind)
            result['explanation'] = controlled['explanation']
            result['model_selection'] = {key: controlled[key] for key in (
                'selection_status', 'provider_kind', 'provider_call_count', 'free_text_answer_generated', 'selection')}
        except ValueError:
            return jsonify(error='Enter a requirement of 1 to 2000 characters'), 400
        return jsonify(result), 503 if result['status'] == 'evidence_unavailable' else 200

    @app.post('/api/verified-turn')
    def turn():
        if request.args:
            return jsonify(error='Query parameters are not accepted for turns'),400
        if not request.is_json:
            return jsonify(error='Use a JSON request'),415
        try:
            payload=json.loads(request.get_data().decode('utf-8'),object_pairs_hook=unique_object)
            if not isinstance(payload,dict) or set(payload)-{'message','release','compare_with','state'}:
                raise ValueError('Unexpected turn fields')
            response=handle_turn(payload.get('message'),payload.get('release'),payload.get('compare_with'),payload.get('state'))
            retrieval=response.pop('retrieval')
            explanation=response.pop('result')
            if retrieval is not None:
                enabled=response['status']=='verified_candidates_found'
                controlled=run_selection(explanation,provider if enabled else None,provider_kind if enabled else 'unconfigured')
                retrieval['explanation']=controlled['explanation']
                retrieval['model_selection']={key:controlled[key] for key in (
                    'selection_status','provider_kind','provider_call_count','free_text_answer_generated','selection')}
            response['query']=retrieval
        except (ValueError,UnicodeDecodeError,RecursionError):
            return jsonify(error='Invalid requirement or bounded session context'),400
        return jsonify(response),503 if response['status']=='evidence_unavailable' else 200

    return app


class ExclusiveServer(BaseWSGIServer):
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        return super().server_bind()


if __name__ == '__main__':
    server = ExclusiveServer('127.0.0.1', 15052, create_app())
    print('Verified sample preview: http://127.0.0.1:15052', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
