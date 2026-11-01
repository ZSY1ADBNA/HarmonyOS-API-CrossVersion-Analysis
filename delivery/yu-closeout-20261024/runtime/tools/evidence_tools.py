"""Six bounded read-only evidence tools. Formal API identities and SDK availability stay unknown."""
from contextlib import closing
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
from urllib.parse import quote
from delivery_sources import sha256
from delivery_doc_query import Library as DocumentLibrary
from query_sample_library import SampleLibrary
from read_only_store import connect


class RequestError(ValueError):pass
class EvidenceError(RuntimeError):pass


def argument(params,names,required=False,default=None):
    values=[params[n] for n in names if n in params and params[n] is not None]
    if values and any(v!=values[0] for v in values):raise RequestError('Conflicting aliases: '+','.join(names))
    value=values[0] if values else default
    if required and (value is None or value==''):raise RequestError('Required argument: '+names[0])
    return value


class EvidenceTools:
    aliases={'search_api':'search','search_apis':'search','graph_neighbors':'detail','get_api_detail':'detail','get_usage_conditions':'conditions',
             'get_related_types':'types','compare_versions':'compare','find_examples':'examples'}
    def __init__(self,manifest):
        self.manifest_path=Path(manifest);self.root=self.manifest_path.resolve().parent
        self.manifest=json.loads(self.manifest_path.read_text(encoding='utf8'));self.paths={};self.stamps={}
        for label,entry in self.manifest['artifacts'].items():
            value=entry['path'];relative=PurePosixPath(value)
            if relative.is_absolute() or '\\' in value or ':' in value or any(p in ('','.','..') for p in value.split('/')):raise EvidenceError('Unsafe artifact path')
            path=(self.root/value).resolve()
            if not path.is_relative_to(self.root):raise EvidenceError('Artifact escapes package root')
            if path.stat().st_size!=entry['bytes'] or sha256(path)!=entry['sha256']:raise EvidenceError('Artifact fingerprint mismatch: '+label)
            self.paths[label]=path;self.stamps[label]=(path.stat().st_size,path.stat().st_mtime_ns)
        self.documents=DocumentLibrary(self.paths['documents'],self.paths['document_names'])
        self.samples=SampleLibrary(self.paths['sample_catalog'],self.paths['sample_contexts'],self.paths.get('project_notes'))
        with closing(connect(self.paths['declarations'])) as con:
            self.versions={r[0] for r in con.execute('SELECT DISTINCT release_id FROM sources')}
            self.coverage=json.loads(con.execute("SELECT value FROM metadata WHERE key='receipt'").fetchone()[0])['coverage']
    def ensure_integrity(self):
        for label,path in self.paths.items():
            stamp=(path.stat().st_size,path.stat().st_mtime_ns)
            if stamp!=self.stamps[label]:
                entry=self.manifest['artifacts'][label]
                if stamp[0]!=entry['bytes'] or sha256(path)!=entry['sha256']:raise EvidenceError('Artifact changed: '+label)
                self.stamps[label]=stamp
    def version(self,value):
        if not isinstance(value,str):raise RequestError('Explicit source release required')
        aliases={v.replace('OpenHarmony-','').replace('-Release',''):v for v in self.versions}
        if value.startswith('API') and value[3:] in aliases:value=value[3:]
        value=aliases.get(value,value)
        if value not in self.versions:raise RequestError('Unknown source release; API level is not a release alias')
        return value
    def _limit(self,params):
        value=argument(params,['limit','per_page'],default=20)
        if type(value) is not int or not 1<=value<=100:raise RequestError('limit must be 1..100')
        return value
    def _name(self,params,required=True):
        value=argument(params,['query','q','name','api_name','keyword','class_name'],required=required)
        if value is not None and (not isinstance(value,str) or not value.strip() or len(value)>256):raise RequestError('Query must be 1..256 characters')
        return value
    def _format(self,payload):
        body=json.loads(payload);text=body.get('original_declaration') or ''
        body['original_declaration_total_chars']=len(text);body['original_declaration_truncated']=len(text)>4000;body['original_declaration']=text[:4000]
        body['unknown_conditions']=['formal_logical_identity','target_sdk_binding','public_sdk_export','preprocessor_or_platform_configuration']
        tags=body.get('tags') or []
        if not any(t.get('name')=='permission' for t in tags):body['unknown_conditions'].append('permission_not_in_record_or_not_parsed')
        if not any(t.get('name')=='since' for t in tags):body['unknown_conditions'].append('since_not_in_record_or_not_parsed')
        body['systemapi_annotation_present_in_record']=any(t.get('name')=='systemapi' for t in tags)
        body['api_id']=None;body['sdk_binding_verified']=False
        evidence=body.get('evidence') or {}
        if evidence.get('repository') and evidence.get('commit') and evidence.get('path'):
            body['source_url']=evidence['repository']+'/blob/'+evidence['commit']+'/'+quote(evidence['path'],safe='/')
            if evidence.get('start_line'):body['source_url']+='#L'+str(evidence['start_line'])
        return body
    def _doc_item(self,row):
        item=dict(row);source=json.loads(item.pop('source_body'));item['source']=source
        item['source_url']=source['repository']+'/blob/'+source['commit']+'/'+quote(item['path'],safe='/')
        raw=item.get('raw_content') or '';item['raw_content_truncated']=len(raw)>4000
        if item['origin']=='member_parser_candidate_ambiguous_span':
            item['candidate_text']=raw[:4000];item['raw_content']=None;item['excerpt_status']='not_uniquely_located_or_derived'
        else:item['raw_content']=raw[:4000];item['excerpt_status']='source_located'
        item['sdk_binding_verified']=False;item['api_identity_status']='documentation_only'
        item['unknown_conditions']=['formal_logical_identity','target_sdk_binding','public_sdk_export','parser_condition_extraction_not_fully_verified']
        return item
    def _document_by_id(self,ident,version):
        with closing(connect(self.paths['documents'])) as con:
            row=con.execute('''SELECT c.chunk_id,c.version,c.api_name,c.full_name,c.category,c.raw_content,e.origin,e.start_line,e.end_line,
              f.path,f.sha256 source_sha256,s.body source_body FROM doc_chunks c JOIN chunk_evidence e USING(chunk_id) JOIN files f USING(file_id)
              JOIN sources s ON s.source_id=f.source_id AND s.release_id=f.release_id WHERE c.chunk_id=? AND c.version=?''',(ident,version)).fetchone()
            return self._doc_item(row) if row else None
    def _related_documents(self,artifact,version,limit=3):
        if 'reconciliation' not in self.paths:return []
        with closing(connect(self.paths['reconciliation'])) as con:
            rows=con.execute('SELECT chunk_id,status FROM document_candidates WHERE artifact_id=? AND release_id=? ORDER BY chunk_id LIMIT ?',(artifact,version,limit)).fetchall()
        result=[]
        for row in rows:
            doc=self._document_by_id(row['chunk_id'],version)
            if doc:result.append(dict(relationship_status=row['status'],document=doc))
        return result
    def _lookup(self,params,version,limit):
        ident=argument(params,['id','api_id','declaration_id'],required=False)
        with closing(connect(self.paths['declarations'])) as con:
            if ident is not None:
                if not isinstance(ident,str) or len(ident)>256:raise RequestError('Invalid declaration reference')
                rows=con.execute('''SELECT DISTINCT d.artifact_id,d.body FROM id_aliases a JOIN declarations d USING(artifact_id)
                       WHERE a.alias=? AND d.release_id=? ORDER BY d.artifact_id LIMIT ? OFFSET ?''',
                       (ident,version,limit+1,(params.get('page',1)-1)*limit)).fetchall()
            else:
                name=self._name(params);module=params.get('module');kind=params.get('kind')
                sql='SELECT artifact_id,body FROM declarations WHERE release_id=? AND name=? COLLATE NOCASE';args=[version,name]
                if module is not None:
                    if not isinstance(module,str) or len(module)>256:raise RequestError('Invalid module locator')
                    sql+=' AND legacy_module=?';args.append(module)
                if kind is not None:
                    if not isinstance(kind,str) or len(kind)>64:raise RequestError('Invalid declaration kind')
                    sql+=' AND kind=?';args.append(kind)
                sql+=' ORDER BY artifact_id LIMIT ? OFFSET ?';rows=con.execute(sql,[*args,limit+1,(params.get('page',1)-1)*limit]).fetchall()
        result=[self._format(row['body']) for row in rows[:limit]]
        return dict(results=result,truncated=len(rows)>limit,
            compatibility_status='no_verified_mapping' if not rows else 'multiple_declaration_candidates' if len(rows)>1 else 'one_declaration_evidence_only',
            formal_api_mapping_status='not_received',absence_conclusion='unknown_not_API_deletion')
    def _docs(self,params,version,limit):
        if limit<1:return []
        mode=params.get('mode','keyword')
        if mode not in ('name','keyword'):raise RequestError('Invalid document search mode')
        rows=self.documents.search(self._name(params),version,limit,mode)
        for row in rows:
            raw=row.get('raw_content') or '';row['raw_content_truncated']=len(raw)>4000;row['raw_content']=raw[:4000]
            if row['origin']=='member_parser_candidate_ambiguous_span':
                row['candidate_text']=row['raw_content'];row['raw_content']=None;row['excerpt_status']='not_uniquely_located_or_derived'
            else:row['excerpt_status']='source_located'
            row['sdk_binding_verified']=False;row['condition_status']='documentary_candidate_not_sdk_verified'
            row['unknown_conditions']=['formal_logical_identity','target_sdk_binding','public_sdk_export','parser_condition_extraction_not_fully_verified']
            row['source_url']=row['source']['repository']+'/blob/'+row['source']['commit']+'/'+quote(row['path'],safe='/')
        return rows
    def _conditions(self,result):
        output=[]
        for row in result['results']:
            tags=row.get('tags') or [];since=[]
            for tag in tags:
                if tag.get('name')=='since':
                    m=re.search(r'@since\s+(\d+)',tag.get('text') or '')
                    if m and m[1] not in since:since.append(m[1])
            output.append(dict(artifact_id=row['artifact_id'],declaration_id=row['declaration_id'],
                since_values_observed=since,since_status='multiple_annotations_not_collapsed' if len(since)>1 else 'observed_annotation' if since else 'unknown',
                annotations=[t for t in tags if t.get('name') in ('since','permission','syscap','systemapi','atomicservice','deprecated','arkts','StageModelOnly','FAModelOnly')],
                raw_comment_evidence=row.get('comment'),annotation_scope='record annotations only; parent inheritance and native tag extraction may be incomplete',
                unknown_conditions=row['unknown_conditions'],sdk_binding_verified=False,evidence=row['evidence']))
        return dict(results=output,truncated=result['truncated'],formal_api_mapping_status='not_received')
    def _types(self,result,version,limit):
        output=[];more=False
        with closing(connect(self.paths['declarations'])) as con:
            for row in result['results']:
                refs=row.get('related_types') or []
                generic_names={m[1] for parameter in row.get('type_parameters') or [] if (m:=re.match(r'([A-Za-z_$][\w$]*)',parameter))}
                if row['language']=='native':refs=[p.get('type') for p in row.get('parameters') or [] if p.get('type')]+([row['return_type']] if row.get('return_type') else [])
                for expression in refs:
                    if len(output)>=limit:more=True;break
                    candidates=[];parts=expression.split('.')
                    is_local_generic=parts[0] in generic_names
                    if row['language']=='arkts' and not is_local_generic and re.fullmatch(r'[\w$.]+',expression):
                        matches=con.execute('''SELECT body FROM declarations WHERE release_id=? AND legacy_module=? AND name=? COLLATE NOCASE
                            AND kind IN ('class','interface','type_alias','enum','namespace') ORDER BY artifact_id LIMIT 4''',(version,row['legacy_module_locator'],parts[-1])).fetchall()
                        for match in matches:
                            target=self._format(match[0]);owners=target.get('owners') or []
                            if len(parts)>1 and owners[-len(parts)+1:]!=parts[:-1]:continue
                            candidates.append(target)
                    output.append(dict(from_artifact_id=row['artifact_id'],type_expression=expression,
                        status='local_generic_parameter' if is_local_generic else 'syntax_reference_candidates' if candidates else 'unresolved_or_local_or_external_type',
                        candidate_declarations=candidates,include_or_alias_resolution_verified=False,
                        evidence=row['evidence'],source_url=row.get('source_url')))
        return dict(results=output,truncated=more or result['truncated'],reference_coverage='legacy_syntax_partial',sdk_binding_verified=False)
    def _example_routes(self,params,version,limit):
        ident=argument(params,['id','api_id','declaration_id']);module=params.get('module')
        if ident is not None:
            declarations=self._lookup(params,version,2)
            if len(declarations['results'])!=1 or declarations['truncated']:
                return dict(results=[],declaration_candidates=declarations['results'],relationship_status='declaration_reference_missing_or_ambiguous',truncated=declarations['truncated'])
            record=declarations['results'][0];name=record['name'];module=record['legacy_module_locator']
        else:name=self._name(params)
        result=self.samples.search(name,version,limit,module)
        if module and len(result['results'])<limit:
            with closing(connect(self.paths['kit_routes'])) as con:
                rows=con.execute('''SELECT kit_module,export_name,body FROM routes WHERE release_id=? AND target_module=?
                    AND type_only=0 AND status='source_reexport_verified' AND target_path IS NOT NULL''',(version,module)).fetchall()
            groups={}
            for row in rows:groups.setdefault((row['kit_module'],row['export_name']),[]).append(json.loads(row['body']))
            for (kit,export),evidence in groups.items():
                remaining=limit-len(result['results'])
                if remaining<1:break
                extra=self.samples.search(name,version,remaining,kit,export)
                for item in extra['results']:item['kit_reexport_source_evidence']=evidence
                result['results'].extend(extra['results']);result['truncated']=result['truncated'] or extra['truncated']
        for item in result['results']:
            item['api_relationship_status']='candidate_not_confirmed_CALLS' if item['association'] is not None else 'source_keyword_match_not_API_binding'
            item['source_url']=item['source']['repository']+'/blob/'+item['source']['commit']+'/'+quote(item['path'],safe='/')
        if module and not result['results']:
            mentions=self.samples.search(name,version,min(limit,5))
            result['unmatched_source_mentions']=mentions['results'];result['relationship_status']='no_verified_import_route_for_this_declaration; lexical mentions are not related API examples'
        return result
    def call(self,tool,params):
        if not isinstance(params,dict):raise RequestError('Arguments must be an object')
        if not isinstance(tool,str):raise RequestError('Tool name must be a string')
        allowed={'query','q','name','api_name','keyword','class_name','version','release_id','module','kind','limit','scope','mode',
                 'id','api_id','declaration_id','from_version','to_version','version_a','version_b','old_version','new_version','direction','page','per_page'}
        if set(params)-allowed:raise RequestError('Unsupported arguments: '+','.join(sorted(set(params)-allowed)))
        for key,value in params.items():
            if key not in ('limit','page','per_page') and value is not None and (not isinstance(value,str) or not value or len(value)>256):raise RequestError('Invalid string argument: '+key)
        tool=self.aliases.get(tool,tool)
        if tool not in ('search','detail','conditions','types','compare','examples'):raise RequestError('Unknown tool')
        if tool!='compare' and any(k in params for k in ('page','per_page','direction','old_version','new_version')):raise RequestError('Legacy paging/direction arguments apply only to comparison')
        if 'page' in params and (type(params['page']) is not int or not 1<=params['page']<=1000000):raise RequestError('Invalid page')
        if params.get('direction') not in (None,'added','removed'):raise RequestError('Invalid legacy comparison direction')
        self.ensure_integrity();limit=self._limit(params)
        if tool=='compare':
            left=self.version(argument(params,['from_version','version_a','old_version'],required=True));right=self.version(argument(params,['to_version','version_b','new_version'],required=True))
            if left==right:raise RequestError('Two different releases required')
            if limit<2:raise RequestError('Comparison requires limit of at least 2')
            budget=max(1,limit//2)
            scoped=self._name(params,False) is not None or argument(params,['id','api_id','declaration_id']) is not None
            first=self._lookup(params,left,budget) if scoped else dict(results=[],truncated=False,result_state='no_scoped_query_or_confirmed_API_change_list')
            second=self._lookup(params,right,budget) if scoped else dict(results=[],truncated=False,result_state='no_scoped_query_or_confirmed_API_change_list')
            payload=dict(results=[dict(release_id=left,**first),dict(release_id=right,**second)],
                relationship_status='formal_cross_version_identity_not_confirmed',
                absence_conclusion='cannot_infer_added_or_removed_from_missing_or_partial_endpoints',
                truncated=first['truncated'] or second['truncated'],requested_direction=params.get('direction'),
                added_or_removed_API_count=None,legacy_change_list_status='not_available_without_confirmed_logical_identity')
            version=[left,right]
        else:
            version=self.version(argument(params,['release_id','version'],required=True))
            if tool=='search':
                scope=params.get('scope','all')
                if scope not in ('all','declarations','documents'):raise RequestError('Invalid search scope')
                declarations=self._lookup(params,version,limit) if scope!='documents' else dict(results=[],truncated=False)
                if scope=='documents':self._name(params)
                docs=self._docs(params,version,limit-len(declarations['results'])) if scope!='declarations' and self._name(params,False) is not None else []
                payload=dict(results=[dict(record_type='declaration',**r) for r in declarations['results']]+[dict(record_type='document',**r) for r in docs],
                     truncation_status='possible_more_at_limit' if len(declarations['results'])+len(docs)==limit else 'not_at_limit',
                     absence_conclusion='no_indexed_match_does_not_establish_API_absence')
            elif tool=='examples':payload=self._example_routes(params,version,limit)
            else:
                ident=argument(params,['id','api_id','declaration_id'])
                if tool=='detail' and isinstance(ident,str) and ident.startswith('docchunk:'):
                    document=self._document_by_id(ident,version);payload=dict(results=[document] if document else [],truncated=False)
                else:
                    result=self._lookup(params,version,limit)
                    if tool=='detail':
                        for row in result['results']:row['related_documents']=self._related_documents(row['artifact_id'],version)
                    payload=result if tool=='detail' else self._conditions(result) if tool=='conditions' else self._types(result,version,limit)
        envelope=dict(tool=tool,delivery_id=self.manifest['delivery_id'],source_release=version,limit=limit,
             coverage=[c for c in self.coverage if c['release_id'] in (version if isinstance(version,list) else [version])],logical_api_identity_status='formal_mapping_not_received',
             sdk_binding_verified=False,unknown_conditions=['formal_logical_identity','target_sdk_binding','public_sdk_export','preprocessor_or_platform_configuration'],
             truncation_status=payload.get('truncation_status','truncated' if payload.get('truncated') else 'not_truncated'),
             evidence_status='source_facts_and_candidates_not_complete_formal_API_inventory')
        envelope.update(payload)
        return envelope


TOOL_SCHEMAS=[dict(type='function',function=dict(name=name,description=description,parameters=dict(type='object',properties={
    'version':dict(type='string',description='Source release, not API level'),
    'query':dict(type='string'), 'id':dict(type='string'), 'module':dict(type='string'),
    'limit':dict(type='integer',minimum=1,maximum=100,default=20),
    'from_version':dict(type='string'),'to_version':dict(type='string')},additionalProperties=True)))
    for name,description in [('search','Search source declarations or official documents with provenance'),
       ('detail','Read declaration evidence; legacy IDs may have multiple candidates'),('conditions','Read annotations and unknown conditions without inventing defaults'),
       ('types','Read syntactic type references and unresolved candidates'),('compare','Compare version-scoped declaration evidence without inferring missing API changes'),
       ('examples','Read sample excerpts; source release and configured SDK remain separate')]]

for schema in TOOL_SCHEMAS:
    name=schema['function']['name'];parameters=schema['function']['parameters'];properties=parameters['properties']
    properties.update(kind=dict(type='string'),scope=dict(type='string',enum=['all','declarations','documents']),mode=dict(type='string',enum=['name','keyword']))
    parameters['additionalProperties']=False
    parameters['required']=['from_version','to_version'] if name=='compare' else ['version']
    if name!='compare':parameters['anyOf']=[dict(required=['query']),dict(required=['id'])]
