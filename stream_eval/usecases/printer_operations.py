"""Printer operation use cases (HoloAssist session R071-19July-BigPrinter)."""

from __future__ import annotations
import pathlib
from typing import Any, Dict, List, Optional, Union, Sequence

from stream_eval.core.models import VideoPacket, StepResult
from stream_eval.core.schedules import DeliverySchedule, DelayedSchedule
from stream_eval.usecases.registry import UseCase, register_usecase

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


class PrinterDisplayTrackingUseCase(UseCase):
    """
    Tracks printer LCD display illumination state across time intervals:
    Early interval (~19s) vs Late interval (~43s).
    """

    def __init__(self):
        question = (
            "Track the central rectangular printer LCD display state across capture time intervals. "
            "Ignore small indicator LEDs. Answer two fields: "
            "earlier = was the main central display illuminated or dark around capture time 19 seconds? "
            "latest = was the main central display illuminated or dark at the latest capture time received? "
            "Use unknown when evidence has not yet arrived. Do not infer earlier status from later footage. "
            "Return only JSON with keys earlier and latest, each with value illuminated, dark, or unknown."
        )
        schema = {"earlier": "unknown", "latest": "unknown"}
        expected_final = {"earlier": "unknown", "latest": "dark"}

        super().__init__(
            usecase_id="printer_display_tracking",
            name="HoloAssist Printer Display Illumination Tracking",
            description="Evaluates historical display state update vs latest live state preservation on BigPrinter.",
            question=question,
            schema=schema,
            expected_final=expected_final,
        )
        self._packets_cache: Optional[List[VideoPacket]] = None

    @property
    def packets(self) -> List[VideoPacket]:
        if self._packets_cache is not None:
            return self._packets_cache

        inputs_dir = REPO_ROOT / "experiments" / "evidence_revision_pilot" / "direct_revision" / "inputs"
        fmt_dir = REPO_ROOT / "experiments" / "format_controls" / "inputs"

        # Packet 0: Early interval (~19.3s)
        p0 = VideoPacket(
            packet_id="printer_early",
            capture_start=18.0,
            capture_end=22.0,
            frames=[inputs_dir / "printer_E1_partial.png"],
            source_fps=1.0,
            metadata={"interval": "19.3s", "screen_visible": False},
        )

        # Packet 1: Late interval (~42.6s)
        p1 = VideoPacket(
            packet_id="printer_late",
            capture_start=40.0,
            capture_end=45.0,
            video_path=fmt_dir / "printer.mp4" if (fmt_dir / "printer.mp4").exists() else None,
            frames=[fmt_dir / f"printer_{i}.png" for i in range(4) if (fmt_dir / f"printer_{i}.png").exists()] or [inputs_dir / "printer_E2_full.png"],
            source_fps=1.0,
            metadata={"interval": "42.6s", "screen_state": "dark"},
        )

        self._packets_cache = [p0, p1]
        return self._packets_cache

    def get_default_delayed_schedule(self, **kwargs) -> DeliverySchedule:
        # Late arrives first (index 1), then early arrives (index 0)
        return DelayedSchedule(order_indices=[1, 0])

    def get_expected_state(
        self,
        condition: str,
        step_index: int,
        arrived_packet_ids: Sequence[Union[str, int]],
    ) -> Optional[Dict[str, Any]]:
        cond = condition.lower()
        if cond in ["together", "batch"]:
            return {"earlier": "unknown", "latest": "dark"}

        if cond == "chronological":
            if step_index == 0:
                # Early only: display occluded, latest capture is ~22s
                return {"earlier": "unknown", "latest": "unknown"}
            else:
                return {"earlier": "unknown", "latest": "dark"}

        elif cond == "delayed":
            if step_index == 0:
                # Late only: earlier is unknown, latest is dark
                return {"earlier": "unknown", "latest": "dark"}
            else:
                return {"earlier": "unknown", "latest": "dark"}

        return {"earlier": "unknown", "latest": "dark"}

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

        earlier_step1 = str(step1.get("earlier", "")).strip().lower()
        latest_step0 = str(step0.get("latest", "")).strip().lower()
        latest_step1 = str(step1.get("latest", "")).strip().lower()

        # Recency preservation: latest must remain 'dark'
        recency_preserved = (latest_step1 == "dark")
        # Historical accuracy: earlier remains 'unknown' (since E1 was occluded outside mask)
        earlier_correct = (earlier_step1 == "unknown")

        return {
            "historical_update_success": earlier_correct,
            "recency_preserved": recency_preserved,
            "prior_latest_state": latest_step0,
            "preserved_latest_state": latest_step1,
            "unsupported_early_hallucination": (earlier_step1 == "illuminated"),
        }


register_usecase(PrinterDisplayTrackingUseCase())
