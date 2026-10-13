"""Check that the real API11 compiler rejects absent sample properties."""
import json
from pathlib import Path
import re
import uuid
from collect_official_sources import ROOT,write_json
from run_sdk_build_probe import prepare,run


def main():
    sdk=Path('C:/Windows/Temp/openharmony-sdk-4.1')
    ide=Path('C:/Program Files/Huawei/DevEco Studio')
    results=[]
    for field,owner in [('minFontScale','ButtonAttribute'),('volumeMode','AudioRendererInfo')]:
        project=Path('C:/Windows/Temp')/('openharmony-negative-'+field+'-'+uuid.uuid4().hex[:8])
        prepare(project,sdk)
        target=project/'entry/src/main/ets/pages/Index.ets'
        source=target.read_text(encoding='utf-8')
        if field=='minFontScale':
            marker="Button('API 11 fontSize').fontSize(16)"
            assert source.count(marker)==1
            source=source.replace(marker,marker+'.minFontScale(0.5)',1)
        else:
            extra="const rendererInfo: audio.AudioRendererInfo = { content: audio.ContentType.CONTENT_TYPE_MUSIC, usage: audio.StreamUsage.STREAM_USAGE_MUSIC, rendererFlags: 0 };\nconst unsupportedMode = rendererInfo.volumeMode;\n"
            assert source.count('@Entry')==1
            source=source.replace('@Entry',extra+'@Entry',1)
        target.write_text(source,encoding='utf-8',newline='\n')
        report_path=ROOT/'docs/official-data-delivery'/('sdk-negative-'+field+'.json')
        result=run(project,sdk,ide,prepare_source=False,report_path=report_path)
        log=(project/'build-output.log').read_text(encoding='utf-8')
        expected=bool(re.search(r"Property ['\"]"+field+r"['\"] does not exist on type ['\"]"+owner,log))
        result.update(expected_outcome='Reject absent property in API11',field=field,owner=owner,
                      expected_diagnostic_seen=expected,negative_control_passed=expected and result['return_code'] not in (None,0) and not result['timed_out'])
        write_json(report_path,result)
        results.append({'field':field,'passed':result['negative_control_passed']})
        if not result['negative_control_passed']:break
    summary={'sdk_version':'4.1.7.5','api_level':11,'results':results,'passed':len(results)==2 and all(x['passed'] for x in results),'device_runtime_verified':False}
    write_json(ROOT/'docs/official-data-delivery/sdk-negative-controls.json',summary)
    print(json.dumps(summary))
    if not summary['passed']:raise SystemExit(2)


if __name__=='__main__':main()
