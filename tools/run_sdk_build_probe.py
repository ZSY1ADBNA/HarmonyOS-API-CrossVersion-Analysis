"""Create and compile a minimal API11 project with the verified local public SDK."""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import zlib
from collect_official_sources import ROOT,write_json
from collect_public_sdk import digest


def save(project,path,text):
    target=project/path;target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Existing probe source differs; preserved')
    target.write_text(text,encoding='utf-8',newline='\n')


def summarize(project,sdk,deveco,returncode,output,timed_out=False,api_level=11,sdk_version='4.1.7.5'):
    output=re.sub(r'\x1b\[[0-9;]*m','',output)
    artifacts=[{'path':p.relative_to(project).as_posix(),'sha256':digest(p)} for p in (project/'entry/build').rglob('*.abc')]
    task_finished=bool(re.search(r'Finished[^\r\n]*CompileArkTS',output))
    # Exit zero without the requested task or bytecode is not compile evidence.
    succeeded=returncode==0 and task_finished and bool(artifacts) and not timed_out
    for prefix,replacement in [(str(project),'<probe_root>'),(str(sdk),'<sdk_root>'),(str(deveco),'<deveco_home>'),(str(Path.home()),'<user_home>')]:
        for variant in [prefix,prefix.replace('\\','\\\\'),prefix.replace('\\','/')]:output=output.replace(variant,replacement)
    tools={}
    for name,path,key in [('deveco',deveco/'product-info.json','version'),('hvigor',deveco/'tools/hvigor/hvigor/package.json','version'),('hvigor_plugin',deveco/'tools/hvigor/hvigor-ohos-plugin/package.json','version')]:
        if path.exists():tools[name]=json.loads(path.read_text(encoding='utf-8'))[key]
    sources=[{'path':p.relative_to(project).as_posix(),'sha256':digest(p)} for p in (project/'entry/src').rglob('*.ets')]
    return {'scope':'Real Hvigor CompileArkTS task; no device or shared database test','sdk_version':sdk_version,'api_level':api_level,
            'tool_versions':tools,'source_files':sources,'return_code':returncode,'timed_out':timed_out,'compile_task_finished':task_finished,
            'compiled_artifacts':artifacts,'compile_task_succeeded':succeeded,'output_tail':output[-5000:],'device_runtime_verified':False}


def prepare(project,sdk,api_level=11):
    save(project,'hvigorfile.js',"module.exports = { system: require(process.env.HVIGOR_OHOS_PLUGIN_PATH).appTasks };\n")
    save(project,'entry/hvigorfile.js',"module.exports = { system: require(process.env.HVIGOR_OHOS_PLUGIN_PATH).hapTasks };\n")
    save(project,'hvigor/hvigor-config.json5',json.dumps({'modelVersion':'5.0.0','dependencies':{},'execution':{'daemon':False,'incremental':False,'parallel':False}},indent=2)+'\n')
    save(project,'build-profile.json5',json.dumps({'app':{'signingConfigs':[],'products':[{'name':'default','compileSdkVersion':api_level,'compatibleSdkVersion':api_level,'targetSdkVersion':api_level,'runtimeOS':'OpenHarmony'}],'buildModeSet':[{'name':'debug'},{'name':'release'}]},'modules':[{'name':'entry','srcPath':'./entry','targets':[{'name':'default','applyToProducts':['default']}]}]},indent=2)+'\n')
    save(project,'entry/build-profile.json5',json.dumps({'apiType':'stageMode','buildOption':{},'targets':[{'name':'default','runtimeOS':'OpenHarmony'}]},indent=2)+'\n')
    save(project,'oh-package.json5',json.dumps({'modelVersion':'5.0.0','name':'sdk-probe','version':'1.0.0','dependencies':{}},indent=2)+'\n')
    save(project,'entry/oh-package.json5',json.dumps({'name':'entry','version':'1.0.0','dependencies':{}},indent=2)+'\n')
    save(project,'local.properties','sdk.dir='+sdk.as_posix()+'\n')
    save(project,'AppScope/app.json5',json.dumps({'app':{'bundleName':'org.example.sdkprobe','vendor':'probe','versionCode':1,'versionName':'1.0.0','icon':'$media:app_icon','label':'$string:app_name'}},indent=2)+'\n')
    save(project,'AppScope/resources/base/element/string.json',json.dumps({'string':[{'name':'app_name','value':'SDK Probe'}]})+'\n')
    save(project,'AppScope/resources/base/element/color.json',json.dumps({'color':[{'name':'start_window_background','value':'#FFFFFF'}]})+'\n')
    icon=project/'AppScope/resources/base/media/app_icon.png';icon.parent.mkdir(parents=True,exist_ok=True)
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',32,32,8,6,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\x30\x60\xa0\xff'*32)*32))+chunk(b'IEND',b'')
    if icon.exists() and icon.read_bytes()!=png:raise ValueError('Existing icon differs')
    icon.write_bytes(png)
    ability_entry_key='srcEntry' if api_level==15 else 'srcEntrance'
    save(project,'entry/src/main/module.json5',json.dumps({'module':{'name':'entry','type':'entry','mainElement':'EntryAbility','deviceTypes':['default'],'deliveryWithInstall':True,'installationFree':False,'pages':'$profile:main_pages','abilities':[{'name':'EntryAbility',ability_entry_key:'./ets/entryability/EntryAbility.ets','startWindowIcon':'$media:app_icon','startWindowBackground':'$color:start_window_background','exported':True,'skills':[{'entities':['entity.system.home'],'actions':['action.system.home']}]}]}},indent=2)+'\n')
    save(project,'entry/src/main/resources/base/profile/main_pages.json',json.dumps({'src':['pages/Index']})+'\n')
    save(project,'entry/src/main/ets/entryability/EntryAbility.ets',"import UIAbility from '@ohos.app.ability.UIAbility';\nimport window from '@ohos.window';\nexport default class EntryAbility extends UIAbility {\n  onWindowStageCreate(stage: window.WindowStage): void { stage.loadContent('pages/Index'); }\n}\n")
    save(project,'entry/src/main/ets/pages/Index.ets',"import audio from '@ohos.multimedia.audio';\nconst streamInfo: audio.AudioStreamInfo = {\n  samplingRate: audio.AudioSamplingRate.SAMPLE_RATE_48000,\n  channels: audio.AudioChannel.CHANNEL_2,\n  sampleFormat: audio.AudioSampleFormat.SAMPLE_FORMAT_S16LE,\n  encodingType: audio.AudioEncodingType.ENCODING_TYPE_RAW,\n  channelLayout: audio.AudioChannelLayout.CH_LAYOUT_STEREO\n};\n@Entry\n@Component\nstruct Index {\n  build() {\n    Column() {\n      Button('API 11 fontSize').fontSize(16)\n      Text('Channels: ' + streamInfo.channels)\n    }\n  }\n}\n")


def run(project,sdk,deveco,prepare_source=True,report_path=None,api_level=11,sdk_version='4.1.7.5'):
    for component in ['ets','js','toolchains']:
        metadata=json.loads((sdk/str(api_level)/component/'oh-uni-package.json').read_text(encoding='utf-8'))
        if metadata['version']!=sdk_version or str(metadata['apiVersion'])!=str(api_level):raise ValueError('Incomplete or wrong SDK component')
    if prepare_source:prepare(project,sdk,api_level)
    node=deveco/'tools/node/node.exe';cli=deveco/'tools/hvigor/hvigor/bin/hvigor.js'
    # Resolve the IDE's packaged name and subpaths only within this process.
    save(project,'resolve-bundled-hvigor.cjs',"const Module = require('module');\nconst path = require('path');\nconst original = Module._resolveFilename;\nconst installed = "+json.dumps((deveco/'tools/hvigor/hvigor').as_posix())+";\nModule._resolveFilename = function(name, ...args) {\n  if (name === '@ohos/hvigor') name = installed;\n  else if (name.startsWith('@ohos/hvigor/')) name = path.join(installed, name.slice('@ohos/hvigor/'.length));\n  return original.call(this, name, ...args);\n};\n")
    env={**os.environ,'JAVA_HOME':str(deveco/'jbr'),'NODE_HOME':str(node.parent),'HVIGOR_OHOS_PLUGIN_PATH':str(deveco/'tools/hvigor/hvigor-ohos-plugin')}
    command=[str(node),'--require',str(project/'resolve-bundled-hvigor.cjs'),str(cli),'--mode','module','-p','product=default','-p','module=entry@default','-p','buildMode=debug','assembleHap','--no-daemon','--no-parallel']
    timed_out=False
    try:
        result=subprocess.run(command,cwd=project,env=env,capture_output=True,timeout=240)
        returncode=result.returncode;raw=(result.stdout or b'')+(result.stderr or b'')
    except subprocess.TimeoutExpired as exc:
        timed_out=True;returncode=None;raw=(exc.stdout or b'')+(exc.stderr or b'')
    output=raw.decode('utf-8',errors='replace');(project/'build-output.log').write_text(output,encoding='utf-8')
    report=summarize(project,sdk,deveco,returncode,output,timed_out,api_level,sdk_version)
    write_json(report_path or ROOT/'docs/official-data-delivery/sdk-build-probe.json',report);print(json.dumps(report,ensure_ascii=False));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--deveco-home',type=Path,default=Path('C:/Program Files/Huawei/DevEco Studio'))
    parser.add_argument('--project',type=Path,default=ROOT/'data/delivery/sdk-build-probe-v2')
    parser.add_argument('--sdk-root',type=Path,default=ROOT/'data/delivery/sdk-packages/sdk-4.1')
    parser.add_argument('--unpack-sdk',action='store_true');args=parser.parse_args()
    if args.unpack_sdk:
        from verify_public_sdk_package import verify,unpack_components,cache_build_components
        base=ROOT/'data/delivery/sdk-packages'
        verified=verify(base/'ohos-4.1-public.tar.gz')
        if not verified['passed']:raise ValueError('SDK evidence checks failed')
        hashes=cache_build_components(base/'ohos-4.1-public.tar.gz',base/'windows-4.1')
        unpack_components(base/'windows-4.1',args.sdk_root/'11',hashes)
        write_json(ROOT/'docs/official-data-delivery/sdk-build-components.json',{'archive_sha256':verified['archive_sha256'],'component_hashes':hashes,'scope':'Five Windows build components from pinned official 4.1 archive'})
    result=run(args.project.resolve(),args.sdk_root.resolve(),args.deveco_home)
    if not result['compile_task_succeeded']:raise SystemExit(2)
