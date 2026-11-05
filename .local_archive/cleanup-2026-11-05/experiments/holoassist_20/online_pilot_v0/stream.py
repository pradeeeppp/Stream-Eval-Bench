"""Emit a visual stream one frame at a time without revealing future frames."""
import argparse
import base64
import json
import time
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent


def load(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--realtime", action="store_true", help="Sleep one second between frames")
    args = parser.parse_args()
    tasks = {t["task_id"]: t for t in load(HERE / "public_tasks.jsonl")}
    task = tasks[args.task_id]
    sources = {s["source_id"]: s for s in json.loads((HERE / "sources.json").read_text())["sources"]}
    session = sources[task["source_id"]]["session_id"]
    frame_dir = ROOT / "stream_frames" / session
    print(json.dumps({"type": "instruction", "task_id": args.task_id,
                      "instruction": task["instruction"], "frame_interval_seconds": 1}), flush=True)
    for i, frame in enumerate(sorted(frame_dir.glob("[0-9][0-9][0-9][0-9].jpg"))):
        payload = {"type": "frame", "task_id": args.task_id,
                   "time_seconds": i, "mime_type": "image/jpeg",
                   "image_base64": base64.b64encode(frame.read_bytes()).decode("ascii")}
        print(json.dumps(payload), flush=True)
        if args.realtime:
            time.sleep(1)
    print(json.dumps({"type": "end", "task_id": args.task_id}), flush=True)


if __name__ == "__main__":
    main()
