"""Rehydrate MP4s, stream frames, and only the 40 cited evidence frames."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    sources = json.loads((HERE / "sources.json").read_text())["sources"]
    tasks = [json.loads(line) for line in (HERE / "tasks.jsonl").read_text().splitlines() if line.strip()]
    needed = {}
    for task in tasks:
        needed.setdefault(task["source_id"], set()).update((
            task["pre_event_checkpoint_seconds"] + 1,
            task["first_positive_sample_seconds"] + 1,
        ))
    for source in sources:
        video = ROOT / source["local_path"]
        video.parent.mkdir(parents=True, exist_ok=True)
        if not video.exists() or sha256(video) != source["sha256"]:
            temp = video.with_suffix(".download")
            subprocess.run(["curl", "-fLsS", source["source_url"], "-o", str(temp)], check=True)
            if sha256(temp) != source["sha256"]:
                temp.unlink(missing_ok=True)
                raise ValueError(f"Hash mismatch: {source['session_id']}")
            temp.replace(video)
        stream_dir = ROOT / "stream_frames" / source["session_id"]
        stream_dir.mkdir(parents=True, exist_ok=True)
        if not (stream_dir / "0001.jpg").exists():
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
                            "-vf", "fps=1,scale=640:-1", "-q:v", "3", "-y",
                            str(stream_dir / "%04d.jpg")], check=True)
        review_dir = ROOT / "full_review" / source["session_id"]
        review_dir.mkdir(parents=True, exist_ok=True)
        for index in needed[source["source_id"]]:
            target = review_dir / f"{index:04d}.jpg"
            if not target.exists():
                stream_frame = stream_dir / f"{index:04d}.jpg"
                if not stream_frame.is_file():
                    raise FileNotFoundError(stream_frame)
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                                "-i", str(stream_frame), "-vf", "scale=240:-1",
                                "-q:v", "5", "-frames:v", "1", "-y", str(target)], check=True)
        print(source["source_id"], source["session_id"], "ready", flush=True)


if __name__ == "__main__":
    main()
