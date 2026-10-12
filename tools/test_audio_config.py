import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import sqlite3
from contextlib import closing
import subprocess
import sys
import zipfile

from collect_official_sources import ROOT, RELEASES, write_json
from extract_audio_config import OWNERS, extract_config, run
from extract_document_semantics import create_index, ingest, publish_batch
from query_document_candidates import resolve_database


class AudioConfigTests(unittest.TestCase):
    evidence={'source_id':'test','path':'audio.md','release_id':'fixed'}

    def test_old_required_and_new_optional_have_opposite_polarity(self):
        for flag,value,expected in [('必填','是',False),('必填','否',True),('可选','是',True),('可选','否',False)]:
            text=f'## AudioStreamInfo<sup>8+</sup>\n| 名称 | 类型 | {flag} | 说明 |\n| -- | -- | -- | -- |\n| channels | number | {value} | channels |\n'
            facts,warnings,coverage=extract_config(text,self.evidence)
            field=facts[1]
            self.assertEqual(field['optional'],expected)
            self.assertIsNone(field['read_only'])
            self.assertIsNone(field['metadata']['since'])
            self.assertEqual(field['parent_metadata']['since'],'8+')
            self.assertEqual(warnings,[]);self.assertTrue(coverage[0]['passed'])

    def test_field_metadata_readonly_and_deprecation_do_not_leak(self):
        text='## AudioRendererInfo<sup>8+</sup>\n**系统能力：** Parent.Cap\n| 名称 | 类型 | 只读 | 可选 | 说明 |\n| -- | -- | -- | -- | -- |\n| volumeMode<sup>19+</sup> | number | 是 | 是 | **系统能力：** Field.Cap |\n| content<sup>(deprecated)</sup> | number | 否 | 是 | old |\n'
        facts,warnings,_=extract_config(text,self.evidence)
        field=facts[1]
        self.assertEqual(field['metadata']['since'],'19+')
        self.assertEqual(field['metadata']['syscap'],'Field.Cap')
        self.assertEqual(field['parent_metadata']['syscap'],'Parent.Cap')
        self.assertTrue(field['read_only'])
        self.assertTrue(facts[2]['metadata']['deprecated_mentioned'])
        self.assertIsNone(facts[2]['metadata']['since'])
        self.assertEqual(warnings,[])

    def test_examples_nested_methods_and_other_types_are_excluded(self):
        text='## AudioRendererOptions\n```\n| 名称 | 类型 | 必填 | 说明 |\n| -- | -- | -- | -- |\n| fake | number | 是 | example |\n```\n| 名称 | 类型 | 必填 | 说明 |\n| -- | -- | -- | -- |\n| streamInfo | Info | 是 | real |\n### helper\n| 参数名 | 类型 |\n| -- | -- |\n| fake | number |\n## Other\n| 名称 | 类型 | 必填 | 说明 |\n| -- | -- | -- | -- |\n| other | number | 是 | other |\n'
        facts,warnings,coverage=extract_config(text,self.evidence)
        self.assertEqual([f['name'] for f in facts if f['kind']=='property'],['streamInfo'])
        self.assertEqual(warnings,[]);self.assertTrue(coverage[0]['passed'])

    def test_same_field_names_keep_different_owners_and_parents(self):
        text=''.join(f'## {owner}\n| 名称 | 类型 | 必填 | 说明 |\n| -- | -- | -- | -- |\n| streamInfo | Info | 是 | info |\n' for owner in ('AudioRendererOptions','AudioCapturerOptions'))
        facts,_,_=extract_config(text,self.evidence)
        fields=[f for f in facts if f['kind']=='property']
        self.assertEqual(len({f['record_id'] for f in fields}),2)
        self.assertNotEqual(fields[0]['parent_record_id'],fields[1]['parent_record_id'])

    def test_unknown_flags_and_bad_columns_fail_coverage(self):
        for row in ('| streamInfo | Info | unknown | info |','| streamInfo | Info | 是 | info | extra |'):
            text='## AudioRendererOptions\n| 名称 | 类型 | 必填 | 说明 |\n| -- | -- | -- | -- |\n'+row+'\n'
            facts,warnings,coverage=extract_config(text,self.evidence)
            self.assertTrue(warnings);self.assertFalse(coverage[0]['passed'])
            self.assertEqual(len(facts),1)

    def test_duplicate_field_names_do_not_pass_coverage(self):
        text='## AudioRendererOptions\n| 名称 | 类型 | 必填 | 说明 |\n| -- | -- | -- | -- |\n| streamInfo | Info | 是 | info |\n| streamInfo | Other | 否 | duplicate |\n'
        facts,_,coverage=extract_config(text,self.evidence)
        self.assertEqual(len(facts),3)
        self.assertFalse(coverage[0]['passed'])

    def test_cli_emits_utf8_even_when_process_default_is_ascii(self):
        base=ROOT/'data/delivery/test-temp';base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as temporary:
            out=Path(temporary);database=out/'pending.db'
            text='## AudioRendererOptions\n| 名称 | 类型 | 必填 | 说明 |\n| -- | -- | -- | -- |\n| streamInfo | Info | 是 | 音频流信息 |\n'
            facts,_,_=extract_config(text,self.evidence)
            with closing(sqlite3.connect(database)) as connection:create_index(connection);ingest(connection,facts)
            publish_batch(out,database,facts)
            result=subprocess.run([sys.executable,str(ROOT/'tools/query_document_candidates.py'),'--batch-root',str(out),'--release','fixed','--owner','AudioRendererOptions','--name','streamInfo'],capture_output=True,env={**os.environ,'PYTHONIOENCODING':'ascii'},check=True)
            field=json.loads(result.stdout.decode('utf-8'))['results'][0]
            self.assertEqual(field['option_flag_source'],'必填')
            self.assertEqual(field['description'],'音频流信息')

    def test_real_pipeline_failure_preserves_previous_active_batch(self):
        base=ROOT/'data/delivery/test-temp';base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as temporary:
            root=Path(temporary);sources=[];(root/'archives').mkdir()
            for index,(release,_) in enumerate(RELEASES):
                source={'source_id':str(index),'kind':'docs','body_status':'complete','release_id':f'OpenHarmony-{release}-Release','repository':'https://example.invalid/test','commit':'a'*40}
                path='zh-cn/application-dev/reference/apis-audio-kit/js-apis-audio.md'
                text=''.join(f'## {owner}<sup>8+</sup>\n| 名称 | 类型 | 必填 | 说明 |\n| -- | -- | -- | -- |\n| streamInfo | Info | 是 | info |\n' for owner in OWNERS)
                raw=text.encode();folder=root/'sources'/str(index);folder.mkdir(parents=True)
                ledger={'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'git_blob_sha':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()}
                (folder/'files.jsonl').write_text(json.dumps(ledger)+'\n',encoding='utf-8')
                with zipfile.ZipFile(root/'archives'/(str(index)+'.zip'),'w') as z:z.writestr('snapshot/'+path,raw)
                sources.append(source)
            write_json(root/'sources.json',{'sources':sources})
            report=run(root,root/'report.json');self.assertTrue(report['passed'])
            out=root/'structured/yu-audio-config';prior=(out/'current.json').read_bytes();database=resolve_database(out).read_bytes()
            sources[0]['release_id']='duplicate-bad-release';write_json(root/'sources.json',{'sources':sources})
            report=run(root,root/'report.json');self.assertFalse(report['passed'])
            self.assertEqual((out/'current.json').read_bytes(),prior)
            self.assertEqual(resolve_database(out).read_bytes(),database)


if __name__=='__main__':unittest.main()
