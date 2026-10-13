"""Multi-video, multi-angle comprehensive evaluation suite for Stream-Eval-Bench."""

from __future__ import annotations
import argparse
import json
import pathlib
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from stream_eval.core.environment import StreamingEnvironment
from stream_eval.core.evaluator import StreamEvaluator
from stream_eval.core.agents import (
    BaseStreamingAgent,
    MockAgent,
    VLMStreamingAgent,
    LocalHuggingFaceBackend,
    OpenAICompatibleBackend,
)
from stream_eval.usecases.registry import get_usecase, list_usecases


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def run_full_suite(
    agent: BaseStreamingAgent,
    usecase_ids: Optional[List[str]] = None,
    output_dir: Optional[pathlib.Path] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Runs the complete multi-video, multi-angle evaluation suite."""
    usecase_ids = usecase_ids or list_usecases()
    output_dir = output_dir or (REPO_ROOT / "experiments" / "suite_results")
    output_dir.mkdir(parents=True, exist_ok=True)

    suite_summary = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent.get_metadata(),
        "total_usecases": len(usecase_ids),
        "results_by_usecase": {},
        "macro_metrics": {},
    }

    print("\n" + "="*70)
    print(f"STREAM-EVAL-BENCH: MULTI-VIDEO MULTI-ANGLE EVALUATION SUITE")
    print(f"Agent: {agent.name}")
    print(f"Total Use Cases: {len(usecase_ids)}")
    print("="*70 + "\n")

    all_joint_acc = []
    all_chrono_acc = []
    all_delayed_acc = []
    all_hist_success = []
    all_recency_pres = []

    for uc_id in usecase_ids:
        uc = get_usecase(uc_id)
        print(f"\n>>> Running Use Case: {uc.name} [{uc_id}]")
        print(f"    Description: {uc.description}")
        
        episodes = {}
        for cond in ["together", "chronological", "delayed"]:
            env = StreamingEnvironment(usecase=uc, schedule=cond)
            ep = env.run_episode(agent=agent, verbose=False)
            episodes[cond] = ep
            acc = ep.metrics.get("final_accuracy", 0.0)
            traj = ep.metrics.get("trajectory_fidelity", 0.0)
            print(f"    • Condition: {cond.upper():<14} | Acc: {acc:.1%} | Trajectory Fidelity: {traj:.1%}")

        joint_acc = episodes["together"].metrics.get("final_accuracy", 0.0)
        chrono_acc = episodes["chronological"].metrics.get("final_accuracy", 0.0)
        delayed_acc = episodes["delayed"].metrics.get("final_accuracy", 0.0)
        hist_succ = episodes["delayed"].metrics.get("historical_update_success")
        rec_pres = episodes["delayed"].metrics.get("recency_preserved")

        all_joint_acc.append(joint_acc)
        all_chrono_acc.append(chrono_acc)
        all_delayed_acc.append(delayed_acc)
        if hist_succ is not None:
            all_hist_success.append(1.0 if hist_succ else 0.0)
        if rec_pres is not None:
            all_recency_pres.append(1.0 if rec_pres else 0.0)

        soe_gap = joint_acc - delayed_acc

        suite_summary["results_by_usecase"][uc_id] = {
            "usecase_name": uc.name,
            "joint_accuracy": joint_acc,
            "chronological_accuracy": chrono_acc,
            "delayed_accuracy": delayed_acc,
            "streaming_order_effect_gap": soe_gap,
            "historical_update_success": hist_succ,
            "recency_preserved": rec_pres,
            "episodes": {c: ep.to_dict() for c, ep in episodes.items()},
        }

    # Macro averages
    macro_joint = sum(all_joint_acc) / len(all_joint_acc) if all_joint_acc else 0.0
    macro_chrono = sum(all_chrono_acc) / len(all_chrono_acc) if all_chrono_acc else 0.0
    macro_delayed = sum(all_delayed_acc) / len(all_delayed_acc) if all_delayed_acc else 0.0
    macro_gap = macro_joint - macro_delayed
    hist_rate = sum(all_hist_success) / len(all_hist_success) if all_hist_success else 0.0
    rec_rate = sum(all_recency_pres) / len(all_recency_pres) if all_recency_pres else 0.0

    suite_summary["macro_metrics"] = {
        "macro_joint_accuracy": macro_joint,
        "macro_chronological_accuracy": macro_chrono,
        "macro_delayed_accuracy": macro_delayed,
        "macro_streaming_order_gap": macro_gap,
        "macro_historical_revision_rate": hist_rate,
        "macro_recency_preservation_rate": rec_rate,
    }

    # Save outputs
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = agent.name.replace(" ", "_").replace("/", "_").replace("(", "_").replace(")", "_")
    report_file = output_dir / f"suite_{safe_name}_{timestamp_str}.json"
    report_file.write_text(json.dumps(suite_summary, indent=2))

    # Print summary table
    print("\n" + "="*70)
    print("SUITE EVALUATION RESULTS SUMMARY")
    print("="*70)
    print(f"{'Use Case':<32} | {'Joint':<7} | {'Chrono':<7} | {'Delayed':<7} | {'Gap':<7} | {'Hist Upd':<8} | {'Rec Pres':<8}")
    print("-" * 85)
    for uc_id, res in suite_summary["results_by_usecase"].items():
        hu = str(res['historical_update_success'])
        rp = str(res['recency_preserved'])
        print(f"{uc_id[:32]:<32} | {res['joint_accuracy']:6.1%} | {res['chronological_accuracy']:6.1%} | {res['delayed_accuracy']:6.1%} | {res['streaming_order_effect_gap']:+6.1%} | {hu:<8} | {rp:<8}")
    print("-" * 85)
    print(f"{'MACRO AVERAGE':<32} | {macro_joint:6.1%} | {macro_chrono:6.1%} | {macro_delayed:6.1%} | {macro_gap:+6.1%} | {hist_rate:6.1%} | {rec_rate:6.1%}")
    print("="*70)
    print(f"\n[*] Audited Suite Report Saved: {report_file}\n")

    return suite_summary


def main():
    parser = argparse.ArgumentParser(description="Run Stream-Eval-Bench Multi-Video Evaluation Suite")
    parser.add_argument(
        "--agent",
        type=str,
        default="mock-oracle",
        choices=["mock-oracle", "mock-no-revision", "mock-recency-bias", "mock-intermediate-error", "openai", "local"],
        help="Agent backend",
    )
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-VL-7B-Instruct")
    parser.add_argument("--api-base", type=str, default="http://localhost:8000/v1")
    parser.add_argument("--api-key", type=str, default="dummy")
    parser.add_argument("--device", type=str, default="cpu")

    args = parser.parse_args()

    if args.agent.startswith("mock-"):
        mode = args.agent.replace("mock-", "")
        agent = MockAgent(mode=mode)
    elif args.agent == "openai":
        backend = OpenAICompatibleBackend(base_url=args.api_base, api_key=args.api_key, model=args.model)
        agent = VLMStreamingAgent(name=f"OpenAI-{args.model}", backend=backend)
    elif args.agent == "local":
        backend = LocalHuggingFaceBackend(model_name_or_path=args.model, device=args.device)
        agent = VLMStreamingAgent(name=f"Local-{args.model}", backend=backend)
    else:
        agent = MockAgent(mode="oracle")

    run_full_suite(agent=agent)


if __name__ == "__main__":
    main()
