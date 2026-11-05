"""Download pinned source MP4s and verify them against the shipped evidence graphs."""
import argparse
import concurrent.futures
import hashlib
import http.client
import json
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

from protocol import HERE, digest


def file_hash(path):
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def load_sources():
    root = HERE.parent
    sources = json.loads((root / 'online_pilot_v0/sources.json').read_text())['sources']
    cases = {case['case_id']: case for case in json.loads((HERE / 'cases.json').read_text())}
    if len(sources) != 20 or {source['source_id'] for source in sources} != set(cases):
        raise ValueError('Expected the same 20 sources in the source register and frozen cases')
    for source in sources:
        sid = source['source_id']
        graph_path = root / 'online_pilot_v0/reviews/batch_v1' / sid / 'evidence_graph.json'
        if digest(graph_path) != cases[sid]['graph_sha256']:
            raise ValueError(f'{sid}: reviewed evidence graph missing or changed')
        graph = json.loads(graph_path.read_text())
        if not (source['sha256'] == cases[sid]['source_sha256'] == graph['source']['sha256']):
            raise ValueError(f'{sid}: source hash disagrees with reviewed evidence graph')
    return sources


def download(source, root, opener, retries=3):
    relative = Path(source['local_path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe destination path in source manifest')
    destination = root / relative
    expected = source['sha256']
    if destination.exists():
        if file_hash(destination) != expected:
            raise ValueError(f'Existing video has the wrong SHA256; move it aside before retrying: {destination}')
        return {'source_id': source['source_id'], 'status': 'already_verified', 'path': str(destination)}
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + '.part')
    for attempt in range(retries):
        if partial.exists() and file_hash(partial) == expected:
            partial.replace(destination)
            return {'source_id': source['source_id'], 'status': 'downloaded', 'path': str(destination)}
        offset = partial.stat().st_size if partial.exists() else 0
        headers = {'User-Agent': 'Stream-Eval-Bench-source-downloader', 'Accept-Encoding': 'identity'}
        if offset:
            headers['Range'] = f'bytes={offset}-'
        request = urllib.request.Request(source['source_url'], headers=headers)
        try:
            with opener(request) as response:
                status = response.status
                if status not in (200, 206):
                    raise ValueError(f'Unexpected download status: {status}')
                if status == 206:
                    expected_range = f'bytes {offset}-'
                    if not response.headers.get('Content-Range', '').startswith(expected_range):
                        raise ValueError('Server returned the wrong byte range')
                # A server that ignores Range returns 200; restart rather than append.
                with partial.open('ab' if status == 206 else 'wb') as stream:
                    for block in iter(lambda: response.read(1024 * 1024), b''):
                        stream.write(block)
            if file_hash(partial) != expected:
                partial.unlink()
                raise ValueError(f'{source["source_id"]}: downloaded bytes failed SHA256 verification')
            partial.replace(destination)
            return {'source_id': source['source_id'], 'status': 'downloaded', 'path': str(destination)}
        except (OSError, ValueError, urllib.error.URLError, http.client.HTTPException) as error:
            if isinstance(error, urllib.error.HTTPError) and error.code == 416 and partial.exists():
                partial.unlink()
            if attempt + 1 == retries:
                raise RuntimeError(f'{source["source_id"]}: download failed ({type(error).__name__}); '
                                   'partial bytes are retained when useful for resuming') from None
            time.sleep(min(2 ** attempt, 8))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', nargs='+', help='Source IDs to download; default: all twenty')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--retries', type=int, default=3)
    parser.add_argument('--output-dir', type=Path, default=HERE.parent,
                        help='Dataset root; source local_path values are relative to this directory')
    parser.add_argument('--verify-only', action='store_true', help='Hash local movies without network access')
    parser.add_argument('--list', action='store_true', help='Print pinned IDs, URLs and hashes without downloading')
    args = parser.parse_args()
    if not 1 <= args.workers <= 16 or not 1 <= args.retries <= 5:
        parser.error('workers must be 1..16 and retries 1..5')
    sources = load_sources()
    if args.cases:
        selected = set(args.cases)
        if selected - {source['source_id'] for source in sources}:
            parser.error('Unknown source ID')
        sources = [source for source in sources if source['source_id'] in selected]
    if args.list:
        print(json.dumps([{key: source[key] for key in ['source_id', 'source_url', 'sha256', 'local_path']}
                          for source in sources], indent=2))
        return
    if args.verify_only:
        for source in sources:
            path = args.output_dir / source['local_path']
            if not path.is_file() or file_hash(path) != source['sha256']:
                raise ValueError(f'Missing or changed source video: {path}')
        print(json.dumps({'verified_videos': len(sources), 'reviewed_graphs_verified': 20}, indent=2))
        return
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()

    def opener(request):
        return urllib.request.urlopen(request, context=context, timeout=90)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(download, source, args.output_dir, opener, args.retries) for source in sources]
        for future in concurrent.futures.as_completed(futures):
            print(json.dumps(future.result()), flush=True)


if __name__ == '__main__':
    main()
