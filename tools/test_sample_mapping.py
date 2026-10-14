import unittest
from unittest.mock import patch
from verify_sample_mapping import audit, identity, PINNED


class MappingTests(unittest.TestCase):
    def test_tampered_legacy_refused_before_sdk_or_database(self):
        with patch.dict(PINNED, {'button':'0'*40}), patch('verify_sample_mapping.samples') as sdk:
            with self.assertRaisesRegex(ValueError, 'Pinned legacy input differs'):
                audit()
            sdk.assert_not_called()

    def test_key_preserves_each_identity_dimension(self):
        d = {'owner':'Owner','kind':'method','name':'member','signature':'member(): void;'}
        baseline = identity('moduleA', d)
        for field, value in [('owner','Other'),('kind','property'),('name','other'),('signature','member(x: number): void;')]:
            with self.subTest(field=field):
                self.assertNotEqual(baseline, identity('moduleA',dict(d, **{field:value})))
        self.assertNotEqual(baseline,identity('moduleB',d))


if __name__ == '__main__':
    unittest.main()
