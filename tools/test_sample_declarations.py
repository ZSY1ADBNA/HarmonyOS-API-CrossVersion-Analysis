"""Regression coverage for provenance, ownership, repair guards and failed publication."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from collect_official_sources import identity, RELEASES, write_json
import verify_sample_declarations as verifier


class DeclarationChecks(unittest.TestCase):
    def test_ast_ownership_comments_and_language_versions(self):
        text = '''declare namespace audio {
interface AudioStreamInfo {
/**
 * @since 11
 */
/**
 * @since 12 dynamic
 * @since 23 static
 * @syscap Cap.Core
 */
channelLayout?: AudioChannelLayout;
}
interface Other {
channelLayout: string;
}
}
declare class ButtonAttribute {
/**
 * @since arkts {'1.1':'11','1.2':'20'}
 */
fontSize(value: Length): ButtonAttribute;
}
'''
        result = verifier.inspect([{'id': 'one', 'path': 'test.d.ts', 'text': text}])['one']
        self.assertFalse(result['diagnostics'])
        self.assertEqual(len(result['facts']), 2)
        channel = verifier.match_declaration(result, 'AudioStreamInfo', 'channelLayout', {})
        self.assertTrue(channel['optional'])
        self.assertEqual(channel['metadata']['since_raw'], ['11', '12 dynamic', '23 static'])
        font = verifier.match_declaration(result, 'ButtonAttribute', 'fontSize', {})
        self.assertEqual(font['metadata']['since_raw'], ["arkts {'1.1':'11','1.2':'20'}"])
        self.assertEqual(font['sdk_public_status'], 'not_verified')

    def test_parent_restricted_tag_is_not_mistaken_for_public(self):
        text = '''/**
 * @systemapi
 */
interface AudioStreamInfo {
channelLayout?: AudioChannelLayout;
}
'''
        result = verifier.inspect([{'id': 'one', 'path': 'test.d.ts', 'text': text}])['one']
        item = verifier.match_declaration(result, 'AudioStreamInfo', 'channelLayout', {})
        self.assertEqual(item['source_visibility'], 'restricted_tag_present')
        self.assertEqual(item['sdk_public_status'], 'not_verified')

    def test_same_name_other_owner_and_ambiguous_declaration(self):
        text = 'declare class TextAttribute {\nminFontScale(scale: number | Resource): TextAttribute;\n}\n'
        parsed = verifier.inspect([{'id': 'one', 'path': 'test.d.ts', 'text': text}])['one']
        self.assertIsNone(verifier.match_declaration(parsed, 'ButtonAttribute', 'minFontScale', {}))
        self.assertIsNotNone(verifier.match_declaration(parsed, 'TextAttribute', 'minFontScale', {}))
        duplicate = {**parsed, 'facts': parsed['facts'] * 2}
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            verifier.match_declaration(duplicate, 'TextAttribute', 'minFontScale', {})

    def test_comparison_rejects_type_optional_and_wrong_version(self):
        fact = {'kind': 'property', 'name': 'channelLayout', 'declared_type': '[AudioChannelLayout](file.md)', 'optional': True,
                'metadata': {'since': '11+', 'syscap': None}}
        declaration = {'name': 'channelLayout', 'declared_type': 'AudioChannelLayout', 'optional': True,
                       'metadata': {'since_raw': ['11', '12 dynamic'], 'syscap': ['Cap.Core']}}
        self.assertTrue(all(verifier.comparison_checks(fact, declaration).values()))
        changed = {**fact, 'declared_type': '[NotAudioChannelLayout](file.md)'}
        self.assertFalse(verifier.comparison_checks(changed, declaration)['type_match'])
        self.assertFalse(verifier.comparison_checks({**fact, 'optional': False}, declaration)['optional_match'])
        self.assertFalse(verifier.comparison_checks({**fact, 'metadata': {'since': '1+', 'syscap': None}}, declaration)['document_since_supported_in_source_tags'])
        method = {'kind': 'component_attribute', 'name': 'minFontScale', 'signature': 'minFontScale(scale: string)',
                  'metadata': {'since': '18+', 'syscap': None}}
        source = {'name': 'minFontScale', 'parameters': [{'name': 'scale', 'type': 'number | Resource', 'optional': False}],
                  'metadata': {'since_raw': ['18'], 'syscap': []}}
        param = {'table_fields': {'必填': '是'}}
        self.assertFalse(verifier.comparison_checks(method, source, [param])['type_match'])
        self.assertTrue(verifier.comparison_checks(method, source, [param])['optional_match'])

    def fixture(self, root):
        sources = []
        old_row = '| fontSize | [Length](ts-types.md#length) | 设置文本显示字号。 |'
        broken_row = '| value  | [Length](ts-types.md#length) | 是   | 文本显示字号。default |\n'
        old_button = '# Button\n' + '\n' * 61 + '## 属性\n| 名称 | 参数类型 | 描述 |\n| -- | -- | -- |\n' + broken_row + '| type | ButtonType | type |\n'
        self.assertEqual(old_button.splitlines()[65], broken_row.rstrip())
        parent_text = '# Button\n' + old_row + '\n'
        first_sdk = None
        for index, (version, api_level) in enumerate(RELEASES):
            newer = version not in ('4.1', '5.0.3')
            volume = version in ('6.0', '6.1')
            button_sdk = 'declare class ButtonAttribute {\n/**\n * @since 7\n */\nfontSize(value: Length): ButtonAttribute;\n'
            if newer:
                button_sdk += '/**\n * @since 18\n * @syscap SystemCapability.ArkUI.ArkUI.Full\n */\nminFontScale(scale: number | Resource): ButtonAttribute;\n'
            button_sdk += '}\n'
            if index == 0:
                first_sdk = button_sdk
            audio_sdk = 'declare namespace audio {\ninterface AudioStreamInfo {\n/**\n * @since 11\n * @syscap SystemCapability.Multimedia.Audio.Core\n */\nchannelLayout?: AudioChannelLayout;\n}\ninterface AudioRendererInfo {\n'
            if volume:
                audio_sdk += '/**\n * @since 19\n * @syscap SystemCapability.Multimedia.Audio.Volume\n */\nvolumeMode?: AudioVolumeMode;\n'
            audio_sdk += '}\n'
            if volume:
                audio_sdk += '/**\n * @since 19\n */\nenum AudioVolumeMode {\nSYSTEM_GLOBAL = 0\n}\n'
            audio_sdk += '}\n'
            button = old_button if index == 0 else '# Button\n## 属性\n| 名称 | 参数类型 | 描述 |\n| -- | -- | -- |\n| type | ButtonType | type |\n'
            if newer:
                button += '### minFontScale<sup>18+</sup>\nminFontScale(scale: number | Resource)\n**系统能力：** SystemCapability.ArkUI.ArkUI.Full\n| 参数名 | 类型 | 必填 | 说明 |\n| -- | -- | -- | -- |\n| scale | number \\| Resource | 是 | scale |\n'
            audio = '## AudioStreamInfo<sup>8+</sup>\n| 名称 | 类型 | 只读 | 可选 | 说明 |\n| -- | -- | -- | -- | -- |\n| channelLayout<sup>11+</sup> | [AudioChannelLayout](file.md) | 否 | 是 | layout |\n'
            if volume:
                audio += '## AudioRendererInfo<sup>8+</sup>\n| 名称 | 类型 | 只读 | 可选 | 说明 |\n| -- | -- | -- | -- | -- |\n| volumeMode<sup>19+</sup> | [AudioVolumeMode](file.md) | 否 | 是 | volume<br/>**系统能力：** SystemCapability.Multimedia.Audio.Volume |\n'
            for kind, repo, docs in [('docs', 'docs', {verifier.DOC_BUTTON: button, 'zh-cn/application-dev/reference/apis-audio-kit/js-apis-audio.md': audio}),
                                      ('arkts_api', 'interface_sdk-js', {verifier.BUTTON_PATH: button_sdk, verifier.AUDIO_PATH: audio_sdk})]:
                if version == '5.0.3':
                    if kind == 'docs':
                        docs['zh-cn/text.md'] = '# Text\n## 属性\n### minFontScale<sup>12+</sup>\nminFontScale(scale: number | Resource)\n'
                    else:
                        docs[verifier.TEXT_PATH] = 'declare class TextAttribute {\n/**\n * @since 12\n */\nminFontScale(scale: number | Resource): TextAttribute;\n}\n'
                commit = str(index + (10 if kind == 'docs' else 20)).zfill(40)
                sid = identity('OpenHarmony', repo, commit, kind)
                folder = root / 'sources' / sid
                folder.mkdir(parents=True)
                archive = root / 'archives' / (sid + '.zip')
                archive.parent.mkdir(exist_ok=True)
                entries = []
                with zipfile.ZipFile(archive, 'w') as z:
                    for path, text in docs.items():
                        raw = text.encode()
                        z.writestr('snapshot/' + path, raw)
                        entries.append({'path': path, 'sha256': hashlib.sha256(raw).hexdigest(), 'git_blob_sha': verifier.git_blob(raw)})
                (folder / 'files.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in entries), encoding='utf-8')
                sources.append({'kind': kind, 'source_id': sid, 'platform': 'OpenHarmony', 'repository': 'https://github.com/openharmony/' + repo,
                                'release_id': f'OpenHarmony-{version}-Release', 'api_level': api_level, 'commit': commit,
                                'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'file_count': len(entries)})
        write_json(root / 'lock.json', {'sources': sources})
        history = {'repository': 'https://github.com/openharmony/docs', 'tag_commit': str(10).zfill(40), 'path': verifier.DOC_BUTTON,
                   'change': {'commit': verifier.REPAIR_COMMIT, 'parent': verifier.REPAIR_PARENT, 'patch': '-'+old_row+'\n+'+broken_row.rstrip()},
                   'parent_file': {'commit': verifier.REPAIR_PARENT, 'content': parent_text, 'git_blob_sha': verifier.git_blob(parent_text.encode())}, 'path_history': []}
        write_json(root / 'history.json', history)
        return {'REPAIR_DOC_SHA': hashlib.sha256(old_button.encode()).hexdigest(), 'REPAIR_PARENT_BLOB': verifier.git_blob(parent_text.encode()),
                'REPAIR_SDK_BLOB': verifier.git_blob(first_sdk.encode())}

    def test_real_fixture_pipeline_repair_and_failure_keep_previous_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guards = self.fixture(root)
            with patch.multiple(verifier, **guards):
                report = verifier.run(root, root / 'lock.json', root / 'history.json', root / 'report.json')
                self.assertTrue(report['passed'])
                self.assertEqual(report['counts']['document_candidates'], 11)
                self.assertNotIn('jsdoc', report['comparisons'][0]['source_declaration'])
                self.assertIn('since_raw', report['comparisons'][0]['source_declaration']['metadata'])
                self.assertEqual([g['status'] for g in report['gap_reviews']].count('same_name_found_on_Text_not_Button'), 1)
                out = root / 'structured/yu-declaration-check'
                manifest = (out / 'current.json').read_bytes()
                saved = json.loads(manifest)
                pair = {k: (out / v['path']).read_bytes() for k, v in saved.items()}
                real = verifier.comparison_checks
                def failed(*args):
                    return {**real(*args), 'type_match': False}
                with patch.object(verifier, 'comparison_checks', side_effect=failed):
                    self.assertFalse(verifier.run(root, root / 'lock.json', root / 'history.json', root / 'report.json')['passed'])
                self.assertEqual((out / 'current.json').read_bytes(), manifest)
                for k, entry in saved.items():
                    self.assertEqual((out / entry['path']).read_bytes(), pair[k])
                bad = json.loads((root / 'history.json').read_text(encoding='utf-8'))
                bad['change']['patch'] = 'unrelated patch'
                write_json(root / 'history.json', bad)
                with self.assertRaisesRegex(ValueError, 'exact replacement'):
                    verifier.run(root, root / 'lock.json', root / 'history.json', root / 'report.json')
                self.assertEqual((out / 'current.json').read_bytes(), manifest)

    def test_original_fingerprints_and_source_labels_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            saved = json.loads((root / 'lock.json').read_text(encoding='utf-8'))
            source = saved['sources'][0]
            archive = root / 'archives' / (source['source_id'] + '.zip')
            archive.write_bytes(archive.read_bytes() + b'changed')
            with self.assertRaisesRegex(ValueError, 'Archive fingerprint'):
                verifier.read_sources(root, root / 'lock.json')
            saved['sources'][0]['repository'] = 'https://example.com/unrelated'
            write_json(root / 'lock.json', saved)
            with self.assertRaisesRegex(ValueError, 'identity or repository'):
                verifier.read_sources(root, root / 'lock.json')

    def test_repair_rejects_changed_text_parent_and_cross_release_sdk(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guards = self.fixture(root)
            with patch.multiple(verifier, **guards):
                verifier.run(root, root / 'lock.json', root / 'history.json', root / 'report.json')
                inputs = verifier.read_sources(root, root / 'lock.json')
                release = 'OpenHarmony-4.1-Release'
                text, evidence = verifier.read_file(*inputs[('docs', release)], verifier.DOC_BUTTON)
                declarations = json.loads((root / 'structured/yu-declaration-check/source-declarations.json').read_text(encoding='utf-8'))
                declaration = next(d for d in declarations if d['name'] == 'fontSize' and d['evidence']['release_id'] == release)
                history = json.loads((root / 'history.json').read_text(encoding='utf-8'))
                with self.assertRaisesRegex(ValueError, 'exact fixed document'):
                    verifier.repair_font_size(text + '\n', evidence, declaration, history)
                changed = json.loads(json.dumps(history))
                changed['parent_file']['content'] += '\n'
                with self.assertRaisesRegex(ValueError, 'parent fingerprint'):
                    verifier.repair_font_size(text, evidence, declaration, changed)
                changed = json.loads(json.dumps(declaration))
                changed['evidence']['release_id'] = 'OpenHarmony-6.1-Release'
                with self.assertRaisesRegex(ValueError, 'does not support repair'):
                    verifier.repair_font_size(text, evidence, changed, history)


if __name__ == '__main__':
    unittest.main()
