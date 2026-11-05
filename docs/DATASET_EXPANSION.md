# Dataset expansion and episode admission

Updated 5 November 2026. This is a collection protocol, not a claim that new
datasets or episodes have already qualified. It implements the question in
[RESEARCH_QUESTIONS.md](../RESEARCH_QUESTIONS.md). Completed work is recorded in
[CURRENT_STATE.md](../CURRENT_STATE.md).

## 1. Select evidence pairs that test the question

The desired episode has an identifiable past occurrence, an initial knowledge
state, later-arriving visual evidence that bears on that occurrence, and facts
that should remain protected. Keep event identity fixed while measuring changes
to the model's claims and supporting evidence.

For example, an initially obscured part-removal event may later be shown from
another view, revealing which part was removed. That observation can refine the
past record. A subsequently attached component is a different current-state
claim and should not become detached just because older footage arrives.

Do not assume that a later physical state reveals what was true earlier. A
closed lid now does not establish whether it was closed during the earlier event.
An alternate view or replay must actually show the same occurrence, or another
independently justified evidence link must be annotated.

The objective is to test the claim, not to collect only videos on which a chosen
model fails. Apply the same admission rules to successes, failures and controls.

## 2. Separate evaluation tracks

| Track | Construction | What it can test | Required label |
|---|---|---|---|
| A: delayed delivery | Known earlier footage is delivered after later footage | Capture/arrival order, state update and preservation under an explicit delivery intervention | Constructed transport schedule |
| B: natural later evidence | A natural replay/reinspection reveals information about the original event | Evidence-to-event attribution and retrospective claim revision | Natural evidence source and verified original-event link |
| C: delayed alternate view | A synchronized view of the old occurrence becomes available later by protocol | Cross-view attribution and revision under a controlled access schedule | Natural multiview recording, constructed evidence availability |
| D: controlled reveal | Occlusion, masking or designed recordings create specific information conditions | Diagnostic controls and missing counterfactual cells | Explicit construction method and its artifacts |

Report these separately. Masked images, delayed old packets and natural broadcast
replays are different evidence constructions. Existing HoloAssist results mostly
support track A diagnostics; they do not automatically qualify tracks B/C.

## 3. Admission gates

Use [the candidate template](../datasets/candidate.template.json) and retain
source/packet identities. Every core episode needs the following recorded checks:

1. **Defined claim:** predicate, objects, reference frame and occurrence are clear.
   "Any similar action" and "this specific earlier occurrence" are different tasks.
2. **Stable event identity:** event interval, candidate confusable events and the
   same-event/new-event/unrelated/unresolvable relation are independently checkable.
3. **Prefix-only knowledge:** label what can be known before the reveal using only
   the causal prefix. Freeze that judgment before viewing the later evidence.
4. **Verified evidence effect:** label whether the new evidence confirms,
   contradicts, refines or leaves the target unresolved, and why. Distinguish first
   evidence about a historical state from correction of a previously false claim.
5. **Protected facts:** specify unrelated historical and recent claims that should
   remain unchanged. Preservation of a model value is conditioned on its prior
   correctness, not merely on a gold claim being known to the evaluator.
6. **Clock alignment:** record event/capture time, evidence availability/arrival
   time, query/response time and, if measured, decision/outcome time. Camera
   synchronization and source PTS must be explicit for alternate views.
7. **Exact model input:** record frame indices, actual timestamps, resolution,
   audio/overlay availability and hashes. Review the cues in the evaluated
   representation, not only a clearer full-resolution source clip.
8. **Independent annotation:** obtain independent judgments for predicate meaning,
   prefix ambiguity, event link, evidence effect and protected facts; adjudicate
   disagreements and retain the originals. One assistant's review is provisional.
9. **Nontrivial controls:** confirm that constant/no-video/schedule rules do not
   solve the intended contrast. Keep unresolvable and irrelevant-evidence cases.
10. **Provenance and splits:** record source version/access/redistribution terms,
    recording/participant grouping and near-duplicate relationships. Alternate
    views and adjacent clips of the same event stay in the same source split.

If a gate fails, retain the rejection/defer reason. An ambiguous predicate, a
task/window mismatch and intentionally inconclusive evidence are separate labels.
The [taxonomy gap register](../experiments/holoassist_20/belief_revision_v1/taxonomy/GAPS.md)
defines those boundaries.

## 4. Collection funnel and selection policy

Use: `candidate -> screened -> prefix_labeled -> link_verified -> adjudicated
-> pilot_admitted -> released`, with `deferred` and `rejected` branches.

Record counts and reasons at every stage. Dataset membership or a difficult
question is not an admission decision. Prefer a small qualifying set over a
large set of generic video QA that does not exercise the research question.

Annotators should be blind to model identity/results during qualification. Save
the inclusion criteria, primary comparisons and source splits before running
selection models. Model mining can suggest intervals; independent review admits
them. Preserve admitted cases where the model succeeds.

No new cross-dataset episodes were admitted during the repository cleanup. The
template and this protocol prepare that work; they are not additional data.

## 5. Candidate source families

Official source descriptions were checked on 5 November 2026. The capabilities
below are publisher descriptions; the proposed research uses are our screening
inferences. No family guarantees qualifying retrospective-revision episodes.

| Source family | Verified source property | Proposed use and unresolved qualification |
|---|---|---|
| [HoloAssist](https://holoassist.github.io/) | Egocentric collaborative manipulation, with action/conversation annotations | Reuse acquisition knowledge to screen mistakes, reinspection and repeated actions. A later state alone is insufficient evidence of an earlier hidden fact. |
| [Assembly101](https://assembly-101.github.io/) | Assembly/disassembly with simultaneous static and egocentric views | Candidate for track C: reveal an old action from a different view, with confusable repeated steps. Event link, prefix ambiguity and the informative claim still need independent annotation. |
| [Ego-Exo4D](https://ego-exo4d-data.org/) | Time-synchronized ego/exo views of skilled activities | Candidate for cross-view evidence under a constructed access schedule. Multiview availability is not itself a labelled belief-revision task. |
| [SoccerNet Replay Grounding](https://www.soccer-net.org/tasks/replay-grounding) | Replay-to-original-action timestamp annotations in broadcast games | Candidate for natural replay identity, then additional labels for what new fact the replay establishes. Timestamp matching alone does not test selective claim revision. |

Assembly101's [official download repository](https://github.com/assembly-101/assembly101-download-scripts)
also describes the multiview structure. Ego-Exo4D's
[official documentation](https://docs.ego-exo4d-data.org/) describes access and
data organization. Resolve current access and source versions before downloads;
the cleanup did not download or redistribute any new dataset.

The existing [replay candidate notes](../experiments/replay_candidates/README.md)
and [source suitability audit](../experiments/source_suitability/README.md) are
starting evidence, not admitted new benchmark episodes. Titles, rulings,
commentary and dataset action labels can suggest a candidate; the actual visual
fact and event correspondence require review.

## 6. Balance the discriminating contrasts

Start with targeted matched contrasts rather than an unchecked Cartesian product:

| Factor | Needed levels |
|---|---|
| Event linkage | Same occurrence; visually similar new occurrence; unrelated; unresolvable |
| Evidence effect | Confirms; contradicts; refines; does not resolve; no new information |
| Prior expressed belief | Unknown; correct; plausible wrong/unsupported claim |
| Protected knowledge | Other attribute of the same event; unrelated past event; current state |
| Endpoint state controls | Negative/negative; positive/positive; negative/positive; positive/negative where meaningful |
| Context | No distractor; confusable intervening event; concurrent current task |

Separate model-generated prior histories from controlled histories. A manually
inserted wrong prior is an intervention, not an observed model mistake. Always
compare identical evidence where the intended intervention is only prior memory.

The current no-video baseline reaches 31/34 final state fields because the
selected labels mostly follow no-then-yes. New questions must make that shortcut
non-discriminating before using high value accuracy as evidence of visual reasoning.

## 7. Evaluation and evidence-graph design

Keep these representations separate:

- **Evaluator graph:** adjudicated event/claim identities, evidence support,
  affected/protected claims and source timebases. Never leak its answers to the
  baseline model.
- **Agent memory:** the model's own claims, uncertainty, event links and support
  references, available causally. Preserve revisions as records, not destructive
  replacements of the event identity.
- **Post-hoc trace graph:** what the model actually emitted. A model-cites edge is
  an assertion until its reference and visual support have been checked.

A new dataset needs an adapter from its events/claims/packets to expected states
and availability at each step. The current A/B taxonomy builder is specific to
the archived HoloAssist protocol; changing a dataset path does not create a
validated general evaluator.

Compare current-window/previous-response memory, retained visual history, an
equivalent flat claim ledger and model-built graph memory with controlled
information and budgets. Use oracle already-seen facts only as separate diagnostic
conditions. Report evidence identity and actual support separately from values.

Use the taxonomy's exclusive primary claim/request outcomes, with citation,
consistency and transition facets as diagnostics. Gate preservation on a correct
prior; do not count duplicate aliases as independent problems. Group statistical
analysis by independent source episode and keep track/condition differences visible.

## 8. Expansion milestones

1. Screen sources for actual same-event evidence pairs and log admission yield.
2. Independently label and adjudicate a bounded pilot, including positive and
   negative controls; freeze exact evidence and an evaluator-only graph.
3. Run atomic perception/addressing controls and a balanced no-video baseline.
4. Measure ordinary history and oracle-prior diagnostics before a method claim.
5. Compare graph/flat-ledger memory only after the control tasks are informative.
6. Add more source families and matched stronger-model comparisons when label
   quality and reproducible effects support scaling.

Success is a validated test of the claim, including evidence that a model can
revise correctly. If available sources do not supply qualifying examples, revise
the candidate construction or narrow the claim and report the limitation.
