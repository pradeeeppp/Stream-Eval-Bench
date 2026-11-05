"""Validate reviewed graph structure, causal availability and local evidence.

This verifies provenance and consistency, not the truth of visual annotations.
"""
import json
import subprocess
import tempfile
from pathlib import Path

from review_media import HERE, PILOT, ROOT, SOURCES, TASKS, digest, timestamps
from verify_timing import selection


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_graph(graph):
    nodes = {n['id']: n for n in graph['nodes']}
    require(len(nodes) == len(graph['nodes']), 'Duplicate node ID')
    entities = {e['id'] for e in graph['entities']}
    require(len(entities) == len(graph['entities']), 'Duplicate entity ID')
    for edge in graph['edges']:
        require(edge['source'] in nodes and edge['target'] in nodes, 'Dangling edge')
        require(bool(edge['relation']), 'Missing edge relation')
        if edge['relation'] == 'corroborates':
            require(edge['used_for_initial_decision'] is False, 'Corroboration used retrospectively for earlier decision')
    observations = [n for n in nodes.values() if n['type'] == 'observation']
    inspected = {i for m in graph['review']['material'] for i in m['native_indices']}
    prior = graph['review'].get('prior_review')
    if prior:
        inspected.update(prior['native_indices'])
    for node in observations:
        require(node['frame_index_zero_based'] in inspected, 'Observation was not in inspected material')
        require(node['source_pts_seconds'] >= 0, 'Negative source PTS')
    for node in nodes.values():
        if node['type'] in ('event', 'event_candidate'):
            evidence_ids = node.get('positive_evidence_ids', node.get('evidence_ids', []))
            require(bool(evidence_ids), 'Event lacks evidence')
            require(all(i in nodes and nodes[i]['type'] == 'observation' for i in evidence_ids), 'Invalid event evidence')
            require(all(i in entities for i in node['entity_ids']), 'Invalid event entity')
        if node['type'] == 'state_claim':
            require(bool(node['evidence_ids']), 'Unsupported claim')
            require(all(i in nodes and nodes[i]['type'] == 'observation' for i in node['evidence_ids']), 'Invalid claim evidence')
            if 'relation' in node:
                r = node['relation']
                require(r['subject'] in entities and (r['object'] is None or r['object'] in entities), 'Invalid claim entity')
    event = nodes['event_1']
    decision = nodes['alert_1']
    delivered = nodes['delivered_positive']
    require(bool(event['positive_evidence_ids']), 'No positive event evidence')
    require(all(i in entities for i in event['entity_ids']), 'Invalid event entity')
    require(event['physical_onset_seconds'] is None, 'Unadjudicated physical onset assigned')
    require(event['first_occurrence_certified'] is False, 'Sparse review cannot certify first occurrence')
    require(decision['evidence_dependencies'] == ['delivered_positive'], 'Decision must depend on supplied evidence')
    require(delivered['source_pts_seconds'] <= decision['source_capture_boundary_seconds'], 'Future delivered evidence')
    require(delivered['packet_time_seconds'] <= decision['confirmed_packet_time_seconds'], 'Future packet')
    for evidence_id in event['positive_evidence_ids']:
        evidence = nodes[evidence_id]
        require(evidence['type'] == 'observation', 'Invalid positive anchor')
        require(evidence['source_pts_seconds'] <= decision['source_capture_boundary_seconds'], 'Future native anchor')
    for evidence in observations:
        require(evidence['available_by_confirmed_packet'] ==
                (evidence['source_pts_seconds'] <= delivered['source_pts_seconds']), 'Wrong availability annotation')
    if graph['task_proposal']['qualification'] == 'requires_adjudication':
        require(decision['status'] == 'blocked_on_task_definition', 'Unresolved task can trigger alert')
    require(decision['scorer_migration_applied'] is False, 'Undocumented scoring migration')
    return observations


def extract_anchors(graph, observations):
    source_id = graph['source_id']
    indices = sorted({n['frame_index_zero_based'] for n in observations})
    with tempfile.TemporaryDirectory(prefix='stream_review_anchors_') as tmp:
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i',
                        str(ROOT / graph['source']['video_path']), '-map', '0:v:0', '-an',
                        '-vf', f'select={selection(indices)}', '-fps_mode', 'passthrough',
                        '-q:v', '2', '-start_number', '0', '-y', str(Path(tmp) / '%06d.jpg')], check=True)
        require(len(list(Path(tmp).glob('*.jpg'))) == len(indices), f'Anchor count: {source_id}')
        for j, index in enumerate(indices):
            target = ROOT / next(n['path'] for n in observations if n['frame_index_zero_based'] == index)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((Path(tmp) / f'{j:06d}.jpg').read_bytes())


def main():
    expected_baseline = json.loads((HERE / 'baseline_hashes.json').read_text())
    for name, sha in expected_baseline.items():
        require(digest(PILOT / name) == sha, f'Baseline changed: {name}')
    graphs = [json.loads(line) for line in (HERE / 'evidence_graphs.reviewed.jsonl').read_text().splitlines()]
    require(len(graphs) == 20, 'Expected 20 graphs')
    require({g['source_id'] for g in graphs} == set(SOURCES), 'Incomplete source coverage')
    require({g['task_id'] for g in graphs} == {t['task_id'] for t in TASKS.values()}, 'Incomplete task coverage')
    require(len({g['task_id'] for g in graphs}) == len(graphs), 'Duplicate task graph')
    rows = []
    for graph in graphs:
        source_id = graph['source_id']
        require(graph == json.loads((HERE / source_id / 'evidence_graph.json').read_text()), 'Combined/per-video mismatch')
        pts = timestamps(source_id)  # Also verifies the pinned MP4 SHA-256.
        require(graph['source']['sha256'] == SOURCES[source_id]['sha256'], 'Manifest hash mismatch')
        require(len(pts) == graph['source']['native_frame_count'], 'Native-frame count mismatch')
        observations = validate_graph(graph)
        for node in observations:
            require(abs(pts[node['frame_index_zero_based']] - node['source_pts_seconds']) < 1e-6, 'Anchor PTS mismatch')
        for material in graph['review']['material']:
            for sheet in material['sheets']:
                require(digest(ROOT / sheet['path']) == sheet['sha256'], 'Inspected sheet changed')
        prior = graph['review'].get('prior_review')
        if prior:
            require(digest(ROOT / prior['path']) == prior['sha256'], 'Prior review changed')
        for packet in graph['timing']['verified_packets']:
            require(abs(pts[packet['native_frame_index']] - packet['source_pts_seconds']) < 1e-6, 'Packet PTS mismatch')
            require(digest(ROOT / packet['stream_path']) == packet['stream_jpeg_sha256'], 'Supplied JPEG changed')
        extract_anchors(graph, observations)
        row = {'source_id': source_id, 'task_id': graph['task_id'], 'status': 'provenance_and_consistency_pass',
               'n_observations': len(observations), 'n_verified_packets': len(graph['timing']['verified_packets']),
               'n_inspected_unique_frames': len({i for m in graph['review']['material'] for i in m['native_indices']}),
               'anchor_sha256': {n['path']: digest(ROOT / n['path']) for n in observations}}
        rows.append(row)
        print(f"{source_id}: PASS ({len(observations)} anchors)", flush=True)
    report = {'status': 'pass', 'n_videos': len(rows),
              'n_observations': sum(r['n_observations'] for r in rows),
              'n_verified_packet_mappings': sum(r['n_verified_packets'] for r in rows),
              'n_inspected_unique_frames': sum(r['n_inspected_unique_frames'] for r in rows),
              'baseline_files_unchanged': expected_baseline,
              'visual_truth_independently_validated': False, 'per_video': rows}
    (HERE / 'validation_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('per_video', 'baseline_files_unchanged')}))


if __name__ == '__main__':
    main()
