# 00 — Already implemented (HoloAssist, code-ready)

These are the only usecases with runnable `stream_eval` code + local packets. Use as reference for expanding 01–14.

## 00a. Table tray — `table_assembly_tray`
* Code: `stream_eval/usecases/table_assembly.py`, packets `experiments/two_clip_diagnostic/earlier.mp4`, `later.mp4`
* Source: `z060-june-28-22-gladom_assemble.mp4` ([HF](https://huggingface.co/datasets/lmms-lab/EgoIT-99K/resolve/a57f1f2078a7b01ea87014050fdb3afe169e54f1/HoloAssist/video/z060-june-28-22-gladom_assemble.mp4)), earlier ~72s tray OFF (`no`), latest tray ON (`yes`)
* Schema `{earlier, latest}`, delayed schedule `[1,0]` (later first). Tests RQ3 preserve-live par excellence.

## 00b. Camera parts — `camera_detachment` / `camera_mount_status`
* Code: `stream_eval/usecases/camera_detachment.py`, `camera_mount.py`
* Source: `z176-sep-05-22-dslr.mp4` ([HF](https://huggingface.co/datasets/lmms-lab/EgoIT-99K/resolve/a57f1f2078a7b01ea87014050fdb3afe169e54f1/HoloAssist/video/z176-sep-05-22-dslr.mp4)), E1@10.01s lens vs E2@17.02s cap (`experiments/fixed_hypothesis/cases.json`). RQ1 bind test.

## 00c. Printer display — `printer_display_tracking`
* Code: `stream_eval/usecases/printer_operations.py`
* Source: `R071-19July-BigPrinter.mp4` ([HF](https://huggingface.co/datasets/lmms-lab/EgoIT-99K/resolve/a57f1f2078a7b01ea87014050fdb3afe169e54f1/HoloAssist/video/R071-19July-BigPrinter.mp4)), E1@19.28s illuminated (masked) vs E2@42.63s dark. Joint `E2=dark` correct, Update `E1=illuminated` wrong on byte-identical image — RQ2 anchor case.

## 00d. Table components — `table_components_tracking`
* Code: `stream_eval/usecases/table_components.py` — leg fastening vs tray placement, multi-angle delayed arrival.

## 25-probe set (downloaded)
* `experiments/hf_hard_prototype/videos/` (25 mp4), `manifest.json`, `evaluation_results.json`, runners `download_and_curate_25_videos.py`, `evaluate_25_hard_videos.py`. Model `SmolVLM-256M`, macro Joint 32% / Chrono 32% / Delayed 36% / Gap -0.04.

## To implement a new case like these
Copy `table_assembly.py`: define `packets` (capture_start/end + video_path/frames), `get_default_delayed_schedule` (e.g. `DelayedSchedule(order_indices=[1,0])`), `get_expected_state` per condition/step, `evaluate_revision` (historical_update + recency_preserved). Register via `register_usecase`.
Status: `implemented`.
