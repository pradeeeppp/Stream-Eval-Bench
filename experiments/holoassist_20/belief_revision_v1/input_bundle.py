"""Transfer exact evaluated JPEGs without downloading or re-encoding source movies."""
import argparse
import hashlib
import io
import json
import tarfile
import tempfile
from pathlib import Path

from protocol import HERE, digest


def expected_files():
    files = {}
    for case in json.loads((HERE / 'cases.json').read_text()):
        for packet in case['packets'].values():
            for frame in packet['frames']:
                files[frame['path']] = frame['sha256']
        files[f"media/{case['case_id']}/review.png"] = case['packet_review_sha256']
    return files


def verify_inputs(root=HERE):
    files = expected_files()
    for name, expected in files.items():
        path = root / name
        if not path.is_file() or digest(path) != expected:
            raise ValueError(f'Missing or changed frozen input: {path}')
    return files


def pack(destination, root=HERE):
    files = verify_inputs(root)
    if destination.exists():
        raise FileExistsError(f'Refusing to replace existing bundle: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    metadata = json.dumps({'cases_sha256': digest(HERE / 'cases.json'), 'files': files}, indent=2).encode()
    with tarfile.open(destination, 'w:gz') as archive:
        entry = tarfile.TarInfo('input_bundle.json')
        entry.size = len(metadata)
        archive.addfile(entry, io.BytesIO(metadata))
        for name in files:
            archive.add(root / name, arcname=name, recursive=False)
    return {'path': str(destination), 'files': len(files), 'sha256': digest(destination)}


def unpack(source, root=HERE):
    expected = expected_files()
    with tarfile.open(source, 'r:gz') as archive, tempfile.TemporaryDirectory(prefix='stream-inputs-') as temporary:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or set(names) != set(expected) | {'input_bundle.json'}:
            raise ValueError('Bundle has missing, extra or duplicate paths')
        if any(not member.isfile() or member.size > 16 * 1024 * 1024 for member in members):
            raise ValueError('Bundle contains a non-file or oversized entry')
        manifest = json.load(archive.extractfile('input_bundle.json'))
        if manifest != {'cases_sha256': digest(HERE / 'cases.json'), 'files': expected}:
            raise ValueError('Bundle does not match this frozen experiment')
        temporary = Path(temporary)
        for name, checksum in expected.items():
            data = archive.extractfile(name).read()
            if hashlib.sha256(data).hexdigest() != checksum:
                raise ValueError(f'Bundle input hash mismatch: {name}')
            target = root / name
            if target.exists() and digest(target) != checksum:
                raise ValueError(f'Refusing to overwrite changed input: {target}')
            staged = temporary / name
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(data)
        # No destination files are written until every path and hash has passed.
        for name in expected:
            target = root / name
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                    stream.write((temporary / name).read_bytes())
                    local_temporary = Path(stream.name)
                local_temporary.replace(target)
    return {'files': len(expected), 'verified': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--pack', type=Path)
    actions.add_argument('--unpack', type=Path)
    actions.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = pack(args.pack) if args.pack else unpack(args.unpack) if args.unpack else {'verified_files': len(verify_inputs())}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
