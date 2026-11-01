"""Receive an exact external snapshot into a fresh directory, with protected free space."""
import argparse,json,shutil
from pathlib import Path,PurePosixPath
from delivery_sources import sha256

def inspect(manifest,destination,reserve_gib=30):
    manifest=Path(manifest).resolve();destination=Path(destination).resolve()
    if destination.exists():raise FileExistsError('Use a fresh reception directory; partial runs are preserved')
    if not destination.parent.is_dir():raise ValueError('Reception parent must already exist')
    if destination.is_relative_to(manifest.parent) or manifest.parent.is_relative_to(destination):raise ValueError('Source and reception directories must be separate')
    lock=json.loads(manifest.read_text(encoding='utf8'));paths=set();total=0
    for entry in lock['artifacts'].values():
        name=entry['path'];relative=PurePosixPath(name)
        if relative.is_absolute() or any(s in name for s in ('\\',':','\x00')) or any(s in ('','.','..') for s in name.split('/')):raise ValueError('Unsafe snapshot path')
        if name in paths or type(entry['bytes']) is not int or entry['bytes']<0:raise ValueError('Invalid snapshot inventory')
        paths.add(name);total+=entry['bytes']
    free=shutil.disk_usage(destination.parent).free;required=total+int(reserve_gib*1024**3)+1024**2
    return dict(source_manifest_sha256=sha256(manifest),delivery_id=lock['delivery_id'],files=len(paths),data_bytes=total,
                free_bytes=free,required_free_bytes=required,reserve_gib=reserve_gib,capacity_ok=free>=required,
                destination=str(destination),data_copied=False,independent_acceptance=False)

def receive(manifest,destination,reserve_gib=30,expected_manifest_sha256=None):
    manifest=Path(manifest).resolve();destination=Path(destination).resolve()
    runtime_root=Path(__file__).resolve().parents[1]
    if (runtime_root/'runtime-lock.json').is_file():
        from run_locked_runtime import validate
        validate(runtime_root,manifest)
    if expected_manifest_sha256 is not None and sha256(manifest)!=expected_manifest_sha256:raise ValueError('Manifest differs from selected runtime package')
    plan=inspect(manifest,destination,reserve_gib)
    if not plan['capacity_ok']:raise ValueError('Insufficient capacity to preserve protected free space; no reception directory created')
    lock=json.loads(manifest.read_text(encoding='utf8'));destination.mkdir();received=[]
    for label,entry in lock['artifacts'].items():
        source=(manifest.parent/entry['path']).resolve()
        if not source.is_relative_to(manifest.parent) or source.is_symlink():raise ValueError('Source escapes snapshot')
        if source.stat().st_size!=entry['bytes'] or sha256(source)!=entry['sha256']:raise ValueError('Source fingerprint differs: '+label)
        if shutil.disk_usage(destination).free<entry['bytes']+int(reserve_gib*1024**3)+1024**2:raise ValueError('Space changed during reception; partial files preserved')
        output=destination/entry['path'];output.parent.mkdir(parents=True,exist_ok=True);partial=output.with_name(output.name+'.part')
        with source.open('rb') as src,partial.open('xb') as dst:
            for block in iter(lambda:src.read(4*1024**2),b''):
                if shutil.disk_usage(destination).free<int(reserve_gib*1024**3)+len(block)+1024**2:
                    raise ValueError('Space changed during reception; partial files preserved')
                dst.write(block)
        if partial.stat().st_size!=entry['bytes'] or sha256(partial)!=entry['sha256']:raise ValueError('Received fingerprint differs: '+label)
        partial.rename(output);received.append(label)
    target=destination/'evidence-manifest-v2.json';target.write_bytes(manifest.read_bytes())
    if sha256(target)!=plan['source_manifest_sha256']:raise ValueError('Manifest changed during reception')
    plan.update(data_copied=True,received=received)
    (destination/'reception-receipt.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return plan

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--destination',required=True);p.add_argument('--preflight',action='store_true');p.add_argument('--report');p.add_argument('--expected-manifest-sha256');a=p.parse_args()
    if a.report and Path(a.report).exists():raise FileExistsError('Preserve historical reception reports')
    result=inspect(a.manifest,a.destination) if a.preflight else receive(a.manifest,a.destination,expected_manifest_sha256=a.expected_manifest_sha256)
    if a.report:
        report=Path(a.report)
        if report.exists():raise FileExistsError('Preserve historical reception reports')
        report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))
