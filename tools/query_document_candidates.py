"""Read-only, bounded queries over the isolated documentary candidate pilot."""
import argparse
import hashlib
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
import sys

from collect_official_sources import ROOT


def resolve_database(out):
    manifest=out/'current.json'
    if not manifest.exists():return out/'candidate-search.db'
    saved=json.loads(manifest.read_text(encoding='utf-8'))
    paths={}
    for key in ('database','candidates'):
        entry=saved[key];path=(out/entry['path']).resolve()
        if not path.is_relative_to(out.resolve()):raise ValueError('Batch path escaped data root')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Batch fingerprint mismatch')
        paths[key]=path
    return paths['database']


def open_readonly(path):
    connection=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    connection.execute('PRAGMA query_only=ON')
    return connection


def search(connection,release,query=None,owner=None,name=None,kind=None,limit=10):
    if type(limit) is not int or not 1<=limit<=100:raise ValueError('limit must be an integer between 1 and 100')
    if not query and not name:raise ValueError('Provide a query or exact name')
    filters=['e.release_id=?'];values=[release]
    for field,value in [('owner',owner),('name',name),('kind',kind)]:
        if value is not None:filters.append('e.'+field+'=?');values.append(value)
    join=''
    if query:
        if any(ord(char)>127 and not char.isspace() for char in query):
            raise ValueError('Pilot supports English identifiers; Chinese natural-language search is not validated')
        tokens=re.findall(r'[A-Za-z0-9_]+',query)
        if not tokens:raise ValueError('Pilot supports English identifiers; Chinese natural-language search is not validated')
        expression=' AND '.join('"'+token+'"' for token in tokens)
        join=' JOIN entity_fts f ON e.rowid=f.rowid'
        filters.append('entity_fts MATCH ?');values.append(expression)
    rows=connection.execute('SELECT e.payload FROM entities e'+join+' WHERE '+' AND '.join(filters)+' ORDER BY e.owner,e.kind,e.name,e.id LIMIT ?',values+[limit]).fetchall()
    fields=('record_id','evidence','kind','name','owner','line','end_line','context_start_line','signature',
            'parent_record_id','metadata','parent_metadata','declared_type','parameter_binding_status',
            'api_identity_status','sdk_public_status','optional','read_only','option_flag_source','description',
            'enum_value','declaration_layout')
    return [{key:fact[key] for key in fields if key in fact} for (payload,) in rows for fact in [json.loads(payload)]]


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__)
    location=p.add_mutually_exclusive_group()
    location.add_argument('--database',type=Path)
    location.add_argument('--batch-root',type=Path,default=ROOT/'data/delivery/structured/yu-semantic-pilot')
    p.add_argument('--release',required=True);p.add_argument('--query');p.add_argument('--owner');p.add_argument('--name')
    p.add_argument('--kind',choices=['method','parameter','property','enum_type','enum_member','component_attribute','component_constructor','config_interface'])
    p.add_argument('--limit',type=int,default=10);args=p.parse_args()
    database=args.database or resolve_database(args.batch_root)
    with closing(open_readonly(database)) as connection:
        results=search(connection,args.release,args.query,args.owner,args.name,args.kind,args.limit)
    print(json.dumps({'release_id':args.release,'results':results,'count':len(results),
                      'status':'candidate_matches' if results else 'no_candidate_matches',
                      'scope':'Documentary pilot; absence does not establish API absence; SDK public scope unverified'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
