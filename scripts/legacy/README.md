# Legacy research utilities

The four former root scripts live here to keep the active entry points clear.
They are retained for the historical experiments, not the current canonical
evaluation pipeline. Run them from the repository root only after reviewing
their dependencies and behavior; no downloads or inference run during cleanup.

| Script | Historical use | Limitation |
|---|---|---|
| `select_hard_videos.py` | Inspect MV-Bench-mini metadata and question categories | Downloads metadata; categories do not establish retrospective-evidence eligibility |
| `download_and_curate_25_videos.py` | Select/download the 25-video QA prototype | Uses an unpinned dataset reference; sample selection is question based |
| `evaluate_25_hard_videos.py` | SmolVLM-256M joint/chronological/reversed QA | Sparse four-frame inputs and no validated same-event revision labels |
| `aggregate_real_metrics.py` | Print mixed older experiment summaries | Heterogeneous model/protocol outputs; not a valid pooled research score |

The two path-based scripts now locate the repository root from this directory.
Their target experiments and saved outputs remain at their original paths.
The other two retain their original behavior; the aggregate script expects the
repository-root working directory. Historical source versions remain in Git.

Current results: [Qwen2.5-VL-3B archived run](../../experiments/holoassist_20/belief_revision_v1/README.md).
Current overview: [CURRENT_STATE.md](../../CURRENT_STATE.md).
