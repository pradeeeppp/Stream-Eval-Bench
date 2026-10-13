"""Experiment runner and CLI for Stream-Eval-Bench."""

from __future__ import annotations
import argparse
import json
import pathlib
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from stream_eval.core.environment import StreamingEnvironment
from stream_eval.core.evaluator import StreamEvaluator
from stream_eval.core.agents import (
    BaseStreamingAgent,
    MockAgent,
    VLMStreamingAgent,
    GradioVLMBackend,
    LocalHuggingFaceBackend,
    OpenAICompatibleBackend,
)
from stream_eval.usecases.registry import get_usecase, list_usecases


def build_agent(agent_type: str, args: argparse.Namespace) -> BaseStreamingAgent:
    a_type = agent_type.lower()
    if a_type == "mock-oracle":
        return MockAgent(mode="oracle")
    elif a_type == "mock-recency-bias":
        return MockAgent(mode="recency_bias")
    elif a_type == "mock-no-revision":
        return MockAgent(mode="no_revision")
    elif a_type == "mock-intermediate-error":
        return MockAgent(mode="intermediate_error")
    elif a_type == "gradio":
        backend = GradioVLMBackend(host=getattr(args, "host", "https://qwen-qwen3-vl-235b-a22b-instruct-demo.hf.space"))
        return VLMStreamingAgent(name="Qwen3-VL-Gradio", backend=backend)
    elif a_type == "local":
        backend = LocalHuggingFaceBackend(
            model_name_or_path=getattr(args, "model", "Qwen/Qwen2.5-VL-7B-Instruct"),
            device=getattr(args, "device", "cpu"),
        )
        return VLMStreamingAgent(name=f"Local-{args.model}", backend=backend)
    elif a_type == "openai":
        backend = OpenAICompatibleBackend(
            base_url=getattr(args, "api_base", "http://localhost:8000/v1"),
            api_key=getattr(args, "api_key", "dummy"),
            model=getattr(args, "model", "qwen-vl"),
        )
        return VLMStreamingAgent(name=f"OpenAI-{args.model}", backend=backend)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


def run_experiment(
    usecase_id: str,
    conditions: List[str],
    agent: BaseStreamingAgent,
    output_dir: Optional[pathlib.Path] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    usecase = get_usecase(usecase_id)
    episodes = []

    print(f"\n=======================================================")
    print(f"Running Experiment: {usecase.name} [{usecase_id}]")
    print(f"Agent: {agent.name}")
    print(f"Conditions: {conditions}")
    print(f"=======================================================\n")

    for cond in conditions:
        print(f"--> Starting condition: {cond.upper()} ...")
        env = StreamingEnvironment(usecase=usecase, schedule=cond)
        ep = env.run_episode(agent=agent, verbose=verbose)
        episodes.append(ep)

        # Print quick summary
        print(f"    Finished {cond.upper()}:")
        print(f"    - Final State: {ep.final_state}")
        print(f"    - Expected Final: {ep.expected_final_state}")
        print(f"    - Final Accuracy: {ep.metrics.get('final_accuracy', 0.0):.1%}")
        print(f"    - Trajectory Fidelity: {ep.metrics.get('trajectory_fidelity', 0.0):.1%}")
        if "historical_update_success" in ep.metrics and ep.metrics["historical_update_success"] is not None:
            print(f"    - Historical Update: {ep.metrics['historical_update_success']}")
            print(f"    - Recency Preserved: {ep.metrics['recency_preserved']}")
        print()

    comparative = StreamEvaluator.compute_comparative_summary(episodes)

    report = {
        "timestamp": datetime.now().isoformat(),
        "usecase_id": usecase_id,
        "usecase_name": usecase.name,
        "agent": agent.get_metadata(),
        "episodes": [ep.to_dict() for ep in episodes],
        "comparative_analysis": comparative,
    }

    if output_dir:
        output_dir = pathlib.Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{usecase_id}_{agent.name.lower().replace(' ', '_')}_{timestamp_str}.json"
        target_path = output_dir / filename
        target_path.write_text(json.dumps(report, indent=2))
        print(f"[*] Saved full experiment report to: {target_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Stream-Eval-Bench Experiment Runner")
    parser.add_argument(
        "--usecase",
        type=str,
        default="table_assembly_tray",
        help=f"Usecase ID or 'all'. Available: {list_usecases()}",
    )
    parser.add_argument(
        "--condition",
        type=str,
        default="all",
        help="Condition to test: chronological, delayed, together, or all",
    )
    parser.add_argument(
        "--agent",
        type=str,
        default="mock-oracle",
        choices=[
            "mock-oracle",
            "mock-recency-bias",
            "mock-no-revision",
            "mock-intermediate-error",
            "gradio",
            "local",
            "openai",
        ],
        help="Agent backend to evaluate",
    )
    parser.add_argument("--host", type=str, default="https://qwen-qwen3-vl-235b-a22b-instruct-demo.hf.space")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-VL-7B-Instruct")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--output-dir", type=str, default="experiments/runs")
    parser.add_argument("--quiet", action="store_true", help="Suppress step-by-step logs")

    args = parser.parse_args()

    # Determine use cases
    if args.usecase.lower() == "all":
        target_usecases = list_usecases()
    else:
        target_usecases = [args.usecase]

    # Determine conditions
    if args.condition.lower() == "all":
        target_conditions = ["together", "chronological", "delayed"]
    else:
        target_conditions = [args.condition.lower()]

    agent = build_agent(args.agent, args)
    out_dir = pathlib.Path(args.output_dir)

    for uc_id in target_usecases:
        run_experiment(
            usecase_id=uc_id,
            conditions=target_conditions,
            agent=agent,
            output_dir=out_dir,
            verbose=not args.quiet,
        )


if __name__ == "__main__":
    main()
