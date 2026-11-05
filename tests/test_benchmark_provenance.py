"""Mock harness checks must not be represented as model measurements."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from stream_eval.benchmark_qwen import main, run_qwen_benchmark
from stream_eval.core.agents import MockAgent


class BenchmarkProvenanceTests(unittest.TestCase):
    def test_mock_keeps_actual_identity_and_uses_separate_default_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('stream_eval.benchmark_qwen.REPO_ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                report = run_qwen_benchmark('Qwen2.5-VL-72B', MockAgent(mode='oracle'))
            self.assertIsNone(report['model_name'])
            self.assertEqual(report['requested_model_name'], 'Qwen2.5-VL-72B')
            self.assertEqual(report['evaluation_kind'], 'mock_simulation')
            self.assertEqual(report['agent_metadata']['type'], 'MockAgent')
            self.assertFalse((root / 'experiments/qwen_benchmarks').exists())
            files = list((root / 'experiments/runs/mock_benchmarks').glob('*.json'))
            self.assertEqual(len(files), 1)
            self.assertNotIn('72B', files[0].name)
            self.assertEqual(json.loads(files[0].read_text()), report)
            self.assertTrue(all(ep['agent_metadata']['type'] == 'MockAgent' for ep in report['episodes'].values()))

    def test_backend_selection_is_required_before_running(self):
        with patch('sys.argv', ['benchmark_qwen']), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main()
        self.assertEqual(raised.exception.code, 2)

    def test_mock_both_is_one_agent_check_not_two_model_runs(self):
        arguments = ['benchmark_qwen', '--backend', 'mock', '--model', 'both']
        with patch('sys.argv', arguments), patch('stream_eval.benchmark_qwen.run_qwen_benchmark') as run:
            main()
        run.assert_called_once()
        self.assertIsInstance(run.call_args.kwargs['agent'], MockAgent)


if __name__ == '__main__':
    unittest.main()
