# 01 — Sports companion: who actually touched the ball?

## User need
Viewer wants accurate account despite fast action, occlusion, replays.

## Stream script
* **E1 (t1):** wide shot, one shot on goal, defender blocks view → touch identity `unknown`, count=1.
* **E2 (t2):** play continues (another passage).
* **E3 (t3, late):** slow-mo replay of *same* shot shows touch by #8. Linkage: replay of same attempt (broadcaster replay tag).

## Expected response
> “The replay shows #8 made the final touch on the earlier shot. Same attempt, not another shot.” Update touch, keep shot id/time/count/sequence. Do NOT treat replay position as live ball position.

## Benchmark test
Ask before/after: who touched, how many attempts, what is live now. Conditions Joint / Chrono / Delayed. Failure: early guess, miss detail, extra attempt, overwrite live with replay.

## RQ mapping
RQ1 (bind replay to right shot among similar shots), RQ3 (count + live preserve, replay≠new event).

## Failure modes
guess-early, miss-reveal, double-count, live-overwrite.

## Candidate footage
Illustrative; needs replay-tagged match clip. E.g. NBA replay clip pattern in `experiments/replay_candidates/prepare.py` (URL template only, not verified).

## To implement
- [ ] E1/E2/E3 timestamps, shot-id schema `{touch, count, live}`, `expected_final={touch:#8, count:1}`
- [ ] Controls: irrelevant later play, other-shot replay, new similar shot
- [ ] G1 (replay alone names #8), G2 (joint binds), G3 (forward tracks count)
Status: `illustrative`.
