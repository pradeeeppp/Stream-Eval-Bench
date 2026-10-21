# 06 — Traffic incident review: order of actions

## User need
Reconstruct order in road encounter.

## Stream script
* **E1:** dashcam ambiguous: pedestrian entered before/after vehicle turn? → `order=unknown`.
* **E2:** encounter continues (single encounter, keep count=1).
* **E3:** overhead of *same interval*, later: pedestrian first. Linkage: same interval timestamps.

## Expected response
Revise order only, keep one encounter + original time. Establishes visible sequence, NOT legal fault.

## Benchmark test
Temporal-order revision without duplicating encounter or mixing with later crossing.

## Candidate footage
WTS staged traffic (overhead + vehicle views). Inspect gallery; illustrative only. Check redistribution before release. [WTS dataset/gallery](https://example.com) — replace with verified link when curating.

## RQ mapping
RQ1 order-binding, RQ3 no-duplicate.
Status: `illustrative`.
