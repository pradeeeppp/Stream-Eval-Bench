# All-video evidence-graph review status

Plan executed for **20/20 videos**: whole-clip sampled overview, candidate-window inspection, local native-frame review, delivered-frame review, typed graph and per-video report.

**These are private single-assistant proposals, not independently adjudicated gold.** The legacy scorer and labels are unchanged.

| Video / review | Original-task qualification | Reviewed positive packet | Legacy positive packet | Findings |
|---|---|---:|---:|---|
| [HA01](HA01/README.md) | provisional | 8 | 8 | Distinct lens detachment, return and cap removal. Preserve historical detachment after current state changes. |
| [HA02](HA02/README.md) | provisional | 16 | 16 | Separate central LCD illumination from earlier side-button lights. Display later darkens, which does not erase the illumination event. |
| [HA03](HA03/README.md) | provisional | 117 | 118 | Separate carrying/alignment from seated placement and later unsupported standing. Do not infer that every fastener is secure. |
| [HA04](HA04/README.md) | provisional | 18 | 19 | Closer inspection separates earlier handle operation and camera motion from actual door opening around 18.3–18.5 s. Later close/reopen is a separate occurrence candidate. |
| [HA05](HA05/README.md) | requires_adjudication | 29 | 38 | An earlier washer-bin reach is visible around 29.5 s; later screw-bin reach is around 38.5 s. Broad metal-fasteners wording may admit the earlier occurrence, conflicting with legacy early-alert scoring. |
| [HA06](HA06/README.md) | provisional | 81 | 81 | Separate opening the compartment, partial ejection, full removal, and later memory-card manipulation. |
| [HA07](HA07/README.md) | provisional | 14 | 15 | Opening the case precedes camera extraction and must not trigger the task. Later accessory/battery work is a different event. |
| [HA08](HA08/README.md) | provisional | 20 | 21 | The visual target is vessel tilt over the opening. Do not infer water flow, amount transferred, or reservoir detachment from this pose alone. |
| [HA09](HA09/README.md) | requires_adjudication | 14 | 14 | The ringed face shown by the legacy positive is already visible earlier. The clip establishes lifting/rotation, but underside identity and a newly revealed underside require adjudication. |
| [HA10](HA10/README.md) | requires_adjudication | 23 | 23 | Legacy target segment primarily shows reorientation of the whole cart. Tilting away from an upright frame is not supported when the frame tilts too. |
| [HB01](HB01/README.md) | provisional | 41 | 52 | Closer review shows a loose belt clear of the pulley route around 41.5 s. The legacy 47 s pre-event checkpoint is already after removal, so valid earlier alerts could be scored false. |
| [HB02](HB02/README.md) | provisional | 17 | 18 | Separate handle operation from door opening. Preserve occurrence identity across later close/reopen. |
| [HB03](HB03/README.md) | provisional | 7 | 8 | Separation is visible around 7 s, earlier than the legacy 8 s positive label; later return must not erase history. |
| [HB04](HB04/README.md) | provisional | 15 | 16 | Distinguish opening the packaging from the camera clearing its recess. |
| [HB05](HB05/README.md) | provisional | 27 | 28 | Separate moving the whole tower, releasing/sliding the panel, and complete panel removal. |
| [HB06](HB06/README.md) | provisional | 77 | 85 | A green expansion board is visibly removed around 77.5 s, well before the legacy 85 s positive. Avoid merging later board handling into the same occurrence. |
| [HB07](HB07/README.md) | provisional | 8 | 11 | Separate grasping, initial lift, complete clearance and setting the top aside. |
| [HB08](HB08/README.md) | provisional | 101 | 102 | Fastener manipulation is preparatory; the target is clearance of one tracked long rail from the remaining frame. |
| [HB09](HB09/README.md) | provisional | 52 | 52 | Specify the paper drawer below the main front cover. Do not merge it with later toner-cover opening. |
| [HB10](HB10/README.md) | provisional | 27 | 33 | Higher-resolution review distinguishes alignment/handle operation at 26–27 s from clearly visible flowing water at about 27.5 s, earlier than the legacy 33 s label. |

Packet values above are output-grid labels. Actual source PTS and frame indices are in each report/graph.
A reviewed positive earlier than the legacy positive is a demonstrated earlier evidence point, not proof of the exact onset or the earliest qualifying observation.

Three original task definitions require adjudication: HA05 (which hardware bin), HA09 (which face is the underside, and whether it was already exposed), HA10 (whole-cart motion versus basket/frame relative motion). HB01 also has a legacy pre-event checkpoint after the observed removal; do not use that checkpoint to judge early alerts without correction.

## Remaining research validation

- Independent annotation, disagreement measurement and adjudication.
- Exhaustive earlier-occurrence review where first-occurrence scoring is required.
- Resolve the three task definitions and review all deadline policies.
- Implement a versioned scorer/protocol migration before using these proposals as new gold.
- No retrospective evidence-revision qualification or model-performance claim follows from this review.
