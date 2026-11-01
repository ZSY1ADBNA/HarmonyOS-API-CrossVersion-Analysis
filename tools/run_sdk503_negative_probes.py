"""Two API15 negative builds, guarded by verified published declarations."""
import hashlib
import argparse
import json
from pathlib import Path
import re
import uuid
import zipfile
from collect_official_sources import ROOT,write_json
from run_sdk_build_probe import prepare,run
from verify_sample_declarations import inspect
from verify_sdk_inheritance import inspect_chain


def diagnostic_seen(log,field,owner):
    pattern=r"(?m)^\s*Property ['\"]"+re.escape(field)+r"['\"] does not exist on type ['\"]"+re.escape(owner)+r"['\"]"
    return bool(re.search(pattern,log))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--field',choices=['all','minFontScale','volumeMode'],default='all')
    selected=parser.parse_args().field
    evidence=json.loads((ROOT/'docs/official-data-delivery/public-sdk-5.0.3-samples.json').read_text(encoding='utf-8'))
    if not evidence['passed'] or evidence['component_metadata']['version']!='5.0.3.135':
        raise ValueError('Verified API15 declarations required')
    component=ROOT/'data/delivery/sdk-packages/windows-5.0.3-ets.zip'
    expected=evidence['facts'][0]['declaration']['evidence']['component_sha256']
    if hashlib.sha256(component.read_bytes()).hexdigest()!=expected:raise ValueError('Published component changed')
    with zipfile.ZipFile(component) as z:
        paths=['ets/component/button.d.ts','ets/component/common.d.ts','ets/api/@ohos.multimedia.audio.d.ts']
        files=[{'id':p,'path':p,'text':z.read(p).decode('utf-8-sig')} for p in paths]
    chain=inspect_chain(files[:2])
    audio=inspect([files[2]])[paths[2]]
    if chain['status']!='member_absent_in_complete_selected_chain' or audio['diagnostics'] or any(f['owner']=='AudioRendererInfo' and f['name']=='volumeMode' for f in audio['facts']):
        raise ValueError('Expected absent API15 fields not established')
    sdk=Path('C:/Windows/Temp/openharmony-sdk-5.0.3')
    ide=Path('C:/Program Files/Huawei/DevEco Studio')
    results=[]
    for field,owner in [('minFontScale','ButtonAttribute'),('volumeMode','AudioRendererInfo')]:
        if selected!='all' and field!=selected:
            previous=json.loads((ROOT/'docs/official-data-delivery'/('sdk503-negative-'+field+'.json')).read_text(encoding='utf-8'))
            if previous['api_level']!=15 or previous['sdk_version']!='5.0.3.135' or not previous.get('negative_control_passed'):
                raise ValueError('Cannot carry forward unverified negative control')
            results.append({'field':field,'passed':True,'carried_forward':True})
            continue
        project=Path('C:/Windows/Temp')/('openharmony-api15-negative-'+field+'-'+uuid.uuid4().hex[:8])
        if project.exists():raise ValueError('Existing negative probe preserved')
        prepare(project,sdk,api_level=15)
        target=project/'entry/src/main/ets/pages/Index.ets'
        source=target.read_text(encoding='utf-8')
        if field=='minFontScale':
            marker="Button('API 11 fontSize').fontSize(16)"
            if source.count(marker)!=1:raise ValueError('Unexpected positive sample')
            source=source.replace(marker,marker+'.minFontScale(0.5)',1)
        else:
            extra="const rendererInfo: audio.AudioRendererInfo = { content: audio.ContentType.CONTENT_TYPE_MUSIC, usage: audio.StreamUsage.STREAM_USAGE_MUSIC, rendererFlags: 0 };\nconst unsupportedMode: number = rendererInfo.volumeMode;\n"
            if source.count('@Entry')!=1:raise ValueError('Unexpected positive sample')
            source=source.replace('@Entry',extra+'@Entry',1)
        target.write_text(source,encoding='utf-8',newline='\n')
        report_path=ROOT/'docs/official-data-delivery'/('sdk503-negative-'+field+'.json')
        result=run(project,sdk,ide,prepare_source=False,report_path=report_path,api_level=15,sdk_version='5.0.3.135')
        log=(project/'build-output.log').read_text(encoding='utf-8')
        expected_diagnostic=diagnostic_seen(log,field,owner)
        result.update(field=field,owner=owner,expected_outcome='Reject absent property in API15',
                      expected_diagnostic_seen=expected_diagnostic,
                      negative_control_passed=expected_diagnostic and result['return_code'] not in (None,0) and not result['timed_out'])
        write_json(report_path,result)
        results.append({'field':field,'passed':result['negative_control_passed']})
        if not result['negative_control_passed']:break
    summary={'sdk_version':'5.0.3.135','api_level':15,'published_button_chain_status':chain['status'],
             'results':results,'execution_fields':['minFontScale','volumeMode'] if selected=='all' else [selected],
             'passed':len(results)==2 and all(x['passed'] for x in results),
             'scope':'Real negative compilation of two published-SDK-absent fields; not device execution',
             'device_runtime_verified':False,'shared_database_updated':False}
    write_json(ROOT/'docs/official-data-delivery/sdk503-negative-controls.json',summary)
    print(json.dumps(summary,ensure_ascii=True))
    if not summary['passed']:raise SystemExit(2)


if __name__=='__main__':main()
