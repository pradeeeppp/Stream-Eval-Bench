# CVPR research direction: literature audit, sharper RQs, and dataset plan

**Prepared:** 2026-10-17  
**Purpose:** working research document; not a novelty guarantee or a claim that a benchmark is already validated.

## Executive assessment

The broad target—real-world, interactive, long-horizon streaming video agents—is already occupied by several recent works. In particular, StreamArena (Aug. 2026) directly claims continuous, interactive, long-horizon agentic streaming evaluation over hour-scale videos with perception, retrospection, proactive interaction, and tools. ProactiveBench (Sep. 2026) evaluates when to respond, silence, and duplicate counting. IPIBench evaluates persistent proactive tasks, task modification/cancellation, and interleaved requests. APM-Bench and StreamMemBench cover persistent memory and evidence use across sessions. DeltaStreamer (14 Oct. 2026) adds an agent that plans retrieval and targeted replay of historical frames.

Therefore, “a real-world benchmark for streaming agents,” a broader task taxonomy, more RQs, or an event-memory baseline is not a defensible novelty claim by itself. There may be a narrower contribution in **evidence-triggered revision of a previously formed event record and its dependent decisions**: later visual evidence can change the agent’s belief about a particular past event; the agent must revise only that event, preserve event identity and unaffected facts, and update or retract a downstream recommendation/alert while continuing the live task.

That gap is a **candidate**, not established novelty. DeltaStreamer’s newly posted preprint is especially close on historical evidence retrieval and replay. A decisive next step is to inspect released tasks and code for StreamArena, DeltaStreamer, IPIBench, and APM-Bench, and compare their annotation fields and scoring at example level. If they already evaluate retrospective state revision with downstream action consequences, the contribution should shift or stop rather than rely on wording.

## 1. Scope and terms

Use “streaming video agent” for a system that receives observations causally and can make decisions during the stream. Distinguish four clocks in every task:

1. **Event time:** when the real-world event occurred.
2. **Evidence-observation time:** when a supporting visual cue became available to the agent (or when archived footage was re-inspected).
3. **Decision time:** when the agent answered, alerted, requested evidence, or changed a plan.
4. **Outcome time:** when the downstream task consequence became observable, if the benchmark can measure one.

Also distinguish (a) the world changing, (b) the camera showing the same unchanged past event again, (c) an independent similar event, and (d) evidence about the past arriving late. Timestamp disorder alone does not represent all four.

## 2. Literature map and implications

| Work | What it establishes | Consequence for our framing |
|---|---|---|
| [OVO-Bench, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Niu_OVO-Bench_How_Far_is_Your_Video-LLMs_from_Real-World_Online_Video_CVPR_2025_paper.html) | Online timestamp-conditioned evaluation: backward tracing, real-time perception, forward active responding. | Do not claim online temporal QA, retrospective recall, or proactive answering as new. Inspect precisely whether labels capture belief revision versus answer-at-query. |
| [OVBench / VideoChat-Online, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Huang_Online_Video_Understanding_OVBench_and_VideoChat-Online_CVPR_2025_paper.pdf) | Spatial/temporal perception, past memory, hallucination verification, future prediction; temporally grounded questions and distractors. | Event recall, current-versus-past state, or temporal grounding alone overlap. A candidate distinction must require a changed event record after new evidence, not merely retrieval. |
| [SPOT-Bench, 2026](https://arxiv.org/abs/2604.24317) | Continuous proactive output, timeliness, response restraint, repeated event counting. | Alert timing, silence, and duplicate counts are established evaluation targets. Use them as controls or downstream consequences, not standalone novelty. |
| [StreamReady / ProReady-QA, 2026](https://arxiv.org/abs/2603.08620) | Evidence-window-aware answer readiness and proactive multi-turn questions over long streams. | “Answer at the right time when evidence appears” is already directly studied. Our claim must concern revision of an earlier event belief/decision, beyond first answer readiness. |
| [IPIBench, 2026](https://arxiv.org/abs/2605.27074) | Proactive monitoring, task cancellation/modification, multi-task management, reactive/proactive interleaving. | Active user goals and task management are not new in isolation. A revised visual belief should be linked to whether the right standing task state changes. |
| [StreamArena, 2026](https://arxiv.org/abs/2608.05703) | 243 videos averaging 88.8 minutes; 3,646 manually checked open-ended tasks for perception, retrospection, proactive interaction, and tools, with query and evidence timestamps. | The previous broad proposal (“sustained real-world agent tasks across memory, timing, tools”) substantially overlaps. Need a task-level contrast/annotation field that it does not provide. |
| [StreamMemBench, 2026](https://arxiv.org/abs/2606.14571) | Evidence from continuous egocentric streams is traced through initial assistance, user feedback, and later reuse. | Stream-grounded assistance and correction incorporation are covered. Our correction should be triggered by later visual evidence about a specific event, not user-provided corrective text, and should test event attribution. |
| [APM-Bench, 2026](https://arxiv.org/abs/2609.37559) | Persistent memory over related sessions, real-time perception, adaptive responses, and whether evidence is unavailable. | Cross-session persistence, abstention for missing evidence, and utility/latency/storage tradeoffs are occupied. Avoid a generic memory benchmark. |
| [DeltaStreamer, 14 Oct. 2026 preprint](https://arxiv.org/abs/2610.19849) | Change-aware memory, query-driven planning, source-linked historical frame retrieval and replay for recovering missed visual details. | This is the closest methodological overlap. Replay/retrieval, event deltas, or a tool to inspect old frames cannot be our claimed novelty. Test what happens after retrieved evidence conflicts with an existing event record and prior actions. Verify the latest version and released implementation before finalizing claims. |
| [SoccerNet replay grounding](https://www.soccer-net.org/tasks/replay-grounding) | Matches broadcast replay clips to the original live event timestamp. | Replay identity is existing computer-vision work. Our extension, if validated, is evidence-dependent record revision and downstream decision evaluation, not replay matching itself. |
| [OVIBench, EMNLP 2026](https://arxiv.org/abs/2608.22279) | Interruption handling, including user corrections, cancellations, and false triggers. | Human-issued correction handling is adjacent. Keep visual evidence as the source of revision and distinguish it from explicit user correction. |
| [VSAS-Bench, CVPR 2026 Findings](https://openaccess.thecvf.com/content/CVPR2026F/html/Vasu_VSAS-Bench_Real-Time_Evaluation_of_Visual_Streaming_Assistant_Models_CVPRF_2026_paper.html) | Synchronous/asynchronous streaming evaluation and accuracy-latency/resource tradeoffs. | A generic runtime protocol and latency score are not novel. We still need a reproducible common harness and report latency as a controlled dimension. |
| [OVO-S-Bench, 2026](https://arxiv.org/abs/2606.03890) | Human-annotated streaming spatial intelligence over scenes and source videos. | Spatial state understanding is adjacent, but not evidence of historical revision. Avoid framing static spatial QA as the core. |

This is a targeted primary-source review, not a systematic review. Preprints can change, releases may differ from papers, and absence of a phrase or field in an abstract does not establish absence from a benchmark. The Drive survey has additional references; reconcile its spreadsheet against current versions, code, and data before manuscript claims.

## 3. Sharpened candidate RQs

Organize the work around one central question and three linked experiments. RQ2/RQ3 are dependent capabilities, not unrelated benchmark tracks.

### Central RQ

**When new visual evidence bears on a past event, can a streaming agent revise the correct event record and the decisions that depend on it, while preserving event identity, unsupported uncertainty, and the live task state?**

Define “revision” operationally: a previously emitted or internally represented event claim changes after new evidence; the updated claim carries evidence provenance; dependent task state is recomputed or left unchanged according to a predeclared dependency map. Merely answering a later question correctly does not count as revision.

### RQ1 — Evidence-to-event attribution

**Given visually similar candidate events, how accurately does the agent determine whether later evidence concerns the same earlier occurrence, a different occurrence, or no identifiable event?**

Controls: same event / replay or alternate view; genuinely repeated action; similar but distinct event; irrelevant footage; evidence insufficient to link. Separate recognition of the revealed object/state from attribution of the evidence to an event. Report event-link precision/recall and selective risk versus coverage; do not condition the headline metric only on successful recognition.

### RQ2 — Selective event revision

**After evidence is linked, does the agent change only claims supported by that evidence, including changing an unsupported guess to unknown when warranted?**

Measure claim-level correction, justified addition, false revision, unsupported certainty, collateral changes, duplicate-event creation, and preservation of verified facts. Include evidence that confirms, contradicts, refines, or does not resolve the earlier claim. Use structured facts and accepted values where possible; open-ended explanation is secondary.

### RQ3 — Decision propagation under live operation

**Does a correct event revision update the appropriate pending recommendation, alert, or task status without disrupting unrelated current monitoring?**

Predefine a small domain-specific rule/dependency graph (for example, “unverified latch” alert is cleared only if later evidence shows the same connector latched). Measure correct retract/retain/change decisions, false actions, missed live events, and response latency. For offline video, score decision correctness and timeliness only; do not claim physical outcome improvement. Use an instrumented simulator or approved live study for outcomes caused by action.

### RQ4 — Mechanism and budget (secondary, only after RQ1–3 reproduce)

**Which combination of event-linked memory, evidence provenance, and targeted reinspection improves revision quality at matched visual and inference budgets?**

Compare ordinary history prompting, full-history/joint-context oracle, retrieval-only, targeted replay, structured event ledger, and an evidence-gated revision policy. This is a method question, not presumed novelty. Include abstention as a valid behavior, but charge for unresolved cases and show risk-coverage curves so an always-unknown system cannot win.

### Candidate contribution statement (provisional)

“We study visually grounded revision of streaming event records: whether agents can attach later evidence to the right earlier occurrence, selectively update its claims, and propagate the update to dependent assistance decisions. We introduce paired event episodes that contrast same-event evidence, similar new events, and insufficient evidence, and evaluate both event-record quality and downstream decision changes under causal streaming constraints.”

Use only if released benchmark audits confirm that the exact unit and measures are missing from the nearest work. Do not claim “first,” “unexplored,” or guaranteed novelty yet.

## 4. Experimental design that makes the claim credible

Each episode needs an initial phase, intervening live events, an evidence/replay phase, and a follow-up phase. At each phase record the agent-visible stream, user instruction, available tools, event ledger/action state, and wall-clock response trace.

Use a factorial construction where feasible:

| Factor | Suggested levels |
|---|---|
| Linkage | Same occurrence / repeated similar occurrence / unrelated / unresolvable |
| Evidence effect | Confirms / contradicts / refines / no new information |
| Delay | Short / medium / long event-to-evidence gap |
| Intervening context | None / unrelated events / confusable candidate events |
| Current load | No concurrent task / active current task / time-critical alert |
| Prior answer | Unknown / correct / plausible unsupported error (controlled intervention) |

Do not cross the full Cartesian product blindly. Use a preregistered fractional design or targeted matched pairs and report which factors are randomized. RQ2 history intervention must use identical video inputs, prompts apart from the history field, counterbalanced order, multiple independent episodes, and separate natural-history versus synthetic-history results. Score model variation across repeated runs and never count repeated prompts on one clip as independent episodes.

Baselines should include: (1) current-window model; (2) full visual history where technically possible; (3) answer-from-all-evidence joint-context upper bound; (4) text-summary memory; (5) event-retrieval memory; (6) targeted video replay/reinspection; (7) no-revision and always-unknown policies; (8) a strong human annotation/decision reference. Compare model backbones through a common harness where feasible, and systems in a separately labeled native-system track. Log exact frames, timestamps, prompts, outputs, tool calls, compute/memory use, and wall-clock latency.

Statistical unit is the independent source episode, not question turn or frame. Report clustered bootstrap confidence intervals by recording/source participant/game, paired contrasts, effect sizes, per-domain results, and failure categories. Use a held-out source/domain split and deduplicate near-identical footage across train/dev/test. Calibrate any LLM judge against blinded human ratings; do not make a model judge the sole ground truth for event identity or visual support.

## 5. Dataset preparation strategy

### Stage A — Source and rights audit before annotation

The project’s candidate-source lists include HoloAssist, Assembly101, Ego4D/ Ego-Exo4D, EPIC-KITCHENS/HD-EPIC, MEVA/MEVID, and SoccerNet. Treat these as leads, not admitted data. Create a source register with: official source URL/version, license and redistribution terms, participant consent/privacy constraints, raw video access, synchronized views/audio/metadata, event annotations, duration, candidate episodes, extraction permissions, face/identity sensitivity, and whether derived clips/frames may be redistributed. Do not assume a public download is a public redistribution license. If raw data cannot ship, make annotations and scripts usable against the official source and provide legally shareable derived assets only.

Source prioritization:

1. **HoloAssist / Assembly101 / Ego-Exo4D / HD-EPIC:** inspect for procedural events and alternate views; manually verify that the second observation proves something about the same action and that intervening changes do not invalidate the inference.
2. **SoccerNet:** strong source for replay-to-original identity and live continuation, but replay linkage exists already; use only if additional replay evidence changes an event fact or decision beyond matching the timestamp.
3. **MEVA / MEVID:** potential long-duration multi-camera surveillance and repeated-event confounds; assess access, privacy, and camera synchronization before prioritizing.
4. **Controlled recordings:** fill precise counterfactual cells (same event vs similar new event, evidence sufficient vs insufficient) that natural corpora lack. Keep them a separate controlled split and report natural and constructed results separately.

Do not create the benchmark by cutting a later physical state and calling it evidence about an earlier state unless same-event identity and no intervening state-changing action are independently established. Controlled occlusion can establish initial uncertainty, but must be labeled as an intervention, not a natural stream property.

### Stage B — Candidate mining and admission gates

Use existing temporal/action labels, narration, replay metadata, synchronized-camera metadata, and manual search to identify candidates. Automated models may propose intervals only; they cannot approve inclusion. Admit an episode only when annotators can verify all of:

1. A specific event has a stable identity and interval.
2. At the initial decision point, the target claim is genuinely unresolved from the available prefix (or the intervention explicitly hides it).
3. Later evidence becomes available at a known time and supports a particular claim.
4. The evidence-to-event link is independently clear, or the example is intentionally labeled ambiguous/insufficient.
5. Ground truth identifies claims that should change and protected claims that should remain.
6. If downstream action is evaluated, the dependency from claim to action is explicit and domain-justified.
7. Prefix-only annotators cannot use future footage; full-context annotators validate final event linkage separately.

Maintain a candidate funnel: mined → first-pass verified → adjudicated → pilotable → released. Publish rejection reasons and counts. Do not select cases because a model failed on them.

### Stage C — Annotation schema

Store a machine-readable event graph, not only QA pairs:

```json
{
  "episode_id": "...",
  "source_id": "...",
  "event_id": "E2",
  "event_interval": [19.2, 22.8],
  "decision_time": 22.8,
  "claims": [{
    "claim_id": "latch_engaged",
    "value_at_t0": "unknown",
    "value_after_evidence": "yes",
    "status": "resolved",
    "support_intervals": [[47.1, 49.0]],
    "evidence_arrival_time": 49.0,
    "link_type": "same_occurrence",
    "confidence_or_ambiguity": "clear"
  }],
  "protected_facts": ["event_count", "current_step"],
  "dependent_decisions": [{
    "decision_id": "clear_unverified_latch_alert",
    "expected_change": "retract",
    "valid_time_window": [49.0, 52.0]
  }],
  "condition": "natural_multiview"
}
```

Add source timebase, capture and arrival timestamps, frame sampling policy, replay provenance, camera identity, audio availability, allowed tools, knowledge visible in each prefix, annotator rationale, and disagreement/adjudication fields. Version the schema and preserve source references/hashes.

### Stage D — Annotation workflow and reliability

1. **Prefix annotator:** watches only evidence available before the reveal and labels what can/cannot be known, the event ledger, and what action is justified then.
2. **Evidence annotator:** sees the reveal and labels claim-level support, event linkage, earliest evidence time, and whether it adds information.
3. **Independent auditor:** checks source identity, intervals, event links, confusable alternatives, and protected facts without seeing model outputs.
4. **Adjudication:** resolve disagreements with a written rule; retain raw judgments. Report agreement separately for event linkage, claim state, evidence interval, and action consequence (appropriate categorical agreement/statistics, not one pooled accuracy).
5. **Pilot qualification:** test annotation clarity with humans and simple policies. A case with unclear human linkage or no discriminative power is excluded or moved to a clearly labeled exploratory set.

Use model-generated QA only as a drafting aid. Human review must inspect the actual video and prefixes. Keep annotators blind to model identity/results and to future video during prefix judgments.

### Stage E — Splits, scale, and release

Split by original recording, participant, match, or source session—not by derived clips. Hold out at least one source/domain family for generalization if source count permits. Prevent leakage from overlapping camera views, adjacent clips, near duplicates, shared transcripts, and public QA. Publish train/dev/test roles explicitly; keep test labels hidden where appropriate. A smaller, audited benchmark with a clear independent episode count is preferable to inflated counts of many QA variants from a few videos.

Recommended sequencing:

- **Pilot (go/no-go):** 20–40 candidate episodes from 2–3 source families; independently annotate and score a fixed pilot across at least 3 model/system classes. This is a design pilot, not a paper-scale result.
- **Main benchmark:** scale only after admission yield, annotator agreement, and a reproducible failure are established. Aim for enough independent source episodes per primary contrast to power a paired, clustered analysis; estimate variance from the pilot before fixing the number. Do not assert a benchmark-size target before this calculation.
- **Release:** annotation JSON, evaluation harness, exact streaming/replay protocol, model traces where licensing allows, source manifest, license/ethics statement, known limitations, and a small public development subset.

## 6. Metrics: primary outcomes before composite score

Report a dashboard first; avoid a single score that can hide abstention or a timing/accuracy tradeoff.

- **Attribution:** event-link accuracy and macro-F1 across same-event, new-event, unrelated, and ambiguous cases.
- **Revision:** claim-level justified update rate, missed update rate, false update rate, unsupported assertion rate, and collateral-change rate.
- **Identity/count preservation:** event duplication, merge, deletion, and order errors.
- **Decision propagation:** proportion of dependent actions correctly changed, retained, or retracted; false interventions and missed interventions.
- **Live continuity:** current-state accuracy and urgent-event recall during revision windows.
- **Uncertainty:** risk-coverage curve and calibration/abstention analysis.
- **Cost:** evidence inspected, tool calls, wall-clock latency, memory/token use, and response-window misses.

Define denominators, matching rules, partial credit, and the “earliest justified response” window before model evaluation. Avoid using free-form LLM judging as the sole score. A composite may be secondary, with a preregistered formula and component scores always shown.

## 7. Go/no-go and paper-strength criteria

### Go to full collection only if

- a released-data audit shows the exact event-revision plus downstream-decision protocol is not already covered by the closest datasets;
- human annotators can reliably distinguish same occurrence from similar new occurrence and identify evidence-supported changes;
- sufficient qualifying natural examples exist, or controlled examples are clearly separated and the paper does not overclaim natural prevalence;
- at least one meaningful model failure or ranking reversal is reproducible over independent episodes and survives strong retrieval/full-context baselines;
- revision quality predicts downstream decision quality in a defensible, predeclared manner.

### No-go or reframe if

- the principal error is ordinary retrospective retrieval already measured by StreamArena/DeltaStreamer;
- qualifying samples require annotators to infer hidden causes from a later state with no event linkage;
- only synthetic occlusion cases work and the paper’s claim is framed as natural real-world prevalence;
- model effects disappear after controlling for recognition, video sampling, prompt, and backend variability;
- one composite score or LLM judge is doing most of the scientific work.

For CVPR, benchmark novelty alone is stronger when paired with (1) a demonstrated measurement blind spot in existing benchmarks, (2) a careful and reproducible corpus/protocol, (3) broad baselines with statistically sound findings, and (4) a useful diagnostic or method result. Acceptance cannot be guaranteed by any checklist.

## 8. Immediate work order

1. Audit the released examples/code for StreamArena, DeltaStreamer, IPIBench, APM-Bench, ProactiveBench, and StreamMemBench against the exact annotation fields in Section 3. Record yes/no/partial with evidence; do not infer from abstracts.
2. Write a one-page preregistration for the same-event / similar-new-event / insufficient-evidence contrasts and primary outcomes.
3. Run a source census and rights audit for the proposed candidate corpora; estimate eligible episode yield before coding a large annotation pipeline.
4. Annotate 20–40 pilot episodes with the blind multi-stage workflow; calculate agreement and clustered variance.
5. Run the fixed model comparison with common inputs and baselines. Decide whether to scale, narrow to one domain, or reframe.

## References checked

- OVO-Bench: https://openaccess.thecvf.com/content/CVPR2025/html/Niu_OVO-Bench_How_Far_is_Your_Video-LLMs_from_Real-World_Online_Video_CVPR_2025_paper.html
- OVBench / VideoChat-Online: https://openaccess.thecvf.com/content/CVPR2025/papers/Huang_Online_Video_Understanding_OVBench_and_VideoChat-Online_CVPR_2025_paper.pdf
- SPOT-Bench: https://arxiv.org/abs/2604.24317
- StreamReady: https://arxiv.org/abs/2603.08620
- IPIBench: https://arxiv.org/abs/2605.27074
- StreamArena: https://arxiv.org/abs/2608.05703
- StreamMemBench: https://arxiv.org/abs/2606.14571
- APM-Bench: https://arxiv.org/abs/2609.37559
- DeltaStreamer: https://arxiv.org/abs/2610.19849
- SoccerNet replay grounding: https://www.soccer-net.org/tasks/replay-grounding
- OVIBench: https://arxiv.org/abs/2608.22279
- VSAS-Bench: https://openaccess.thecvf.com/content/CVPR2026F/html/Vasu_VSAS-Bench_Real-Time_Evaluation_of_Visual_Streaming_Assistant_Models_CVPRF_2026_paper.html
- OVO-S-Bench: https://arxiv.org/abs/2606.03890

