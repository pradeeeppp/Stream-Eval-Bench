"""Build private reviewed graphs and readable reports from visual annotations."""
import json
import os
import struct
from pathlib import Path

from review_media import HERE, ROOT, SOURCES, TASKS, cache, digest, timestamps

# One-based entity positions: subject, visible relation, optional object.
RELATIONS = {
    'HA01': (2, 'separated_from', 1), 'HA02': (2, 'visibly_illuminated', None),
    'HA03': (1, 'visibly_seated_on', 2), 'HA04': (2, 'open_exposing', 3),
    'HA05': (3, 'inside', 1), 'HA06': (3, 'outside', 1),
    'HA07': (1, 'clear_of', 2), 'HA08': (1, 'tipped_over', 2),
    'HA09': (1, 'ringed_face_visible', None), 'HA10': (1, 'tilted', None),
    'HB01': (1, 'clear_of', 2), 'HB02': (2, 'open_exposing', 3),
    'HB03': (2, 'separated_from', 1), 'HB04': (1, 'clear_of', 2),
    'HB05': (2, 'clear_of', 1), 'HB06': (2, 'outside', 1),
    'HB07': (1, 'clear_of', 2), 'HB08': (1, 'separated_from', 2),
    'HB09': (2, 'extended_from', 1), 'HB10': (1, 'under_flow_from', 2),
}


def make_graph(source_id, annotation):
    source, task = SOURCES[source_id], TASKS[source_id]
    pts = timestamps(source_id)
    mapping = json.loads((cache(source_id) / 'packet_mapping.json').read_text())
    packet = next(p for p in mapping if p['packet_time_seconds'] == annotation['confirmed_packet'])
    qualified = annotation.get('target_verified', True)
    inspections = json.loads((cache(source_id) / 'inspections.json').read_text())
    review_material = []
    for name, record in inspections.items():
        assert record['status'] == 'visually_inspected_by_codex_2026_11_02', (source_id, name)
        sheet_width, sheet_height = struct.unpack('!II', Path(record['paths'][0]).read_bytes()[16:24])
        columns = sheet_width // record['width']
        cell_height = record['width'] * source['height'] // source['width'] + 24
        review_material.append({'name': name, 'native_indices': record['indices'],
                                'display_width': record['width'], 'status': record['status'],
                                'render_columns': columns,
                                'render_per_page': sheet_height // cell_height * columns,
                                'sheets': [{'path': str(Path(p).relative_to(ROOT)), 'sha256': digest(Path(p))}
                                           for p in record['paths']]})
    entities = [{'id': f'object_{i}', 'description': value}
                for i, value in enumerate(annotation['entities'], 1)]
    nodes, edges = [], []
    positive_id = None
    for j, (index, role, description) in enumerate(annotation['observations']):
        oid, cid = f'observation_{j}', f'claim_{j}'
        nodes.append({'id': oid, 'type': 'observation', 'role': role,
                      'frame_index_zero_based': index, 'source_pts_seconds': pts[index],
                      'path': f'full_review/batch_v1/{source_id}/anchors/{index:06d}.jpg',
                      'description': description,
                      'available_by_confirmed_packet': pts[index] <= packet['source_pts_seconds']})
        nodes.append({'id': cid, 'type': 'state_claim', 'text': description,
                      'evidence_ids': [oid], 'certainty': 'single_assistant_visual_assessment',
                      'scope': 'this_observation_only'})
        edges.append({'source': oid, 'relation': 'supports', 'target': cid})
        if role == 'positive':
            subject, predicate, obj = RELATIONS[source_id]
            nodes[-1]['relation'] = {'subject': f'object_{subject}', 'predicate': predicate,
                                     'object': f'object_{obj}' if obj else None}
            positive_id = oid
            edges.append({'source': cid, 'relation': 'outcome_evidence_for', 'target': 'event_1'})
        elif role == 'pre':
            edges.append({'source': cid, 'relation': 'prior_state_evidence_for', 'target': 'event_1'})
        elif role == 'transition':
            edges.append({'source': oid, 'relation': 'localizes_or_limits', 'target': 'event_1'})
        elif role == 'corroboration':
            edges.append({'source': oid, 'relation': 'corroborates', 'target': 'event_1',
                          'used_for_initial_decision': False})
        elif role == 'later_state':
            edges.append({'source': cid, 'relation': 'subsequent_state_in_episode', 'target': 'event_1',
                          'retracts_historical_occurrence': False})
        elif role == 'distractor':
            edges.append({'source': oid, 'relation': 'insufficient_alone_to_trigger', 'target': 'alert_1'})
        else:
            edges.append({'source': oid, 'relation': 'context_for', 'target': 'event_1',
                          'same_occurrence_link_certified': False})
    positive = next(n for n in nodes if n['id'] == positive_id)
    # A native anchor after the delivered image would introduce future evidence.
    assert positive['source_pts_seconds'] <= packet['source_pts_seconds'], source_id
    nodes.append({'id': 'event_1', 'type': 'event', 'occurrence_id': f'{source_id}:reviewed_occurrence_1',
                  'event_class': annotation['event'], 'positive_evidence_ids': [positive_id],
                  'entity_ids': [f'object_{i}' for i in RELATIONS[source_id][::2] if i is not None],
                  'conservative_positive_source_pts_seconds': positive['source_pts_seconds'],
                  'physical_onset_seconds': None, 'first_occurrence_certified': False,
                  'first_detectable_frame_certified': False,
                  'identity_basis': 'Local visual sequence; exact inspected indices are in review.material. '
                                    'No replay or cross-event identity claim is inferred from temporal order.',
                  'supports_original_task': 'provisional' if qualified else 'requires_adjudication'})
    nodes.append({'id': 'delivered_positive', 'type': 'stream_observation', **packet,
                  'visual_assessment': annotation['confirmed_packet_interpretation'],
                  'is_earliest_qualifying_packet_certified': False})
    nodes.append({'id': 'alert_1', 'type': 'decision',
                  'status': 'provisional_target_supported' if qualified else 'blocked_on_task_definition',
                  'policy': annotation['instruction'], 'evidence_dependencies': ['delivered_positive'],
                  'confirmed_packet_time_seconds': packet['packet_time_seconds'],
                  'source_capture_boundary_seconds': packet['source_pts_seconds'],
                  'wall_clock_decision_time': None,
                  'legacy_deadline_packet_seconds': task['deadline_seconds'],
                  'deadline_basis': 'Inherited pilot scoring allowance; not video-derived or deployment-validated.',
                  'scorer_migration_applied': False})
    for secondary in annotation.get('secondary_events', []):
        evidence_ids = [n['id'] for n in nodes if n['type'] == 'observation'
                        and n['frame_index_zero_based'] in secondary['evidence_indices']]
        require_observed = secondary['qualification'] == 'observed_distinct_event'
        nodes.append({'id': secondary['id'], 'type': 'event' if require_observed else 'event_candidate',
                      'event_class': secondary['event_class'],
                      'occurrence_id': f"{source_id}:{secondary['id']}",
                      'entity_ids': [f'object_{i}' for i in secondary['entity_positions']],
                      'evidence_ids': evidence_ids, 'physical_onset_seconds': None,
                      'qualification': secondary['qualification'], 'note': secondary['note']})
        edges += [{'source': oid, 'relation': 'supports_separate_event' if require_observed else 'suggests_candidate',
                   'target': secondary['id']} for oid in evidence_ids]
        edges.append({'source': secondary['id'], 'relation': 'distinct_from' if require_observed
                      else 'must_not_be_automatically_merged_with', 'target': 'event_1'})
    edges += [{'source': 'delivered_positive', 'relation': 'supports_reviewed_event', 'target': 'event_1'},
              {'source': 'delivered_positive', 'relation': 'available_evidence_for', 'target': 'alert_1'},
              {'source': 'event_1', 'relation': 'triggers_if_target_definition_accepted', 'target': 'alert_1'}]
    prior_review = None
    if source_id == 'HA01':
        prior_path = HERE.parent / 'stream_alert_01' / 'evidence_graph.json'
        prior = json.loads(prior_path.read_text())
        prior_review = {'path': str(prior_path.relative_to(ROOT)), 'sha256': digest(prior_path),
                        'native_indices': [n['frame_index_zero_based'] for n in prior['nodes']
                                           if n['type'] == 'observation']}
    return {'schema_version': 'reviewed_evidence_graph_v2', 'task_id': task['task_id'],
            'source_id': source_id, 'original_instruction': task['instruction'],
            'source': {'session_id': source['session_id'], 'sha256': source['sha256'],
                       'video_path': source['local_path'], 'paths_relative_to': 'experiments/holoassist_20',
                       'native_frame_count': len(pts), 'frame_index_convention': 'zero-based presentation order'},
            'review': {'date': '2026-11-02', 'reviewer': 'Codex',
                       'status': 'single_assistant_review_pending_independent_adjudication',
                       'material': review_material, 'prior_review': prior_review, 'audio_reviewed': False,
                       'full_native_rate_review': False, 'original_gold_modified': False,
                       'findings': annotation['findings'], 'flags': annotation['flags'],
                       'historical_evidence_revision_qualification': 'not_established',
                       'limitations': ['Conservative anchors are not exact physical onset.',
                                       'Sparse whole-clip overview cannot certify first occurrence or event counts.',
                                       'No intent, safety, mechanical security or task-success claim is assigned.']},
            'entities': entities, 'nodes': nodes, 'edges': edges,
            'timing': {'packet_labels': 'FFmpeg 1 FPS output grid, not source capture PTS',
                       'mapping_verification': 'Selected native and fps=1 scaled-frame MD5s match; '
                                               'selected existing JPEGs reproduce byte-for-byte.',
                       'verified_packets': mapping},
            'task_proposal': {'instruction': annotation['instruction'],
                              'qualification': 'provisional' if qualified else 'requires_adjudication',
                              'independent_review_required': True, 'legacy_scorer_consumes_this_graph': False}}


def report(graph, folder):
    observations = [n for n in graph['nodes'] if n['type'] == 'observation']
    event = next(n for n in graph['nodes'] if n['type'] == 'event')
    decision = next(n for n in graph['nodes'] if n['type'] == 'decision')
    positive = next(n for n in observations if n['role'] == 'positive')
    before = next(n for n in observations if n['role'] == 'pre')
    text = [f"# {graph['source_id']} — {event['event_class']}", '',
            f"Task: `{graph['task_id']}`. Original instruction: {graph['original_instruction']}", '',
            '**Single-assistant review; independent adjudication pending.**', '',
            graph['review']['findings'], '', f"Original-task qualification: **{graph['task_proposal']['qualification']}**.", '',
            '## Evidence anchors', '', '| Native frame | Source PTS (s) | Role | Visual evidence |',
            '|---:|---:|---|---|']
    for n in observations:
        path = os.path.relpath(ROOT / n['path'], folder)
        text.append(f"| [{n['frame_index_zero_based']}]({path}) | {n['source_pts_seconds']:.6f} | {n['role']} | {n['description']} |")
    text += ['', '## Evidence dependencies', '', '```mermaid', 'flowchart TD',
             f'    A["Prior-state evidence · {before["source_pts_seconds"]:.3f} s"] -->|constrains| E["Reviewed event occurrence"]',
             f'    B["Positive native anchor · {positive["source_pts_seconds"]:.3f} s"] -->|supports| E',
             f'    P["Reviewed supplied packet · label {decision["confirmed_packet_time_seconds"]} s"] -->|supports| E',
             '    P -->|available evidence| D["Alert policy; original-task qualification checked separately"]',
             '    E -->|triggers if task definition accepted| D', '```', '',
             'The graph JSON carries additional transitions, corroboration, distractors and later states.',
             'Later evidence is not an initial-alert dependency. Temporal edges do not imply causation.', '',
             '## Timing and task proposal', '',
             f"The inspected supplied packet labeled **{decision['confirmed_packet_time_seconds']} s** comes from source PTS "
             f"**{decision['source_capture_boundary_seconds']:.6f} s**. It is a reviewed positive packet, not a certified earliest positive.", '',
             f"The legacy deadline remains **{decision['legacy_deadline_packet_seconds']} packet seconds**, an inherited policy choice.", '',
             graph['task_proposal']['instruction'], '',
             'No gold/scorer migration has been applied. Exact physical onset, first occurrence and native-rate full-clip coverage remain unverified.', '',
             '## Review coverage', '',
             '| Inspection | Native frames inspected | Display width |', '|---|---:|---:|']
    for material in graph['review']['material']:
        text.append(f"| {material['name']} | {len(material['native_indices'])} | {material['display_width']} |")
    text += ['', 'The complete list of indices and sheet hashes is stored in `evidence_graph.json`.',
             'Extracted media remain under ignored `full_review/`; rehydrate with the batch verification scripts.', '',
             'Flags: ' + ', '.join(f'`{f}`' for f in graph['review']['flags']) + '.', '']
    return '\n'.join(text)


def main():
    annotations = json.loads((HERE / 'annotations.json').read_text())
    assert set(annotations) == set(SOURCES)
    graphs, rows = [], []
    for source_id, annotation in annotations.items():
        graph = make_graph(source_id, annotation)
        folder = HERE / source_id
        folder.mkdir(exist_ok=True)
        (folder / 'evidence_graph.json').write_text(json.dumps(graph, indent=2) + '\n')
        (folder / 'README.md').write_text(report(graph, folder))
        graphs.append(graph)
        d = next(n for n in graph['nodes'] if n['type'] == 'decision')
        rows.append({'source_id': source_id, 'task_id': graph['task_id'],
                     'qualification': graph['task_proposal']['qualification'],
                     'reviewed_packet_seconds': d['confirmed_packet_time_seconds'],
                     'legacy_positive_packet_seconds': TASKS[source_id]['first_positive_sample_seconds'],
                     'source_pts_seconds': d['source_capture_boundary_seconds'],
                     'findings': graph['review']['findings']})
    (HERE / 'evidence_graphs.reviewed.jsonl').write_text(''.join(json.dumps(g) + '\n' for g in graphs))
    (HERE / 'review_index.json').write_text(json.dumps(rows, indent=2) + '\n')
    status = ['# All-video evidence-graph review status', '',
              'Plan executed for **20/20 videos**: whole-clip sampled overview, candidate-window inspection, '
              'local native-frame review, delivered-frame review, typed graph and per-video report.', '',
              '**These are private single-assistant proposals, not independently adjudicated gold.** '
              'The legacy scorer and labels are unchanged.', '',
              '| Video / review | Original-task qualification | Reviewed positive packet | Legacy positive packet | Findings |',
              '|---|---|---:|---:|---|']
    for row in rows:
        status.append(f"| [{row['source_id']}]({row['source_id']}/README.md) | {row['qualification']} | "
                      f"{row['reviewed_packet_seconds']} | {row['legacy_positive_packet_seconds']} | {row['findings']} |")
    status += ['', 'Packet values above are output-grid labels. Actual source PTS and frame indices are in each report/graph.',
               'A reviewed positive earlier than the legacy positive is a demonstrated earlier evidence point, '
               'not proof of the exact onset or the earliest qualifying observation.', '',
               'Three original task definitions require adjudication: HA05 (which hardware bin), HA09 '
               '(which face is the underside, and whether it was already exposed), HA10 (whole-cart '
               'motion versus basket/frame relative motion). HB01 also has a legacy pre-event checkpoint '
               'after the observed removal; do not use that checkpoint to judge early alerts without correction.', '',
               '## Remaining research validation', '',
               '- Independent annotation, disagreement measurement and adjudication.',
               '- Exhaustive earlier-occurrence review where first-occurrence scoring is required.',
               '- Resolve the three task definitions and review all deadline policies.',
               '- Implement a versioned scorer/protocol migration before using these proposals as new gold.',
               '- No retrospective evidence-revision qualification or model-performance claim follows from this review.', '']
    (HERE / 'STATUS.md').write_text('\n'.join(status))
    print(f'Built {len(graphs)} reviewed graphs and per-video reports.')


if __name__ == '__main__':
    main()
