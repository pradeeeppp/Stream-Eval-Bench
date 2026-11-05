"""Classify saved outputs without changing the archived evaluation.

All partitions are exclusive within their declared unit. Different partitions
describe different questions; their counts must never be added together.
Only the Python standard library is required.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
sys.path.insert(0, str(RUN))
from protocol import PHASES, expected_state, parse_response, prompt_for, score_episode

VERSION = '1.0.0'
VALUES = {'yes', 'no', 'unknown'}
FINAL_PHASES = ['joint', 'chronological_1', 'delayed_1']
TRANSITION_ROLES = {
    'historical_arrival': ('delayed_0', 'delayed_1', 'earlier'),
    'historical_retention': ('chronological_0', 'chronological_1', 'earlier'),
    'recent_retention': ('delayed_0', 'delayed_1', 'latest'),
}
CATALOG = {
    'request_format': {
        'R00': ('Valid exact JSON', 'One JSON object satisfying the frozen four-key schema.'),
        'R10': ('Unrecoverable JSON', 'No recoverable JSON object; excludes valid JSON with the wrong schema.'),
        'R11': ('Schema violation', 'Recoverable JSON, but wrong type, keys, values, IDs or duplicate citation IDs.'),
        'R12': ('Extra output around JSON', 'A valid schema object can be extracted, but the complete response is not that JSON object.'),
        'R20': ('Missing result', 'No saved step. Not a semantic model error.'),
        'R21': ('Infrastructure failure', 'Saved step reports a non-ok execution status. Not a semantic model error.'),
    },
    'state': {
        'S00': ('Correct known value', 'Expected yes/no and the output matches.'),
        'S01': ('Correct abstention before evidence', 'Target packet not received; expected and output are unknown.'),
        'S02': ('Correct abstention on unsettled evidence', 'Target packet received, provisional label remains unknown, output unknown.'),
        'S10': ('Commitment before target evidence', 'Output yes/no while target packet has not been received.'),
        'S11': ('Commitment on unsettled evidence', 'Output yes/no after the target packet arrived, although its provisional label remains unknown.'),
        'S12': ('Abstention on a provisionally known state', 'Output unknown where the frozen label is yes/no. Does not establish a perception failure.'),
        'S13': ('Opposite binary value', 'Expected yes/no, output is the other binary value. Does not identify the internal cause.'),
    },
    'citation': {
        'E00': ('Requested packet named', 'Exactly the received packet for the requested capture time. Does not verify visual support or the state value.'),
        'E01': ('Empty citation permitted', 'No citation and no known-state support requirement: unseen target or an unresolved label.'),
        'E10': ('Required citation missing', 'Known expected value and received target packet, but an empty evidence list. Independent of value correctness.'),
        'E11': ('Wrong received capture-time packet', 'All references received, but list is not exactly the requested packet; includes both A and B.'),
        'E12': ('Unreceived packet named', 'At least one reference not received; takes precedence over wrong-time citation.'),
    },
    'same_claim_consistency': {
        'K00': ('Same answer', 'Both fields target the same predicate and capture time and have equal values; may still both be wrong.'),
        'K10': ('Binary contradiction', 'Same claim gets opposing yes/no answers.'),
        'K11': ('Certainty disagreement', 'Same claim gets unknown in one field and yes/no in the other. Not a yes/no contradiction.'),
    },
    'transition': {
        'T00': ('Correct new-evidence value update', 'Expected unknown becomes known, prior output correctly unknown, final output matches the new label. No grounding claim.'),
        'T01': ('Correct value maintained', 'Expected value unchanged and both outputs match; includes justified unknown remaining unknown.'),
        'T02': ('Recovery after an incorrect prior', 'Expected value unchanged; incorrect prior becomes correct. Does not prove retrieval of earlier visual evidence.'),
        'T10': ('Missed resolution after evidence', 'Expected unknown becomes known, correctly unknown prior stays unknown.'),
        'T11': ('Wrong resolution after evidence', 'Expected unknown becomes known, correctly unknown prior resolves to the wrong binary value.'),
        'T12': ('Appropriate uncertainty lost', 'Expected unknown unchanged; prior correctly unknown becomes binary.'),
        'T13': ('Known value withdrawn', 'Expected yes/no unchanged; initially correct value becomes unknown.'),
        'T14': ('Known value inverted', 'Expected yes/no unchanged; initially correct value becomes the other binary value.'),
        'T15': ('Prior error not repaired', 'Expected value unchanged; both prior and final outputs wrong. Excludes loss of a correct prior.'),
        'T16': ('Update starts from an incorrect prior', 'Expected value changes but the prior was already wrong; not a clean update trial. Final correctness is retained separately.'),
    },
}
ERROR_CODES = {'S10', 'S11', 'S12', 'S13'}
# Curated from the reviewed graph's original_instruction/task_proposal, not
# inferred from model behavior. Missing mappings must be adjudicated manually.
DATA_BLOCKERS = {'HA05': 'D01', 'HA09': 'D01', 'HA10': 'D04'}


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def target_packet(phase, field):
    return 'A' if field == 'earlier' or 'B' not in PHASES[phase]['arrived'] else 'B'


def response_format(step):
    if step is None:
        return 'R20', None
    if step.get('status') != 'ok':
        return 'R21', None
    raw = step.get('raw_response', '')
    obj, exact, valid = parse_response(raw)
    try:
        json.loads(raw)
        syntactic_json = True
    except (ValueError, TypeError):
        syntactic_json = False
    if valid:
        return ('R00' if exact else 'R12'), obj
    if obj is not None or syntactic_json:
        return 'R11', None
    return 'R10', None


def state_code(predicted, expected, target_received):
    if predicted not in VALUES or expected not in VALUES:
        raise ValueError('State classification requires schema-valid values and a qualified label.')
    if not target_received and expected != 'unknown':
        raise ValueError('A known expected state cannot require an unreceived target packet.')
    if expected == 'unknown':
        if target_received:
            return 'S02' if predicted == 'unknown' else 'S11'
        return 'S01' if predicted == 'unknown' else 'S10'
    if predicted == expected:
        return 'S00'
    return 'S12' if predicted == 'unknown' else 'S13'


def citation_code(refs, target, arrived, expected):
    if not isinstance(refs, list) or len(refs) != len(set(refs)) or any(r not in ('A', 'B') for r in refs):
        raise ValueError('Malformed citations belong to request schema failure, not this partition.')
    received, citations = set(arrived), set(refs)
    if citations - received:
        return 'E12'
    if not citations:
        return 'E10' if target in received and expected in ('yes', 'no') else 'E01'
    return 'E00' if citations == {target} else 'E11'


def consistency_code(first, second):
    if first not in VALUES or second not in VALUES:
        raise ValueError('Consistency requires schema-valid values.')
    if first == second:
        return 'K00'
    return 'K11' if 'unknown' in (first, second) else 'K10'


def transition_code(before, after, expected_before, expected_after):
    if any(value not in VALUES for value in (before, after, expected_before, expected_after)):
        raise ValueError('Transitions require valid values and qualified labels.')
    if expected_before != expected_after:
        if expected_before != 'unknown' or expected_after == 'unknown':
            raise ValueError('This protocol resolves unknown to known; changing gold is not event revision.')
        if before != expected_before:
            return 'T16'
        if after == expected_after:
            return 'T00'
        return 'T10' if after == 'unknown' else 'T11'
    if before != expected_before:
        return 'T02' if after == expected_after else 'T15'
    if after == expected_after:
        return 'T01'
    if expected_after == 'unknown':
        return 'T12'
    return 'T13' if after == 'unknown' else 'T14'


def classify_case(case, record):
    sid = case['case_id']
    requests, fields, transitions = [], [], []
    parsed = {}
    for phase, meta in PHASES.items():
        step = record.get('steps', {}).get(phase)
        code, obj = response_format(step)
        parsed[phase] = obj
        eligible = case['primary_qualified'] and obj is not None
        disposition = ('ungraded_target' if not case['primary_qualified'] else
                       'blocked_response' if obj is None else 'qualified')
        expected = expected_state(case, phase)
        same_target = target_packet(phase, 'earlier') == target_packet(phase, 'latest')
        consistency = consistency_code(obj['earlier'], obj['latest']) if eligible and same_target else None
        requests.append({'id': f'{sid}/{phase}', 'case_id': sid, 'phase': phase,
                         'format_code': code, 'semantic_disposition': disposition,
                         'same_claim_consistency_code': consistency,
                         'source': f'responses/{sid}.json#/steps/{phase}',
                         'input_packets': meta['current'], 'arrived_packets': meta['arrived']})
        for field in ('earlier', 'latest'):
            packet = target_packet(phase, field)
            received = packet in meta['arrived']
            prediction = obj[field] if obj else None
            gold = expected[field] if expected else None
            state = state_code(prediction, gold, received) if eligible else None
            citation = citation_code(obj[field + '_evidence'], packet, meta['arrived'], gold) if eligible else None
            fields.append({'id': f'{sid}/{phase}/{field}', 'case_id': sid, 'phase': phase, 'field': field,
                           'claim_id': f'{sid}@{packet}',
                           'capture_time': case['packets'][packet]['capture_end'],
                           'target_packet': packet, 'target_received': received,
                           'current_visual_contains_target': packet in meta['current'],
                           'predicted': prediction, 'expected': gold,
                           'citation_ids': obj[field + '_evidence'] if obj else None,
                           'disposition': disposition, 'state_code': state, 'citation_code': citation,
                           'state_correct': prediction == gold if eligible else None,
                           'known_value_and_packet_correct': state == 'S00' and citation == 'E00'
                                                            if eligible and gold != 'unknown' else None,
                           'source': f'responses/{sid}.json#/steps/{phase}'})
    for role, (before_phase, after_phase, field) in TRANSITION_ROLES.items():
        before, after = parsed[before_phase], parsed[after_phase]
        eligible = case['primary_qualified'] and before is not None and after is not None
        expected_before, expected_after = expected_state(case, before_phase), expected_state(case, after_phase)
        before_target, after_target = target_packet(before_phase, field), target_packet(after_phase, field)
        assert before_target == after_target, 'A retention transition must refer to a fixed capture-time claim.'
        target = before_target
        known_before = eligible and expected_before[field] != 'unknown'
        support_before = known_before and before[field] == expected_before[field] and before[field + '_evidence'] == [target]
        support_after = (after[field] == expected_after[field] and after[field + '_evidence'] == [target]) if support_before else None
        transitions.append({'id': f'{sid}/{role}', 'case_id': sid, 'role': role, 'field': field,
                            'claim_id': f'{sid}@{target}',
                            'before_phase': before_phase, 'after_phase': after_phase,
                            'before': before[field] if before else None, 'after': after[field] if after else None,
                            'expected_before': expected_before[field] if expected_before else None,
                            'expected_after': expected_after[field] if expected_after else None,
                            'transition_code': transition_code(before[field], after[field], expected_before[field], expected_after[field])
                                               if eligible else None,
                            'support_correct_before': bool(support_before) if eligible else None,
                            'support_preserved_after': support_after,
                            'source_before': f'responses/{sid}.json#/steps/{before_phase}',
                            'source_after': f'responses/{sid}.json#/steps/{after_phase}'})
    episode = score_episode(case, record.get('steps', {}))
    if not case['primary_qualified']:
        profile = 'ungraded_target'
    elif episode['status'] == 'incomplete' or any(parsed[phase] is None for phase in FINAL_PHASES):
        profile = 'blocked_response'
    else:
        profile = ''.join('1' if episode['steps'][phase]['state_perfect'] else '0' for phase in FINAL_PHASES)
    case_summary = {'case_id': sid, 'primary_qualified': case['primary_qualified'],
                    'primary_data_blocker': DATA_BLOCKERS.get(sid) if not case['primary_qualified'] else None,
                    'final_value_profile_JCD': profile,
                    'gold_endpoints': {'A': case['earlier_gold'], 'B': case['later_gold']},
                    'predicate': case['predicate'], 'qualification_notes': case['qualification_notes'],
                    'state_codes': dict(Counter(f['state_code'] for f in fields if f['state_code'])),
                    'citation_codes': dict(Counter(f['citation_code'] for f in fields if f['citation_code'])),
                    'transition_codes': dict(Counter(t['transition_code'] for t in transitions if t['transition_code'])),
                    'same_claim_consistency_code': next((r['same_claim_consistency_code'] for r in requests
                                                         if r['same_claim_consistency_code']), None)}
    return requests, fields, transitions, case_summary


def code_counts(rows, key):
    return dict(sorted(Counter(row[key] for row in rows if row[key] is not None).items()))


def claim_checks(fields):
    """One primary outcome per claim per request; collapse duplicate field aliases."""
    groups = {}
    for field in fields:
        key = (field['case_id'], field['phase'], field['claim_id'])
        groups.setdefault(key, []).append(field)
    checks = []
    for (sid, phase, claim_id), group in groups.items():
        assert len({row['expected'] for row in group}) == 1
        assert len({row['capture_time'] for row in group}) == 1
        assert len({row['disposition'] for row in group}) == 1
        eligible = group[0]['disposition'] == 'qualified'
        different = eligible and len({row['predicted'] for row in group}) > 1
        code = (consistency_code(group[0]['predicted'], group[1]['predicted']) if different else
                group[0]['state_code']) if eligible else None
        checks.append({'id': f'{sid}/{phase}/{claim_id}', 'case_id': sid, 'phase': phase,
                       'claim_id': claim_id, 'capture_time': group[0]['capture_time'],
                       'expected': group[0]['expected'],
                       'field_ids': [row['id'] for row in group],
                       'predictions': {row['field']: row['predicted'] for row in group},
                       'disposition': group[0]['disposition'], 'primary_code': code,
                       'source': group[0]['source']})
    return checks


def build(run_dir=RUN, output_dir=HERE):
    cases = json.loads((run_dir / 'cases.json').read_text())
    manifest = json.loads((run_dir / 'execution_manifest.json').read_text())
    for signature, filename in [('cases_sha256', 'cases.json'), ('protocol_sha256', 'protocol.py'), ('runner_sha256', 'run.py')]:
        assert fingerprint(run_dir / filename) == manifest['signatures'][signature], filename
    assert len(cases) == 20 and len({case['case_id'] for case in cases}) == 20
    requests, fields, transitions, case_summaries = [], [], [], []
    provenance = {}
    for filename in ('cases.json', 'execution_manifest.json', 'model_manifest.json', 'protocol.py', 'run.py'):
        provenance[filename] = fingerprint(run_dir / filename)
    for case in cases:
        sid = case['case_id']
        graph_relative = f'../online_pilot_v0/reviews/batch_v1/{sid}/evidence_graph.json'
        graph_path = run_dir / graph_relative
        assert fingerprint(graph_path) == case['graph_sha256'], f'{sid}: reviewed graph changed'
        graph = json.loads(graph_path.read_text())
        assert graph['source']['sha256'] == case['source_sha256'], f'{sid}: source identity mismatch'
        provenance[graph_relative] = fingerprint(graph_path)
        relative = f'responses/{sid}.json'
        record = json.loads((run_dir / relative).read_text())
        assert record['case_id'] == sid
        provenance[relative] = fingerprint(run_dir / relative)
        assert record['analysis'] == score_episode(case, record['steps']), sid
        for phase, step in record['steps'].items():
            meta = PHASES[phase]
            prior_phase = PHASES[phase]['previous']
            previous = record['steps'][prior_phase]['raw_response'] if prior_phase else None
            assert step['previous_memory'] == previous
            assert step['prompt'] == prompt_for(case, phase, previous)
            assert step['current_packets'] == meta['current'] and step['arrived_packets'] == meta['arrived']
            frames = [{'packet_id': packet, **frame} for packet in meta['current']
                      for frame in case['packets'][packet]['frames']]
            assert step['input_frames'] == frames
        r, f, t, summary = classify_case(case, record)
        requests.extend(r)
        fields.extend(f)
        transitions.extend(t)
        case_summaries.append(summary)
    eligible_fields = [field for field in fields if field['disposition'] == 'qualified']
    qualified_requests = [request for request in requests if request['semantic_disposition'] == 'qualified']
    eligible_transitions = [transition for transition in transitions if transition['transition_code']]
    checks = claim_checks(fields)
    eligible_checks = [check for check in checks if check['disposition'] == 'qualified']
    state_counts = code_counts(eligible_fields, 'state_code')
    citation_counts = code_counts(eligible_fields, 'citation_code')
    summaries = {
        'videos': len(cases), 'requests': len(requests), 'qualified_requests': len(qualified_requests),
        'qualified_fields': len(eligible_fields), 'ungraded_fields': sum(f['disposition'] == 'ungraded_target' for f in fields),
        'known_fields': sum(f['expected'] != 'unknown' for f in eligible_fields),
        'unknown_fields': sum(f['expected'] == 'unknown' for f in eligible_fields),
        'unique_qualified_capture_time_claims': len({f['claim_id'] for f in eligible_fields}),
        'qualified_claim_request_checks': len(eligible_checks),
        'primary_claim_outcomes': code_counts(eligible_checks, 'primary_code'),
        'qualified_same_claim_transitions': len(eligible_transitions),
        'request_format': code_counts(requests, 'format_code'),
        'state': state_counts, 'citation': citation_counts,
        'same_claim_consistency': code_counts(qualified_requests, 'same_claim_consistency_code'),
        'transition': code_counts(eligible_transitions, 'transition_code'),
        'transition_by_role': {role: code_counts([t for t in eligible_transitions if t['role'] == role], 'transition_code')
                               for role in TRANSITION_ROLES},
        'case_profiles_JCD': dict(sorted(Counter(c['final_value_profile_JCD'] for c in case_summaries).items())),
        'primary_data_blockers': dict(sorted(Counter(c['primary_data_blocker'] for c in case_summaries
                                                      if c['primary_data_blocker']).items())),
        'unsettled_A_cases': [c['case_id'] for c in case_summaries if c['primary_qualified'] and c['gold_endpoints']['A'] == 'unknown'],
        'state_by_phase': {phase: code_counts([f for f in eligible_fields if f['phase'] == phase], 'state_code') for phase in PHASES},
        'known_citation': code_counts([f for f in eligible_fields if f['expected'] != 'unknown'], 'citation_code'),
        'state_citation_cross_table': dict(sorted(Counter(f"{f['state_code']}:{f['citation_code']}" for f in eligible_fields).items())),
    }
    assert len(requests) == 100 and len(eligible_fields) == 170 and len(eligible_transitions) == 51
    assert len(eligible_checks) == 153 and len(checks) == 180
    assert sum(state_counts.values()) == 170 == sum(citation_counts.values())
    assert sum(summaries['same_claim_consistency'].values()) == 17
    assert sum(summaries['case_profiles_JCD'].values()) == 20
    for axis, rows, key in [('state', eligible_fields, 'state_code'), ('citation', eligible_fields, 'citation_code'),
                            ('transition', eligible_transitions, 'transition_code'), ('request_format', requests, 'format_code')]:
        assert all(row[key] in CATALOG[axis] for row in rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = {'taxonomy_version': VERSION, 'created_date': '2026-11-05',
              'paths_relative_to': 'archived experiment root: belief_revision_v1',
              'scope': 'Post-hoc operational classification of frozen provisional labels and saved outputs; no new model calls or independent annotation.',
              'input_sha256': provenance, 'summary': summaries,
              'requests': requests, 'claim_checks': checks, 'fields': fields,
              'transitions': transitions, 'cases': case_summaries}
    (output_dir / 'annotations.json').write_text(json.dumps(output, indent=2) + '\n')
    catalog = {'version': VERSION, 'units': {'request_format': 'request', 'state': 'field at request',
               'citation': 'field at request', 'same_claim_consistency': 'same-claim request',
               'transition': 'fixed capture-time claim across two requests'},
               'partitions': {axis: {code: {'name': values[0], 'definition': values[1]} for code, values in entries.items()}
                              for axis, entries in CATALOG.items()},
               'primary_claim_partition': {
                   'unit': 'one capture-time claim per request, collapsing aliased fields',
                   'codes': list(CATALOG['state']) + ['K10', 'K11'],
                   'precedence': 'If aliased fields disagree, assign K10/K11 only. Otherwise assign one S code for the shared value. Citation and transition facets are not added to this partition.'},
               'case_profile': {'order': ['joint final', 'chronological final', 'reversed final'],
                                'values': ['000', '001', '010', '011', '100', '101', '110', '111', 'ungraded_target', 'blocked_response']},
               'study_gap_register': 'GAPS.md',
               'curated_task_blockers': {
                   'unit': 'ungraded task, assigned from reviewed source/task findings',
                   'D01': 'Target identity or occurrence specification requires clarification.',
                   'D04': 'Specified target and intended positive evidence window do not align.',
                   'precedence': 'Resolve target meaning before asserting a task/window mismatch; not inferred from model outputs.'},
               'overlap_policy': 'One code per eligible unit within each partition. Never sum different partitions. A case can contain many distinct observations.'}
    (output_dir / 'catalog.json').write_text(json.dumps(catalog, indent=2) + '\n')
    write_findings(output, output_dir)
    assert all(fingerprint(run_dir / path) == value for path, value in provenance.items())
    print(json.dumps(summaries, indent=2))
    return output


def write_findings(output, directory):
    summary = output['summary']
    lines = ['# Applied failure taxonomy: twenty-video archived run', '',
             'Generated by `build_taxonomy.py` from exact saved responses and the frozen provisional labels. '
             'The [taxonomy and assignment rules](README.md) explain exclusions and causal limits. '
             'The [gap and hypothesis register](GAPS.md) separates study limitations from observed output errors.', '',
             '## Denominators and non-overlap', '',
             '100 requests across 20 videos; 85 qualified requests from 17 videos; 170 qualified field observations '
             '(138 known, 32 required unknown); 30 fields excluded for unresolved targets. The 170 observations '
             'repeat only 34 capture-time claims. They are not 170 independent events. '
             'There are 51 eligible fixed-claim transitions and 17 same-claim consistency checks.', '',
             'The primary claim-level view collapses same-request aliases: **153 qualified claim/request checks**, '
             '105 with matching values and 48 with a value error or internal inconsistency. These are repeated '
             'checks of 34 endpoint claims, not 153 independent events.', '',
             'Counts partition their own unit only. Do not add state errors, citation errors, consistency violations '
             'and transition failures to make a total: those describe different aspects of some of the same responses.', '',
             'Task qualification is separate: HA05/HA09 have curated D01 blockers (target identity/occurrence); '
             'HA10 has a D04 blocker (task/positive-window mismatch). HA06/HA08/HB06 are qualified with unsettled '
             'A evidence (D02), not invalid tasks. All of these findings remain single-reviewer judgments.', '']
    lines += ['## Primary non-overlapping claim outcomes', '',
              'One code per claim/request. An alias disagreement takes K10/K11 precedence; otherwise a shared value '
              'receives one S code. This prevents two fields asking the same claim from becoming two primary errors.', '',
              '| Code | Category | Claim/request checks |', '|---|---|---|']
    for code, (name, _) in {**CATALOG['state'], **{k: v for k, v in CATALOG['same_claim_consistency'].items() if k != 'K00'}}.items():
        lines.append(f"| {code} | {name} | {summary['primary_claim_outcomes'].get(code, 0)}/153 |")
    lines += ['', 'The 48 primary problems are 21 known-state abstentions, eight opposite binary values, '
              'five commitments on unsettled evidence and 14 certainty disagreements. The field-level partition '
              'below intentionally retains both requested fields for compatibility with the archived scorer; '
              'its 60 errors have a different denominator and must not be added to these 48.', '']
    for axis, title, denominator in [('state', 'State judgments', 170), ('citation', 'Citation attribution', 170),
                                     ('request_format', 'Response format', 100),
                                     ('same_claim_consistency', 'Same-claim consistency', 17),
                                     ('transition', 'Fixed-claim transitions', 51)]:
        lines += [f'## {title}', '', '| Code | Category | Count |', '|---|---|---|']
        for code, (name, _) in CATALOG[axis].items():
            lines.append(f'| {code} | {name} | {summary[axis].get(code, 0)}/{denominator} |')
        lines.append('')
    failures = sum(summary['state'].get(code, 0) for code in ERROR_CODES)
    lines += ['## Reading the partitions together', '',
              f'The **{failures}/170 state errors** consist of 34 abstentions on provisionally known states, '
              '19 opposite binary values and seven commitments on unsettled evidence. There are no premature '
              'commitments before A in the qualified set. These are output descriptions, not proven internal causes.', '',
              'The 14 same-claim inconsistencies are all unknown-versus-binary certainty disagreements; '
              '**zero are opposing yes/no contradictions**. Both fields refer to A at the first chronological step.', '',
              'For the 138 known fields, citation categories are: '
              + ', '.join(f"{code}={summary['known_citation'].get(code, 0)}" for code in CATALOG['citation']) + '. '
              'E00 means the requested packet is named; the predicted value can still be wrong.', '',
              'Among 85 correct known-value observations, 43 have an incorrect citation result: 29 omit required support '
              'and 14 cite the wrong capture-time packet. Conversely, 16 opposite-binary answers name the requested '
              'packet. This is why citation IDs and answer values need separate partitions.', '',
              '## State errors by phase', '',
              '| Phase | Correct known/unknown | Unseen commitment | Unsettled commitment | Known-state abstention | Binary error |',
              '|---|---|---|---|---|---|']
    for phase, counts in summary['state_by_phase'].items():
        correct = sum(counts.get(code, 0) for code in ('S00', 'S01', 'S02'))
        lines.append(f"| {phase} | {correct}/34 | {counts.get('S10', 0)} | {counts.get('S11', 0)} | "
                     f"{counts.get('S12', 0)} | {counts.get('S13', 0)} |")
    lines += ['', '## Transition roles: keep their opportunities separate', '',
              '| Role | Outcomes | Meaning |', '|---|---|---|']
    meanings = {'historical_arrival': '13/14 known targets resolve correctly; HB01 stays unknown. Three unresolved targets acquire unjustified binary values.',
                'historical_retention': 'Only HB01 starts with a correct known historical value and loses it. Eleven later correct values recover from previously incorrect summaries, not preservation successes.',
                'recent_retention': '14/14 initially correct recent values remain correct. The three initially incorrect recent answers stay incorrect; they are not newly forgotten facts.'}
    for role, counts in summary['transition_by_role'].items():
        lines.append(f"| {role} | {', '.join(f'{code}={n}' for code, n in counts.items())} | {meanings[role]} |")
    retained = [t for t in output['transitions'] if t['role'] == 'recent_retention' and t['support_correct_before']]
    lines += ['', f"Recent support-chain preservation is {sum(t['support_preserved_after'] for t in retained)}/{len(retained)} "
              'conditional opportunities, despite 14/14 value preservation. This is a cross-facet diagnostic, '
              'not another disjoint error bucket: it is the same 14 wrong-time citations recorded as E11.', '',
              'Chronological latest is deliberately absent from the retention table: its target changes from A to B, '
              'so comparing those two values as if they referred to one fixed event would be invalid.', '',
              '## Exclusive case profiles', '',
              'Bits J/C/D indicate whether both final state fields are correct for joint/chronological/reversed arrival. '
              'These patterns ignore citation correctness and are not causal diagnoses.', '',
              '| Profile | Cases |', '|---|---|']
    for profile in ['000', '001', '010', '011', '100', '101', '110', '111', 'ungraded_target', 'blocked_response']:
        ids = [case['case_id'] for case in output['cases'] if case['final_value_profile_JCD'] == profile]
        lines.append(f"| {profile} | {', '.join(ids) if ids else 'none'} |")
    lines += ['', '## All-video assignment ledger', '',
              'State and citation counts below are repeated field observations, not unique events. '
              'Each raw trace link contains the exact prompts, memory and outputs.', '',
              '| Case | JCD | State error codes | Citation error codes | Qualification |', '|---|---|---|---|---|']
    for case in output['cases']:
        errors = ', '.join(f'{code}={n}' for code, n in sorted(case['state_codes'].items()) if code in ERROR_CODES) or 'none'
        citations = ', '.join(f'{code}={n}' for code, n in sorted(case['citation_codes'].items()) if code in ('E10', 'E11', 'E12')) or 'none'
        qualification = ('ungraded: ' + (case['primary_data_blocker'] or 'needs adjudication')) if not case['primary_qualified'] else 'unsettled A label' if case['gold_endpoints']['A'] == 'unknown' else 'known endpoints'
        lines.append(f"| [{case['case_id']}](../responses/{case['case_id']}.json) | {case['final_value_profile_JCD']} | "
                     f"{errors if case['primary_qualified'] else 'ungraded'} | {citations if case['primary_qualified'] else 'ungraded'} | {qualification} |")
    lines += ['', '## Trace-backed boundary examples', '',
              '- **HB01:** chronological earlier no -> unknown is T13, loss of an initially correct value. '
              'Reversed latest no -> no is T15, a persistent prior error; calling it forgotten knowledge would be wrong.',
              '- **HA01:** reversed earlier unknown -> no is T00. Final earlier has E10 (missing citation), '
              'while final latest has E11 (older A cited for B). Correct values do not establish preserved provenance.',
              '- **HA08:** reversed earlier unknown -> no with an unresolved A label is T12/S11, not successful correction '
              'and not a demonstrated known-fact delayed-revision failure.',
              '- **HB08:** reversed earlier resolves correctly (T00), but latest unknown -> no is T15 because the initial '
              'latest was already incorrect. Historical correction and a wrong final recent answer can coexist.',
              '- **HA05/HA09/HA10:** task qualification blocks semantic scoring before any model-failure category is assigned. '
              'Their format remains observable; no positive/negative labels are invented.', '',
              '## What remains unproved', '',
              'No code here proves internal forgetting, a visual perception deficit, arrival-recency bias, memory-capacity '
              'limits, shortcut use, model-size insufficiency or backend numerical error. Joint failure does not isolate '
              'perception from instruction/slot interpretation. The original evidence graph selected and qualified '
              'inputs; graph memory was never supplied to the model. No graph-memory benefit is measured.', '',
              'The input hashes, every atomic field assignment and the before/after transition records are retained in '
              '[annotations.json](annotations.json). The machine-readable definitions are in [catalog.json](catalog.json).', '']
    (directory / 'FINDINGS.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=HERE)
    args = parser.parse_args()
    build(output_dir=args.output_dir.resolve())


if __name__ == '__main__':
    main()
