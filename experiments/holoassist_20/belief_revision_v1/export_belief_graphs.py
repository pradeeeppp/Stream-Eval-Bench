"""Export expressed beliefs separately from the reviewed factual evidence graphs."""
import argparse
import json

from protocol import HERE, PHASES, parse_response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jsonl', action='store_true', help='Also generate a combined JSONL copy.')
    args = parser.parse_args()
    graphs = []
    for case in json.loads((HERE / 'cases.json').read_text()):
        sid = case['case_id']
        path = HERE / 'responses' / f'{sid}.json'
        records = json.loads(path.read_text())['steps'] if path.exists() else {}
        nodes, edges = [], []
        for pid, packet in case['packets'].items():
            nodes.append({'id': f'packet:{pid}', 'type': 'evidence_packet',
                          'capture_start': packet['capture_start'], 'capture_end': packet['capture_end'],
                          'frames': packet['frames']})
        # Claim identity is capture time, not arrival time or changing model output.
        for pid, label in [('A', case['earlier_gold']), ('B', case['later_gold'])]:
            nodes.append({'id': f'claim:{pid}', 'type': 'capture_time_claim',
                          'predicate': case['predicate'], 'capture_time': case['packets'][pid]['capture_end'],
                          'provisional_evidence_label': label,
                          'independently_adjudicated': False})
        for phase, meta in PHASES.items():
            if phase not in records:
                continue
            step = records[phase]
            rid = f'request:{phase}'
            obj, exact, valid = parse_response(step['raw_response'])
            nodes.append({'id': rid, 'type': 'model_request', 'phase': phase,
                          'raw_record': f'responses/{sid}.json#/steps/{phase}',
                          'raw_response': step['raw_response'], 'exact_json': exact, 'schema_valid': valid,
                          'arrived_packets': meta['arrived']})
            for pid in meta['current']:
                edges.append({'type': 'visual_input', 'source': f'packet:{pid}', 'target': rid})
            if meta['previous']:
                edges.append({'type': 'verbatim_response_memory',
                              'source': f"request:{meta['previous']}", 'target': rid})
            for field in ('earlier', 'latest'):
                bid = f'belief:{phase}:{field}'
                target = 'A' if field == 'earlier' or 'B' not in meta['arrived'] else 'B'
                value = (obj or {}).get(field)
                citations = (obj or {}).get(field + '_evidence')
                nodes.append({'id': bid, 'type': 'expressed_model_belief', 'field': field,
                              'value': value, 'capture_time': case['packets'][target]['capture_end'],
                              'citations_valid_list': isinstance(citations, list) and
                              all(isinstance(c, str) and c in ('A', 'B') for c in citations)})
                edges += [{'type': 'generated', 'source': rid, 'target': bid},
                          {'type': 'asserts', 'source': bid, 'target': f'claim:{target}'}]
                if isinstance(citations, list):
                    for citation in citations:
                        if citation not in ('A', 'B'):
                            continue
                        edges.append({'type': 'model_cites', 'source': bid,
                                      'target': f'packet:{citation}',
                                      'packet_received': citation in meta['arrived'],
                                      'matches_requested_capture_time': citation == target,
                                      'support_verification': 'model_assertion_only'})
        graphs.append({'case_id': sid, 'graph_type': 'expressed_belief_trace',
                       'paths_relative_to': 'experiment root: directory containing cases.json',
                       'primary_qualified': case['primary_qualified'],
                       'reviewed_factual_graph': f'../online_pilot_v0/reviews/batch_v1/{sid}/evidence_graph.json',
                       'reviewed_factual_graph_sha256': case['graph_sha256'],
                       'citation_semantics': 'Model citations are assertions, not verified support edges.',
                       'nodes': nodes, 'edges': edges})
    directory = HERE / 'belief_graphs'
    directory.mkdir(exist_ok=True)
    for graph in graphs:
        (directory / f"{graph['case_id']}.json").write_text(json.dumps(graph, indent=2) + '\n')
    if args.jsonl:
        (HERE / 'belief_graphs.jsonl').write_text(''.join(json.dumps(g) + '\n' for g in graphs))
    print(f'Exported {len(graphs)} belief trace graphs.')


if __name__ == '__main__':
    main()
