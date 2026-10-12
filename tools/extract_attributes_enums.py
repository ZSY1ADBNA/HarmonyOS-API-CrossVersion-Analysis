"""Fixed-source Button attributes and three audio enums; isolated documentary pilot."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import uuid
import zipfile

from collect_official_sources import ROOT, RELEASES, identity, write_json
from extract_document_semantics import metadata, create_index, ingest, publish_batch
from pilot_document_structure import heading_spans, clean_heading, outside_fenced_lines
from query_document_candidates import open_readonly, resolve_database, search

ATTRIBUTES = ('type', 'fontColor', 'fontWeight', 'labelStyle', 'minFontScale')
ENUMS = ('AudioSampleFormat', 'AudioChannelLayout', 'AudioVolumeMode')


def strict_rows(section):
    """Retain malformed rows, reject duplicate headers, and keep escaped unions intact."""
    headers = None
    rows, issues = [], []
    for offset, line in enumerate(outside_fenced_lines(section['text'])):
        if line is None or not line.lstrip().startswith('|'):
            headers = None
            continue
        cells = [c.strip().replace(r'\|', '|') for c in re.split(r'(?<!\\)\|', line.strip().strip('|'))]
        if all(re.fullmatch(r':?-{2,}:?', c.replace(' ', '')) for c in cells):
            continue
        if headers is None:
            headers = cells
            if len(set(headers)) != len(headers):
                issues.append({'line': section['start_line'] + offset, 'status': 'duplicate_table_headers', 'raw_content': line})
            continue
        row = {'line': section['start_line'] + offset, 'raw_content': line,
               'first_cell': cells[0], 'fields': dict(zip(headers, cells))}
        if len(cells) != len(headers) or len(set(headers)) != len(headers):
            issues.append({**row, 'status': 'invalid_table_columns'})
        else:
            rows.append(row)
    return rows, issues


def prefix_metadata(section):
    prefix = []
    for line in outside_fenced_lines(section['text']):
        if line and line.lstrip().startswith('|'):
            break
        prefix.append(line or '\n')
    return metadata(''.join(prefix), section['heading'])


def record(evidence, kind, name, owner, line, raw, **extra):
    return {'record_id': identity(evidence['source_id'], evidence['path'], kind, owner, name, line),
            'evidence': evidence, 'kind': kind, 'name': name, 'owner': owner,
            'line': line, 'end_line': line, 'signature': None, 'parent_record_id': None,
            'metadata': metadata(raw, allow_inline=True), 'raw_content': raw,
            'api_identity_status': 'documentation_candidate', 'sdk_public_status': 'not_verified', **extra}


def extract(text, evidence, adapter):
    if adapter not in ('button_attributes', 'audio_enums'):
        raise ValueError('Unknown explicit adapter')
    sections = heading_spans(text)
    facts, warnings, source_issues, coverage, gaps = [], [], [], [], []
    seen = Counter()
    if adapter == 'audio_enums':
        for section in sections:
            owner = clean_heading(section['heading'])
            if owner not in ENUMS or section['level'] != 2:
                continue
            seen[owner] += 1
            parent = record(evidence, 'enum_type', owner, owner, section['start_line'], section['text'],
                            end_line=section['end_line'], metadata=prefix_metadata(section))
            facts.append(parent)
            rows, issues = strict_rows(section)
            warnings.extend(issues)
            extracted = []
            for row in rows:
                fields = row['fields']
                name = clean_heading(fields.get('名称', ''))
                if not {'名称', '值', '说明'}.issubset(fields) or not re.fullmatch(r'[A-Z][A-Z0-9_]*', name) or not fields['值']:
                    warnings.append({**row, 'status': 'unsupported_enum_row'})
                    continue
                facts.append(record(evidence, 'enum_member', name, owner, row['line'], row['raw_content'],
                                    signature=fields['值'], enum_value=fields['值'], description=fields['说明'],
                                    parent_record_id=parent['record_id'], parent_metadata=parent['metadata'],
                                    metadata=metadata(row['raw_content'], fields['名称'], allow_inline=True), table_fields=fields))
                extracted.append((name, row['line']))
            # Independent scan of non-example source rows, including malformed target rows.
            expected = [(clean_heading(m[1]), section['start_line'] + i)
                        for i, line in enumerate(outside_fenced_lines(section['text'])) if line is not None
                        for m in [re.match(r'^\s*\|\s*([A-Z][A-Z0-9_]*(?:<sup>.*?</sup>)?)\s*\|', line)] if m]
            coverage.append({'owner': owner, 'expected': expected, 'extracted': extracted,
                             'passed': bool(expected) and expected == extracted and len(set(n for n, _ in extracted)) == len(extracted)})
        gaps = [{'owner': name, 'status': 'section_absent_in_selected_document'} for name in ENUMS if not seen[name]]
    else:
        roots = [s for s in sections if s['level'] == 1 and clean_heading(s['heading']) == 'Button']
        root_meta = prefix_metadata(roots[0]) if len(roots) == 1 else {}
        if len(roots) != 1:
            warnings.append({'status': 'button_root_missing_or_duplicate'})
        for section in sections:
            title = clean_heading(section['heading'])
            ancestors = [clean_heading(h) for h in section['ancestors']]
            if not ((section['level'] == 2 and ancestors == ['Button']) or
                    (section['level'] == 3 and ancestors == ['Button', '属性'])):
                continue
            if title == '属性':
                rows, issues = strict_rows(section)
                for issue in issues:
                    if clean_heading(issue.get('first_cell', '')) in ATTRIBUTES or issue['status'] == 'duplicate_table_headers':
                        warnings.append(issue)
                    else:
                        source_issues.append({**issue, 'status': 'unselected_source_row_quarantined', 'original_status': issue['status']})
                expected = []
                for i, line in enumerate(outside_fenced_lines(section['text'])):
                    if line is None:
                        continue
                    m = re.match(r'^\s*\|\s*([^|]+)\|', line)
                    if m and clean_heading(m[1]) in ATTRIBUTES:
                        expected.append((clean_heading(m[1]), section['start_line'] + i))
                extracted = []
                for row in rows:
                    fields = row['fields']
                    name = clean_heading(fields.get('名称', ''))
                    if name not in ATTRIBUTES:
                        continue
                    seen[name] += 1
                    if not {'名称', '参数类型', '描述'}.issubset(fields):
                        warnings.append({**row, 'status': 'unsupported_legacy_attribute_table'})
                        continue
                    facts.append(record(evidence, 'component_attribute', name, 'Button', row['line'], row['raw_content'],
                                        metadata=metadata(row['raw_content'], fields['名称'], allow_inline=True),
                                        parent_metadata=root_meta, declared_type=fields['参数类型'], description=fields['描述'],
                                        table_fields=fields, declaration_layout='legacy_attribute_table',
                                        parameter_binding_status='no_signature_in_source'))
                    extracted.append((name, row['line']))
                if expected:
                    coverage.append({'owner': 'Button', 'layout': 'legacy_attribute_table', 'expected': expected,
                                     'extracted': extracted, 'passed': expected == extracted and len(set(n for n, _ in extracted)) == len(extracted)})
            elif title in ATTRIBUTES and '属性' in ancestors:
                seen[title] += 1
                visible = outside_fenced_lines(section['text'])
                declarations = [(section['start_line'] + i, line.strip()) for i, line in enumerate(visible)
                                if line is not None and re.fullmatch(re.escape(title) + r'\s*\([^\n]*\)\s*(?::[^\n]+)?', line.strip())
                                and ':' in line]
                rows, issues = strict_rows(section)
                warnings.extend(issues)
                if len(declarations) != 1:
                    warnings.append({'line': section['start_line'], 'status': 'missing_or_ambiguous_attribute_signature'})
                    coverage.append({'owner': title, 'passed': False})
                    continue
                line, signature = declarations[0]
                declared_parameters = re.findall(r'(?:\(|,)\s*([A-Za-z_]\w*)\??\s*:', signature)
                # Parameter explanations must not overwrite the attribute's own metadata.
                own_meta = prefix_metadata(section)
                fact = record(evidence, 'component_attribute', title, 'Button', line, section['text'],
                              context_start_line=section['start_line'], end_line=section['end_line'], signature=signature,
                              metadata=own_meta, parent_metadata=root_meta, declaration_layout='attribute_signature',
                              parameter_binding_status='within_single_declaration_section')
                facts.append(fact)
                extracted = []
                for row in rows:
                    fields = row['fields']
                    if '参数名' not in fields:
                        warnings.append({**row, 'status': 'unsupported_attribute_table'})
                        continue
                    name = clean_heading(fields['参数名'])
                    if not {'参数名', '类型', '必填', '说明'}.issubset(fields) or fields['必填'] not in ('是', '否') or not re.fullmatch(r'[A-Za-z_]\w*', name):
                        warnings.append({**row, 'status': 'unsupported_attribute_parameter'})
                        continue
                    facts.append(record(evidence, 'parameter', name, 'Button', row['line'], row['raw_content'],
                                        parent_record_id=fact['record_id'], declared_type=fields['类型'],
                                        optional=fields['必填'] == '否', description=fields['说明'], table_fields=fields))
                    extracted.append((name, row['line']))
                expected = [(m[1], section['start_line'] + i) for i, raw in enumerate(visible) if raw is not None
                            for m in [re.match(r'^\s*\|\s*([A-Za-z_]\w*)\s*\|', raw)] if m]
                coverage.append({'owner': title, 'expected': expected, 'extracted': extracted,
                                 'declared_parameters': declared_parameters,
                                 'passed': bool(expected) and expected == extracted and len(set(n for n, _ in extracted)) == len(extracted)
                                 and declared_parameters == [n for n, _ in extracted]})
        gaps = [{'owner': name, 'status': 'declaration_absent_in_selected_document'} for name in ATTRIBUTES if not seen[name]]
    if any(count > 1 for count in seen.values()):
        warnings.append({'status': 'duplicate_selected_owner', 'counts': dict(seen)})
    return facts, warnings, source_issues, coverage, gaps


def run(root, report_path, lock_path=None):
    sources = [s for s in json.loads((root / 'sources.json').read_text(encoding='utf-8'))['sources'] if s['kind'] == 'docs']
    lock_path = lock_path or ROOT / 'docs/official-data-delivery/yu-source-lock.json'
    locked = [s for s in json.loads(lock_path.read_text(encoding='utf-8'))['sources'] if s['kind'] == 'docs']
    releases = {f'OpenHarmony-{v}-Release' for v, _ in RELEASES}
    if len(sources) != len(releases) or {s['release_id'] for s in sources} != releases or len({s['source_id'] for s in sources}) != len(sources):
        raise ValueError('Expected exactly five unique fixed document sources')
    locked_by_id = {s['source_id']: s for s in locked}
    lock_keys = ('source_id', 'platform', 'release_id', 'api_level', 'repository', 'commit', 'archive_sha256', 'file_count')
    if len(locked) != 5 or len(locked_by_id) != 5 or set(locked_by_id) != {s['source_id'] for s in sources}:
        raise ValueError('Fixed source lock source set mismatch')
    if any(any(k not in source or k not in locked_by_id[source['source_id']] or source[k] != locked_by_id[source['source_id']][k]
               for k in lock_keys) for source in sources):
        raise ValueError('Fixed source lock metadata mismatch')
    out = root / 'structured/yu-attributes-enums'
    if not out.resolve().is_relative_to(root.resolve()):
        raise ValueError('Isolated database escaped data root')
    facts, inputs, warnings, anomalies, gaps = [], [], [], [], []
    for source in sources:
        if source.get('body_status') != 'complete':
            raise ValueError('Incomplete source')
        entries = list(map(json.loads, (root / 'sources' / source['source_id'] / 'files.jsonl').read_text(encoding='utf-8').splitlines()))
        ledger = {e['path']: e for e in entries}
        if len(entries) != len(ledger):
            raise ValueError('Duplicate ledger path')
        if len(entries) != source['file_count']:
            raise ValueError('Fixed source ledger count mismatch')
        with zipfile.ZipFile(root / 'archives' / (source['source_id'] + '.zip')) as archive:
            for adapter, directory, names in [('button_attributes', 'apis-arkui/', ('ts-basic-components-button.md',)),
                                              ('audio_enums', 'apis-audio-kit/', ('arkts-apis-audio-e.md', 'js-apis-audio.md'))]:
                matches = []
                for basename in names:
                    matches = [p for p in ledger if directory in p and p.endswith('/' + basename)]
                    if matches:
                        break
                if len(matches) != 1:
                    raise ValueError('Representative missing or ambiguous: ' + adapter)
                path = matches[0]
                members = [n for n in archive.namelist() if n.endswith('/' + path)]
                if len(members) != 1:
                    raise ValueError('Archive member missing or ambiguous')
                raw = archive.read(members[0])
                digest = hashlib.sha256(raw).hexdigest()
                if digest != ledger[path]['sha256']:
                    raise ValueError('Original source fingerprint mismatch')
                git_blob = hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()
                if git_blob != ledger[path]['git_blob_sha']:
                    raise ValueError('Original Git blob fingerprint mismatch')
                evidence = {k: source[k] for k in ('source_id', 'platform', 'release_id', 'api_level', 'repository', 'commit')}
                evidence.update(path=path, source_sha256=digest, git_blob_sha=ledger[path]['git_blob_sha'])
                text = raw.decode('utf-8-sig')
                parsed, issues, source_issues, coverage, missing = extract(text, evidence, adapter)
                original = text.splitlines(keepends=True)
                checks = {'nonempty_selection': bool(parsed), 'no_unresolved_selected_rows': not issues,
                          'selected_rows_complete': bool(coverage) and all(c['passed'] for c in coverage),
                          'source_spans_match': all(1 <= f.get('context_start_line', f['line']) <= f['line'] <= f['end_line'] <= len(original)
                              and ''.join(original[f.get('context_start_line', f['line']) - 1:f['end_line']]).rstrip('\r\n') == f['raw_content'].rstrip('\r\n') for f in parsed),
                          'signature_lines_match': all(original[f['line'] - 1].strip() == f['signature'] for f in parsed if f.get('declaration_layout') == 'attribute_signature')}
                # Expected inventory is fixed to these five source snapshots; absence is not API absence.
                expected_missing = ({'minFontScale'} if source['release_id'] in ('OpenHarmony-4.1-Release', 'OpenHarmony-5.0.3-Release') else set()) if adapter == 'button_attributes' else ({'AudioVolumeMode'} if source['release_id'] in ('OpenHarmony-4.1-Release', 'OpenHarmony-5.0.3-Release', 'OpenHarmony-5.1.0-Release') else set())
                checks['expected_snapshot_inventory'] = {g['owner'] for g in missing} == expected_missing
                facts.extend(parsed)
                warnings.extend({**evidence, **i} for i in issues)
                anomalies.extend({**evidence, **i} for i in source_issues)
                gaps.extend({**evidence, **g} for g in missing)
                inputs.append({**evidence, 'adapter': adapter, 'counts': dict(Counter(f['kind'] for f in parsed)), 'coverage': coverage, 'checks': checks})
    checks = {'fixed_source_lock_matches': True, 'exact_ten_inputs': len(inputs) == 10, 'all_input_checks': all(all(i['checks'].values()) for i in inputs),
              'unique_record_ids': len({f['record_id'] for f in facts}) == len(facts)}
    by_id = {f['record_id']: f for f in facts}
    checks['member_and_parameter_parents_match'] = all(f['parent_record_id'] in by_id
        and by_id[f['parent_record_id']]['kind'] == ('enum_type' if f['kind'] == 'enum_member' else 'component_attribute')
        and by_id[f['parent_record_id']]['evidence'] == f['evidence']
        and by_id[f['parent_record_id']]['owner'] == f['owner']
        for f in facts if f['kind'] in ('enum_member', 'parameter'))
    out.mkdir(parents=True, exist_ok=True)
    temporary = out / ('pending-' + uuid.uuid4().hex + '.db')
    with closing(sqlite3.connect(temporary)) as conn:
        create_index(conn)
        ingest(conn, facts)
        ingest(conn, facts)
        checks['repeat_ingest_same_count'] = conn.execute('SELECT count(*) FROM entities').fetchone()[0] == len(facts)
        conn.execute("INSERT INTO entity_fts(entity_fts,rank) VALUES('integrity-check',1)")
        checks['fts_integrity'] = True
        conn.commit()
    with closing(open_readonly(temporary)) as conn:
        for release in sorted(releases):
            for owner, name, kind in [('Button', 'fontWeight', 'component_attribute'), ('AudioChannelLayout', 'CH_LAYOUT_STEREO', 'enum_member')]:
                hits = search(conn, release, query=name, owner=owner, name=name, kind=kind)
                checks[release + ':' + name + ':readonly_search'] = len(hits) == 1 and hits[0]['owner'] == owner
        checks['unknown_release_empty'] = search(conn, 'not-a-release', name='fontWeight') == []
        try:
            conn.execute('DELETE FROM entities')
        except sqlite3.OperationalError:
            checks['readonly_rejects_delete'] = True
        else:
            checks['readonly_rejects_delete'] = False
    passed = all(checks.values())
    report = {'schema_version': 1, 'inputs': inputs, 'counts': dict(Counter(f['kind'] for f in facts)),
              'warnings': warnings, 'source_anomalies': anomalies, 'representative_gaps': gaps, 'checks': checks,
              'passed': passed, 'sdk_public_scope_verified': False, 'official_api_identity_verified': False,
              'sdk_or_build_verified': False, 'shared_database_updated': False,
              'scope': 'Five selected Button attributes and three audio enums; unselected malformed source rows quarantined, gaps do not prove SDK absence'}
    if passed:
        publish_batch(out, temporary, facts)
        with closing(open_readonly(resolve_database(out))) as conn:
            if conn.execute('SELECT count(*) FROM entities').fetchone()[0] != len(facts):
                raise ValueError('Published count mismatch')
    else:
        temporary.with_suffix('.jsonl').write_text(''.join(json.dumps(f, ensure_ascii=False) + '\n' for f in facts), encoding='utf-8', newline='\n')
    write_json(report_path, report)
    return report


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT / 'data/delivery')
    parser.add_argument('--report', type=Path, default=ROOT / 'docs/official-data-delivery/attributes-enums-pilot.json')
    parser.add_argument('--lock', type=Path, default=ROOT / 'docs/official-data-delivery/yu-source-lock.json')
    args = parser.parse_args()
    report = run(args.root, args.report, args.lock)
    print(json.dumps({'counts': report['counts'], 'passed': report['passed'], 'warnings': len(report['warnings']),
                      'source_anomalies': len(report['source_anomalies']), 'gaps': len(report['representative_gaps']),
                      'failed_checks': [k for k, v in report['checks'].items() if not v]}, ensure_ascii=False))
    if not report['passed']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
