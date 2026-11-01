"""Download official public SDK archives with bounded resumable I/O and SHA256 checks."""
import argparse
import hashlib
import http.client
import json
from pathlib import Path
import re
import time
import urllib.request
import urllib.error
from collect_official_sources import ROOT, write_json

SPECS = {'4.1': {'api_level': 11, 'sdk_version': '4.1.7.5'},
         '5.0.3': {'api_level': 15, 'sdk_version': '5.0.3.135', 'max_archive_bytes': 5 * 1024 ** 3,
                   'expected_archive_bytes': 4563988878},
         '6.1': {'api_level': 23, 'sdk_version': '6.1.0.31'}}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def collect(release, root, budget=900):
    if release not in SPECS or budget <= 0:
        raise ValueError('Unsupported release or invalid time budget')
    root.mkdir(parents=True, exist_ok=True)
    url = f'https://repo.huaweicloud.com/openharmony/os/{release}-Release/ohos-sdk-windows_linux-public.tar.gz'
    with urllib.request.urlopen(url + '.sha256', timeout=30) as response:
        checksum_raw = response.read(4096)
    match = re.fullmatch(rb'\s*([a-fA-F0-9]{64})(?:\s+[^\r\n]+)?\s*', checksum_raw)
    if not match:
        raise ValueError('Invalid official checksum response')
    expected = match[1].decode('ascii').lower()
    archive = root / f'ohos-{release}-public.tar.gz'
    receipt_path = root / f'ohos-{release}-public.json'
    partial = archive.with_suffix(archive.suffix + '.part')
    context = {'platform': 'OpenHarmony', 'release': release, **SPECS[release], 'url': url,
               'checksum_url': url + '.sha256', 'sha256': expected,
               'scope': 'Official archive integrity; extracted component visibility/build verification is separate'}
    if archive.exists():
        if digest(archive) != expected:
            raise ValueError('Existing SDK archive differs; preserved without overwrite')
        write_json(receipt_path, {**context, 'status': 'archive_verified', 'size': archive.stat().st_size})
        return context
    offset = partial.stat().st_size if partial.exists() else 0
    old = {}
    if offset:
        old = json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.exists() else {}
        if any(old.get(k) != context[k] for k in ('url', 'sha256', 'release')):
            raise ValueError('Partial archive provenance differs; preserved without overwrite')
    started = time.monotonic()
    total = None
    last = 0
    attempts = 0
    consecutive_failures = 0
    initial_received = offset
    known_size = context.get('expected_archive_bytes') or old.get('size')
    try:
        # An interrupted run may have all bytes but not yet have published its receipt.
        if offset and (not known_size or offset == known_size) and digest(partial) == expected:
            partial.replace(archive)
            write_json(receipt_path, {**context, 'status': 'archive_verified', 'size': offset, 'received': offset})
            return context
        while total is None or offset < total:
            attempts += 1
            max_attempts = (SPECS[release].get('max_archive_bytes', 3 * 1024 ** 3) // (16 * 1024 * 1024)) + 64
            if attempts > max_attempts or time.monotonic() - started > budget:
                raise TimeoutError('SDK transfer budget exhausted; partial retained')
            end = offset + 16 * 1024 * 1024 - 1
            if total is not None:
                end = min(end, total - 1)
            request = urllib.request.Request(url, headers={'Range': f'bytes={offset}-{end}'})
            before = offset
            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    content_range = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range', ''))
                    if response.status != 206 or not content_range or int(content_range[1]) != offset or int(content_range[2]) > end:
                        raise ValueError('Server did not honor the exact requested range')
                    current_total = int(content_range[3])
                    if context.get('expected_archive_bytes') and current_total != context['expected_archive_bytes']:
                        raise ValueError('Official SDK length differs from pinned release')
                    response_end = int(content_range[2])
                    if not offset <= response_end < current_total <= SPECS[release].get('max_archive_bytes', 3 * 1024 ** 3) or (total is not None and current_total != total):
                        raise ValueError('Invalid or changing SDK archive length')
                    total = current_total
                    write_json(receipt_path, {**context, 'status': 'downloading', 'size': total, 'received': offset})
                    with partial.open('ab' if offset else 'wb') as stream:
                        while True:
                            if time.monotonic() - started > budget:
                                raise TimeoutError('SDK transfer time budget exhausted; partial retained')
                            block = response.read1(1024 * 1024)
                            if not block:
                                break
                            if offset + len(block) > response_end + 1:
                                raise ValueError('SDK response exceeds declared byte range')
                            stream.write(block)
                            offset += len(block)
                            if time.monotonic() - last >= 15:
                                print(json.dumps({'release': release, 'received': offset, 'total': total, 'percent': round(100 * offset / total, 1)}), flush=True)
                                last = time.monotonic()
                consecutive_failures = 0
            except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.IncompleteRead) as exc:
                if isinstance(exc, urllib.error.HTTPError):
                    raise
                consecutive_failures = consecutive_failures + 1 if offset == before else 1
                if consecutive_failures >= 3 or time.monotonic() - started > budget:
                    raise
                print(json.dumps({'release':release,'received':offset,'retry_error_type':type(exc).__name__,'consecutive_failures':consecutive_failures}),flush=True)
                time.sleep(consecutive_failures)
                continue
            # A short response is resumable only if it made actual progress.
            if offset == before:
                raise ValueError('SDK transfer made no progress; partial retained')
        if digest(partial) != expected:
            raise ValueError('SDK archive SHA256 mismatch; partial retained')
        partial.replace(archive)
        write_json(receipt_path, {**context, 'status': 'archive_verified', 'size': total, 'received': total,
                                  'initial_received': initial_received, 'transfer_seconds': round(time.monotonic()-started,3),
                                  'range_attempts': attempts})
        return context
    except Exception as exc:
        write_json(receipt_path, {**context, 'status': 'transfer_incomplete', 'received': partial.stat().st_size if partial.exists() else 0,
                                  'size': total, 'initial_received': initial_received,
                                  'transfer_seconds': round(time.monotonic()-started,3), 'range_attempts': attempts,
                                  'error': type(exc).__name__ + ': ' + str(exc)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', choices=SPECS, required=True)
    parser.add_argument('--root', type=Path, default=ROOT / 'data/delivery/sdk-packages')
    parser.add_argument('--max-seconds', type=int, default=900)
    args = parser.parse_args()
    print(json.dumps(collect(args.release, args.root, args.max_seconds)))


if __name__ == '__main__':
    main()
