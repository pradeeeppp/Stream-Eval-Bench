"""Boundary tests for exclusivity, censoring and causal over-attribution."""
from collections import Counter
from copy import deepcopy
from itertools import product
import json
import unittest

from build_taxonomy import (
    CATALOG, RUN, VALUES, citation_code, claim_checks, classify_case, consistency_code,
    response_format, state_code, target_packet, transition_code,
)


def answer(earlier, latest, earlier_evidence=None, latest_evidence=None):
    return {'status': 'ok', 'raw_response': json.dumps({
        'earlier': earlier, 'latest': latest,
        'earlier_evidence': earlier_evidence or [], 'latest_evidence': latest_evidence or [],
    })}


class TaxonomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = next(c for c in json.loads((RUN / 'cases.json').read_text()) if c['case_id'] == 'HA01')

    def oracle(self):
        return {'steps': {
            'joint': answer('no', 'yes', ['A'], ['B']),
            'chronological_0': answer('no', 'no', ['A'], ['A']),
            'chronological_1': answer('no', 'yes', ['A'], ['B']),
            'delayed_0': answer('unknown', 'yes', [], ['B']),
            'delayed_1': answer('no', 'yes', ['A'], ['B']),
        }}

    def test_state_rules_are_a_partition_of_legal_inputs(self):
        # Independent predicates express the definitions, not a second copy of the branch order.
        seen = set()
        for prediction, expected, received in product(VALUES, VALUES, (False, True)):
            if not received and expected != 'unknown':
                with self.assertRaises(ValueError):
                    state_code(prediction, expected, received)
                continue
            matches = {
                'S00': expected != 'unknown' and prediction == expected,
                'S01': expected == prediction == 'unknown' and not received,
                'S02': expected == prediction == 'unknown' and received,
                'S10': expected == 'unknown' and prediction != 'unknown' and not received,
                'S11': expected == 'unknown' and prediction != 'unknown' and received,
                'S12': expected != 'unknown' and prediction == 'unknown',
                'S13': expected != 'unknown' and prediction != 'unknown' and prediction != expected,
            }
            valid = [code for code, value in matches.items() if value]
            self.assertEqual(len(valid), 1)
            self.assertEqual(state_code(prediction, expected, received), valid[0])
            seen.add(valid[0])
        self.assertEqual(seen, set(CATALOG['state']))

    def test_uncertain_label_is_not_a_negative(self):
        self.assertEqual(state_code('no', 'unknown', True), 'S11')
        self.assertEqual(state_code('unknown', 'unknown', True), 'S02')
        self.assertEqual(state_code('unknown', 'no', True), 'S12')

    def test_unreceived_citation_takes_precedence_over_wrong_time(self):
        self.assertEqual(citation_code(['A', 'B'], 'B', ['B'], 'yes'), 'E12')
        self.assertEqual(citation_code(['A', 'B'], 'B', ['A', 'B'], 'yes'), 'E11')
        self.assertEqual(citation_code(['A'], 'B', ['B', 'A'], 'yes'), 'E11')

    def test_citation_rules_are_exclusive_on_legal_inputs(self):
        seen = set()
        for target, arrived, refs, expected in product(
                ('A', 'B'), (['A'], ['B'], ['A', 'B']), ([], ['A'], ['B'], ['A', 'B']), VALUES):
            if target not in arrived and expected != 'unknown':
                continue
            received, cited = set(arrived), set(refs)
            outside = bool(cited - received)
            predicates = {
                'E12': outside,
                'E11': not outside and bool(cited) and cited != {target},
                'E10': not cited and target in received and expected != 'unknown',
                'E01': not cited and (target not in received or expected == 'unknown'),
                'E00': not outside and cited == {target},
            }
            codes = [code for code, value in predicates.items() if value]
            self.assertEqual(len(codes), 1)
            self.assertEqual(citation_code(refs, target, arrived, expected), codes[0])
            seen.add(codes[0])
        self.assertEqual(seen, set(CATALOG['citation']))

    def test_empty_support_has_different_requirements_for_unknown(self):
        self.assertEqual(citation_code([], 'A', ['B'], 'unknown'), 'E01')
        self.assertEqual(citation_code([], 'A', ['A'], 'unknown'), 'E01')
        self.assertEqual(citation_code([], 'A', ['A'], 'no'), 'E10')

    def test_target_matching_is_not_value_correctness(self):
        record = self.oracle()
        record['steps']['chronological_1'] = answer('yes', 'no', ['A'], ['B'])
        _, fields, _, _ = classify_case(self.case, record)
        fields = [f for f in fields if f['phase'] == 'chronological_1']
        self.assertTrue(all(f['citation_code'] == 'E00' and f['state_code'] == 'S13' for f in fields))
        self.assertTrue(all(f['known_value_and_packet_correct'] is False for f in fields))

    def test_certainty_disagreement_is_not_binary_contradiction(self):
        counts = Counter(consistency_code(a, b) for a, b in product(VALUES, repeat=2))
        self.assertEqual(counts, {'K00': 3, 'K10': 2, 'K11': 4})

    def test_wrong_prior_does_not_become_forgotten_fact(self):
        self.assertEqual(transition_code('no', 'no', 'yes', 'yes'), 'T15')
        self.assertEqual(transition_code('unknown', 'no', 'yes', 'yes'), 'T15')
        self.assertEqual(transition_code('yes', 'unknown', 'yes', 'yes'), 'T13')
        self.assertEqual(transition_code('yes', 'no', 'yes', 'yes'), 'T14')

    def test_correct_initial_guess_is_not_clean_evidence_update(self):
        self.assertEqual(transition_code('no', 'no', 'unknown', 'no'), 'T16')
        self.assertEqual(transition_code('unknown', 'no', 'unknown', 'no'), 'T00')

    def test_maintaining_uncertainty_and_resolving_it_are_distinct(self):
        self.assertEqual(transition_code('unknown', 'no', 'unknown', 'unknown'), 'T12')
        self.assertEqual(transition_code('unknown', 'unknown', 'unknown', 'unknown'), 'T01')
        self.assertEqual(transition_code('unknown', 'unknown', 'unknown', 'no'), 'T10')

    def test_transition_outcomes_cover_all_protocol_trajectories(self):
        observed = set()
        expected_pairs = [(gold, gold) for gold in VALUES] + [('unknown', 'no'), ('unknown', 'yes')]
        for (before_gold, after_gold), before, after in product(expected_pairs, VALUES, VALUES):
            code = transition_code(before, after, before_gold, after_gold)
            self.assertIn(code, CATALOG['transition'])
            observed.add(code)
        self.assertEqual(observed, set(CATALOG['transition']))

    def test_transition_definitions_do_not_overlap(self):
        expected_pairs = [(gold, gold) for gold in VALUES] + [('unknown', 'no'), ('unknown', 'yes')]
        for (before_gold, after_gold), before, after in product(expected_pairs, VALUES, VALUES):
            changes = before_gold != after_gold
            prior_correct = before == before_gold
            final_correct = after == after_gold
            definitions = {
                'T00': changes and prior_correct and final_correct,
                'T01': not changes and prior_correct and final_correct,
                'T02': not changes and not prior_correct and final_correct,
                'T10': changes and prior_correct and not final_correct and after == 'unknown',
                'T11': changes and prior_correct and not final_correct and after != 'unknown',
                'T12': not changes and prior_correct and not final_correct and after_gold == 'unknown',
                'T13': not changes and prior_correct and not final_correct and after_gold != 'unknown' and after == 'unknown',
                'T14': not changes and prior_correct and not final_correct and after_gold != 'unknown' and after != 'unknown',
                'T15': not changes and not prior_correct and not final_correct,
                'T16': changes and not prior_correct,
            }
            codes = [code for code, condition in definitions.items() if condition]
            self.assertEqual(len(codes), 1)
            self.assertEqual(transition_code(before, after, before_gold, after_gold), codes[0])

    def test_chronological_latest_is_not_same_claim_retention(self):
        self.assertNotEqual(target_packet('chronological_0', 'latest'), target_packet('chronological_1', 'latest'))
        _, _, transitions, _ = classify_case(self.case, self.oracle())
        self.assertEqual(len(transitions), 3)
        self.assertFalse(any(t['field'] == 'latest' and t['before_phase'] == 'chronological_0' for t in transitions))

    def test_unresolved_tasks_are_censored_not_model_errors(self):
        case = deepcopy(self.case)
        case.update(primary_qualified=False, earlier_gold=None, later_gold=None)
        requests, fields, transitions, summary = classify_case(case, self.oracle())
        self.assertTrue(all(r['format_code'] == 'R00' for r in requests))
        self.assertTrue(all(f['state_code'] is None and f['citation_code'] is None for f in fields))
        self.assertTrue(all(t['transition_code'] is None for t in transitions))
        self.assertEqual(summary['final_value_profile_JCD'], 'ungraded_target')

    def test_invalid_schema_censors_dependent_semantic_checks(self):
        record = self.oracle()
        record['steps']['delayed_1'] = {'status': 'ok', 'raw_response': '[1,2]'}
        requests, fields, transitions, summary = classify_case(self.case, record)
        self.assertEqual(next(r for r in requests if r['phase'] == 'delayed_1')['format_code'], 'R11')
        self.assertTrue(all(f['state_code'] is None for f in fields if f['phase'] == 'delayed_1'))
        self.assertTrue(all(t['transition_code'] is None for t in transitions if t['after_phase'] == 'delayed_1'))
        self.assertEqual(summary['final_value_profile_JCD'], 'blocked_response')

    def test_missing_steps_and_infrastructure_are_not_semantic_errors(self):
        self.assertEqual(response_format(None), ('R20', None))
        self.assertEqual(response_format({'status': 'error'}), ('R21', None))
        record = self.oracle()
        del record['steps']['chronological_0']
        requests, _, _, summary = classify_case(self.case, record)
        self.assertEqual(next(r for r in requests if r['phase'] == 'chronological_0')['format_code'], 'R20')
        self.assertEqual(summary['final_value_profile_JCD'], 'blocked_response')

    def test_wrapped_json_is_a_format_error_with_recoverable_semantics(self):
        step = answer('no', 'yes', ['A'], ['B'])
        step['raw_response'] = '```json\n' + step['raw_response'] + '\n```'
        code, obj = response_format(step)
        self.assertEqual(code, 'R12')
        self.assertEqual(obj['earlier'], 'no')
        self.assertEqual(response_format({'status': 'ok', 'raw_response': 'no JSON'})[0], 'R10')

    def test_value_preservation_can_lose_cited_support(self):
        record = self.oracle()
        record['steps']['delayed_1'] = answer('no', 'yes', [], ['A'])
        _, _, transitions, _ = classify_case(self.case, record)
        recent = next(t for t in transitions if t['role'] == 'recent_retention')
        self.assertEqual(recent['transition_code'], 'T01')
        self.assertTrue(recent['support_correct_before'])
        self.assertFalse(recent['support_preserved_after'])

    def test_equal_wrong_aliases_are_one_primary_error(self):
        record = self.oracle()
        record['steps']['chronological_0'] = answer('unknown', 'unknown')
        _, fields, _, _ = classify_case(self.case, record)
        checks = [row for row in claim_checks(fields) if row['phase'] == 'chronological_0']
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0]['primary_code'], 'S12')
        self.assertEqual(len(checks[0]['field_ids']), 2)

    def test_inconsistent_aliases_have_one_primary_consistency_code(self):
        record = self.oracle()
        record['steps']['chronological_0'] = answer('unknown', 'no')
        _, fields, _, _ = classify_case(self.case, record)
        checks = [row for row in claim_checks(fields) if row['phase'] == 'chronological_0']
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0]['primary_code'], 'K11')
        self.assertEqual({f['state_code'] for f in fields if f['phase'] == 'chronological_0'}, {'S12', 'S00'})

    def test_same_claim_in_different_requests_is_not_collapsed(self):
        _, fields, _, _ = classify_case(self.case, self.oracle())
        checks = claim_checks(fields)
        self.assertEqual(len(checks), 9)
        self.assertEqual(len([row for row in checks if row['claim_id'].endswith('@A')]), 5)
        self.assertEqual(len({row['id'] for row in checks}), 9)


if __name__ == '__main__':
    unittest.main()
