from pathlib import Path
import tempfile
import unittest
from run_sdk_build_probe import summarize,save


class BuildEvidenceTests(unittest.TestCase):
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
