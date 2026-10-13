"""Inspect a hash-verified official 4.1 SDK, not a source-repository substitute."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path,PurePosixPath
import shutil
import tarfile
import tempfile
import zipfile
from collect_official_sources import ROOT,write_json
from collect_public_sdk import digest
from verify_sample_declarations import inspect,match_declaration
from verify_sdk_inheritance import inspect_chain

EXPECTED_SHA='67d532368880bef8a11ef2c7caa812501f19922c5815e59d1ca46b4460e1bdf9'
MEMBER='ohos-sdk/windows/ets-windows-x64-4.1.7.5-Release.zip'
COMPONENTS={MEMBER,'ohos-sdk/windows/js-windows-x64-4.1.7.5-Release.zip','ohos-sdk/windows/toolchains-windows-x64-4.1.7.5-Release.zip'}


def verify(archive):
    if digest(archive)!=EXPECTED_SHA:raise ValueError('Official SDK archive fingerprint mismatch')
    raw=None;component_hashes={}
    with tarfile.open(archive,'r|gz') as t:
        for member in t:
            if member.name in COMPONENTS:
                if not member.isfile() or member.size>128*1024*1024:raise ValueError('Unexpected ETS component')
                payload=t.extractfile(member).read();component_hashes[PurePosixPath(member.name).name]=hashlib.sha256(payload).hexdigest()
                if member.name==MEMBER:raw=payload
                if len(component_hashes)==3:break
    if raw is None or len(component_hashes)!=3:raise ValueError('Windows SDK component missing')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate SDK ZIP member')
        meta=json.loads(z.read('ets/oh-uni-package.json'))
        if meta.get('version')!='4.1.7.5' or str(meta.get('apiVersion'))!='11' or meta.get('releaseType')!='Release':raise ValueError('SDK package metadata mismatch')
        paths=['ets/component/button.d.ts','ets/component/common.d.ts','ets/api/@ohos.multimedia.audio.d.ts']
        files=[{'id':p,'path':p,'text':z.read(p).decode('utf-8-sig')} for p in paths]
        parsed=inspect(files);facts=[]
        for name,owner,path in [('fontSize','ButtonAttribute',paths[0]),('channelLayout','AudioStreamInfo',paths[2]),('volumeMode','AudioRendererInfo',paths[2]),('AudioVolumeMode','audio',paths[2])]:
            evidence={'platform':'OpenHarmony','sdk_version':meta['version'],'api_level':11,'archive_sha256':EXPECTED_SHA,
                      'component_member':MEMBER,'component_sha256':hashlib.sha256(raw).hexdigest(),'path':path,'file_sha256':hashlib.sha256(z.read(path)).hexdigest()}
            item=match_declaration(parsed[path],owner,name,evidence)
            if item:
                item['sdk_public_status']='present_in_verified_public_sdk_package'
                item['scope']='Declaration in hash-verified Windows ETS Public SDK 4.1.7.5/API11; build and device execution are separate'
            facts.append({'name':name,'owner':owner,'declaration':item,'present':item is not None})
        chain=inspect_chain([{'path':f['path'],'text':f['text']} for f in files[:2]])
        checks={'metadata_matches':True,'all_selected_files_parse':all(not p['diagnostics'] for p in parsed.values()),
            'fontSize_and_channelLayout_present':all(f['present'] for f in facts[:2]),
            'channelLayout_optional_and_type_match':facts[1]['present'] and facts[1]['declaration']['optional'] and facts[1]['declaration']['declared_type']=='AudioChannelLayout',
            'audio_default_export_present':'export default audio;' in files[2]['text'],
            'button_minFontScale_not_in_complete_chain':chain['status']=='member_absent_in_complete_selected_chain',
            'volume_not_declared_in_selected_public_audio_module':all(not f['present'] for f in facts[2:])}
        return {'schema_version':1,'component_metadata':meta,'archive_sha256':EXPECTED_SHA,'component_hashes':component_hashes,'facts':facts,'inheritance':chain,
                'checks':checks,'passed':all(checks.values()),'scope':'Only named declarations in official Windows ETS Public SDK 4.1.7.5/API11',
                'application_compile_verified':False,'device_runtime_verified':False}


def unpack_components(component_dir,sdk_root,expected_hashes):
    """Preserve existing bytes and reject traversal/symlinks before writing SDK files."""
    names=set(expected_hashes)
    kinds={n.split('-')[0] for n in names}
    if len(names) not in (3,5) or kinds not in ({'ets','js','toolchains'},{'ets','js','toolchains','native','previewer'}):raise ValueError('Expected verified SDK component set')
    if any(PurePosixPath(n).name!=n or '\\' in n or ':' in n for n in names):raise ValueError('Unsafe component filename')
    components=[component_dir/n for n in sorted(names)]
    for archive in components:
        if archive.name not in expected_hashes or digest(archive)!=expected_hashes[archive.name]:raise ValueError('Cached component differs from verified parent archive')
        with zipfile.ZipFile(archive) as z:
            if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate component paths')
            for info in z.infolist():
                path=PurePosixPath(info.filename)
                target=sdk_root.joinpath(*path.parts)
                if path.is_absolute() or '..' in path.parts or '\\' in info.orig_filename or not target.resolve().is_relative_to(sdk_root.resolve()):raise ValueError('Unsafe SDK extraction path')
                if ((info.external_attr>>16)&0o170000)==0o120000:raise ValueError('SDK symlink not materialized')
                if info.is_dir():continue
                raw=z.read(info)
                if target.exists():
                    if target.read_bytes()!=raw:raise ValueError('Existing SDK file differs; preserved')
                else:
                    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)


def cache_build_components(archive,component_dir):
    """Stream all five Windows components from the pinned official archive."""
    if digest(archive)!=EXPECTED_SHA:raise ValueError('Official SDK archive fingerprint mismatch')
    component_dir.mkdir(parents=True,exist_ok=True)
    names={f'{kind}-windows-x64-4.1.7.5-Release.zip' for kind in ['ets','js','toolchains','native','previewer']}
    hashes={}
    with tarfile.open(archive,'r|gz') as t:
        for member in t:
            name=PurePosixPath(member.name).name
            if member.name!='ohos-sdk/windows/'+name or name not in names:continue
            if name in hashes or not member.isfile() or not 0<member.size<=2*1024**3:raise ValueError('Invalid Windows component')
            target=component_dir/name
            fd,tmp=tempfile.mkstemp(prefix='sdk-component-',suffix='.part',dir=component_dir)
            try:
                with os.fdopen(fd,'wb') as out,t.extractfile(member) as source:shutil.copyfileobj(source,out,1024*1024)
                tmp=Path(tmp)
                if tmp.stat().st_size!=member.size:raise ValueError('Incomplete SDK component')
                value=digest(tmp)
                if target.exists():
                    if digest(target)!=value:raise ValueError('Existing cached SDK differs; preserved')
                else:tmp.replace(target)
                hashes[name]=value
                print(json.dumps({'verified_component':name,'size':member.size}),flush=True)
            finally:
                Path(tmp).unlink(missing_ok=True)
    if set(hashes)!=names:raise ValueError('Required Windows build component missing')
    return hashes


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--unpack',action='store_true')
    parser.add_argument('--cache-build-components',action='store_true');args=parser.parse_args()
    base=ROOT/'data/delivery/sdk-packages';report=verify(base/'ohos-4.1-public.tar.gz')
    write_json(ROOT/'docs/official-data-delivery/public-sdk-4.1-verification.json',report)
    if args.cache_build_components:
        hashes=cache_build_components(base/'ohos-4.1-public.tar.gz',base/'windows-4.1')
        write_json(ROOT/'docs/official-data-delivery/sdk-build-components.json',{'archive_sha256':report['archive_sha256'],'component_hashes':hashes,'scope':'Five Windows build components from pinned official 4.1 archive; unpack/build not implied'})
    if args.unpack and report['passed']:unpack_components(base/'windows-4.1',base/'sdk-4.1/11',report['component_hashes'])
    print(json.dumps({'passed':report['passed'],'sdk':report['component_metadata'],'checks':report['checks']}))
    if not report['passed']:raise SystemExit(2)
