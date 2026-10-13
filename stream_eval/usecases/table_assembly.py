"""Table assembly tray-tracking use case (HoloAssist)."""

from __future__ import annotations
import pathlib
from typing import Any, Dict, List, Optional, Union, Sequence

from stream_eval.core.models import VideoPacket, StepResult
from stream_eval.core.schedules import DeliverySchedule, DelayedSchedule
from stream_eval.usecases.registry import UseCase, register_usecase


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


class TableAssemblyTrayUseCase(UseCase):
    """
    Evaluates tracking of table frame vs round tray in HoloAssist session:
    z060-june-28-22-gladom_assemble.mp4.
    """

    def __init__(self, use_mp4: bool = True):
        question = (
            "Track whether the large round tray rests on the table frame. An open frame is not a tray. "
            "Answer two questions: earlier = was the tray resting on the frame around capture time 72 seconds? "
            "latest = was the tray resting on the frame at the latest capture time received? "
            "Use unknown when the relevant evidence has not been received. Do not infer an earlier state from later footage. "
            "An older clip arriving later can update history but does not become the latest capture time. "
            "Return only JSON with keys earlier and latest, each with value yes, no, or unknown."
        )
        schema = {"earlier": "unknown", "latest": "unknown"}
        expected_final = {"earlier": "no", "latest": "yes"}

        super().__init__(
            usecase_id="table_assembly_tray",
            name="HoloAssist Table Assembly Tray Tracking",
            description="Diagnostic test for historical-record update and recency preservation during out-of-order streaming.",
            question=question,
            schema=schema,
            expected_final=expected_final,
        )
        self.use_mp4 = use_mp4
        self._packets_cache: Optional[List[VideoPacket]] = None

    @property
    def packets(self) -> List[VideoPacket]:
        if self._packets_cache is not None:
            return self._packets_cache

        diag_dir = REPO_ROOT / "experiments" / "two_clip_diagnostic"
        earlier_mp4 = diag_dir / "earlier.mp4"
        later_mp4 = diag_dir / "later.mp4"

        # Frame fallbacks if frames exist
        packets_dir = REPO_ROOT / "experiments" / "evidence_revision_pilot" / "streaming_trial" / "packets"
        earlier_frames = [packets_dir / f"table_1_{i}.png" for i in range(4)]
        later_frames = [packets_dir / f"table_6_{i}.png" for i in range(4)]

        p_earlier = VideoPacket(
            packet_id="earlier",
            capture_start=64.019,
            capture_end=75.908,
            video_path=earlier_mp4 if earlier_mp4.exists() else None,
            frames=[f for f in earlier_frames if f.exists()],
            source_fps=1.0,
            metadata={"description": "Tray off frame (around 72s)"},
        )

        p_later = VideoPacket(
            packet_id="later",
            capture_start=112.009,
            capture_end=119.924,
            video_path=later_mp4 if later_mp4.exists() else None,
            frames=[f for f in later_frames if f.exists()],
            source_fps=1.0,
            metadata={"description": "Tray rests on frame"},
        )

        self._packets_cache = [p_earlier, p_later]
        return self._packets_cache

    def get_default_delayed_schedule(self, **kwargs) -> DeliverySchedule:
        # Later arrives first (index 1), then earlier arrives (index 0)
        return DelayedSchedule(order_indices=[1, 0])

    def get_expected_state(
        self,
        condition: str,
        step_index: int,
        arrived_packet_ids: Sequence[Union[str, int]],
    ) -> Optional[Dict[str, Any]]:
        cond = condition.lower()
        if cond in ["together", "batch"]:
            return {"earlier": "no", "latest": "yes"}

        if cond == "chronological":
            if step_index == 0:
                # Only earlier received so far: at capture ~72s tray is off (no), latest received is ~76s (no)
                return {"earlier": "no", "latest": "no"}
            else:
                return {"earlier": "no", "latest": "yes"}

        elif cond == "delayed":
            if step_index == 0:
                # Only later received: earlier at ~72s is unknown, latest at ~120s is yes
                return {"earlier": "unknown", "latest": "yes"}
            else:
                # Both received: earlier is no, latest is yes
                return {"earlier": "no", "latest": "yes"}

        return {"earlier": "no", "latest": "yes"}

    def evaluate_revision(self, condition: str, steps: List[StepResult]) -> Dict[str, Any]:
        """Specific metrics for the table assembly diagnostic."""
        cond = condition.lower()
        if cond != "delayed" or len(steps) < 2:
            return {
                "historical_update_success": None,
                "recency_preserved": None,
                "revision_diagnostic": "Condition not delayed or < 2 steps",
            }

        step0 = steps[0].parsed_state or {}
        step1 = steps[1].parsed_state or {}

        # Historical update check: did step 0 have unknown for earlier, and did step 1 update earlier to 'no'?
        earlier_step0 = str(step0.get("earlier", "")).strip().lower()
        earlier_step1 = str(step1.get("earlier", "")).strip().lower()
        historical_update = (earlier_step1 == "no")

        # Recency preservation check: did step 1 retain latest as 'yes'?
        latest_step0 = str(step0.get("latest", "")).strip().lower()
        latest_step1 = str(step1.get("latest", "")).strip().lower()
        recency_preserved = (latest_step1 == "yes")

        return {
            "historical_update_success": historical_update,
            "recency_preserved": recency_preserved,
            "prior_earlier_state": earlier_step0,
            "updated_earlier_state": earlier_step1,
            "prior_latest_state": latest_step0,
            "preserved_latest_state": latest_step1,
            "isolated_order_effect_detected": (not historical_update and recency_preserved),
        }


# Register default instance
register_usecase(TableAssemblyTrayUseCase())
