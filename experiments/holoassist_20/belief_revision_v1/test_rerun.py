"""Portable-run integrity tests; fixture outputs are never benchmark results."""
import contextlib
import copy
import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import input_bundle
import rerun
from protocol import HERE, digest


class RerunTests(unittest.TestCase):
    def setUp(self):
        self.runs_root = HERE.parent / 'runs'
        self.runs_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='unit-fixture-', dir=self.runs_root)
        self.addCleanup(self.temporary.cleanup)
        self.destination = Path(self.temporary.name) / 'run'
        self.model = json.loads((HERE / 'model_manifest.json').read_text())
        self.signature = rerun.signatures(HERE / 'cases.json', self.model['revision'], 'cpu', 'single', {'fixture': True})

    def initialize(self):
        return rerun.initialize_run(self.destination, self.signature, self.model)

    def test_baseline_and_nonempty_outputs_cannot_be_overwritten(self):
        with self.assertRaises(ValueError):
            rerun.initialize_run(HERE, self.signature, self.model)
        self.destination.mkdir()
        (self.destination / 'existing.txt').write_text('preserve')
        with self.assertRaises(ValueError):
            self.initialize()

    def test_resume_requires_identical_environment_and_code(self):
        first = self.initialize()
        self.assertEqual(self.initialize(), first)
        changed = copy.deepcopy(self.signature)
        changed['environment'] = {'fixture': False}
        with self.assertRaises(ValueError):
            rerun.initialize_run(self.destination, changed, self.model)
        (self.destination / 'code/protocol.py').write_text('changed')
        with self.assertRaises(ValueError):
            self.initialize()

    def test_interrupted_episode_resumes_without_repeating_or_losing_memory(self):
        self.initialize()
        cases = json.loads((HERE / 'cases.json').read_text())[:1]

        class FixtureBackend:
            calls = 0
            def generate(self, prompt, videos, fps):
                self.calls += 1
                return json.dumps({'earlier': 'unknown', 'latest': 'unknown',
                                   'earlier_evidence': [], 'latest_evidence': []}), {
                    'generation_seconds': 0, 'input_tokens': 1, 'generated_tokens': 1,
                    'video_grid_thw': [], 'second_per_grid_ts': [], 'rendered_prompt_sha256': 'fixture'}

        backend = FixtureBackend()
        with patch.object(rerun, 'packet_inputs', return_value=([], [], [])), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(rerun.execute(self.destination, cases, backend, max_calls=2), 2)
            self.assertEqual(rerun.execute(self.destination, cases, backend), 3)
            self.assertEqual(rerun.execute(self.destination, cases, backend), 0)
        self.assertEqual(backend.calls, 5)
        record = json.loads((self.destination / 'responses/HA01.json').read_text())
        for phase in ['chronological_1', 'delayed_1']:
            previous = record['steps'][phase.replace('_1', '_0')]['raw_response']
            self.assertEqual(record['steps'][phase]['previous_memory'], previous)

    def test_bundle_roundtrip_and_rejects_overwriting_changed_inputs(self):
        root = Path(self.temporary.name)
        original = root / 'source'
        (original / 'media').mkdir(parents=True)
        data = b'fixture input bytes'
        (original / 'media/frame.jpg').write_bytes(data)
        expected = {'media/frame.jpg': hashlib.sha256(data).hexdigest()}
        bundle = root / 'inputs.tar.gz'
        target = root / 'restored'
        with patch.object(input_bundle, 'expected_files', return_value=expected):
            input_bundle.pack(bundle, original)
            input_bundle.unpack(bundle, target)
            self.assertEqual((target / 'media/frame.jpg').read_bytes(), data)
            (target / 'media/frame.jpg').write_text('changed')
            with self.assertRaises(ValueError):
                input_bundle.unpack(bundle, target)

    def test_bundle_rejects_traversal_and_hash_mismatch_before_writing(self):
        root = Path(self.temporary.name)
        expected = {'media/frame.jpg': hashlib.sha256(b'expected').hexdigest()}
        manifest = json.dumps({'cases_sha256': digest(HERE / 'cases.json'), 'files': expected}).encode()
        for name in ['../escape.jpg', 'media/frame.jpg']:
            archive_path = root / 'bad.tar.gz'
            with tarfile.open(archive_path, 'w:gz') as archive:
                for path, data in [('input_bundle.json', manifest), (name, b'wrong')]:
                    entry = tarfile.TarInfo(path)
                    entry.size = len(data)
                    archive.addfile(entry, io.BytesIO(data))
            with patch.object(input_bundle, 'expected_files', return_value=expected), self.assertRaises(ValueError):
                input_bundle.unpack(archive_path, root / 'restore')
            self.assertFalse((root / 'restore').exists())


if __name__ == '__main__':
    unittest.main()
