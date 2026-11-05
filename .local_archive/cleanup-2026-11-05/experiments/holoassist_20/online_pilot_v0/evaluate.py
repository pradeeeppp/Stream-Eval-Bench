"""Run a JSONL model adapter with a per-frame handshake, then score its alerts.

Adapter protocol: for every input JSON line, output exactly one JSON line with
{"alert": true} or {"alert": false}. Future frames are withheld until reply.
"""
import argparse
import base64
import json
import select
import subprocess
import time
from pathlib import Path

from score import load_jsonl, score

HERE = Path(__file__).parent
ROOT = HERE.parent


def reply(process, packet, timeout):
    process.stdin.write(json.dumps(packet) + "\n")
    process.stdin.flush()
    ready, _, _ = select.select([process.stdout], [], [], timeout)
    if not ready:
        raise TimeoutError("Adapter did not acknowledge a stream packet")
    line = process.stdout.readline()
    if not line:
        raise RuntimeError("Adapter exited without a response")
    obj = json.loads(line)
    if type(obj.get("alert")) is not bool:
        raise ValueError("Adapter reply must contain a boolean alert")
    return obj["alert"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["development", "evaluation", "all"], default="all")
    parser.add_argument("--timeout-seconds", type=float, default=60)
    parser.add_argument("--output", default="predictions.jsonl")
    parser.add_argument("adapter", nargs=argparse.REMAINDER,
                        help="Adapter command after --, e.g. -- python3 adapter.py")
    args = parser.parse_args()
    command = args.adapter[1:] if args.adapter and args.adapter[0] == "--" else args.adapter
    if not command:
        parser.error("Provide an adapter command after --")
    public = load_jsonl(HERE / "public_tasks.jsonl")
    sources = {s["source_id"]: s for s in json.loads((HERE / "sources.json").read_text())["sources"]}
    selected = [t for t in public if args.split == "all" or t["split"] == args.split]
    predictions, traces = [], []
    for task in selected:
        session = sources[task["source_id"]]["session_id"]
        frame_dir = ROOT / "stream_frames" / session
        frames = sorted(frame_dir.glob("[0-9][0-9][0-9][0-9].jpg"))
        if not frames:
            raise FileNotFoundError(frame_dir)
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True, bufsize=1)
        started = time.monotonic()
        try:
            reply(process, {"type": "instruction", **task}, args.timeout_seconds)
            for i, frame in enumerate(frames):
                packet = {"type": "frame", "task_id": task["task_id"],
                          "time_seconds": i, "mime_type": "image/jpeg",
                          "image_base64": base64.b64encode(frame.read_bytes()).decode("ascii")}
                if reply(process, packet, args.timeout_seconds):
                    predictions.append({"task_id": task["task_id"], "alert_seconds": i})
                    break
            traces.append({"task_id": task["task_id"],
                           "wall_seconds": round(time.monotonic() - started, 3)})
        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
    output = Path(args.output)
    output.write_text("".join(json.dumps(p) + "\n" for p in predictions))
    gold = [t for t in load_jsonl(HERE / "tasks.jsonl") if t["task_id"] in {x["task_id"] for x in selected}]
    report = score(gold, predictions)
    report["adapter_command"] = command
    report["split"] = args.split
    report["wall_traces"] = traces
    output.with_suffix(".report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("per_task", "wall_traces")}, indent=2))


if __name__ == "__main__":
    main()
