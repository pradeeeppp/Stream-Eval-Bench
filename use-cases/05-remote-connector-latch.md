# 05 — Remote assistance: was the connector latched before the next step?

## User need
Revise past manipulation while following ongoing task.

## Stream script
* **E1:** insert connector, hand hides latch → `inserted=yes, latched=unknown`.
* **E2:** worker moves to cable-routing (live, must track).
* **E3:** delayed close-up of *same* insertion shows latch engage. Live continues in separate view.

## Expected response
> “Close-up confirms earlier insertion latched. Current step is cable routing.” Update latch, keep current-step. Do NOT ask to repeat insertion.

## Benchmark test
Score history update + live recognition jointly. Failure: lose current task, repeat instruction, delayed-as-live. Requires visible live input (2nd feed/split); hidden events not scored observable.

## RQ mapping
RQ3 live-preservation stress test + RQ1 bind.

## To implement
- [ ] dual-feed packets (delayed E1 + live E2), schema `{latched, current_step}`
Status: `illustrative`.
