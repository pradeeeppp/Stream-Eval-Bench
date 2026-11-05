"""Verify candidate source/packet mappings against frame hashes and input JPEGs."""
import argparse
import bisect
import json
import subprocess
import tempfile
from pathlib import Path

from review_media import HERE, ROOT, SOURCES, TASKS, cache, command, digest, sheets, timestamps


def selection(indices):
    return '+'.join(f'eq(n\\,{i})' for i in indices)


def hashes(video, vf):
    data = command('ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(video),
                   '-map', '0:v:0', '-an', '-vf', vf, '-fps_mode', 'passthrough',
                   '-f', 'framemd5', '-').decode()
    return [line.split(',')[-1].strip() for line in data.splitlines()
            if line and not line.startswith('#')]


def verify_source(source_id, annotation):
    pts = timestamps(source_id)
    source = SOURCES[source_id]
    video = ROOT / source['local_path']
    task = TASKS[source_id]
    positive = next(o[0] for o in annotation['observations'] if o[1] == 'positive')
    center = int(pts[positive])
    # Include the changed interval and both legacy boundary anchors.
    packets = set(range(max(0, task['pre_event_checkpoint_seconds'] - 1),
                        task['first_positive_sample_seconds'] + 3))
    packets.update(range(max(0, center - 2), center + 3))
    packet_count = len(list((ROOT / 'stream_frames' / source['session_id']).glob('[0-9][0-9][0-9][0-9].jpg')))
    packets = sorted(t for t in packets if t < packet_count)
    # fps=1 with default near rounding selects the last frame rounded to each
    # output-grid second. This hypothesis is checked against actual frame hashes.
    indices = [max(0, bisect.bisect_left(pts, t + 0.5) - 1) for t in packets]
    assert len(set(indices)) == len(indices), 'Duplicate mapping requires explicit handling'
    native_hashes = hashes(video, f'select={selection(indices)},scale=640:-1')
    sampled_hashes = hashes(video, f'fps=1,scale=640:-1,select={selection(packets)}')
    assert len(native_hashes) == len(sampled_hashes) == len(packets)
    assert native_hashes == sampled_hashes, f'PTS mapping hypothesis failed: {source_id}'
    with tempfile.TemporaryDirectory(prefix='stream_review_timing_') as tmp:
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(video),
                        '-map', '0:v:0', '-an', '-vf',
                        f'fps=1,scale=640:-1,select={selection(packets)}',
                        '-fps_mode', 'passthrough', '-q:v', '3', '-start_number', '0',
                        '-y', str(Path(tmp) / '%04d.jpg')], check=True)
        mapping = []
        for j, (packet, index, frame_hash) in enumerate(zip(packets, indices, sampled_hashes)):
            existing = ROOT / 'stream_frames' / source['session_id'] / f'{packet + 1:04d}.jpg'
            assert digest(existing) == digest(Path(tmp) / f'{j:04d}.jpg'), (source_id, packet)
            mapping.append({'packet_time_seconds': packet, 'native_frame_index': index,
                            'source_pts_seconds': pts[index], 'decoded_scaled_frame_md5': frame_hash,
                            'stream_path': str(existing.relative_to(ROOT)),
                            'stream_jpeg_sha256': digest(existing)})
    path = cache(source_id) / 'packet_mapping.json'
    path.write_text(json.dumps(mapping, indent=2) + '\n')
    # Show actual delivered frames around the review anchor, not just native
    # frames that may never be supplied to the model.
    nearby = [p['native_frame_index'] for p in mapping if center - 1 <= p['packet_time_seconds'] <= center + 1]
    paths = sheets(source_id, 'delivered', nearby, width=480, columns=3)
    print(json.dumps({'source_id': source_id, 'verified_packets': len(mapping),
                      'review_anchor_pts': pts[positive], 'delivered_review': paths}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('sources', nargs='*', default=list(SOURCES))
    args = parser.parse_args()
    annotations = json.loads((HERE / 'annotations.json').read_text())
    for source_id in args.sources:
        verify_source(source_id, annotations[source_id])


if __name__ == '__main__':
    main()
