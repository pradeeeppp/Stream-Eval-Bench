"""Generate the three-question analysis for each video from actual saved outputs."""
import argparse
import json
import os
from pathlib import Path

from protocol import HERE, PHASES, expected_state, score_episode

ORDER = ['joint', 'chronological_0', 'chronological_1', 'delayed_0', 'delayed_1']


def fraction(values):
    eligible = [v for v in values if v is not None]
    return {'successes': sum(bool(v) for v in eligible), 'denominator': len(eligible),
            'rate': sum(bool(v) for v in eligible) / len(eligible) if eligible else None}


def fmt_fraction(value):
    return f"{value['successes']}/{value['denominator']}" if value['denominator'] else 'not applicable'


def show_state(obj):
    if not isinstance(obj, dict):
        return 'unparseable'
    return f"{obj.get('earlier', 'missing')} / {obj.get('latest', 'missing')}"


def research_answers(case, episode):
    if episode['status'] == 'incomplete':
        return ['Inference is incomplete; no model finding is assigned.'] * 3
    if episode['status'] == 'diagnostic_only':
        return [
            'The original target definition is unresolved, so a correct historical belief and its revision cannot be scored. Raw outputs are retained for inspection.',
            'Evidence citations can be inspected, but correctness of event association requires resolving the target definition first.',
            'Do not label model certainty or abstention unjustified from unresolved ground truth. This case is excluded from primary accuracy and revision rates.',
        ]
    steps, metrics = episode['steps'], episode['metrics']
    parsed = {p: (s['parsed'] or {}) for p, s in steps.items()}
    d0, d1 = parsed['delayed_0'], parsed['delayed_1']
    if not case['clean_revision_opportunity']:
        q1 = ('The earlier relation is unresolved even in the checked prior packet. This is an uncertainty-maintenance case, '
              'not a clean unknown-to-known correction opportunity. The final earlier answer is '
              f"{d1.get('earlier', 'missing')}; expected unknown under the provisional evidence labels.")
    elif metrics['clean_historical_update_success']:
        q1 = ('An observable historical value correction occurred: unknown -> '
              f"{d1.get('earlier')}. This concerns the model output; it does not establish an internal mechanism.")
    elif metrics['historical_final_factual_correct']:
        q1 = ('The final historical value is correct, but a clean correction was not observed. The earlier value changed '
              f"{d0.get('earlier', 'missing')} -> {d1.get('earlier', 'missing')}. A correct initial guess before packet A "
              'is not evidence-grounded historical revision. An unchanged value may still acquire new supporting evidence.')
    else:
        q1 = ('The historical field did not complete the required unknown-to-correct transition: '
              f"{d0.get('earlier', 'missing')} -> {d1.get('earlier', 'missing')}; expected final {case['earlier_gold']}.")
    bindings = steps['delayed_1']['known_binding_accuracy']
    q2 = (f"Final delayed evidence lists: earlier={d1.get('earlier_evidence', 'missing')}, "
          f"latest={d1.get('latest_evidence', 'missing')}. Known-target value-plus-citation accuracy is "
          f"{bindings if bindings is not None else 'not applicable'}. Earlier evidence must target A and later evidence B. "
          'Incorrect citations or state values are observable output errors; they do not distinguish internal forgetting, overwriting and misbinding. '
          'Packet identities/times are supplied, so natural same-event discovery is not tested.')
    q3 = ('Before A arrives, the historical field is '
          f"{d0.get('earlier', 'missing')}: "
          + ('appropriate unknown.' if metrics['uncertainty_preserved_before_earlier_evidence'] else 'the required unknown was not preserved.')
          + ' ')
    if metrics['recent_fact_preserved'] is True:
        q3 += 'The already-correct later fact remained correct after the older packet arrived.'
    elif metrics['recent_fact_preserved'] is False:
        q3 += 'The initially correct later fact was lost after the older packet arrived.'
    else:
        q3 += 'The later fact was not initially correct, so conditional preservation is not applicable.'
    q3 += ' This measures expressed answers and abstention, not calibrated confidence.'
    return [q1, q2, q3]


def analyze(here):
    cases = json.loads((here / 'cases.json').read_text())
    summaries = []
    analysis_dir = here / 'analysis'
    analysis_dir.mkdir(exist_ok=True)
    for case in cases:
        sid = case['case_id']
        path = here / 'responses' / f'{sid}.json'
        record = json.loads(path.read_text()) if path.exists() else {'steps': {}}
        episode = score_episode(case, record['steps'])
        answers = research_answers(case, episode)
        item = {'case_id': sid, 'primary_qualified': case['primary_qualified'],
                'clean_revision_opportunity': case['clean_revision_opportunity'],
                'episode': episode, 'research_question_answers': answers}
        summaries.append(item)
        text = [f'# {sid}: belief revision analysis', '',
                f"Visible condition: {case['predicate']}.", '',
                f"Status: **{episode['status']}**. One deterministic trial per condition.", '',
                f"Earlier target: {case['earlier_target_seconds']:.6f} s; later target: {case['later_target_seconds']:.6f} s.", '',
                'The two fields refer to fixed capture-time claims; receiving older footage does not change either event.', '',
                '| Condition / step | Current packet | Earlier / latest output | Expected earlier / latest | Field matches |',
                '|---|---|---|---|---|']
        for phase in ORDER:
            saved = record['steps'].get(phase)
            scored = episode.get('steps', {}).get(phase)
            raw = scored['parsed'] if scored else None
            expected = scored['expected_state'] if scored else None
            matches = sum(scored.get('field_matches', {}).values()) if scored and expected else None
            text.append(f"| {phase} | {','.join(PHASES[phase]['current'])} | "
                        f"{show_state(raw) if saved else 'pending'} | {show_state(expected) if expected else 'unscored'} | "
                        f"{str(matches) + '/2' if matches is not None else 'not scored'} |")
        for title, answer in zip([
                'Question one: does new evidence produce an observable historical correction?',
                'Question two: is evidence assigned to the appropriate capture-time claim?',
                'Question three: when should the answer change or remain uncertain?'], answers):
            text += ['', f'## {title}', '', answer]
        text += ['', '## Qualification and limits', '', case['qualification_notes'], '',
                 (case.get('prior_uncertainty_reason') or 'The earlier negative is provisionally supported by the selected packet.')
                 if case['primary_qualified'] else
                 'Neither endpoint is assigned a gold label until the original task definition is adjudicated.', '',
                 'Gold labels are single-assistant judgments. This local two-packet diagnostic does not establish a native '
                 'continuous-stream failure, natural replay association, a causal memory mechanism, or population reliability.', '',
                 f'[Exact requests and raw responses](../responses/{sid}.json) · '
                 f'[Model belief trace graph](../belief_graphs/{sid}.json) · '
                 f'[Reviewed factual evidence graph]({os.path.relpath(HERE.parent / "online_pilot_v0/reviews/batch_v1" / sid / "evidence_graph.json", analysis_dir)})', '',
                 '## Expressed evidence links', '',
                 '| Phase | Earlier evidence IDs | Latest evidence IDs |', '|---|---|---|']
        for phase in ORDER:
            scored = episode.get('steps', {}).get(phase)
            obj = (scored['parsed'] or {}) if scored else {}
            text.append(f"| {phase} | {obj.get('earlier_evidence', 'pending')} | "
                        f"{obj.get('latest_evidence', 'pending')} |")
        text.append('')
        (analysis_dir / f'{sid}.md').write_text('\n'.join(text))
    primary = [s for s in summaries if s['episode']['status'] == 'complete']
    totals = {'n_source_videos': len(cases), 'n_primary_qualified': sum(c['primary_qualified'] for c in cases),
              'n_clean_revision_opportunities': sum(c['clean_revision_opportunity'] for c in cases),
              'n_completed_primary': len(primary),
              'n_completed_diagnostic': sum(s['episode']['status'] == 'diagnostic_only' for s in summaries),
              'n_actual_benchmark_responses': sum(len(json.loads(p.read_text()).get('steps', {}))
                                                for p in (here / 'responses').glob('*.json')) if (here / 'responses').exists() else 0}
    rates = {}
    if primary:
        for metric in primary[0]['episode']['metrics']:
            if metric.endswith('_applicable'):
                continue
            rates[metric] = fraction([s['episode']['metrics'][metric] for s in primary])
    condition_totals = {}
    for phase in ORDER:
        steps = [s['episode']['steps'][phase] for s in primary]
        known = sum(s['known_fields'] for s in steps)
        condition_totals[phase] = {
            'correct_state_fields': sum(sum(s['field_matches'].values()) for s in steps),
            'state_fields': len(steps) * 2,
            'correct_known_fields': sum(round(s['known_state_accuracy'] * s['known_fields'])
                                        for s in steps if s['known_fields']),
            'known_fields': known,
            'correct_known_value_and_packet': sum(round(s['known_binding_accuracy'] * s['known_fields'])
                                                   for s in steps if s['known_fields']),
            'both_fields_correct_cases': sum(s['state_perfect'] for s in steps),
            'cases': len(steps),
        }
    all_steps = [step for s in summaries for step in s['episode'].get('steps', {}).values()]
    formats = {'scored_responses': len(all_steps),
               'exact_json': sum(s['exact_json'] for s in all_steps),
               'valid_four_key_schema': sum(s['schema_valid'] for s in all_steps)}
    # Descriptive checks added during inspection; these do not modify locked metrics.
    contradictions, citing_older = [], []
    for item in primary:
        c0 = item['episode']['steps']['chronological_0']['parsed'] or {}
        d1 = item['episode']['steps']['delayed_1']['parsed'] or {}
        if c0.get('earlier') in ('yes', 'no', 'unknown') and c0.get('latest') in ('yes', 'no', 'unknown'):
            contradictions.append(c0['earlier'] != c0['latest'])
        citations = d1.get('latest_evidence')
        citing_older.append(isinstance(citations, list) and 'A' in citations)
    descriptive = {'chronological_first_same_capture_time_disagreement': fraction(contradictions),
                   'delayed_final_latest_cites_older_packet_A': fraction(citing_older),
                   'status': 'Descriptive checks added during result inspection; qualified cases only.'}
    # Label-balance diagnostic, not a model run: a fixed arrival schedule can exploit
    # the selected negative-before/positive-after design without looking at pixels.
    qualified = [c for c in cases if c['primary_qualified']]
    schedule_baseline = {}
    for phase, meta in PHASES.items():
        prediction = {'earlier': 'no' if 'A' in meta['arrived'] else 'unknown',
                      'latest': 'yes' if 'B' in meta['arrived'] else 'no'}
        matches = [[prediction[k] == v for k, v in expected_state(c, phase).items()]
                   for c in qualified]
        schedule_baseline[phase] = {'prediction': prediction,
                                    'correct_fields': sum(sum(m) for m in matches),
                                    'fields': 2 * len(matches),
                                    'both_correct': sum(all(m) for m in matches),
                                    'cases': len(matches)}
    case_groups = {key: [s['case_id'] for s in primary if s['episode']['metrics'][key]]
                   for key in ('joint_correct_both_sequential_fail',
                               'joint_and_chronological_correct_delayed_fails',
                               'clean_historical_update_success')}
    full = {'status': 'complete' if totals['n_actual_benchmark_responses'] == 100 and
            totals['n_completed_primary'] + totals['n_completed_diagnostic'] == 20 else 'incomplete',
            'totals': totals, 'metrics': rates, 'condition_totals': condition_totals,
            'response_format': formats, 'descriptive_checks': descriptive,
            'analytical_no_pixel_schedule_baseline': schedule_baseline,
            'case_groups': case_groups, 'per_video': summaries}
    (here / 'analysis.json').write_text(json.dumps(full, indent=2) + '\n')
    text = ['# Twenty-video Qwen2.5-VL-3B belief revision findings', '',
            f"Execution status: **{full['status']}**. Actual saved benchmark responses: "
            f"**{totals['n_actual_benchmark_responses']}/100**.", '',
            'Seventeen original tasks have provisional labels; HA05/HA09/HA10 are diagnostic-only. '
            'Fourteen cases have a known earlier state suitable for testing clean correction. '
            'HA06/HA08/HB06 retain an unknown earlier label. All labels await independent annotation.', '',
            f"Among {len(primary)} completed qualified cases, both final fields are correct in "
            f"{condition_totals['joint']['both_fields_correct_cases']} joint, "
            f"{condition_totals['chronological_1']['both_fields_correct_cases']} chronological, and "
            f"{condition_totals['delayed_1']['both_fields_correct_cases']} reversed-arrival runs. "
            'These counts concern expressed state values; evidence correctness is reported separately.', '',
            f"Reversed final known-fact-plus-packet correctness is "
            f"{condition_totals['delayed_1']['correct_known_value_and_packet']}/{condition_totals['delayed_1']['known_fields']}. "
            'Value corrections therefore do not establish successful evidence association. A no-pixel schedule baseline '
            'also exploits the negative-to-positive label pattern; see the interpretation below.', '',
            '## Per-video results', '',
            '| Video | Status | Joint fields | Chronological final fields | Reversed final fields |',
            '|---|---|---|---|---|']
    for s in summaries:
        ep = s['episode']
        values = []
        for phase in ['joint', 'chronological_1', 'delayed_1']:
            step = ep.get('steps', {}).get(phase)
            values.append(str(sum(step.get('field_matches', {}).values())) + '/2'
                          if step and step['expected_state'] else 'unscored' if ep['status'] == 'diagnostic_only' else 'pending')
        text.append(f"| [{s['case_id']}](analysis/{s['case_id']}.md) | {ep['status']} | {' | '.join(values)} |")
    text += ['', '## Condition comparison', '',
             'Only the 17 provisionally qualified cases enter this table. State fields include required unknown '
             'answers; known fields exclude unresolved states.', '',
             '| Phase | Correct state fields | Correct known facts | Correct known fact + packet | Both fields correct |',
             '|---|---|---|---|---|']
    for phase, row in condition_totals.items():
        text.append(f"| {phase} | {row['correct_state_fields']}/{row['state_fields']} | "
                    f"{row['correct_known_fields']}/{row['known_fields']} | "
                    f"{row['correct_known_value_and_packet']}/{row['known_fields']} | "
                    f"{row['both_fields_correct_cases']}/{row['cases']} |")
    text += ['', f"Response format across completed cases: {formats['exact_json']}/{formats['scored_responses']} "
             f"exact JSON; {formats['valid_four_key_schema']}/{formats['scored_responses']} valid four-key schema.", '',
             '## Outcomes with explicit denominators', '', '| Measure | Cases satisfying measure / applicable cases |', '|---|---|']
    for name, value in rates.items():
        text.append(f'| {name} | {fmt_fraction(value)} |')
    text += ['', 'Descriptive checks added during result inspection (qualified cases only):', '',
             f"- Chronological first-step answers disagree about the same capture-time condition: "
             f"{fmt_fraction(descriptive['chronological_first_same_capture_time_disagreement'])}.",
             f"- Reversed final latest answers cite older packet A: "
             f"{fmt_fraction(descriptive['delayed_final_latest_cites_older_packet_A'])}."]
    text += ['', 'Paired condition patterns:', '',
             '- Joint correct, both sequential finals fail: '
             + (', '.join(case_groups['joint_correct_both_sequential_fail']) or 'none') + '.',
             '- Joint and chronological correct, reversed final fails: '
             + (', '.join(case_groups['joint_and_chronological_correct_delayed_fails']) or 'none') + '.']
    text += ['', '## Interpretation', '',
             'The tables report two-field output correctness, including required unknown answers. Known-fact accuracy and '
             'value-plus-evidence accuracy are recorded separately in analysis.json. Conditional preservation excludes '
             'cases where the initial answer was already incorrect. No missing or infrastructure-failed request is scored '
             'as a model error.', '',
             'Joint success with failure in both sequential orders describes a segmented-input difficulty; it does not '
             'identify a state-maintenance mechanism. Joint and chronological success with a delayed failure is an '
             'order-sensitive candidate within this protocol. '
             + ('The only such case here, HA08, has expected earlier=unknown, '
                'so it concerns uncertainty maintenance rather than failure to recover a known earlier fact. '
                'HB06 also has an unknown earlier label. ' if here.resolve() == HERE.resolve() else
                'Inspect each paired candidate against its known or unknown prior label; these are output patterns. ')
             + 'One trial does not establish a reproducible mechanism or a novel streaming-specific phenomenon.', '',
             'A label-balance check reveals an additional limit: a rule that never inspects pixels and always answers '
             'earlier=unknown until A, earlier=no after A, and latest=no before B/yes after B achieves '
             f"{schedule_baseline['delayed_1']['correct_fields']}/{schedule_baseline['delayed_1']['fields']} final state fields "
             f"and {schedule_baseline['delayed_1']['both_correct']}/{schedule_baseline['delayed_1']['cases']} fully correct cases. "
             'It also produces all fourteen required unknown-to-no transitions. This is an analytical baseline, not a '
             'model execution. Therefore high value-transition success alone cannot establish visual evidence use. '
             'Balanced unchanged-positive, unchanged-negative and positive-to-negative controls are needed for that claim.', '',
             'This uses two event-centered four-frame video packets and external JSON memory. The same eight frames are '
             'used across conditions. It does not evaluate all frames of each recording or reproduce the PDF\'s separate '
             'uniform whole-video sampling. It also does not test natural replay discovery or calibrated confidence.', '']
    (here / 'RESULTS.md').write_text('\n'.join(text))
    print(json.dumps({'status': full['status'], **totals}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, default=HERE)
    args = parser.parse_args()
    analyze(args.run_dir.resolve())


if __name__ == '__main__':
    main()
