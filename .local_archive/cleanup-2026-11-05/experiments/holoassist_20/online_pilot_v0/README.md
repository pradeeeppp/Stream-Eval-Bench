# HoloAssist 20-video online alert pilot (v0.1)

This is the **single entry point for both ten-video batches**: 20 distinct HoloAssist sessions, one visual alert task per video, six development tasks and 14 internal evaluation tasks. The `HA` IDs came from batch one and `HB` IDs from batch two. All public instructions, private pilot labels, source metadata, evaluation code and scoring code are together here.

## Files and media

- `sources.json`: all 20 source sessions, pinned URLs, SHA-256 hashes, metadata and rights notes.
- `public_tasks.jsonl`: model-facing instructions and stream settings, with gold times omitted.
- `tasks.jsonl`: private pilot labels, evidence frames and scoring windows.
- `evidence_graphs.jsonl`: one private three-node graph per task: before frame → confirmed event → alert. Regenerate with `python3 build_evidence_graphs.py`.
- `prepare_media.py`: verifies or fetches source videos, extracts 1 FPS 640-pixel model frames, and keeps only the 40 cited 240-pixel evidence frames.
- `stream.py`, `evaluate.py`, `score.py`, `validate.py`: stream, run, score and check the combined pilot.

The local `videos/` directory contains all 20 source videos. `stream_frames/` contains model input frames; `full_review/` contains only the two cited evidence frames per task. These media directories are ignored by Git. Earlier annotation drafts and selection notes are retained in `../provenance/`. On another machine, run `prepare_media.py` to rehydrate media from the pinned source URLs.

## Run

From this directory:

```bash
python3 prepare_media.py
python3 validate.py
python3 stream.py stream_alert_01 > /tmp/holoassist20_stream.jsonl
python3 evaluate.py --split development --output /tmp/holoassist20_predictions.jsonl -- python3 example_adapter.py
python3 score.py /path/to/predictions.jsonl
```

The second-batch task IDs are `stream_alert_b2_01` through `stream_alert_b2_10`. For the supplied evaluator, an adapter receives the instruction and then one base64 JPEG packet at a time. It must reply to each packet with one JSON line containing `{"alert": true}` or `{"alert": false}` before seeing the next frame. The adapter must not access source MP4s, future frames, `tasks.jsonl` or `evidence_graphs.jsonl`.

The graphs document annotation provenance. `before` is the checked pre-event frame; `event` is the first clearly positive sampled frame; `alert` is the decision with its deadline. They do not establish exact onset, causal mechanism or later evidence-revision behavior. The old duplicate graph fields have been removed from `tasks.jsonl`.

Scoring uses source-video seconds. An alert at or before the pre-event checkpoint is early; an alert from the first clearly positive sample through its deadline is on time. The intervening transition is unscored because exact onset is not established. The earliest alert determines the outcome. Compare wall-clock latency separately under a fixed model budget.

## Status

The [all-video evidence-graph review](reviews/batch_v1/README.md) applies the
[improvement plan](reviews/PLAN.md) to all 20 videos, with typed graphs,
native-frame anchors and verified packet/source timestamp mappings. The
[status table](reviews/batch_v1/STATUS.md) includes three task-definition issues
and timing discrepancies. These are single-assistant proposals; v0 labels and
scoring have not been migrated. The earlier
[DSLR sample review](reviews/stream_alert_01/README.md) is retained for provenance.

These are **single-reviewer, 1 FPS pilot labels**. Each event has a checked pre-event frame and clearly positive frame, but native-rate boundary review, independent annotation, adjudication and model baselines remain outstanding. This package supports an internal online-alert comparison; it does not yet establish publication-ready ground truth or a retrospective evidence-revision benchmark.

The [official HoloAssist project](https://holoassist.github.io/) states CDLA-Permissive 2.0. The videos here came from a pinned EgoIT-99K rehost and have not been byte-matched to the official archive. The shareable package contains labels, hashes, provenance and code, not MP4s or extracted frames. Confirm original-source equivalence and notice requirements before distributing media.

The superseded ten-video batch directories have been removed. This is the only active benchmark package.
