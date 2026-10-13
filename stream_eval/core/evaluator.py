"""Evaluation metrics and episode scorer for streaming video agents."""

from __future__ import annotations
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from stream_eval.core.models import EpisodeResult, StepResult

if TYPE_CHECKING:
    from stream_eval.usecases.registry import UseCase


class StreamEvaluator:
    """Evaluates agent performance on historical-evidence revision and streaming consistency."""

    def evaluate_episode(
        self,
        usecase: "UseCase",
        condition: str,
        steps: List[StepResult],
        agent_metadata: Optional[Dict[str, Any]] = None,
        environment_metadata: Optional[Dict[str, Any]] = None,
    ) -> EpisodeResult:
        if not steps:
            return EpisodeResult(
                usecase_id=usecase.usecase_id,
                condition=condition,
                steps=[],
                final_state=None,
                expected_final_state=usecase.expected_final,
                metrics={"error": "no steps executed"},
                agent_metadata=agent_metadata or {},
                environment_metadata=environment_metadata or {},
            )

        final_step = steps[-1]
        final_state = final_step.parsed_state
        expected_final = usecase.expected_final

        # 1. JSON parsing and schema validity
        valid_json_count = sum(1 for s in steps if s.is_valid_json)
        json_parse_rate = valid_json_count / len(steps)

        schema_adherence_count = 0
        required_keys = set(usecase.schema.keys())
        for s in steps:
            if s.parsed_state and isinstance(s.parsed_state, dict):
                if required_keys.issubset(set(s.parsed_state.keys())):
                    schema_adherence_count += 1
        schema_adherence_rate = schema_adherence_count / len(steps)

        # 2. Final accuracy
        final_field_matches = 0
        final_field_details = {}
        if final_state and expected_final:
            for k, exp_val in expected_final.items():
                got_val = final_state.get(k)
                if isinstance(exp_val, str) and isinstance(got_val, str):
                    matched = (exp_val.strip().lower() == got_val.strip().lower())
                else:
                    matched = (exp_val == got_val)
                if matched:
                    final_field_matches += 1
                final_field_details[k] = {"expected": exp_val, "got": got_val, "matched": matched}
            final_accuracy = final_field_matches / len(expected_final) if expected_final else 0.0
            final_perfect = (final_field_matches == len(expected_final))
        else:
            final_accuracy = 0.0
            final_perfect = False

        # 3. Trajectory fidelity (step-by-step accuracy)
        step_accuracies = [s.step_metrics.get("accuracy", 0.0) for s in steps]
        avg_trajectory_fidelity = sum(step_accuracies) / len(step_accuracies) if step_accuracies else 0.0
        perfect_trajectory = all(s.step_metrics.get("accuracy", 0.0) == 1.0 for s in steps)

        # 4. Domain-specific research metrics: Historical revision & Recency preservation
        revision_metrics = usecase.evaluate_revision(condition, steps)

        # 5. Timing
        total_time = sum(s.elapsed_seconds for s in steps)
        avg_step_time = total_time / len(steps) if steps else 0.0

        metrics = {
            "json_parse_rate": json_parse_rate,
            "schema_adherence_rate": schema_adherence_rate,
            "final_accuracy": final_accuracy,
            "final_perfect": final_perfect,
            "trajectory_fidelity": avg_trajectory_fidelity,
            "perfect_trajectory": perfect_trajectory,
            "total_elapsed_seconds": total_time,
            "avg_step_seconds": avg_step_time,
            "final_field_details": final_field_details,
            **revision_metrics,
        }

        return EpisodeResult(
            usecase_id=usecase.usecase_id,
            condition=condition,
            steps=steps,
            final_state=final_state,
            expected_final_state=expected_final,
            metrics=metrics,
            agent_metadata=agent_metadata or {},
            environment_metadata=environment_metadata or {},
        )

    @staticmethod
    def compute_comparative_summary(episodes: List[EpisodeResult]) -> Dict[str, Any]:
        """Compares multiple conditions (e.g. chronological vs delayed vs together) for a use case."""
        by_condition = {ep.condition: ep for ep in episodes}
        summary = {
            "conditions_evaluated": list(by_condition.keys()),
            "condition_metrics": {c: ep.metrics for c, ep in by_condition.items()},
        }

        chrono = by_condition.get("chronological")
        delayed = by_condition.get("delayed")
        together = by_condition.get("together")

        if chrono and delayed:
            chrono_acc = chrono.metrics.get("final_accuracy", 0.0)
            delayed_acc = delayed.metrics.get("final_accuracy", 0.0)
            chrono_traj = chrono.metrics.get("trajectory_fidelity", 0.0)
            delayed_traj = delayed.metrics.get("trajectory_fidelity", 0.0)

            summary["order_effect"] = {
                "final_accuracy_gap": chrono_acc - delayed_acc,
                "trajectory_fidelity_gap": chrono_traj - delayed_traj,
                "delayed_matched_chrono_final": (chrono.final_state == delayed.final_state),
                "delayed_historical_update_success": delayed.metrics.get("historical_update_success", False),
                "delayed_recency_preservation_success": delayed.metrics.get("recency_preserved", False),
            }

        if together and delayed:
            together_acc = together.metrics.get("final_accuracy", 0.0)
            summary["batch_control_gap"] = together_acc - delayed.metrics.get("final_accuracy", 0.0)

        return summary
