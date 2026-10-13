"""Interactive Streaming Video Agent Environment."""

from __future__ import annotations
import json
import time
from typing import Any, Dict, List, Optional, Union, Tuple, TYPE_CHECKING

from stream_eval.core.models import (
    VideoPacket,
    Observation,
    StepResult,
    EpisodeResult,
)
from stream_eval.core.schedules import (
    DeliverySchedule,
    create_schedule,
)

if TYPE_CHECKING:
    from stream_eval.usecases.registry import UseCase
    from stream_eval.core.agents import BaseStreamingAgent


def parse_json_response(text: str) -> Optional[Dict[str, Any]]:
    """Robustly extract and parse a JSON object from raw agent text."""
    if not text or not isinstance(text, str):
        return None
    try:
        # Direct parsing
        return json.loads(text)
    except Exception:
        pass

    # Search for first '{' and parse with raw_decode
    try:
        idx = text.find("{")
        if idx != -1:
            obj, _ = json.JSONDecoder().raw_decode(text[idx:])
            if isinstance(obj, dict):
                return obj
    except Exception:
        pass
    return None


class StreamingEnvironment:
    """Simulates a live streaming video environment with configurable packet arrival conditions."""

    def __init__(
        self,
        usecase: "UseCase",
        schedule: Union[DeliverySchedule, str] = "chronological",
        schedule_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.usecase = usecase
        self.schedule_kwargs = schedule_kwargs or {}

        if isinstance(schedule, str):
            self.schedule = self.usecase.get_schedule(schedule, **self.schedule_kwargs)
        else:
            self.schedule = schedule

        self._steps_packets: List[List[VideoPacket]] = []
        self._current_step_idx: int = 0
        self._latest_capture_boundary: float = 0.0
        self._arrived_packet_ids: List[Union[str, int]] = []
        self._previous_memory: str = "{}"
        self._step_results: List[StepResult] = []
        self._done: bool = False
        self._start_time: float = 0.0

    @property
    def condition(self) -> str:
        return self.schedule.name

    @property
    def current_step(self) -> int:
        return self._current_step_idx

    @property
    def total_steps(self) -> int:
        return len(self._steps_packets)

    @property
    def is_done(self) -> bool:
        return self._done

    def reset(
        self,
        schedule: Optional[Union[DeliverySchedule, str]] = None,
        **schedule_kwargs,
    ) -> Observation:
        """Resets the environment with an optional new schedule or parameters."""
        if schedule is not None:
            if isinstance(schedule, str):
                self.schedule = self.usecase.get_schedule(schedule, **schedule_kwargs)
            else:
                self.schedule = schedule

        # Prepare packet arrivals for this episode
        self._steps_packets = self.schedule.organize_steps(self.usecase.packets)
        self._current_step_idx = 0
        self._latest_capture_boundary = 0.0
        self._arrived_packet_ids = []
        self._previous_memory = "{}"
        self._step_results = []
        self._done = (len(self._steps_packets) == 0)
        self._start_time = time.perf_counter()

        if self._done:
            raise ValueError(f"Schedule {self.schedule.name} produced 0 steps.")

        return self._create_observation(self._current_step_idx)

    def _create_observation(self, step_idx: int) -> Observation:
        packets = self._steps_packets[step_idx]
        for p in packets:
            if p.capture_end > self._latest_capture_boundary:
                self._latest_capture_boundary = p.capture_end
            if p.packet_id not in self._arrived_packet_ids:
                self._arrived_packet_ids.append(p.packet_id)

        obs = Observation(
            step_index=step_idx,
            total_steps=len(self._steps_packets),
            packets=packets,
            latest_capture_boundary=self._latest_capture_boundary,
            task_prompt=self.usecase.question,
            schema=self.usecase.schema,
            previous_memory=self._previous_memory,
            metadata={
                "condition": self.condition,
                "arrived_packet_ids": list(self._arrived_packet_ids),
                "usecase_id": self.usecase.usecase_id,
            },
        )
        return obs

    def step(self, agent_response: Union[str, Dict[str, Any]], elapsed_seconds: float = 0.0) -> Tuple[Optional[Observation], StepResult, bool, Dict[str, Any]]:
        """Takes an agent response/action, records step results, and transitions to the next streaming packet."""
        if self._done:
            raise RuntimeError("Environment is already finished. Call reset() to begin a new episode.")

        # Format agent response
        if isinstance(agent_response, dict):
            raw_text = json.dumps(agent_response)
            parsed = agent_response
        else:
            raw_text = str(agent_response)
            parsed = parse_json_response(raw_text)

        curr_packets = self._steps_packets[self._current_step_idx]
        packet_ids = [p.packet_id for p in curr_packets]
        is_valid = parsed is not None

        # Memory persists as raw response or compact json string
        self._previous_memory = raw_text

        # Get ground truth expectation for this step if defined in use case
        expected = self.usecase.get_expected_state(
            condition=self.condition,
            step_index=self._current_step_idx,
            arrived_packet_ids=self._arrived_packet_ids,
        )

        step_res = StepResult(
            step_index=self._current_step_idx,
            packet_ids=packet_ids,
            latest_capture_boundary=self._latest_capture_boundary,
            input_memory=self._step_results[-1].raw_response if self._step_results else "{}",
            prompt=self._create_observation(self._current_step_idx).formatted_prompt(),
            raw_response=raw_text,
            parsed_state=parsed,
            expected_state=expected,
            elapsed_seconds=elapsed_seconds,
            is_valid_json=is_valid,
            step_metrics=self._evaluate_step_metrics(parsed, expected),
        )
        self._step_results.append(step_res)

        # Advance step
        self._current_step_idx += 1
        if self._current_step_idx >= len(self._steps_packets):
            self._done = True
            next_obs = None
        else:
            next_obs = self._create_observation(self._current_step_idx)

        info = {
            "step": self._current_step_idx,
            "condition": self.condition,
            "arrived_packets": list(self._arrived_packet_ids),
        }
        return next_obs, step_res, self._done, info

    def _evaluate_step_metrics(
        self,
        parsed: Optional[Dict[str, Any]],
        expected: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculates step-level correctness."""
        if not parsed or not expected:
            return {"match_count": 0, "total_fields": len(self.usecase.schema), "accuracy": 0.0}

        matches = 0
        total = 0
        field_details = {}
        for k, exp_val in expected.items():
            total += 1
            got_val = parsed.get(k)
            # Normalize strings for comparison (e.g. lowercase)
            if isinstance(exp_val, str) and isinstance(got_val, str):
                is_match = (exp_val.strip().lower() == got_val.strip().lower())
            else:
                is_match = (exp_val == got_val)
            if is_match:
                matches += 1
            field_details[k] = {"expected": exp_val, "got": got_val, "match": is_match}

        acc = (matches / total) if total > 0 else 0.0
        return {"match_count": matches, "total_fields": total, "accuracy": acc, "fields": field_details}

    def get_episode_result(self, agent_metadata: Optional[Dict[str, Any]] = None) -> EpisodeResult:
        """Summarizes and evaluates the full streaming episode."""
        from stream_eval.core.evaluator import StreamEvaluator
        evaluator = StreamEvaluator()
        return evaluator.evaluate_episode(
            usecase=self.usecase,
            condition=self.condition,
            steps=self._step_results,
            agent_metadata=agent_metadata or {},
            environment_metadata={
                "schedule": self.condition,
                "total_packets": len(self.usecase.packets),
                "steps_count": len(self._steps_packets),
            },
        )

    def run_episode(
        self,
        agent: "BaseStreamingAgent",
        schedule: Optional[Union[DeliverySchedule, str]] = None,
        verbose: bool = False,
    ) -> EpisodeResult:
        """Runs an end-to-end streaming trial with the given agent."""
        agent.reset()
        obs = self.reset(schedule=schedule)

        while not self.is_done:
            t0 = time.perf_counter()
            response = agent.act(obs)
            elapsed = time.perf_counter() - t0

            obs, step_res, done, info = self.step(response, elapsed_seconds=elapsed)
            if verbose:
                print(
                    f"[{self.usecase.usecase_id} | {self.condition}] "
                    f"Step {step_res.step_index + 1}/{len(self._steps_packets)} "
                    f"Packets {step_res.packet_ids}: "
                    f"Response: {step_res.raw_response.strip()[:100]}... "
                    f"({step_res.elapsed_seconds:.2f}s)"
                )

        return self.get_episode_result(agent_metadata=agent.get_metadata())
