"""Immutable archive-backed official sources; never trust a missing expanded directory."""
import argparse
from collections import Counter
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()


def safe_relative(value):
    p=PurePosixPath(value)
    if not value or p.is_absolute() or any(x in value for x in ('\\','\x00',':')) or any(x in ('','.','..') for x in value.split('/')):
        raise ValueError('Unsafe source path')
    return value


class ArchiveSource:
    def __init__(self, source, data=ROOT/'data/delivery', verify_archive=True):
        if not re.fullmatch('[0-9a-f]{64}',source['source_id']):
            raise ValueError('Invalid archive source ID')
        self.source=source;self.data=Path(data);self.archive=self.data/'archives'/(source['source_id']+'.zip')
        ledger_name=source.get('ledger_basename','files.jsonl')
        if '/' in ledger_name or '\\' in ledger_name or ledger_name in ('.','..'):raise ValueError('Invalid source ledger name')
        ledger=self.data/'sources'/source['source_id']/ledger_name
        self.files={}
        with ledger.open(encoding='utf8') as stream:
            for line in stream:
                row=json.loads(line);p=safe_relative(row['path'])
                if p in self.files:raise ValueError('Duplicate source ledger path')
                self.files[p]=row
        if len(self.files)!=source['file_count']:raise ValueError('Source count differs from manifest')
        if verify_archive and sha256(self.archive)!=source['archive_sha256']:
            raise ValueError('Archive differs from fixed source lock')
        self.zip=zipfile.ZipFile(self.archive);self.members={}
        try:
            roots=set()
            for info in self.zip.infolist():
                if info.is_dir():continue
                parts=info.filename.split('/',1)
                if len(parts)!=2:raise ValueError('Archive root missing')
                roots.add(parts[0])
                if len(roots)>1:raise ValueError('Mixed archive roots')
                rel=safe_relative(parts[1])
                if rel in self.members:raise ValueError('Duplicate archive member')
                self.members[rel]=info
            missing=set(self.files)-set(self.members)
            if missing:raise ValueError('Archive lacks ledger files: '+str(len(missing)))
        except Exception:
            self.zip.close();raise

    def __enter__(self):return self
    def __exit__(self,*args):self.zip.close()

    def read(self, path):
        row=self.files[safe_relative(path)]
        if row['status'] not in ('collected','symlink_not_materialized'):
            raise ValueError('Unresolved source entry: '+row['status'])
        raw=self.zip.read(self.members[path])
        if len(raw)!=row['size'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise ValueError('Original file fingerprint mismatch: '+path)
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob!=(row.get('payload_git_blob_sha') or row['git_blob_sha']):
            raise ValueError('Git source fingerprint mismatch: '+path)
        return raw


def audit(data, output, manifest_path=None):
    manifest_path=manifest_path or data/'sources.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf8'))
    results=[];started=time.monotonic()
    for source in manifest['sources']:
        row={k:source.get(k) for k in ('source_id','release_id','kind','repository','commit','archive_sha256')}
        try:
            with ArchiveSource(source,data) as reader:
                count=0;byte_count=0
                for path in reader.files:
                    raw=reader.read(path);count+=1;byte_count+=len(raw)
                row.update(status='archive_and_files_verified',files=count,bytes=byte_count,
                           access='archive_backed',expanded_directory_required=False)
        except (OSError,ValueError,KeyError,zipfile.BadZipFile,RuntimeError) as exc:
            row.update(status='input_unavailable_or_invalid',reason=type(exc).__name__+': '+str(exc)[:250])
        results.append(row)
        report={'schema_version':1,'source_lock_sha256':sha256(manifest_path),'sources':results,
                'complete':len(results)==len(manifest['sources']),'summary':dict(Counter(r['status'] for r in results)),
                'elapsed_seconds':round(time.monotonic()-started,2)}
        output.parent.mkdir(parents=True,exist_ok=True)
        tmp=output.with_suffix('.building');tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n');tmp.replace(output)
        print(source['kind'],source['release_id'],row['status'],row.get('files',0),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,default=ROOT/'data/delivery');p.add_argument('--output',type=Path,required=True);p.add_argument('--manifest',type=Path)
    a=p.parse_args();audit(a.data,a.output,a.manifest)
