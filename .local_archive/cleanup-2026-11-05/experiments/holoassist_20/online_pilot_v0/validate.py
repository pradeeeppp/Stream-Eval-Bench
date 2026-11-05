"""Check source integrity and task consistency before any model evaluation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent


def lines(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def main():
    sources = json.loads((HERE / "sources.json").read_text())["sources"]
    tasks = lines(HERE / "tasks.jsonl")
    public = lines(HERE / "public_tasks.jsonl")
    graphs = lines(HERE / "evidence_graphs.jsonl")
    assert len(sources) == len(tasks) == len(public) == 20
    assert len(graphs) == 20
    assert len({s["session_id"] for s in sources}) == 20
    assert len({s["source_id"] for s in sources}) == 20
    assert len({t["task_id"] for t in tasks}) == 20
    by_source = {s["source_id"]: s for s in sources}
    for source in sources:
        video = ROOT / source["local_path"]
        assert video.is_file(), video
        assert hashlib.sha256(video.read_bytes()).hexdigest() == source["sha256"], video
        frames = sorted((ROOT / "stream_frames" / source["session_id"]).glob("[0-9][0-9][0-9][0-9].jpg"))
        assert abs(len(frames) - source["duration_seconds"]) <= 1.5, source["session_id"]
        assert all(f.stat().st_size > 0 for f in frames)
    for task, exposed in zip(tasks, public):
        assert task["task_id"] == exposed["task_id"]
        assert task["source_id"] in by_source
        assert 0 <= task["pre_event_checkpoint_seconds"] < task["first_positive_sample_seconds"] <= task["deadline_seconds"]
        assert task["deadline_seconds"] < by_source[task["source_id"]]["duration_seconds"]
        frame = ROOT / task["evidence_frame"]
        assert frame.is_file(), frame
        assert int(frame.stem) - 1 == task["first_positive_sample_seconds"]
        assert "first_positive_sample_seconds" not in exposed
        assert "evidence_frame" not in exposed
    by_graph = {g["task_id"]: g for g in graphs}
    assert len(by_graph) == 20
    for task in tasks:
        graph = by_graph[task["task_id"]]
        nodes = {n["id"]: n for n in graph["nodes"]}
        assert set(nodes) == {"before", "event", "alert"}
        assert graph["edges"] == [["before", "event"], ["event", "alert"]]
        assert nodes["before"]["second"] == task["pre_event_checkpoint_seconds"]
        assert nodes["event"]["second"] == task["first_positive_sample_seconds"]
        assert nodes["event"]["path"] == task["evidence_frame"]
        assert nodes["event"]["observation"] == task["evidence_rationale"]
        assert nodes["alert"]["deadline_second"] == task["deadline_seconds"]
        assert all((ROOT / nodes[k]["path"]).is_file() for k in ("before", "event"))
    print("VALID: 20 distinct sources, 20 bounded tasks and evidence graphs, matching hashes, private labels separate")


if __name__ == "__main__":
    main()
