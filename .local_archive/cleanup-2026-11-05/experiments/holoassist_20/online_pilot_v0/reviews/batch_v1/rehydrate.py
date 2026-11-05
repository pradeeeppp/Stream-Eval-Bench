"""Reproduce the exact reviewed contact sheets from the shipped graph manifests.

Matching hashes refer back to the recorded review; reproduction is not a new
independent visual review. Source MP4s must already be available locally.
"""
import argparse
import json

from review_media import HERE, ROOT, cache, digest, sheets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('sources', nargs='*')
    args = parser.parse_args()
    graphs = [json.loads(line) for line in (HERE / 'evidence_graphs.reviewed.jsonl').read_text().splitlines()]
    for graph in graphs:
        source_id = graph['source_id']
        if args.sources and source_id not in args.sources:
            continue
        for material in graph['review']['material']:
            paths = sheets(source_id, material['name'], material['native_indices'],
                           width=material['display_width'], columns=material['render_columns'],
                           per_page=material['render_per_page'])
            assert len(paths) == len(material['sheets'])
            for expected in material['sheets']:
                assert digest(ROOT / expected['path']) == expected['sha256'], expected['path']
            manifest_path = cache(source_id) / 'inspections.json'
            manifest = json.loads(manifest_path.read_text())
            manifest[material['name']]['status'] = material['status']
            manifest[material['name']]['reproduced_from_published_review'] = True
            manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        print(f'{source_id}: exact reviewed sheets reproduced', flush=True)


if __name__ == '__main__':
    main()
