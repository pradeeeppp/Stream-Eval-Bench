import hashlib
import io
import tempfile
import unittest
from pathlib import Path

from download_videos import download, load_sources


class Response(io.BytesIO):
    def __init__(self, data, status=200, headers=None):
        super().__init__(data)
        self.status = status
        self.headers = headers or {}


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = b'fixture video bytes'
        self.source = {'source_id': 'fixture', 'local_path': 'videos/test.mp4',
                       'source_url': 'https://example.invalid/pinned/test.mp4',
                       'sha256': hashlib.sha256(self.data).hexdigest()}

    def test_graphs_and_source_register_agree(self):
        self.assertEqual(len(load_sources()), 20)

    def test_download_verifies_and_reuses_existing_file(self):
        result = download(self.source, self.root, lambda _: Response(self.data), retries=1)
        self.assertEqual(result['status'], 'downloaded')
        result = download(self.source, self.root, lambda _: self.fail('No network expected'), retries=1)
        self.assertEqual(result['status'], 'already_verified')

    def test_resume_and_ignored_range_both_produce_exact_bytes(self):
        for status in (200, 206):
            destination = self.root / 'videos/test.mp4'
            destination.parent.mkdir(exist_ok=True)
            destination.unlink(missing_ok=True)
            destination.with_suffix('.mp4.part').write_bytes(self.data[:5])
            def opener(request):
                self.assertEqual(request.get_header('Range'), 'bytes=5-')
                return Response(self.data[5:] if status == 206 else self.data, status,
                                {'Content-Range': f'bytes 5-{len(self.data)-1}/{len(self.data)}'})
            download(self.source, self.root, opener, retries=1)
            self.assertEqual(destination.read_bytes(), self.data)

    def test_bad_download_never_becomes_final_and_existing_mismatch_is_preserved(self):
        with self.assertRaises(RuntimeError):
            download(self.source, self.root, lambda _: Response(b'wrong'), retries=1)
        destination = self.root / 'videos/test.mp4'
        self.assertFalse(destination.exists())
        destination.write_bytes(b'existing modified data')
        with self.assertRaises(ValueError):
            download(self.source, self.root, lambda _: self.fail('No network expected'), retries=1)
        self.assertEqual(destination.read_bytes(), b'existing modified data')


if __name__ == '__main__':
    unittest.main()
