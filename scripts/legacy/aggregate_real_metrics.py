import json

print("="*80)
print("1. DISENTANGLEMENT PROOF (SmolVLM-256M-Instruct on CPU)")
print("="*80)
with open('experiments/disentanglement_proof/results.json') as f:
    d = json.load(f)
for k, v in d.items():
    passed = v.get('passed', v.get('success'))
    secs = v.get('seconds', 0)
    print(f"  {k:<25}: passed={passed!s:<6} | latency={secs:.1f}s")

print("\n" + "="*80)
print("2. TWO-CLIP DIAGNOSTIC (Qwen3-VL-235B on HuggingFace Space)")
print("="*80)
with open('experiments/two_clip_diagnostic/results.json') as f:
    d = json.load(f)
for r in d['results']:
    print(f"  {r['id']:<18}: parsed={r['parsed']} | elapsed={r['elapsed_seconds']:.1f}s")
print("  Audit matches:", d['audit']['exact_match_by_step'])

print("\n" + "="*80)
print("3. FIXED HYPOTHESIS MULTI-EVENT (Qwen3-VL-235B Frontier Model)")
print("="*80)
with open('experiments/fixed_hypothesis/results.json') as f:
    d = json.load(f)
for v in d['conditions']:
    name = v.get('condition_name') or v.get('name') or v.get('id')
    p = v.get('parsed')
    sc = v.get('score', {}).get('pass')
    print(f"  {name:<26}: parsed={p} | pass={sc}")

print("\n" + "="*80)
print("4. DIRECT REVISION 30-CALL PILOT (Qwen2-VL-2B-Instruct on CPU)")
print("="*80)
with open('experiments/evidence_revision_pilot/direct_revision/results/qwen.json') as f:
    d = json.load(f)
tests = {}
for r in d['results']:
    t = r['condition']
    tests.setdefault(t, {'total': 0, 'pass': 0})
    tests[t]['total'] += 1
    if r['score'].get('pass'):
        tests[t]['pass'] += 1
for t, s in tests.items():
    pct = s['pass'] / s['total']
    print(f"    {t:<22}: {s['pass']}/{s['total']} ({pct:.1%})")

print("\n" + "="*80)
print("5. NATIVE MP4 STREAMING TRIAL (Qwen3-VL-2B on Continuous Video Packets)")
print("="*80)
with open('experiments/evidence_revision_pilot/streaming_trial/results/run.json') as f:
    d = json.load(f)
for r in d['results']:
    cid = r.get('case')
    cnd = r.get('condition')
    stp = r.get('step')
    prs = r.get('parsed')
    secs = r.get('seconds')
    sec_str = f"{secs:.1f}s" if secs else "N/A"
    print(f"    {cid}_{cnd}_{stp}: parsed={prs} | latency={sec_str}")
