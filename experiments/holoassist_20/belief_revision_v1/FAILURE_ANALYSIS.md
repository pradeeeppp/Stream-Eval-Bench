# Historical Belief Revision in Streaming Video

Failure analysis across 20 HoloAssist videos | Qwen2.5-VL-3B | 4 November 2026

## Research question

Can late-arriving video evidence correct a model's knowledge of the past, affect the right capture-time claim, and preserve already supported recent states? The event is fixed; the model's expressed belief and its claimed evidence may change. [1, 2]

## Experimental evidence

Each recording supplies two event-centered packets: four native frames in earlier packet A and four in later packet B. The same eight frames are tested jointly, chronologically (A then B), and in reversed arrival order (B then A). Sequential requests see only the current packet and the exact prior response as external memory. Capture times and packet IDs are supplied explicitly.

Evidence panel: HA01, exact four-frame packets A and B; source capture timestamps.

HA01 example: A ends at 8.044704 s; B ends at 8.512032 s. Condition: lens visibly separated from the DSLR body. Provisional endpoint labels: A=no, B=yes. These are sampled packets, not full-length clips.

| Condition | Both states correct | Correct state fields | Known fact + packet |
| --- | --- | --- | --- |
| Joint final | 4/17 | 21/34 | 16/31 |
| Chronological final | 11/17 | 24/34 | 12/31 |
| Reversed final | 12/17 | 27/34 | 0/31 |

**Central finding:** state values are often recovered in reversed order, but none of the 31 known final fields has both a correct value and the required packet citation. A no-video schedule rule also scores 31/34 final state fields. Value correction alone therefore does not establish evidence use.

100 requests completed; one greedy trial per condition. Seventeen targets are provisionally scored; HA05, HA09 and HA10 are diagnostic-only. All labels await independent adjudication. [1, 2]

---

## Question one: can knowledge change while the past event stays fixed?

Before A arrives in reversed order, earlier=unknown in 17/17 qualified cases. In the 14 cases with a known earlier label, 13/14 show the observable transition unknown to no after A. Unlike a correct early guess, this is a change in the historical value. It is still a value-only measure, not proof of visual grounding.

## HB01: joint success, failure in both sequential orders

Condition: the drive belt is free of the machine pulley route. Earlier target: 34.489038 s (no); later target: 41.781579 s (yes). The positive endpoint precedes the legacy 52 s anchor; this run uses the reviewed native endpoint. [1, 2]

Evidence panel: HB01, exact four-frame packets A and B; source capture timestamps.

| Input step | Expected earlier / latest | Observed earlier / latest |
| --- | --- | --- |
| Joint A+B | no / yes | no / yes |
| Chronological: A | no / no | no / no |
| Chronological: B | no / yes | unknown / no |
| Reversed: B | unknown / yes | unknown / no |
| Reversed: A | no / yes | unknown / no |

Chronological input first gives the correct no/no values. After B, earlier becomes unknown and latest stays no: a correct historical value is lost and the later positive is missed. Reversed input gives unknown/no before and after A, so the historical correction never occurs. Its latest answer was already wrong, so this is not loss of an initially correct recent fact.

HB08 illustrates a different limit: reversed input does correct earlier from unknown to no, but ends no/no when no/yes is required. Historical correction can succeed while the full state remains wrong.

**Answer:** observable historical value revision occurs in 13/14 eligible cases. That does not establish a stable evidence-driven policy: no-pixel rules can produce the same transitions, citations are incorrect, and individual sequential failures remain. Joint value success is a comparison condition, not proof of an internal representation or perception mechanism.

---

## Question two: which belief does the new evidence affect?

Fixed capture-time claims and evidence packet IDs make state accuracy separable from citation accuracy. Earlier targets A; latest targets B once B has arrived, even when older A is received last. A supplied packet ID tests expressed temporal attribution, not natural discovery that two views show the same event.

## HA01: correct reversed values, incorrect supporting packet

| Input step | Expected E / L | Observed E / L | Cites E / L |
| --- | --- | --- | --- |
| Joint A+B | no / yes | unknown / yes | [] / ['B'] |
| Chronological: A | no / no | unknown / no | [] / [] |
| Chronological: B | no / yes | yes / no | ['A'] / ['B'] |
| Reversed: B | unknown / yes | unknown / yes | [] / ['B'] |
| Reversed: A | no / yes | no / yes | [] / ['A'] |

After B, the model says unknown/yes and correctly cites B for latest. After older A, the values become no/yes, but earlier has no cited support and latest now cites A. The true latest target is still B's capture time. A correct value has survived while its expressed support has moved to the wrong packet.

Fixed claim: earlier at 8.044704 s -> A; latest at 8.512032 s -> B.
Observed reversed final: earlier=no -> []; latest=yes -> [A].

| Check | Observed result | Meaning |
| --- | --- | --- |
| Known final value + packet | Joint 16/31; chronological 12/31; reversed 0/31 | Value-only scores hide evidence-association errors. |
| Reversed latest cites older A | 14/17 qualified cases | All 14 initially correct recent values are preserved, but each ends with the wrong A citation. |
| Same-time field disagreement | 14/17 chronological first steps | At this step both fields target the identical A endpoint; different answers are inconsistent. |

**Answer:** the model does not consistently assign expressed support to the requested capture-time claim. The observable errors include missing historical support, older-packet citations for the later claim, and conflicting same-time answers. They do not distinguish internal forgetting, overwriting, misbinding or a generic citation/prompt-following failure.

Graph implication: keep evidence observations, fixed claims and model beliefs as separate node types. The exported belief graphs retain each request and memory link; model-cites edges remain unverified assertions. A correct state value does not turn these into verified support edges. [2]

---

## Question three: when should the model revise or remain uncertain?

Unknown has two distinct reasons here: the relevant packet has not arrived, or the received packet does not settle the visual relation. The second reason applies to HA06, HA08 and HB06 even after A. Those cases are uncertainty-maintenance tests, not clean unknown-to-known opportunities.

## HA08: the only joint-and-chronological success with reversed failure

Evidence panel: HA08, exact four-frame packets A and B; source capture timestamps.

Condition: vessel tilted with its mouth over the open reservoir. Earlier target 19.498907 s remains unresolved; later target 20.798834 s is positive. Both joint and chronological final outputs are unknown/yes. Reversed output changes unknown/yes to no/yes after A. The earlier no is unjustified under the provisional packet label; this is an uncertainty-maintenance error. [1, 2]

| Case | Expected final E / L | Reversed first -> final | Failure distinction |
| --- | --- | --- | --- |
| HA06 | unknown / yes | unknown / unknown -> no / unknown | Earlier overcommitment plus missed later positive. |
| HA08 | unknown / yes | unknown / yes -> no / yes | Earlier overcommitment; later value preserved. |
| HB06 | unknown / yes | unknown / yes -> no / yes | Earlier overcommitment; both sequential finals fail. |

Recent values are preserved in 14/14 eligible reversed runs; the denominator includes only cases whose latest value was initially correct. HA06, HB01 and HB08 are excluded from this preservation rate because latest was already wrong or unknown. Historical preservation in chronological order is 0/1: only HB01 starts with a correct known earlier value.

**Answer:** the model appropriately abstains before unseen historical evidence in 17/17 qualified cases, but does not reliably remain uncertain when received evidence is inconclusive. Correct recent values can persist with incorrect evidence citations. These are expressed state and abstention outcomes; no probability calibration or internal confidence is measured.

---

## Current conclusion and failure taxonomy

| Observed pattern | Cases or count | Supported interpretation |
| --- | --- | --- |
| Joint correct; both sequential finals fail | HB01, HB06 | Segmented-input difficulty in these cases; HB06 has an unknown prior label. |
| Joint + chronological correct; reversed fails | HA08 only | Order-sensitive uncertainty failure in one trial; not failure to recover a known earlier fact. |
| All final state values correct | HB07 only | A positive value-level comparison; its reversed citations are still incorrect. |
| Invalid JSON or truncated output | 0/100; 0/100 | Observed errors are not explained by invalid formatting or the output cap. |
| Unresolved original task | HA05, HA09, HA10 | Retain raw traces; exclude from primary correctness and revision rates. |

## What differs from the supplied findings note?

The reference table-assembly example reported a premature earlier=no commitment and loss of a previously correct latest=yes. [3] Neither pattern should be copied into this batch's conclusion: all 17 qualified reversed runs initially answer earlier=unknown, and all 14 initially correct latest values remain correct. The prominent new observation is broken evidence attribution despite retained values. This comparison is qualitative: prompts, sampling and the reference's undocumented runtime settings prevent an exact replication claim.

## A no-video rule exposes a benchmark confound

Consider an analytical rule: earlier=unknown until A, then no; latest=no until B, then yes. Without examining any pixels, it achieves 31/34 final state fields, 14/17 fully correct cases and all 14 unknown-to-no transitions. This is a label-balance calculation, not a model run. The observed model reaches only 12/17 fully correct reversed finals. These results cannot establish visual evidence use or reliable historical revision from value-transition scores alone.

## Next experiment

**1.** Balance unchanged-positive, unchanged-negative, negative-to-positive and positive-to-negative cases. Add wrong-time and shuffled-packet controls to test whether answers depend on the evidence. **2.** Obtain independent labels and adjudicate HA05/HA09/HA10 and uncertain endpoints. **3.** Grade value correctness, time targeting, evidence citations and conditional preservation separately; retain same-time consistency checks. **4.** Repeat across trials and vary packet gaps and memory format before estimating reliability or attributing an internal mechanism.

Scope: one deterministic trial, event-centered eight-frame inputs and external response memory. This is not native continuous-stream evaluation, natural replay discovery, a causal mechanism experiment, or a reproduction of the reference's separate uniform whole-video sampling experiment.

---

## Appendix: all 20 videos

Every entry is an exact final earlier/latest output, not an accuracy percentage. N=no, Y=yes, U=unknown. Gold denotes provisional endpoint labels after both packets. Dashes mark unscored targets; highlighted rows are diagnostic-only. Earlier questions and latest boundaries use the capture endpoints recorded in cases.json.

| ID | Visible condition (short label) | Gold | Joint | Chronol. | Reversed |
| --- | --- | --- | --- | --- | --- |
| HA01 | DSLR lens separated | N / Y | U / Y | Y / N | N / Y |
| HA02 | Printer LCD illuminated | N / Y | U / Y | U / Y | N / Y |
| HA03 | Round tabletop seated | N / Y | U / Y | N / Y | N / Y |
| HA04 | Cabinet door open | N / Y | U / Y | N / Y | N / Y |
| HA05 | Hand in fastener bin | -- | N / Y | Y / N | N / U |
| HA06 | DSLR battery clear | U / Y | U / U | N / U | N / U |
| HA07 | Action camera out of insert | N / Y | U / Y | N / Y | N / Y |
| HA08 | Vessel tilted over reservoir | U / Y | U / Y | U / Y | N / Y |
| HA09 | Perforated-panel underside exposed | -- | U / Y | N / Y | N / Y |
| HA10 | Basket tilted relative to cart | -- | U / U | U / N | Y / N |
| HB01 | Drive belt free of pulley route | N / Y | N / Y | U / N | U / N |
| HB02 | Cabinet door open | N / Y | U / Y | N / Y | N / Y |
| HB03 | DSLR lens separated | N / Y | U / Y | N / N | N / Y |
| HB04 | Action camera out of insert | N / Y | U / Y | N / Y | N / Y |
| HB05 | Desktop side panel clear | N / Y | U / Y | N / Y | N / Y |
| HB06 | Expansion board outside chassis | U / Y | U / Y | Y / N | N / Y |
| HB07 | Round tabletop removed | N / Y | N / Y | N / Y | N / Y |
| HB08 | Black rail separated | N / Y | U / Y | N / Y | N / N |
| HB09 | Paper drawer extended | N / Y | U / Y | N / Y | N / Y |
| HB10 | Reservoir under flowing water | N / Y | U / Y | N / Y | N / Y |

## Reproducibility and sources

Official checkpoint: Qwen/Qwen2.5-VL-3B-Instruct; revision 66285546d2b821cf421d4f5eb2576359d3770cd3. FP16, Apple MPS (CPU fallback enabled), SDPA; greedy decoding, seed 20261104, 128-token cap, 112,896 max pixels/frame. The run completed 100 benchmark requests with no infrastructure failures or output-limit hits. All 100 responses are valid four-key JSON. Full provenance audit and eight metric tests passed.

[1] experiments/holoassist_20/belief_revision_v1/: cases.json, analysis.json, execution_manifest.json, responses/<ID>.json and analysis/<ID>.md. All counts were recomputed from saved outputs.

[2] experiments/holoassist_20/online_pilot_v0/reviews/batch_v1/<ID>/evidence_graph.json; belief_revision_v1/belief_graphs/<ID>.json. Source records and attribution are in online_pilot_v0/sources.json and ATTRIBUTION.md.

[3] User-supplied reference: STREAMING_BELIEF_REVISION_FINDINGS_EN.pdf, six pages. The present report follows its three-question structure; its historical examples are not pooled with this run. HoloAssist recordings are attributed to Wang et al., ICCV 2023; local source bytes come from the pinned EgoIT-99K mirror recorded in sources.json. Images show the exact selected frames, with source capture timestamps. Annotations remain provisional.
