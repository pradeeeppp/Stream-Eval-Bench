"""Score timestamped alerts for the combined 20-video online pilot.

Predictions JSONL: {"task_id":"stream_alert_01","alert_seconds":8.0}
Multiple alerts for a task are allowed; the earliest one determines false alarms.
"""
import argparse
import json
from pathlib import Path


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def score(tasks, predictions):
    by_id = {t["task_id"]: t for t in tasks}
    alerts = {key: [] for key in by_id}
    for p in predictions:
        key = p.get("task_id")
        if key not in by_id:
            raise ValueError(f"Unknown task_id: {key}")
        t = p.get("alert_seconds")
        if not isinstance(t, (int, float)) or isinstance(t, bool):
            raise ValueError(f"Invalid alert_seconds for {key}")
        alerts[key].append(float(t))
    rows = []
    for key, task in by_id.items():
        first = min(alerts[key]) if alerts[key] else None
        pre = task["pre_event_checkpoint_seconds"]
        positive = task["first_positive_sample_seconds"]
        deadline = task["deadline_seconds"]
        # The transition is not frame-exactly labeled; do not call it false.
        status = ("miss" if first is None else
                  "early_false_alarm" if first <= pre else
                  "transition_unscored" if first < positive else
                  "on_time" if first <= deadline else "late")
        rows.append({"task_id": key, "first_alert_seconds": first,
                     "status": status, "latency_from_positive_seconds":
                     None if first is None else round(first - positive, 3),
                     "pre_event_checkpoint_seconds": pre})
    n = len(rows)
    return {"n_tasks": n, "on_time": sum(r["status"] == "on_time" for r in rows),
            "early_false_alarms": sum(r["status"] == "early_false_alarm" for r in rows),
            "transition_unscored": sum(r["status"] == "transition_unscored" for r in rows),
            "late": sum(r["status"] == "late" for r in rows),
            "misses": sum(r["status"] == "miss" for r in rows),
            "on_time_rate": sum(r["status"] == "on_time" for r in rows) / n if n else 0,
            "per_task": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions", help="JSONL of task_id and alert_seconds")
    parser.add_argument("--tasks", default=str(Path(__file__).with_name("tasks.jsonl")))
    args = parser.parse_args()
    print(json.dumps(score(load_jsonl(args.tasks), load_jsonl(args.predictions)), indent=2))
