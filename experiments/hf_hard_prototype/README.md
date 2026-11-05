# Legacy 25-video QA prototype

The saved `evaluation_results.json` identifies HuggingFaceTB/SmolVLM-256M-Instruct,
with 25 questions from the MV-Bench-mini source selection. Recorded final correct
answers are joint 8/25, chronological 8/25 and reversed 9/25.

This is a sparse four-frame video-QA comparison. It does not contain independently
validated same-event retrospective-revision episodes and is not the Qwen2.5-VL-3B
experiment. The source manifest lacks pinned source revisions and content hashes,
and its labels/answer normalization have not been re-audited for the current claim.
Treat these as historical recorded QA scores, not a validated current benchmark.

The source videos, manifest and results remain at their original locations.
Former root selection/download/evaluation helpers now live in
[scripts/legacy](../../scripts/legacy/README.md). They can download data or run
inference when explicitly executed; cleanup did not execute them.

For current work, use [CURRENT_STATE.md](../../CURRENT_STATE.md) and the
[new-episode admission protocol](../../docs/DATASET_EXPANSION.md).
