# 11 — Retail checkout: which variant on the tray?

## User need
Which product variant was placed?

## Stream script
* **E1:** carton placed, label hidden → `variant=unknown, count=1`.
* **E2:** checkout continues.
* **E3:** delayed close-up of *original* placement reveals variant.

## Expected response
Update identity of counted item; no extra placement/bill.

## Benchmark test
Attribute refinement with stable counts.

## Candidate footage
AI City Challenge 2022 checkout is single-view, not paired-ready. Needs alternative or controlled recording. See challenge data + paper when scoping.

## RQ mapping
RQ3 count-stability.
Status: `illustrative, needs source`.
