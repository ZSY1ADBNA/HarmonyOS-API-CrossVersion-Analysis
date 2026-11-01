"""Archive-backed document library. Exact sections and semantic candidates stay distinct."""
import argparse
from functools import lru_cache
from collections import Counter
from contextlib import closing
from dataclasses import fields
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import time
from delivery_sources import ROOT,ArchiveSource,sha256
from delivery_progress import work_key
from api_identity_v2 import source_id,digest
from pilot_document_structure import heading_spans,clean_heading
from extract_document_semantics import extract as semantic_extract

BASE=ROOT/'data/delivery/six-stage-20261019'
INTEGRATION=BASE/'integration'
sys.path.insert(0,str(INTEGRATION))
from doc_rag.models import DocChunk
from doc_rag.indexer import DocIndexer,tokenize_for_search
from doc_rag.retriever import DocRetriever


def safe_sections(content):
    """Keep member parser semantics while ignoring heading-like lines in fenced examples."""
    sections=heading_spans(content)
    selected=[s for s in sections if 1<=s['level']<=4]
    if not selected:return [(1,'Overview',content)] if content.strip() else []
    # H5/H6 are body content for the legacy H1-H4 parser; retain all source text.
    lines=content.splitlines(keepends=True);result=[]
    if selected[0]['start_line']>1:result.append((1,'Overview',''.join(lines[:selected[0]['start_line']-1]).strip()))
    for n,s in enumerate(selected):
        end=selected[n+1]['start_line']-1 if n+1<len(selected) else len(lines)
        result.append((s['level'],s['heading'],''.join(lines[s['start_line']:end]).strip()))
    return result


@lru_cache(maxsize=10)
def member_parser(version):
    # Load a separate module so the fixed upstream files and imported member module stay untouched.
    spec=importlib.util.spec_from_file_location('delivery_member_parser',INTEGRATION/'doc_rag/parser.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.extract_sections_by_headings=safe_sections
    return module.DocParser(version)


def kind_for(path):
    p=path.lower()
    if 'permission' in p:return 'permission'
    if any(s in p for s in ('errorcode','error-code','errcode')):return 'error_code'
    if 'faq' in p or '/faqs/' in p:return 'faq'
    if any(s in p for s in ('release-notes','releasenotes','changelogs','release-notes')):return 'release_or_change'
    if '/reference/' in p:return 'api_reference'
    return 'guide_or_other'


def adapters_for(path):
    name=Path(path).name
    if name=='js-apis-audio.md':return ['audio_renderer','audio_capturer']
    if name in ('arkts-apis-audio-AudioRenderer.md','js-apis-audio-AudioRenderer.md'):return ['audio_renderer']
    if name in ('arkts-apis-audio-AudioCapturer.md','js-apis-audio-AudioCapturer.md'):return ['audio_capturer']
    if name=='ts-basic-components-button.md':return ['arkui_button']
    if name=='native_averrors.h.md' or name=='capi-native-averrors-h.md':return ['av_error_codes']
    return []


def chunks_for(text,path,version,source):
    spans=heading_spans(text)
    if ''.join(s['text'] for s in spans)!=text:raise ValueError('Section coverage differs from original')
    kit=next((p for p in path.split('/') if p.startswith('apis-') or p.endswith('-kit')),'')
    rows=[]
    for s in spans:
        title=clean_heading(s['heading'])
        c=DocChunk('',version,kit=kit,file_path=path,file_title=path.rsplit('/',1)[-1],
                   heading_level=s['level'],heading_text=title,heading_path=' > '.join(s['ancestors']+[title]),
                   category='source_section',api_name=title,full_name=title,raw_content=s['text'])
        rows.append((c,'exact_source_section',s['start_line'],s['end_line']))
    issues=[];facts=[]
    evidence={k:source[k] for k in ('source_id','release_id','commit','repository')}
    evidence.update(path=path,source_sha256=hashlib.sha256(text.encode()).hexdigest())
    lines=text.splitlines(keepends=True)
    for adapter in adapters_for(path):
        parsed,warnings=semantic_extract(text,evidence,adapter);issues.extend(warnings)
        for f in parsed:
            start=f.get('context_start_line',f['line']);end=f['end_line']
            if not (1<=start<=end<=len(lines)) or ''.join(lines[start-1:end]).rstrip('\r\n')!=f['raw_content'].rstrip('\r\n'):
                raise ValueError('Semantic adapter source span mismatch')
            meta=f.get('metadata',{});owner=f.get('owner') or ''
            c=DocChunk('',version,kit=kit,file_path=path,category=f['kind'],api_name=f['name'],
                parent_title=owner,full_name='.'.join(x for x in (owner,f['name']) if x),
                signature=f.get('signature') or '',since=meta.get('since') or '',
                permission=meta.get('permission') or '',syscap=meta.get('syscap') or '',
                raw_content=f['raw_content'])
            rows.append((c,'specialized_document_candidate',start,end));facts.append(f)
    if kind_for(path)=='api_reference':
        for c in member_parser(version).parse_file_content(path,text):
            raw=c.raw_content;start=text.find(raw) if raw else -1
            unique=start>=0 and text.find(raw,start+1)<0
            first=text[:start].count('\n')+1 if unique else None
            last=first+raw.count('\n') if first else None
            # Legacy parser ownership/signature is a candidate until the corresponding layout is validated.
            origin='member_parser_candidate' if unique else 'member_parser_candidate_ambiguous_span'
            rows.append((c,origin,first,last))
    is_api=kind_for(path)=='api_reference'
    state='whole_document_fallback' if is_api and not facts else 'structured'
    if not any(s['level'] for s in spans):state='whole_document_fallback'
    detail='selected_specialized_declarations' if facts else 'document_sections_only'
    return rows,state,dict(semantic_coverage=detail,adapters=adapters_for(path),warnings=issues,
                           full_api_semantics_verified=False,member_parser_candidates_not_confirmed=True)


def initialize(con):
    # Upstream schema, with a bulk external-content FTS index to avoid per-chunk full-table DELETE.
    con.executescript('''CREATE TABLE files(file_id TEXT PRIMARY KEY,source_id TEXT,release_id TEXT,path TEXT,
       sha256 TEXT,kind TEXT,status TEXT,detail TEXT,original_text TEXT,unparsed_bytes BLOB,work_key TEXT);
       CREATE UNIQUE INDEX file_source_path ON files(source_id,release_id,path);
       CREATE TABLE sources(source_id TEXT,release_id TEXT,body TEXT,PRIMARY KEY(source_id,release_id));
       CREATE TABLE chunk_evidence(chunk_id TEXT PRIMARY KEY,file_id TEXT,origin TEXT,start_line INTEGER,end_line INTEGER);
       CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);''')
    # Column order and defaults follow the reused member data model.
    columns=','.join(f.name+(' INTEGER' if f.name in ('heading_level','deprecated') else ' TEXT') for f in fields(DocChunk))
    con.execute('CREATE TABLE doc_chunks('+columns+',search_tokens TEXT)')
    con.executescript('''CREATE UNIQUE INDEX doc_chunk_id ON doc_chunks(chunk_id);
       CREATE INDEX doc_version_name ON doc_chunks(version,api_name);
       CREATE INDEX doc_version_full_name ON doc_chunks(version,full_name);
       CREATE VIRTUAL TABLE doc_chunks_fts USING fts5(chunk_id UNINDEXED,api_name,parent_title,full_name,search_tokens,
          content='doc_chunks',content_rowid='rowid',tokenize='unicode61');''')


def insert_file(con,source,path,raw,processor_sha256):
    version=source['release_id'];sid=source_id(source['platform'],source['repository'],source['commit'],'docs')
    fid=digest('docfile',[sid,version,path]);input_sha=hashlib.sha256(raw).hexdigest()
    key=work_key(source,path,input_sha,processor_sha256,{'section_profile':'fence-aware-v1'})
    if not path.lower().endswith(('.md','.markdown')):
        con.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?,?,?)',(fid,sid,version,path,input_sha,'asset_or_metadata',
             'excluded',json.dumps({'reason':'non-Markdown asset or repository metadata; original remains in fixed archive'}),None,None,key))
        return 0
    try:
        text=raw.decode('utf8')
        if not text.strip():
            con.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?,?,?)',(fid,sid,version,path,input_sha,kind_for(path),
                 'excluded',json.dumps({'reason':'empty Markdown input'}),text,None,key))
            return 0
        rows,state,detail=chunks_for(text,path,version,source)
    except (UnicodeError,ValueError,IndexError,TypeError) as exc:
        con.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?,?,?)',(fid,sid,version,path,input_sha,kind_for(path),
             'failed',json.dumps({'reason':type(exc).__name__+': '+str(exc)},ensure_ascii=False),None,raw,key))
        return 0
    con.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?,?,?)',(fid,sid,version,path,input_sha,kind_for(path),state,
         json.dumps(detail,ensure_ascii=False),text,None,key))
    for n,(c,origin,start,end) in enumerate(rows):
        legacy=c.chunk_id;c.chunk_id=digest('docchunk',[fid,origin,start,end,n,legacy])
        c.created_at='';data=c.to_dict()
        values=[data[f.name] for f in fields(DocChunk)]
        values.append(tokenize_for_search(' '.join(str(v) for v in values if v is not None)))
        con.execute('INSERT INTO doc_chunks VALUES('+','.join('?' for _ in values)+')',values)
        con.execute('INSERT INTO chunk_evidence VALUES(?,?,?,?,?)',(c.chunk_id,fid,origin,start,end))
    return len(rows)


def processor_fingerprint():
    paths=[Path(__file__),ROOT/'tools/pilot_document_structure.py',ROOT/'tools/extract_document_semantics.py',
           ROOT/'tools/delivery_sources.py',ROOT/'tools/delivery_progress.py',INTEGRATION/'doc_rag/parser.py',
           INTEGRATION/'doc_rag/models.py',INTEGRATION/'doc_rag/indexer.py']
    return digest('docprocessor',[[p.relative_to(ROOT).as_posix(),sha256(p)] for p in paths])


def build(manifest_path,output,data=ROOT/'data/delivery',minimum_free_gib=85):
    if output.exists() or output.with_suffix('.building').exists():raise FileExistsError('Choose a new isolated output')
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_suffix('.building');manifest=json.loads(manifest_path.read_text(encoding='utf8'))
    started=time.monotonic();processor=processor_fingerprint();total=0
    with closing(sqlite3.connect(temporary)) as con:
        con.execute('PRAGMA journal_mode=DELETE');initialize(con)
        for source in manifest['sources']:
            if source['kind']!='docs':continue
            sid=source_id(source['platform'],source['repository'],source['commit'],'docs')
            public_source={k:source[k] for k in ('platform','repository','commit','kind','release_id','archive_sha256')}
            con.execute('INSERT INTO sources VALUES(?,?,?)',(sid,source['release_id'],json.dumps(public_source)))
            with ArchiveSource(source,data) as reader:
                for n,path in enumerate(reader.files):
                    if n%100==0:
                        if shutil.disk_usage(output.parent).free < minimum_free_gib*1024**3:raise OSError('Free space reached protected floor')
                        con.commit()
                    if n%2000==0:print(source['release_id'],'input',n,'of',len(reader.files),flush=True)
                    total+=insert_file(con,source,path,reader.read(path),processor)
            con.commit();print(source['release_id'],'files',len(reader.files),'total_chunks',total,flush=True)
        # One rebuild, keyed by rowid; no full-scan deletes and no duplicate inserts on replace.
        con.set_progress_handler(lambda:int(shutil.disk_usage(output.parent).free < minimum_free_gib*1024**3),50000)
        con.execute("INSERT INTO doc_chunks_fts(doc_chunks_fts) VALUES('rebuild')")
        con.execute("INSERT INTO doc_chunks_fts(doc_chunks_fts,rank) VALUES('integrity-check',1)")
        con.set_progress_handler(None,0)
        expected=sum(s['file_count'] for s in manifest['sources'] if s['kind']=='docs')
        assert con.execute('SELECT count(*) FROM files').fetchone()[0]==expected
        assert con.execute('SELECT count(*) FROM doc_chunks').fetchone()[0]==total
        assert con.execute('PRAGMA quick_check').fetchone()[0]=='ok'
        stats=[dict(release_id=r[0],status=r[1],kind=r[2],files=r[3]) for r in con.execute('SELECT release_id,status,kind,count(*) FROM files GROUP BY 1,2,3')]
        receipt=dict(schema_version=1,source_manifest_sha256=sha256(manifest_path),processor_fingerprint=processor,
             input_files=expected,chunks=total,dispositions=stats,full_api_semantics_verified=False,
             all_input_dispositions_present=True,fts_external_content_verified=True,
             elapsed_seconds=round(time.monotonic()-started,2))
        con.execute('INSERT INTO metadata VALUES(?,?)',('build_receipt',json.dumps(receipt)));con.commit()
    temporary.replace(output);receipt['database_sha256']=sha256(output)
    output.with_suffix('.receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return receipt


class ReadOnlyIndexer:
    def __init__(self,path,timeout=.75):self.path=Path(path);self.timeout=timeout
    def get_connection(self):
        con=sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
        con.execute('PRAGMA query_only=ON');deadline=time.monotonic()+self.timeout
        con.set_progress_handler(lambda:int(time.monotonic()>deadline),1000)
        return con


class Library:
    def __init__(self,path):
        self.indexer=ReadOnlyIndexer(path);self.member=DocRetriever(indexer=self.indexer)
    def search(self,query,version,limit=20,mode='keyword'):
        if not isinstance(query,str) or not query.strip() or len(query)>256:raise ValueError('Nonempty query up to 256 characters required')
        if type(limit) is not int or not 1<=limit<=100:raise ValueError('Limit must be 1..100')
        if mode not in ('keyword','name'):raise ValueError('Unknown query mode')
        with closing(self.indexer.get_connection()) as con:
            if not con.execute('SELECT 1 FROM sources WHERE release_id=?',(version,)).fetchone():raise ValueError('Unknown or missing release')
            if mode=='name':ids=[r.chunk.chunk_id for r in self.member.search_by_name(query,version=version,limit=limit)]
            else:
                tokens=list(dict.fromkeys(tokenize_for_search(query).split()))
                if not tokens:return []
                expression=' AND '.join('"'+t+'"' for t in tokens)
                ids=[r[0] for r in con.execute('''SELECT dc.chunk_id FROM doc_chunks_fts JOIN doc_chunks dc ON dc.rowid=doc_chunks_fts.rowid
                    WHERE doc_chunks_fts MATCH ? AND dc.version=? ORDER BY bm25(doc_chunks_fts),dc.rowid LIMIT ?''',(expression,version,limit))]
            results=[]
            for ident in ids:
                row=con.execute('''SELECT dc.*,e.origin,e.start_line,e.end_line,f.source_id,f.path,f.sha256 source_sha256,
                    f.status disposition,s.body source_body FROM doc_chunks dc JOIN chunk_evidence e USING(chunk_id)
                    JOIN files f USING(file_id) JOIN sources s ON s.source_id=f.source_id AND s.release_id=f.release_id WHERE dc.chunk_id=?''',(ident,)).fetchone()
                result=dict(row);result['source']=json.loads(result.pop('source_body'));result.pop('search_tokens',None)
                result['api_identity_status']='documentation_only';results.append(result)
            return results


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,default=BASE/'source-manifest.json');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=build(a.manifest,a.output);print(json.dumps(r,ensure_ascii=True))
