"""Read-only, hash-guarded evidence queries for two members in two releases."""
import argparse
import hashlib
import json
from pathlib import Path
from collect_official_sources import ROOT,write_json

DIRECTORY=ROOT/'docs/official-data-delivery'
MANIFEST='verified-sample-query-manifest.json'
SPECS={'4.1':('OpenHarmony-4.1-Release',11,'4.1.7.5','API4.1','public-sdk-4.1-verification.json','sdk-build-probe.json'),
       '5.0.3':('OpenHarmony-5.0.3-Release',15,'5.0.3.135','API5.0','public-sdk-5.0.3-samples.json','sdk503-build-probe.json')}
TARGETS={'fontSize':('ButtonAttribute','method','ArkUI globals','ets/component/button.d.ts'),
         'channelLayout':('AudioStreamInfo','property','@ohos.multimedia.audio','ets/api/@ohos.multimedia.audio.d.ts')}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def read_json(path):
    if path.stat().st_size>512*1024:raise ValueError('Evidence size exceeds bounded sample scope')
    raw=path.read_bytes()
    text=raw.decode('utf-8')
    if '\ufffd' in text:raise ValueError('Evidence contains replacement characters')
    return json.loads(text),raw


def write_manifest(directory=DIRECTORY):
    names=sorted({name for spec in SPECS.values() for name in spec[-2:]})
    manifest={'schema_version':1,'scope':'Two selected declarations and recorded builds; no device claim',
              'files':{name:sha(read_json(directory/name)[1]) for name in names}}
    target=directory/MANIFEST
    if target.exists() and read_json(target)[0]!=manifest:raise ValueError('Existing manifest differs; explicit review required')
    write_json(target,manifest)
    return manifest


def load_catalog(directory=DIRECTORY):
    manifest,raw_manifest=read_json(directory/MANIFEST)
    expected={name for spec in SPECS.values() for name in spec[-2:]}
    if manifest.get('schema_version')!=1 or set(manifest.get('files',{}))!=expected:raise ValueError('Unexpected manifest scope')
    reports={}
    for name,expected_hash in manifest['files'].items():
        report,raw=read_json(directory/name)
        if sha(raw)!=expected_hash:raise ValueError('Evidence fingerprint mismatch: '+name)
        reports[name]=report
    catalog=[]
    for release,(release_id,level,version,graph_tag,sdk_file,build_file) in SPECS.items():
        sdk=reports[sdk_file];build=reports[build_file];meta=sdk['component_metadata']
        if not sdk.get('passed') or meta['version']!=version or str(meta['apiVersion'])!=str(level) or meta.get('releaseType')!='Release':raise ValueError('Published SDK identity mismatch')
        if not build.get('compile_task_succeeded') or build['api_level']!=level or build['sdk_version']!=version or not build.get('compiled_artifacts'):raise ValueError('Recorded build identity mismatch')
        for name,(owner,kind,module,path) in TARGETS.items():
            matches=[f for f in sdk['facts'] if f.get('name')==name and f.get('declaration')]
            if len(matches)!=1:raise ValueError('Ambiguous selected declaration')
            declaration=matches[0]['declaration'];e=declaration['evidence']
            if declaration['owner']!=owner or declaration['kind']!=kind or type(declaration['optional']) is not bool or declaration.get('sdk_public_status')!='present_in_verified_public_sdk_package':raise ValueError('Selected declaration identity mismatch')
            if e['platform']!='OpenHarmony' or e['sdk_version']!=version or e['api_level']!=level or e['path']!=path:raise ValueError('Selected declaration provenance mismatch')
            catalog.append({'platform':'OpenHarmony','release':release,'release_id':release_id,'api_level':level,
                'sdk_version':version,'project_graph_tag':graph_tag,'name':name,'owner':owner,'kind':kind,'module':module,
                'signature':declaration['signature'],'optional':declaration['optional'],
                'parameters':declaration['parameters'],'declared_type':declaration['declared_type'],
                'metadata':declaration['metadata'],'ancestor_metadata':declaration['ancestor_metadata'],
                'sdk_evidence':e,'sdk_archive_url':f'https://repo.huaweicloud.com/openharmony/os/{release}-Release/ohos-sdk-windows_linux-public.tar.gz',
                'evidence_report':sdk_file,'evidence_report_sha256':manifest['files'][sdk_file],
                'recorded_compile_report':build_file,'recorded_compile_report_sha256':manifest['files'][build_file],
                'recorded_compile_status':'passed','manifest_sha256':sha(raw_manifest),
                'team_global_identity_assigned':False,'device_runtime_verified':False,
                'verification_scope':'Hash-checked committed declaration and build reports; no SDK extraction or compilation executed by query'})
    return catalog


def query(catalog,release,name):
    records=[r for r in catalog if r['release']==release and r['name']==name]
    return {'status':'verified_sample_found' if records else 'no_verified_sample','records':records,
            'absence_in_sdk_proven':False}


def compare(catalog,old_release,new_release,name):
    old=query(catalog,old_release,name)['records'];new=query(catalog,new_release,name)['records']
    if len(old)!=1 or len(new)!=1:return {'status':'insufficient_verified_evidence','absence_in_sdk_proven':False}
    fields=['signature','optional','declared_type','parameters','metadata','ancestor_metadata']
    return {'status':'selected_declarations_compared','name':name,'old':old[0],'new':new[0],
            'differences':{k:{'old':old[0][k],'new':new[0][k]} for k in fields if old[0][k]!=new[0][k]},
            'device_behavior_equivalence_verified':False,'team_cross_version_identity_assigned':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-manifest',action='store_true')
    parser.add_argument('--release',default='4.1')
    parser.add_argument('--name',default='channelLayout')
    parser.add_argument('--compare-with')
    args=parser.parse_args()
    if args.write_manifest:write_manifest()
    catalog=load_catalog()
    result=compare(catalog,args.release,args.compare_with,args.name) if args.compare_with else query(catalog,args.release,args.name)
    print(json.dumps(result,ensure_ascii=True,indent=2))
