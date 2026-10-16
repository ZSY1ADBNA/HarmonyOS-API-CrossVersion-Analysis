import json
import unittest
from collect_official_sources import ROOT
from run_sdk503_negative_probes import diagnostic_seen


class NegativeDiagnosticTests(unittest.TestCase):
    def test_wrong_owner_prefix_and_other_field_rejected(self):
        for line in ["Property 'volumeMode' does not exist on type 'AudioRendererInfoOther'.",
                     "Property 'other' does not exist on type 'AudioRendererInfo'.",
                     "const s = Property 'volumeMode' does not exist on type 'AudioRendererInfo'."]:
            self.assertFalse(diagnostic_seen(line,'volumeMode','AudioRendererInfo'))

    def test_saved_real_compiler_diagnostics_match_exact_target(self):
        for name,owner in [('minFontScale','ButtonAttribute'),('volumeMode','AudioRendererInfo')]:
            with self.subTest(name=name):
                report=json.loads((ROOT/'docs/official-data-delivery'/('sdk503-negative-'+name+'.json')).read_text(encoding='utf-8'))
                self.assertTrue(diagnostic_seen(report['output_tail'],name,owner))
                self.assertNotIn(report['return_code'],(None,0))
                self.assertFalse(report['timed_out'])


if __name__=='__main__':unittest.main()
