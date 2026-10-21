"""Read-only recipient check of a selected runtime and its external eight databases."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, ProxyHandler, HTTPRedirectHandler, build_opener

VERSION = '1.0.0'
FILES = {
    'documents': ('doc_chunks', 'build_receipt', 'chunks'),
    'document_names': ('names', 'source', 'rows'),
    'declarations': ('declarations', 'receipt', 'declaration_facts'),
    'sample_catalog': ('files', 'receipt', 'input_files'),
    'sample_contexts': ('source_files', 'receipt', 'processed_source_files'),
    'project_notes': ('project_notes', 'receipt', 'projects'),
    'kit_routes': ('routes', 'receipt', 'routes'),
    'reconciliation': ('declaration_status', 'receipt', 'declarations_accounted_for'),
}
INTEGRATION = 'data/delivery/six-stage-20261019/integration/'
FORBIDDEN_PORTS = {8548, 8559, 8562}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def relative_file(root, name):
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name
            or '\x00' in name or PurePosixPath(name).is_absolute()
            or any(p in ('', '.', '..') for p in name.split('/'))):
        raise ValueError('Unsafe locked path: ' + str(name))
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Locked path escapes root: ' + name)
    return path


class LockedImports(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Load only the already hashed source bytes; ignore sys.path and stale pyc."""
    def __init__(self, root, sources):
        self.entries = {}
        self.stdlib_paths = tuple(sys.path)
        for name, raw in sources.items():
            prefix = next((p for p in ('tools/', INTEGRATION) if name.startswith(p)), None)
            if prefix is None or not name.endswith('.py'):
                continue
            parts = name[len(prefix):-3].split('/')
            package = parts[-1] == '__init__'
            if package:
                parts.pop()
            module = '.'.join(parts)
            if not module or module in self.entries or parts[0] in sys.stdlib_module_names:
                raise ValueError('Ambiguous runtime module: ' + name)
            self.entries[module] = (root / name, raw, package)

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.entries:
            return importlib.util.spec_from_loader(fullname, self, is_package=self.entries[fullname][2])
        if fullname.split('.')[0] in sys.stdlib_module_names:
            # Some locked libraries prepend integration paths themselves. Do
            # not let an unlocked csv.py/other stdlib names there shadow Python.
            spec = (importlib.machinery.BuiltinImporter.find_spec(fullname)
                    or importlib.machinery.FrozenImporter.find_spec(fullname)
                    or importlib.machinery.PathFinder.find_spec(
                        fullname, path if path is not None else self.stdlib_paths))
            if spec is not None:
                return spec
            raise ModuleNotFoundError('Standard library module unavailable: ' + fullname)
        raise ModuleNotFoundError('Module is not in selected code lock: ' + fullname)

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        path, raw, package = self.entries[module.__name__]
        module.__file__ = str(path)
        if package:
            module.__path__ = [str(path.parent)]
        exec(compile(raw, str(path), 'exec'), module.__dict__)


def stamp(path):
    info = path.stat()
    return info.st_size, info.st_mtime_ns, info.st_ctime_ns


def protect_io(report_fd):
    """Defense in depth for accidental writes, model processes and nonlocal sockets."""
    def audit(event, args):
        if event == 'open':
            path, mode, flags = args
            if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                if path != report_fd:
                    raise PermissionError('Recipient verification forbids file writes')
        elif event == 'sqlite3.connect':
            if not str(args[0]).startswith('file:') or '?mode=ro' not in str(args[0]):
                raise PermissionError('Only read-only SQLite connections allowed')
        elif event in ('socket.connect', 'socket.bind'):
            address = args[1]
            if (not isinstance(address, tuple) or address[0] != '127.0.0.1'
                    or address[1] in FORBIDDEN_PORTS):
                raise PermissionError('Only temporary loopback sockets allowed')
        elif event in ('subprocess.Popen', 'os.system', 'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir'):
            raise PermissionError('Recipient verification forbids mutation/processes: ' + event)
    sys.addaudithook(audit)


def check_databases(tools, result):
    """Same mode=ro/quick_check/receipt checks as verify_evidence_databases.verify.

    That verifier is not included in runtime32 and its entrypoint instantiates
    EvidenceTools again. Keep the read-only checks here to avoid another hash pass.
    """
    for label, path in tools.paths.items():
        table, key, count_key = FILES[label]
        item = dict(label=label, bytes=path.stat().st_size,
                    sha256=tools.manifest['artifacts'][label]['sha256'], sha256_verified=True)
        result['databases'].append(item)
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as con:
            con.execute('PRAGMA query_only=ON')
            if [r[0] for r in con.execute('PRAGMA quick_check')] != ['ok']:
                raise ValueError('SQLite quick_check failed: ' + label)
            item['sqlite_quick_check'] = 'ok'
            receipt = json.loads(con.execute('SELECT value FROM metadata WHERE key=?', (key,)).fetchone()[0])
            rows = con.execute('SELECT count(*) FROM ' + table).fetchone()[0]
            item.update(table=table, rows=rows, receipt_rows=receipt[count_key])
            if rows != receipt[count_key]:
                raise ValueError('Receipt count differs: ' + label)
            source = receipt.get('source_manifest_sha256')
            if source is not None and source != tools.manifest['source_manifest_sha256']:
                raise ValueError('Source manifest differs: ' + label)
            if label == 'declarations':
                if con.execute("SELECT count(*) FROM declarations WHERE json_extract(body,'$.api_id') IS NOT NULL").fetchone()[0]:
                    raise ValueError('Unexpected formal API identities')
            # Other recorded counts, without scanning FTS shadow tables.
            extras = {'documents': {'files': 'input_files'},
                      'sample_catalog': {'projects': 'projects', 'modules': 'modules'},
                      'sample_contexts': {'contexts': 'contexts'},
                      'reconciliation': {'document_candidates': 'document_candidate_edges'}}.get(label, {})
            item['additional_counts'] = {}
            for extra, receipt_key in extras.items():
                count = con.execute('SELECT count(*) FROM ' + extra).fetchone()[0]
                item['additional_counts'][extra] = count
                if count != receipt[receipt_key]:
                    raise ValueError('Receipt count differs: ' + label + '/' + extra)
    counts = {x['label']: x['rows'] for x in result['databases']}
    if counts['documents'] != counts['document_names'] or counts['declarations'] != counts['reconciliation']:
        raise ValueError('Paired database counts differ')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('HTTP redirects forbidden')


def check_http(tools, result):
    # Reuse the real transport, rather than verify_evidence_http.verify which
    # writes package-local tamper fixtures and repeats all database fingerprints.
    from serve_evidence_tools import create_server
    server = None
    for _ in range(20):
        candidate = create_server(tools, port=0)
        if candidate.server_address[0] != '127.0.0.1' or candidate.server_port in FORBIDDEN_PORTS:
            candidate.server_close()
            continue
        server = candidate
        break
    if server is None:
        raise RuntimeError('Could not allocate an allowed temporary loopback port')
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    result.update(base_url='http://127.0.0.1:' + str(server.server_port), cases=[])
    opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(path, params=None, expected=200):
        req = Request(result['base_url'] + path,
                      data=None if params is None else json.dumps(params).encode(),
                      headers={'Content-Type': 'application/json'})
        try:
            with opener.open(req, timeout=20) as response:
                status, body = response.status, json.load(response)
        except HTTPError as exc:
            with exc:
                status, body = exc.code, json.load(exc)
        result['cases'].append(dict(path=path, status=status, expected=expected, passed=status == expected))
        if status != expected:
            raise ValueError('Unexpected HTTP status: ' + path)
        return body
    try:
        health = request('/health')
        if health.get('delivery_id') != tools.manifest['delivery_id'] or health.get('read_only') is not True:
            raise ValueError('HTTP health identity differs')
        if not request('/tools').get('tools'):
            raise ValueError('HTTP tool definitions missing')
        # A bounded real query, with direct SQLite readback, inspired by
        # verify_evidence_http.verify_comparison_readback (no write-guard DELETE).
        with closing(sqlite3.connect(tools.paths['declarations'].as_uri() + '?mode=ro', uri=True)) as con:
            row = con.execute('SELECT release_id,name FROM declarations ORDER BY artifact_id LIMIT 1').fetchone()
            if row is None:
                raise ValueError('No declaration available for HTTP readback')
            version, name = row
            expected = [r[0] for r in con.execute('SELECT artifact_id FROM declarations WHERE release_id=? AND name=? COLLATE NOCASE ORDER BY artifact_id LIMIT 2', row)]
        body = request('/tools/search', dict(version=version, query=name, scope='declarations', limit=2))
        if ([r['artifact_id'] for r in body['results']] != expected
                or any(r['release_id'] != version or r['api_id'] is not None for r in body['results'])
                or not all(k in body for k in ('coverage', 'unknown_conditions', 'truncation_status'))):
            raise ValueError('HTTP declaration readback differs')
        request('/tools/search', dict(version=version, query=name, limit=101), expected=400)
        result.update(passed=True, field_readback_records=len(expected))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        result['server_closed'] = not thread.is_alive()


def verify(runtime, manifest, report, http=False):
    runtime, manifest, report = (Path(p).resolve() for p in (runtime, manifest, report))
    # Never create reports inside protected inputs. The parent must already exist.
    if report.is_relative_to(runtime) or report.is_relative_to(manifest.parent):
        raise ValueError('Report must be outside runtime and data directories')
    with report.open('x', encoding='utf8') as stream:
        result = dict(schema_version=1, author='Codex', validator_version=VERSION,
                      validator_sha256=digest(Path(__file__).read_bytes()),
                      checked_at=datetime.now(timezone.utc).isoformat(),
                      runtime=str(runtime), manifest=str(manifest), passed=False, complete=False,
                      stage='code_lock', databases=[], read_only=True,
                      member_acceptance=False, recipient_identity_verified=False,
                      actual_receipt_confirmed_by_member=False, full_public_sdk_inventory_established=False,
                      sdk_build_verified=False, model_tested=False,
                      http=dict(requested=http, passed=False))
        started = time.monotonic()
        def save():
            stream.seek(0)
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.truncate()
            stream.flush()
        save()
        try:
            protect_io(stream.fileno())
            raw_lock = (runtime / 'runtime-lock.json').read_bytes()
            lock = json.loads(raw_lock)
            sources = {}
            for name, expected in lock['code_sha256'].items():
                raw = relative_file(runtime, name).read_bytes()
                if digest(raw) != expected:
                    raise ValueError('Runtime code fingerprint mismatch: ' + name)
                sources[name] = raw
            for required in ('tools/run_locked_runtime.py', 'tools/evidence_tools.py', 'tools/delivery_sources.py'):
                if required not in sources:
                    raise ValueError('Required runtime code is not locked: ' + required)
            # Fresh -I -S child has no author modules or site packages. The finder
            # takes precedence even if runtime code adds paths for doc_rag.
            finder = LockedImports(runtime, sources)
            sys.meta_path.insert(0, finder)
            result.update(runtime_lock_sha256=digest(raw_lock), locked_files=len(sources),
                          runtime_delivery_id=lock['delivery_id'])
            result['stage'] = 'manifest_binding'
            from run_locked_runtime import validate
            validate(runtime, manifest)
            data_raw = manifest.read_bytes()
            data = json.loads(data_raw)
            result.update(manifest_sha256=digest(data_raw), data_delivery_id=data['delivery_id'])
            if set(data['artifacts']) != set(FILES):
                raise ValueError('Expected exactly the contracted eight artifact labels')
            identity_data = {k: v for k, v in data.items() if k != 'delivery_id'}
            identity = digest(json.dumps(identity_data, sort_keys=True, separators=(',', ':')).encode())
            if data['delivery_id'] != 'openharmony-evidence-' + identity[:20]:
                raise ValueError('Data manifest identity mismatch')
            paths = [relative_file(manifest.parent, e['path']) for e in data['artifacts'].values()]
            if len(set(paths)) != 8:
                raise ValueError('Eight distinct databases required')
            result['stage'] = 'data_fingerprints'
            for path in paths:
                if any(Path(str(path) + suffix).exists() for suffix in ('-wal', '-shm', '-journal')):
                    raise ValueError('Database must be a closed snapshot without sidecars: ' + path.name)
                with path.open('rb') as source:
                    header = source.read(100)
                if header[:16] != b'SQLite format 3\x00' or header[18:20] != b'\x01\x01':
                    raise ValueError('Expected a closed rollback-mode SQLite snapshot: ' + path.name)
            before = {p: stamp(p) for p in paths}
            import delivery_sources
            original_hash = delivery_sources.sha256
            cache = {}
            def cached_hash(path):
                path = Path(path).resolve()
                current = stamp(path)
                if path not in cache or cache[path][0] != current:
                    value = original_hash(path)
                    if stamp(path) != current:
                        raise ValueError('Database changed during hashing: ' + path.name)
                    cache[path] = (current, value)
                return cache[path][1]
            delivery_sources.sha256 = cached_hash
            from evidence_tools import EvidenceTools
            tools = EvidenceTools(manifest)
            result['stage'] = 'sqlite_counts'
            check_databases(tools, result)
            if http:
                result['stage'] = 'http'
                check_http(tools, result['http'])
            result['stage'] = 'final_stability'
            if any(stamp(p) != before[p] for p in paths):
                raise ValueError('Database changed during verification')
            if manifest.read_bytes() != data_raw or (runtime / 'runtime-lock.json').read_bytes() != raw_lock:
                raise ValueError('Lock/manifest changed during verification')
            validate(runtime, manifest)
            result.update(passed=True, complete=True, stage='complete', database_count=len(tools.paths),
                          database_bytes=sum(p.stat().st_size for p in paths), fingerprint_scans=len(cache))
        except Exception as exc:
            result['error'] = dict(stage=result['stage'], type=type(exc).__name__, message=str(exc))
        finally:
            result['elapsed_seconds'] = round(time.monotonic() - started, 3)
            save()
        return 0 if result['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True, help='Selected received code package directory')
    parser.add_argument('--manifest', type=Path, required=True, help='External eight-database manifest')
    parser.add_argument('--report', type=Path, required=True, help='New JSON file outside runtime/data; parent must exist')
    parser.add_argument('--http', action='store_true', help='Also check the real transport on a temporary loopback port')
    parser.add_argument('--_worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args._worker:
        return subprocess.run([sys.executable, '-I', '-S', '-B', '-X', 'utf8', str(Path(__file__).resolve()),
                               *sys.argv[1:], '--_worker'], check=False).returncode
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        parser.error('Internal worker requires isolated Python with -I -S -B')
    try:
        return verify(args.runtime, args.manifest, args.report, args.http)
    except Exception as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
