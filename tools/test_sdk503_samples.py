import copy
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from verify_sdk503_samples import comparison, declarations, published_component, MEMBER


class SDK503Tests(unittest.TestCase):
    def test_wrong_published_metadata_refused_before_parser(self):
        for meta in [{'version':'4.1.7.5','apiVersion':'15','releaseType':'Release'},
                     {'version':'5.0.3.135','apiVersion':'11','releaseType':'Release'},
                     {'version':'5.0.3.135','apiVersion':'15','releaseType':'Beta'}]:
            with self.subTest(meta=meta):
                payload=io.BytesIO()
                with zipfile.ZipFile(payload,'w') as z:z.writestr('ets/oh-uni-package.json',json.dumps(meta))
                with patch('verify_sdk503_samples.inspect') as parser:
                    with self.assertRaisesRegex(ValueError,'metadata'):declarations(payload.getvalue())
                    parser.assert_not_called()

    def test_component_cache_is_verified_and_modified_bytes_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'sdk.tar.gz';body=b'ETS fixture'
            with tarfile.open(p,'w:gz') as t:
                info=tarfile.TarInfo(MEMBER);info.size=len(body);t.addfile(info,io.BytesIO(body))
            with patch('verify_sdk503_samples.SIZE',p.stat().st_size),patch('verify_sdk503_samples.EXPECTED',hashlib.sha256(p.read_bytes()).hexdigest()):
                self.assertEqual(published_component(p),body)
                with patch('verify_sdk503_samples.tarfile.open') as scanned:
                    self.assertEqual(published_component(p),body);scanned.assert_not_called()
                cache=p.parent/'windows-5.0.3-ets.zip';cache.write_bytes(b'manual edit')
                with self.assertRaisesRegex(ValueError,'preserved'):published_component(p)
                self.assertEqual(cache.read_bytes(),b'manual edit')

    def test_signature_equality_does_not_hide_annotation_difference(self):
        old={'signature':'f(): void;','optional':False,'kind':'method','declared_type':'void','parameters':[],
             'metadata':{'since_raw':['11']},'ancestor_metadata':{}}
        new=copy.deepcopy(old);new['metadata']['since_raw'].append('15')
        result=comparison(old,new)
        self.assertTrue(result['signature']['equal'])
        self.assertFalse(result['metadata']['equal'])


if __name__=='__main__':unittest.main()
