"""Three explicit documentation adapters and an isolated candidate-search database."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import html
import json
from pathlib import Path
import re
import sqlite3
import uuid
import zipfile

from collect_official_sources import ROOT, identity, write_json
from pilot_document_structure import heading_spans, clean_heading, outside_fenced_lines


def metadata(text, heading='', allow_inline=False):
    text=''.join(line or '\n' for line in outside_fenced_lines(text))
    result={}
    for name,label in [('permission','(?:需要)?权限'),('syscap','系统能力'),('since','起始版本')]:
        prefix='' if allow_inline else r'^\s*'
        match=re.search(prefix+r'\*\*'+label+r'[：:]?\*\*[：:]?\s*([^\n<|]+)',text,re.M)
        result[name]=match[1].strip() if match else None
    if result['since'] is None:
        match=re.search(r'<sup>\s*(\d+\+?)',heading)
        if match: result['since']=match[1]
    result['deprecated_mentioned']=bool(re.search('deprecated|废弃',heading,re.I))
    return result


def table_rows(text, first_line):
    lines=outside_fenced_lines(text); headers=None; result=[]; warnings=[]; label=None
    for offset,line in enumerate(lines):
        if line is None:
            headers=None;label=None;continue
        if re.match(r'^#{1,6}\s',line):label=None
        labeled=re.match(r'^\*\*([^*]+)\*\*',line)
        if labeled:label=labeled[1].strip().rstrip('：:')
        if not line.lstrip().startswith('|'):
            headers=None;continue
        cells=[c.strip().replace(r'\|','|') for c in re.split(r'(?<!\\)\|',line.strip().strip('|'))]
        if cells and all(re.fullmatch(r':?-{2,}:?',c.replace(' ','')) for c in cells): continue
        if headers is None:
            headers=cells;continue
        if len(cells)!=len(headers):
            warnings.append({'line':first_line+offset,'status':'table_columns_require_review'});continue
        result.append({'fields':dict(zip(headers,cells)),'line':first_line+offset,'raw_row':line,'table_label':label})
    return result,warnings


def section_block(sections, index):
    section=sections[index];end=index+1
    while end<len(sections) and sections[end]['level']>section['level']:end+=1
    return ''.join(s['text'] for s in sections[index:end]),sections[end-1]['end_line']


def extract(text, evidence, adapter):
    if adapter not in ('av_error_codes','audio_renderer','audio_capturer','arkui_button'):
        raise ValueError('Unknown documentation adapter: '+adapter)
    sections=heading_spans(text);facts=[];warnings=[]
    def add(kind,name,owner,line,raw,signature=None,parent=None,meta=None,end=None):
        record={'record_id':identity(evidence['source_id'],evidence['path'],kind,line,name,signature),
                'evidence':evidence,'kind':kind,'name':name,'owner':owner,'line':line,'end_line':end or line,
                'signature':signature,'parent_record_id':parent,'metadata':meta or metadata(raw),
                'raw_content':raw,'api_identity_status':'documentation_candidate','sdk_public_status':'not_verified'}
        facts.append(record);return record
    if adapter=='av_error_codes':
        for section in sections:
            title=clean_heading(section['heading'])
            if title=='枚举':
                for offset,line in enumerate(outside_fenced_lines(section['text'])):
                    if line is None:continue
                    if '[OH_AVErrCode]' not in line or '{' not in line:continue
                    for match in re.finditer(r'\b(AV_ERR_[A-Z_]+)\s*=\s*([^,<}]+)',line):
                        add('enum_member',match[1],'OH_AVErrCode',section['start_line']+offset,line,match[2].strip(),meta=metadata(line,allow_inline=True))
            elif title=='OH_AVErrCode':
                parent_meta=metadata(section['text'],section['heading'])
                lines=[line.rstrip('\r\n') if line is not None else '' for line in outside_fenced_lines(section['text'])]
                for offset,line in enumerate(lines):
                    match=re.match(r'^\|\s*(AV_ERR_[A-Z_]+)\s*=\s*([^|]+)\|',line)
                    if not match:continue
                    raw=line;cursor=offset+1
                    while not raw.rstrip().endswith('|') and cursor<len(lines) and not lines[cursor].lstrip().startswith(('|','#')):
                        raw+='\n'+lines[cursor];cursor+=1
                    record=add('enum_member',match[1],'OH_AVErrCode',section['start_line']+offset,raw,match[2].strip(),meta=metadata(raw,allow_inline=True),end=section['start_line']+cursor-1)
                    record['parent_metadata']=parent_meta
        return facts,warnings
    audio_owners={'audio_renderer':'AudioRenderer','audio_capturer':'AudioCapturer'}
    audio_owner=audio_owners.get(adapter)
    for index,section in enumerate(sections):
        title=clean_heading(section['heading'])
        ancestors=[clean_heading(h) for h in section['ancestors']]
        if audio_owner:
            containers=[]
            for heading in ancestors+[title]:
                declared=re.match(r'^(?:Interface|Class|Struct|接口|类)\s*\(([^)]+)\)',heading)
                if declared:containers.append(declared[1])
                elif heading==audio_owner:containers.append(heading)
            owned=bool(containers) and containers[-1]==audio_owner
            owner=audio_owner
            property_scope=owned and (title==audio_owner or title=='属性')
        else:
            owned='Button' in ancestors
            owner='Button'
            property_scope=False
        if not owned:continue
        if property_scope:
            rows,issues=table_rows(section['text'],section['start_line']);warnings.extend(issues)
            for row in rows:
                fields=row['fields']
                if '名称' not in fields or '类型' not in fields or '参数名' in fields:continue
                name=clean_heading(fields['名称'])
                if not re.fullmatch(r'[A-Za-z_]\w*',name):continue
                fact=add('property',name,owner,row['line'],row['raw_row'],meta=metadata(section['text'],fields['名称']))
                fact['declared_type']=fields['类型'];fact['table_fields']=fields
            continue
        if adapter=='arkui_button' and title not in ('Button','fontSize'):continue
        method=re.match(r'^([A-Za-z_]\w*)',title)
        if not method:continue
        name=method[1]
        block,end_line=section_block(sections,index)
        # Declaration must start with this heading's name and include a typed argument
        # or return type. Chained example calls never satisfy this rule.
        declarations=[]
        for offset,line in enumerate(outside_fenced_lines(section['text'])):
            if line is None:continue
            match=re.match(r'^\s*'+re.escape(name)+r'\s*\(.*\)\s*(?::.*)?$',line)
            if match and ':' in line:
                declarations.append((section['start_line']+offset,line.strip()))
        for line,signature in declarations:
            kind=('component_attribute' if name=='fontSize' else 'component_constructor') if adapter=='arkui_button' else 'method'
            fact=add(kind,name,owner,line,block,signature,meta=metadata(block,section['heading']),end=end_line)
            fact['context_start_line']=section['start_line']
            fact['return_values']=[]
            if len(declarations)>1:
                warnings.append({'line':section['start_line'],'status':'shared_table_overload_binding_requires_review'})
                fact['parameter_binding_status']='ambiguous_multiple_declarations'
                continue
            fact['parameter_binding_status']='within_single_declaration_section'
            rows,issues=table_rows(block,section['start_line']);warnings.extend(issues)
            for row in rows:
                fields=row['fields']
                if row['table_label']=='返回值':fact['return_values'].append(row)
                if '参数名' not in fields or '类型' not in fields:continue
                param=clean_heading(fields['参数名'])
                if not re.fullmatch(r'[A-Za-z_]\w*',param):continue
                item=add('parameter',param,owner,row['line'],row['raw_row'],parent=fact['record_id'],meta=metadata(row['raw_row'],allow_inline=True))
                item['declared_type']=fields['类型'];item['table_fields']=fields
    return facts,warnings


def create_index(connection):
    connection.executescript('''
      CREATE TABLE entities(id TEXT PRIMARY KEY, source_id TEXT, release_id TEXT, kind TEXT,
                            name TEXT, owner TEXT, signature TEXT, payload TEXT);
      CREATE VIRTUAL TABLE entity_fts USING fts5(name, owner, payload, content='entities', content_rowid='rowid');
      CREATE TRIGGER entity_insert AFTER INSERT ON entities BEGIN
        INSERT INTO entity_fts(rowid,name,owner,payload) VALUES(new.rowid,new.name,new.owner,new.payload); END;
      CREATE TRIGGER entity_delete AFTER DELETE ON entities BEGIN
        INSERT INTO entity_fts(entity_fts,rowid,name,owner,payload) VALUES('delete',old.rowid,old.name,old.owner,old.payload); END;
      CREATE TRIGGER entity_update AFTER UPDATE ON entities BEGIN
        INSERT INTO entity_fts(entity_fts,rowid,name,owner,payload) VALUES('delete',old.rowid,old.name,old.owner,old.payload);
        INSERT INTO entity_fts(rowid,name,owner,payload) VALUES(new.rowid,new.name,new.owner,new.payload); END;
    ''')


def ingest(connection, facts):
    ids=[f['record_id'] for f in facts]
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate candidate identity; nothing imported')
    with connection:
        connection.executemany('''INSERT INTO entities VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
             source_id=excluded.source_id, release_id=excluded.release_id, kind=excluded.kind,
             name=excluded.name, owner=excluded.owner, signature=excluded.signature,payload=excluded.payload''',
             [(f['record_id'],f['evidence']['source_id'],f['evidence']['release_id'],f['kind'],f['name'],f['owner'],
               f['signature'],json.dumps(f,ensure_ascii=False)) for f in facts])


def publish_batch(out, temporary, facts):
    """Publish one complete generation through a single atomic manifest update."""
    generation=out/'batches'/uuid.uuid4().hex
    generation.mkdir(parents=True)
    database=generation/'candidate-search.db'
    candidates=generation/'candidates.jsonl'
    candidates.write_text(''.join(json.dumps(f,ensure_ascii=False)+'\n' for f in facts),encoding='utf-8',newline='\n')
    temporary.replace(database)
    manifest={name:{'path':str(path.relative_to(out).as_posix()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
              for name,path in [('database',database),('candidates',candidates)]}
    write_json(out/'current.json',manifest)
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT/'data/delivery')
    p.add_argument('--report',type=Path,default=ROOT/'docs/official-data-delivery/document-semantics-pilot.json')
    args=p.parse_args();facts=[];inputs=[];gaps=[];warnings=[]
    sources=json.loads((args.root/'sources.json').read_text(encoding='utf-8'))['sources']
    for source in sources:
        if source['kind']!='docs':continue
        if source.get('body_status')!='complete':raise ValueError('Incomplete input source')
        folder=args.root/'sources'/source['source_id']
        ledger={e['path']:e for e in map(json.loads,(folder/'files.jsonl').read_text(encoding='utf-8').splitlines())}
        names={'av_error_codes':('apis-avcodec-kit/',('capi-native-averrors-h.md','native__averrors_8h.md')),
               'audio_renderer':('apis-audio-kit/',('arkts-apis-audio-AudioRenderer.md','js-apis-audio-AudioRenderer.md','js-apis-audio.md')),
               'audio_capturer':('apis-audio-kit/',('arkts-apis-audio-AudioCapturer.md','js-apis-audio-AudioCapturer.md','js-apis-audio.md')),
               'arkui_button':('apis-arkui/',('ts-basic-components-button.md',))}
        with zipfile.ZipFile(args.root/'archives'/f"{source['source_id']}.zip") as archive:
            prefix=archive.namelist()[0].split('/')[0]+'/'
            for adapter,(directory,basenames) in names.items():
                path=next((p for name in basenames for p in sorted(ledger) if directory in p and p.endswith('/'+name)),None)
                if path is None:gaps.append({'release_id':source['release_id'],'adapter':adapter});continue
                raw=archive.read(prefix+path);sha=hashlib.sha256(raw).hexdigest()
                if sha!=ledger[path]['sha256']:raise ValueError('Source fingerprint mismatch')
                text=raw.decode('utf-8-sig')
                evidence={'source_id':source['source_id'],'release_id':source['release_id'],'commit':source['commit'],'repository':source['repository'],
                          'path':path,'source_sha256':sha,'git_blob_sha':ledger[path]['git_blob_sha']}
                parsed,issues=extract(text,evidence,adapter);facts.extend(parsed)
                warnings.extend({**evidence,**issue} for issue in issues)
                original=text.splitlines(keepends=True)
                input_checks={'all_evidence_lines_in_bounds':all(1<=f['line']<=f['end_line']<=len(original) for f in parsed),
                              'source_spans_match':all(''.join(original[f.get('context_start_line',f['line'])-1:f['end_line']]).rstrip('\r\n')==f['raw_content'].rstrip('\r\n') for f in parsed)}
                callable_kinds={'method','component_attribute','component_constructor'}
                input_checks['declaration_lines_match_source']=all(original[f['line']-1].strip()==f['signature'] for f in parsed if f['kind'] in callable_kinds)
                if adapter=='av_error_codes':
                    expected=set(re.findall(r'\b(AV_ERR_[A-Z_]+)\s*=',text))
                    input_checks['all_source_enum_names_retained']=bool(expected) and expected=={f['name'] for f in parsed}
                inputs.append({**evidence,'adapter':adapter,'counts':dict(Counter(f['kind'] for f in parsed)),
                               'table_warnings':len(issues),'checks':input_checks})
    out=args.root/'structured/yu-semantic-pilot';out.mkdir(parents=True,exist_ok=True)
    if not out.resolve().is_relative_to(args.root.resolve()):raise ValueError('Database escaped isolated data root')
    temporary=out/('candidate-'+uuid.uuid4().hex+'.db')
    with closing(sqlite3.connect(temporary)) as conn:
        create_index(conn);ingest(conn,facts);ingest(conn,facts)
        count=conn.execute('SELECT count(*) FROM entities').fetchone()[0]
        conn.execute("INSERT INTO entity_fts(entity_fts,rank) VALUES('integrity-check',1)")
        checks={'repeat_ingest_same_count':count==len(facts),'unique_identities':len({f['record_id'] for f in facts})==len(facts),
                'fts_external_content_integrity':True,'all_representatives_present':len(inputs)==20 and not gaps,
                'all_selected_inputs_have_candidates':all(i['counts'] for i in inputs),'table_rows_unambiguous':not warnings}
        checks['all_original_source_span_checks']=all(all(i['checks'].values()) for i in inputs)
        callable_ids={f['record_id'] for f in facts if f['kind'] in ('method','component_attribute','component_constructor')}
        checks['all_parameter_parents_are_callable_declarations']=all(f['parent_record_id'] in callable_ids for f in facts if f['kind']=='parameter')
        checks['parameter_tables_never_create_properties']=all('参数名' not in f.get('table_fields',{}) for f in facts if f['kind']=='property')
        for source in sources:
            if source['kind']!='docs':continue
            release=source['release_id']
            hits=conn.execute("SELECT e.release_id FROM entity_fts f JOIN entities e ON e.rowid=f.rowid WHERE entity_fts MATCH ? AND e.release_id=?",('AudioRenderer',release)).fetchall()
            checks[release+':version_filtered_audio_search']=bool(hits) and all(row[0]==release for row in hits)
            overloads=conn.execute("SELECT signature FROM entities WHERE release_id=? AND kind='method' AND owner='AudioRenderer' AND name='setVolume'",(release,)).fetchall()
            checks[release+':setVolume_overloads_retained']=len(set(row[0] for row in overloads))>=2
            properties=conn.execute("SELECT count(*) FROM entities WHERE release_id=? AND kind='property' AND owner='AudioRenderer' AND name='state'",(release,)).fetchone()[0]
            checks[release+':state_property_retained']=properties>0
            capturer=conn.execute("SELECT count(*) FROM entities WHERE release_id=? AND kind='property' AND owner='AudioCapturer' AND name='state'",(release,)).fetchone()[0]
            checks[release+':capturer_state_separate_owner']=capturer>0
            captured=conn.execute("SELECT e.owner FROM entity_fts f JOIN entities e ON e.rowid=f.rowid WHERE entity_fts MATCH ? AND e.release_id=? AND e.owner=?",('AudioCapturer',release,'AudioCapturer')).fetchall()
            checks[release+':capturer_version_owner_search']=bool(captured) and all(row[0]=='AudioCapturer' for row in captured)
            checks[release+':AV_ERR_OK_retained']=any(f['kind']=='enum_member' and f['name']=='AV_ERR_OK' and f['evidence']['release_id']==release for f in facts)
        unknown=conn.execute("SELECT count(*) FROM entities WHERE release_id='not-a-release'").fetchone()[0]
        checks['unknown_release_empty']=unknown==0
        conn.commit()
    passed=all(checks.values())
    if passed:publish_batch(out,temporary,facts)
    else:
        temporary.with_suffix('.jsonl').write_text(''.join(json.dumps(f,ensure_ascii=False)+'\n' for f in facts),encoding='utf-8',newline='\n')
    report={'schema_version':1,'inputs':inputs,'unique_document_inputs':len({(i['source_id'],i['path']) for i in inputs}),
            'counts':dict(Counter(f['kind'] for f in facts)),
            'warnings':warnings,'representative_gaps':gaps,'checks':checks,'passed':passed,
            'database_publication_status':'verified_batch_published' if passed else 'failed_batch_retained_previous_verified_database_unchanged',
            'database_scope':'Isolated candidate database under ignored data root; shared databases untouched',
            'all_kit_semantics_verified':False,'official_api_identity_verified':False,'sdk_public_scope_verified':False,
            'scope':'Only AudioRenderer/AudioCapturer declarations, Button/ fontSize and AVErrCode documentary candidates; field inheritance is not silently inferred; English identifier search, Chinese natural-language retrieval unverified'}
    write_json(args.report,report)
    print(json.dumps({'adapter_runs':len(inputs),'unique_documents':report['unique_document_inputs'],'counts':report['counts'],'warnings':len(warnings),'passed':report['passed'],
                      'failed_checks':[k for k,v in checks.items() if not v]},ensure_ascii=False))
    if not passed:raise SystemExit(2)


if __name__=='__main__':main()
