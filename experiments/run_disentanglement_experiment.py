"""Empirical evaluation of Causal Retrospective Revision on SmolVLM-256M-Instruct."""

import json
import time
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText

R = Path(__file__).resolve().parent.parent
INPUTS_DIR = R / 'experiments/evidence_revision_pilot/direct_revision/inputs'
OUTPUT_DIR = R / 'experiments/disentanglement_proof'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_ID = "HuggingFaceTB/SmolVLM-256M-Instruct"

print(f"Loading {MODEL_ID} from local cache...")
processor = AutoProcessor.from_pretrained(MODEL_ID)
model = AutoModelForImageTextToText.from_pretrained(
    MODEL_ID,
    dtype=torch.float32,
    low_cpu_mem_usage=True
).eval()
print("Model ready!")

def generate_answer(images, prompt_text, max_new_tokens=60):
    content = []
    for _ in images:
        content.append({"type": "image"})
    content.append({"type": "text", "text": prompt_text})
    
    messages = [{"role": "user", "content": content}]
    formatted_prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    inputs = processor(text=[formatted_prompt], images=images if images else None, return_tensors="pt")
    
    t0 = time.time()
    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    elapsed = time.time() - t0
    
    output_text = processor.batch_decode(
        generated_ids[:, inputs.input_ids.shape[1]:],
        skip_special_tokens=True
    )[0].strip()
    
    return output_text, elapsed

# Load input images
im_e1_partial = Image.open(INPUTS_DIR / 'printer_E1_partial.png').convert('RGB')
im_e2_partial = Image.open(INPUTS_DIR / 'printer_E2_partial.png').convert('RGB')
im_e2_full = Image.open(INPUTS_DIR / 'printer_E2_full.png').convert('RGB')

results = {}

# -------------------------------------------------------------
# GATE 1: Standalone Perception Gate (P-Gate)
# -------------------------------------------------------------
print("\n[1/4] Running Gate 1: Standalone Perception Gate...")
p_prompt = (
    "Look at this printer display. Is the central rectangular screen illuminated or dark? "
    "Answer with only 'illuminated' or 'dark'."
)
p_out, p_time = generate_answer([im_e2_full], p_prompt)
p_pass = "dark" in p_out.lower() and "illuminated" not in p_out.lower()
results["gate_1_perception"] = {
    "prompt": p_prompt,
    "response": p_out,
    "expected": "dark",
    "passed": p_pass,
    "seconds": p_time
}
print(f"Gate 1 Output: '{p_out}' (Passed: {p_pass}, {p_time:.2f}s)")

# -------------------------------------------------------------
# GATE 2: Static / Joint Context Gate (J-Gate)
# -------------------------------------------------------------
print("\n[2/4] Running Gate 2: Static Joint Context Gate...")
j_prompt = (
    "You are given 3 images:\n"
    "Image 1 is earlier record E1 (partially obscured).\n"
    "Image 2 is later record E2 (partially obscured).\n"
    "Image 3 is a newly available clear reveal view of one record.\n"
    "Does Image 3 match E1 or E2? And is that revealed screen dark or illuminated?\n"
    "Answer in format: Match: [E1 or E2], Screen: [dark or illuminated]."
)
j_out, j_time = generate_answer([im_e1_partial, im_e2_partial, im_e2_full], j_prompt)
j_matched_e2 = "e2" in j_out.lower() and "e1" not in j_out.lower().split("match")[1] if "match" in j_out.lower() else "e2" in j_out.lower()
j_dark = "dark" in j_out.lower()
j_pass = j_matched_e2 and j_dark
results["gate_2_joint"] = {
    "prompt": j_prompt,
    "response": j_out,
    "expected": "Match: E2, Screen: dark",
    "passed": j_pass,
    "seconds": j_time
}
print(f"Gate 2 Output: '{j_out}' (Passed: {j_pass}, {j_time:.2f}s)")

# -------------------------------------------------------------
# GATE 3: Forward Chronological Memory Gate (C-Gate)
# -------------------------------------------------------------
print("\n[3/4] Running Gate 3: Forward Chronological Memory Gate...")
c1_prompt = "Record E1 is received. Is the screen status known, or unknown due to occlusion? Answer: known or unknown."
c1_out, c1_time = generate_answer([im_e1_partial], c1_prompt)

c2_prompt = (
    f"Previous memory: E1 screen is {c1_out}.\n"
    "Now record E2 is received. Can you observe E2's screen status, or is it unknown? Answer: known or unknown."
)
c2_out, c2_time = generate_answer([im_e2_partial], c2_prompt)
c_pass = "unknown" in c1_out.lower() or "obscured" in c1_out.lower()
results["gate_3_chronological"] = {
    "step1_response": c1_out,
    "step2_response": c2_out,
    "passed": c_pass,
    "seconds": c1_time + c2_time
}
print(f"Gate 3 Output: Step 1: '{c1_out}', Step 2: '{c2_out}' (Passed: {c_pass})")

# -------------------------------------------------------------
# TARGET TEST: Causal Retrospective Revision (CRR)
# -------------------------------------------------------------
print("\n[4/4] Running Target Test: Causal Retrospective Revision...")
# In streaming step 3, the reveal arrives along with the agent's prior belief:
stream_prompt = (
    "STREAMING UPDATE STEP 3:\n"
    "Your previous state memory was: Record E1 screen is unknown; Record E2 screen is unknown.\n"
    "Now a delayed retrospective packet arrives showing this clear view.\n"
    "Task: Update historical records without confusing event identities.\n"
    "Which record does this reveal update (E1 or E2), and what is its updated status?\n"
    "Output: Updated Record: [E1 or E2], Value: [dark or illuminated]."
)
crr_out, crr_time = generate_answer([im_e2_full], stream_prompt)
crr_matched_e2 = "e2" in crr_out.lower()
crr_val_dark = "dark" in crr_out.lower()
crr_success = crr_matched_e2 and crr_val_dark

results["target_test_crr"] = {
    "prompt": stream_prompt,
    "response": crr_out,
    "expected": "Updated Record: E2, Value: dark",
    "updated_e2_correctly": crr_matched_e2,
    "value_dark_correctly": crr_val_dark,
    "success": crr_success,
    "seconds": crr_time
}
print(f"Target CRR Output: '{crr_out}' (Success: {crr_success}, {crr_time:.2f}s)")

# Save full results
report_path = OUTPUT_DIR / 'results.json'
report_path.write_text(json.dumps(results, indent=2))
print(f"\nSaved full audited report to: {report_path}")
