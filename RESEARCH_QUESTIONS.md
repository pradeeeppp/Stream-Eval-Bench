# Active research questions

Updated 5 November 2026. This is the current question set, consolidated around
the project's central statement. Prior formulations are preserved in
[docs/history](docs/history/README.md). Results and completion status belong in
[CURRENT_STATE.md](CURRENT_STATE.md).

## Central question

Stream-Eval-Bench asks whether a video model can use late-arriving evidence to
correct what it knows about the past, apply that evidence to the correct
historical event, and preserve unrelated facts and already established recent
states.

An event does not change after it happens. What may change is the model's
knowledge of that event. This is the distinction between revising knowledge and
rewriting event history.

The unit is an identifiable event occurrence and its claims. A later physical
state, a newly repeated action, and new evidence about an old occurrence are
different situations. They need separate labels and controls.

## RQ1. Historical knowledge revision

When new visual evidence concerns a fixed past event, does the model update its
previously expressed claims in the way that evidence justifies?

- Distinguish unknown-to-known completion, wrong-to-correct revision,
  confirmation, refinement and evidence that remains inconclusive.
- Record the claim before and after evidence, capture time, arrival time,
  supporting observations and the reason an update is permitted.
- A correct final answer, an unchanged correct guess or a value change caused by
  a fixed answer schedule is insufficient evidence of visually grounded revision.
- Use perception controls, joint/full-history references, no-new-information
  controls and comparisons with initially correct versus incorrect memory.

## RQ2. Evidence-to-event attribution

Can the model identify which historical occurrence the new evidence concerns,
including distinguishing the same event, a similar new occurrence, unrelated
evidence and evidence insufficient for a reliable match?

- Separate recognizing a visible fact from attaching it to an event.
- Include confusable candidate events and repeated actions.
- Report attribution and revision separately. A supplied A/B packet citation is
  a simpler temporal-reference test, not proof of natural event reidentification.
- Preserve event IDs and occurrence counts when evidence is replayed; create a
  new occurrence only when the scene actually contains one.

## RQ3. Selective preservation and current-state continuity

While revising an affected past claim, does the model preserve unsupported
uncertainty, unrelated verified facts and already established recent states?

- Predeclare affected claims and protected claims rather than choosing them
  after seeing a response.
- Measure collateral changes, false updates, unsupported certainty, duplicate
  or merged events and loss of correct current facts.
- A preservation trial requires a correct prior value. A wrong answer remaining
  wrong is a persistent error, not loss of established knowledge.
- Evaluate live continuity when there is an actual concurrent task; model
  generation time alone is not a measurement of missed live events.

## Method question: representation, retrieval and budget

Once qualifying episodes and reproducible effects exist, compare prior-answer
memory, retained visual history, retrieval, immutable claim ledgers and model-built
evidence graphs with comparable information and inference budgets.

The evaluator's gold graph stays private. An oracle graph or oracle prior is a
diagnostic upper bound, not an end-to-end model result. A graph benefit must be
separated from benefits due to extra information, correct answers or more tokens.

## Optional extension: downstream decisions

An event revision may change a pending alert, recommendation or task status.
This is a useful extension, but is not required to admit a sample for the three
core questions above. If evaluated, predeclare claim-to-decision dependencies
and score retain/change/retract decisions. Do not infer physical outcome benefits
from offline video answers.

## Current evidence boundary

The archived 20-video run is a sampled two-packet diagnostic with supplied
timestamps, not a full test of natural event association or long-stream revision.
Its reviewed evidence graphs were used for preparation and evaluation provenance;
the model did not receive graph memory. The [taxonomy](experiments/holoassist_20/belief_revision_v1/taxonomy/README.md)
improves measurement but does not establish a causal mechanism or novelty.

Dataset expansion should follow [the admission protocol](docs/DATASET_EXPANSION.md)
and retain successes, counterexamples and model failures under the same rules.
