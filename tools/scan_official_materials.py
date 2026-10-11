"""Scan all collected document/sample domains, preserving provenance and uncertainty.

This is a coverage and source-text scan, not an API semantic parser or build check.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile
from urllib.parse import unquote, urlsplit

from collect_official_sources import filesystem_path, identity, write_json

ROOT = Path(__file__).resolve().parents[1]
CODE = {'.ets', '.ts', '.js', '.cpp', '.cc', '.c', '.h', '.hpp'}
TEXT = CODE | {'.md', '.json', '.json5', '.yaml', '.yml', '.xml', '.txt', '.gradle'}
IMPORT = re.compile(r"(?:from\s*|import\s*)['\"](@(?:ohos|kit)\.[^'\"]+)['\"]")
LINK = re.compile(r'!?\[[^\]\n]*\]\(([^)\s]+)(?:\s+[^)]*)?\)')

def category(path):
    if path.startswith('zh-cn/application-dev/reference/'):
        return 'application_reference'
    parts = path.split('/')
    return parts[1] if len(parts)>1 and parts[0]=='zh-cn' else 'repository_context'

def scan(source, root):
    folder = root/'sources'/source['source_id']
    content = folder/'content'
    with (folder/'files.jsonl').open(encoding='utf-8') as ledger_file:
        ledger = [json.loads(line) for line in ledger_file]
    paths = {entry['path'] for entry in ledger}
    # Root build configuration is required; README count is never an app count.
    build_entries = {str(PurePosixPath(p).parent) for p in paths
                     if PurePosixPath(p).name in ('hvigorfile.ts','hvigorfile.js','settings.gradle')}
    projects = sorted({str(PurePosixPath(p).parent) for p in paths
                       if PurePosixPath(p).name in ('build-profile.json5','build.gradle')
                       and str(PurePosixPath(p).parent) in build_entries}) if source['kind']=='samples' else []
    project_set = set(projects)
    archive_path = root/'archives'/f"{source['source_id']}.zip"
    archive = zipfile.ZipFile(archive_path) if archive_path.exists() else None
    prefix = archive.namelist()[0].split('/')[0]+'/' if archive else None
    outdir = root/'structured'/'yu-materials'/source['source_id']
    outdir.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    failures = []
    unresolved_links = []
    license_files = []
    with (outdir/'documents.jsonl').open('w',encoding='utf-8',newline='\n') as docs, \
         (outdir/'sample-files.jsonl').open('w',encoding='utf-8',newline='\n') as samples:
        for entry in ledger:
            path = entry['path']
            counts['ledger_files'] += 1
            if entry['status'] != 'collected':
                failures.append({'path':path,'status':entry['status']}); continue
            raw = archive.read(prefix+path) if archive else filesystem_path(content/Path(*PurePosixPath(path).parts)).read_bytes()
            if hashlib.sha256(raw).hexdigest() != entry['sha256']:
                failures.append({'path':path,'status':'fingerprint_mismatch'}); continue
            counts['fingerprints_verified'] += 1
            if PurePosixPath(path).name.lower().startswith(('license','notice','copying','copyright')):
                license_files.append({'path':path,'sha256':entry['sha256']})
            ext = PurePosixPath(path).suffix.lower()
            if ext not in TEXT:
                counts['binary_or_other_files'] += 1; continue
            try:
                text = raw.decode('utf-8-sig')
            except UnicodeDecodeError:
                failures.append({'path':path,'status':'utf8_decode_failed'}); continue
            lines = text.splitlines()
            evidence = {'source_id':source['source_id'],'release_id':source['release_id'],
                        'repository':source['repository'],'commit':source['commit'],
                        'path':path,'sha256':entry['sha256'],'git_blob_sha':entry['git_blob_sha']}
            if source['kind']=='docs' and ext=='.md':
                counts['markdown_files'] += 1
                counts['category:'+category(path)] += 1
                fence = None
                headings = []
                for number,line in enumerate(lines,1):
                    match = re.match(r'^\s*(`{3,}|~{3,})',line)
                    if match:
                        marker=match[1]
                        if fence is None: fence=marker
                        elif marker[0]==fence[0] and len(marker)>=len(fence): fence=None
                        continue
                    if fence is not None: continue
                    heading = re.match(r'^(#{1,6})\s+(.+)',line)
                    if heading: headings.append({'line':number,'level':len(heading[1]),'title':heading[2]})
                    for target in LINK.findall(line):
                        parsed=urlsplit(target.strip('<>'))
                        if parsed.scheme or target.startswith(('#','//')): continue
                        relative=unquote(parsed.path)
                        if not relative: continue
                        # Resolve lexical paths without touching the filesystem.
                        parts=list(PurePosixPath(path).parent.parts)
                        if relative.startswith('/'): parts=[]
                        for part in relative.split('/'):
                            if part=='..':
                                if parts: parts.pop()
                            elif part not in ('','.'): parts.append(part)
                        resolved='/'.join(parts)
                        if resolved not in paths:
                            unresolved_links.append({'path':path,'line':number,'target':target,
                                                     'resolved_path':resolved,'status':'not_in_collected_scope'})
                if not text.strip(): counts['empty_markdown'] += 1
                docs.write(json.dumps({'document_id':identity(source['source_id'],path),'evidence':evidence,
                                      'category':category(path),'line_count':len(lines),'headings':headings,
                                      'text':text,'status':'source_text_preserved',
                                      'semantic_parse_status':'pending_category_specific_validation'},ensure_ascii=False)+'\n')
            elif source['kind']=='samples':
                counts['text_files'] += 1
                if ext in CODE: counts['code_files'] += 1
                owner = next((str(p) for p in PurePosixPath(path).parents if str(p) in project_set),None)
                imports = [{'line':n,'module':m[1],'status':'lexical_import_candidate'}
                           for n,line in enumerate(lines,1) for m in IMPORT.finditer(line)] if ext in CODE else []
                counts['import_candidates'] += len(imports)
                samples.write(json.dumps({'evidence':evidence,'project_root_candidate':owner,
                                          'imports':imports,'line_count':len(lines),
                                          'configuration_parse_status':'not_semantically_parsed' if ext in ('.json','.json5') else None,
                                          'api_relationship_status':'unconfirmed','build_status':'not_run'},ensure_ascii=False)+'\n')
    if archive: archive.close()
    report={'source_id':source['source_id'],'kind':source['kind'],'release_id':source['release_id'],
            'commit':source['commit'],'body_status':source.get('body_status','unknown'),
            'counts':dict(counts),'project_roots_candidates':projects,'project_detection':'build_configuration_and_build_entry',
            'license_evidence':license_files,'failures':failures,'relative_links_requiring_review':len(unresolved_links),
            'verification_passed':not failures,'semantic_parsing_verified':False,'build_verified':False}
    write_json(outdir/'links-requiring-review.json',unresolved_links)
    write_json(outdir/'report.json',report)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT/'data/delivery')
    parser.add_argument('--report',type=Path,default=ROOT/'docs/official-data-delivery/materials-scan.json')
    args=parser.parse_args()
    sources=json.loads((args.root/'sources.json').read_text(encoding='utf-8'))['sources']
    reports=[]
    for source in sources:
        if source['kind'] not in ('docs','samples'): continue
        if source['status']!='collected':
            reports.append({'source_id':source['source_id'],'kind':source['kind'],
                            'release_id':source['release_id'],'commit':source['commit'],
                            'status':'body_unavailable','verification_passed':False}); continue
        report=scan(source,args.root); reports.append(report)
        print(source['kind'],source['release_id'],report['counts'],flush=True)
        write_json(args.report,{'schema_version':1,'sources':reports,'all_targets_verified':False})
    complete=len(reports)==10 and all(r.get('verification_passed') for r in reports)
    write_json(args.report,{'schema_version':1,'sources':reports,'all_targets_verified':complete,
                           'scope':'All domains; provenance, fingerprints and source-text coverage only. No API association or build acceptance.'})

if __name__=='__main__': main()
