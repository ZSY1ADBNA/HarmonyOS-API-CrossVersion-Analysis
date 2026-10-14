"""Verify Button inheritance in fixed source snapshots; SDK packages are separate."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
from collect_official_sources import ROOT,write_json
from verify_sample_declarations import read_file,git_blob


def since_conditions(raw):
    match=re.fullmatch(r'(\d+)(?:\s+(dynamic|static))?',raw)
    if match:return {'status':'explicit_annotation','api_level':int(match[1]),'language_mode':match[2] or 'unspecified','raw':raw}
    if raw.startswith('arkts '):
        try:
            mapping=ast.literal_eval(raw[len('arkts '):])
            if type(mapping) is not dict or not mapping or any(type(k) is not str or type(v) not in (str,int) or not str(v).isdigit() for k,v in mapping.items()):raise ValueError()
            return {'status':'explicit_language_mapping','language_api_levels':{k:int(v) for k,v in mapping.items()},'raw':raw}
        except (ValueError,SyntaxError):pass
    return {'status':'unresolved_annotation','raw':raw}


def inspect_chain(files,root='ButtonAttribute',member='minFontScale'):
    result=subprocess.run([shutil.which('node'),str(ROOT/'tools/inspect_sdk_inheritance.cjs')],
        input=json.dumps({'files':files,'root':root,'member':member}),encoding='utf-8',capture_output=True,timeout=30)
    if result.returncode:raise ValueError(result.stderr[-1000:])
    return json.loads(result.stdout)


def run(data,lock_path,report_path):
    sources=[s for s in json.loads(lock_path.read_text(encoding='utf-8'))['sources'] if s['kind']=='arkts_api']
    if len(sources)!=5 or len({s['release_id'] for s in sources})!=5:raise ValueError('Expected five unique sources')
    results=[]
    for source in sources:
        archive=data/'archives'/(source['source_id']+'.zip')
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=source['archive_sha256']:raise ValueError('Archive mismatch')
        entries=list(map(json.loads,(data/'sources'/source['source_id']/'files.jsonl').read_text(encoding='utf-8').splitlines()))
        ledger={e['path']:e for e in entries}
        if len(ledger)!=source['file_count'] or len(entries)!=len(ledger):raise ValueError('Invalid ledger')
        files=[];evidence=[]
        for path in ['api/@internal/component/ets/button.d.ts','api/@internal/component/ets/common.d.ts']:
            text,proof=read_file(source,ledger,archive,path);files.append({'path':path,'text':text});evidence.append(proof)
        result=inspect_chain(files)
        result.update(release_id=source['release_id'],evidence=evidence,scope='Selected fixed-source class chain; published SDK package not inferred')
        results.append(result)
    annotations=json.loads((data/'structured/yu-declaration-check/source-declarations.json').read_text(encoding='utf-8'))
    conditions=[{'release_id':d['evidence']['release_id'],'owner':d['owner'],'name':d['name'],
        'conditions':[since_conditions(raw) for raw in d['metadata']['since_raw']],
        'scope':'Structured source annotations, without inferring rule precedence or device support'} for d in annotations]
    checks={'five_complete_inheritance_chains':all(r['status']!='incomplete_inheritance_evidence' for r in results),
        'old_button_minFontScale_absent':all(r['status']=='member_absent_in_complete_selected_chain' for r in results if r['release_id'] in ['OpenHarmony-4.1-Release','OpenHarmony-5.0.3-Release']),
        'new_button_minFontScale_declared':all(r['status']=='member_found' and all(m['owner']=='ButtonAttribute' for m in r['matches']) for r in results if r['release_id'] not in ['OpenHarmony-4.1-Release','OpenHarmony-5.0.3-Release'])}
    report={'schema_version':1,'chains':results,'annotation_conditions':conditions,'checks':checks,'passed':all(checks.values()),
        'published_sdk_verified':False,'application_compile_verified':False}
    write_json(report_path,report);return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT/'data/delivery')
    args=parser.parse_args();report=run(args.root,ROOT/'docs/official-data-delivery/sample-declaration-source-lock.json',ROOT/'docs/official-data-delivery/sdk-inheritance-verification.json')
    print(json.dumps({'passed':report['passed'],'chains':[(r['release_id'],r['status']) for r in report['chains']]}))
    if not report['passed']:raise SystemExit(2)
