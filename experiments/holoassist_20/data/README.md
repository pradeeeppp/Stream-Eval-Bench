# Evaluation data

`holoassist20-inputs.tar.gz` contains the exact evaluated inputs: 160 native-frame
JPEGs and 20 reviewed contact sheets. SHA256:

```text
90c2d74e7b45a2ed6d641b6b702c71812d07bfac80ce395fef3c739ba9660caf
```

From the repository root:

```sh
python3 experiments/holoassist_20/belief_revision_v1/input_bundle.py --unpack experiments/holoassist_20/data/holoassist20-inputs.tar.gz
```

The 20 reviewed factual evidence graphs are shipped in
`../online_pilot_v0/reviews/batch_v1/<ID>/evidence_graph.json`. The 20 original
model belief graphs are in `../belief_revision_v1/belief_graphs/<ID>.json`.
All graph files remain available independently of the source movies.

Download the full source MP4s on demand:

```sh
python3 experiments/holoassist_20/belief_revision_v1/download_videos.py
```

Their exact SHA256 values, pinned mirror URLs and recorded video properties
are in `../online_pilot_v0/sources.json`; the downloader cross-checks source
hashes against the shipped graphs before downloading. Source movies are ignored
by Git and do not consume the repository's exhausted LFS budget.
The frame bundle allows the frozen-packet evaluation to run without downloading
the full source MP4s or re-encoding any frames.

See `../online_pilot_v0/ATTRIBUTION.md` for dataset attribution and license notes,
`LICENSE-CDLA-Permissive-2.0.txt` for the publisher-specified data license, and
`../belief_revision_v1/CUDA_RERUN.md` for the GPU rerun procedure.
