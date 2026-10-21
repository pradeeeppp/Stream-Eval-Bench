# 02 — Multi-camera incident review: which bag was picked up?

## User need
Operator wants one consistent record when views arrive at different times.

## Stream script
* **E1:** cam A, person-1 picks bag near doorway, bag obscured → description `unknown`.
* **E2:** person-2 picks another bag soon after (competitor, must preserve).
* **E3:** delayed cam B, clearer angle of *first* pickup, red tag visible. Linkage: capture timestamps / overlapping actions.

## Expected response
> “The bag in the first pickup had a red tag.” Update only E1 description. Keep 2 pickups, order, person-2 record. Do NOT infer ownership/theft/intent.

## Benchmark test
Attach tag to correct pickup among similar candidates. Vary delay + intervening count. Joint / Chrono / Delayed + Gap. Failure: merge events, 3rd pickup, wrong-person bind.

## RQ mapping
RQ1 (core bind-among-competitors), RQ3 (no merge/duplicate), RQ2 (does early `unknown` vs guess change binding?).

## Candidate footage
No verified pair in repo; design only. Record synchronized A/B with readable tags if implementing.

## To implement
- [ ] packet split A/B, schema `{pickup1_desc, pickup2_desc, count}`, controls: B-replay-of-pickup2, new 3rd pickup
Status: `illustrative`.
