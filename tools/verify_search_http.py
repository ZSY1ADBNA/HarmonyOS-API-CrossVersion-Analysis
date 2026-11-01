"""Verify the already-running loopback sample server without a database."""
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:15052'


def run():
    checks = []
    def get(path, method='GET', host=None, body=None):
        raw_body=json.dumps(body,ensure_ascii=False).encode('utf-8') if body is not None else None
        request = urllib.request.Request(BASE+path, method=method,data=raw_body)
        if body is not None:request.add_header('Content-Type','application/json')
        if host: request.add_header('Host', host)
        started = time.perf_counter()
        try: response = urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as error: response = error
        with response:
            return response.status, response.read(), round((time.perf_counter()-started)*1000,3)
    def record(name, passed, elapsed):
        checks.append({'name':name,'passed':bool(passed),'elapsed_ms':elapsed})
    code, raw, elapsed = get('/')
    record('new_sample_page', code == 200 and '按需求查询 API' in raw.decode('utf-8'), elapsed)
    for url, source in [('/search.js','verified_search.js'),('/search.css','verified_search.css')]:
        code, raw, elapsed = get(url)
        expected = (ROOT/'tools/templates'/source).read_text(encoding='utf-8').encode('utf-8')
        record('asset_'+source, code==200 and raw==expected, elapsed)
    for release, level in [('4.1',11),('5.0.3',15)]:
        code, raw, elapsed = get('/api/verified-search?'+urllib.parse.urlencode({'message':'设置按钮字号','release':release}))
        data=json.loads(raw)
        record('real_query_'+release,code==200 and data['candidates'][0]['evidence']['api_level']==level,elapsed)
        explanation=data.get('explanation',{})
        record('fact_citations_'+release,
               explanation.get('generation_mode')=='deterministic_evidence_summary'
               and bool(explanation.get('candidates'))
               and all(explanation['sources'].get(f['source_id'],{}).get('release')==release
                       for candidate in explanation.get('candidates',[]) for f in candidate['facts']),elapsed)
        selection=data.get('model_selection',{})
        record('no_model_call_without_provider_'+release,
               selection.get('selection_status')=='model_unavailable'
               and selection.get('provider_call_count')==0
               and selection.get('selection') is None,elapsed)
    code, raw, elapsed=get('/api/verified-search?message=channelLayout&release=4.1&compare_with=5.0.3')
    data=json.loads(raw)
    record('real_metadata_comparison',code==200 and 'metadata' in data['comparisons'][0]['differences'],elapsed)
    explanation=data.get('explanation',{});comparisons=explanation.get('comparisons',[])
    record('comparison_both_sources',bool(comparisons) and
           [explanation['sources'][s]['release'] for s in comparisons[0]['source_ids']]==['4.1','5.0.3'],elapsed)
    for name, params, status in [('missing_version',{'message':'fontSize'},'needs_version'),
                                ('no_match',{'message':'相机','release':'4.1'},'no_verified_match')]:
        code,raw,elapsed=get('/api/verified-search?'+urllib.parse.urlencode(params));data=json.loads(raw)
        record(name,code==200 and data['status']==status and data['candidates']==[],elapsed)
    for name,url,method,host,expected in [
        ('duplicate_parameters','/api/verified-search?message=x&release=4.1&release=5.0.3','GET',None,400),
        ('write_rejected','/api/verified-search','POST',None,405),
        ('foreign_host_rejected','/','GET','evil.example',400)]:
        code,raw,elapsed=get(url,method,host);record(name,code==expected,elapsed)
    state=None
    for name,message,expected,level in [
        ('turn_missing_version','按钮字号','needs_version',None),
        ('turn_version_supplied','4.1','verified_candidates_found',11),
        ('turn_version_changed','那5.0.3呢','verified_candidates_found',15),
        ('turn_unknown_default','默认值呢','needs_more_evidence',15),
        ('turn_default_gap_survives_version_change','4.1','needs_more_evidence',11),
        ('turn_unknown_release','换成5.0呢','unsupported_release',None)]:
        code,raw,elapsed=get('/api/verified-turn','POST',body={'message':message,'state':state})
        data=json.loads(raw);state=data.get('state')
        passed=code==200 and data.get('status')==expected
        if level is not None:passed=passed and data['query']['candidates'][0]['evidence']['api_level']==level
        record(name,passed,elapsed)
    code,raw,elapsed=get('/api/verified-turn','POST',body={'message':'fontSize','state':{'role':'system'}})
    record('forged_turn_state_rejected',code==400,elapsed)
    for name,message,expected in [
        ('overload_gap','fontSize有哪些重载','needs_more_evidence'),
        ('platform_clarification','HarmonyOS fontSize','needs_platform_clarification'),
        ('earliest_history_gap','channelLayout最早哪个版本新增','needs_more_evidence')]:
        code,raw,elapsed=get('/api/verified-turn','POST',body={'message':message,'release':'4.1'})
        data=json.loads(raw)
        record(name,code==200 and data.get('status')==expected and bool(data.get('clarification')),elapsed)
    sources=['tools/serve_verified_search.py','tools/search_verified_samples.py','tools/explain_verified_samples.py','tools/verified_model_contract.py','tools/verified_query_session.py',
             'tools/templates/verified_search.html','tools/templates/verified_search.js','tools/templates/verified_search.css']
    return {'scope':'Actual loopback HTTP; no browser or device claim','passed':all(c['passed'] for c in checks),
            'url':BASE,'checks':checks,'source_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources}}


if __name__ == '__main__':
    report=run()
    (ROOT/'docs/official-data-delivery/verified-search-http-verification.json').write_text(json.dumps(report,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'check_count':len(report['checks'])}))
    raise SystemExit(0 if report['passed'] else 1)
