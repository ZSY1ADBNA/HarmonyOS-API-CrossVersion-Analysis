"""Regression checks for provenance, coverage and scan boundaries."""
import hashlib
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from collect_official_sources import collect, write_json, import_source_lock
from scan_official_materials import scan

class MaterialsTests(unittest.TestCase):
    def temporary_directory(self):
        base=Path(__file__).resolve().parents[1]/'data/delivery/test-temp'
        base.mkdir(parents=True,exist_ok=True)
        return tempfile.TemporaryDirectory(dir=base)

    def fixture(self, root, kind, files):
        source={'source_id':'fixture','kind':kind,'release_id':'OpenHarmony-test-Release',
                'repository':'https://github.com/openharmony/test','repository_name':'test',
                'commit':'a'*40,'status':'collected','body_status':'complete'}
        folder=root/'sources/fixture'
        entries=[]
        for name,raw in files.items():
            target=folder/'content'/name; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
            entries.append({'path':name,'status':'collected','sha256':hashlib.sha256(raw).hexdigest(),
                            'git_blob_sha':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()})
        (folder/'files.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in entries),encoding='utf-8')
        return source

    def test_source_text_and_fence_boundaries(self):
        with self.temporary_directory() as temporary:
            root=Path(temporary)
            source=self.fixture(root,'docs',{'zh-cn/device-dev/test.md':b'# H1\n```\n## fake\n[x](missing.md)\n```\nbody\n'})
            report=scan(source,root)
            self.assertTrue(report['verification_passed'])
            self.assertEqual(report['relative_links_requiring_review'],0)
            doc=json.loads((root/'structured/yu-materials/fixture/documents.jsonl').read_text())
            self.assertEqual(len(doc['headings']),1)
            self.assertIn('body',doc['text'])
            self.assertEqual(doc['category'],'device-dev')

    def test_mismatched_fingerprint_is_not_counted_verified(self):
        with self.temporary_directory() as temporary:
            root=Path(temporary)
            source=self.fixture(root,'docs',{'zh-cn/test.md':b'original'})
            (root/'sources/fixture/content/zh-cn/test.md').write_bytes(b'changed')
            report=scan(source,root)
            self.assertFalse(report['verification_passed'])
            self.assertEqual(report['failures'][0]['status'],'fingerprint_mismatch')

    def test_project_requires_build_configuration(self):
        with self.temporary_directory() as temporary:
            root=Path(temporary)
            source=self.fixture(root,'samples',{'code/App/build-profile.json5':b'{}',
                                                'code/App/hvigorfile.ts':b'// entry',
                                                'code/App/a.ets':b"import http from '@ohos.net.http';",
                                                'code/OnlyReadme/README.md':b'# App'})
            report=scan(source,root)
            self.assertEqual(report['project_roots_candidates'],['code/App'])
            self.assertEqual(report['counts']['import_candidates'],1)
            self.assertFalse(report['build_verified'])

    def test_valid_zip_with_wrong_git_blob_is_rejected(self):
        with self.temporary_directory() as temporary:
            root=Path(temporary); (root/'archives').mkdir()
            source={'source_id':'fixture','kind':'samples','status':'locked',
                    'repository_name':'test','commit':'a'*40}
            with zipfile.ZipFile(root/'archives/fixture.zip','w') as archive:
                archive.writestr('snapshot/LICENSE',b'incorrect')
            write_json(root/'sources/fixture/inventory.json',{'files':[{'path':'LICENSE','git_blob_sha':'b'*40}]})
            result=collect(source,root)
            self.assertEqual(result['status'],'collection_failed')
            self.assertIn('differs from fixed Git tree',result['error'])

    def test_git_archive_preserves_bytes_with_autocrlf_enabled(self):
        with self.temporary_directory() as temporary:
            root=Path(temporary); cache=root/'git-cache-v3/fixture'
            cache.mkdir(parents=True)
            def git(*args):
                return subprocess.run(['git','-C',str(cache),*args],check=True,
                                      capture_output=True,text=True,encoding='utf-8').stdout.strip()
            git('init')
            git('config','core.autocrlf','false')
            raw=b'License\nOriginal LF bytes\n'
            (cache/'LICENSE').write_bytes(raw)
            git('add','LICENSE')
            git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                'commit','-m','fixture')
            commit=git('rev-parse','HEAD')
            git('config','core.autocrlf','true')
            source={'source_id':'fixture','kind':'samples','status':'locked',
                    'repository':'https://github.com/openharmony/test',
                    'repository_name':'test','release_id':'test','commit':commit}
            result=collect(source,root,'git-batches')
            self.assertEqual(result['status'],'collected',result.get('error'))
            with zipfile.ZipFile(root/'archives/fixture.zip') as archive:
                self.assertEqual(archive.read('snapshot/LICENSE'),raw)

    def lfs_fixture_result(self, root, wrong_payload=False):
        cache=root/'git-cache-v3/fixture'; cache.mkdir(parents=True)
        def git(*args):
            return subprocess.run(['git','-C',str(cache),*args],check=True,
                                  capture_output=True,text=True,encoding='utf-8').stdout.strip()
        git('init'); git('config','core.autocrlf','false')
        payload=b'PK exact source attachment\n'
        pointer=('version https://git-lfs.github.com/spec/v1\noid sha256:'+hashlib.sha256(payload).hexdigest()+'\nsize '+str(len(payload))+'\n').encode('ascii')
        (cache/'zh-cn').mkdir(); (cache/'zh-cn/asset.zip').write_bytes(pointer)
        git('add','zh-cn/asset.zip')
        git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','fixture')
        source={'source_id':'fixture','kind':'docs','status':'locked','repository':'https://github.com/openharmony/test',
                'repository_name':'test','release_id':'test','commit':git('rev-parse','HEAD'),
                'archive_normalization':'git_bytes_autocrlf_false_v1'}
        (root/'archives').mkdir()
        with zipfile.ZipFile(root/'archives/fixture.zip','w') as archive:
            archive.writestr('snapshot/zh-cn/asset.zip',payload if not wrong_payload else b'PK corrupted source attachment\n')
        return collect(source,root,'git-batches')

    def test_lfs_payload_preserves_pointer_and_validates_object(self):
        with self.temporary_directory() as temporary:
            root=Path(temporary); result=self.lfs_fixture_result(root)
            self.assertEqual(result['status'],'collected',result.get('error'))
            self.assertEqual(result['lfs_expanded_files_verified'],1)
            entry=json.loads((root/'sources/fixture/files.jsonl').read_text(encoding='utf-8'))
            self.assertIn('oid sha256:',entry['lfs_pointer_text'])
            self.assertNotEqual(entry['git_blob_sha'],entry['payload_git_blob_sha'])

    def test_wrong_lfs_payload_is_rejected(self):
        with self.temporary_directory() as temporary:
            result=self.lfs_fixture_result(Path(temporary),True)
            self.assertEqual(result['status'],'collection_failed')
            self.assertIn('differs from fixed Git tree',result['error'])

    def test_progress_replace_retries_transient_windows_lock(self):
        with self.temporary_directory() as temporary:
            target=Path(temporary)/'status.json'
            write_json(target,{'verified':False})
            original=Path.replace; attempts=[]
            def locked_replace(path,destination):
                attempts.append(1)
                if len(attempts)<3:
                    self.assertFalse(json.loads(target.read_text())['verified'])
                    raise PermissionError('simulated transient file sharing lock')
                return original(path,destination)
            with patch.object(Path,'replace',locked_replace): write_json(target,{'verified':True})
            self.assertTrue(json.loads(target.read_text())['verified'])
            self.assertEqual(len(attempts),3)

    def test_published_lock_preserves_commit_and_requires_new_body_verification(self):
        with self.temporary_directory() as temporary:
            path=Path(temporary)/'lock.json'
            source={'source_id':'fixed','kind':'docs','repository':'https://github.com/openharmony/docs',
                    'commit':'a'*40,'ref':'refs/tags/fixed','status':'collected','archive_sha256':'b'*64,'file_count':10}
            write_json(path,{'sources':[source]})
            record=import_source_lock(path,['docs'])[0]
            self.assertEqual(record['commit'],source['commit'])
            self.assertEqual(record['repository_name'],'docs')
            self.assertEqual(record['status'],'locked')
            self.assertEqual(record['body_status'],'unavailable')
            self.assertEqual(record['expected_archive_sha256'],source['archive_sha256'])
            with self.assertRaises(ValueError): import_source_lock(path,['samples'])

if __name__=='__main__': unittest.main()
