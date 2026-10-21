# 13 — Lab experiment: which vial got the transfer?

## User need
Which marked vial received earlier pipette transfer?

## Stream script
* **E1:** hand blocks target → `target=unknown`.
* **E2:** experimental order continues (keep count/order).
* **E3:** delayed overhead of *same* transfer: vial B.

## Expected response
Update target only; keep count/order. No chemical/volume inference unless evidenced. Keep `unknown` if still ambiguous.

## Benchmark test
Target correction; uncertainty retention.

## Collection route
No verified source. Controlled demo with marked vials + synced views.

## RQ mapping
RQ1 target-binding, RQ3 no-overinfer.
Status: `illustrative, needs recording`.
