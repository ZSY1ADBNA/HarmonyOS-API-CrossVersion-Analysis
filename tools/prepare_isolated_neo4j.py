"""Prepare a pinned Neo4j distribution for an isolated loopback-only test."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import time
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
VERSION='5.26.32'
URL='https://dist.neo4j.org/neo4j-community-'+VERSION+'-windows.zip'
EXPECTED='00eca54f38f601b3adb596611505280a4784d9726c6df5f0b72b7a4a04cc87ec'
BASE=ROOT/'data/delivery/isolated-neo4j'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destination',type=Path);args=parser.parse_args()
    BASE.mkdir(parents=True,exist_ok=True)
    archive=BASE/('neo4j-community-'+VERSION+'-windows.zip')
    with urllib.request.urlopen(URL+'.sha256',timeout=30) as r:actual=r.read(1024).decode().strip().split()[0]
    if actual!=EXPECTED:raise ValueError('Official checksum changed; recheck version before use')
    if not archive.exists():
        partial=archive.with_suffix('.zip.part')
        if partial.exists():raise ValueError('Incomplete earlier download retained; explicit recovery required')
        started=time.monotonic();received=0
        with urllib.request.urlopen(URL,timeout=45) as source,partial.open('xb') as out:
            while True:
                block=source.read(1024*1024)
                if not block:break
                received+=len(block)
                if received>512*1024*1024 or time.monotonic()-started>300:raise ValueError('Download size/time bound exceeded; partial preserved')
                out.write(block)
        if digest(partial)!=EXPECTED:raise ValueError('Downloaded archive fingerprint mismatch; partial preserved')
        partial.replace(archive)
    if digest(archive)!=EXPECTED:raise ValueError('Existing archive differs; preserved')
    extraction=args.destination or BASE/'distribution';root=extraction.resolve()
    with zipfile.ZipFile(archive) as z:
        infos=z.infolist()
        if len({i.orig_filename for i in infos})!=len(infos):raise ValueError('Duplicate archive paths')
        if sum(i.file_size for i in infos)>2*1024**3:raise ValueError('Unexpected expanded size')
        for i in infos:
            path=PurePosixPath(i.orig_filename)
            target=extraction.joinpath(*path.parts)
            if path.is_absolute() or '..' in path.parts or '\\' in i.orig_filename or ':' in i.orig_filename or not target.resolve().is_relative_to(root):raise ValueError('Unsafe archive path')
            if ((i.external_attr>>16)&0o170000)==0o120000:raise ValueError('Archive symlink rejected')
            if i.is_dir():continue
            raw=z.read(i)
            if target.exists():
                if target.read_bytes()!=raw:raise ValueError('Existing distribution file differs; preserved')
            else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    home=extraction/('neo4j-community-'+VERSION)
    for f in ['bin/neo4j.bat','bin/neo4j-admin.bat','conf/neo4j.conf']:
        if not (home/f).is_file():raise ValueError('Distribution incomplete')
    report={'version':VERSION,'url':URL,'checksum_url':URL+'.sha256','archive_sha256':EXPECTED,
      'archive_bytes':archive.stat().st_size,'archive_verified':True,'distribution_extracted':True,
      'scope':'Distribution prepared only; server not started and no database connected',
      'proposed_bolt':'127.0.0.1:17687','proposed_http':'127.0.0.1:17474',
      'java_compatibility_source':'https://neo4j.com/docs/operations-manual/5/installation/requirements/',
      'server_started':False,'shared_database_updated':False}
    target=ROOT/'docs/official-data-delivery/isolated-neo4j-setup.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report))


if __name__=='__main__':main()
