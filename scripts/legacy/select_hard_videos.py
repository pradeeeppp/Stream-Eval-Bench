from huggingface_hub import hf_hub_download
import csv
import ast

p = hf_hub_download(repo_id='firstep-ai/MV-Bench-mini', filename='resampled_data.csv', repo_type='dataset')
with open(p, encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print(f"Total rows in MV-Bench-mini: {len(rows)}")

tasks = {}
for r in rows:
    q = r['question']
    if 'next' in q.lower() or 'predict' in q.lower():
        cat = 'Action Prediction (Future Horizon)'
    elif 'how many' in q.lower() or 'count' in q.lower():
        cat = 'Action & Event Counting'
    elif 'when' in q.lower() or 'sequence' in q.lower() or 'order' in q.lower() or 'first' in q.lower() or 'second' in q.lower():
        cat = 'Temporal Sequence & Localization'
    elif 'which object' in q.lower() or 'taken' in q.lower() or 'put down' in q.lower():
        cat = 'Object Possession & State Tracking'
    elif 'turn on' in q.lower() or 'state' in q.lower() or 'change' in q.lower() or 'temperature' in q.lower():
        cat = 'State Change & Physical Affordance'
    elif 'interacts' in q.lower() or 'multiple' in q.lower():
        cat = 'Multi-Object Interaction'
    elif 'direction' in q.lower() or 'moving' in q.lower() or 'camera' in q.lower():
        cat = 'Egocentric Motion & Direction'
    else:
        cat = 'Fine-Grained Action Understanding'
    tasks.setdefault(cat, []).append(r)

for cat, items in sorted(tasks.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n[{len(items):2d} videos] Category: {cat}")
    for sample in items[:2]:
        q_text = sample['question'][:80]
        cands = ast.literal_eval(sample['candidates'])
        print(f"   ID: {sample['relpath']:<15} | Ans: {sample['answer']:<30} | Q: {q_text}")
