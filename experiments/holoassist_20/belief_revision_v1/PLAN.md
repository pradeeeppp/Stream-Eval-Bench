# Twenty-video belief revision analysis

Requested 2026-11-04. Model selected by the user: Qwen2.5-VL-3B, matching the
supplied findings PDF. Use the official Qwen/Qwen2.5-VL-3B-Instruct checkpoint,
resolve its revision, and record installed inference dependencies and device.

1. Freeze a two-packet diagnostic for each of the 20 reviewed source videos.
   Packet A contains four native frames ending at the reviewed prior anchor;
   packet B contains four frames starting at the reviewed positive anchor.
   Inspect all eight selected frames and qualify the actual packet endpoints.
2. Use the same eight pixels across joint, chronological A→B, and reversed B→A
   conditions. Both sequential orders use only the current packet and the exact
   previous model response as external memory. Run one deterministic trial per
   condition: five requests per video, 100 requests total.
3. Keep two PDF-compatible state fields (`earlier`, `latest`) and add evidence
   packet IDs for each. Ask about the same earlier capture time at every step;
   define latest by capture time rather than arrival order. Gold labels and graph
   descriptions must never enter model prompts.
4. Distinguish final factual correctness, clean unknown-to-correct correction,
   evidence association, unsupported initial commitment and conditional
   preservation of an already-correct state. Unknown prior-state labels are not
   silently converted into negatives. Unresolved original task definitions
   (HA05/HA09/HA10) are diagnostic-only, with no invented model accuracy.
5. Save exact prompts, raw responses, model/processor manifests, input hashes,
   timings and failures. Resume only identical configurations. JSON failures are
   model outcomes; infrastructure failures are archived and not counted as
   semantic errors. Do not select a different sample because a model succeeds.
6. Produce a report for every video answering the PDF's three questions, plus an
   aggregate table with explicit denominators. A failure in both sequential
   orders cannot establish a delayed-order-specific mechanism. Report a single
   trial as a case observation, not a reliability estimate.

This is an event-centered sampled-video diagnostic, comparable to the PDF's
two-clip design. It is not the other PDF experiment's whole-video uniform
eight-frame sampling, a full continuous-stream evaluation, a replay-discovery
test, or an independent human annotation pass. Event records remain fixed while
model belief outputs are measured at each arrival step.
