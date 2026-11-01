"""Repair only the owned failed API15 manifest, then rerun the same sample."""
import json
from pathlib import Path
from run_sdk_build_probe import run
from collect_public_sdk import digest
from collect_official_sources import ROOT,write_json

project=Path('C:/Windows/Temp/openharmony-sdk503-probe-v1')
report_path=ROOT/'docs/official-data-delivery/sdk503-build-probe.json'
previous=json.loads(report_path.read_text(encoding='utf-8'))
if previous['compile_task_succeeded'] or previous['api_level']!=15 or previous['sdk_version']!='5.0.3.135':
    raise ValueError('Expected owned failed API15 build')
if any(digest(project/x['path'])!=x['sha256'] for x in previous['source_files']):
    raise ValueError('Probe source changed; preserved')
path=project/'entry/src/main/module.json5'
manifest=json.loads(path.read_text(encoding='utf-8'))
ability=manifest['module']['abilities'][0]
if ability.get('srcEntrance')!='./ets/entryability/EntryAbility.ets' or 'srcEntry' in ability:
    raise ValueError('Unexpected manifest baseline; preserved')
write_json(ROOT/'docs/official-data-delivery/sdk503-build-first-failure.json',previous)
ability['srcEntry']=ability.pop('srcEntrance')
path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
result=run(project,Path('C:/Windows/Temp/openharmony-sdk-5.0.3'),Path('C:/Program Files/Huawei/DevEco Studio'),
           prepare_source=False,report_path=report_path,api_level=15,sdk_version='5.0.3.135')
if not result['compile_task_succeeded']:raise SystemExit(2)
