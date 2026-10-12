"""Small fixed-source pilots with explicit layout adapters, not a universal API parser."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

from collect_official_sources import ROOT, identity, write_json


def heading_spans(text):
    lines=text.splitlines(keepends=True); headings=[]; fence=None; stack=[]
    for index,line in enumerate(lines):
        marker=re.match(r'^\s*(`{3,}|~{3,})',line)
        if marker:
            value=marker[1]
            if fence is None: fence=value
            elif value[0]==fence[0] and len(value)>=len(fence): fence=None
            continue
        if fence is not None: continue
        match=re.match(r'^(#{1,6})\s+(.+?)\s*$',line)
        if not match: continue
        level=len(match[1]);title=match[2]
        while stack and stack[-1]['level']>=level: stack.pop()
        headings.append({'start':index,'level':level,'heading':title,'ancestors':[h['heading'] for h in stack]})
        stack.append(headings[-1])
    starts=[{'start':0,'level':0,'heading':'preamble','ancestors':[]}]+headings if not headings or headings[0]['start']>0 else headings
    result=[]
    for n,heading in enumerate(starts):
        end=starts[n+1]['start'] if n+1<len(starts) else len(lines)
        result.append({**heading,'start_line':heading['start']+1,'end_line':end,
                       'text':''.join(lines[heading['start']:end])})
    return result


def clean_heading(value):
    return re.sub(r'<sup>.*?</sup>','',value).strip().rstrip('#').strip()


def layout_candidates(layout, sections):
    candidates=[]
    if layout=='c_api_ipc_enum':
        for section in sections:
            if clean_heading(section['heading'])!='OH_IPC_ErrorCode': continue
            for offset,line in enumerate(section['text'].splitlines()):
                match=re.match(r'^\|\s*(OH_IPC_[A-Z_]+)\s*=\s*([^|]+)\|',line)
                if match:
                    candidates.append({'kind':'documented_enum_row','owner':'OH_IPC_ErrorCode','name':match[1],
                                       'assignment':match[2].strip(),'line':section['start_line']+offset,'raw_row':line})
    elif layout=='arkui_button':
        for section in sections:
            if clean_heading(section['heading'])=='fontSize' and section['level']==3 and any(clean_heading(h)=='Button' for h in section['ancestors']):
                candidates.append({'kind':'documented_attribute_section','owner':'Button','name':'fontSize',
                                   'line':section['start_line'],'raw_heading':section['heading']})
    # Guides, event lists, deprecated interfaces and audio use source sections only.
    # Method ownership, overloads and parameter tables require dedicated next-stage adapters.
    return candidates


def select_files(paths):
    by_name={PurePosixPath(path).name:path for path in sorted(paths) if path.endswith('.md')}
    choices={
        'arkui_button':['ts-basic-components-button.md'],
        'c_api_ipc_enum':['capi-ipc-error-code-h.md'],
        'event_specification':['commonEvent-definitions.md'],
        'application_guide':['app-structure.md'],
        'deprecated_media':['arkts-apis-media-VideoPlayer.md','js-apis-media.md'],
        'audio_reference':['arkts-apis-audio-AudioRenderer.md','js-apis-audio-AudioRenderer.md','js-apis-audio.md'],
    }
    return {layout:next((by_name[name] for name in names if name in by_name),None) for layout,names in choices.items()}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT/'data/delivery')
    p.add_argument('--report',type=Path,default=ROOT/'docs/official-data-delivery/document-structure-pilot.json')
    args=p.parse_args(); records=[]; gaps=[]; ids=set(); collisions=[]
    sources=json.loads((args.root/'sources.json').read_text(encoding='utf-8'))['sources']
    for source in sources:
        if source['kind']!='docs': continue
        if source.get('body_status')!='complete': raise ValueError('Incomplete document source')
        folder=args.root/'sources'/source['source_id']
        ledger={e['path']:e for e in map(json.loads,(folder/'files.jsonl').read_text(encoding='utf-8').splitlines())}
        selected=select_files(ledger)
        out=args.root/'structured/yu-structure-pilot'/source['source_id'];out.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(args.root/'archives'/f"{source['source_id']}.zip") as archive, (out/'sections.jsonl').open('w',encoding='utf-8',newline='\n') as output:
            prefix=archive.namelist()[0].split('/')[0]+'/'
            for layout,path in selected.items():
                if path is None:
                    gaps.append({'release_id':source['release_id'],'layout':layout,'status':'named_representative_not_in_fixed_scope'});continue
                raw=archive.read(prefix+path);sha=hashlib.sha256(raw).hexdigest()
                if sha!=ledger[path]['sha256']: raise ValueError('Changed document: '+path)
                text=raw.decode('utf-8-sig');sections=heading_spans(text)
                candidates=layout_candidates(layout,sections)
                checks={'complete_text_coverage':''.join(s['text'] for s in sections)==text,
                        'nonempty_source_has_sections':not text.strip() or bool(sections)}
                observations=[]
                if layout=='arkui_button':
                    declaration=any(clean_heading(s['heading'])=='fontSize' for s in sections)
                    if declaration: checks['fontSize_owned_by_Button']=bool(candidates) and all(c['owner']=='Button' for c in candidates)
                    else:
                        checks['no_attribute_inferred_from_examples']=not candidates
                        observations.append('No standalone fontSize declaration heading on this version page; example calls do not create an attribute fact')
                if layout=='c_api_ipc_enum':
                    expected=set(re.findall(r'^\|\s*(OH_IPC_[A-Z_]+)\s*=',text,re.M))
                    checks['all_documented_enum_assignments_retained']=bool(expected) and expected=={c['name'] for c in candidates}
                metadata={name:(match[1].strip() if (match:=re.search(pattern,text)) else None) for name,pattern in {
                    'kit_comment':r'<!--\s*Kit:\s*(.*?)-->',
                    'subsystem_comment':r'<!--\s*Subsystem:\s*(.*?)-->',
                }.items()}
                evidence={'source_id':source['source_id'],'release_id':source['release_id'],'commit':source['commit'],
                          'repository':source['repository'],'path':path,'source_sha256':sha,'git_blob_sha':ledger[path]['git_blob_sha']}
                for section in sections:
                    section_id=identity(source['source_id'],path,layout,section['start_line'],section['end_line'])
                    if section_id in ids:collisions.append(section_id)
                    ids.add(section_id)
                    output.write(json.dumps({'section_id':section_id,'evidence':evidence,'layout_adapter':layout,
                                            **metadata,**section,'api_identity_status':'not_confirmed'},ensure_ascii=False)+'\n')
                write_json(out/(layout+'-candidates.json'),{'evidence':evidence,'candidates':candidates,'api_identity_status':'not_confirmed'})
                records.append({**evidence,'layout_adapter':layout,'sections':len(sections),'candidate_entries':len(candidates),
                                'checks':checks,'observations':observations,'passed':all(checks.values()),**metadata})
    result={'schema_version':1,'inputs':records,'unavailable_representatives':gaps,'unique_sections':len(ids),
            'identity_collisions':collisions,'selected_cases_passed':bool(records) and all(r['passed'] for r in records) and not collisions,
            'all_layouts_all_releases_covered':not gaps,'semantic_parsing_verified':False,'database_ingestion_verified':False,
            'scope':'Specific source-preserving layout pilots and two explicit field adapters; no whole-corpus API semantics, generic parser dependency, SDK or build acceptance'}
    write_json(args.report,result)
    print(json.dumps({'documents':len(records),'sections':len(ids),'selected_cases_passed':result['selected_cases_passed'],
                      'representative_gaps':len(gaps),'failed_cases':[{'release_id':r['release_id'],'layout':r['layout_adapter'],'checks':r['checks']} for r in records if not r['passed']]},ensure_ascii=False))


if __name__=='__main__': main()
