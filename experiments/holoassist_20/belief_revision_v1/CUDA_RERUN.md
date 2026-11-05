# Run the same 20-video evaluation on another GPU machine

Branch: `codex/holoassist-cuda-rerun`. Python 3.11+ and an NVIDIA driver are
recommended. This reruns the frozen Qwen2.5-VL-3B checkpoint, exact eight frames
per video, prompts and scoring. Larger GPUs do not automatically change the
model, resolution or sampling. Graphs remain offline annotation/provenance;
the model receives video packets, timestamps and its previous raw response.

Clone the published branch. Git LFS is not required:

```sh
git clone -b codex/holoassist-cuda-rerun https://github.com/pradeeeppp/Stream-Eval-Bench.git
cd Stream-Eval-Bench
```

## Transfer the repository and exact inputs

The Git branch contains code, labels, all 20 reviewed factual evidence graphs,
the completed Mac results and the exact evaluated frame bundle. Full source
MP4s are downloaded on demand from pinned public URLs because the repository's
Git LFS budget is exhausted. Model weights and new-run outputs are ignored.
The exact 180 input files (160 JPEG frames and 20 review sheets) are included in:

```text
experiments/holoassist_20/data/holoassist20-inputs.tar.gz
SHA256: 90c2d74e7b45a2ed6d641b6b702c71812d07bfac80ce395fef3c739ba9660caf
```

Retain the dataset attribution in `../online_pilot_v0/ATTRIBUTION.md`. Full source
MP4s and FFmpeg are unnecessary for the frozen-packet rerun when using this
bundle. After checking out the branch:

```sh
python3 experiments/holoassist_20/belief_revision_v1/input_bundle.py --unpack experiments/holoassist_20/data/holoassist20-inputs.tar.gz
python3 experiments/holoassist_20/belief_revision_v1/input_bundle.py --verify
```

The importer checks every path and SHA256 before writing, and refuses changed
existing files. To rebuild a bundle on the original machine, use `--pack PATH`.

## Download full source videos when needed

For full-video experiments or to recreate frames:

```sh
python3 experiments/holoassist_20/belief_revision_v1/download_videos.py --workers 4
python3 experiments/holoassist_20/belief_revision_v1/download_videos.py --verify-only
```

The script first validates all 20 shipped graphs against frozen case hashes.
It downloads the pinned source URLs in `sources.json`, verifies every MP4 SHA256,
resumes useful `.part` downloads, and skips already verified videos. It refuses
to overwrite changed existing videos. `--cases HA01 HB01` selects sources;
`--list` prints pinned URLs and hashes without downloading. No GPU is needed.
If the frame bundle is unavailable, run `rehydrate.py` after downloading the
source movies; exact encoder hashes must match.

## Evidence graphs are included

- Reviewed factual graphs: `online_pilot_v0/reviews/batch_v1/<ID>/evidence_graph.json`
  under `experiments/holoassist_20/` (20 files).
- Original model belief traces: `belief_revision_v1/belief_graphs/<ID>.json`
  under the same dataset directory (20 files).
- Frozen prompts, endpoint labels, capture times and graph hashes: `cases.json`.

These annotations are shipped in Git and do not need to be regenerated after
downloading videos. The downloader and audit check their hashes. The graphs
continue to serve as offline evidence/provenance, not model-visible memory.

## Install the GPU environment

```sh
python3 -m venv .venv-cuda
source .venv-cuda/bin/activate
python -m pip install --upgrade pip
```

Install a matching CUDA build of torch and torchvision using the command from
the [official PyTorch selector](https://pytorch.org/get-started/locally/) for the
target driver/platform, then install the remaining requirements:

```sh
python -m pip install -r experiments/holoassist_20/belief_revision_v1/requirements-rerun.txt
python -c 'import torch; print(torch.__version__, torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))'
```

Do not use `requirements.lock.txt` to reproduce the Mac's torch wheel on Linux.
The new runner records the actual package versions, CUDA runtime, GPU names and
memory, model placement and code snapshots. CUDA execution has not been tested
on the original Mac, which has no NVIDIA GPU.

## Validate, then start a new run

All commands below run from the repository root. Choose a unique directory under
`experiments/holoassist_20/runs/`. No archived responses are reused.

```sh
python -m unittest discover -s experiments/holoassist_20/belief_revision_v1 -p 'test_*.py'
python experiments/holoassist_20/belief_revision_v1/rerun.py --run-dir experiments/holoassist_20/runs/qwen3b-cuda-01 --device cuda:0 --dry-run
python experiments/holoassist_20/belief_revision_v1/rerun.py --run-dir experiments/holoassist_20/runs/qwen3b-cuda-01 --device cuda:0
```

The runner downloads the **recorded checkpoint revision**, performs one separate
synthetic-video smoke check, then issues 100 benchmark requests. Downloads use
the ignored local model cache; `--cache-dir PATH` changes its location and
`--offline` requires an already populated cache. One process runs the conditions
in the same seeded order as the Mac experiment. Each generation starts a fresh
context; the second sequential step receives only its predecessor's raw output.

For a bounded first batch, add `--max-calls 5`; invoke the same command without
the limit to resume. `--smoke` saves only the synthetic check. Configuration,
environment or code changes require a new run directory. Original `run.py`,
`protocol.py`, labels and Mac responses are preserved byte-for-byte.

For model sharding across visible GPUs:

```sh
CUDA_VISIBLE_DEVICES=0,1 python experiments/holoassist_20/belief_revision_v1/rerun.py --run-dir experiments/holoassist_20/runs/qwen3b-cuda-sharded-01 --device cuda:0 --device-map auto
```

This uses [Accelerate model dispatch](https://huggingface.co/docs/accelerate/en/usage_guides/big_modeling),
not parallel benchmark workers. Automatic placement may offload layers to CPU;
inspect the saved `model_placement.json`. For this 3B model, a single sufficiently
large GPU is the simpler comparison. The pinned model integration follows the
[Qwen2.5-VL Transformers API](https://huggingface.co/docs/transformers/v4.57.1/en/model_doc/qwen2_5_vl).

## Generate results and audit the run

After all 100 requests complete:

```sh
python experiments/holoassist_20/belief_revision_v1/analyze.py --run-dir experiments/holoassist_20/runs/qwen3b-cuda-01
python experiments/holoassist_20/belief_revision_v1/export_belief_graphs.py --run-dir experiments/holoassist_20/runs/qwen3b-cuda-01
python experiments/holoassist_20/belief_revision_v1/audit.py --run-dir experiments/holoassist_20/runs/qwen3b-cuda-01 --with-inputs
```

Reports and belief graphs are written inside that new run. `--with-inputs` checks
selected images without requiring full movies; `--with-media` additionally
checks the source MP4s. JSON/schema failures remain model outcomes. Runtime
failures are saved separately and do not count as semantic mistakes. The same
17 provisional targets, 14 clean correction opportunities and 3 diagnostic-only
tasks apply. A larger GPU does not remove the label-balance confound described
in the original failure report.
