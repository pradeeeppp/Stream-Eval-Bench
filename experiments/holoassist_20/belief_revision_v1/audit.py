"""Check input provenance, request isolation and saved-result reproducibility."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from protocol import CONFIG, HERE, PHASES, digest, prompt_for, score_episode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-media', action='store_true',
                        help='Also hash local source videos, extracted frames and contact sheets.')
    parser.add_argument('--output', type=Path, help='Save the audit report; otherwise print only.')
    args = parser.parse_args()
    cases = json.loads((HERE / 'cases.json').read_text())
    manifest = json.loads((HERE / 'execution_manifest.json').read_text())
    model = json.loads((HERE / 'model_manifest.json').read_text())
    failures, counts = [], {'videos': len(cases), 'reviewed_frames': 0,
                            'saved_requests': 0, 'completed_episodes': 0,
                            'verified_frame_files': 0}

    def check(condition, message):
        if not condition:
            failures.append(message)

    signatures = manifest['signatures']
    for key, filename in [('cases_sha256', 'cases.json'), ('protocol_sha256', 'protocol.py'),
                          ('runner_sha256', 'run.py')]:
        check(signatures[key] == digest(HERE / filename), f'{filename}: changed since execution')
    check(signatures['config'] == CONFIG, 'Protocol config changed')
    check(signatures['model_revision'] == model['revision'], 'Model revision changed')
    check(model['model_id'] == 'Qwen/Qwen2.5-VL-3B-Instruct', 'Wrong model')
    check(len(cases) == 20 and len({c['case_id'] for c in cases}) == 20, 'Expected 20 unique videos')
    check(sum(c['primary_qualified'] for c in cases) == 17, 'Expected 17 qualified targets')
    check(sum(c['clean_revision_opportunity'] for c in cases) == 14, 'Expected 14 clean opportunities')
    excluded = {c['case_id'] for c in cases if not c['primary_qualified']}
    check(excluded == {'HA05', 'HA09', 'HA10'}, 'Diagnostic exclusions changed')
    reviews = HERE.parent / 'online_pilot_v0/reviews/batch_v1'
    for case in cases:
        sid = case['case_id']
        graph_path = reviews / sid / 'evidence_graph.json'
        graph = json.loads(graph_path.read_text())
        check(digest(graph_path) == case['graph_sha256'], f'{sid}: reviewed graph changed')
        source = HERE.parent / graph['source']['video_path']
        check(graph['source']['sha256'] == case['source_sha256'], f'{sid}: source manifest mismatch')
        if args.with_media:
            h = hashlib.sha256()
            if source.exists():
                with source.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        h.update(block)
                check(h.hexdigest() == case['source_sha256'], f'{sid}: source video changed')
            else:
                check(False, f'{sid}: source video missing')
        check(case['packet_visual_review'] == 'reviewed_by_codex_2026_11_04', f'{sid}: unreviewed packets')
        if args.with_media:
            sheet = HERE / 'media' / sid / 'review.png'
            check(sheet.exists() and digest(sheet) == case['packet_review_sha256'],
                  f'{sid}: reviewed contact sheet missing or changed')
        a, b = case['packets']['A'], case['packets']['B']
        check(a['capture_end'] < b['capture_start'], f'{sid}: capture order invalid')
        check(case['earlier_target_seconds'] == a['capture_end'] and
              case['later_target_seconds'] == b['capture_end'], f'{sid}: target endpoints mismatch')
        indices = []
        for packet_id, packet in case['packets'].items():
            check(len(packet['frames']) == 4, f'{sid}/{packet_id}: expected four frames')
            times = [f['source_pts_seconds'] for f in packet['frames']]
            check(times == sorted(times) and len(set(times)) == 4, f'{sid}/{packet_id}: timestamp order')
            check(times[0] == packet['capture_start'] and times[-1] == packet['capture_end'],
                  f'{sid}/{packet_id}: packet boundary mismatch')
            for frame in packet['frames']:
                if args.with_media:
                    image = HERE / frame['path']
                    valid = image.exists() and digest(image) == frame['sha256']
                    check(valid, f'{sid}: input frame missing or changed')
                    counts['verified_frame_files'] += int(valid)
                indices.append(frame['native_frame_index'])
                counts['reviewed_frames'] += 1
        check(len(set(indices)) == 8, f'{sid}: duplicate native frame')
        if not case['primary_qualified']:
            check(case['earlier_gold'] is None and case['later_gold'] is None,
                  f'{sid}: diagnostic case has invented gold')
        if case['earlier_gold'] == 'unknown':
            check(not case['clean_revision_opportunity'], f'{sid}: unknown prior treated as correction')
        path = HERE / 'responses' / f'{sid}.json'
        record = json.loads(path.read_text()) if path.exists() else {'steps': {}}
        steps = record['steps']
        check(set(steps) <= set(PHASES), f'{sid}: unexpected phase')
        for phase, step in steps.items():
            counts['saved_requests'] += 1
            meta = PHASES[phase]
            previous = steps[meta['previous']]['raw_response'] if meta['previous'] else None
            check(step['status'] == 'ok', f'{sid}/{phase}: incomplete request saved as result')
            check(step['previous_memory'] == previous, f'{sid}/{phase}: previous memory changed')
            check(step['prompt'] == prompt_for(case, phase, previous), f'{sid}/{phase}: prompt mismatch')
            check(step['current_packets'] == meta['current'] and step['arrived_packets'] == meta['arrived'],
                  f'{sid}/{phase}: packet isolation mismatch')
            expected_frames = [{'packet_id': pid, **f} for pid in meta['current']
                               for f in case['packets'][pid]['frames']]
            check(step['input_frames'] == expected_frames, f'{sid}/{phase}: frame selection mismatch')
            check(isinstance(step['raw_response'], str) and step['generated_tokens'] > 0,
                  f'{sid}/{phase}: missing raw generation')
            check(len(step['video_grid_thw']) == len(meta['current']), f'{sid}/{phase}: video tensor count')
        recomputed = score_episode(case, steps)
        if steps:
            check(record['analysis'] == recomputed, f'{sid}: saved scores differ from recomputation')
        if recomputed['status'] != 'incomplete':
            counts['completed_episodes'] += 1
    check(counts['saved_requests'] == 100 and counts['completed_episodes'] == 20,
          'Benchmark run is not complete')
    smoke_path = HERE / 'infrastructure_smoke.json'
    check(smoke_path.exists(), 'Infrastructure smoke record missing')
    if smoke_path.exists():
        check(json.loads(smoke_path.read_text())['is_benchmark_request'] is False,
              'Infrastructure test incorrectly pooled with benchmark')
    graph_paths = sorted((HERE / 'belief_graphs').glob('*.json'))
    check(len(graph_paths) == 20, 'Expected 20 belief trace graphs')
    if graph_paths:
        graphs = [json.loads(path.read_text()) for path in graph_paths]
        graph_requests = 0
        for graph in graphs:
            sid = graph['case_id']
            ids = [n['id'] for n in graph['nodes']]
            check(len(ids) == len(set(ids)), f'{sid}: duplicate graph node ID')
            for edge in graph['edges']:
                check(edge['source'] in ids and edge['target'] in ids, f'{sid}: dangling graph edge')
                if edge['type'] == 'model_cites':
                    check(edge['support_verification'] == 'model_assertion_only',
                          f'{sid}: model assertion promoted to verified evidence')
            graph_requests += sum(n['type'] == 'model_request' for n in graph['nodes'])
        check(graph_requests == counts['saved_requests'], 'Belief graphs omit saved requests')
    result = {'status': 'pass' if not failures else 'fail',
              'checked_utc': datetime.now(timezone.utc).isoformat(), 'counts': counts,
              'failures': failures, 'local_media_checked': args.with_media,
              'scope': 'Provenance, protocol and score consistency; not independent semantic annotation.'}
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
