# 03 — Cooking assistant: which ingredient went into the bowl?

## User need
Accurate prep history when hands/containers block camera.

## Stream script
* **E1:** one spoonful from unreadable container → `ingredient=unknown, quantity=1`.
* **E2:** stirring + another ingredient addition (preserve).
* **E3:** delayed side-cam of *original* spoonful, label → sugar. Linkage: same transfer.

## Expected response
> “That earlier spoonful was sugar.” Update E1 ingredient only; keep quantity 1, position, later actions. Do NOT count replay as spoonful 2 or claim current bowl contents visible if not.

## Benchmark test
What was step-1, how many additions, what was last seen. Control: label visible later but *unlinked* to transfer → must stay `unknown`.

## RQ mapping
RQ1 (link label to transfer), RQ3 (count preserve, no unsupported inference).

## To implement
- [ ] schema `{step1_ingredient, additions_count, live_step}`, kitchen multi-view recording
Status: `illustrative`.
