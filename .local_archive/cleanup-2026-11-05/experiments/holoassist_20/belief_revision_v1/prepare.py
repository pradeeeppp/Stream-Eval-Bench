"""Freeze 4+4 native-frame packets for every reviewed source video."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REVIEWS = ROOT / 'online_pilot_v0/reviews/batch_v1'

PREDICATES = {
    'HA01': 'the interchangeable lens is visibly separated from the DSLR body',
    'HA02': 'the large central printer LCD is visibly illuminated',
    'HA03': 'the round tabletop is visibly seated on the upright white support frame',
    'HA04': 'the main cabinet access door is open with interior components exposed',
    'HA05': 'a hand is inside the clear bin of metal fasteners',
    'HA06': 'the rectangular battery is visibly clear of the DSLR battery compartment',
    'HA07': 'the action camera is visibly clear of the white molded packaging insert',
    'HA08': 'the clear vessel is tilted with its mouth over the open reservoir',
    'HA09': 'the underside face of the round perforated panel is visibly exposed',
    'HA10': 'the upper mesh basket is tilted away from an upright cart frame',
    'HB01': 'the black drive belt is free of the machine pulley route',
    'HB02': 'the main cabinet access door is open with interior components exposed',
    'HB03': 'the interchangeable lens is visibly separated from the DSLR body',
    'HB04': 'the action camera is visibly clear of the white molded packaging insert',
    'HB05': 'the black side panel is clear of the desktop chassis and the interior is exposed',
    'HB06': 'the green expansion board is visibly outside the desktop chassis',
    'HB07': 'the round tabletop is visibly clear of the white support frame',
    'HB08': 'the long black rail is visibly separated from the remaining table frame',
    'HB09': 'the paper drawer below the main front cover is visibly extended with its interior exposed',
    'HB10': 'the detached reservoir is positioned under visibly flowing faucet water',
}
UNCERTAIN_PRIOR = {'HA06', 'HA08', 'HB06'}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def pts_for(video):
    data = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_frames',
        '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'json', str(video)]))
    return [float(f['best_effort_timestamp_time']) for f in data['frames']]


def main():
    graphs = [json.loads(line) for line in (REVIEWS / 'evidence_graphs.reviewed.jsonl').read_text().splitlines()]
    cases = []
    for graph in graphs:
        sid = graph['source_id']
        video = ROOT / graph['source']['video_path']
        assert digest(video) == graph['source']['sha256']
        pts = pts_for(video)
        observations = [n for n in graph['nodes'] if n['type'] == 'observation']
        pre = next(n for n in observations if n['role'] == 'pre')['frame_index_zero_based']
        positive = next(n for n in observations if n['role'] == 'positive')['frame_index_zero_based']
        indices = {'A': [pre - 9, pre - 6, pre - 3, pre],
                   'B': [positive, positive + 3, positive + 6, positive + 9]}
        assert indices['A'][0] >= 0 and indices['B'][-1] < len(pts)
        assert indices['A'][-1] < indices['B'][0]
        media = HERE / 'media' / sid
        media.mkdir(parents=True, exist_ok=True)
        selected = indices['A'] + indices['B']
        expression = '+'.join(f'eq(n\\,{i})' for i in selected)
        with tempfile.TemporaryDirectory(prefix='belief_packets_') as tmp:
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(video),
                            '-map', '0:v:0', '-an', '-vf', f'select={expression}',
                            '-fps_mode', 'passthrough', '-start_number', '0', '-q:v', '2',
                            '-y', str(Path(tmp) / '%02d.jpg')], check=True)
            assert len(list(Path(tmp).glob('*.jpg'))) == 8
            for j, index in enumerate(selected):
                (media / f'{index:06d}.jpg').write_bytes((Path(tmp) / f'{j:02d}.jpg').read_bytes())
        packets = {}
        sheet = Image.new('RGB', (320 * 4, 208 * 2), '#101820')
        draw = ImageDraw.Draw(sheet)
        for row, packet_id in enumerate(('A', 'B')):
            frames = []
            for col, index in enumerate(indices[packet_id]):
                path = media / f'{index:06d}.jpg'
                im = Image.open(path).convert('RGB')
                im.thumbnail((320, 180))
                sheet.paste(im, (col * 320, row * 208))
                draw.text((col * 320 + 4, row * 208 + 183),
                          f'{packet_id} frame {index} | {pts[index]:.6f} s', fill='white')
                frames.append({'native_frame_index': index, 'source_pts_seconds': pts[index],
                               'path': str(path.relative_to(HERE)), 'sha256': digest(path)})
            duration = pts[indices[packet_id][-1]] - pts[indices[packet_id][0]]
            packets[packet_id] = {'frames': frames, 'capture_start': frames[0]['source_pts_seconds'],
                                  'capture_end': frames[-1]['source_pts_seconds'],
                                  'sampled_fps': 3 / duration}
        sheet.save(media / 'review.png')
        qualified = graph['task_proposal']['qualification'] == 'provisional'
        cases.append({'case_id': sid, 'source_task_id': graph['task_id'],
                      'source_sha256': graph['source']['sha256'],
                      'graph_sha256': digest(REVIEWS / sid / 'evidence_graph.json'),
                      'predicate': PREDICATES[sid], 'packets': packets,
                      'earlier_target_seconds': packets['A']['capture_end'],
                      'later_target_seconds': packets['B']['capture_end'],
                      'earlier_gold': ('unknown' if sid in UNCERTAIN_PRIOR else 'no') if qualified else None,
                      'later_gold': 'yes' if qualified else None,
                      'primary_qualified': qualified,
                      'clean_revision_opportunity': qualified and sid not in UNCERTAIN_PRIOR,
                      'prior_uncertainty_reason': 'Prior visual relation is not sufficiently established for a negative label.'
                                                   if sid in UNCERTAIN_PRIOR else None,
                      'annotation_status': 'assistant_review_pending_independent_adjudication',
                      'packet_visual_review': 'pending',
                      'qualification_notes': graph['review']['findings']})
        print(f'{sid}: prepared 8 frames, primary={qualified}', flush=True)
    (HERE / 'cases.json').write_text(json.dumps(cases, indent=2) + '\n')
    print('Prepared 20 cases; visual endpoint confirmation required before inference.')


if __name__ == '__main__':
    main()
