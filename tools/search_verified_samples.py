"""Bounded requirement lookup over four verified SDK declaration records."""
import argparse
import json
import re
import time

from query_verified_samples import SPECS, TARGETS, compare, load_catalog, query


ALIASES = {
    'fontSize': ('按钮字号', '按钮字体大小', '按钮的字号', '按钮的字体大小'),
    'channelLayout': ('音频声道布局', '音频的声道布局', '音频流声道布局', '声道布局'),
}
LIMITATIONS = [
    'Only ButtonAttribute.fontSize and AudioStreamInfo.channelLayout in releases 4.1 and 5.0.3 are covered.',
    'Alias matches are candidates, not proof that every requirement or platform constraint is satisfied.',
    'No default value, device behavior, or direct migration compatibility is inferred.',
]


def search_requirements(message, release=None, compare_with=None, directory=None):
    """Return evidence before any downstream answer; never execute user query text."""
    started = time.perf_counter()
    if not isinstance(message, str) or not message.strip() or len(message) > 2000:
        raise ValueError('message must contain 1 to 2000 characters')
    if release is not None and not isinstance(release, str):
        raise ValueError('release must be a string or None')
    if compare_with is not None and not isinstance(compare_with, str):
        raise ValueError('compare_with must be a string or None')
    result = {'status': None, 'candidates': [], 'comparisons': [],
              'release': release, 'compare_with': compare_with,
              'absence_in_sdk_proven': False, 'limitations': list(LIMITATIONS),
              'trace': {'tool': 'search_verified_samples', 'evidence_loaded': False,
                        'matched_terms': {}, 'elapsed_ms': None}}

    def finish(status):
        result['status'] = status
        if status != 'verified_candidates_found':
            result['candidates'] = []
            result['comparisons'] = []
        result['trace']['elapsed_ms'] = round((time.perf_counter()-started)*1000, 3)
        return result

    if not release or (compare_with is not None and not compare_with):
        return finish('needs_version')
    if release not in SPECS or (compare_with is not None and compare_with not in SPECS):
        return finish('unsupported_release')
    # A small alias index cannot safely interpret negated intent or exclusions.
    if any(term in message.casefold() for term in ('不要', '不是', '不需要', '不想', 'not ', "don't", 'without ')):
        return finish('needs_intent_clarification')
    terms = {}
    for name in TARGETS:
        matches = [alias for alias in ALIASES[name] if alias in message]
        qualified_names = re.findall(
            r'(?<![A-Za-z0-9_$.])(?:[A-Za-z_$][A-Za-z0-9_$]*\.)*'
            + re.escape(name) + r'(?![A-Za-z0-9_$])', message, re.IGNORECASE)
        owner = TARGETS[name][0]
        allowed = {name.casefold(), (owner+'.'+name).casefold()}
        if name == 'channelLayout':
            allowed.add(('audio.'+owner+'.'+name).casefold())
        if any(value.casefold() in allowed for value in qualified_names):
            matches.insert(0, name)
        if matches:
            terms[name] = matches
    result['trace']['matched_terms'] = terms
    if not terms:
        return finish('no_verified_match')
    try:
        catalog = load_catalog() if directory is None else load_catalog(directory)
    except (ValueError, OSError, KeyError, TypeError) as error:
        # Do not expose private paths or raw parser/service errors to callers.
        result['trace']['failure_kind'] = type(error).__name__
        return finish('evidence_unavailable')
    result['trace']['evidence_loaded'] = True
    for name, matches in terms.items():
        records = query(catalog, release, name)['records']
        if len(records) != 1:
            return finish('evidence_unavailable')
        result['candidates'].append({'name': name, 'matched_terms': matches,
                                     'selection_basis': 'exact_name_or_reviewed_alias',
                                     'evidence': records[0]})
        if compare_with is not None:
            comparison = compare(catalog, release, compare_with, name)
            if comparison['status'] != 'selected_declarations_compared':
                result['candidates'] = []
                result['comparisons'] = []
                return finish('evidence_unavailable')
            result['comparisons'].append(comparison)
    return finish('verified_candidates_found')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--message', required=True)
    parser.add_argument('--release')
    parser.add_argument('--compare-with')
    args = parser.parse_args()
    try:
        output = search_requirements(args.message, args.release, args.compare_with)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(output, ensure_ascii=True, indent=2))
