# Qwen2.5-VL-3B: twenty-video belief revision comparison

This experiment compares belief revision on twenty reviewed HoloAssist recordings
using the official
Qwen2.5-VL-3B-Instruct checkpoint locally on Apple MPS. The checkpoint revision,
dependencies, device and inference settings are recorded rather than inferred
from the PDF. Exact reproduction of the PDF's undocumented settings is not claimed.

For a fresh run on another machine, follow [CUDA_RERUN.md](CUDA_RERUN.md).
It uses a separate output directory, a pinned checkpoint and transferable exact
inputs; the completed Mac run remains available here for comparison.

Start with [RESULTS.md](RESULTS.md) for the aggregate comparison and links to all
twenty per-video reports. [analysis.json](analysis.json) contains machine-readable
scores. [PLAN.md](PLAN.md) describes the protocol; [cases.json](cases.json) freezes
the task predicates, provisional gold labels, capture timestamps and input hashes.

The [failure analysis](FAILURE_ANALYSIS.md) follows the supplied reference's three
research questions and includes failure traces and an all-video appendix.
Read the [six-page PDF with evidence frames](../../../output/pdf/HOLOASSIST_20_FAILURE_ANALYSIS_EN.pdf).

The [detailed failure taxonomy](taxonomy/README.md) provides exclusive per-unit
categories, [all-video assignments](taxonomy/FINDINGS.md), and a separate
[data, interface, design and measurement gap register](taxonomy/GAPS.md).
It classifies the archived traces without changing the original scoring protocol.

## Inputs and experiment

Each video supplies two event-centered packets, each containing four native
frames. Packet A ends at the reviewed prior anchor. Packet B starts at the
reviewed positive anchor. All 160 selected frames were visually checked before
benchmark inference. The same eight frames per video enter three conditions:

| Condition | Requests | Visual input and external memory |
|---|---|---|
| Joint | 1 | A and B together; no memory |
| Chronological | 2 | A, then B with the exact first response |
| Reversed arrival | 2 | B, then A with the exact first response |

Five requests per video produce 100 benchmark requests. There is one greedy
trial per condition. Each request starts a fresh model context. Sequential
conditions retain only the preceding raw response, with no earlier images or
hidden state. Model outputs contain earlier/latest state values and supporting
packet IDs. The latest target follows capture time, including after older A
arrives. Gold labels and graph descriptions are not included in prompts.

Seventeen original targets have provisional labels. HA05, HA09 and HA10 retain
raw outputs but are excluded from correctness rates because their task definitions
need adjudication. HA06, HA08 and HB06 have an unknown prior state even after A
is inspected, leaving fourteen clean unknown-to-known correction opportunities.
All labels are assistant judgments awaiting independent annotation.

## Recorded evidence

- `responses/HA01.json` through `responses/HB10.json`: exact prompts, raw responses,
  verbatim external memory, packet/frame hashes, video tensor grids, timing and scores.
- `model_manifest.json`: official checkpoint and pinned revision.
- `execution_manifest.json`: hashes of the frozen cases, protocol and runner;
  device, generation configuration and installed library versions.
- `execution_summary.json`: final request counts, generation time, failures and
  output-limit checks.
- `requirements.lock.txt`: the local environment's installed package versions.
- `belief_graphs/<video>.json`: twenty graphs linking evidence packets, fixed capture-time
  claims, model requests, expressed beliefs and model citations. Model citations
  are explicitly marked as assertions; they are not verified support edges.
- `infrastructure_smoke.json`: a separate solid-red synthetic-video GPU check,
  explicitly excluded from benchmark counts.
- `audit_report.json`: source/frame/graph hashes, request isolation, memory
  consistency, completion and independently recomputed score checks.
- `media/`: exact extracted frames and reviewed contact sheets; ignored by git.

## Running and checking

Inspect and recompute the saved results with Python 3, without model weights,
videos or additional packages. Run from the repository root:

```sh
python3 -m unittest discover -s experiments/holoassist_20/belief_revision_v1 -p 'test_*.py'
python3 experiments/holoassist_20/belief_revision_v1/audit.py
python3 experiments/holoassist_20/belief_revision_v1/analyze.py
python3 experiments/holoassist_20/belief_revision_v1/export_belief_graphs.py
```

The default audit checks committed manifests, graphs, exact requests and score
consistency. It explicitly reports that local media were not checked. Add
`--with-media` to verify all source videos, frames and contact sheets. Audits print
to stdout; `--output PATH` saves a new report. The recorded `audit_report.json`
documents the original full local-media audit.

### Restore media for the archived run

Source URLs and local paths are pinned in
[`sources.json`](../online_pilot_v0/sources.json); see the
[dataset attribution](../online_pilot_v0/ATTRIBUTION.md). Use `download_videos.py`
to fetch the pinned source MP4s and check their hashes against the included
evidence graphs. The exact evaluated frames are included in
`../data/holoassist20-inputs.tar.gz`; see the CUDA guide to unpack them without
re-encoding. To recreate frames from the MP4s with FFmpeg:

```sh
python3 -m venv .venv-qwen3b
.venv-qwen3b/bin/python -m pip install -r experiments/holoassist_20/belief_revision_v1/requirements.lock.txt
python3 experiments/holoassist_20/belief_revision_v1/download_videos.py
.venv-qwen3b/bin/python experiments/holoassist_20/belief_revision_v1/rehydrate.py
python3 experiments/holoassist_20/belief_revision_v1/audit.py --with-media
```

`rehydrate.py` verifies exact JPEG and contact-sheet hashes before restoring
missing files. It refuses changed existing files and never rewrites labels or
review status. Encoder or Pillow differences can cause a hash mismatch.

`run.py`, `protocol.py`, `cases.json` and raw responses are preserved exactly as
executed; their recorded hashes are part of the audit. `run.py` is the archived
Mac entry point. Use `rerun.py` and a fresh `--run-dir` for new measurements, as
described in [CUDA_RERUN.md](CUDA_RERUN.md). It downloads the pinned checkpoint
and keeps all new outputs separate. Preserve the published responses and
manifests. `export_belief_graphs.py --jsonl` optionally produces an ignored
combined copy of the per-video graphs.

To rebuild the failure report, install ReportLab in a separate reporting
environment, restore media for HA01/HB01/HA08, and run `build_failure_report.py`.
It reads the frozen responses, validates scores and image hashes, and writes the
Markdown analysis and PDF without changing execution artifacts.

## Scope

This tests a two-packet external-memory diagnostic, not full continuous native
video ingestion. It follows the PDF's two-clip comparison structure rather than
its separate uniform whole-video sampling experiment. An unchanged value can
acquire new evidence; final correctness alone is not a clean revision success.
Preservation is measured only where the earlier prediction was already correct.
Packet IDs measure expressed evidence association, not an identified internal
memory mechanism. One trial and provisional labels support case observations,
not population reliability or claims of calibrated confidence.
