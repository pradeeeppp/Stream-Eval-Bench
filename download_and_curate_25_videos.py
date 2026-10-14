"""Curates and downloads 25 hard video understanding tasks from Hugging Face MV-Bench-mini."""

import ast
import csv
import json
import os
import pathlib
import time
from huggingface_hub import hf_hub_download
import decord

REPO_ROOT = pathlib.Path(__file__).resolve().parent
OUTPUT_DIR = REPO_ROOT / "experiments" / "hf_hard_prototype"
VIDEOS_DIR = OUTPUT_DIR / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Fetch metadata
print(">>> Fetching MV-Bench-mini metadata from Hugging Face...")
csv_path = hf_hub_download(
    repo_id="firstep-ai/MV-Bench-mini",
    filename="resampled_data.csv",
    repo_type="dataset",
)

with open(csv_path, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print(f"Total candidate rows available: {len(rows)}")

# 2. Categorize and select 25 hard tasks
# 6 distinct challenge categories:
# - Multi-Object Occlusion Tracking (5)
# - Action & Event Counting (5)
# - Temporal Sequence & Action Order (4)
# - Object Possession & State Tracking (4)
# - Action Prediction & Horizon (4)
# - State Change & Physical Dynamics (3)

categories_targets = {
    "Multi-Object Occlusion Tracking": (
        lambda q: "multiple similar objects" in q.lower() or "occlusion game" in q.lower(),
        5,
    ),
    "Action & Event Counting": (
        lambda q: "how many times" in q.lower() or "count" in q.lower(),
        5,
    ),
    "Temporal Sequence & Action Order": (
        lambda q: "when in the video" in q.lower() or "when does the action" in q.lower() or "sequence" in q.lower(),
        4,
    ),
    "Object Possession & State Tracking": (
        lambda q: "which object" in q.lower() or "put down" in q.lower() or "held the phone" in q.lower() or "took the phone" in q.lower(),
        4,
    ),
    "Action Prediction (Future Horizon)": (
        lambda q: "what will the person do next" in q.lower(),
        4,
    ),
    "State Change & Physical Dynamics": (
        lambda q: "scenes in the video change" in q.lower() or "temperature" in q.lower() or "turn on" in q.lower(),
        3,
    ),
}

selected_items = []
used_ids = set()

for cat_name, (predicate, target_count) in categories_targets.items():
    cat_items = []
    for r in rows:
        vid_id = r["relpath"]
        if vid_id in used_ids:
            continue
        if predicate(r["question"]):
            cat_items.append(r)
    
    # Pick the target count
    chosen = cat_items[:target_count]
    for c in chosen:
        used_ids.add(c["relpath"])
        selected_items.append({
            "category": cat_name,
            "id": c["relpath"].replace(".mp4", ""),
            "filename": c["relpath"],
            "question": c["question"],
            "candidates": ast.literal_eval(c["candidates"]),
            "answer": c["answer"],
        })
    print(f"  • {cat_name:<38}: selected {len(chosen)} / target {target_count}")

print(f"\nTotal selected hard benchmark tasks: {len(selected_items)}")
assert len(selected_items) == 25, f"Expected 25 tasks, got {len(selected_items)}"

# 3. Download the 25 videos from Hugging Face
print("\n>>> Downloading 25 video files from Hugging Face Hub...")
final_records = []

for idx, item in enumerate(selected_items, 1):
    fname = item["filename"]
    target_path = VIDEOS_DIR / fname
    
    t0 = time.time()
    if not target_path.exists():
        dl_path = hf_hub_download(
            repo_id="firstep-ai/MV-Bench-mini",
            filename=fname,
            repo_type="dataset",
        )
        # Copy or hardlink to VIDEOS_DIR
        import shutil
        shutil.copy2(dl_path, target_path)
    dl_time = time.time() - t0
    
    # Inspect video with decord
    vr = decord.VideoReader(str(target_path))
    num_frames = len(vr)
    h, w, c = vr[0].shape
    
    record = {
        "index": idx,
        "category": item["category"],
        "id": item["id"],
        "filename": fname,
        "video_path": str(target_path.relative_to(REPO_ROOT)),
        "frames_count": num_frames,
        "resolution": f"{w}x{h}",
        "question": item["question"],
        "candidates": item["candidates"],
        "ground_truth_answer": item["answer"],
    }
    final_records.append(record)
    print(f"  [{idx:2d}/25] {fname:<18} | {w}x{h} ({num_frames:3d} frames) | {item['category']}")

manifest_path = OUTPUT_DIR / "manifest.json"
manifest_path.write_text(json.dumps(final_records, indent=2), encoding="utf-8")
print(f"\nSaved 25-video hard benchmark manifest to {manifest_path}")
