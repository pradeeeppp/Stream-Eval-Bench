# Experiment index

For the research question and current evidence, read [CURRENT_STATE.md](../CURRENT_STATE.md).
Experiments below are not interchangeable replications and should not be pooled
into one aggregate accuracy or model-call count.

| Directory | Classification | Starting point |
|---|---|---|
| `holoassist_20/belief_revision_v1/` | Current archived local Qwen2.5-VL-3B diagnostic; 100 saved requests | [Protocol/results](holoassist_20/belief_revision_v1/README.md) |
| `holoassist_20/belief_revision_v1/taxonomy/` | Current post-hoc failure analysis; no new model calls | [Taxonomy](holoassist_20/belief_revision_v1/taxonomy/README.md) |
| `holoassist_20/online_pilot_v0/` | Offline source metadata and reviewed factual graphs | [Attribution](holoassist_20/online_pilot_v0/ATTRIBUTION.md) |
| `two_clip_diagnostic/` | Completed hosted successful-update comparison | [Results](two_clip_diagnostic/RESULTS.md) |
| `intervening_video/` | Completed hosted extension; shared control failure | [Results](intervening_video/RESULTS.md) |
| `format_controls/` | Six completed endpoint recognition controls | [Results](format_controls/RESULTS.md) |
| `fixed_hypothesis/` | Completed controlled two-source prototype; not a replicated causal result | [Findings](fixed_hypothesis/FINDINGS.md) |
| `source_suitability/` | Three-source screening audit | [Admission limits](source_suitability/README.md) |
| `replay_candidates/` | Screening and inconclusive NBA diagnostic | [Results](replay_candidates/RESULTS.md) |
| `evidence_revision_pilot/direct_revision/` | Corrected controlled still-image pilot | [Results and invalidation](evidence_revision_pilot/direct_revision/RESULTS.md) |
| `evidence_revision_pilot/streaming_trial/` | Recovered partial/historical work | [Recovery record](evidence_revision_pilot/provenance/RECOVERY.md) |
| `hf_hard_prototype/` | Legacy SmolVLM-256M sparse-video QA, 25 examples | [Scope](hf_hard_prototype/README.md) |
| `qwen_benchmarks/` | Four model-labelled files whose actual agents are mock oracles | [Provenance correction](qwen_benchmarks/README.md) |
| `disentanglement_proof/` | Legacy gate diagnostic; upstream controls fail | [Scope](disentanglement_proof/README.md) |
| `suite_results/` | Mock-agent harness outputs | Software checks only |

Frozen runs retain their original code/data paths. New inference belongs in a
separate output directory with its own model/backend manifest. See the
[CUDA guide](holoassist_20/belief_revision_v1/CUDA_RERUN.md). Older root utility
scripts moved to [scripts/legacy](../scripts/legacy/README.md).
