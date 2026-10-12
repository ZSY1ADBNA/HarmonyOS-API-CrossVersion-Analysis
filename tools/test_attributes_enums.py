"""Failure and ownership regressions for the bounded attributes/enum expansion."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from collect_official_sources import RELEASES, write_json
from extract_attributes_enums import extract, run


EVIDENCE = {'source_id': 's', 'release_id': 'fixed', 'path': 'test.md', 'commit': 'a' * 40}
LEGACY = '# Button\n## 属性\n| 名称 | 参数类型 | 描述 |\n| -- | -- | -- |\n| fontWeight | number \\| string | weight |\n| labelStyle<sup>10+</sup> | LabelStyle | label |\n'
NEW = '# Button\n## 属性\n### fontWeight\nfontWeight(value: number | string)\n**系统能力：** Cap.UI\n| 参数名 | 类型 | 必填 | 说明 |\n| -- | -- | -- | -- |\n| value | number \\| string | 是 | weight<br/>**起始版本：** 20 |\n'
ENUM = '# Audio\n## AudioSampleFormat<sup>8+</sup>\n**系统能力：** Cap.Core\n| 名称 | 值 | 说明 |\n| -- | -- | -- |\n| SAMPLE_FORMAT_INVALID | -1 | invalid |\n| SAMPLE_FORMAT_F32LE<sup>9+</sup> | 4 | float |\n## AudioChannelLayout<sup>11+</sup>\n| 名称 | 值 | 说明 |\n| -- | -- | -- |\n| CH_LAYOUT_STEREO | 0x3 | stereo |\n'


class ExpansionTests(unittest.TestCase):
    def test_legacy_union_and_heading_versions_without_fabricated_signature(self):
        facts, warnings, _, coverage, _ = extract(LEGACY, EVIDENCE, 'button_attributes')
        self.assertFalse(warnings)
        self.assertTrue(all(c['passed'] for c in coverage))
        self.assertEqual(facts[0]['declared_type'], 'number | string')
        self.assertIsNone(facts[0]['signature'])
        self.assertEqual(facts[1]['metadata']['since'], '10+')

    def test_new_parameter_does_not_pollute_attribute_metadata(self):
        facts, warnings, _, coverage, _ = extract(NEW, EVIDENCE, 'button_attributes')
        self.assertFalse(warnings)
        self.assertTrue(coverage[0]['passed'])
        self.assertEqual(facts[0]['metadata']['syscap'], 'Cap.UI')
        self.assertIsNone(facts[0]['metadata']['since'])
        self.assertEqual(facts[1]['metadata']['since'], '20')
        self.assertEqual(facts[1]['parent_record_id'], facts[0]['record_id'])

    def test_quarantine_unselected_but_reject_selected_malformed_row(self):
        text = LEGACY + '| value | Length | 是 | suspicious |\n'
        facts, warnings, anomalies, coverage, _ = extract(text, EVIDENCE, 'button_attributes')
        self.assertFalse(warnings)
        self.assertEqual(len(anomalies), 1)
        self.assertTrue(all(c['passed'] for c in coverage))
        self.assertFalse(any(f['name'] in ('value', 'fontSize') for f in facts))
        _, warnings, _, coverage, _ = extract(LEGACY + '| type | ButtonType | extra | cells |\n', EVIDENCE, 'button_attributes')
        self.assertTrue(warnings)
        self.assertFalse(all(c['passed'] for c in coverage))

    def test_duplicate_owner_and_duplicate_enum_name_are_rejected(self):
        _, warnings, _, _, _ = extract(NEW + NEW.replace('# Button\n## 属性\n', ''), EVIDENCE, 'button_attributes')
        self.assertTrue(any(w['status'] == 'duplicate_selected_owner' for w in warnings))
        _, _, _, coverage, _ = extract(ENUM + '| CH_LAYOUT_STEREO | 3 | duplicate |\n', EVIDENCE, 'audio_enums')
        self.assertFalse(all(c['passed'] for c in coverage))

    def test_duplicate_headers_and_unknown_required_flag_rejected(self):
        _, warnings, _, _, _ = extract(NEW.replace('| 必填 |', '| 类型 |'), EVIDENCE, 'button_attributes')
        self.assertTrue(warnings)
        _, warnings, _, coverage, _ = extract(NEW.replace('| 是 |', '| 可能 |'), EVIDENCE, 'button_attributes')
        self.assertTrue(warnings)
        self.assertFalse(coverage[0]['passed'])

    def test_examples_other_sections_and_multiple_signatures_excluded(self):
        text = '# Button\n## 示例\n### fontColor\nfontColor(value: Fake)\n```ts\n## 属性\n### fontWeight\nfontWeight(value: Fake)\n```\n'
        self.assertEqual(extract(text, EVIDENCE, 'button_attributes')[0], [])
        _, warnings, _, _, _ = extract(NEW.replace('fontWeight(value: number | string)', 'fontWeight(value: number)\nfontWeight(value: string)'), EVIDENCE, 'button_attributes')
        self.assertTrue(any(w['status'] == 'missing_or_ambiguous_attribute_signature' for w in warnings))

    def test_enum_values_parent_metadata_and_gap_are_preserved(self):
        facts, warnings, _, coverage, gaps = extract(ENUM, EVIDENCE, 'audio_enums')
        self.assertFalse(warnings)
        self.assertTrue(all(c['passed'] for c in coverage))
        member = next(f for f in facts if f['name'] == 'SAMPLE_FORMAT_F32LE')
        self.assertEqual(member['metadata']['since'], '9+')
        self.assertEqual(member['parent_metadata']['since'], '8+')
        self.assertIsNone(member['metadata']['syscap'])
        self.assertEqual(next(f['enum_value'] for f in facts if f['name'] == 'SAMPLE_FORMAT_INVALID'), '-1')
        self.assertEqual(next(f['enum_value'] for f in facts if f['name'] == 'CH_LAYOUT_STEREO'), '0x3')
        self.assertEqual(gaps[0]['owner'], 'AudioVolumeMode')

    def test_nested_example_or_other_container_does_not_create_declarations(self):
        text = '# Button\n## 属性\n### Other\n#### fontColor\nfontColor(value: Fake)\n'
        self.assertEqual(extract(text, EVIDENCE, 'button_attributes')[0], [])
        text = '# Audio\n## 示例\n' + ENUM.replace('# Audio\n', '').replace('## ', '### ')
        self.assertEqual(extract(text, EVIDENCE, 'audio_enums')[0], [])

    def test_parameter_name_must_match_signature(self):
        text = NEW.replace('| value |', '| unrelated |')
        _, _, _, coverage, _ = extract(text, EVIDENCE, 'button_attributes')
        self.assertFalse(coverage[0]['passed'])

    def make_sources(self, root):
        sources = []
        for version, _ in RELEASES:
            sid = version
            legacy = version == '4.1'
            names = ['type', 'fontColor', 'fontWeight', 'labelStyle']
            if version not in ('4.1', '5.0.3'):
                names.append('minFontScale')
            if legacy:
                button = '# Button\n## 属性\n| 名称 | 参数类型 | 描述 |\n| -- | -- | -- |\n' + ''.join(f'| {n} | number | desc |\n' for n in names)
            else:
                button = '# Button\n## 属性\n' + ''.join(f'### {n}\n{n}(value: number)\n| 参数名 | 类型 | 必填 | 说明 |\n| -- | -- | -- | -- |\n| value | number | 是 | desc |\n' for n in names)
            audio = ENUM
            if version in ('6.0', '6.1'):
                audio += '## AudioVolumeMode<sup>19+</sup>\n| 名称 | 值 | 说明 |\n| -- | -- | -- |\n| SYSTEM_GLOBAL | 0 | system |\n'
            docs = {'zh-cn/apis-arkui/ts-basic-components-button.md': button,
                    'zh-cn/apis-audio-kit/js-apis-audio.md': audio}
            folder = root / 'sources' / sid
            folder.mkdir(parents=True)
            (root / 'archives').mkdir(exist_ok=True)
            with zipfile.ZipFile(root / 'archives' / (sid + '.zip'), 'w') as archive:
                for path, text in docs.items():
                    archive.writestr('docs/' + path, text.encode())
            (folder / 'files.jsonl').write_text(''.join(json.dumps({'path': p, 'sha256': hashlib.sha256(t.encode()).hexdigest(), 'git_blob_sha': hashlib.sha1(b'blob ' + str(len(t.encode())).encode() + b'\0' + t.encode()).hexdigest()}) + '\n' for p, t in docs.items()), encoding='utf-8')
            sources.append({'kind': 'docs', 'body_status': 'complete', 'source_id': sid,
                            'release_id': f'OpenHarmony-{version}-Release', 'commit': 'a' * 40, 'repository': 'fixture',
                            'platform': 'OpenHarmony', 'api_level': _, 'file_count': len(docs), 'archive_sha256': 'c' * 64})
        write_json(root / 'sources.json', {'sources': sources})
        write_json(root / 'lock.json', {'sources': sources})

    def test_real_pipeline_failure_preserves_previous_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_sources(root)
            report = root / 'report.json'
            self.assertTrue(run(root, report, root / 'lock.json')['passed'])
            out = root / 'structured/yu-attributes-enums'
            manifest = (out / 'current.json').read_bytes()
            saved = json.loads(manifest)
            pair = {k: (out / v['path']).read_bytes() for k, v in saved.items()}
            real_extract = extract
            def broken(text, evidence, adapter):
                facts, warnings, anomalies, coverage, gaps = real_extract(text, evidence, adapter)
                if adapter == 'audio_enums':
                    coverage[0]['passed'] = False
                return facts, warnings, anomalies, coverage, gaps
            with patch('extract_attributes_enums.extract', side_effect=broken):
                self.assertFalse(run(root, report, root / 'lock.json')['passed'])
            self.assertEqual((out / 'current.json').read_bytes(), manifest)
            for k, v in saved.items():
                self.assertEqual((out / v['path']).read_bytes(), pair[k])
            ledger = root / 'sources/4.1/files.jsonl'
            ledger.write_text(ledger.read_text().replace('"sha256": "', '"sha256": "wrong'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'fingerprint'):
                run(root, report, root / 'lock.json')
            self.assertEqual((out / 'current.json').read_bytes(), manifest)

    def test_wrong_release_and_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'data'
            root.mkdir()
            self.make_sources(root)
            real_resolve = Path.resolve
            def escaped(path, *args, **kwargs):
                if path == root / 'structured/yu-attributes-enums':
                    return real_resolve(Path(temp))
                return real_resolve(path, *args, **kwargs)
            with patch.object(Path, 'resolve', escaped):
                with self.assertRaisesRegex(ValueError, 'escaped'):
                    run(root, root / 'report.json', root / 'lock.json')
            saved = json.loads((root / 'sources.json').read_text())
            saved['sources'][0]['release_id'] = 'wrong-release'
            write_json(root / 'sources.json', saved)
            with self.assertRaisesRegex(ValueError, 'five unique'):
                run(root, root / 'report.json', root / 'lock.json')

    def test_changed_commit_or_git_blob_rejected_before_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_sources(root)
            saved = json.loads((root / 'sources.json').read_text())
            saved['sources'][0]['commit'] = 'd' * 40
            write_json(root / 'sources.json', saved)
            with self.assertRaisesRegex(ValueError, 'lock metadata'):
                run(root, root / 'report.json', root / 'lock.json')
            self.make_sources_reset(root)
            ledger = root / 'sources/4.1/files.jsonl'
            entries = [json.loads(line) for line in ledger.read_text().splitlines()]
            entries[0]['git_blob_sha'] = 'd' * 40
            ledger.write_text(''.join(json.dumps(e) + '\n' for e in entries), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Git blob fingerprint'):
                run(root, root / 'report.json', root / 'lock.json')
            self.assertFalse((root / 'structured/yu-attributes-enums/current.json').exists())

    def make_sources_reset(self, root):
        write_json(root / 'sources.json', json.loads((root / 'lock.json').read_text()))


if __name__ == '__main__':
    unittest.main()
