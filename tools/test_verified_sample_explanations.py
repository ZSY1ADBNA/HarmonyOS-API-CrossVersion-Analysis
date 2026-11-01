import unittest
from unittest.mock import patch
from explain_verified_samples import explain


class ExplanationTests(unittest.TestCase):
    def test_every_fact_has_resolvable_target_version_source(self):
        result = explain('按钮字号和声道布局', '5.0.3')
        self.assertEqual(len(result['candidates']), 2)
        for candidate in result['candidates']:
            for fact in candidate['facts']:
                source = result['sources'][fact['source_id']]
                self.assertEqual(source['release'], '5.0.3')
                self.assertEqual(len(source['report_sha256']), 64)
        self.assertEqual(result['generation_mode'], 'deterministic_evidence_summary')

    def test_optional_is_not_default_or_runtime_claim(self):
        result = explain('channelLayout', '4.1')
        facts = result['candidates'][0]['facts']
        optional = next(fact for fact in facts if fact['field'] == 'optional')
        self.assertTrue(optional['value'])
        self.assertIn('不说明有默认值', optional['text'])
        self.assertIn('设备运行尚未验证', result['unknowns'])

    def test_comparison_has_both_sources_and_direction(self):
        for old, new in [('4.1','5.0.3'), ('5.0.3','4.1')]:
            result = explain('channelLayout', old, new)
            comparison = result['comparisons'][0]
            self.assertEqual([result['sources'][s]['release'] for s in comparison['source_ids']], [old,new])
            self.assertIn('metadata', comparison['differences'])
            self.assertEqual(comparison['from_signature'],comparison['to_signature'])

    def test_no_match_and_failure_never_invent_explanations(self):
        for message, release in [('相机','4.1'),('fontSize',None),('fontSize','5.0')]:
            result=explain(message,release)
            self.assertEqual(result['candidates'],[])
            self.assertEqual(result['sources'],{})
        with patch('search_verified_samples.load_catalog',side_effect=ValueError('private')):
            result=explain('fontSize','4.1')
        self.assertEqual(result['status'],'evidence_unavailable')
        self.assertEqual(result['sources'],{})


if __name__ == '__main__':unittest.main()
