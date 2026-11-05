"""Verify HA01 review anchors and timing; rehydrate cited native frames locally.

Requires Python's standard library, ffmpeg, ffprobe and the pinned local MP4.
Does not change the pilot's tasks, scores or three-node graphs.
"""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def run(*args):
    return subprocess.check_output(args, text=True)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def frame_hashes(video, vf, count):
    output = run("ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
                 "-map", "0:v:0", "-an", "-vf", vf, "-frames:v", str(count),
                 "-fps_mode", "passthrough", "-f", "framemd5", "-")
    return [line.split(",")[-1].strip() for line in output.splitlines()
            if line and not line.startswith("#")]


def main():
    graph = json.loads((HERE / "evidence_graph.json").read_text())
    video = ROOT / graph["source"]["video_path"]
    assert digest(video) == graph["source"]["sha256"], "Source hash mismatch"
    frames = json.loads(run("ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_frames", "-show_entries",
                            "frame=best_effort_timestamp_time", "-of", "json",
                            str(video)))["frames"]
    pts = [float(f["best_effort_timestamp_time"]) for f in frames]
    assert len(pts) == graph["source"]["native_frame_count"]
    ids = [n["id"] for n in graph["nodes"]]
    assert len(ids) == len(set(ids)), "Duplicate node IDs"
    for edge in graph["edges"]:
        assert edge["source"] in ids and edge["target"] in ids

    observations = [n for n in graph["nodes"] if n["type"] == "observation"]
    for node in observations:
        index = node["frame_index_zero_based"]
        assert abs(pts[index] - node["source_pts_seconds"]) < 0.000001
        path = ROOT / node["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i",
                        str(video), "-vf", f"select=eq(n\\,{index})", "-frames:v",
                        "1", "-q:v", "2", "-y", str(path)], check=True)

    mapping = graph["stream_timing"]["first_12_packets"]
    native = frame_hashes(video, "scale=640:-1",
                          max(p["native_frame_index"] for p in mapping) + 1)
    sampled = frame_hashes(video, "fps=1,scale=640:-1", len(mapping))
    assert len(sampled) == len(mapping)
    for packet, h in zip(mapping, sampled):
        index = packet["native_frame_index"]
        assert native[index] == h, packet
        assert abs(pts[index] - packet["source_pts_seconds"]) < 0.000001

    # Also check that this sampling recipe really reproduces the existing inputs.
    with tempfile.TemporaryDirectory(prefix="ha01_review_") as tmp:
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i",
                        str(video), "-vf", "fps=1,scale=640:-1", "-frames:v",
                        str(len(mapping)), "-q:v", "3", "-y",
                        str(Path(tmp) / "%04d.jpg")], check=True)
        stream = ROOT / "stream_frames" / graph["source"]["session_id"]
        for i in range(1, len(mapping) + 1):
            name = f"{i:04d}.jpg"
            assert digest(stream / name) == digest(Path(tmp) / name), name
    print(f"VALID: source hash, {len(observations)} native anchors, graph endpoints, "
          f"{len(mapping)} packet/source mappings and existing JPEG inputs. "
          "Visual claims still require independent annotation.")


if __name__ == "__main__":
    main()
