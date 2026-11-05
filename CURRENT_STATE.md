# Stream-Eval-Bench: current state and work completed

**As of 5 November 2026.** This is the canonical project handoff and status
document. [RESEARCH_QUESTIONS.md](RESEARCH_QUESTIONS.md) defines the active questions;
[dataset expansion](docs/DATASET_EXPANSION.md) defines the next collection process.
Earlier plans remain in [docs/history](docs/history/README.md).

## 1. Research objective

> Stream-Eval-Bench asks whether a video model can use late-arriving evidence to
> correct what it knows about the past, apply that evidence to the correct
> historical event, and preserve unrelated facts and already established recent
> states.
>
> An event does not change after it happens. What may change is the model's
> knowledge of that event. This is the distinction between revising knowledge and
> rewriting event history.

The project is a research prototype with completed diagnostics and an audited
local run. It is not yet a validated cross-dataset benchmark, an established
streaming-specific limitation, a tested graph-memory method, or a verified novelty
claim. Dataset expansion should test this question with qualifying episodes and
controls, including cases where a model succeeds.

## 2. Current authoritative artifacts

| Artifact | What is complete | Location |
|---|---|---|
| Archived 20-video experiment | 100 actual Qwen2.5-VL-3B requests, exact inputs/prompts/outputs, pinned checkpoint and execution settings | [Experiment README](experiments/holoassist_20/belief_revision_v1/README.md) |
| Results | Aggregate and all 20 case analyses; 17 provisionally scored, three diagnostic-only | [RESULTS.md](experiments/holoassist_20/belief_revision_v1/RESULTS.md) |
| Factual evidence review | 20 typed graphs, 104 observation anchors and 1,491 inspected source frames recorded in review manifests | [Reviewed graphs](experiments/holoassist_20/online_pilot_v0/reviews/batch_v1/) |
| Evaluated media | 160 selected JPEGs and 20 reviewed contact sheets in a transferable, hashed bundle | [Data instructions](experiments/holoassist_20/data/README.md) |
| Failure report | Six-page report with evidence frames, exact state traces and an all-video appendix | [PDF](output/pdf/HOLOASSIST_20_FAILURE_ANALYSIS_EN.pdf), [Markdown](experiments/holoassist_20/belief_revision_v1/FAILURE_ANALYSIS.md) |
| Failure taxonomy v1 | Exclusive claim/request outcomes, diagnostic facets, all-case annotations, gap register and tests | [Taxonomy](experiments/holoassist_20/belief_revision_v1/taxonomy/README.md) |
| New GPU execution | CUDA runner, checkpoint/input verification and separate output-directory procedure | [CUDA_RERUN.md](experiments/holoassist_20/belief_revision_v1/CUDA_RERUN.md) |
| Generic environment | Schedule simulation, agent interfaces, use cases and mock tests | [stream_eval](stream_eval/) |

The CUDA tooling is prepared; the archived result documented here is the MPS
run. A script, transfer bundle or model-labelled filename is not evidence of a
completed inference run. Keep any future backend run in its own directory.

## 3. What the 20-video experiment actually evaluated

- **Model:** official `Qwen/Qwen2.5-VL-3B-Instruct`, revision
  `66285546d2b821cf421d4f5eb2576359d3770cd3`.
- **Execution:** local Apple MPS, FP16, SDPA, greedy decoding, seed 20261104;
  one trial per condition. Exact package versions are in the execution manifest.
- **Evidence:** four native frames in earlier packet A and four in later packet B,
  centered around reviewed anchors. These are not full recordings or continuous
  native-rate input. Source PTS and image hashes are retained.
- **Conditions:** A+B together; A then B; B then A. Each sequential second request
  receives only the new packet and the exact previous four-key response.
- **Output:** earlier/latest yes/no/unknown values and supporting packet IDs.
  Capture times are supplied. There are five requests per video, 100 total.
- **Labels:** single-assistant review, pending independent annotation. Seventeen
  tasks have provisional labels. Fourteen have known prior states; HA06/HA08/HB06
  retain unknown prior labels. HA05/HA09/HA10 are ungraded for task qualification.
- **Audit:** saved score recomputation, source/graph/input identities, request
  construction and memory-chain checks pass. These checks do not independently
  validate visual labels or prove a model used an image.

### Role of the evidence graph

The reviewed graph supplied source identity, frame anchors and qualification
information during offline preparation. The scorer used frozen case labels and
packet/time rules; it did not perform full graph reasoning. Qwen received images,
the predicate, IDs, timestamps and prior-response text, without the gold graph.
Model belief graphs were exported after inference for inspection. No measured
graph-memory benefit exists yet.

## 4. Main observations and their limits

| Final condition | Both state fields correct | Correct state fields | Correct known value plus required packet |
|---|---|---|---|
| Joint | 4/17 | 21/34 | 16/31 |
| Chronological | 11/17 | 24/34 | 12/31 |
| Reversed arrival | 12/17 | 27/34 | 0/31 |

- Historical unknown-to-no value correction occurs in 13/14 eligible cases.
  That is a value-level observation, not proof of evidence-grounded reasoning.
- All 17 qualified reversed runs initially leave earlier unknown. The premature
  commitment pattern in the supplied older findings note does not recur here.
- All 14 initially correct recent values remain correct, but their correct B
  citations are replaced by A. Value preservation is 14/14; expressed support
  preservation is 0/14 on those conditional opportunities.
- Fourteen first chronological requests disagree about the same claim. Every
  disagreement is unknown versus a binary answer; none is yes versus no.
- HB01 and HB06 have correct joint values but fail both sequential finals.
  HA08 alone has correct joint/chronological finals and a wrong reversed final;
  its earlier label is unresolved, so this is an uncertainty-maintenance case.
- A fixed no-video answer-schedule rule achieves 31/34 final state fields and
  14/17 final pairs. The present label distribution therefore cannot establish
  visual evidence use from value scores alone.

The current data do not isolate internal forgetting, perception failure,
arrival-recency bias, model-capacity limits or a numerical backend problem.
They do not yet test natural same-event matching, concurrent live tasks or
downstream action propagation.

## 5. Taxonomy work completed

The [taxonomy ledger](experiments/holoassist_20/belief_revision_v1/taxonomy/FINDINGS.md)
reconciles exactly with the archived scorer while adding a deduplicated view.

- 170 scored field observations repeat 34 capture-time claims.
- Collapsing same-request aliases gives 153 qualified claim/request checks:
  105 correct and 48 problematic.
- The 48 primary problems partition into 21 known-state abstentions, eight
  opposite binary values, five commitments on unsettled evidence and 14 certainty
  disagreements. Citation and transition facets are not added to this count.
- Data blockers are separated: HA05/HA09 target-identity or occurrence ambiguity;
  HA10 task/positive-window mismatch. Unsettled endpoints remain a legitimate
  uncertainty test, not automatically a dataset defect.
- The [gap register](experiments/holoassist_20/belief_revision_v1/taxonomy/GAPS.md)
  separates data, design, interface and measurement properties from seven
  unisolated model hypotheses and a prioritized experimental backlog.
- Twenty-one taxonomy boundary tests pass, including exclusivity, alias
  deduplication, incorrect priors, exclusions and preservation of values with
  loss of citations. Generated annotations include input hashes and raw pointers.

These counts are repeated observations from a small pilot, not independent
failure events or population reliability estimates. The taxonomy is an analysis
instrument, not new model measurements.

## 6. Earlier work and its disposition

| Work | Recorded outcome | How to use it now |
|---|---|---|
| [Corrected direct-revision pilot](experiments/evidence_revision_pilot/direct_revision/RESULTS.md) | Qwen2-VL-2B; six controlled views across three sources; 27 unique main requests; visual updates 0/6, joint matching 2/6 | Generic multimodal/structured-update diagnostic; not a streaming-specific finding. Earlier cached-feature results were invalidated. |
| [Fixed two-source prototype](experiments/fixed_hypothesis/FINDINGS.md) | Ten planned conditions answered; camera association fails jointly; printer joint/update discrepancy | Exploratory evidence association/history effects; neither case passes every clean qualification gate. Proposed repeats were not completed. |
| [Two-clip experiment](experiments/two_clip_diagnostic/RESULTS.md) | Five hosted calls; all three final conditions correct | Retain as a successful-update control; do not select it out because it succeeds. |
| [Intervening-footage experiment](experiments/intervening_video/RESULTS.md) | Nine answers and two preserved service errors; historical field wrong in every matched condition | Does not isolate delayed arrival; partial report is superseded by completed results. |
| [Endpoint format controls](experiments/format_controls/RESULTS.md) | Six hosted image/video answers match screened labels | Controls for those specific endpoints, not general time grounding or natural event attribution. |
| [Original source suitability audit](experiments/source_suitability/README.md) | Three sources screened; no fully qualified natural original-event reveal pair in that audit | A source/admission result; it does not mean the datasets contain no useful examples. |
| [Replay candidate diagnostic](experiments/replay_candidates/RESULTS.md) | One NBA prefix answer; later/joint/update requests failed at service level | Inconclusive; independent episode qualification and successful controls missing. |
| [25-video QA prototype](experiments/hf_hard_prototype/README.md) | Saved SmolVLM-256M results: joint 8/25, chronological 8/25, reversed 9/25 | Legacy sparse-video QA, not the Qwen3B run or an admitted retrospective-event suite. |
| [7B/72B-labelled reports](experiments/qwen_benchmarks/README.md) | All four reports record MockAgent(oracle) in their actual episode metadata | Simulations only; not measured Qwen 7B/72B results. Original bytes remain preserved. |
| [Gate diagnostic](experiments/disentanglement_proof/README.md) | Small-model perception and joint controls fail | Upstream control failures block an isolated revision claim; the directory name is not evidence of proof. |
| Suite outputs in `experiments/suite_results/` | Saved mock oracle/no-revision environment checks | Software harness validation, not model capability results. |
| Earlier streaming trial | Recovered partial run; lost outputs not reconstructed | Historical incomplete evidence; never pool with completed paired runs. |

These experiments differ in model, input type, conditions and annotation quality.
There is no defensible single pooled accuracy or overall model-call total across
all of them. The generic harness's legacy revision fields are not interchangeable
with the audited 20-video scorer or new taxonomy.

## 7. Coverage of the active questions

| Question | Current support | Missing decisive work |
|---|---|---|
| Historical knowledge revision | Operational value/update measurements and exploratory controlled reveal cases | Balanced, independently labelled episodes with confirmations, contradictions, refinements and unresolved evidence |
| Evidence-to-event attribution | Packet/time attribution errors and controlled image-association examples | Natural same-occurrence versus similar-new-event and unrelated/unresolvable contrasts |
| Preservation/current-state continuity | Conditional state and citation-retention diagnostics | Multiple protected claims, intervening events and concurrent live-state monitoring |
| Method/budget comparison | Rerun and analysis infrastructure | Matched-information flat-ledger, retained-history and graph-memory experiments |
| Optional decision propagation | Research design only | Explicit decision dependencies and actual decision outputs |

## 8. What to do before scaling

1. Independently adjudicate existing ambiguous/unsettled labels and inspect the
   actual evaluated pixels. Preserve old versions when labels change.
2. Start a candidate funnel using the [admission protocol](docs/DATASET_EXPANSION.md)
   and [episode template](datasets/candidate.template.json). Admit evidence pairs,
   not dataset names or generic hard QA videos.
3. Balance same-event/new-event/unrelated/unresolvable links and evidence effects,
   alongside nontrivial endpoint-label baselines. Keep natural reveals and
   constructed delayed delivery in separately reported tracks.
4. Fix primary outcomes and source-level splits before model-based selection.
   Keep successes and negative controls under identical admission criteria.
5. Run atomic perception/claim-address controls and oracle-prior versus predicted
   memory diagnostics before assigning an update mechanism.
6. Compare plain response memory, retained history and model-built graph/ledger
   memory at matched information/budgets. Keep gold graphs evaluator-only.
7. Expand only after qualifying yield, label agreement and reproducible effects
   support the intended question. New-source novelty and model-size claims require
   separate evidence; the older literature notes are not a current novelty audit.

## 9. Repository cleanup and navigation

- Root entry points are README, this state document and the active research questions.
- Four previous research documents are preserved verbatim under `docs/history/`;
  three old root filenames remain compatibility links.
- Four older standalone utilities moved to `scripts/legacy/`; their dataset/output
  directories remain stable, with repository-root resolution adjusted where needed.
- The generic Qwen harness now requires explicit backend selection, records actual
  agent identity and keeps default mock outputs separate from model-labelled reports.
- Historical reports, invalidation records, source material and frozen experimental
  hashes are retained. No source movies, weights or private configuration were deleted.
- Local scratch and recovery directories are ignored. The tracked exact-input
  bundle remains intentional; the existing 25-video assets remain historical data.

## 10. Verification entry points

These checks require no model download or paid inference:

Cleanup verification: eight environment/provenance tests, 17 archived-experiment
helper/scorer tests and 21 taxonomy tests pass (46 total); the saved-artifact
audit passes. Exact frozen run
hashes and historical document snapshots are checked separately. The default
audit does not re-read source movie bytes; use the documented media options for
that check.

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m unittest discover -s experiments/holoassist_20/belief_revision_v1 -p 'test_*.py'
python3 -m unittest discover -s experiments/holoassist_20/belief_revision_v1/taxonomy -p 'test_*.py'
python3 experiments/holoassist_20/belief_revision_v1/audit.py
python3 experiments/holoassist_20/belief_revision_v1/taxonomy/build_taxonomy.py
```

Use the experiment README for media verification/restoration and the CUDA guide
for a new measured run. New results must use a new output directory, explicit
model/backend metadata, exact inputs and their own execution manifest.
