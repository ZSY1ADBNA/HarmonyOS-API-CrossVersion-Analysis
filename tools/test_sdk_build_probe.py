from pathlib import Path
import tempfile
import unittest
from run_sdk_build_probe import summarize,save,prepare
import json


class BuildEvidenceTests(unittest.TestCase):
    def test_api15_profile_and_evidence_preserve_version(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);prepare(root/'project',root/'sdk',api_level=15)
            profile=json.loads((root/'project/build-profile.json5').read_text(encoding='utf-8'))
            product=profile['app']['products'][0]
            self.assertEqual([product[k] for k in ['compileSdkVersion','compatibleSdkVersion','targetSdkVersion']],[15,15,15])
            ability=json.loads((root/'project/entry/src/main/module.json5').read_text(encoding='utf-8'))['module']['abilities'][0]
            self.assertIn('srcEntry',ability)
            self.assertNotIn('srcEntrance',ability)
            report=summarize(root/'project',root/'sdk',root/'ide',0,'BUILD SUCCESSFUL',api_level=15,sdk_version='5.0.3.135')
            self.assertEqual((report['api_level'],report['sdk_version']),(15,'5.0.3.135'))
            self.assertFalse(report['compile_task_succeeded'])
    def test_exit_zero_and_stale_bytecode_do_not_prove_task_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);project=root/'project';sdk=root/'sdk';ide=root/'ide'
            p=project/'entry/build/default/modules.abc';p.parent.mkdir(parents=True);p.write_bytes(b'fixture')
            self.assertFalse(summarize(project,sdk,ide,0,'BUILD SUCCESSFUL')['compile_task_succeeded'])
            log='> hvigor Finished :entry:default@CompileArkTS... after 1 s'
            self.assertTrue(summarize(project,sdk,ide,0,log)['compile_task_succeeded'])
            self.assertFalse(summarize(project,sdk,ide,1,log)['compile_task_succeeded'])
            self.assertFalse(summarize(project,sdk,ide,None,log,True)['compile_task_succeeded'])

    def test_task_log_without_artifact_and_existing_manual_source_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);project=root/'project'
            self.assertFalse(summarize(project,root/'sdk',root/'ide',0,'Finished :entry:default@CompileArkTS')['compile_task_succeeded'])
            save(project,'sample.ets','original')
            with self.assertRaisesRegex(ValueError,'preserved'):save(project,'sample.ets','different')
            self.assertEqual((project/'sample.ets').read_text(),'original')


if __name__=='__main__':unittest.main()
