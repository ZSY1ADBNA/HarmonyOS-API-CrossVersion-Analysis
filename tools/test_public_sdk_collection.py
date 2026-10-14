import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
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
    def test_503_large_official_length_is_bounded_and_partial_preserved(self):
        for size, accepted in [(4563988878, True),(4563988878+1, False),(5 * 1024 ** 3 + 1, False)]:
            with self.subTest(size=size), tempfile.TemporaryDirectory() as temp:
                root=Path(temp)
                replies=[Response(self.checksum()),Response(self.data,206,{'Content-Range':f'bytes 0-{len(self.data)-1}/{size}'})]+[TimeoutError('Expected transfer interruption')]*3
                with patch('urllib.request.urlopen',side_effect=replies),patch('time.sleep'):
                    with self.assertRaises(TimeoutError if accepted else ValueError):collect('5.0.3',root)
                partial=root/'ohos-5.0.3-public.tar.gz.part'
                self.assertEqual(partial.read_bytes() if partial.exists() else b'',self.data if accepted else b'')
                self.assertFalse((root/'ohos-5.0.3-public.tar.gz').exists())
    def test_known_incomplete_partial_skips_full_scan_before_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.receipt(root,5)
            receipt=json.loads((root/'ohos-4.1-public.json').read_text(encoding='utf-8'))
            receipt['size']=len(self.data);write_json(root/'ohos-4.1-public.json',receipt)
            from collect_public_sdk import digest
            with patch('collect_public_sdk.digest',wraps=digest) as scanned,patch('urllib.request.urlopen',side_effect=[Response(self.checksum()),Response(self.data[5:],206,{'Content-Range':f'bytes 5-{len(self.data)-1}/{len(self.data)}'})]):
                collect('4.1',root)
                self.assertEqual(scanned.call_count,1)
            self.assertEqual((root/'ohos-4.1-public.tar.gz').read_bytes(),self.data)
    def test_transient_network_failure_has_bounded_retry(self):
        for exhausted in [False, True]:
            with self.subTest(exhausted=exhausted),tempfile.TemporaryDirectory() as temp:
                replies=[Response(self.checksum()),urllib.error.URLError('Expected TLS failure')]
                replies += [urllib.error.URLError('Expected TLS failure')]*2 if exhausted else [Response(self.data,206,{'Content-Range':f'bytes 0-{len(self.data)-1}/{len(self.data)}'})]
                with patch('urllib.request.urlopen',side_effect=replies) as opened,patch('time.sleep'):
                    if exhausted:
                        with self.assertRaises(urllib.error.URLError):collect('4.1',Path(temp))
                        self.assertEqual(opened.call_count,4)
                    else:
                        collect('4.1',Path(temp))
                        self.assertEqual((Path(temp)/'ohos-4.1-public.tar.gz').read_bytes(),self.data)
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
