"""Versioned conservative identity reference; does not migrate any production data."""
import hashlib
import json
import re

VERSION = 'ohapi-id-v2'


def canonical(value):
    """Only positional JSON arrays, strings, null, booleans and safe integers."""
    def check(x):
        if x is None or type(x) is bool:
            return
        if type(x) is int and abs(x) <= 9007199254740991:
            return
        if isinstance(x, str):
            if '\x00' in x:
                raise ValueError('NUL is forbidden')
            x.encode('utf-8', errors='strict')
            return
        if isinstance(x, list):
            for item in x:
                check(item)
            return
        raise ValueError('Unsupported canonical value')
    check(value)
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(domain, payload):
    return domain + ':' + hashlib.sha256(canonical([VERSION, domain, payload])).hexdigest()


def required(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(field + ' required')
    return value


def source_id(platform, repository, commit, kind):
    for field, value in [('platform', platform), ('repository', repository), ('kind', kind)]:
        required(value, field)
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Full lowercase Git SHA1 required')
    return digest('source', [platform, repository, commit, kind])


def declaration_id(source, path, start, end, profile, variant=None):
    required(source, 'source'); required(profile, 'profile')
    required(path, 'path')
    if path.startswith('/') or '\\' in path or any(p in ('', '.', '..') for p in path.split('/')) or ':' in path:
        raise ValueError('Canonical repository-relative path required')
    if type(start) is not int or type(end) is not int or not 0 <= start < end:
        raise ValueError('Nonempty half-open UTF-8 byte span required')
    return digest('decl', [source, path, start, end, profile, variant])


def api_id(record):
    """Return null on unresolved identity. Every declaration remains addressable."""
    required(record.get('declaration_id'), 'declaration_id')
    fields = ['platform', 'release_id', 'language', 'scope', 'owners', 'kind',
              'name', 'static', 'signature', 'conditions']
    if record.get('identity_status') != 'resolved' or any(record.get(k) is None for k in fields):
        return None
    for k in ['platform', 'release_id', 'language', 'kind', 'name']:
        required(record[k], k)
    for k in ['scope', 'owners', 'signature', 'conditions']:
        if not isinstance(record[k], list):
            raise ValueError(k + ' must be a canonical array')
    scope = record['scope']
    if len(scope) != 2 or scope[0] not in ('module', 'global_file', 'native_header'):
        raise ValueError('Explicit module/global_file/native_header scope required')
    required(scope[1], 'scope locator')
    if type(record['static']) is not bool:
        raise ValueError('static must be explicit boolean')
    for owner in record['owners']:
        if not isinstance(owner, list) or len(owner) != 2:
            raise ValueError('Typed owner path required')
        for value in owner:
            required(value, 'owner')
    return digest('api', [record[k] for k in fields])


def migration_rows(old_to_declarations, declarations):
    """Never choose the first candidate for a legacy UID."""
    by_decl = {r['declaration_id']: r for r in declarations}
    if len(by_decl) != len(declarations):
        raise ValueError('Duplicate declaration ID; retain variants before migration')
    rows = []
    for old, ids in sorted(old_to_declarations.items()):
        ids = sorted(set(ids))
        targets = sorted({api_id(by_decl[d]) for d in ids if d in by_decl and api_id(by_decl[d])})
        unresolved = any(d not in by_decl or api_id(by_decl[d]) is None for d in ids)
        status = 'no_match' if not ids else 'ambiguous' if unresolved else 'one_to_one' if len(targets) == 1 else 'one_to_many'
        rows.append({'legacy_id': old, 'declaration_ids': ids, 'api_ids': targets,
                     'status': status, 'auto_redirect': status == 'one_to_one'})
    return rows
