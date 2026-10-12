"""Review only recorded issues against immutable local inputs; never repair source bytes."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

from collect_official_sources import GIT, ROOT, file_sha256, write_json


def encoding_candidates(raw):
    groups={}
    codecs=['gbk','gb18030','cp1252']
    if raw.startswith((b'\xff\xfe',b'\xfe\xff')): codecs.insert(0,'utf-16')
    for codec in codecs:
        try:
            text=raw.decode(codec)
            if text.encode(codec)!=raw: continue
        except UnicodeError:
            continue
        digest=hashlib.sha256(text.encode('utf-8')).hexdigest()
        candidate=groups.setdefault(digest,{'equivalent_codecs':[],'text_sha256':digest,'text':text})
        candidate['equivalent_codecs'].append(codec)
    return list(groups.values())


def classify_link(entry, paths, folded, directories):
    target=entry['target']; resolved=entry['resolved_path']
    if '\\' in target or target.count('(')!=target.count(')'):
        return 'link_syntax_requires_review',[]
    if target.startswith('/'):
        return 'root_relative_base_requires_review',[]
    if resolved in paths: return 'exists_outside_collected_scope',[resolved]
    if resolved in directories: return 'directory_target',[resolved]
    if resolved.casefold() in folded: return 'case_mismatch',folded[resolved.casefold()]
    if not PurePosixPath(resolved).suffix:
        guesses=[p for p in (resolved+'.md',resolved+'/README.md',resolved+'/index.md') if p in paths]
        if guesses: return 'site_path_expansion_candidate',guesses
    return 'target_absent_in_fixed_repository_tree',[]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT/'data/delivery')
    p.add_argument('--scan-report',type=Path,default=ROOT/'docs/official-data-delivery/materials-scan.json')
    p.add_argument('--report',type=Path,default=ROOT/'docs/official-data-delivery/material-issues-review.json')
    args=p.parse_args()
    sources={s['source_id']:s for s in json.loads((args.root/'sources.json').read_text(encoding='utf-8'))['sources']}
    scans=json.loads(args.scan_report.read_text(encoding='utf-8'))['sources']
    summaries=[]; encoding_contents=set(); totals=Counter()
    for report in scans:
        source=sources[report['source_id']]
        if report['commit']!=source['commit'] or source.get('body_status')!='complete':
            raise ValueError('Issue input is not a verified fixed source')
        folder=args.root/'sources'/source['source_id']
        out=args.root/'structured/yu-issue-review'/source['source_id']; out.mkdir(parents=True,exist_ok=True)
        ledger={e['path']:e for e in map(json.loads,(folder/'files.jsonl').read_text(encoding='utf-8').splitlines())}
        counts=Counter(); reviews=[]
        archive_path=args.root/'archives'/f"{source['source_id']}.zip"
        with zipfile.ZipFile(archive_path) as archive:
            prefix=archive.namelist()[0].split('/')[0]+'/'
            for issue in report.get('failures',[]):
                if issue['status']!='utf8_decode_failed':
                    reviews.append({**issue,'review_status':'other_scan_failure_unresolved'}); continue
                raw=archive.read(prefix+issue['path']); sha=hashlib.sha256(raw).hexdigest()
                if sha!=ledger[issue['path']]['sha256']: raise ValueError('Changed issue file: '+issue['path'])
                encoding_contents.add(sha)
                try:
                    raw.decode('utf-8-sig')
                except UnicodeDecodeError as exc:
                    failure={'start':exc.start,'end':exc.end,'reason':exc.reason}
                else:
                    raise ValueError('Recorded decoding failure no longer reproduces')
                candidates=encoding_candidates(raw)
                for candidate in candidates:
                    candidate['derived_text_file']=candidate['text_sha256']+'.txt'
                    (out/candidate['derived_text_file']).write_text(candidate.pop('text'),encoding='utf-8',newline='')
                status='lossless_encoding_candidates_unconfirmed' if candidates else 'no_lossless_candidate'
                counts[status]+=1
                reviews.append({'source_id':source['source_id'],'commit':source['commit'],**issue,
                                'source_sha256':sha,'git_blob_sha':ledger[issue['path']]['git_blob_sha'],
                                'utf8_failure':failure,'candidates':candidates,'selected_encoding':None,
                                'review_status':status,'original_modified':False})
            if source['kind']=='docs':
                cache=args.root/'git-cache-v3'/source['source_id']
                tree=subprocess.run([GIT,'-C',str(cache),'-c','core.quotepath=false','ls-tree','-r','--full-tree',source['commit']],
                                    capture_output=True,text=True,encoding='utf-8',check=True,timeout=60,
                                    env={**os.environ,'GIT_NO_LAZY_FETCH':'1'}).stdout
                # Directory metadata only: no English bodies or moving-ref fallback.
                paths={line.split('\t',1)[1] for line in tree.splitlines() if line.split()[1]=='blob'}
                folded=defaultdict(list); directories=set()
                for path in paths:
                    folded[path.casefold()].append(path)
                    directories.update(str(parent) for parent in PurePosixPath(path).parents)
                write_json(out/'fixed-tree-evidence.json',{'commit':source['commit'],'tree_listing_sha256':hashlib.sha256(tree.encode()).hexdigest(),'blob_paths':sorted(paths)})
                links=json.loads((args.root/'structured/yu-materials'/source['source_id']/'links-requiring-review.json').read_text(encoding='utf-8'))
                line_cache={}
                for entry in links:
                    path=entry['path']
                    if path not in line_cache:
                        raw=archive.read(prefix+path)
                        if hashlib.sha256(raw).hexdigest()!=ledger[path]['sha256']: raise ValueError('Changed link source: '+path)
                        line_cache[path]=raw.decode('utf-8-sig').splitlines()
                    source_line=line_cache[path][entry['line']-1]
                    if entry['target'] not in source_line: raise ValueError('Link evidence line differs')
                    classification,targets=classify_link(entry,paths,folded,directories)
                    counts[classification]+=1
                    reviews.append({**entry,'source_id':source['source_id'],'commit':source['commit'],
                                    'source_sha256':ledger[path]['sha256'],'source_line':source_line,
                                    'review_status':classification,'candidate_targets':targets,
                                    'anchor_verified':False,'upstream_link_repaired':False})
        write_json(out/'issues.json',reviews)
        totals.update(counts)
        summaries.append({'source_id':source['source_id'],'kind':source['kind'],'release_id':source['release_id'],
                          'commit':source['commit'],'reviewed_items':len(reviews),'counts':dict(counts)})
    result={'schema_version':1,'sources':summaries,'counts':dict(totals),
            'unique_non_utf8_contents':len(encoding_contents),'all_recorded_items_reviewed':len(summaries)==10,
            'all_issues_resolved':False,'scope':'Fixed-tree path review and lossless encoding candidates; no upstream edits, encoding declarations, anchor verification or semantic acceptance'}
    write_json(args.report,result)
    print(json.dumps({'counts':dict(totals),'unique_non_utf8_contents':len(encoding_contents)},ensure_ascii=False))


if __name__=='__main__': main()
