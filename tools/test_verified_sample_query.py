import copy
import json
import shutil
import tempfile
from pathlib import Path
import unittest
from query_verified_samples import DIRECTORY,MANIFEST,SPECS,write_manifest,load_catalog,query,compare,sha


class VerifiedQueryTests(unittest.TestCase):
    def test_unknown_release_is_not_an_absence_claim(self):
        catalog=load_catalog()
        result=query(catalog,'5.0','channelLayout')
        self.assertEqual(result['records'],[])
        self.assertFalse(result['absence_in_sdk_proven'])
        self.assertEqual(query(catalog,'5.0.3','channelLayout')['records'][0]['project_graph_tag'],'API5.0')

    def test_real_metadata_difference_and_direction_preserved(self):
        catalog=load_catalog();a=compare(catalog,'4.1','5.0.3','channelLayout');b=compare(catalog,'5.0.3','4.1','channelLayout')
        self.assertNotIn('signature',a['differences'])
        self.assertIn('metadata',a['differences'])
        self.assertEqual(a['differences']['metadata']['old'],b['differences']['metadata']['new'])
        self.assertFalse(a['device_behavior_equivalence_verified'])

    def test_tampered_report_and_wrong_version_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            names={name for spec in SPECS.values() for name in spec[-2:]}
            for name in names:shutil.copyfile(DIRECTORY/name,root/name)
            write_manifest(root)
            target=root/'sdk503-build-probe.json'
            report=json.loads(target.read_text(encoding='utf-8'));report['api_level']=11
            target.write_text(json.dumps(report),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'fingerprint'):load_catalog(root)
            manifest=json.loads((root/MANIFEST).read_text(encoding='utf-8'))
            manifest['files'][target.name]=sha(target.read_bytes());(root/MANIFEST).write_text(json.dumps(manifest),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'build identity'):load_catalog(root)


if __name__=='__main__':unittest.main()
