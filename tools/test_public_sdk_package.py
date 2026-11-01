import hashlib
import io
from pathlib import Path
import tempfile
import tarfile
import unittest
from unittest.mock import patch
import zipfile
from verify_public_sdk_package import unpack_components,cache_build_components


class SDKUnpackTests(unittest.TestCase):
    def build_archive(self,root,kinds):
        archive=root/'sdk.tar.gz'
        with tarfile.open(archive,'w:gz') as t:
            for kind in kinds:
                payload=(kind+'-fixture').encode()
                info=tarfile.TarInfo(f'ohos-sdk/windows/{kind}-windows-x64-4.1.7.5-Release.zip');info.size=len(payload)
                t.addfile(info,io.BytesIO(payload))
        return archive,hashlib.sha256(archive.read_bytes()).hexdigest()

    def test_all_five_components_cached_without_overwriting_changed_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cache=root/'cache'
            archive,sha=self.build_archive(root,['ets','js','native','previewer','toolchains'])
            with patch('verify_public_sdk_package.EXPECTED_SHA',sha):
                hashes=cache_build_components(archive,cache)
                self.assertEqual(len(hashes),5)
                self.assertEqual(cache_build_components(archive,cache),hashes)
                target=cache/'native-windows-x64-4.1.7.5-Release.zip';target.write_bytes(b'manual')
                with self.assertRaisesRegex(ValueError,'preserved'):cache_build_components(archive,cache)
                self.assertEqual(target.read_bytes(),b'manual')
                self.assertEqual(list(cache.glob('*.part')),[])

    def test_missing_duplicate_or_unverified_component_archive_fails(self):
        for kinds in [['ets','js','toolchains'],['ets','ets','js','native','previewer','toolchains']]:
            with self.subTest(kinds=kinds),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);archive,sha=self.build_archive(root,kinds)
                with patch('verify_public_sdk_package.EXPECTED_SHA',sha):
                    with self.assertRaises(ValueError):cache_build_components(archive,root/'cache')
                with self.assertRaisesRegex(ValueError,'fingerprint'):cache_build_components(archive,root/'unverified')
                self.assertFalse((root/'unverified').exists())

    def fixture(self,root,ets_entries=None):
        root.mkdir()
        hashes={}
        for component in ['ets','js','toolchains']:
            path=root/(component+'-windows-test.zip')
            with zipfile.ZipFile(path,'w') as z:
                for name,raw in (ets_entries if component=='ets' and ets_entries is not None else [(component+'/sample.txt',b'original')]):
                    if isinstance(name,str):
                        info=zipfile.ZipInfo(name);info.filename=name;name=info
                    z.writestr(name,raw)
            hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        return hashes

    def test_repeat_unpack_preserves_original_and_rejects_modified_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);components=root/'components';sdk=root/'sdk'
            hashes=self.fixture(components)
            unpack_components(components,sdk,hashes)
            unpack_components(components,sdk,hashes)
            self.assertEqual((sdk/'ets/sample.txt').read_bytes(),b'original')
            archive=components/'ets-windows-test.zip'
            archive.write_bytes(archive.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError,'verified parent'):unpack_components(components,sdk,hashes)
            self.assertEqual((sdk/'ets/sample.txt').read_bytes(),b'original')

    def test_existing_different_file_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);components=root/'components';sdk=root/'sdk'
            hashes=self.fixture(components)
            (sdk/'ets').mkdir(parents=True);(sdk/'ets/sample.txt').write_bytes(b'manual')
            with self.assertRaisesRegex(ValueError,'Existing SDK file differs'):unpack_components(components,sdk,hashes)
            self.assertEqual((sdk/'ets/sample.txt').read_bytes(),b'manual')

    def test_unsafe_paths_symlinks_and_duplicate_entries_are_rejected(self):
        link=zipfile.ZipInfo('ets/link');link.create_system=3;link.external_attr=0o120777<<16
        cases=[[('../outside',b'x')],[('/absolute',b'x')],[('ets\\escape',b'x')],[(link,b'target')], [('ets/a',b'a'),('ets/a',b'b')]]
        for entries in cases:
            with self.subTest(entries=entries),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);components=root/'components';sdk=root/'sdk'
                hashes=self.fixture(components,entries)
                with self.assertRaises(ValueError):unpack_components(components,sdk,hashes)
                self.assertFalse((root/'outside').exists())


if __name__=='__main__':unittest.main()
