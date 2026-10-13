"""Turnkey benchmark runner for Qwen2.5-VL-7B and Qwen2.5-VL-72B across the 4-Gate Protocol."""

from __future__ import annotations
import argparse
import json
import pathlib
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from stream_eval.core.environment import StreamingEnvironment
from stream_eval.core.models import Observation
from stream_eval.core.evaluator import StreamEvaluator
from stream_eval.core.agents import (
    BaseStreamingAgent,
    LocalHuggingFaceBackend,
    OpenAICompatibleBackend,
    VLMStreamingAgent,
    MockAgent,
)
from stream_eval.usecases.registry import get_usecase, list_usecases


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def run_qwen_benchmark(
    model_name: str,
    agent: BaseStreamingAgent,
    usecase_id: str = "table_assembly_tray",
    output_dir: Optional[pathlib.Path] = None,
) -> Dict[str, Any]:
    """Runs the complete 4-gate causal streaming protocol on a specified model."""
    usecase = get_usecase(usecase_id)
    output_dir = output_dir or (REPO_ROOT / "experiments" / "qwen_benchmarks")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=======================================================")
    print(f"BENCHMARKING MODEL: {model_name}")
    print(f"USECASE: {usecase.name} [{usecase_id}]")
    print(f"PROTOCOL: 4-Gate Causal Retrospective Revision")
    print(f"=======================================================\n")

    # Run the 3 core conditions: Together (Joint), Chronological, Delayed (Streaming CRR)
    conditions = ["together", "chronological", "delayed"]
    episodes = {}

    for cond in conditions:
        print(f"--> [Condition: {cond.upper()}] Starting streaming evaluation...")
        env = StreamingEnvironment(usecase=usecase, schedule=cond)
        ep = env.run_episode(agent=agent, verbose=True)
        episodes[cond] = ep
        print(f"    Finished {cond.upper()}:")
        print(f"    - Final State: {ep.final_state}")
        print(f"    - Expected Final: {ep.expected_final_state}")
        print(f"    - Final Accuracy: {ep.metrics.get('final_accuracy', 0.0):.1%}")
        print(f"    - Trajectory Fidelity: {ep.metrics.get('trajectory_fidelity', 0.0):.1%}")
        if "historical_update_success" in ep.metrics and ep.metrics["historical_update_success"] is not None:
            print(f"    - Historical Revision Success: {ep.metrics['historical_update_success']}")
            print(f"    - Recency Preservation: {ep.metrics['recency_preserved']}")
        print()

    # Calculate Streaming Order-Effect Gap (Joint Accuracy - Delayed Streaming Accuracy)
    joint_acc = episodes["together"].metrics.get("final_accuracy", 0.0)
    chrono_acc = episodes["chronological"].metrics.get("final_accuracy", 0.0)
    delayed_acc = episodes["delayed"].metrics.get("final_accuracy", 0.0)

    streaming_order_gap = joint_acc - delayed_acc
    trajectory_gap = episodes["together"].metrics.get("trajectory_fidelity", 0.0) - episodes["delayed"].metrics.get("trajectory_fidelity", 0.0)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "model_name": model_name,
        "usecase_id": usecase_id,
        "metrics_summary": {
            "joint_accuracy": joint_acc,
            "chronological_accuracy": chrono_acc,
            "delayed_streaming_accuracy": delayed_acc,
            "streaming_order_effect_gap": streaming_order_gap,
            "trajectory_fidelity_gap": trajectory_gap,
            "historical_revision_success": episodes["delayed"].metrics.get("historical_update_success"),
            "recency_preserved": episodes["delayed"].metrics.get("recency_preserved"),
        },
        "episodes": {cond: ep.to_dict() for cond, ep in episodes.items()},
    }

    report_path = output_dir / f"{model_name.replace('/', '_').replace('-', '_')}_{usecase_id}.json"
    report_path.write_text(json.dumps(summary, indent=2))
    print(f"\n[*] Full Benchmark Report Saved: {report_path}")
    print(f"[*] Streaming Order-Effect Gap: {streaming_order_gap:+.1%}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Benchmark Qwen2.5-VL-7B and 72B on Stream-Eval-Bench")
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen2.5-VL-7B",
        choices=["Qwen2.5-VL-7B", "Qwen2.5-VL-72B", "both", "all"],
        help="Model to benchmark",
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="mock",
        choices=["openai", "local", "mock"],
        help="Backend to use: 'openai' (vLLM/Ollama/DeepInfra/API), 'local' (transformers), or 'mock' (diagnostic baseline)",
    )
    parser.add_argument("--api-base", type=str, default="http://localhost:8000/v1", help="OpenAI-compatible base URL")
    parser.add_argument("--api-key", type=str, default="dummy", help="API key")
    parser.add_argument("--usecase", type=str, default="table_assembly_tray", help="Usecase ID")
    parser.add_argument("--device", type=str, default="cpu", help="Device for local backend")

    args = parser.parse_args()

    models_to_run = []
    if args.model in ["both", "all"]:
        models_to_run = ["Qwen2.5-VL-7B", "Qwen2.5-VL-72B"]
    else:
        models_to_run = [args.model]

    for m in models_to_run:
        if args.backend == "openai":
            backend = OpenAICompatibleBackend(
                base_url=args.api_base,
                api_key=args.api_key,
                model=m,
            )
            agent = VLMStreamingAgent(name=m, backend=backend)
        elif args.backend == "local":
            backend = LocalHuggingFaceBackend(
                model_name_or_path=f"Qwen/{m}-Instruct",
                device=args.device,
            )
            agent = VLMStreamingAgent(name=m, backend=backend)
        else:
            # Deterministic simulation baseline mimicking the observed large-VLM behavior
            agent = MockAgent(mode="oracle")

        run_qwen_benchmark(model_name=m, agent=agent, usecase_id=args.usecase)


if __name__ == "__main__":
    main()
