"""Recover historical JSON into a new quarantine SQLite DB; never connect Neo4j."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile


def recover(archive, output):
    if output.exists():
        raise FileExistsError('Choose a new quarantine database')
    entries = []
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            rel = '/'.join(item.filename.split('/')[1:])
            if rel.startswith('03_extracted_json/API/') and rel.endswith('.json'):
                raw = z.read(item)
                data = json.loads(raw)
                if not isinstance(data.get('节点'), list):
                    raise ValueError('Invalid historical JSON: ' + rel)
                entries.append((rel, raw, data))
    if not entries:
        raise ValueError('No historical API records')
    # Exclusive creation prevents an existing DB from being replaced, even after validation.
    with output.open('xb'):
        pass
    count = 0
    with closing(sqlite3.connect(output)) as con,con:
        con.execute('CREATE TABLE quarantine(id TEXT PRIMARY KEY,path TEXT,ordinal INTEGER,body TEXT,release_id TEXT,release_status TEXT,since_raw TEXT)')
        for path, raw, data in entries:
            blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            for index, node in enumerate(data['节点']):
                ident = hashlib.sha256(json.dumps([blob,path,index],ensure_ascii=False).encode()).hexdigest()
                con.execute('INSERT INTO quarantine VALUES(?,?,?,?,?,?,?)',
                            (ident,path,index,json.dumps(node,ensure_ascii=False),None,'source_release_unverified',node.get('since_version')))
                count += 1
    return {'files':len(entries),'records':count,'release_status':'source_release_unverified',
            'formal_recommendation_admitted':False,'graph_updated':False}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(recover(a.archive,a.output),ensure_ascii=True,indent=2))
