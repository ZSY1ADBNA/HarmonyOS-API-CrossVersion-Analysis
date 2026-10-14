"""Prepare verified API15 components in a fresh English path and compile two samples."""
import json
from pathlib import Path
import shutil
import time
import zipfile
from collect_official_sources import ROOT,write_json
from collect_public_sdk import digest
from verify_sdk503_samples import EXPECTED,SIZE
from verify_public_sdk_package import cache_build_components,unpack_components
from run_sdk_build_probe import run


def main():
    base=ROOT/'data/delivery/sdk-packages'
    archive=base/'ohos-5.0.3-public.tar.gz'
    components=base/'windows-5.0.3'
    receipt=base/'windows-5.0.3-components.json'
    if archive.stat().st_size!=SIZE:raise ValueError('Official archive length differs')
    started=time.monotonic()
    if receipt.exists():
        old=json.loads(receipt.read_text(encoding='utf-8'))
        hashes=old['component_hashes']
        if old['archive_sha256']!=EXPECTED or digest(archive)!=EXPECTED or any(digest(components/n)!=sha for n,sha in hashes.items()):
            raise ValueError('Existing component provenance differs; preserved')
    else:
        hashes=cache_build_components(archive,components,sdk_version='5.0.3.135',archive_sha=EXPECTED)
        write_json(receipt,{'archive_sha256':EXPECTED,'component_hashes':hashes})
    expected={f'{kind}-windows-x64-5.0.3.135-Release.zip' for kind in ['ets','js','native','previewer','toolchains']}
    if set(hashes)!=expected:raise ValueError('Expected five API15 components')
    sdk=Path('C:/Windows/Temp/openharmony-sdk-5.0.3')
    project=Path('C:/Windows/Temp/openharmony-sdk503-probe-v1')
    total=0
    for name in hashes:
        with zipfile.ZipFile(components/name) as z:total+=sum(i.file_size for i in z.infolist())
    if not sdk.exists() and shutil.disk_usage(sdk.parent).free<total+1024**3:
        raise ValueError('Not enough disk space for new isolated SDK; cached components preserved')
    sdk.mkdir(exist_ok=True)
    lock=sdk/'component-lock.json'
    context={'archive_sha256':EXPECTED,'component_hashes':hashes}
    if lock.exists() and json.loads(lock.read_text(encoding='utf-8'))!=context:
        raise ValueError('Existing SDK ownership differs; preserved')
    if not lock.exists():
        if list(sdk.iterdir()):raise ValueError('Nonempty unowned SDK directory; preserved')
        write_json(lock,context)
    unpack_components(components,sdk/'15',hashes)
    for kind in ['ets','js','native','previewer','toolchains']:
        meta=json.loads((sdk/'15'/kind/'oh-uni-package.json').read_text(encoding='utf-8'))
        if meta['version']!='5.0.3.135' or str(meta['apiVersion'])!='15':raise ValueError('Wrong API15 component metadata')
    write_json(ROOT/'docs/official-data-delivery/sdk503-build-components.json',{
        **context,'sdk_version':'5.0.3.135','api_level':15,'unpacked_bytes':total,
        'preparation_seconds':round(time.monotonic()-started,3),'scope':'Five verified official Windows API15 components in isolated SDK'})
    if project.exists():raise ValueError('Probe directory already exists; preserve and inspect before rerun')
    project.mkdir()
    report=run(project,sdk,Path('C:/Program Files/Huawei/DevEco Studio'),
               report_path=ROOT/'docs/official-data-delivery/sdk503-build-probe.json',api_level=15,sdk_version='5.0.3.135')
    if not report['compile_task_succeeded']:raise SystemExit(2)


if __name__=='__main__':main()
