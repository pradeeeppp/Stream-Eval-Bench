"""Delivery schedules simulating diverse streaming packet arrival patterns."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Sequence, Union, Optional
from stream_eval.core.models import VideoPacket


class DeliverySchedule(ABC):
    """Abstract base class for streaming packet arrival schedules."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def organize_steps(self, packets: Sequence[VideoPacket]) -> List[List[VideoPacket]]:
        """Splits and orders packets into a list of steps, where each step delivers one or more packets."""
        pass


class ChronologicalSchedule(DeliverySchedule):
    """Delivers packets sequentially in capture-time chronological order."""

    def __init__(self):
        super().__init__("chronological")

    def organize_steps(self, packets: Sequence[VideoPacket]) -> List[List[VideoPacket]]:
        # Sort by capture_start
        sorted_packets = sorted(packets, key=lambda p: (p.capture_start, p.capture_end))
        return [[p] for p in sorted_packets]


class TogetherSchedule(DeliverySchedule):
    """Batch control condition: delivers all packets simultaneously in a single step."""

    def __init__(self):
        super().__init__("together")

    def organize_steps(self, packets: Sequence[VideoPacket]) -> List[List[VideoPacket]]:
        sorted_packets = sorted(packets, key=lambda p: (p.capture_start, p.capture_end))
        return [list(sorted_packets)]


class DelayedSchedule(DeliverySchedule):
    """Delivers packets in a specified or constructed out-of-order sequence to test retroactive revision."""

    def __init__(self, order_indices: Optional[List[int]] = None, delayed_packet_id: Optional[Union[str, int]] = None, delay_by_steps: int = 1):
        super().__init__("delayed")
        self.order_indices = order_indices
        self.delayed_packet_id = delayed_packet_id
        self.delay_by_steps = delay_by_steps

    def organize_steps(self, packets: Sequence[VideoPacket]) -> List[List[VideoPacket]]:
        if self.order_indices is not None:
            # Map indices to packets
            return [[packets[idx]] for idx in self.order_indices]

        # Automatically construct a delayed schedule by delaying a designated packet
        sorted_packets = sorted(packets, key=lambda p: (p.capture_start, p.capture_end))
        if len(sorted_packets) <= 1:
            return [[p] for p in sorted_packets]

        if self.delayed_packet_id is not None:
            # Find the designated packet
            target_idx = next((i for i, p in enumerate(sorted_packets) if p.packet_id == self.delayed_packet_id), 0)
        else:
            # Default: delay the earliest packet (packet 0)
            target_idx = 0

        target = sorted_packets.pop(target_idx)
        insert_pos = min(target_idx + self.delay_by_steps, len(sorted_packets))
        sorted_packets.insert(insert_pos, target)

        return [[p] for p in sorted_packets]


class DropSchedule(DeliverySchedule):
    """Simulates network packet loss by dropping specified packet IDs or indices."""

    def __init__(self, drop_packet_ids: Sequence[Union[str, int]]):
        super().__init__("drop")
        self.drop_packet_ids = set(drop_packet_ids)

    def organize_steps(self, packets: Sequence[VideoPacket]) -> List[List[VideoPacket]]:
        sorted_packets = sorted(packets, key=lambda p: (p.capture_start, p.capture_end))
        retained = [p for p in sorted_packets if p.packet_id not in self.drop_packet_ids]
        return [[p] for p in retained]


def create_schedule(schedule_name: str, **kwargs) -> DeliverySchedule:
    """Factory function for schedule creation."""
    s = schedule_name.lower()
    if s == "chronological":
        return ChronologicalSchedule()
    elif s == "together" or s == "batch":
        return TogetherSchedule()
    elif s == "delayed" or s == "out_of_order":
        return DelayedSchedule(**kwargs)
    elif s == "drop":
        return DropSchedule(**kwargs)
    else:
        raise ValueError(f"Unknown schedule: {schedule_name}. Choose from: chronological, together, delayed, drop")
