"""Regression checks for review invariants that affect benchmark validity."""
import copy
import json
import unittest

from review_media import HERE
from validate import validate_graph


class EvidenceIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graphs = [json.loads(line) for line in (HERE / 'evidence_graphs.reviewed.jsonl').read_text().splitlines()]

    def test_all_completed_graphs_pass_structural_checks(self):
        for graph in self.graphs:
            with self.subTest(source_id=graph['source_id']):
                validate_graph(graph)

    def test_future_native_evidence_is_rejected(self):
        graph = copy.deepcopy(self.graphs[0])
        next(n for n in graph['nodes'] if n['id'] == 'alert_1')['source_capture_boundary_seconds'] = 0
        with self.assertRaisesRegex(ValueError, 'Future'):
            validate_graph(graph)

    def test_unresolved_task_cannot_become_an_alert(self):
        graph = copy.deepcopy(next(g for g in self.graphs if g['source_id'] == 'HA10'))
        next(n for n in graph['nodes'] if n['id'] == 'alert_1')['status'] = 'provisional_target_supported'
        with self.assertRaisesRegex(ValueError, 'Unresolved task'):
            validate_graph(graph)

    def test_uninspected_anchor_is_rejected(self):
        graph = copy.deepcopy(self.graphs[0])
        next(n for n in graph['nodes'] if n['type'] == 'observation')['frame_index_zero_based'] = 999999
        with self.assertRaisesRegex(ValueError, 'not in inspected'):
            validate_graph(graph)

    def test_dangling_evidence_link_is_rejected(self):
        graph = copy.deepcopy(self.graphs[0])
        graph['edges'][0]['target'] = 'missing_claim'
        with self.assertRaisesRegex(ValueError, 'Dangling edge'):
            validate_graph(graph)


if __name__ == '__main__':
    unittest.main()
