"""Regressions for reproduced parser, publication and collection failures."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from collect_official_sources import ROOT, collect, write_json
from extract_document_semantics import extract, publish_batch
from pilot_document_structure import heading_spans
from query_document_candidates import resolve_database, search
from scan_official_materials import scan, cached_scan
import test_material_collection


class BugfixTests(unittest.TestCase):
    evidence={'source_id':'test','path':'test.md','release_id':'test'}

    def temp(self):
        base=ROOT/'data/delivery/test-temp';base.mkdir(parents=True,exist_ok=True)
        return tempfile.TemporaryDirectory(dir=base)

    def test_fenced_signature_table_and_metadata_are_examples(self):
        text='# Interface (AudioRenderer)\n## start\n```ts\nstart(fake: number): void\n| 参数名 | 类型 |\n| -- | -- |\n| fake | number |\n**起始版本：** 99\n```\nstart(): void\n**起始版本：** 9\n'
        facts,_=extract(text,self.evidence,'audio_renderer')
        self.assertEqual(len(facts),1)
        self.assertEqual(facts[0]['signature'],'start(): void')
        self.assertEqual(facts[0]['metadata']['since'],'9')
        self.assertIn('fake',facts[0]['raw_content'])

    def test_real_and_counterfeit_interface_containers(self):
        text='# Interface (AudioRenderer)\n## start\nstart(): void\n# Interface (Other)\n## start\nstart(fake: number): void\n'
        facts,_=extract(text,self.evidence,'audio_renderer')
        self.assertEqual(len(facts),1)
        fake='```\n# Interface (AudioRenderer)\n```\n# Interface (Other)\n## start\nstart(): void\n'
        self.assertEqual(extract(fake,self.evidence,'audio_renderer')[0],[])
        with self.assertRaises(ValueError):extract(text,self.evidence,'typo')

    def test_language_suffix_does_not_close_fence(self):
        text='# Real\n```\n```ts\n# Fake\n```\n# Second\n'
        sections=heading_spans(text)
        self.assertEqual([s['heading'] for s in sections],['Real','Second'])
        self.assertEqual(''.join(s['text'] for s in sections),text)

    def test_batch_publication_failure_preserves_active_generation(self):
        with self.temp() as temp:
            out=Path(temp);first=out/'first.db';first.write_bytes(b'first')
            publish_batch(out,first,[{'batch':1}]);prior=(out/'current.json').read_bytes()
            second=out/'second.db';second.write_bytes(b'second')
            with patch('extract_document_semantics.write_json',side_effect=OSError('injected publication failure')):
                with self.assertRaises(OSError):publish_batch(out,second,[{'batch':2}])
            self.assertEqual((out/'current.json').read_bytes(),prior)
            self.assertEqual(resolve_database(out).read_bytes(),b'first')
            resolve_database(out).write_bytes(b'changed')
            with self.assertRaises(ValueError):resolve_database(out)

    def test_unsupported_query_constraints_are_not_silently_discarded(self):
        for query,limit in [('播放 AudioRenderer',10),('state',True),('state',1.5)]:
            with self.assertRaises(ValueError):search(None,'test',query=query,limit=limit)

    def test_imported_lock_is_enforced_on_full_collection(self):
        for constraints in ({'expected_archive_sha256':'0'*64},{'expected_file_count':2}):
            with self.temp() as temp:
                root=Path(temp);(root/'archives').mkdir()
                with zipfile.ZipFile(root/'archives/test.zip','w') as archive:archive.writestr('snapshot/LICENSE',b'license')
                source={'source_id':'test','kind':'samples','status':'locked','repository_name':'test','commit':'a'*40,**constraints}
                result=collect(source,root,'archive')
                self.assertEqual(result['status'],'collection_failed')
                self.assertIn('imported lock',result['error'])
                self.assertFalse((root/'verified-results/test.json').exists())

    def test_symlink_is_fingerprinted_and_reported_as_unresolved(self):
        with self.temp() as temp:
            root=Path(temp);(root/'archives').mkdir()
            info=zipfile.ZipInfo('snapshot/link');info.create_system=3;info.external_attr=0o120777<<16
            with zipfile.ZipFile(root/'archives/test.zip','w') as archive:archive.writestr(info,b'target')
            result=collect({'source_id':'test','kind':'samples','status':'locked','repository_name':'test','commit':'a'*40},root,'archive')
            self.assertEqual(result['body_status'],'complete_with_unresolved_dependencies')
            self.assertEqual(result['file_count'],1)
            entry=json.loads((root/'sources/test/files.jsonl').read_text())
            self.assertEqual(entry['size'],6);self.assertTrue(entry['git_blob_sha'])

    def test_incomplete_scan_receipt_is_rejected(self):
        with self.temp() as temp:
            root=Path(temp);source=test_material_collection.MaterialsTests().fixture(root,'docs',{'zh-cn/test.md':b'# Heading'})
            (root/'archives').mkdir();archive=root/'archives/fixture.zip'
            with zipfile.ZipFile(archive,'w') as z:z.writestr('snapshot/zh-cn/test.md',b'# Heading')
            from collect_official_sources import file_sha256
            source['archive_sha256']=file_sha256(archive);scan(source,root)
            receipt=root/'structured/yu-materials/fixture/scan-receipt.json'
            saved=json.loads(receipt.read_text());saved['outputs_sha256']={};write_json(receipt,saved)
            self.assertIsNone(cached_scan(source,root))


if __name__=='__main__':unittest.main()
