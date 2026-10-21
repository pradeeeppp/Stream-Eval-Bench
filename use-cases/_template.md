# Template — copy for a new use-case

> How to use: copy this file to `NN-short-name.md` and fill each section. Keep it runnable-minded: someone should be able to turn it into a `stream_eval/usecases/*.py` + packets + `protocol.json`.

## 1. Title + one-liner

## 2. User need
Who wants what, and why lateness is unavoidable (replay, 2nd camera, occlusion, network)?

## 3. Stream script
* **E1 (ambiguous, t1):** what is seen, what stays `unknown` (do NOT guess)?
* **E2 (intervening, t2):** what happens next, must be preserved?
* **E3 (delayed, t3, capture_time < watermark):** what new detail about E1, and how do we know it is E1 (timestamp / overlap / same transfer / label linkage)?

## 4. Expected response (quote format)
> “...” Update field X for E1, keep E1 id/time/count, keep E2 intact, state live now.

Explicitly forbid: duplicate event, merge E1+E2, bind to wrong E, overwrite live with replay, infer beyond evidence (intent, fault, competence, contents not visible).

## 5. Benchmark test
* Ask before E3: E1=?, count=?, live=?
* Ask after E3: E1=?, count=?, live=?
* Conditions: **Joint** (E1+E2+E3 together), **Chrono** (E1→E2), **Delayed** (E2→E1-late). Compute `Streaming Order Gap = Acc_joint - Acc_delayed`.
* Controls: irrelevant evidence, replay-of-other-event, genuinely-new-similar-action, label-visible-but-unlinked (must stay `unknown`).

## 6. RQ mapping
* RQ1: competitors + same/new discrimination
* RQ2: no-prior vs real-prior vs `unknown`-prior on identical final frames
* RQ3: justified-correction / collateral / duplicate / live-preservation

## 7. Failure modes to score
- [ ] early guess, [ ] miss detail, [ ] extra count, [ ] wrong-E bind, [ ] wipe E2, [ ] replay-as-live

## 8. Candidate footage / collection route
Dataset + gallery/visualizer link, access/redistribution terms, what pair to verify. If none verified, say how to record synchronized views with readable identifiers.

## 9. To implement (4-Gate ready)
* [ ] timestamps + SHA + packet split (A=0-50%, B=50-100% or E1/E2/E3 packets)
* [ ] schema e.g. `{earlier, latest}` + `expected_final`
* [ ] G1 perception (E3 alone), G2 joint, G3 chrono pass before claiming CRR fail
* [ ] status: illustrative → validated (independent annotation, initial-uncertainty verified)

## 10. Status
`illustrative` | `candidate clips found` | `validated` | `implemented (link python usecase)`
