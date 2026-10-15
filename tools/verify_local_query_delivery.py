"""Audit the fixed local delivery allowlist; no SDK/build/network/database action."""
import argparse
import hashlib
import json
from pathlib import Path
from query_verified_samples import ROOT, DIRECTORY, load_catalog

MANIFEST=DIRECTORY/'local-query-delivery-manifest.json'
PROTECTED={'workplan.md','docs/official-data-delivery/implementation-status.json',
           'docs/official-data-delivery/source-lock.json','tools/collect_official_sources.py','tools/export_delivery_status.py'}
NEGATIVE=['tools/run_sdk503_negative_probes.py','tools/test_sdk503_negative_probes.py']+[
    'docs/official-data-delivery/'+name for name in ['sdk503-negative-controls.json','sdk503-negative-minFontScale.json',
    'sdk503-negative-volumeMode.json','sdk503-negative-progress.md']]
PENDING=['tools/query_verified_samples.py','tools/test_verified_sample_query.py']+[
    'docs/official-data-delivery/'+name for name in ['verified-sample-query-manifest.json',
    'verified-sample-query-verification.json','verified-sample-query-progress.md']]
FEATURE_TOOLS='search_verified_samples.py test_verified_sample_search.py evaluate_verified_search.py serve_verified_search.py test_verified_search_http.py test_verified_search_ui.cjs explain_verified_samples.py test_verified_sample_explanations.py verified_model_contract.py test_verified_model_contract.py verified_query_session.py test_verified_query_session.py evaluate_verified_capabilities.py verify_search_http.py verify_local_query_delivery.py'.split()
FEATURE_DOCS='verified-search-progress.md verified-search-dev-cases.json verified-search-dev-results.json verified-search-web-progress.md verified-search-http-verification.json verified-search-browser-verification.json verified-explanation-example.json verified-explanation-progress.md verified-model-contract-verification.json verified-model-contract-progress.md verified-session-progress.md verified-session-verification.json verified-session-browser-verification.json verified-session-web-progress.md verified-capability-dev-cases.json verified-capability-evaluation.json verified-capability-progress.md local-query-delivery-progress.md verified-query-reproduction.md query-publication-verification.json query-publication-progress.md'.split()
FEATURES=['requirements-query-preview.txt']+['tools/'+name for name in FEATURE_TOOLS]+['tools/templates/verified_search.'+ext for ext in ('html','js','css')]+['docs/official-data-delivery/'+name for name in FEATURE_DOCS]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def file_entry(name):
    path=ROOT/name
    if name in PROTECTED or path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Out-of-scope delivery path: '+name)
    raw=path.read_bytes()
    if len(raw)>2*1024*1024 or raw.startswith(b'\xef\xbb\xbf'):
        raise ValueError('Unexpected file size or BOM: '+name)
    text=raw.decode('utf-8')
    if '\ufffd' in text:raise ValueError('Replacement characters: '+name)
    if path.suffix=='.json':json.loads(text)
    return {'path':name,'bytes':len(raw),'sha256':sha(raw),
            'git_blob':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()}


def check_sources(mapping):
    if not isinstance(mapping,dict) or not mapping:raise ValueError('Missing report source fingerprints')
    for name,expected in mapping.items():
        if name not in set(NEGATIVE+PENDING+FEATURES):raise ValueError('Report source outside delivery allowlist')
        if file_entry(name)['sha256']!=expected:raise ValueError('Stale report source: '+name)


def build():
    groups={'negative_controls_pr12':NEGATIVE,'original_pending_query_five':PENDING,'local_query_features':FEATURES}
    all_paths=[name for paths in groups.values() for name in paths]
    if len(set(all_paths))!=len(all_paths):raise ValueError('Duplicate delivery path')
    entries={name:file_entry(name) for name in all_paths}
    receipt=json.loads((DIRECTORY/'query-publication-verification.json').read_bytes())
    saved_files=receipt['verified_files']
    if {e['path'] for e in saved_files}!=set(NEGATIVE+PENDING) or len(saved_files)!=len(NEGATIVE+PENDING):
        raise ValueError('Published receipt scope changed')
    for saved in saved_files:
        local=entries[saved['path']]
        if saved.get('matches') is not True or local['git_blob']!=saved['git_blob'] or saved['remote_git_blob']!=local['git_blob'] or local['sha256']!=saved['sha256']:
            raise ValueError('Published prerequisite changed: '+saved['path'])
    catalog=load_catalog()
    if len(catalog)!=4:raise ValueError('Unexpected verified sample scope')
    http=json.loads((DIRECTORY/'verified-search-http-verification.json').read_bytes())
    contract=json.loads((DIRECTORY/'verified-model-contract-verification.json').read_bytes())
    coverage=json.loads((DIRECTORY/'verified-capability-evaluation.json').read_bytes())
    if not all(report.get('passed') is True for report in (http,contract,coverage)):raise ValueError('Failed evidence report')
    check_sources(http['source_sha256']);check_sources(contract['source_sha256'])
    check_sources({'tools/'+name:value for name,value in coverage['implementation_sha256'].items()})
    if coverage['fixture_sha256']!=sha((DIRECTORY/'verified-capability-dev-cases.json').read_bytes()):raise ValueError('Stale development fixture')
    if coverage['question_source_sha256']!=sha((ROOT/'docs/openharmony-query-plan/02-用户问题与参考答案.md').read_bytes()):raise ValueError('Question source changed')
    if coverage['original_questions_accepted']!=0 or coverage['reserved_ids_not_executed']!=[15,16,17,18,19,20,27,28]:raise ValueError('Acceptance boundary changed')
    return {'schema_version':1,'scope':'Two members in OpenHarmony 4.1/API11 and 5.0.3/API15; local-only delivery inventory',
            'groups':{group:[entries[name] for name in paths] for group,paths in groups.items()},
            'current_code_reports':['verified-search-http-verification.json','verified-model-contract-verification.json','verified-capability-evaluation.json'],
            'historical_reports_note':'Earlier browser/session/development reports are stage records, not proof of a full current-code acceptance rerun.',
            'checks':{'utf8_and_json_valid':True,'original_pending_five_unchanged':True,'verified_catalog_records':len(catalog),
                      'current_report_fingerprints_match':True,'protected_modifications_excluded':True},
            'publication':{'master_merge_last_verified':'ba8ac9e86f89962a4d6fff728876b8dd56c61fb8',
                           'pr12_last_verified_head':receipt['verified_head'],
                           'pr12_verified_tree':receipt['verified_tree'],
                           'remote_checked_by_this_audit':False,'local_features_published_by_this_task':False},
            'remaining':['Real model requires runtime credentials; only rule explanation and simulated ordering verified',
                         'Original 28 questions need reference answers and human acceptance',
                         'PR12 prerequisites published as a draft; new feature publication requires fresh baseline checks'],
            'excluded':['Full workplan and unrelated preexisting modifications','Credentials and private environment files',
                        'SDK archives and originals','Database/runtime directories, logs, screenshots, bytecode caches']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-manifest',action='store_true')
    args=parser.parse_args()
    manifest=build()
    if args.write_manifest:
        if MANIFEST.exists() and json.loads(MANIFEST.read_bytes())!=manifest:
            raise ValueError('Existing delivery manifest differs; review before replacing')
        MANIFEST.write_text(json.dumps(manifest,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    if json.loads(MANIFEST.read_bytes())!=manifest:raise ValueError('Local delivery files changed after manifest creation')
    report={'passed':True,'manifest_sha256':sha(MANIFEST.read_bytes()),'file_count':sum(len(v) for v in manifest['groups'].values()),
            'checks':manifest['checks'],'scope':'Local fingerprint audit only; no tests, compile, SDK extraction or remote access rerun'}
    (DIRECTORY/'local-query-delivery-verification.json').write_text(json.dumps(report,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True))
