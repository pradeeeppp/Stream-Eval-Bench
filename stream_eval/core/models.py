"""Core data models for Stream-Eval-Bench agent environment."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import json
import pathlib
import hashlib
from datetime import datetime


@dataclass
class VideoPacket:
    """Represents a discrete packet / chunk of streaming video evidence."""
    packet_id: Union[str, int]
    capture_start: float
    capture_end: float
    frames: List[Union[str, pathlib.Path]] = field(default_factory=list)
    video_path: Optional[Union[str, pathlib.Path]] = None
    source_fps: float = 1.0
    total_source_frames: int = 4
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_hash(self) -> str:
        """Computes SHA256 of packet contents (video file or frame files)."""
        hasher = hashlib.sha256()
        if self.video_path and pathlib.Path(self.video_path).exists():
            hasher.update(pathlib.Path(self.video_path).read_bytes())
        elif self.frames:
            for f in sorted(self.frames, key=str):
                p = pathlib.Path(f)
                if p.exists():
                    hasher.update(p.read_bytes())
                else:
                    hasher.update(str(f).encode())
        else:
            hasher.update(f"{self.packet_id}-{self.capture_start}-{self.capture_end}".encode())
        return hasher.hexdigest()


@dataclass
class Observation:
    """The observation passed to the streaming agent at each step."""
    step_index: int
    total_steps: int
    packets: List[VideoPacket]
    latest_capture_boundary: float
    task_prompt: str
    schema: Dict[str, Any]
    previous_memory: str = "{}"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def formatted_prompt(self) -> str:
        """Renders standard prompt with transport metadata, task instructions, and previous memory."""
        lines = []
        for i, p in enumerate(self.packets):
            lines.append(
                f"Video packet {i+1} (ID: {p.packet_id}): "
                f"Original capture timestamp {p.capture_start:.3f}–{p.capture_end:.3f}s."
            )
        lines.append("Playback time is local to each packet. Use original capture timestamps.")
        lines.append("A delayed packet represents older evidence, not a newly occurring physical event.")
        lines.append("Update historical facts supported by older evidence, and preserve facts about later capture times.")
        lines.append(f"Latest capture timestamp boundary received: {self.latest_capture_boundary:.3f}s.")
        lines.append(f"Previous model-produced memory: {self.previous_memory}")
        lines.append(f"Task: {self.task_prompt}")
        lines.append(f"Return only a single JSON object with keys: {json.dumps(list(self.schema.keys()))}.")
        lines.append("Use 'unknown' for unsupported or unobserved fields. Do not include commentary or markdown fences.")
        return "\n".join(lines)


@dataclass
class StepResult:
    """Record of a single interaction step in the streaming environment."""
    step_index: int
    packet_ids: List[Union[str, int]]
    latest_capture_boundary: float
    input_memory: str
    prompt: str
    raw_response: str
    parsed_state: Optional[Dict[str, Any]]
    expected_state: Optional[Dict[str, Any]]
    elapsed_seconds: float
    is_valid_json: bool
    step_metrics: Dict[str, Any] = field(default_factory=dict)
    utc_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class EpisodeResult:
    """Complete record and evaluation of a streaming episode."""
    usecase_id: str
    condition: str  # e.g., 'chronological', 'delayed', 'together'
    steps: List[StepResult]
    final_state: Optional[Dict[str, Any]]
    expected_final_state: Optional[Dict[str, Any]]
    metrics: Dict[str, Any]
    environment_metadata: Dict[str, Any] = field(default_factory=dict)
    agent_metadata: Dict[str, Any] = field(default_factory=dict)
    utc_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "usecase_id": self.usecase_id,
            "condition": self.condition,
            "steps": [
                {
                    "step_index": s.step_index,
                    "packet_ids": s.packet_ids,
                    "latest_capture_boundary": s.latest_capture_boundary,
                    "input_memory": s.input_memory,
                    "prompt": s.prompt,
                    "raw_response": s.raw_response,
                    "parsed_state": s.parsed_state,
                    "expected_state": s.expected_state,
                    "elapsed_seconds": s.elapsed_seconds,
                    "is_valid_json": s.is_valid_json,
                    "step_metrics": s.step_metrics,
                    "utc_timestamp": s.utc_timestamp,
                }
                for s in self.steps
            ],
            "final_state": self.final_state,
            "expected_final_state": self.expected_final_state,
            "metrics": self.metrics,
            "environment_metadata": self.environment_metadata,
            "agent_metadata": self.agent_metadata,
            "utc_timestamp": self.utc_timestamp,
        }
