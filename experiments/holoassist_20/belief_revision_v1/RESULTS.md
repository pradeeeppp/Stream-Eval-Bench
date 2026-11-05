# Twenty-video Qwen2.5-VL-3B belief revision findings

Execution status: **complete**. Actual saved benchmark responses: **100/100**.

Seventeen original tasks have provisional labels; HA05/HA09/HA10 are diagnostic-only. Fourteen cases have a known earlier state suitable for testing clean correction. HA06/HA08/HB06 retain an unknown earlier label. All labels await independent annotation.

Among 17 completed qualified cases, both final fields are correct in 4 joint, 11 chronological, and 12 reversed-arrival runs. These counts concern expressed state values; evidence correctness is reported separately.

Reversed final known-fact-plus-packet correctness is 0/31. Value corrections therefore do not establish successful evidence association. A no-pixel schedule baseline also exploits the negative-to-positive label pattern; see the interpretation below.

## Per-video results

| Video | Status | Joint fields | Chronological final fields | Reversed final fields |
|---|---|---|---|---|
| [HA01](analysis/HA01.md) | complete | 1/2 | 0/2 | 2/2 |
| [HA02](analysis/HA02.md) | complete | 1/2 | 1/2 | 2/2 |
| [HA03](analysis/HA03.md) | complete | 1/2 | 2/2 | 2/2 |
| [HA04](analysis/HA04.md) | complete | 1/2 | 2/2 | 2/2 |
| [HA05](analysis/HA05.md) | diagnostic_only | unscored | unscored | unscored |
| [HA06](analysis/HA06.md) | complete | 1/2 | 0/2 | 0/2 |
| [HA07](analysis/HA07.md) | complete | 1/2 | 2/2 | 2/2 |
| [HA08](analysis/HA08.md) | complete | 2/2 | 2/2 | 1/2 |
| [HA09](analysis/HA09.md) | diagnostic_only | unscored | unscored | unscored |
| [HA10](analysis/HA10.md) | diagnostic_only | unscored | unscored | unscored |
| [HB01](analysis/HB01.md) | complete | 2/2 | 0/2 | 0/2 |
| [HB02](analysis/HB02.md) | complete | 1/2 | 2/2 | 2/2 |
| [HB03](analysis/HB03.md) | complete | 1/2 | 1/2 | 2/2 |
| [HB04](analysis/HB04.md) | complete | 1/2 | 2/2 | 2/2 |
| [HB05](analysis/HB05.md) | complete | 1/2 | 2/2 | 2/2 |
| [HB06](analysis/HB06.md) | complete | 2/2 | 0/2 | 1/2 |
| [HB07](analysis/HB07.md) | complete | 2/2 | 2/2 | 2/2 |
| [HB08](analysis/HB08.md) | complete | 1/2 | 2/2 | 1/2 |
| [HB09](analysis/HB09.md) | complete | 1/2 | 2/2 | 2/2 |
| [HB10](analysis/HB10.md) | complete | 1/2 | 2/2 | 2/2 |

## Condition comparison

Only the 17 provisionally qualified cases enter this table. State fields include required unknown answers; known fields exclude unresolved states.

| Phase | Correct state fields | Correct known facts | Correct known fact + packet | Both fields correct |
|---|---|---|---|---|
| joint | 21/34 | 18/31 | 16/31 | 4/17 |
| chronological_0 | 7/34 | 3/28 | 0/28 | 2/17 |
| chronological_1 | 24/34 | 23/31 | 12/31 | 11/17 |
| delayed_0 | 31/34 | 14/17 | 14/17 | 14/17 |
| delayed_1 | 27/34 | 27/31 | 0/31 | 12/17 |

Response format across completed cases: 100/100 exact JSON; 100/100 valid four-key schema.

## Outcomes with explicit denominators

| Measure | Cases satisfying measure / applicable cases |
|---|---|
| uncertainty_preserved_before_earlier_evidence | 17/17 |
| unsupported_earlier_commitment | 0/17 |
| historical_final_factual_correct | 13/14 |
| historical_epistemic_correct | 13/17 |
| clean_historical_update_success | 13/14 |
| recent_fact_preserved | 14/14 |
| past_fact_preserved_chronological | 0/1 |
| joint_final_perfect | 4/17 |
| chronological_final_perfect | 11/17 |
| delayed_final_perfect | 12/17 |
| joint_correct_both_sequential_fail | 2/17 |
| joint_and_chronological_correct_delayed_fails | 1/17 |

Descriptive checks added during result inspection (qualified cases only):

- Chronological first-step answers disagree about the same capture-time condition: 14/17.
- Reversed final latest answers cite older packet A: 14/17.

Paired condition patterns:

- Joint correct, both sequential finals fail: HB01, HB06.
- Joint and chronological correct, reversed final fails: HA08.

## Interpretation

The tables report two-field output correctness, including required unknown answers. Known-fact accuracy and value-plus-evidence accuracy are recorded separately in analysis.json. Conditional preservation excludes cases where the initial answer was already incorrect. No missing or infrastructure-failed request is scored as a model error.

Joint success with failure in both sequential orders describes a segmented-input difficulty; it does not identify a state-maintenance mechanism. Joint and chronological success with a delayed failure is an order-sensitive candidate within this protocol. The only such case here, HA08, has expected earlier=unknown, so it concerns uncertainty maintenance rather than failure to recover a known earlier fact. HB06 also has an unknown earlier label. One trial does not establish a reproducible mechanism or a novel streaming-specific phenomenon.

A label-balance check reveals an additional limit: a rule that never inspects pixels and always answers earlier=unknown until A, earlier=no after A, and latest=no before B/yes after B achieves 31/34 final state fields and 14/17 fully correct cases. It also produces all fourteen required unknown-to-no transitions. This is an analytical baseline, not a model execution. Therefore high value-transition success alone cannot establish visual evidence use. Balanced unchanged-positive, unchanged-negative and positive-to-negative controls are needed for that claim.

This uses two event-centered four-frame video packets and external JSON memory. The same eight frames are used across conditions. It does not evaluate all frames of each recording or reproduce the PDF's separate uniform whole-video sampling. It also does not test natural replay discovery or calibrated confidence.
