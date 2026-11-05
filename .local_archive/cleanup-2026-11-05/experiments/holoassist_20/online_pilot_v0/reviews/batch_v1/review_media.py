"""Reproducible, standard-library-only video review preparation.

Contact labels are zero-based native frame index | actual source PTS seconds.
Generated media/PTS caches live in the ignored full_review directory.
"""
import argparse
import bisect
import hashlib
import json
import struct
import subprocess
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
PILOT = HERE.parents[1]
ROOT = PILOT.parent
SOURCES = {s['source_id']: s for s in json.loads((PILOT / 'sources.json').read_text())['sources']}
TASKS = {t['source_id']: t for t in map(json.loads, (PILOT / 'tasks.jsonl').read_text().splitlines())}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def command(*args):
    return subprocess.check_output(args)


def cache(source_id):
    directory = ROOT / 'full_review' / 'batch_v1' / source_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def timestamps(source_id):
    directory = cache(source_id)
    source = SOURCES[source_id]
    video = ROOT / source['local_path']
    assert digest(video) == source['sha256'], source_id
    pts_path = directory / 'pts.json'
    if not pts_path.exists():
        data = json.loads(command('ffprobe', '-v', 'error', '-select_streams', 'v:0',
                                  '-show_frames', '-show_entries',
                                  'frame=best_effort_timestamp_time', '-of', 'json', str(video)))
        pts_path.write_text(json.dumps([float(f['best_effort_timestamp_time']) for f in data['frames']]))
    return json.loads(pts_path.read_text())


def nearest(pts, second):
    i = min(bisect.bisect_left(pts, second), len(pts) - 1)
    return i - 1 if i and abs(pts[i - 1] - second) < abs(pts[i] - second) else i


FONT = dict(zip('0123456789.|-', [
    '111101101101111', '010110010010111', '111001111100111',
    '111001111001111', '101101111001001', '111100111001111',
    '111100111101111', '111001001001001', '111101111101111',
    '111101111001111', '000000000000010', '010010010010010', '000000111000000']))


def png(path, width, height, pixels):
    def chunk(kind, body):
        return struct.pack('!I', len(body)) + kind + body + struct.pack('!I', zlib.crc32(kind + body))
    rows = b''.join(b'\0' + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(rows, 4)) + chunk(b'IEND', b''))


def label(pixels, width, x, y, text):
    for c in text:
        for k, value in enumerate(FONT.get(c, '0' * 15)):
            if value == '1':
                for dy in range(3):
                    for dx in range(3):
                        offset = ((y + k // 3 * 3 + dy) * width + x + k % 3 * 3 + dx) * 3
                        pixels[offset:offset + 3] = b'\xff\xff\xff'
        x += 12


def sheets(source_id, name, indices, width=320, columns=5, per_page=40):
    pts = timestamps(source_id)
    indices = sorted(set(indices))
    source = SOURCES[source_id]
    height = width * source['height'] // source['width']
    expression = '+'.join(f'eq(n\\,{i})' for i in indices)
    raw = command('ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(ROOT / source['local_path']),
                  '-map', '0:v:0', '-an', '-vf', f'select={expression},scale={width}:{height}',
                  '-fps_mode', 'passthrough', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-')
    size = width * height * 3
    assert len(raw) == len(indices) * size, (source_id, name)
    paths = []
    for start in range(0, len(indices), per_page):
        batch = indices[start:start + per_page]
        w = columns * width
        h = ((len(batch) + columns - 1) // columns) * (height + 24)
        pixels = bytearray(w * h * 3)
        for j, index in enumerate(batch):
            x = j % columns * width
            y = j // columns * (height + 24)
            frame = raw[(start + j) * size:(start + j + 1) * size]
            for row in range(height):
                dest = ((y + row) * w + x) * 3
                pixels[dest:dest + width * 3] = frame[row * width * 3:(row + 1) * width * 3]
            label(pixels, w, x + 4, y + height + 4, f'{index}|{pts[index]:.3f}')
        path = cache(source_id) / f'{name}_{start // per_page + 1:02d}.png'
        png(path, w, h, pixels)
        paths.append(str(path.resolve()))
    manifest_path = cache(source_id) / 'inspections.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest[name] = {'indices': indices, 'paths': paths, 'width': width,
                      'status': 'prepared_pending_visual_inspection'}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    return paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--details', action='store_true')
    parser.add_argument('sources', nargs='*', default=list(SOURCES))
    args = parser.parse_args()
    baseline = HERE / 'baseline_hashes.json'
    if not baseline.exists():
        baseline.write_text(json.dumps({name: digest(PILOT / name) for name in
            ['sources.json', 'tasks.jsonl', 'public_tasks.jsonl', 'evidence_graphs.jsonl']}, indent=2) + '\n')
    for source_id in args.sources:
        pts = timestamps(source_id)
        if args.details:
            annotation = json.loads((HERE / 'annotations.json').read_text())[source_id]
            paths = []
            for number, (start, stop) in enumerate(annotation['native_ranges'], 1):
                paths += sheets(source_id, f'native{number}', range(start, stop + 1))
            if annotation.get('extra_seconds'):
                paths += sheets(source_id, 'extra', [nearest(pts, t) for t in annotation['extra_seconds']],
                                width=480, columns=3, per_page=24)
            print(json.dumps({'source_id': source_id, 'details': paths}), flush=True)
            continue
        task = TASKS[source_id]
        overview = [nearest(pts, t) for t in range(0, int(pts[-1]) + 1, 5)] + [len(pts) - 1]
        start = max(0, task['pre_event_checkpoint_seconds'] - 1)
        stop = min(pts[-1], task['first_positive_sample_seconds'] + 3)
        event = [nearest(pts, start + j / 2) for j in range(int((stop - start) * 2) + 1)]
        result = {'source_id': source_id, 'overview': sheets(source_id, 'overview', overview),
                  'candidate': sheets(source_id, 'candidate', event)}
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
