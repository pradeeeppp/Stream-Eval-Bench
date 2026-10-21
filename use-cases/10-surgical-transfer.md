# 10 — Surgical training: which instrument got the needle?

## User need
Which instrument received needle in earlier transfer (simulated)?

## Stream script
* **E1:** overlapping instruments obscure transfer → `receiver=unknown`.
* **E2:** gesture sequence continues (keep one transfer, order).
* **E3:** 2nd camera of *same gesture* reveals receiver.

## Expected response
Correct attribution, keep single transfer + sequence. No safety/competence inference.

## Benchmark test
Tool-role correction, fine-grained procedural.

## Candidate footage
JIGSAWS (stereo + kinematics + gestures). Narrow baseline may give too little gain — verify 2nd view actually resolves.

## RQ mapping
RQ1 fine-grained binding.
Status: `illustrative`.
