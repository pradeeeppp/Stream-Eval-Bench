"""Table components and leg assembly status use case (HoloAssist)."""

from __future__ import annotations
import pathlib
from typing import Any, Dict, List, Optional, Union, Sequence

from stream_eval.core.models import VideoPacket, StepResult
from stream_eval.core.schedules import DeliverySchedule, DelayedSchedule
from stream_eval.usecases.registry import UseCase, register_usecase

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


class TableComponentsUseCase(UseCase):
    """
    Evaluates tracking of table assembly components across time:
    legs attached vs tabletop tray mounted.
    """

    def __init__(self):
        question = (
            "Track the assembly components of the round table. Answer two questions: "
            "legs_assembled = are the metal table legs fastened to the circular frame at capture time 75s? "
            "tray_placed = is the removable round tray resting on the top frame at latest capture time received? "
            "Use yes, no, or unknown. Return only JSON with keys legs_assembled and tray_placed."
        )
        schema = {"legs_assembled": "unknown", "tray_placed": "unknown"}
        expected_final = {"legs_assembled": "yes", "tray_placed": "yes"}

        super().__init__(
            usecase_id="table_components_tracking",
            name="HoloAssist Table Component Assembly State Tracking",
            description="Multi-angle test assessing leg frame fastening vs final tray placement under delayed arrival.",
            question=question,
            schema=schema,
            expected_final=expected_final,
        )
        self._packets_cache: Optional[List[VideoPacket]] = None

    @property
    def packets(self) -> List[VideoPacket]:
        if self._packets_cache is not None:
            return self._packets_cache

        diag_dir = REPO_ROOT / "experiments" / "two_clip_diagnostic"
        fmt_dir = REPO_ROOT / "experiments" / "format_controls" / "inputs"

        p_earlier = VideoPacket(
            packet_id="frame_assembly",
            capture_start=64.0,
            capture_end=75.9,
            video_path=diag_dir / "earlier.mp4" if (diag_dir / "earlier.mp4").exists() else None,
            source_fps=1.0,
            metadata={"legs_assembled": True, "tray_placed": False},
        )

        p_later = VideoPacket(
            packet_id="tray_completion",
            capture_start=112.0,
            capture_end=120.0,
            video_path=diag_dir / "later.mp4" if (diag_dir / "later.mp4").exists() else None,
            source_fps=1.0,
            metadata={"legs_assembled": True, "tray_placed": True},
        )

        self._packets_cache = [p_earlier, p_later]
        return self._packets_cache

    def get_default_delayed_schedule(self, **kwargs) -> DeliverySchedule:
        # Out of order: completion arrives first (index 1), then earlier frame assembly arrives (index 0)
        return DelayedSchedule(order_indices=[1, 0])

    def get_expected_state(
        self,
        condition: str,
        step_index: int,
        arrived_packet_ids: Sequence[Union[str, int]],
    ) -> Optional[Dict[str, Any]]:
        arrived = set(arrived_packet_ids)
        legs = "yes" if "frame_assembly" in arrived or "tray_completion" in arrived else "unknown"
        tray = "yes" if "tray_completion" in arrived else "no"
        return {"legs_assembled": legs, "tray_placed": tray}

    def evaluate_revision(self, condition: str, steps: List[StepResult]) -> Dict[str, Any]:
        cond = condition.lower()
        if cond != "delayed" or len(steps) < 2:
            return {
                "historical_update_success": None,
                "recency_preserved": None,
                "revision_diagnostic": "Condition not delayed or < 2 steps",
            }

        step0 = steps[0].parsed_state or {}
        step1 = steps[1].parsed_state or {}

        # Legs assembled should be recognized
        legs_correct = (str(step1.get("legs_assembled", "")).strip().lower() == "yes")
        # Tray placed at latest capture should remain 'yes'
        tray_preserved = (str(step1.get("tray_placed", "")).strip().lower() == "yes")

        return {
            "historical_update_success": legs_correct,
            "recency_preserved": tray_preserved,
            "prior_tray_state": step0.get("tray_placed"),
            "final_tray_state": step1.get("tray_placed"),
        }


register_usecase(TableComponentsUseCase())
