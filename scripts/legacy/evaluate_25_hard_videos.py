"""Runs multi-condition streaming evaluation across 25 hard Hugging Face videos."""

import ast
import json
import os
import pathlib
import re
import time
from typing import Any, Dict, List
import decord
import numpy as np
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
PROTOTYPE_DIR = REPO_ROOT / "experiments" / "hf_hard_prototype"
MANIFEST_PATH = PROTOTYPE_DIR / "manifest.json"
RESULTS_PATH = PROTOTYPE_DIR / "evaluation_results.json"


def normalize_answer(text: str, candidates: List[str]) -> str:
    """Extracts or normalizes model response to match candidate options."""
    clean = text.strip()
    # Check exact match
    for c in candidates:
        if c.strip().lower() in clean.lower():
            return c.strip()
    # Fallback to option letter if present (A, B, C...)
    m = re.search(r"\b([A-E])\b", clean, re.IGNORECASE)
    if m:
        idx = ord(m.group(1).upper()) - ord("A")
        if 0 <= idx < len(candidates):
            return candidates[idx].strip()
    return clean


def main():
    print("=" * 80)
    print("STREAM-EVAL-BENCH: 25 HARD HUGGING FACE VIDEOS EVALUATION")
    print("=" * 80)

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found at {MANIFEST_PATH}")

    manifest: List[Dict[str, Any]] = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(manifest)} hard video benchmark tasks from manifest.")

    print("\n>>> Initializing Vision-Language Model (SmolVLM-256M-Instruct on CPU)...")
    model_id = "HuggingFaceTB/SmolVLM-256M-Instruct"
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForImageTextToText.from_pretrained(model_id, dtype=torch.float32).eval()
    print("Model initialized successfully.")

    results_by_video = []

    for item in manifest:
        idx = item["index"]
        vid_id = item["id"]
        fname = item["filename"]
        vpath = REPO_ROOT / item["video_path"]
        cat = item["category"]
        q = item["question"]
        cands = item["candidates"]
        gt = item["ground_truth_answer"].strip()

        print(f"\n[{idx:2d}/25] Evaluating: {fname} | Category: {cat}")
        print(f"       Question: {q}")
        print(f"       Ground Truth: {gt}")

        vr = decord.VideoReader(str(vpath))
        num_frames = len(vr)

        # 4 evenly spaced frames for joint evaluation, resized to standard 384px for fast CPU evaluation
        joint_indices = [0, num_frames // 3, 2 * num_frames // 3, num_frames - 1]
        all_frames = []
        for i in joint_indices:
            im = Image.fromarray(vr[i].asnumpy())
            im.thumbnail((384, 384))
            all_frames.append(im)

        # Temporal split into 2 packets: Packet A (earlier), Packet B (later)
        # Packet A: frames 0, 1
        # Packet B: frames 2, 3
        frames_packet_a = all_frames[:2]
        frames_packet_b = all_frames[2:]

        # Formulate candidate choices prompt
        options_text = ", ".join([f"'{c}'" for c in cands])
        prompt_instruction = (
            f"{q}\n"
            f"Choose the correct answer from: [{options_text}].\n"
            f"Answer with ONLY the exact chosen text."
        )

        # -------------------------------------------------------------
        # Condition 1: Joint (Both packets together, all 4 frames)
        # -------------------------------------------------------------
        joint_msgs = [
            {
                "role": "user",
                "content": [{"type": "video"}, {"type": "text", "text": prompt_instruction}],
            }
        ]
        joint_txt = processor.apply_chat_template(joint_msgs, add_generation_prompt=True)
        joint_inp = processor(text=joint_txt, videos=[all_frames], return_tensors="pt")

        t0 = time.time()
        with torch.inference_mode():
            out_joint = model.generate(**joint_inp, max_new_tokens=40, do_sample=False)
        raw_joint = processor.batch_decode(
            out_joint[:, joint_inp["input_ids"].shape[1] :], skip_special_tokens=True
        )[0]
        joint_latency = time.time() - t0
        norm_joint = normalize_answer(raw_joint, cands)
        joint_correct = (norm_joint.lower() == gt.lower())

        # -------------------------------------------------------------
        # Condition 2: Chronological Streaming (Packet A -> Packet B)
        # -------------------------------------------------------------
        # Step 1: Packet A
        p1_msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "video"},
                    {
                        "type": "text",
                        "text": f"Early video segment (time 0-50%).\n{prompt_instruction}",
                    },
                ],
            }
        ]
        p1_txt = processor.apply_chat_template(p1_msgs, add_generation_prompt=True)
        p1_inp = processor(text=p1_txt, videos=[frames_packet_a], return_tensors="pt")
        with torch.inference_mode():
            out_p1 = model.generate(**p1_inp, max_new_tokens=40, do_sample=False)
        mem_step1 = processor.batch_decode(
            out_p1[:, p1_inp["input_ids"].shape[1] :], skip_special_tokens=True
        )[0].strip()

        # Step 2: Packet B arrives, receives prior memory
        p2_msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "video"},
                    {
                        "type": "text",
                        "text": (
                            f"Continuing stream (time 50-100%).\n"
                            f"Your memory from earlier: '{mem_step1}'.\n"
                            f"Update your answer based on the full chronological stream.\n"
                            f"{prompt_instruction}"
                        ),
                    },
                ],
            }
        ]
        p2_txt = processor.apply_chat_template(p2_msgs, add_generation_prompt=True)
        p2_inp = processor(text=p2_txt, videos=[frames_packet_b], return_tensors="pt")
        with torch.inference_mode():
            out_p2 = model.generate(**p2_inp, max_new_tokens=40, do_sample=False)
        raw_chrono = processor.batch_decode(
            out_p2[:, p2_inp["input_ids"].shape[1] :], skip_special_tokens=True
        )[0]
        norm_chrono = normalize_answer(raw_chrono, cands)
        chrono_correct = (norm_chrono.lower() == gt.lower())

        # -------------------------------------------------------------
        # Condition 3: Delayed Streaming (Packet B arrives FIRST, then Packet A arrives LATE)
        # -------------------------------------------------------------
        # Step 1: Later footage arrives first
        d1_msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "video"},
                    {
                        "type": "text",
                        "text": f"Arrived packet (later segment time 50-100%).\n{prompt_instruction}",
                    },
                ],
            }
        ]
        d1_txt = processor.apply_chat_template(d1_msgs, add_generation_prompt=True)
        d1_inp = processor(text=d1_txt, videos=[frames_packet_b], return_tensors="pt")
        with torch.inference_mode():
            out_d1 = model.generate(**d1_inp, max_new_tokens=40, do_sample=False)
        mem_delayed1 = processor.batch_decode(
            out_d1[:, d1_inp["input_ids"].shape[1] :], skip_special_tokens=True
        )[0].strip()

        # Step 2: Delayed retrospective Packet A arrives
        d2_msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "video"},
                    {
                        "type": "text",
                        "text": (
                            f"Retrospective delayed packet just arrived (older capture time 0-50%).\n"
                            f"Your previous state belief was: '{mem_delayed1}'.\n"
                            f"Revise your historical understanding without corrupting facts.\n"
                            f"{prompt_instruction}"
                        ),
                    },
                ],
            }
        ]
        d2_txt = processor.apply_chat_template(d2_msgs, add_generation_prompt=True)
        d2_inp = processor(text=d2_txt, videos=[frames_packet_a], return_tensors="pt")
        with torch.inference_mode():
            out_d2 = model.generate(**d2_inp, max_new_tokens=40, do_sample=False)
        raw_delayed = processor.batch_decode(
            out_d2[:, d2_inp["input_ids"].shape[1] :], skip_special_tokens=True
        )[0]
        norm_delayed = normalize_answer(raw_delayed, cands)
        delayed_correct = (norm_delayed.lower() == gt.lower())

        order_gap = 1.0 if (joint_correct and not delayed_correct) else 0.0

        print(f"       • Joint:       {norm_joint:<25} | Correct: {joint_correct!s:<5}")
        print(f"       • Chrono:      {norm_chrono:<25} | Correct: {chrono_correct!s:<5}")
        print(f"       • Delayed:     {norm_delayed:<25} | Correct: {delayed_correct!s:<5}")
        print(f"       • Order Gap:   {order_gap:+.0f}")

        video_record = {
            "index": idx,
            "id": vid_id,
            "category": cat,
            "question": q,
            "ground_truth": gt,
            "joint": {
                "raw": raw_joint.strip(),
                "normalized": norm_joint,
                "correct": joint_correct,
                "latency_seconds": round(joint_latency, 2),
            },
            "chronological": {
                "step1_memory": mem_step1,
                "raw": raw_chrono.strip(),
                "normalized": norm_chrono,
                "correct": chrono_correct,
            },
            "delayed": {
                "step1_memory": mem_delayed1,
                "raw": raw_delayed.strip(),
                "normalized": norm_delayed,
                "correct": delayed_correct,
            },
            "streaming_order_gap": order_gap,
        }
        results_by_video.append(video_record)

    # Compute Macro Metrics
    total = len(results_by_video)
    macro_joint = sum(1 for r in results_by_video if r["joint"]["correct"]) / total
    macro_chrono = sum(1 for r in results_by_video if r["chronological"]["correct"]) / total
    macro_delayed = sum(1 for r in results_by_video if r["delayed"]["correct"]) / total
    macro_gap = macro_joint - macro_delayed

    # Breakdown by category
    category_metrics = {}
    for r in results_by_video:
        c = r["category"]
        category_metrics.setdefault(c, {"total": 0, "joint": 0, "chrono": 0, "delayed": 0})
        category_metrics[c]["total"] += 1
        if r["joint"]["correct"]:
            category_metrics[c]["joint"] += 1
        if r["chronological"]["correct"]:
            category_metrics[c]["chrono"] += 1
        if r["delayed"]["correct"]:
            category_metrics[c]["delayed"] += 1

    summary = {
        "benchmark_name": "Stream-Eval-Bench: 25 Hard Hugging Face Videos Prototype",
        "model": model_id,
        "total_videos": total,
        "macro_metrics": {
            "joint_accuracy": round(macro_joint, 3),
            "chronological_accuracy": round(macro_chrono, 3),
            "delayed_accuracy": round(macro_delayed, 3),
            "streaming_order_gap": round(macro_gap, 3),
        },
        "by_category": {
            k: {
                "total": v["total"],
                "joint_acc": round(v["joint"] / v["total"], 3),
                "chrono_acc": round(v["chrono"] / v["total"], 3),
                "delayed_acc": round(v["delayed"] / v["total"], 3),
                "order_gap": round((v["joint"] - v["delayed"]) / v["total"], 3),
            }
            for k, v in category_metrics.items()
        },
        "per_video_results": results_by_video,
    }

    RESULTS_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETED SUCCESSFULLY")
    print(f"Results saved to: {RESULTS_PATH}")
    print(f"Macro Joint Accuracy:         {macro_joint:.1%}")
    print(f"Macro Chronological Accuracy: {macro_chrono:.1%}")
    print(f"Macro Delayed Accuracy:       {macro_delayed:.1%}")
    print(f"Streaming Order Effect Gap:   {macro_gap:+.1%}")
    print("=" * 80)


if __name__ == "__main__":
    main()
