import json
import unittest

from protocol import HERE, expected_state, parse_response, prompt_for, score_episode


def answer(earlier, latest, earlier_evidence, latest_evidence):
    return {'status': 'ok', 'raw_response': json.dumps(dict(earlier=earlier, latest=latest,
            earlier_evidence=earlier_evidence, latest_evidence=latest_evidence))}


class BeliefRevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((HERE / 'cases.json').read_text())
        cls.known = next(c for c in cls.cases if c['case_id'] == 'HA01')

    def oracle(self):
        return {'joint': answer('no', 'yes', ['A'], ['B']),
                'chronological_0': answer('no', 'no', ['A'], ['A']),
                'chronological_1': answer('no', 'yes', ['A'], ['B']),
                'delayed_0': answer('unknown', 'yes', [], ['B']),
                'delayed_1': answer('no', 'yes', ['A'], ['B'])}

    def test_clean_correction_and_both_preservations(self):
        report = score_episode(self.known, self.oracle())
        self.assertTrue(report['metrics']['clean_historical_update_success'])
        self.assertTrue(report['metrics']['recent_fact_preserved'])
        self.assertTrue(report['metrics']['past_fact_preserved_chronological'])

    def test_correct_early_guess_is_not_clean_correction(self):
        records = self.oracle()
        records['delayed_0'] = answer('no', 'yes', ['A'], ['B'])
        report = score_episode(self.known, records)
        self.assertTrue(report['metrics']['historical_final_factual_correct'])
        self.assertFalse(report['metrics']['clean_historical_update_success'])
        self.assertTrue(report['steps']['delayed_0']['future_packet_citation']['earlier'])

    def test_preservation_requires_initially_correct_fact(self):
        records = self.oracle()
        records['delayed_0'] = answer('unknown', 'no', [], ['B'])
        report = score_episode(self.known, records)
        self.assertIsNone(report['metrics']['recent_fact_preserved'])

    def test_unknown_prior_does_not_create_false_revision_opportunity(self):
        case = next(c for c in self.cases if c['case_id'] == 'HA06')
        report = score_episode(case, self.oracle())
        self.assertIsNone(report['metrics']['clean_historical_update_success'])
        self.assertIsNone(report['metrics']['historical_final_factual_correct'])

    def test_unresolved_task_is_never_scored_as_wrong(self):
        case = next(c for c in self.cases if c['case_id'] == 'HA10')
        report = score_episode(case, self.oracle())
        self.assertEqual(report['status'], 'diagnostic_only')
        self.assertIsNone(report['metrics'])
        self.assertIsNone(report['steps']['joint']['state_accuracy'])

    def test_missing_calls_are_not_model_failures(self):
        records = self.oracle()
        del records['delayed_1']
        self.assertEqual(score_episode(self.known, records)['status'], 'incomplete')

    def test_capture_time_survives_reversed_arrival(self):
        self.assertEqual(expected_state(self.known, 'delayed_1'), {'earlier': 'no', 'latest': 'yes'})
        text = prompt_for(self.known, 'delayed_1', 'verbatim previous output')
        self.assertIn('verbatim previous output', text)
        self.assertIn(f"{self.known['later_target_seconds']:.6f}", text)
        self.assertNotIn('earlier_gold', text)

    def test_non_object_json_is_invalid(self):
        self.assertEqual(parse_response('[1, 2]'), (None, False, False))


if __name__ == '__main__':
    unittest.main()
