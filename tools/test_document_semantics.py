import sqlite3
import unittest
from contextlib import closing
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from collect_official_sources import ROOT,write_json
from extract_document_semantics import extract,create_index,ingest


class SemanticTests(unittest.TestCase):
    evidence={'source_id':'source','release_id':'fixed','path':'test.md','commit':'a'*40,'source_sha256':'b'*64}

    def test_overloads_and_parameter_property_separation(self):
        text='# Interface (AudioRenderer)\n## 属性\n| 名称 | 类型 | 只读 |\n| -- | -- | -- |\n| state<sup>8+</sup> | AudioState | 是 |\n## setVolume<sup>9+</sup>\nsetVolume(volume: number): Promise<void>\n**系统能力：** Cap.Audio\n| 参数名 | 类型 | 说明 |\n| -- | -- | -- |\n| volume | number | value |\n## setVolume<sup>9+</sup>\nsetVolume(volume: number, callback: Callback<void>): void\n| 参数名 | 类型 | 说明 |\n| -- | -- | -- |\n| volume | number | value |\n| callback | Callback<void> | callback |\n'
        facts,warnings=extract(text,self.evidence,'audio_renderer')
        self.assertEqual(warnings,[])
        methods=[f for f in facts if f['kind']=='method']
        self.assertEqual(len(methods),2)
        self.assertNotEqual(methods[0]['record_id'],methods[1]['record_id'])
        self.assertEqual(methods[0]['metadata']['syscap'],'Cap.Audio')
        self.assertEqual(methods[0]['metadata']['since'],'9+')
        self.assertEqual([f['name'] for f in facts if f['kind']=='property'],['state'])
        self.assertTrue(all(f['parent_record_id'] in {m['record_id'] for m in methods} for f in facts if f['kind']=='parameter'))

    def test_legacy_audio_interface_scope_excludes_other_interface(self):
        text='# Audio\n## AudioRenderer\n### setVolume\nsetVolume(volume: number): void\n## Other\n### setVolume\nsetVolume(volume: string): void\n'
        facts,_=extract(text,self.evidence,'audio_renderer')
        self.assertEqual(len([f for f in facts if f['kind']=='method']),1)

    def test_two_c_enum_layouts_and_inline_since(self):
        old='# Errors\n### 枚举\n| 名称 | 描述 |\n| -- | -- |\n| [OH_AVErrCode](core.md) {<br/>AV_ERR_OK = 0,<br/>AV_ERR_OTHER = 100<br/>} | error |\n'
        new='# Errors\n### OH_AVErrCode\n**起始版本：** 9\n| 枚举项 | 描述 |\n| -- | -- |\n| AV_ERR_OK = 0 | OK |\n| AV_ERR_OTHER = 100 | Error<br>**起始版本：** 12 |\n'
        a,_=extract(old,self.evidence,'av_error_codes');b,_=extract(new,self.evidence,'av_error_codes')
        self.assertEqual([(f['name'],f['signature']) for f in a],[(f['name'],f['signature']) for f in b])
        self.assertEqual(b[1]['metadata']['since'],'12')
        self.assertEqual(b[1]['parent_metadata']['since'],'9')

    def test_index_repeat_and_payload_change_do_not_leave_stale_fts(self):
        facts,_=extract('# Interface (AudioRenderer)\n## setVolume\nsetVolume(volume: number): void\n',self.evidence,'audio_renderer')
        with sqlite3.connect(':memory:') as conn:
            create_index(conn);ingest(conn,facts);ingest(conn,facts)
            self.assertEqual(conn.execute('SELECT count(*) FROM entities').fetchone()[0],1)
            modified=[{**facts[0],'raw_content':'new_unique_text'}];ingest(conn,modified)
            conn.execute("INSERT INTO entity_fts(entity_fts,rank) VALUES('integrity-check',1)")
            self.assertEqual(conn.execute("SELECT count(*) FROM entity_fts WHERE entity_fts MATCH 'new_unique_text'").fetchone()[0],1)
            with self.assertRaises(ValueError):ingest(conn,facts+facts)
            self.assertEqual(conn.execute('SELECT count(*) FROM entities').fetchone()[0],1)

    def test_example_and_ambiguous_table_do_not_create_false_properties(self):
        facts,_=extract('# Button\n## 示例\n```ts\nButton().fontSize(30)\n```\n',self.evidence,'arkui_button')
        self.assertEqual(facts,[])
        text='# Interface (AudioRenderer)\n## 属性\n| 名称 | 类型 |\n| -- | -- |\n| wrong | type | extra |\n'
        facts,warnings=extract(text,self.evidence,'audio_renderer')
        self.assertEqual(facts,[]);self.assertTrue(warnings)

    def test_shared_table_does_not_fabricate_overload_parameter_binding(self):
        text='# Interface (AudioRenderer)\n## setVolume\nsetVolume(volume: number): Promise<void>\nsetVolume(volume: number, callback: Callback): void\n| 参数名 | 类型 |\n| -- | -- |\n| callback | Callback |\n'
        facts,warnings=extract(text,self.evidence,'audio_renderer')
        self.assertEqual(len([f for f in facts if f['kind']=='method']),2)
        self.assertFalse(any(f['kind']=='parameter' for f in facts))
        self.assertTrue(any(w['status']=='shared_table_overload_binding_requires_review' for w in warnings))

    def test_return_table_is_not_a_parameter_or_property(self):
        text='# Interface (AudioRenderer)\n## getState\ngetState(): Promise<AudioState>\n**返回值：**\n| 类型 | 说明 |\n| -- | -- |\n| Promise<AudioState> | state |\n'
        facts,warnings=extract(text,self.evidence,'audio_renderer')
        self.assertEqual(warnings,[])
        self.assertEqual(len(facts),1)
        self.assertEqual(facts[0]['return_values'][0]['fields']['类型'],'Promise<AudioState>')

    def test_same_named_state_is_bound_to_each_audio_interface(self):
        text='# Audio\n## AudioRenderer\n| 名称 | 类型 |\n| -- | -- |\n| state | AudioState |\n## AudioCapturer\n| 名称 | 类型 |\n| -- | -- |\n| state | AudioState |\n'
        renderer,_=extract(text,self.evidence,'audio_renderer')
        capturer,_=extract(text,self.evidence,'audio_capturer')
        self.assertEqual(renderer[0]['owner'],'AudioRenderer')
        self.assertEqual(capturer[0]['owner'],'AudioCapturer')
        self.assertNotEqual(renderer[0]['record_id'],capturer[0]['record_id'])

    def test_parameter_since_does_not_overwrite_method_since(self):
        text='# Interface (AudioRenderer)\n## configure<sup>8+</sup>\nconfigure(value: number): void\n| 参数名 | 类型 | 说明 |\n| -- | -- | -- |\n| value | number | extra option<br>**起始版本：** 12 |\n'
        facts,warnings=extract(text,self.evidence,'audio_renderer')
        self.assertEqual(warnings,[])
        self.assertEqual(next(f['metadata']['since'] for f in facts if f['kind']=='method'),'8+')
        self.assertEqual(next(f['metadata']['since'] for f in facts if f['kind']=='parameter'),'12')

    def test_component_attribute_is_not_an_interface_method(self):
        text='# Button\n## 属性\n### fontSize\nfontSize(value: number): ButtonAttribute\n| 参数名 | 类型 |\n| -- | -- |\n| value | number |\n'
        facts,warnings=extract(text,self.evidence,'arkui_button')
        self.assertEqual(warnings,[])
        attribute=next(f for f in facts if f['kind']=='component_attribute')
        parameter=next(f for f in facts if f['kind']=='parameter')
        self.assertEqual(attribute['owner'],'Button')
        self.assertEqual(parameter['parent_record_id'],attribute['record_id'])
        self.assertFalse(any(f['kind'] in ('method','property') for f in facts))

    def test_failed_real_pipeline_preserves_previous_verified_artifacts(self):
        base=ROOT/'data/delivery/test-temp';base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as temporary:
            root=Path(temporary);path='zh-cn/application-dev/reference/apis-audio-kit/js-apis-audio.md'
            raw=b'# Audio\n## AudioRenderer\n### getState\ngetState(): AudioState\n'
            write_json(root/'sources.json',{'sources':[{'source_id':'fixture','kind':'docs','release_id':'test',
                                                       'commit':'a'*40,'body_status':'complete','repository':'https://example.invalid/fixture'}]})
            folder=root/'sources/fixture';folder.mkdir(parents=True)
            (folder/'files.jsonl').write_text(json.dumps({'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'git_blob_sha':'b'*40})+'\n',encoding='utf-8')
            (root/'archives').mkdir()
            with zipfile.ZipFile(root/'archives/fixture.zip','w') as archive:archive.writestr('snapshot/'+path,raw)
            out=root/'structured/yu-semantic-pilot';out.mkdir(parents=True)
            database=out/'candidate-search.db'
            with closing(sqlite3.connect(database)) as conn:conn.execute('CREATE TABLE sentinel(value TEXT)');conn.commit()
            before=database.read_bytes();(out/'candidates.jsonl').write_bytes(b'previous verified candidates\n')
            result=subprocess.run([sys.executable,str(ROOT/'tools/extract_document_semantics.py'),'--root',str(root),'--report',str(root/'report.json')],capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(result.returncode,2,result.stderr)
            self.assertEqual(database.read_bytes(),before)
            self.assertEqual((out/'candidates.jsonl').read_bytes(),b'previous verified candidates\n')
            self.assertFalse(json.loads((root/'report.json').read_text(encoding='utf-8'))['passed'])


if __name__=='__main__':unittest.main()
