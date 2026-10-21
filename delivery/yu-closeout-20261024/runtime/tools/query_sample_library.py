"""Read source excerpts and conservative import associations, without implying SDK binding."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import re
import sys
from read_only_store import connect


class SampleLibrary:
    def __init__(self,catalog,contexts,notes=None):self.catalog=Path(catalog);self.contexts=Path(contexts);self.notes=Path(notes) if notes else None
    def search(self,query,version,limit=20,module=None,export_name=None):
        if not isinstance(query,str) or not query.strip() or len(query)>256:raise ValueError('Query must be 1..256 characters')
        if type(limit) is not int or not 1<=limit<=100:raise ValueError('Limit must be 1..100')
        if export_name is not None and (not module or not isinstance(export_name,str) or not export_name or len(export_name)>256):raise ValueError('Export filter requires a module and a valid name')
        with closing(connect(self.contexts)) as con,closing(connect(self.catalog)) as cat:
            if not con.execute('SELECT 1 FROM sources WHERE release_id=?',(version,)).fetchone():raise ValueError('Unknown or missing release')
            if module:
                sql='''SELECT c.body,f.file_id,f.path,f.project_id,f.original_text,f.sha256,f.status
                   FROM contexts c JOIN source_files f USING(file_id) WHERE (c.member=? OR
                   (c.member IS NULL AND json_extract(c.body,'$.import_origin.exported')=?)) AND c.import_module=? AND f.release_id=?'''
                args=[query,query,module,version]
                if export_name is not None:sql+=" AND json_extract(c.body,'$.import_origin.exported')=?";args.append(export_name)
                rows=con.execute(sql+' LIMIT ?',[*args,limit+1]).fetchall()
            else:
                tokens=list(dict.fromkeys(re.findall(r'[\w.]+',query)))
                if not tokens:return dict(release_id=version,results=[],truncated=False)
                expression=' AND '.join('"'+t+'"' for t in tokens)
                rows=con.execute('''SELECT f.* FROM source_fts JOIN source_files f ON f.rowid=source_fts.rowid
                    WHERE source_fts MATCH ? AND f.release_id=? ORDER BY f.rowid LIMIT ?''',(expression,version,limit+1)).fetchall()
            results=[]
            for row in rows[:limit]:
                text=row['original_text'];lines=text.splitlines(keepends=True);context=json.loads(row['body']) if module else None
                if context:start=context['target']['start_line']
                else:
                    hit=re.search(re.escape(query),text,re.I);start=text[:hit.start()].count('\n')+1 if hit else 1
                first=max(1,start-2);last=min(len(lines),start+5);snippet=''.join(lines[first-1:last])
                project=cat.execute('SELECT root,body FROM projects WHERE project_id=?',(row['project_id'],)).fetchone()
                project_body=json.loads(project['body']) if project else None
                result=dict(release_id=version,file_id=row['file_id'],path=row['path'],source_sha256=row['sha256'],
                    source_parse_status=row['status'],project_root=project['root'] if project else None,
                    configured_sdk_settings=project_body['sdk_settings'] if project_body else [],
                    sdk_binding_verified=False,association=context,
                    excerpt=dict(start_line=first,end_line=last,text=snippet[:4000],truncated=len(snippet)>4000),
                    scope='source excerpt and local syntax candidate; execution/lifecycle/SDK binding not established')
                catalog_file=cat.execute('SELECT source_id FROM files WHERE file_id=? AND release_id=?',(row['file_id'],version)).fetchone()
                if catalog_file is None:raise ValueError('Source excerpt lacks matching catalog provenance')
                source=con.execute('SELECT body FROM sources WHERE source_id=? AND release_id=?',(catalog_file[0],version)).fetchone()
                if source is None:raise ValueError('Source excerpt belongs to an unavailable source snapshot')
                result['source']=json.loads(source[0])
                results.append(result)
            return dict(release_id=version,query=query,module_filter=module,results=results,truncated=len(rows)>limit,
                unmatched_kit_aliases_may_exist=bool(module),sdk_binding_verified=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--catalog',type=Path,required=True);p.add_argument('--contexts',type=Path,required=True)
    p.add_argument('--notes',type=Path);p.add_argument('--version',required=True);p.add_argument('--query',required=True);p.add_argument('--module');p.add_argument('--limit',type=int,default=20);p.add_argument('--save',type=Path)
    a=p.parse_args();r=SampleLibrary(a.catalog,a.contexts,a.notes).search(a.query,a.version,a.limit,a.module);payload=json.dumps(r,ensure_ascii=False,indent=2)+'\n'
    if a.save:a.save.write_text(payload,encoding='utf8',newline='\n')
    else:sys.stdout.reconfigure(encoding='utf8');print(payload,end='')
