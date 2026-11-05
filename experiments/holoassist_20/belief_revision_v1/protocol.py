"""Prompt and metric contract shared by execution, tests and reporting."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PHASES = {
    'joint': {'current': ['A', 'B'], 'arrived': ['A', 'B'], 'previous': None},
    'chronological_0': {'current': ['A'], 'arrived': ['A'], 'previous': None},
    'chronological_1': {'current': ['B'], 'arrived': ['A', 'B'], 'previous': 'chronological_0'},
    'delayed_0': {'current': ['B'], 'arrived': ['B'], 'previous': None},
    'delayed_1': {'current': ['A'], 'arrived': ['B', 'A'], 'previous': 'delayed_0'},
}
CONFIG = {'model_id': 'Qwen/Qwen2.5-VL-3B-Instruct', 'seed': 20261104,
          'dtype': 'float16', 'attention': 'sdpa', 'max_new_tokens': 128,
          'do_sample': False, 'num_beams': 1, 'max_pixels_per_frame': 448 * 252,
          'min_pixels_per_frame': 56 * 56, 'trials_per_condition': 1,
          'visual_memory': 'current packet only; previous raw output verbatim',
          'input_mode': 'two four-frame video tensors; actual capture times in prompt',
          'phases': list(PHASES)}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_state(case, phase):
    if not case['primary_qualified']:
        return None
    arrived = PHASES[phase]['arrived']
    return {'earlier': case['earlier_gold'] if 'A' in arrived else 'unknown',
            'latest': case['later_gold'] if 'B' in arrived else case['earlier_gold']}


def prompt_for(case, phase, previous_response=None):
    meta = PHASES[phase]
    latest_packet = 'B' if 'B' in meta['arrived'] else 'A'
    boundary = case['packets'][latest_packet]['capture_end']
    lines = [
        'Evaluate the following visible condition at the requested capture times.',
        f"Condition: {case['predicate']}.",
        f"earlier: did this condition hold at capture time {case['earlier_target_seconds']:.6f} seconds?",
        f'latest: did this condition hold at the latest capture time received, {boundary:.6f} seconds?',
        'Answer yes, no, or unknown for each field. Use unknown when the evidence for that capture time '
        'has not been received or does not settle the condition. Do not infer an earlier state from a later state.',
        'A packet arriving later can have an older capture time. Preserve supported facts about other capture times.',
        f"Packet IDs received so far, in arrival order: {json.dumps(meta['arrived'])}.",
        f'Latest capture-time boundary received: {boundary:.6f} seconds.',
    ]
    for packet_id in meta['current']:
        packet = case['packets'][packet_id]
        times = [f['source_pts_seconds'] for f in packet['frames']]
        lines.append(f'Attached video packet {packet_id}: frame capture times '
                     + ', '.join(f'{t:.6f}' for t in times) + ' seconds, in chronological order.')
    if previous_response is not None:
        lines += ['Previous model response, verbatim (your external memory):', previous_response]
    else:
        lines.append('No previous model response is available in this condition.')
    lines += [
        'Return only one JSON object with exactly these keys: earlier, latest, earlier_evidence, latest_evidence.',
        'earlier and latest must each be yes, no, or unknown. The two evidence values must be lists of '
        'supporting packet IDs, using only A or B. Cite the packet for the requested capture time. '
        'Use an empty list when no supporting packet was received. Do not cite future packets.',
    ]
    return '\n'.join(lines)


def parse_response(raw):
    try:
        obj = json.loads(raw.strip())
        exact = True
    except (ValueError, AttributeError):
        exact = False
        try:
            start = raw.index('{')
            obj, _ = json.JSONDecoder().raw_decode(raw[start:])
        except (ValueError, AttributeError, TypeError):
            return None, False, False
    if not isinstance(obj, dict):
        return None, False, False
    valid = set(obj) == {'earlier', 'latest', 'earlier_evidence', 'latest_evidence'}
    valid = valid and all(obj.get(k) in ('yes', 'no', 'unknown') for k in ('earlier', 'latest'))
    valid = valid and all(isinstance(obj.get(k), list) and
                          all(v in ('A', 'B') for v in obj[k]) and len(obj[k]) == len(set(obj[k]))
                          for k in ('earlier_evidence', 'latest_evidence'))
    return obj, exact, bool(valid)


def score_step(case, phase, raw):
    obj, exact, valid = parse_response(raw)
    expected = expected_state(case, phase)
    out = {'parsed': obj, 'exact_json': exact, 'schema_valid': valid,
           'expected_state': expected, 'state_accuracy': None, 'state_perfect': None,
           'known_state_accuracy': None, 'known_fields': 0, 'known_binding_accuracy': None}
    if expected is None:
        return out
    obj = obj or {}
    matches = {k: obj.get(k) == v for k, v in expected.items()}
    out.update(field_matches=matches, state_accuracy=sum(matches.values()) / 2,
               state_perfect=all(matches.values()))
    arrived = set(PHASES[phase]['arrived'])
    known = [k for k, v in expected.items() if v != 'unknown']
    binding, future, targeting = {}, {}, {}
    for key in ('earlier', 'latest'):
        citations = obj.get(key + '_evidence')
        correct_packet = 'A' if key == 'earlier' or 'B' not in arrived else 'B'
        if not isinstance(citations, list) or not all(isinstance(c, str) for c in citations):
            future[key], targeting[key], binding[key] = None, False, False
            continue
        refs = set(citations)
        future[key] = bool(refs - arrived)
        targeting[key] = refs <= ({correct_packet} & arrived)
        binding[key] = matches[key] and refs == {correct_packet} and not future[key]
    out.update(known_fields=len(known),
               known_state_accuracy=sum(matches[k] for k in known) / len(known) if known else None,
               known_binding_accuracy=sum(binding[k] for k in known) / len(known) if known else None,
               evidence_targeting=targeting, future_packet_citation=future)
    return out


def score_episode(case, records):
    if any(p not in records or records[p].get('status') != 'ok' for p in PHASES):
        return {'status': 'incomplete', 'missing_phases': [p for p in PHASES if p not in records or records[p].get('status') != 'ok']}
    steps = {p: score_step(case, p, records[p]['raw_response']) for p in PHASES}
    if not case['primary_qualified']:
        return {'status': 'diagnostic_only', 'steps': steps, 'metrics': None}
    parsed = {p: s['parsed'] or {} for p, s in steps.items()}
    d0, d1 = parsed['delayed_0'], parsed['delayed_1']
    c0, c1 = parsed['chronological_0'], parsed['chronological_1']
    historical_known = case['earlier_gold'] != 'unknown'
    preserve_latest_applicable = d0.get('latest') == case['later_gold']
    preserve_past_applicable = historical_known and c0.get('earlier') == case['earlier_gold']
    metrics = {
        'uncertainty_preserved_before_earlier_evidence': d0.get('earlier') == 'unknown',
        'unsupported_earlier_commitment': d0.get('earlier') in ('yes', 'no'),
        'historical_final_factual_correct': d1.get('earlier') == case['earlier_gold'] if historical_known else None,
        'historical_epistemic_correct': d1.get('earlier') == case['earlier_gold'],
        'clean_historical_update_success': (d0.get('earlier') == 'unknown' and d1.get('earlier') == case['earlier_gold'])
                                            if case['clean_revision_opportunity'] else None,
        'recent_preservation_applicable': preserve_latest_applicable,
        'recent_fact_preserved': d1.get('latest') == case['later_gold'] if preserve_latest_applicable else None,
        'historical_preservation_applicable': preserve_past_applicable,
        'past_fact_preserved_chronological': c1.get('earlier') == case['earlier_gold'] if preserve_past_applicable else None,
        'joint_final_perfect': steps['joint']['state_perfect'],
        'chronological_final_perfect': steps['chronological_1']['state_perfect'],
        'delayed_final_perfect': steps['delayed_1']['state_perfect'],
        'joint_correct_both_sequential_fail': steps['joint']['state_perfect'] and not steps['chronological_1']['state_perfect'] and not steps['delayed_1']['state_perfect'],
        'joint_and_chronological_correct_delayed_fails': steps['joint']['state_perfect'] and steps['chronological_1']['state_perfect'] and not steps['delayed_1']['state_perfect'],
    }
    return {'status': 'complete', 'steps': steps, 'metrics': metrics}
