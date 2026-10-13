"""UseCase base abstraction and global registry for streaming benchmark tasks."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Sequence
from stream_eval.core.models import VideoPacket, StepResult
from stream_eval.core.schedules import (
    DeliverySchedule,
    ChronologicalSchedule,
    TogetherSchedule,
    DelayedSchedule,
)


class UseCase(ABC):
    """Abstract base class for streaming video evaluation use cases."""

    def __init__(
        self,
        usecase_id: str,
        name: str,
        description: str,
        question: str,
        schema: Dict[str, Any],
        expected_final: Dict[str, Any],
    ):
        self.usecase_id = usecase_id
        self.name = name
        self.description = description
        self.question = question
        self.schema = schema
        self.expected_final = expected_final

    @property
    @abstractmethod
    def packets(self) -> List[VideoPacket]:
        """Returns the list of video packets for this use case."""
        pass

    def get_schedule(self, condition: str, **kwargs) -> DeliverySchedule:
        """Returns the appropriate delivery schedule for the given condition."""
        cond = condition.lower()
        if cond == "chronological":
            return ChronologicalSchedule()
        elif cond == "together" or cond == "batch":
            return TogetherSchedule()
        elif cond == "delayed" or cond == "out_of_order":
            return self.get_default_delayed_schedule(**kwargs)
        else:
            from stream_eval.core.schedules import create_schedule
            return create_schedule(cond, **kwargs)

    @abstractmethod
    def get_default_delayed_schedule(self, **kwargs) -> DeliverySchedule:
        """Returns the canonical out-of-order schedule that isolates historical revision for this use case."""
        pass

    @abstractmethod
    def get_expected_state(
        self,
        condition: str,
        step_index: int,
        arrived_packet_ids: Sequence[Union[str, int]],
    ) -> Optional[Dict[str, Any]]:
        """Returns the ground truth state expected given the evidence arrived so far."""
        pass

    @abstractmethod
    def evaluate_revision(self, condition: str, steps: List[StepResult]) -> Dict[str, Any]:
        """Calculates historical update and recency preservation metrics for this specific use case."""
        pass


_REGISTRY: Dict[str, UseCase] = {}


def register_usecase(usecase: UseCase) -> None:
    """Registers a use case in the global registry."""
    _REGISTRY[usecase.usecase_id] = usecase


def get_usecase(usecase_id: str) -> UseCase:
    """Retrieves a registered usecase by ID."""
    if usecase_id not in _REGISTRY:
        available = list(_REGISTRY.keys())
        raise KeyError(f"UseCase '{usecase_id}' not found. Available use cases: {available}")
    return _REGISTRY[usecase_id]


def list_usecases() -> List[str]:
    """Returns a list of all registered use case IDs."""
    return list(_REGISTRY.keys())
