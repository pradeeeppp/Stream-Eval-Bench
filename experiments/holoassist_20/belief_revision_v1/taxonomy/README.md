# Failure taxonomy v1: streaming belief revision

This is an operational taxonomy for the archived 20-video Qwen2.5-VL-3B experiment,
with an initial assignment ledger for every saved response. It distinguishes
observable output errors from dataset limitations, interface constraints and
unproved explanations of model behavior. Version 1.0.0, 5 November 2026.

Start with [applied findings](FINDINGS.md), then the [gap and hypothesis register](GAPS.md).
The [catalog](catalog.json) and [atomic annotations](annotations.json) are machine-readable.
The archived model outputs, labels, prompts, scorer and failure-analysis PDF are unchanged.

## 1. What non-overlapping means

A video is too coarse to have one informative failure label. For example, HA01
corrects its earlier value, omits its historical citation and cites older footage
for its latest value. These are distinct observations, not three competing names
for one internal cause.

The taxonomy therefore has **exclusive partitions with explicitly different units**:

| Partition | Assignment unit | Exactly one category when eligible | What it does not claim |
|---|---|---|---|
| Primary claim outcome | One capture-time claim in one request | A state code, or consistency code when aliased fields disagree | Does not count two aliases as two independent problems |
| Response format R | One request | Exact JSON, schema/format failure, missing result or infrastructure failure | An invalid response is not also counted as several semantic mistakes |
| State judgment S | One requested field at one step | Correct, early commitment, unsettled commitment, abstention or wrong binary value | No diagnosis of perception, forgetting or model capacity |
| Evidence attribution E | One field's citation list | Requested packet, permitted empty, missing, wrong-time or unreceived citation | Naming a packet does not verify that it supports the answer |
| Same-claim consistency K | One request asking both fields about the same claim | Equal answers, binary contradiction or certainty disagreement | Agreement does not establish correctness |
| State transition T | One fixed capture-time claim across two sequential requests | Maintained, corrected, degraded or prior error not repaired | Wrong-before/wrong-after is not forgetting |
| Final condition profile JCD | One video | One of eight three-bit final-state patterns, or an exclusion | A condition pattern is not an internal failure mechanism |

Within a partition, the rule assigns one and only one code. Across partitions,
the same response can legitimately appear more than once. **Never sum counts
from different partitions to create a total failure count.** Root-cause
hypotheses and study gaps are a separate register and are never added to model
error counts.

The observed 170 qualified field observations repeat only 34 capture-time claims.
They are neither 170 unique events nor 170 independent statistical trials.
Every record includes its case, phase, field, claim ID, source pointer and
eligibility status so that aggregate counts can be audited.

For the strictest non-overlapping summary, collapse aliases within each request.
This yields **153 qualified claim/request checks: 105 correct and 48 problematic**.
The 48 are 21 known-state abstentions, eight opposite binary values, five
commitments on unsettled evidence and 14 same-claim certainty disagreements.
For an alias disagreement, the consistency code takes precedence over its
individual S codes. For equal aliases, the shared S code is counted once.
This is a summary precedence rule, not a statement that inconsistency is the
internal cause of the other field errors. The 170-field view remains available
to reconcile exactly with the archived scorer; do not add its 60 errors to the
48 primary problems. Both views still repeat the same 34 endpoints across conditions.

## 2. Assignment order and validity gates

1. **Validate the run.** Check frozen runner/protocol/case hashes, source and
   reviewed-graph identities, raw-record scores, exact prompts, packet selections
   and previous-memory strings. A mismatch invalidates the analysis rather than
   becoming evidence of a model failure. Actual image/source-byte verification
   is available separately through the archived audit's media options.
2. **Check task qualification.** HA05/HA09 have unresolved target identity or
   occurrence (D01); HA10 has a reviewed task/window mismatch (D04). Their request
   format remains observable, but state, citation and transition correctness are
   ungraded. No yes/no labels are invented. These are curated review findings,
   not diagnoses derived from the model's mistakes.
3. **Classify response format.** Unrecoverable or schema-invalid outputs block
   dependent semantic checks. Recoverable JSON surrounded by extra text gets
   its own format code; its valid semantics remain inspectable, consistent with
   the archived parser.
4. **Identify the immutable claim.** A means the condition at A's endpoint; B
   means the condition at B's endpoint. The first chronological request asks
   both fields about A. Later chronological latest refers to B. Reversed latest
   stays B after A arrives. Arrival order never changes claim identity.
5. **Assign S and E independently.** Compare each value with the frozen
   provisional expected state; check citations against received packet IDs and
   the requested capture time. The label is evidence-based expected output,
   not proof of the world's inaccessible physical truth.
6. **Assign relational checks only where eligible.** K needs the same claim in
   both fields. T needs a fixed claim across steps. The chronological latest
   field changes from A to B and is therefore not a retention transition.
7. **Collapse same-request claim aliases for the primary summary.** If their values
   disagree, assign only K10/K11 to that claim check. Otherwise assign the shared
   S code once. Keep the individual fields as diagnostic facets, not extra primary
   errors. Do not collapse different requests into one observation.
8. **Assign one final JCD profile.** Keep all atomic mistakes in the ledger;
   do not choose a single causal label for the whole video.

Semantic codes are provisional wherever their underlying labels are provisional.
This work re-analyzes saved traces; it is not a fresh visual annotation pass or
an independent adjudication of the videos.

## 3. Response-format partition R

| Code | Inclusion rule | Exclusion and precedence |
|---|---|---|
| R00 | Entire response is one valid four-key JSON object | Correct format can still contain wrong values or citations |
| R10 | No recoverable JSON object | Valid JSON of the wrong type is R11; recoverable valid schema object with surrounding text is R12 |
| R11 | JSON exists but violates the schema: type, keys, value vocabulary, citation IDs or duplicate IDs | Do not create extra state/citation failures from missing or malformed fields |
| R12 | Valid schema object extracted from a response containing extra material | A format-contract error with recoverable semantics, not an execution failure |
| R20 | Saved result missing | Not a semantic model error; record missingness and stop downstream grading |
| R21 | Step reports execution failure | Not a semantic model error; retain error provenance separately |

Observed: **100/100 R00**. No format or execution explanation is demonstrated by
these requests. The separate red-video smoke test verifies that inference runs;
it is not a balanced perception control for benchmark tasks.

## 4. State-judgment partition S

Required inputs are the prediction, provisional expected state and whether the
packet for this capture-time claim has been received. A known expected label
with an unreceived target packet is a protocol inconsistency, not a valid input
to the classifier.

| Code | Name | Inclusion | Do not confuse with |
|---|---|---|---|
| S00 | Correct known value | Expected yes/no; prediction matches | Verified visual grounding or correct evidence association |
| S01 | Correct abstention before evidence | Target packet unseen; expected/predicted unknown | Uncertainty caused by ambiguous received footage |
| S02 | Correct abstention on unsettled evidence | Target packet received; expected/predicted unknown | A failure to perceive a provisionally known state |
| S10 | Commitment before target evidence | Target packet unseen; prediction yes/no | S11, which requires receipt of the relevant packet |
| S11 | Commitment on unsettled evidence | Target packet received; expected unknown; prediction yes/no | Wrong binary classification against a known opposite label |
| S12 | Abstention on a provisionally known state | Expected yes/no; prediction unknown | S02; do not diagnose insufficient perception or irrational uncertainty without adjudication/controls |
| S13 | Opposite binary value | Expected yes/no; prediction is the other binary value | Unknown outputs, unavailable targets or unsettled labels |

For a valid, qualified field, decide in this order:

- If expected is unknown, split by whether the target packet has arrived; then
  split by abstention versus binary commitment.
- If expected is known, distinguish matching value, unknown and opposite value.

This partitions all legal value/availability combinations. In the archived run:
85 S00 + 17 S01 + 8 S02 + 0 S10 + 7 S11 + 34 S12 + 19 S13 = 170.
The **60 errors** are exclusively S11/S12/S13 here. They are not 60 independent
videos or 60 demonstrated internal failures.

An important epistemic distinction: S11 says a binary claim is unsupported under
the received-evidence label. It does not say that the actual physical state must
be the opposite binary value. Unknown is not silently converted to no.

S12 is likewise an end-to-end mismatch with the frozen evidence-history label.
When the prior images are absent and the supplied memory is already wrong or
incomplete, abstention need not be irrational given the actual current request.
The annotation records both target receipt and current visual availability;
only controlled prior-memory comparisons can isolate the update component.

## 5. Citation-attribution partition E

This partition tests the explicit A/B reference contract. It is independent of
state correctness. Apply it only to qualified, schema-valid field observations.

| Code | Inclusion | Precedence/boundary |
|---|---|---|
| E00 | Exactly the received packet for the requested capture-time claim | Can accompany S13: correct packet identity, wrong answer |
| E01 | Empty evidence list and no known-value support requirement | Permitted for an unseen target or unsettled label; does not excuse an S10/S11 binary commitment |
| E10 | Empty evidence list for a known expected state whose packet was received | Can accompany a correct value, abstention or wrong binary value |
| E11 | All referenced packets received, but list is not exactly the requested packet | Includes older A cited for latest B and lists containing both A and B |
| E12 | Any referenced packet has not arrived | Takes precedence over E11, preventing two codes for one list |

Malformed lists belong to R11 and are not relabeled as E10/E11. A known-state
reference is considered required even if the model abstains: this is the
archived strict value-plus-reference contract, not a claim that the model
subjectively had supporting evidence for its incorrect output.

Observed: 60 E00, 30 E01, 66 E10, 14 E11, 0 E12 = 170. Among correct known values,
29 omit the required citation and 14 cite the wrong capture time. Conversely,
16 opposite-binary answers still name the requested packet. Packet-ID matching
alone is therefore not evidence verification.

## 6. Same-claim consistency partition K

Eligibility is determined by claim identity, not matching field names. In this
protocol, both first chronological fields ask the same predicate at A's endpoint.

| Code | Rule | Example |
|---|---|---|
| K00 | Values equal | no/no or unknown/unknown; either can still be wrong |
| K10 | Opposing binary values | yes/no for the exact same capture-time claim |
| K11 | One unknown and one binary value | unknown/no or unknown/yes: certainty disagreement |

Observed: **3 K00, 0 K10, 14 K11** across the 17 qualified checks. Calling all
14 cases yes/no contradictions would overstate what the traces show. This
failure precedes cross-request updating, so a pure forgetting account cannot
explain the entire batch.

## 7. Fixed-claim transition partition T

Eligible roles are historical arrival (reversed earlier), historical retention
(chronological earlier), and recent retention (reversed latest). These are
51 qualified transitions. Each records its exact before/after expectation,
prediction, capture-time claim and source request.

| Code | Inclusion rule | Interpretation boundary |
|---|---|---|
| T00 | Expected unknown becomes known; prior correctly unknown; final value matches | Observable correction only; not proof the new image caused it |
| T01 | Expected unchanged; both predictions correct | Retains a correct value or appropriate uncertainty, not necessarily its supporting citation |
| T02 | Expected unchanged; incorrect prior becomes correct | Recovery, not preservation or clean evidence-driven correction |
| T10 | Expected unknown becomes known; correctly unknown prior stays unknown | Missed resolution; does not identify why evidence was missed |
| T11 | Expected unknown becomes known; correctly unknown prior resolves to the wrong binary value | Wrong resolution, distinct from continued abstention |
| T12 | Expected unknown unchanged; correctly unknown prior becomes binary | Loss of appropriate uncertainty, not a successful unknown-to-known update |
| T13 | Expected binary unchanged; correct prior becomes unknown | Withdrawal of an established value; internal forgetting remains unproved |
| T14 | Expected binary unchanged; correct prior flips to the opposite value | Value inversion, distinct from uncertainty |
| T15 | Expected unchanged; prior and final outputs both incorrect | Persistent prior error or failed repair; never count as loss of a correct fact |
| T16 | Expectation changes but the prior was already incorrect | Not a clean update opportunity; final correctness remains recorded separately |

If the expectation changes, first check whether the prior was correct. Otherwise
split by final match/unknown/wrong binary. If the expectation stays fixed, first
check prior correctness, then distinguish maintenance, recovery, persistent
error, uncertainty loss, withdrawal and inversion. This ordering makes the
outcomes exhaustive and exclusive for this protocol's legal trajectories.

The 14 recent values that stay correct all lose their previously correct B
citations in favor of A. **Value retention is 14/14; expressed support retention
is 0/14.** The latter is a cross-facet view of the same E11 observations, not
14 additional independent failures.

## 8. Exclusive final condition profiles

JCD bits mean both state values correct at the final joint, chronological and
reversed requests, in that order. There is one profile per eligible video.

| Profile | Observation | Causal limit |
|---|---|---|
| 000 | All three finals fail | Cannot isolate a sequential deficit from a weak joint baseline |
| 001 | Only reversed final succeeds | Does not prove reverse order helps generally |
| 010 | Only chronological final succeeds | Joint failure prevents an isolated delayed-order diagnosis |
| 011 | Both sequential finals succeed; joint fails | Can reflect question presentation, information compression or answer priors; not identified here |
| 100 | Joint succeeds; both sequential finals fail | Segmented-input difficulty in this example; not an identified memory mechanism |
| 101 | Joint and reversed succeed; chronological fails | Candidate chronological-order sensitivity; no such case here |
| 110 | Joint and chronological succeed; reversed fails | Candidate reversed-order sensitivity; HA08 involves an unresolved prior, not recovery of a known past fact |
| 111 | All final state values correct | Citations and intermediate states can still fail; HB07 is the example |

Ungraded target and blocked response are explicit exclusion profiles. See the
case ledger for every assignment. No profile is called "memory failure" or
"perception failure" without the additional controls in the gap register.

## 9. Evidence strength, ownership and hypotheses

Every explanatory statement must belong to one of these levels:

| Level | Meaning | Example |
|---|---|---|
| Observed output | Directly reproducible from saved values/citations | HA01 latest cites A after older A arrives |
| Verified configuration | What the implementation supplied or omitted | Prior images are absent from the second request |
| Provisional evidence label | A recorded assistant judgment, awaiting adjudication | HA08 earlier remains unknown |
| Analytical design result | A calculation on the label schedule | No-pixel rule gives 31/34 final fields |
| Unisolated hypothesis | Plausible explanation requiring intervention | Arrival-recency bias causes wrong citations |
| Not observed | Zero eligible occurrences in this run | S10 and K10 |
| Not tested | No experiment addresses it | Graph-memory benefit, replay discovery, causal forgetting |

The [gap register](GAPS.md) gives each issue one primary owner: data/annotation,
study design, interface or measurement. These ownership labels classify study
properties, not videos. Multiple distinct properties can coexist; no ownership
label establishes a model-internal cause.

## 10. Reproduce and extend

From the repository root, using Python 3 and no external packages:

```sh
python3 experiments/holoassist_20/belief_revision_v1/taxonomy/build_taxonomy.py
python3 -m unittest discover -s experiments/holoassist_20/belief_revision_v1/taxonomy -p 'test_*.py'
```

The builder checks archived provenance and recomputes the original scores before
writing only taxonomy files. It records input hashes and verifies them again
after generation. It performs no model calls and does not alter the archived
protocol. `--output-dir PATH` supports deterministic regeneration elsewhere.

Boundary tests cover all legal state combinations, uncertainty versus negative
labels, citation precedence, same-claim certainty versus binary disagreement,
transition outcome coverage, incorrect priors, moving latest targets, task
exclusions, schema errors, same-request alias deduplication and value preservation
with lost cited support.

When adding a category, specify its unit, eligibility, inclusion, exclusion,
precedence, evidence requirement, counterexample and falsifying test. Add a
counterexample test demonstrating separation from the nearest existing category.
Do not add a second name for a phenomenon that already fits a partition.
Use a new major taxonomy version if assignment meaning changes; retain the old
ledger. New datasets need their own claim-identity and evidence-availability
adapters; this builder deliberately targets the archived 20-video experiment.
