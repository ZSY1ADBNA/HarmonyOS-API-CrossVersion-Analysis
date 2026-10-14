"""Reproducible source-declaration checks and one evidence-guarded document repair."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import uuid
import zipfile

from collect_official_sources import ROOT, RELEASES, identity, write_json
from extract_attributes_enums import extract as extract_attributes, record
from extract_audio_config import extract_config
from extract_document_semantics import create_index, ingest, publish_batch
from query_document_candidates import open_readonly, resolve_database, search
from pilot_document_structure import outside_fenced_lines, clean_heading

BUTTON_PATH = 'api/@internal/component/ets/button.d.ts'
AUDIO_PATH = 'api/@ohos.multimedia.audio.d.ts'
TEXT_PATH = 'api/@internal/component/ets/text.d.ts'
DOC_BUTTON = 'zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-basic-components-button.md'
SDK_SCOPE = 'Fixed official source declarations; published SDK package and build not verified'
REPAIR_DOC_SHA = '3f9883d9a811aba0ff5f3618958880de7a351e0214ae404ce9ac568abda6d175'
REPAIR_COMMIT = '2027c65cf14cc88cb8bbb5a10df68aec31e6f776'
REPAIR_PARENT = 'f2345b138f205c8cdf37a8885dabd7abe1596c9c'
REPAIR_PARENT_BLOB = '82b5a73637614e540572afc5f404564a3f08dd09'
REPAIR_SDK_BLOB = '251c6bc7691219655f5d87823ca40d16aab3a6d2'


def git_blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


def tags(blocks):
    # Preserve language-specific mappings rather than flattening since to one integer.
    result = {'since_raw': [], 'syscap': [], 'systemapi': False, 'internal': False}
    for block in blocks:
        for name, value in re.findall(r'^\s*\*\s*@([A-Za-z]+)\b([^\r\n]*)', block, re.M):
            value = value.strip()
            if name == 'since':
                result['since_raw'].append(value)
            elif name == 'syscap':
                result['syscap'].append(value)
            elif name in ('systemapi', 'internal'):
                result[name] = True
    return result


def reference_type(text):
    return html.unescape(re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', text)).replace('\xa0', ' ').strip()


def comparison_checks(fact, declaration, document_parameters=()):
    if fact['kind'] == 'component_attribute':
        match = re.fullmatch(re.escape(fact['name']) + r'\((\w+):\s*(.*?)\)(?::.*)?', html.unescape(fact['signature']))
        type_match = bool(match) and len(declaration['parameters']) == 1 and declaration['parameters'][0]['name'] == match[1] and reference_type(match[2]) == declaration['parameters'][0]['type']
        optional_match = len(document_parameters) == 1 and len(declaration['parameters']) == 1 and (document_parameters[0]['table_fields']['必填'] == '否') == declaration['parameters'][0]['optional']
    else:
        type_match = reference_type(fact['declared_type']) == declaration['declared_type']
        optional_match = declaration['optional'] == fact['optional']
    return {'name_and_owner_match': fact['name'] == declaration['name'], 'type_match': type_match,
            'optional_match': optional_match,
            'document_since_supported_in_source_tags': bool(fact['metadata']['since']) and any(re.match(r'^' + re.escape(fact['metadata']['since'].rstrip('+')) + r'(?:\s|$)', s) for s in declaration['metadata']['since_raw']),
            'document_syscap_supported': fact['metadata']['syscap'] is None or fact['metadata']['syscap'] in declaration['metadata']['syscap']}


def report_declaration(declaration):
    """Keep source pointers and interpreted tags; full comments remain in local evidence."""
    if declaration is None:
        return None
    return {k: v for k, v in declaration.items() if k not in ('jsdoc', 'ancestor_jsdoc')}


def read_sources(root, lock_path):
    sources = json.loads(lock_path.read_text(encoding='utf-8'))['sources']
    releases = {f'OpenHarmony-{v}-Release' for v, _ in RELEASES}
    selected = [s for s in sources if s['kind'] in ('docs', 'arkts_api')]
    for kind in ('docs', 'arkts_api'):
        group = [s for s in selected if s['kind'] == kind]
        if len(group) != 5 or {s['release_id'] for s in group} != releases or len({s['source_id'] for s in group}) != 5:
            raise ValueError('Expected exactly five fixed sources per kind')
    inputs = {}
    for source in selected:
        expected_repo = 'docs' if source['kind'] == 'docs' else 'interface_sdk-js'
        if source['platform'] != 'OpenHarmony' or source['repository'] != 'https://github.com/openharmony/' + expected_repo or source['source_id'] != identity('OpenHarmony', expected_repo, source['commit'], source['kind']):
            raise ValueError('Source identity or repository mismatch')
        archive = root / 'archives' / (source['source_id'] + '.zip')
        if hashlib.sha256(archive.read_bytes()).hexdigest() != source['archive_sha256']:
            raise ValueError('Archive fingerprint mismatch')
        entries = list(map(json.loads, (root / 'sources' / source['source_id'] / 'files.jsonl').read_text(encoding='utf-8').splitlines()))
        ledger = {e['path']: e for e in entries}
        if len(ledger) != len(entries) or len(entries) != source['file_count']:
            raise ValueError('Invalid source ledger count or duplicates')
        inputs[(source['kind'], source['release_id'])] = (source, ledger, archive)
    return inputs


def read_file(source, ledger, archive_path, path):
    if path not in ledger:
        raise ValueError('Selected source file missing: ' + path)
    with zipfile.ZipFile(archive_path) as archive:
        members = [n for n in archive.namelist() if n.endswith('/' + path)]
        if len(members) != 1:
            raise ValueError('Ambiguous or missing archive member')
        raw = archive.read(members[0])
    if hashlib.sha256(raw).hexdigest() != ledger[path]['sha256'] or git_blob(raw) != ledger[path]['git_blob_sha']:
        raise ValueError('Selected original fingerprint mismatch')
    evidence = {k: source[k] for k in ('source_id', 'platform', 'release_id', 'api_level', 'repository', 'commit')}
    evidence.update(path=path, source_sha256=ledger[path]['sha256'], git_blob_sha=ledger[path]['git_blob_sha'])
    return raw.decode('utf-8-sig'), evidence


def inspect(requests):
    node = shutil.which('node')
    if not node:
        raise ValueError('Node runtime unavailable')
    result = subprocess.run([node, str(ROOT / 'tools/inspect_sample_declarations.cjs')],
                            input=json.dumps(requests, ensure_ascii=False), encoding='utf-8', capture_output=True, timeout=60)
    if result.returncode:
        raise ValueError('Declaration inspector failed: ' + result.stderr[-1200:])
    parsed = json.loads(result.stdout)
    if len(parsed) != len(requests) or {x['id'] for x in parsed} != {x['id'] for x in requests}:
        raise ValueError('Inspector request/output mismatch')
    return {x['id']: x for x in parsed}


def match_declaration(parsed, owner, name, evidence):
    hits = [f for f in parsed['facts'] if f['owner'] == owner and f['name'] == name]
    if len(hits) > 1:
        raise ValueError('Ambiguous target declaration')
    if not hits:
        return None
    fact = hits[0]
    own = tags(fact['jsdoc'])
    parent = tags(fact['ancestor_jsdoc'])
    return {**fact, 'evidence': evidence, 'metadata': own, 'ancestor_metadata': parent,
            'source_visibility': 'restricted_tag_present' if own['systemapi'] or own['internal'] or parent['systemapi'] or parent['internal'] else 'no_restricted_tag_on_declaration_or_ancestors',
            'sdk_public_status': 'not_verified', 'scope': SDK_SCOPE}


def repair_font_size(text, evidence, declaration, history):
    if evidence['source_sha256'] != REPAIR_DOC_SHA or hashlib.sha256(text.encode('utf-8')).hexdigest() != REPAIR_DOC_SHA or evidence['release_id'] != 'OpenHarmony-4.1-Release' or evidence['path'] != DOC_BUTTON:
        raise ValueError('Repair rule requires exact fixed document')
    change = history['change']
    parent = history['parent_file']
    if history['repository'] != 'https://github.com/openharmony/docs' or history['tag_commit'] != evidence['commit'] or history['path'] != evidence['path']:
        raise ValueError('Repair history source identity mismatch')
    if history['repository'] != 'https://github.com/openharmony/docs' or history['tag_commit'] != evidence['commit'] or history['path'] != evidence['path']:
        raise ValueError('Repair history source identity mismatch')
    if change['commit'] != REPAIR_COMMIT or change['parent'] != REPAIR_PARENT or parent['commit'] != REPAIR_PARENT:
        raise ValueError('Unexpected repair history commits')
    if parent['git_blob_sha'] != REPAIR_PARENT_BLOB or git_blob(parent['content'].encode('utf-8')) != parent['git_blob_sha']:
        raise ValueError('History parent fingerprint mismatch')
    original = text.splitlines(keepends=True)
    raw = original[65]
    cells = [c.strip() for c in raw.strip().strip('|').split('|')]
    old = next((line for line in parent['content'].splitlines() if line.startswith('| fontSize')), None)
    if len(cells) != 4 or cells[:3] != ['value', '[Length](ts-types.md#length)', '是'] or not cells[3].startswith('文本显示字号。'):
        raise ValueError('Repair row content changed')
    if not old or '-'+old not in change['patch'] or '+'+raw.rstrip('\r\n') not in change['patch']:
        raise ValueError('History patch does not prove the exact replacement')
    if not declaration or declaration['evidence']['git_blob_sha'] != REPAIR_SDK_BLOB or declaration['evidence']['release_id'] != evidence['release_id'] or declaration['owner'] != 'ButtonAttribute' or declaration['name'] != 'fontSize' or declaration['signature'] != 'fontSize(value: Length): ButtonAttribute;' or declaration['parameters'] != [{'name': 'value', 'type': 'Length', 'optional': False}] or declaration['declared_type'] != 'ButtonAttribute':
        raise ValueError('SDK source declaration does not support repair')
    proof = {'rule_id': 'oh41-button-fontsize-misplaced-parameter-row-v1', 'status': 'evidence_guarded_repair',
             'history_commit': change['commit'], 'history_parent': change['parent'], 'parent_git_blob_sha': parent['git_blob_sha'],
             'old_document_row': old, 'source_name_before_repair': 'value', 'source_row_unchanged': True,
             'reason': 'History replaced fontSize row with a parameter-shaped value row; same-release source declares fontSize(value: Length)'}
    return record(evidence, 'component_attribute', 'fontSize', 'Button', 66, raw,
                  declared_type=cells[1], description=cells[3], declaration_layout='evidence_repaired_legacy_attribute_table',
                  metadata={'permission': None, 'syscap': None, 'since': None, 'deprecated_mentioned': False},
                  correction=proof, sdk_declaration=declaration, source_declaration_status='matched',
                  source_table_cells=cells)


def scan_other_documents(source, ledger, archive_path, names):
    hits, failures = {n: [] for n in names}, []
    files = [p for p in ledger if p.startswith('zh-cn/') and p.endswith('.md')]
    checked = 0
    with zipfile.ZipFile(archive_path) as archive:
        prefix = archive.namelist()[0].split('/')[0] + '/'
        for path in files:
            raw = archive.read(prefix + path)
            if hashlib.sha256(raw).hexdigest() != ledger[path]['sha256'] or git_blob(raw) != ledger[path]['git_blob_sha']:
                raise ValueError('Search corpus fingerprint mismatch')
            try:
                text = raw.decode('utf-8-sig')
            except UnicodeDecodeError:
                failures.append(path)
                continue
            checked += 1
            present = [n for n in names if n in text]
            if not present:
                continue
            visible = outside_fenced_lines(text)
            headings = []
            for line_no, line in enumerate(text.splitlines(), 1):
                heading = re.match(r'^(#{1,6})\s+(.+)', line) if visible[line_no-1] is not None else None
                if heading:
                    level = len(heading[1])
                    while headings and headings[-1][0] >= level:
                        headings.pop()
                    headings.append((level, clean_heading(heading[2])))
                for name in present:
                    if re.search(r'(?<![A-Za-z0-9_])' + re.escape(name) + r'(?![A-Za-z0-9_])', line):
                        hits[name].append({'path': path, 'line': line_no, 'raw_line': line, 'source_sha256': ledger[path]['sha256'],
                                           'context_headings': [h[1] for h in headings], 'inside_example_fence': visible[line_no-1] is None,
                                           'named_heading_declaration': bool(heading and clean_heading(heading[2]) == name)})
    return {'source_id': source['source_id'], 'release_id': source['release_id'], 'commit': source['commit'],
            'scope': 'All zh-cn Markdown files in this fixed archive; a mention is not a declaration',
            'expected_files': len(files), 'decoded_files': checked, 'decode_failures': failures, 'hits': hits}


def run(root, lock_path, history_path, report_path):
    sources = read_sources(root, lock_path)
    history = json.loads(history_path.read_text(encoding='utf-8'))
    out = root / 'structured/yu-declaration-check'
    if not out.resolve().is_relative_to(root.resolve()):
        raise ValueError('Output escaped isolated data root')
    requests, sdk_evidence, documents = [], {}, {}
    for version, _ in RELEASES:
        release = f'OpenHarmony-{version}-Release'
        source, ledger, archive = sources[('arkts_api', release)]
        for path in ((BUTTON_PATH, AUDIO_PATH, TEXT_PATH) if version == '5.0.3' else (BUTTON_PATH, AUDIO_PATH)):
            text, evidence = read_file(source, ledger, archive, path)
            rid = release + ':' + path
            requests.append({'id': rid, 'text': text, 'path': path})
            sdk_evidence[rid] = evidence
        source, ledger, archive = sources[('docs', release)]
        for kind, choices in [('button', [DOC_BUTTON]), ('audio_config', ['zh-cn/application-dev/reference/apis-audio-kit/arkts-apis-audio-i.md', 'zh-cn/application-dev/reference/apis-audio-kit/js-apis-audio.md'])]:
            path = next((p for p in choices if p in ledger), None)
            if path is None:
                raise ValueError('Document representative missing')
            documents[(release, kind)] = read_file(source, ledger, archive, path)
    parsed = inspect(requests)
    declarations, candidates, comparisons, gaps, corpus_searches, input_checks = [], [], [], [], [], []
    for version, _ in RELEASES:
        release = f'OpenHarmony-{version}-Release'
        selected = {}
        for owner, name, path in [('ButtonAttribute', 'fontSize', BUTTON_PATH), ('ButtonAttribute', 'minFontScale', BUTTON_PATH),
                                  ('AudioStreamInfo', 'channelLayout', AUDIO_PATH), ('AudioRendererInfo', 'volumeMode', AUDIO_PATH), ('audio', 'AudioVolumeMode', AUDIO_PATH)]:
            rid = release + ':' + path
            item = match_declaration(parsed[rid], owner, name, sdk_evidence[rid])
            selected[name] = item
            if item:
                declarations.append(item)
        text_declaration = None
        if version == '5.0.3':
            rid = release + ':' + TEXT_PATH
            text_declaration = match_declaration(parsed[rid], 'TextAttribute', 'minFontScale', sdk_evidence[rid])
            if not text_declaration:
                raise ValueError('Same-name Text declaration not verified')
            declarations.append(text_declaration)
        for kind in ('button', 'audio_config'):
            text, evidence = documents[(release, kind)]
            if kind == 'button':
                facts, warnings, anomalies, coverage, missing = extract_attributes(text, evidence, 'button_attributes')
            else:
                facts, warnings, coverage = extract_config(text, evidence)
            if warnings or not coverage or not all(c['passed'] for c in coverage):
                raise ValueError('Selected documentary parser checks failed')
            for fact in facts:
                name = fact['name']
                if (kind == 'button' and fact['kind'] == 'component_attribute' and name == 'minFontScale') or (kind == 'audio_config' and fact['kind'] == 'property' and name in ('channelLayout', 'volumeMode')):
                    item = selected[name]
                    if not item:
                        raise ValueError('Document candidate lacks selected source declaration')
                    expected_owner = 'AudioStreamInfo' if name == 'channelLayout' else 'AudioRendererInfo' if name == 'volumeMode' else 'ButtonAttribute'
                    if item['owner'] != expected_owner or (kind == 'audio_config' and fact['owner'] != expected_owner):
                        raise ValueError('Incorrect documentary/source owner')
                    candidates.append({**fact, 'sdk_declaration': item, 'source_declaration_status': 'matched'})
                    parameters = [f for f in facts if f['kind'] == 'parameter' and f['parent_record_id'] == fact['record_id']]
                    checks = comparison_checks(fact, item, parameters)
                    comparisons.append({'release_id': release, 'name': name, 'document': {'evidence': evidence, 'line': fact['line'], 'metadata': fact['metadata']},
                                        'source_declaration': item, 'checks': checks})
        if version == '4.1':
            text, evidence = documents[(release, 'button')]
            candidates.append(repair_font_size(text, evidence, selected['fontSize'], history))
        missing_names = (['minFontScale'] if version in ('4.1', '5.0.3') else []) + (['AudioVolumeMode'] if version in ('4.1', '5.0.3', '5.1.0') else [])
        if missing_names:
            source, ledger, archive = sources[('docs', release)]
            corpus = scan_other_documents(source, ledger, archive, missing_names)
            corpus_searches.append(corpus)
            for name in missing_names:
                path = BUTTON_PATH if name == 'minFontScale' else AUDIO_PATH
                rid = release + ':' + path
                expected_owner = 'ButtonAttribute' if name == 'minFontScale' else 'AudioRendererInfo'
                owner_found = any(o['name'] == expected_owner for o in parsed[rid]['owners'])
                absence_checked = selected[name] is None and owner_found and not parsed[rid]['diagnostics']
                other_owner_verified = bool(name == 'minFontScale' and text_declaration and any(h['named_heading_declaration'] and h['context_headings'][0] == 'Text' for h in corpus['hits'][name]))
                gaps.append({'release_id': release, 'name': name, 'document_hits': corpus['hits'][name],
                             'source_evidence': sdk_evidence[rid], 'source_owner_present': owner_found,
                             'declaration_absent_in_selected_source_file': absence_checked,
                             'status': 'same_name_found_on_Text_not_Button' if absence_checked and other_owner_verified else 'not_declared_in_fixed_source_owner' if absence_checked and not corpus['hits'][name] and not corpus['decode_failures'] else 'requires_further_review',
                             'same_name_other_owner_declaration': text_declaration if other_owner_verified else None,
                             'published_sdk_availability': 'not_verified', 'scope': 'Same-release Chinese documents and selected source .d.ts; not a statement about every SDK package or inherited members'})
    for rid, result in parsed.items():
        req = next(r for r in requests if r['id'] == rid)
        lines = req['text'].splitlines()
        input_checks.append({'id': rid, 'evidence': sdk_evidence[rid], 'no_syntax_diagnostics': not result['diagnostics'],
                             'declarations_match_original': all('\n'.join(lines[f['line']-1:f['end_line']]).strip() == f['raw_declaration'].strip() for f in result['facts'])})
    checks = {'exact_eleven_source_inputs': len(parsed) == 11,
              'original_source_spans_match': all(i['declarations_match_original'] for i in input_checks),
              'no_syntax_diagnostics': all(i['no_syntax_diagnostics'] for i in input_checks),
              'all_sample_comparisons_match': bool(comparisons) and all(all(c['checks'].values()) for c in comparisons),
              'all_expected_samples_retained': len(comparisons) == 10 and len(candidates) == 11 and len(declarations) == 18,
              'all_expected_samples_retained': len(comparisons) == 10 and len(candidates) == 11 and len(declarations) == 18,
              'exact_five_gaps_reviewed': len(gaps) == 5,
              'full_selected_document_corpora_decoded': all(not s['decode_failures'] for s in corpus_searches),
              'repair_exactly_one_candidate': sum('correction' in f for f in candidates) == 1,
              'unique_candidate_ids': len({f['record_id'] for f in candidates}) == len(candidates)}
    out.mkdir(parents=True, exist_ok=True)
    temporary = out / ('pending-' + uuid.uuid4().hex + '.db')
    with closing(sqlite3.connect(temporary)) as conn:
        create_index(conn)
        ingest(conn, candidates)
        ingest(conn, candidates)
        checks['repeat_ingest_same_count'] = conn.execute('SELECT count(*) FROM entities').fetchone()[0] == len(candidates)
        conn.execute("INSERT INTO entity_fts(entity_fts,rank) VALUES('integrity-check',1)")
        checks['fts_integrity'] = True
        conn.commit()
    with closing(open_readonly(temporary)) as conn:
        hits = search(conn, 'OpenHarmony-4.1-Release', owner='Button', name='fontSize', kind='component_attribute')
        checks['repaired_font_size_readonly_search'] = len(hits) == 1 and hits[0]['line'] == 66
        try:
            conn.execute('DELETE FROM entities')
        except sqlite3.OperationalError:
            checks['readonly_rejects_write'] = True
        else:
            checks['readonly_rejects_write'] = False
    passed = all(checks.values())
    report = {'schema_version': 1, 'as_of': '2026-10-13', 'scope': SDK_SCOPE,
              'counts': {'source_files': len(parsed), 'source_declarations': len(declarations), 'document_candidates': len(candidates), 'comparisons': len(comparisons)},
              'input_checks': input_checks,
              'comparisons': [{**c, 'source_declaration': report_declaration(c['source_declaration'])} for c in comparisons],
              'gap_reviews': [{**g, 'same_name_other_owner_declaration': report_declaration(g['same_name_other_owner_declaration'])} for g in gaps],
              'correction': next(f['correction'] for f in candidates if 'correction' in f),
              'history': {k: history[k] for k in ('repository', 'tag_commit', 'path', 'change', 'path_history')},
              'document_search_summary': [{k: v for k, v in s.items() if k != 'hits'} for s in corpus_searches],
              'checks': checks, 'passed': passed, 'typescript': next(iter(parsed.values()))['typescript'],
              'published_sdk_verified': False, 'build_verified': False, 'shared_database_updated': False}
    write_json(out / 'document-search-evidence.json', corpus_searches)
    write_json(out / 'source-declarations.json', declarations)
    if passed:
        publish_batch(out, temporary, candidates)
        resolve_database(out)
    else:
        write_json(temporary.with_suffix('.json'), candidates)
    write_json(report_path, report)
    return report


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT / 'data/delivery')
    parser.add_argument('--lock', type=Path, default=ROOT / 'docs/official-data-delivery/sample-declaration-source-lock.json')
    parser.add_argument('--history', type=Path, default=ROOT / 'data/delivery/structured/yu-declaration-check/history-evidence.json')
    parser.add_argument('--report', type=Path, default=ROOT / 'docs/official-data-delivery/sample-declaration-verification.json')
    args = parser.parse_args()
    report = run(args.root, args.lock, args.history, args.report)
    print(json.dumps({'counts': report['counts'], 'passed': report['passed'], 'gap_statuses': dict(Counter(g['status'] for g in report['gap_reviews'])),
                      'failed_checks': [k for k, v in report['checks'].items() if not v]}, ensure_ascii=False))
    if not report['passed']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
