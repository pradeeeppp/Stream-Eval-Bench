# Stream-Eval-Bench

Stream-Eval-Bench asks whether a video model can use late-arriving evidence to
correct what it knows about the past, apply that evidence to the correct
historical event, and preserve unrelated facts and already established recent
states. An event remains fixed; the model's knowledge of it can change.

## Start here

| Document | Purpose |
|---|---|
| [CURRENT_STATE.md](CURRENT_STATE.md) | Canonical handoff: work completed, results, limitations and next steps |
| [RESEARCH_QUESTIONS.md](RESEARCH_QUESTIONS.md) | Active questions and evidence required to answer them |
| [Dataset expansion](docs/DATASET_EXPANSION.md) | Candidate sources, admission gates, controls and collection stages |
| [Experiment index](experiments/README.md) | Completed, historical, inconclusive and mock work |
| [Failure taxonomy](experiments/holoassist_20/belief_revision_v1/taxonomy/README.md) | Exclusive outcome rules, all-video assignments and research gaps |

## Current measured result

The archived HoloAssist experiment contains **100 actual Qwen2.5-VL-3B requests
across 20 recordings**, with exact inputs, raw outputs and a pinned checkpoint.
Seventeen targets are provisionally scored; three require adjudication. This is
a sampled two-packet diagnostic with prior-response memory, not a completed
natural-event-revision benchmark. Gold evidence graphs were used offline and
were not supplied as model memory.

Read the [results](experiments/holoassist_20/belief_revision_v1/RESULTS.md),
[failure-analysis PDF](output/pdf/HOLOASSIST_20_FAILURE_ANALYSIS_EN.pdf),
[protocol](experiments/holoassist_20/belief_revision_v1/README.md), and
[exact-input data instructions](experiments/holoassist_20/data/README.md).
For a new measured GPU run, use the separate
[CUDA rerun procedure](experiments/holoassist_20/belief_revision_v1/CUDA_RERUN.md).

Four older files named for Qwen 7B/72B contain mock-oracle outputs. Their
[provenance correction](experiments/qwen_benchmarks/README.md) explains why they
are not model measurements. No novelty or streaming-specific failure mechanism
has been established by the current pilots.

## Repository map

| Location | Role |
|---|---|
| `stream_eval/` | Generic streaming schedule/agent environment and legacy use cases |
| `tests/` | Environment and benchmark-provenance checks |
| `experiments/holoassist_20/belief_revision_v1/` | Frozen local run, reports, taxonomy, audits and fresh-run tools |
| `experiments/` | Other experiments, each with its own scope and provenance |
| `datasets/` | New-episode template and candidate-record conventions |
| `docs/` | Dataset admission and historical planning records |
| `scripts/legacy/` | Older root utilities retained for historical work |
| `output/pdf/` | Shareable report artifacts |

The older root research filenames for the synthesis, decision and literature
plan remain as links to [historical snapshots](docs/history/README.md).
Source recordings, model caches, environments and scratch/recovery files stay
outside the normal tracked work. The exact evaluated input bundle and legacy
25-video assets are intentional tracked data; their reports specify the scope.

## Verify saved work without model inference

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m unittest discover -s experiments/holoassist_20/belief_revision_v1 -p 'test_*.py'
python3 -m unittest discover -s experiments/holoassist_20/belief_revision_v1/taxonomy -p 'test_*.py'
python3 experiments/holoassist_20/belief_revision_v1/audit.py
```

The audit defaults to committed artifacts; media checks require restored inputs.
See the experiment README for input/source verification and deterministic report
regeneration. Preserve frozen outputs and put every new run in a new directory.

## Generic environment smoke check

```sh
python3 -m pip install -e .
stream-eval --usecase table_assembly_tray --condition all --agent mock-oracle
```

This exercises software with known mock answers. It measures no model ability.
The generic Qwen runner requires explicit `--backend` selection; mock reports
identify the real agent, use `model_name=null` and default to an ignored mock-run
directory. Its legacy aggregate metrics are not the canonical 20-video scorer.

See [third-party provenance](THIRD_PARTY.md) and the experiment-specific data
notices. Original project code is MIT; dataset/model/reference materials retain
their own terms.
