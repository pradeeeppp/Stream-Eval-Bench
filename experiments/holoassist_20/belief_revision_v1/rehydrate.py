"""Recreate frozen model inputs without changing labels or review records.

Place the source MP4s at the paths in ../online_pilot_v0/sources.json first.
FFmpeg and Pillow are required. Encoder differences are rejected by hash checks.
"""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from protocol import HERE, digest


def restore_case(case, source):
    from PIL import Image, ImageDraw

    sid = case['case_id']
    source_path = HERE.parent / source['local_path']
    h = hashlib.sha256()
    with source_path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    if h.hexdigest() != case['source_sha256'] or source['sha256'] != case['source_sha256']:
        raise ValueError(f'{sid}: source video does not match the frozen input')

    frames = [frame for packet in case['packets'].values() for frame in packet['frames']]
    expression = '+'.join(f"eq(n\\,{frame['native_frame_index']})" for frame in frames)
    with tempfile.TemporaryDirectory(prefix='belief_packets_') as directory:
        temporary = Path(directory)
        subprocess.run([
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(source_path),
            '-map', '0:v:0', '-an', '-vf', f'select={expression}',
            '-fps_mode', 'passthrough', '-start_number', '0', '-q:v', '2',
            '-y', str(temporary / '%02d.jpg'),
        ], check=True)
        if len(list(temporary.glob('*.jpg'))) != len(frames):
            raise ValueError(f'{sid}: decoded frame count differs')
        sheet = Image.new('RGB', (1280, 416), '#101820')
        draw = ImageDraw.Draw(sheet)
        for index, frame in enumerate(frames):
            path = temporary / f'{index:02d}.jpg'
            if digest(path) != frame['sha256']:
                raise ValueError(f'{sid}: extracted frame hash differs: {frame["path"]}')
            row, column = divmod(index, 4)
            image = Image.open(path).convert('RGB')
            image.thumbnail((320, 180))
            sheet.paste(image, (column * 320, row * 208))
            packet_id = ('A', 'B')[row]
            draw.text((column * 320 + 4, row * 208 + 183),
                      f"{packet_id} frame {frame['native_frame_index']} | "
                      f"{frame['source_pts_seconds']:.6f} s", fill='white')
        sheet_path = temporary / 'review.png'
        sheet.save(sheet_path)
        if digest(sheet_path) != case['packet_review_sha256']:
            raise ValueError(f'{sid}: contact sheet hash differs; use the recorded Pillow version')
        outputs = [(temporary / f'{i:02d}.jpg', HERE / frame['path'])
                   for i, frame in enumerate(frames)]
        outputs.append((sheet_path, HERE / 'media' / sid / 'review.png'))
        # Validate the entire case before writing any missing output.
        for origin, target in outputs:
            if target.exists() and digest(target) != digest(origin):
                raise ValueError(f'{sid}: refusing to overwrite changed input {target}')
        for origin, target in outputs:
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(origin.read_bytes())
    print(f'{sid}: frozen frame and contact sheet hashes verified', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', nargs='+', help='Restore selected case IDs; default: all twenty.')
    args = parser.parse_args()
    cases = json.loads((HERE / 'cases.json').read_text())
    sources = json.loads((HERE.parent / 'online_pilot_v0/sources.json').read_text())['sources']
    by_id = {source['source_id']: source for source in sources}
    if args.cases and set(args.cases) - {case['case_id'] for case in cases}:
        parser.error('Unknown case ID')
    for case in cases:
        if not args.cases or case['case_id'] in args.cases:
            restore_case(case, by_id[case['case_id']])


if __name__ == '__main__':
    main()
