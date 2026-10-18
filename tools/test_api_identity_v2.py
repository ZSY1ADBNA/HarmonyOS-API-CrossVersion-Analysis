import json
import tempfile
from pathlib import Path
import unittest
import zipfile
from api_identity_v2 import api_id, canonical, declaration_id, migration_rows, source_id
from recover_unversioned_api import recover


def record(**kwargs):
    result=dict(declaration_id='decl:example',identity_status='resolved',platform='OpenHarmony',
                release_id='OpenHarmony-6.1-Release',language='arkts',scope=['module','@ohos.demo'],
                owners=[['namespace','demo'],['interface','Client']],kind='method',name='request',
                static=False,signature=['call',[],[['string',False,False]],'void',False],conditions=[])
    result.update(kwargs)
    return result


class IdentityTests(unittest.TestCase):
    def test_domain_encoding_and_delimiters(self):
        self.assertNotEqual(canonical(['a::b','c']),canonical(['a','b::c']))
        self.assertEqual(canonical(['中文',None,True,1]),'["中文",null,true,1]'.encode())
        for bad in [1.5,{},'\x00','\ud800']:
            with self.subTest(bad=repr(bad)),self.assertRaises((ValueError,UnicodeError)):canonical(bad)
    def test_source_snapshot_not_release(self):
        a=source_id('OpenHarmony','https://github.com/openharmony/interface_sdk-js','a'*40,'arkts_api')
        self.assertNotEqual(a,source_id('OpenHarmony','https://github.com/openharmony/interface_sdk-js','b'*40,'arkts_api'))
    def test_byte_span_and_path(self):
        self.assertNotEqual(declaration_id('src','api/a.d.ts',0,3,'ts-utf8'),declaration_id('src','api/a.d.ts',1,3,'ts-utf8'))
        for path in ['../a','/a','a\\b','a/./b','a//b','C:/a']:
            with self.subTest(path=path),self.assertRaises(ValueError):declaration_id('src',path,0,3,'ts-utf8')
    def test_boundaries(self):
        base=record()
        variants=[dict(scope=['module','@ohos.other']),dict(owners=[['namespace','other'],['interface','Client']]),
                  dict(signature=['call',[],[['number',False,False]],'void',False]),
                  dict(kind='constructor',name='<constructor>'),dict(kind='getter'),dict(kind='setter'),
                  dict(kind='call_signature',name='<call>'),dict(kind='index_signature',name='<index>'),
                  dict(signature=['call',[['T','string',None]],[['T',False,False]],'T',False]),
                  dict(signature=['call',[],[['string',True,False]],'void',False]),
                  dict(signature=['call',[],[['string',False,True]],'void',False]),
                  dict(signature=['call',[],[[['callback',['number'],'void'],False,False]],'void',False]),
                  dict(kind='export_alias',scope=['module','@kit.DemoKit']),
                  dict(scope=['global_file','api/global/a.d.ts']),dict(scope=['global_file','api/global/b.d.ts']),
                  dict(language='native',scope=['native_header','include/a.h'],conditions=[['arch','arm64']]),
                  dict(language='native',scope=['native_header','include/a.h'],conditions=[['arch','x86_64']]),
                  dict(static=True),dict(release_id='OpenHarmony-6.0-Release')]
        ids={api_id(base)}
        for variant in variants:
            ident=api_id(record(**variant));self.assertNotIn(ident,ids);ids.add(ident)
    def test_comment_line_and_location_not_logical_identity(self):
        self.assertEqual(api_id(record()),api_id(record(declaration_id='other',description='new',line=99,since_raw=None)))
    def test_unresolved_never_becomes_shared_unknown(self):
        self.assertIsNone(api_id(record(scope=None)))
        self.assertIsNone(api_id(record(identity_status='ambiguous')))
    def test_migration(self):
        a=record(declaration_id='a');b=record(declaration_id='b',name='other');c=record(declaration_id='c',scope=None)
        result=migration_rows({'single':['a'],'split':['a','b'],'unknown':['a','c'],'lost':[]},[a,b,c])
        self.assertEqual({x['legacy_id']:x['status'] for x in result},dict(single='one_to_one',split='one_to_many',unknown='ambiguous',lost='no_match'))
        self.assertFalse(next(x for x in result if x['legacy_id']=='split')['auto_redirect'])
    def test_quarantine_retains_since_and_missing(self):
        base=Path(__file__).resolve().parents[1]/'data/delivery/test-temp'
        base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as tmp:
            root=Path(tmp);archive=root/'fixture.zip';output=root/'q.db'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('snapshot/03_extracted_json/API/ets/a.json',json.dumps({'节点':[{'since_version':'12'},{'since_version':''}]}))
            self.assertEqual(recover(archive,output)['records'],2)
            with self.assertRaises(FileExistsError):recover(archive,output)


if __name__ == '__main__':unittest.main()
