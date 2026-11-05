"""Build a minimal private evidence graph for each alert task."""
import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent


def main():
    sources = {s["source_id"]: s for s in json.loads((HERE / "sources.json").read_text())["sources"]}
    tasks = [json.loads(line) for line in (HERE / "tasks.jsonl").read_text().splitlines() if line.strip()]
    graphs = []
    for task in tasks:
        session = sources[task["source_id"]]["session_id"]
        before = task["pre_event_checkpoint_seconds"]
        confirmed = task["first_positive_sample_seconds"]
        before_frame = f"full_review/{session}/{before + 1:04d}.jpg"
        event_frame = task["evidence_frame"]
        if not (ROOT / before_frame).is_file() or not (ROOT / event_frame).is_file():
            raise FileNotFoundError(session)
        graphs.append({
            "task_id": task["task_id"],
            "nodes": [
                {"id": "before", "type": "frame", "second": before, "path": before_frame},
                {"id": "event", "type": "confirmed_event", "second": confirmed,
                 "path": event_frame, "observation": task["evidence_rationale"]},
                {"id": "alert", "type": "decision", "deadline_second": task["deadline_seconds"]},
            ],
            "edges": [["before", "event"], ["event", "alert"]],
        })
    (HERE / "evidence_graphs.jsonl").write_text("".join(json.dumps(g) + "\n" for g in graphs))
    print(f"Built {len(graphs)} evidence graphs")


if __name__ == "__main__":
    main()
