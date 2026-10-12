"""Dedicated five-type audio configuration adapter; documentary candidates only."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import uuid
import zipfile

from collect_official_sources import ROOT, RELEASES, identity, write_json
from extract_document_semantics import metadata, table_rows, create_index, ingest, publish_batch
from pilot_document_structure import heading_spans, clean_heading, outside_fenced_lines
from query_document_candidates import open_readonly, search, resolve_database

OWNERS=('AudioStreamInfo','AudioRendererInfo','AudioCapturerInfo','AudioRendererOptions','AudioCapturerOptions')


def extract_config(text,evidence):
    facts=[];warnings=[];coverage=[]
    for section in heading_spans(text):
        owner=clean_heading(section['heading'])
        if owner not in OWNERS:continue
        # Interface-level metadata is confined to the text preceding its table.
        visible=outside_fenced_lines(section['text'])
        prefix=[]
        for line in visible:
            if line and line.lstrip().startswith('|'):break
            prefix.append(line or '\n')
        parent_meta=metadata(''.join(prefix),section['heading'])
        parent_id=identity(evidence['source_id'],evidence['path'],'config_interface',section['start_line'],owner)
        common={'evidence':evidence,'signature':None,'api_identity_status':'documentation_candidate','sdk_public_status':'not_verified'}
        facts.append({**common,'record_id':parent_id,'kind':'config_interface','name':owner,'owner':owner,
                      'line':section['start_line'],'end_line':section['end_line'],'parent_record_id':None,
                      'metadata':parent_meta,'raw_content':section['text']})
        rows,issues=table_rows(section['text'],section['start_line']);warnings.extend(issues)
        extracted=[]
        for row in rows:
            fields=row['fields'];name=clean_heading(fields.get('名称',''))
            required_columns={'名称','类型','说明'}
            if not required_columns.issubset(fields) or not re.fullmatch(r'[A-Za-z_]\w*',name):
                warnings.append({'line':row['line'],'status':'unsupported_config_table'});continue
            polarity=[key for key in ('必填','可选') if key in fields]
            if len(polarity)!=1 or fields[polarity[0]] not in ('是','否') or ('只读' in fields and fields['只读'] not in ('是','否')):
                warnings.append({'line':row['line'],'status':'unknown_or_conflicting_option_flags'});continue
            optional=(fields[polarity[0]]=='是') if polarity[0]=='可选' else (fields[polarity[0]]=='否')
            record={**common,'record_id':identity(evidence['source_id'],evidence['path'],'property',row['line'],owner,name),
                    'kind':'property','name':name,'owner':owner,'line':row['line'],'end_line':row['line'],
                    'parent_record_id':parent_id,'metadata':metadata(row['raw_row'],fields['名称'],allow_inline=True),
                    'parent_metadata':parent_meta,'declared_type':fields['类型'],'description':fields['说明'],
                    'optional':optional,'option_flag_source':polarity[0],
                    'read_only':None if '只读' not in fields else fields['只读']=='是',
                    'table_fields':fields,'raw_content':row['raw_row']}
            facts.append(record);extracted.append((name,row['line']))
        expected=[]
        for offset,line in enumerate(visible):
            if line is None:continue
            match=re.match(r'^\s*\|\s*([A-Za-z_]\w*)(?:<sup>[^<]*</sup>)?\s*\|',line)
            if match:expected.append((match[1],section['start_line']+offset))
        coverage.append({'owner':owner,'line':section['start_line'],'expected_fields':len(expected),
                         'extracted_fields':len(extracted),'passed':bool(expected) and expected==extracted and len({name for name,_ in extracted})==len(extracted)})
    return facts,warnings,coverage


def run(root,report_path):
    sources=[s for s in json.loads((root/'sources.json').read_text(encoding='utf-8'))['sources'] if s['kind']=='docs']
    facts=[];inputs=[];warnings=[]
    for source in sources:
        if source.get('body_status')!='complete':raise ValueError('Incomplete document source')
        ledger={e['path']:e for e in map(json.loads,(root/'sources'/source['source_id']/'files.jsonl').read_text(encoding='utf-8').splitlines())}
        paths=[p for p in ledger if 'apis-audio-kit/' in p and p.endswith(('/arkts-apis-audio-i.md','/js-apis-audio.md'))]
        selected=next((p for p in paths if p.endswith('/arkts-apis-audio-i.md')),next(iter(paths),None))
        if selected is None:raise ValueError('Audio configuration representative missing')
        with zipfile.ZipFile(root/'archives'/(source['source_id']+'.zip')) as archive:
            prefix=archive.namelist()[0].split('/')[0]+'/'
            raw=archive.read(prefix+selected)
        digest=hashlib.sha256(raw).hexdigest()
        if digest!=ledger[selected]['sha256']:raise ValueError('Original document fingerprint mismatch')
        evidence={key:source[key] for key in ('source_id','release_id','repository','commit')}
        evidence.update(path=selected,source_sha256=digest,git_blob_sha=ledger[selected]['git_blob_sha'])
        text=raw.decode('utf-8-sig');parsed,issues,coverage=extract_config(text,evidence)
        lines=text.splitlines(keepends=True)
        checks={'five_exact_type_sections':Counter(c['owner'] for c in coverage)==Counter(OWNERS),
                'all_field_rows_retained':bool(coverage) and all(c['passed'] for c in coverage),
                'source_spans_match':all(''.join(lines[f['line']-1:f['end_line']]).rstrip('\r\n')==f['raw_content'].rstrip('\r\n') for f in parsed),
                'no_unresolved_table_issues':not issues}
        inputs.append({**evidence,'coverage':coverage,'checks':checks,'counts':dict(Counter(f['kind'] for f in parsed))})
        facts.extend(parsed);warnings.extend({**evidence,**issue} for issue in issues)
    expected_releases={f'OpenHarmony-{version}-Release' for version,_ in RELEASES}
    checks={'exact_five_releases':len(sources)==5 and {s['release_id'] for s in sources}==expected_releases,
            'unique_source_ids':len({s['source_id'] for s in sources})==len(sources),
            'all_input_checks':bool(inputs) and all(all(i['checks'].values()) for i in inputs),
            'unique_record_ids':len({f['record_id'] for f in facts})==len(facts)}
    parents={f['record_id'] for f in facts if f['kind']=='config_interface'}
    checks['all_properties_have_interface_parent']=all(f['parent_record_id'] in parents for f in facts if f['kind']=='property')
    out=root/'structured/yu-audio-config';out.mkdir(parents=True,exist_ok=True)
    if not out.resolve().is_relative_to(root.resolve()):raise ValueError('Database escaped isolated data root')
    temporary=out/('pending-'+uuid.uuid4().hex+'.db')
    with closing(sqlite3.connect(temporary)) as connection:
        create_index(connection);ingest(connection,facts);ingest(connection,facts)
        checks['repeat_ingest_same_count']=connection.execute('SELECT count(*) FROM entities').fetchone()[0]==len(facts)
        connection.execute("INSERT INTO entity_fts(entity_fts,rank) VALUES('integrity-check',1)")
        checks['fts_integrity']=True
        connection.commit()
    with closing(open_readonly(temporary)) as connection:
        for release in sorted(expected_releases):
            for owner in ('AudioRendererOptions','AudioCapturerOptions'):
                hits=search(connection,release,query='streamInfo',name='streamInfo',owner=owner,kind='property')
                checks[release+':'+owner+':exact_readonly_search']=len(hits)==1 and hits[0]['owner']==owner
        checks['unknown_release_empty']=search(connection,'not-a-release',name='streamInfo')==[]
        try:connection.execute('DELETE FROM entities')
        except sqlite3.OperationalError:checks['readonly_rejects_write']=True
        else:checks['readonly_rejects_write']=False
    passed=all(checks.values())
    report={'schema_version':1,'inputs':inputs,'counts':dict(Counter(f['kind'] for f in facts)),
            'warnings':warnings,'checks':checks,'passed':passed,'api_identity_verified':False,
            'sdk_or_build_verified':False,'scope':'Only five named audio configuration types; fields keep their own metadata separate from parent metadata'}
    if passed:publish_batch(out,temporary,facts)
    else:temporary.with_suffix('.jsonl').write_text(''.join(json.dumps(f,ensure_ascii=False)+'\n' for f in facts),encoding='utf-8')
    write_json(report_path,report)
    if passed:
        with closing(open_readonly(resolve_database(out))) as connection:
            if connection.execute('SELECT count(*) FROM entities').fetchone()[0]!=len(facts):raise ValueError('Published batch count mismatch')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT/'data/delivery')
    parser.add_argument('--report',type=Path,default=ROOT/'docs/official-data-delivery/audio-config-pilot.json')
    args=parser.parse_args();report=run(args.root,args.report)
    print(json.dumps({'counts':report['counts'],'documents':len(report['inputs']),'passed':report['passed'],
                      'failed_checks':[k for k,v in report['checks'].items() if not v],'warnings':len(report['warnings'])}))
    if not report['passed']:raise SystemExit(2)


if __name__=='__main__':main()
