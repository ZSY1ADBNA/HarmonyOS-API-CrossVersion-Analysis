import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from collect_public_sdk import collect
from collect_official_sources import write_json


class Response(io.BytesIO):
    def __init__(self, data, status=200, headers=None):
        super().__init__(data)
        self.status = status
        self.headers = headers or {}
    def read1(self, size=-1):
        return self.read(size)


class SDKCollectionTests(unittest.TestCase):
    data = b'official-sdk-fixture'
    def checksum(self):
        return hashlib.sha256(self.data).hexdigest().encode()
    def receipt(self, root, offset):
        (root / 'ohos-4.1-public.tar.gz.part').write_bytes(self.data[:offset])
        write_json(root / 'ohos-4.1-public.json', {'url': 'https://repo.huaweicloud.com/openharmony/os/4.1-Release/ohos-sdk-windows_linux-public.tar.gz',
                                               'sha256': self.checksum().decode(), 'release': '4.1'})
    def test_short_response_is_resumed_and_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            replies = [Response(self.checksum()), Response(self.data[:5],206,{'Content-Range':f'bytes 0-{len(self.data)-1}/{len(self.data)}'}),
                       Response(self.data[5:],206,{'Content-Range':f'bytes 5-{len(self.data)-1}/{len(self.data)}'})]
            with patch('urllib.request.urlopen', side_effect=replies) as opened:
                collect('4.1', root)
                self.assertEqual(opened.call_count, 3)
            self.assertEqual((root / 'ohos-4.1-public.tar.gz').read_bytes(), self.data)
            self.assertEqual(json.loads((root / 'ohos-4.1-public.json').read_text(encoding='utf-8'))['status'],'archive_verified')
    def test_wrong_resume_start_preserves_previous_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);self.receipt(root, 5)
            with patch('urllib.request.urlopen', side_effect=[Response(self.checksum()), Response(self.data,206,{'Content-Range':f'bytes 0-{len(self.data)-1}/{len(self.data)}'})]):
                with self.assertRaisesRegex(ValueError,'exact requested range'):collect('4.1',root)
            self.assertEqual((root / 'ohos-4.1-public.tar.gz.part').read_bytes(),self.data[:5])
            self.assertFalse((root / 'ohos-4.1-public.tar.gz').exists())
    def test_complete_interrupted_partial_is_verified_before_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.receipt(root,len(self.data))
            with patch('urllib.request.urlopen',side_effect=[Response(self.checksum())]) as opened:collect('4.1',root)
            self.assertEqual(opened.call_count,1)
            self.assertEqual((root / 'ohos-4.1-public.tar.gz').read_bytes(),self.data)
    def test_zero_progress_and_oversize_range_fail(self):
        for data in [b'',self.data+b'excess']:
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp)
                with patch('urllib.request.urlopen',side_effect=[Response(self.checksum()),Response(data,206,{'Content-Range':f'bytes 0-{len(self.data)-1}/{len(self.data)}'})]):
                    with self.assertRaises(ValueError):collect('4.1',root)
                self.assertFalse((root/'ohos-4.1-public.tar.gz').exists())
    def test_mismatch_and_wrong_source_do_not_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch('urllib.request.urlopen',side_effect=[Response(self.checksum()),Response(b'x'*len(self.data),206,{'Content-Range':f'bytes 0-{len(self.data)-1}/{len(self.data)}'})]):
                with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):collect('4.1',root)
            partial=root/'ohos-4.1-public.tar.gz.part';before=partial.read_bytes()
            with patch('urllib.request.urlopen',side_effect=[Response(hashlib.sha256(b'changed').hexdigest().encode())]):
                with self.assertRaisesRegex(ValueError,'provenance differs'):collect('4.1',root)
            self.assertEqual(partial.read_bytes(),before)


if __name__ == '__main__':unittest.main()
