# 12 — Parcel logistics: which trolley got the parcel?

## User need
Which trolley received parcel during original loading?

## Stream script
* **E1:** body hides trolley label during load → `dest=unknown`.
* **E2:** subsequent transfers (preserve).
* **E3:** 2nd recording of *that* loading: trolley B. Note: seeing parcel on B *now* ≠ proof of origin.

## Expected response
Correct original dest, keep one loading + later transfers. Distinguish historical vs current location.

## Benchmark test
Destination correction; history/current split.

## Collection route
No verified source. Record synced views of controlled transfers with readable parcel/trolley IDs.

## RQ mapping
RQ1 + RQ3 history-vs-current (like tray ON/OFF).
Status: `illustrative, needs recording`.
