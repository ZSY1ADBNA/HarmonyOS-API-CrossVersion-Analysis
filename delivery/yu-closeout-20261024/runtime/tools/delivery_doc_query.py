"""Content-bound name index and read-only queries over the fixed document body database."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
from delivery_doc_library import Library as BodyLibrary,ReadOnlyIndexer
from doc_rag.retriever import parse_api_query
from delivery_sources import sha256


def build_names(database,output,minimum_free_gib=85):
    if output.exists():raise FileExistsError('Choose a new name index')
    if shutil.disk_usage(output.parent).free<minimum_free_gib*1024**3:raise OSError('Protected free-space floor reached')
    with closing(ReadOnlyIndexer(database,timeout=600).get_connection()) as source,closing(sqlite3.connect(output)) as con:
        con.execute('CREATE TABLE names(chunk_id TEXT PRIMARY KEY,version TEXT,api_name TEXT,parent_title TEXT,full_name TEXT,heading_text TEXT,module TEXT)')
        con.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)')
        rows=source.execute('SELECT chunk_id,version,api_name,parent_title,full_name,heading_text,module FROM doc_chunks')
        con.executemany('INSERT INTO names VALUES(?,?,?,?,?,?,?)',rows)
        for name,columns in [('name','api_name'),('owner_name','parent_title,api_name'),('full_name','full_name'),('heading','heading_text')]:
            quoted=','.join(c+' COLLATE NOCASE' for c in columns.split(','))
            con.execute('CREATE INDEX lookup_'+name+' ON names(version,'+quoted+')')
        count=con.execute('SELECT count(*) FROM names').fetchone()[0]
        assert count==source.execute('SELECT count(*) FROM doc_chunks').fetchone()[0]
        meta=dict(database_sha256=sha256(database),rows=count,case_insensitive_indexes=True)
        con.execute('INSERT INTO metadata VALUES(?,?)',('source',json.dumps(meta)));con.commit()
        assert con.execute('PRAGMA quick_check').fetchone()[0]=='ok'
    return meta


class Library:
    def __init__(self,path,names=None):
        self.path=Path(path);self.base=BodyLibrary(path)
        self.names=ReadOnlyIndexer(names or self.path.with_suffix('.names.db'))
        with closing(self.names.get_connection()) as con:meta=json.loads(con.execute("SELECT value FROM metadata WHERE key='source'").fetchone()[0])
        if sha256(self.path)!=meta['database_sha256']:raise ValueError('Name index belongs to a different body database')
    def search(self,query,version,limit=20,mode='keyword'):
        if mode!='name':return self.base.search(query,version,limit,mode)
        if not isinstance(query,str) or not query.strip() or len(query)>256:raise ValueError('Nonempty query up to 256 characters required')
        if type(limit) is not int or not 1<=limit<=100:raise ValueError('Limit must be 1..100')
        clean,parent,member=parse_api_query(query);ids={}
        with closing(self.base.indexer.get_connection()) as source,closing(self.names.get_connection()) as con:
            if not source.execute('SELECT 1 FROM sources WHERE release_id=?',(version,)).fetchone():raise ValueError('Unknown or missing release')
            conditions=[('full_name = ? COLLATE NOCASE',[clean],100),('api_name = ? COLLATE NOCASE',[clean],95),
                        ('heading_text = ? COLLATE NOCASE',[clean],90)]
            if parent:
                conditions.append(('parent_title = ? COLLATE NOCASE AND api_name = ? COLLATE NOCASE',[parent,member],98))
                # Keep the member retriever's module-shortcut form, e.g. http.createHttp().
                # Narrow by indexed api_name before matching the module suffix.
                suffix=parent.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
                conditions.append(("api_name = ? COLLATE NOCASE AND parent_title='' AND (module=? COLLATE NOCASE OR module LIKE ? ESCAPE '\\')",
                                   [member,parent,'%.'+suffix],85))
            for where,args,score in conditions:
                for row in con.execute('SELECT chunk_id FROM names WHERE version=? AND '+where+' LIMIT ?',[version,*args,limit]):ids[row[0]]=max(ids.get(row[0],0),score)
            if not ids:
                # Bounded prefix lookup; arbitrary substring search belongs in the full-text tool.
                prefix=clean.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
                for row in con.execute("SELECT chunk_id FROM names WHERE version=? AND api_name LIKE ? ESCAPE '\\' LIMIT ?",(version,prefix,limit)):ids[row[0]]=70
            result=[]
            for ident in sorted(ids,key=lambda i:(-ids[i],i))[:limit]:
                row=source.execute('''SELECT dc.*,e.origin,e.start_line,e.end_line,f.source_id,f.path,f.sha256 source_sha256,
                   f.status disposition,s.body source_body FROM doc_chunks dc JOIN chunk_evidence e USING(chunk_id)
                   JOIN files f USING(file_id) JOIN sources s ON s.source_id=f.source_id AND s.release_id=f.release_id
                   WHERE dc.chunk_id=?''',(ident,)).fetchone()
                if row is None:raise ValueError('Name index contains an orphan chunk')
                item=dict(row);item['source']=json.loads(item.pop('source_body'));item.pop('search_tokens',None)
                item['api_identity_status']='documentation_only';item['sdk_binding_verified']=False
                item['condition_status']='documentary_candidate_not_sdk_verified';result.append(item)
            return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--database',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build_names(a.database,a.output)))
