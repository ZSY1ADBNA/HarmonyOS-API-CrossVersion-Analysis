import unittest
from unittest.mock import patch

from search_verified_samples import search_requirements


class RequirementSearchTests(unittest.TestCase):
    def test_chinese_aliases_return_target_version_and_real_evidence(self):
        for message, name in [('设置按钮字号', 'fontSize'), ('查询音频流声道布局', 'channelLayout')]:
            result = search_requirements(message, '5.0.3')
            self.assertEqual(result['status'], 'verified_candidates_found')
            evidence = result['candidates'][0]['evidence']
            self.assertEqual(evidence['name'], name)
            self.assertEqual(evidence['api_level'], 15)
            self.assertTrue(evidence['sdk_evidence'])
            self.assertFalse(evidence['device_runtime_verified'])

    def test_missing_unknown_versions_and_no_match_never_load_evidence(self):
        with patch('search_verified_samples.load_catalog', side_effect=AssertionError('unexpected load')):
            for message, release, expected in [
                ('fontSize', None, 'needs_version'), ('fontSize', '5.0', 'unsupported_release'),
                ('打开相机', '4.1', 'no_verified_match'), ('fontSizeSuffix', '4.1', 'no_verified_match'),
                ('my_channelLayout', '4.1', 'no_verified_match'),
                ('不要设置按钮字号', '4.1', 'needs_intent_clarification')]:
                result = search_requirements(message, release)
                self.assertEqual(result['status'], expected)
                self.assertEqual(result['candidates'], [])
                self.assertFalse(result['absence_in_sdk_proven'])

    def test_comparison_direction_and_multiple_candidates(self):
        result = search_requirements('fontSize和channelLayout', '5.0.3', '4.1')
        self.assertEqual(len(result['candidates']), 2)
        audio = result['comparisons'][1]
        self.assertEqual(audio['old']['release'], '5.0.3')
        self.assertEqual(audio['new']['release'], '4.1')
        self.assertIn('metadata', audio['differences'])
        self.assertFalse(audio['device_behavior_equivalence_verified'])

    def test_evidence_failure_is_distinct_and_private_details_hidden(self):
        with patch('search_verified_samples.load_catalog', side_effect=ValueError('private/path')):
            result = search_requirements('fontSize', '4.1')
        self.assertEqual(result['status'], 'evidence_unavailable')
        self.assertEqual(result['candidates'], [])
        self.assertNotIn('private/path', str(result))

    def test_invalid_inputs_and_comparison_versions(self):
        for message in [None, {}, '', ' '*2, 'x'*2001]:
            with self.assertRaises(ValueError): search_requirements(message, '4.1')
        for version in [[], 11]:
            with self.assertRaises(ValueError): search_requirements('fontSize', version)
        self.assertEqual(search_requirements('fontSize', '4.1', '')['status'], 'needs_version')
        self.assertEqual(search_requirements('fontSize', '4.1', '6.0')['status'], 'unsupported_release')

    def test_owner_qualification_prevents_same_name_false_match(self):
        for message in ['TextAttribute.fontSize', 'Other.channelLayout', 'fake.ButtonAttribute.fontSize']:
            self.assertEqual(search_requirements(message, '4.1')['status'], 'no_verified_match')
        for message in ['ButtonAttribute.fontSize', 'audio.AudioStreamInfo.channelLayout']:
            self.assertEqual(search_requirements(message, '4.1')['status'], 'verified_candidates_found')


if __name__ == '__main__':
    unittest.main()
