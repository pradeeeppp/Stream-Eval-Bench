# Gap register and causal hypotheses

This register accompanies the [operational taxonomy](README.md) and
[trace assignments](FINDINGS.md). It classifies study properties and plausible
explanations, not additional model mistakes. Version 1.0.0, 5 November 2026.

The reviewed evidence graphs and archived traces are the evidence base. No new
independent video labels, model runs, graph-memory interventions or CUDA results
were produced by this taxonomy analysis. The existing CUDA rerun instructions
are preparation, not a second measured result included here.

Evidence index: [frozen cases and qualification notes](../cases.json),
[prompt/scoring contract](../protocol.py), [archived runner](../run.py),
[execution manifest](../execution_manifest.json), [execution summary](../execution_summary.json),
and [reviewed factual graphs](../../online_pilot_v0/reviews/batch_v1/).
The [atomic ledger](annotations.json) links each classified observation to its raw request.

## Ownership boundaries

| Owner | Question owned | Boundary |
|---|---|---|
| Data/annotation D | Is the target well specified and the evidence label defensible? | Does not explain how the model computes its answer |
| Study design P | Which stimuli, interventions, controls and replications were measured? | Does not change what was actually visible in a given request |
| Interface I | What information and claim addresses reach each request? | An intentional baseline restriction is not automatically an implementation bug |
| Measurement E | What does the recorded score identify, and what is its counting unit? | A valid end-to-end score need not identify a causal mechanism |
| Model hypotheses H | Which unobserved capability or computation could produce an error? | Require discriminating interventions; never assigned as established root causes from outputs alone |

Every gap below has one primary owner and a distinct property/unit. A video can
be affected by several properties; that is coexistence of different conditions,
not permission to count them as multiple instances of the same model failure.
An unsettled endpoint, missing graph-memory condition and lossy baseline memory
are not all called "bad data" or "forgetting."

## Data and annotation

### D01. Target-definition validity

- **Property/unit:** whether a task predicate denotes the intended observable
  relation or occurrence, before assigning endpoint truth labels.
- **Evidence/status:** registered qualification blocker for HA05 and HA09.
  Their semantic model outputs remain ungraded.
- **HA05:** the original broad fastener-bin wording may admit an earlier washer-bin
  reach as well as a later screw-bin reach. Object/bin identity and occurrence
  selection are not interchangeable with a generic hand-in-bin condition.
- **HA09:** the face called the underside in the legacy positive is visible
  earlier; which face and whether a newly revealed face is required need resolution.
- **Boundary:** this is not S13 wrong binary prediction and not simply an unknown
  frame. The target specification itself blocks correctness judgments.
- **Action/exit criterion:** independently agree on object identity, reference
  frame, occurrence and visible threshold; freeze a revised task version and
  re-annotate. Do not silently replace the original target with an easier one.
- **Precedence:** if target meaning is unresolved, assign D01 first; do not also
  assert that the same observation is a proven wrong-positive label. Once meaning
  is fixed, a remaining task/window mismatch belongs to D04.

### D02. Endpoint evidence remains unsettled

- **Property/unit:** determinacy of the supplied evidence for one specified
  capture-time claim, after the relevant packet has arrived.
- **Evidence/status:** three registered uncertain A endpoints: HA06 battery near
  the compartment, HA08 orientation/mouth-over-opening near the visual criterion,
  HB06 board/slot interface occluded by the hand. These are provisional judgments.
- **Boundary:** uncertainty is a legitimate test condition, not inherently a
  dataset defect. Unknown is not a negative physical state. S11 tests unsupported
  binary commitment relative to these labels. If adjudication finds the predicate
  under-specified rather than the image inconclusive, escalate the specification
  issue to D01 instead of claiming two root causes for one ambiguity.
- **Action/exit criterion:** reviewers inspect the exact evaluated samples and
  endpoint, record whether the visible relation is settled, and keep reason codes
  such as occluded, criterion-boundary or unobserved. Add clearer evidence only
  as a separately versioned test, preserving uncertainty cases when intentional.

### D03. Label reliability is not independently established

- **Property/unit:** annotation process across the 20 recordings, distinct from
  the content of a particular uncertain label.
- **Evidence/status:** labels and review judgments come from a single assistant;
  the archived execution manifest records no independent annotation.
- **Boundary:** hash checks certify artifact identity, not visual truth. This gap
  does not prove any particular label is wrong; it limits how strongly S11/S12/S13
  can be described as physical-world mistakes.
- **Action/exit criterion:** independent reviewers blinded to model outputs,
  explicit instructions, agreement/disagreement records and adjudication. Report
  agreement and residual uncertainty rather than forcing unanimous yes/no labels.

### D04. Intended target and positive evidence window do not align

- **Property/unit:** compatibility of a specified task with the source segment
  presented as its positive evidence; not uncertainty about what an object name means.
- **Evidence/status:** the reviewed HA10 graph reports cart and baskets tilting
  together, while the original instruction requires the upper basket to tilt away
  from an upright frame. It proposes either targeting whole-cart tipping or
  separately annotating later basket/frame separation. The current task/window
  combination remains ungraded pending adjudication.
- **Boundary:** this is different from a blurry frame, unknown physical state or
  binary model error. Whole-cart rotation is evidence of a different relation.
  The finding is a single-reviewer source/task mismatch, not an independently
  adjudicated statement that the target never occurs anywhere in the video.
- **Action/exit criterion:** keep the intended predicate and locate matching
  evidence, or explicitly version a different task matched to the segment. Review
  the resulting positive and negative endpoints. Do not declare model failure for
  rejecting an unsupported legacy positive, and do not silently turn the wrong
  task/window pair into a normal positive example.

## Study design

### P01. Answer schedule can substitute for evidence

- **Property/unit:** endpoint-label distribution of the qualified sample.
- **Evidence/status:** all 17 qualified later endpoints are yes; 14 earlier
  endpoints are no and three are unknown. The analytical rule "unknown before A,
  no after A, no before B, yes after B" scores 31/34 final fields, 14/17 final
  pairs and all 14 unknown-to-no value transitions without inspecting images.
- **Boundary:** this demonstrates shortcut availability, not that Qwen actually
  uses the shortcut. It is separate from D01/D02: labels can be correct and still
  make a benchmark non-discriminating.
- **Action/exit criterion:** include unchanged-negative, unchanged-positive,
  negative-to-positive and positive-to-negative evidence for comparable predicates.
  Balance object/task/template cues and report no-video/constant/schedule baselines.
  Counterbalancing question wording alone does not create new independent events.

### P02. Limited evidence and temporal coverage

- **Property/unit:** sampling protocol per recording and supported scope of the study.
- **Evidence/status:** only four native frames in each of two event-centered
  packets reach the model; there are 160 selected frames total. These are short
  samples around chosen anchors, not full recordings or long streams.
- **Boundary:** missing an event between samples and failing to interpret an
  available frame are different possibilities. The current sampling does not
  prove either caused a particular error. Visual review of the source recording
  is not equivalent to showing that recording to the model.
- **Action/exit criterion:** controlled endpoint-preserving changes in density,
  spatial resolution, inter-packet gap, distractors and history length. Validate
  actual model-visible frames. Avoid giving one condition future evidence or a
  different target timestamp while calling the change a memory intervention.

### P03. Missing interventions for causal attribution

- **Property/unit:** the experimental control matrix, rather than the distribution
  of labels or the memory interface itself.
- **Evidence/status:** the run compares joint, chronological and reversed arrival
  under previous-response memory. It has no task-matched blank/shuffled-video,
  atomic single-claim, oracle-prior-memory, retained-visual-history or graph-memory
  condition. The solid-red smoke test is not such a control.
- **Boundary:** comparison patterns locate observable differences, not their
  mechanism. The two joint-success/both-sequential-fail cases cannot by themselves
  separate perception, prompt interpretation, summary error and state updating.
- **Action/exit criterion:** execute the controls below with fixed evidence and
  explicit information-availability rules. Oracle conditions are diagnostic upper
  bounds, not headline model results or fair substitutes for model-generated memory.

### P04. Event association is supplied, not discovered

- **Property/unit:** which event-identity and temporal-association capability is tested.
- **Evidence/status:** predicates, packet IDs and capture timestamps are explicitly
  supplied. No natural replay discovery or matching of an unlabelled new view to
  an earlier event is required.
- **Boundary:** E11 demonstrates a violated supplied-ID/time contract. It does not
  demonstrate failure of a natural event-reidentification algorithm. Conversely,
  correct A/B IDs would not establish that capability.
- **Action/exit criterion:** a separately designed association task with independent
  event/instance labels, distractor events, multiple occurrences and unlabelled
  evidence, after the simpler supplied-time contract is measured adequately.

### P05. Reliability and population scope are limited

- **Property/unit:** replication and coverage of models, prompts, examples and backends.
- **Evidence/status:** one greedy trial per condition, one pinned 3B checkpoint and
  one archived MPS configuration across a small selected HoloAssist sample.
- **Boundary:** 100 requests are not 100 independent replications. Repeating an
  identical deterministic call is a reproducibility check, not a substitute for
  new independent examples or a broad reliability estimate. A CUDA runner in the
  repository is not evidence that this batch has been replicated there.
- **Unmeasured exposure:** the videos' presence or absence in model pretraining
  was not audited. No claim of unseen-data generalization follows from source
  provenance or a pinned checkpoint; this is an unresolved scope question, not
  evidence of contamination.
- **Action/exit criterion:** additional independently selected examples, matched
  prompt variants, repeated executions where numerical reproducibility is the
  question, controlled decoding variation where appropriate, and separately
  reported models/backends. Do not pool incompatible protocols as one accuracy.

## Interface and representation

### I01. The previous response is a restricted information channel

- **Property/unit:** the input to each of the 40 sequential second requests
  (34 provisionally scored, six diagnostic-only).
- **Evidence/status:** only the current packet's images plus the exact previous
  four-key response are supplied. Earlier images and a full history are absent.
- **Boundary:** this is verified configuration and an intentional baseline, not a
  demonstrated coding error. The lost information may originate in perception,
  summary generation or the imposed memory channel. It does not prove a neural
  context-capacity failure. An initially incorrect summary can make a later
  wrong answer unsurprising without any loss of a previously correct fact.
- **Action/exit criterion:** compare predicted summary, oracle summary of already
  received evidence, retained images and a typed ledger under controlled inputs.
  Never let an oracle reveal a target packet that has not arrived.

### I02. Field names are not persistent capture-time addresses

- **Property/unit:** identity and provenance carried in external memory.
- **Evidence/status:** latest means A's endpoint on the first chronological step
  and B's endpoint on the second. The previous output carries values and packet
  IDs, but no explicit per-field capture-time address or observation record.
  The two first-step fields also alias the same claim.
- **Boundary:** moving latest is well defined by the prompt, not intrinsically an
  incorrect task. The constraint is that stored field names are not immutable
  claim IDs. K11 and E11 are compatible with addressing difficulty but do not
  prove it. This differs from I01, which concerns discarded visual information.
- **Action/exit criterion:** use immutable `(predicate, object, capture_time)` keys
  and compare them with the existing slot format on identical evidence and facts.
  A graph variant needs an equivalent flat-ledger control; otherwise richer
  information, longer text and graph structure are confounded.

### I03. Unknown reasons are collapsed in the output

- **Property/unit:** representation of evidence availability versus evidence ambiguity.
- **Evidence/status:** unseen historical evidence and received-but-inconclusive
  evidence both become the string unknown; the schema has no uncertainty reason
  or calibrated probability. The taxonomy can separate the reasons using metadata,
  but the model's expressed reason cannot be recovered from that string.
- **Boundary:** do not call every unknown a perception error, every binary answer
  high confidence, or every appropriate abstention a calibrated belief. A yes/no
  value is an assertion, not a measured confidence estimate.
- **Action/exit criterion:** separately measure unseen/inconclusive/contradictory
  evidence, with reason fields if needed. Test whether elicited reasons correspond
  to the evidence; adding explanation text alone does not validate uncertainty.

## Measurement and interpretation

### E01. Output proxies do not identify internal evidence use

- **Property/unit:** construct validity of value/citation metrics.
- **Evidence/status:** 43 of the 85 correct known-value observations have a missing
  or wrong-time citation. Sixteen opposite-binary answers nevertheless name the
  requested packet. The no-pixel rule can produce every expected clean value
  transition. The existing scorer checks packet IDs, not a verified visual
  entailment edge or the model's internal retrieval.
- **Boundary:** the archived output metrics are useful and reproducible. The gap
  is inferring a stronger construct than they measure, not evidence that the
  scorer is numerically broken. E00 is not a verified-support claim. The original
  reviewed graph is offline provenance; generated model-cites edges are assertions.
- **Knowledge available to the request:** the expected state uses the qualified
  evidence history, while a second request may receive only an incorrect or
  incomplete prior summary instead of that history. Its final unknown can be an
  end-to-end state error without being irrational given its actual current input.
  S12 does not establish unjustified uncertainty or a faulty update in isolation.
  Oracle-prior and initially-correct-prior controls are needed to separate those claims.
- **Action/exit criterion:** report state, citation, uncertainty and conditional
  preservation separately; add counterfactual evidence controls and independently
  checked support. Do not say the model rewrote an event, forgot internally, used
  the graph or grounded its answer solely from these output scores.

### E02. Repeated and aliased fields are dependent observations

- **Property/unit:** denominator and unit-of-analysis interpretation.
- **Evidence/status:** 170 scored fields repeat 34 capture-time claims. The first
  chronological fields ask the same claim twice. Preservation has smaller
  conditional opportunities: one initially correct known historical value versus
  14 initially correct recent values. The three wrong recent priors are not
  additional preservation failures.
- **Boundary:** keeping per-field scores is legitimate when labelled as such.
  Treating them as independent events, summing axes, or using all cases as a
  preservation denominator is not. This is distinct from P05's shortage of new
  trials/examples.
- **Implemented mitigation:** the taxonomy's primary partition collapses aliases
  within a request, giving 153 claim/request checks instead of 170 fields. A
  disagreement gets one consistency outcome, not two primary value errors. This
  avoids same-request double counting but does not make repeated conditions on
  the same 34 endpoints independent.
- **Action/exit criterion:** retain claim IDs, gate transition opportunities,
  report raw counts and denominators, and use video/claim-level dependence-aware
  analysis if future uncertainty intervals are estimated. In the present report,
  rates are descriptive counts, not population reliability estimates.

## Operational checks: no demonstrated runtime failure

All 100 archived responses are valid exact schema JSON; no output-cap hits or
infrastructure failures were reported. The source/protocol/input-selection audit
passes. These facts exclude observed R10/R11/R12/R20/R21 explanations for this run;
they do not prove numerical equivalence across devices or perfect visual labels.
A future hash, decode, source-time or packet-selection mismatch must be handled
as an integrity gate and repaired before semantic model attribution.

## Model hypotheses: candidates, not assignments

| ID | Candidate mechanism | What motivates it | Discriminating test and boundary |
|---|---|---|---|
| H01 | Temporal question/slot interpretation difficulty | Fourteen first-step certainty disagreements occur without a previous request | Same pixels and labels, atomic single-time question versus duplicate/moving slots and immutable keys. Improvement locates interface sensitivity, not automatically a general temporal reasoning defect. |
| H02 | Visual relation or criterion extraction difficulty | Joint input has 13/17 non-perfect final pairs | Human-adjudicated exact model-visible endpoint images, single-claim prompts and matched higher-resolution controls. Joint failure alone mixes perception with instruction and label problems. |
| H03 | Arrival order dominates explicit capture-time citation | Fourteen final recent values replace B citation with A | Counterbalance opaque packet names, arrival order and capture-time order; isolate citation generation with states held fixed. A citation-only effect is not proof of changed internal event binding. |
| H04 | Prior summary error or restricted history causes later errors | Most chronological earlier summaries are already wrong; only one known earlier value starts correct | Predicted versus oracle prior memory, then retained visual history, with no future/oracle leakage. Oracle improvement shows a dependency on supplied information, not an intrinsic model-memory limit. |
| H05 | Answer/transition priors substitute for visual evidence | A no-pixel schedule baseline outperforms the observed reversed final pair rate | Balanced labels plus matched blank, unchanged and shuffled visuals. No change on an already failing/floor task is insufficient evidence that images are ignored. |
| H06 | Spatial/temporal sampling makes critical cues insufficient | Only four frames per packet and a fixed pixel budget reach the model | Inspect exact preprocessed inputs and vary one of resolution/density/context at a time, preserving capture targets and rechecking labels. Missing cues are plausible, not demonstrated by current traces. |
| H07 | Model-size or numerical/backend sensitivity | Only one checkpoint/configuration is measured | Matched checkpoint/device/precision comparisons after task and input controls. There is currently no evidence that MPS, FP16 or 3B parameter count caused a particular failure. |

These hypotheses describe different unobserved mechanisms but can coexist.
They are deliberately not a mutually exclusive root-cause classifier: the data
do not identify such a classifier. Operational S/E/K/T assignments remain the
non-overlapping, reproducible part of the taxonomy.

## Prioritized experiment backlog

| Priority / ID | Work item | Controlled contrast | Output needed before promotion to a causal finding |
|---|---|---|---|
| P0 / X00 | Independent target and endpoint adjudication | Same predicate/endpoint/evaluated pixels, blinded reviewers | Versioned eligibility, labels and uncertainty reasons; no post-hoc label edits driven by model success |
| P0 / X01 | Balanced evidence suite and baselines | Four endpoint-transition types, comparable tasks and independent events | Label-cell counts plus constant/schedule/no-video baselines on held-out examples |
| P1 / X02 | Atomic claim versus temporal slots | Same four-frame packet and target, changed claim-address format only | State and K differences; no old images or oracle answers added as a second simultaneous change |
| P1 / X03 | Citation targeting and arrival/name controls | Fixed capture-time facts; counterbalanced names and arrival order | E partition with identical or independently measured state correctness; distinguish token/ID emission from support selection |
| P1 / X04 | Memory-channel decomposition | Predicted summary, oracle already-seen summary, retained images, immutable ledger | Conditional updates with initially correct versus incorrect priors separated; information budgets and oracle conditions explicit |
| P1 / X05 | Actual visual dependence | Correct, blank, shuffled or irrelevant visuals on balanced tasks | Case-paired changes with adequate non-floor baseline performance; never equate value accuracy with visual use |
| P2 / X06 | Graph-memory intervention | Model-produced graph versus equivalent flat ledger, same facts and comparable budgets | Measured benefit attributable to representation/retrieval, not oracle labels, extra evidence or extra tokens |
| P2 / X07 | Sampling and robustness | One factor at a time: resolution, density, time gap, distractors, model/backend | Separate versioned runs and stable source/claim identities; no pooling incompatible protocols |

X00 and X01 are the first blockers for strong capability claims. X02-X05 can
diagnose the current errors with a small, transparent case panel before expanding
the suite. Useful cases include HB01 (known-state sequential failure), HA01
(value/citation split), HA08 (unsettled prior), HB08 (wrong recent prior) and HB07
(correct final values but wrong provenance). This is a proposed panel, not an
executed experiment or an unbiased new test set.

For X06, the model must build memory from evidence that has actually arrived.
The reference gold graph stays evaluator-only. A graph filled with correct labels
by the evaluator is an oracle upper bound and cannot demonstrate learned graph
construction or fair end-to-end improvement.

## How a hypothesis becomes an established explanation

1. Specify the affected taxonomy outcomes and a falsifiable prediction in advance.
2. Validate task labels and actual inputs; keep alternative explanations explicit.
3. Change the intended factor while matching other information, prompts and budgets
   as far as possible; disclose unavoidable differences.
4. Include counterexamples and negative controls, rather than selecting only cases
   where the preferred mechanism seems plausible.
5. Repeat across independent cases and report case-level changes and exclusions.
6. Promote only the supported statement. For example, "immutable keys reduce K11"
   is narrower than "the model understands time"; "oracle history repairs this
   case" is narrower than "the model forgot".

New evidence may merge, split or reject hypotheses. Preserve the old annotations
and version the taxonomy instead of retroactively turning an untested explanation
into the meaning of an observed error code.
