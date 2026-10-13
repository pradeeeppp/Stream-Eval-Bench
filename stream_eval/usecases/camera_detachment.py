"""Camera detachment sequence use case (HoloAssist DSLR session)."""

from __future__ import annotations
import pathlib
from typing import Any, Dict, List, Optional, Union, Sequence

from stream_eval.core.models import VideoPacket, StepResult
from stream_eval.core.schedules import DeliverySchedule, DelayedSchedule
from stream_eval.usecases.registry import UseCase, register_usecase

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


class CameraDetachmentUseCase(UseCase):
    """
    Evaluates tracking of camera part removal actions across multiple stream packets:
    HoloAssist session z176-sep-05-22-dslr.
    """

    def __init__(self):
        question = (
            "Track camera-part detachments in the capture-time interval 6–24 seconds. "
            "first_detached and second_detached name the first and second separate part-removal actions in CAPTURE-TIME order (lens or cap; unknown if not established). "
            "detachments is the number of distinct removals supported by the received footage, not the number of clips. "
            "lens_attached_now describes the latest capture time received, not the last packet arrival. "
            "Do not count putting a part back on as another removal. "
            "Return only JSON with keys first_detached, second_detached, detachments, lens_attached_now."
        )
        schema = {
            "first_detached": "unknown",
            "second_detached": "unknown",
            "detachments": "unknown",
            "lens_attached_now": "unknown",
        }
        expected_final = {
            "first_detached": "lens",
            "second_detached": "cap",
            "detachments": 2,
            "lens_attached_now": "yes",
        }

        super().__init__(
            usecase_id="camera_detachment",
            name="HoloAssist Camera Part Detachment Tracking",
            description="Multi-packet streaming task testing sequential action discovery and retroactive insertion.",
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
        bounds = [6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0]

        packets = []
        for i in range(6):
            frames = [packets_dir / f"camera_{i}_{j}.png" for j in range(4)]
            existing_frames = [f for f in frames if f.exists()]
            p = VideoPacket(
                packet_id=i,
                capture_start=bounds[i],
                capture_end=bounds[i + 1],
                frames=existing_frames,
                source_fps=1.0,
                metadata={"session": "z176-sep-05-22-dslr"},
            )
            packets.append(p)

        self._packets_cache = packets
        return self._packets_cache

    def get_default_delayed_schedule(self, **kwargs) -> DeliverySchedule:
        # Canonical delayed sequence: packet 1 is delayed, arriving after packet 3: [0, 2, 3, 1, 4, 5]
        return DelayedSchedule(order_indices=[0, 2, 3, 1, 4, 5])

    def get_expected_state(
        self,
        condition: str,
        step_index: int,
        arrived_packet_ids: Sequence[Union[str, int]],
    ) -> Optional[Dict[str, Any]]:
        arrived = set(arrived_packet_ids)

        # Before packet 1 arrives, only cap detachment was seen in packet 2
        if 1 not in arrived:
            return {
                "first_detached": "unknown",
                "second_detached": "unknown",
                "detachments": 1 if (2 in arrived or 3 in arrived) else 0,
                "lens_attached_now": "yes" if any(p >= 3 for p in arrived) else "unknown",
            }
        else:
            # Once packet 1 arrives, lens detachment (at capture 9-12s) is established
            return {
                "first_detached": "lens",
                "second_detached": "cap" if 2 in arrived else "unknown",
                "detachments": 2 if 2 in arrived else 1,
                "lens_attached_now": "yes",
            }

    def evaluate_revision(self, condition: str, steps: List[StepResult]) -> Dict[str, Any]:
        cond = condition.lower()
        if cond != "delayed" or len(steps) < 4:
            return {
                "historical_update_success": None,
                "recency_preserved": None,
                "revision_diagnostic": "Condition not delayed or < 4 steps",
            }

        # Step 2: packets [0, 2, 3] arrived. Packet 1 is missing.
        # Step 3: packet 1 arrives!
        step_pre_late = steps[2].parsed_state or {}
        step_post_late = steps[3].parsed_state or {}

        # Historical update: first_detached should become 'lens', detachments should become 2
        first_post = str(step_post_late.get("first_detached", "")).strip().lower()
        hist_success = (first_post == "lens")

        # Recency preservation: lens_attached_now must remain 'yes'
        lens_post = str(step_post_late.get("lens_attached_now", "")).strip().lower()
        recency_success = (lens_post == "yes")

        return {
            "historical_update_success": hist_success,
            "recency_preserved": recency_success,
            "pre_arrival_first_detached": step_pre_late.get("first_detached"),
            "post_arrival_first_detached": step_post_late.get("first_detached"),
            "pre_arrival_lens_attached_now": step_pre_late.get("lens_attached_now"),
            "post_arrival_lens_attached_now": step_post_late.get("lens_attached_now"),
        }


# Register default instance
register_usecase(CameraDetachmentUseCase())
