"""Camera mount state use case testing ongoing stream integrity."""

from __future__ import annotations
import pathlib
from typing import Any, Dict, List, Optional, Union, Sequence

from stream_eval.core.models import VideoPacket, StepResult
from stream_eval.core.schedules import DeliverySchedule, DelayedSchedule
from stream_eval.usecases.registry import UseCase, register_usecase

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


class CameraMountStateUseCase(UseCase):
    """
    Evaluates tracking whether the cylindrical lens is mounted on the camera body
    at capture start (~6-9s) vs during detachment (~10-15s) vs at endpoint (~24s).
    """

    def __init__(self):
        question = (
            "Track whether the cylindrical lens is mounted on the camera body (not held separately). "
            "Ignore the lens cap. Answer two fields: "
            "at_start = was the lens mounted on the camera body around capture time 6 to 9 seconds? "
            "at_end = was the lens mounted on the camera body at the latest capture time received? "
            "Use yes, no, or unknown. Return only JSON with keys at_start and at_end."
        )
        schema = {"at_start": "unknown", "at_end": "unknown"}
        expected_final = {"at_start": "yes", "at_end": "yes"}

        super().__init__(
            usecase_id="camera_mount_status",
            name="HoloAssist Camera Lens Mounting State Across Intervals",
            description="Multi-angle test assessing mounting status at start vs endpoint under arrival reordering.",
            question=question,
            schema=schema,
            expected_final=expected_final,
        )
        self._packets_cache: Optional[List[VideoPacket]] = None

    @property
    def packets(self) -> List[VideoPacket]:
        if self._packets_cache is not None:
            return self._packets_cache

        packets_dir = REPO_ROOT / "experiments" / "evidence_revision_pilot" / "streaming_trial" / "packets"
        fmt_dir = REPO_ROOT / "experiments" / "format_controls" / "inputs"

        # Packet 0: Start (6-9s) - Lens is mounted on body
        p0 = VideoPacket(
            packet_id="camera_start",
            capture_start=6.0,
            capture_end=9.0,
            frames=[packets_dir / f"camera_0_{j}.png" for j in range(4) if (packets_dir / f"camera_0_{j}.png").exists()],
            source_fps=1.0,
            metadata={"mounted": True},
        )

        # Packet 1: Middle detachment (10-14s) - Lens detached / held in hand
        p1 = VideoPacket(
            packet_id="camera_middle",
            capture_start=10.0,
            capture_end=14.0,
            frames=[packets_dir / f"camera_1_{j}.png" for j in range(4) if (packets_dir / f"camera_1_{j}.png").exists()],
            source_fps=1.0,
            metadata={"mounted": False},
        )

        # Packet 2: End (~21-24s) - Lens remounted / inspected
        p2 = VideoPacket(
            packet_id="camera_end",
            capture_start=21.0,
            capture_end=24.0,
            video_path=fmt_dir / "camera.mp4" if (fmt_dir / "camera.mp4").exists() else None,
            frames=[packets_dir / f"camera_5_{j}.png" for j in range(4) if (packets_dir / f"camera_5_{j}.png").exists()],
            source_fps=1.0,
            metadata={"mounted": True},
        )

        self._packets_cache = [p0, p1, p2]
        return self._packets_cache

    def get_default_delayed_schedule(self, **kwargs) -> DeliverySchedule:
        # Out of order: end arrives first (index 2), then middle (index 1), then start (index 0)
        return DelayedSchedule(order_indices=[2, 1, 0])

    def get_expected_state(
        self,
        condition: str,
        step_index: int,
        arrived_packet_ids: Sequence[Union[str, int]],
    ) -> Optional[Dict[str, Any]]:
        arrived = set(arrived_packet_ids)
        at_start = "yes" if "camera_start" in arrived else "unknown"
        at_end = "yes" if "camera_end" in arrived else ("no" if "camera_middle" in arrived else "unknown")
        return {"at_start": at_start, "at_end": at_end}

    def evaluate_revision(self, condition: str, steps: List[StepResult]) -> Dict[str, Any]:
        cond = condition.lower()
        if cond != "delayed" or len(steps) < 3:
            return {
                "historical_update_success": None,
                "recency_preserved": None,
                "revision_diagnostic": "Condition not delayed or < 3 steps",
            }

        step0 = steps[0].parsed_state or {}
        step2 = steps[2].parsed_state or {}

        # Historical update: at_start was unknown at step 0, becomes 'yes' at step 2
        start_step2 = str(step2.get("at_start", "")).strip().lower()
        hist_update = (start_step2 == "yes")

        # Recency preservation: at_end was 'yes' at step 0, must remain 'yes' at step 2
        end_step2 = str(step2.get("at_end", "")).strip().lower()
        recency_preserved = (end_step2 == "yes")

        return {
            "historical_update_success": hist_update,
            "recency_preserved": recency_preserved,
            "prior_start_state": step0.get("at_start"),
            "final_start_state": step2.get("at_start"),
            "prior_end_state": step0.get("at_end"),
            "final_end_state": step2.get("at_end"),
        }


register_usecase(CameraMountStateUseCase())
