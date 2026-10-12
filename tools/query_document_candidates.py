"""Read-only, bounded queries over the isolated documentary candidate pilot."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3

from collect_official_sources import ROOT


def open_readonly(path):
    connection=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    connection.execute('PRAGMA query_only=ON')
    return connection


def search(connection,release,query=None,owner=None,name=None,kind=None,limit=10):
    if not 1<=limit<=100:raise ValueError('limit must be between 1 and 100')
    if not query and not name:raise ValueError('Provide a query or exact name')
    filters=['e.release_id=?'];values=[release]
    for field,value in [('owner',owner),('name',name),('kind',kind)]:
        if value is not None:filters.append('e.'+field+'=?');values.append(value)
    join=''
    if query:
        tokens=re.findall(r'[A-Za-z0-9_]+',query)
        if not tokens:raise ValueError('Pilot supports English identifiers; Chinese natural-language search is not validated')
        expression=' AND '.join('"'+token+'"' for token in tokens)
        join=' JOIN entity_fts f ON e.rowid=f.rowid'
        filters.append('entity_fts MATCH ?');values.append(expression)
    rows=connection.execute('SELECT e.payload FROM entities e'+join+' WHERE '+' AND '.join(filters)+' ORDER BY e.owner,e.kind,e.name,e.id LIMIT ?',values+[limit]).fetchall()
    fields=('record_id','evidence','kind','name','owner','line','end_line','context_start_line','signature',
            'parent_record_id','metadata','parent_metadata','declared_type','parameter_binding_status',
            'api_identity_status','sdk_public_status')
    return [{key:fact[key] for key in fields if key in fact} for (payload,) in rows for fact in [json.loads(payload)]]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--database',type=Path,default=ROOT/'data/delivery/structured/yu-semantic-pilot/candidate-search.db')
    p.add_argument('--release',required=True);p.add_argument('--query');p.add_argument('--owner');p.add_argument('--name')
    p.add_argument('--kind',choices=['method','parameter','property','enum_member','component_attribute','component_constructor'])
    p.add_argument('--limit',type=int,default=10);args=p.parse_args()
    with closing(open_readonly(args.database)) as connection:
        results=search(connection,args.release,args.query,args.owner,args.name,args.kind,args.limit)
    print(json.dumps({'release_id':args.release,'results':results,'count':len(results),
                      'status':'candidate_matches' if results else 'no_candidate_matches',
                      'scope':'Documentary pilot; absence does not establish API absence; SDK public scope unverified'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
