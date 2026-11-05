# Reviewed evidence graphs for all 20 HoloAssist pilot videos

The [improvement plan](../PLAN.md) has been executed for all 20 sources. Start
with [the per-video status and findings](STATUS.md), then follow each video link
to its review, evidence anchors and diagram.

The review contains **20 typed graphs, 104 native evidence anchors, 223 verified
packet/source mappings and 1,491 unique inspected frames in the batch manifests**.
HA01 also cites the earlier detailed DSLR review. Whole-clip overview sampling
is approximately every five seconds; candidate intervals are approximately every
half second, followed by local consecutive native-frame inspection and inspection
of actual supplied frame selections. Exact reviewed indices and image hashes are
recorded rather than claiming exhaustive native-rate review of all 54 minutes.

**17 original tasks have provisional visual support; three require task-definition
adjudication (HA05, HA09 and HA10).** This is one assistant review, not independent
annotation or publication-ready ground truth. No model calls were made.

## What changed

- Separate entities, observations, supported state claims, event occurrences and
  alert decisions. Link claims to actual frames and use named edge relations.
- Store decoded frame index and actual source PTS alongside legacy packet labels.
  `fps=1` output-grid seconds differ from the source PTS of the selected frame.
- Distinguish a conservative positive anchor from exact onset, earliest detectable
  evidence and first occurrence. None of those stronger claims is certified here.
- Keep later corroboration out of earlier alert dependencies. Decisions use a
  visually reviewed supplied packet, not arbitrary native frames unavailable to
  the model.
- Preserve historical occurrences when current state changes. Separate cap
  removal from lens detachment and the two hardware-bin reaches. Later cabinet
  reopenings are recorded as candidates rather than exhaustively verified events.
- Block the reviewed decision on unresolved original task definitions rather than
  forcing a target relation that the imagery does not establish.

The original public/private tasks, source register and legacy three-node graphs
are byte-for-byte unchanged. `baseline_hashes.json` records that check. The old
scorer does not consume the reviewed graphs; inherited deadlines remain policy
choices, not video-derived timing ground truth.

## Important findings

- **HA05:** washer-bin entry is already visible in packet 29; the later screw-bin
  entry is different. The broad original wording could admit both, while packet
  29 is an early false alarm under legacy scoring.
- **HA09:** the ringed face called the underside in the legacy positive is already
  visible earlier. Face identity and the intended reveal need clarification.
- **HA10:** the legacy interval shows the cart and baskets tilting together;
  basket motion relative to an upright frame is not established.
- **HB01:** a loose belt is visible clear of the pulley route in reviewed packet
  41, preceding the legacy pre-event checkpoint at 47 and positive label at 52.
- **HB06 / HB10:** reviewed positive packets are 77 / 27, compared with legacy
  positive labels 85 / 33. These are earlier supported observations, not certified
  earliest-event labels. The faucet task requires actual visible water flow.

## Files and schema

`evidence_graphs.reviewed.jsonl` holds one complete graph per task. The identical
per-video JSON is stored in `HA01/evidence_graph.json`, etc. `review_index.json`
is the compact machine-readable index. `annotations.json` contains the visual
review inputs; `build.py` creates the graphs, reports and status index.

Each v2 graph has `source`, `review`, `entities`, `nodes`, `edges`, `timing` and
`task_proposal`. Observation roles distinguish pre-event/context evidence,
transitions, positive anchors, corroboration, later states and distractors.
`event_1.supports_original_task` and `task_proposal.qualification` separate the
observed relation from its qualification under the original instruction.
`alert_1.evidence_dependencies` contains the supplied stream observation.

For an unresolved task, the supplied packet supports a reviewed observation or
alternative event; it is not automatically positive for the original target.
Typed secondary events distinguish confirmed different occurrences from coarse
overview candidates. No temporal edge is a causal-mechanism claim.

## Reproduce and verify

Python 3, FFmpeg and FFprobe are required; all scripts use the Python standard
library. Source MP4s and original stream frames must first be present using the
pilot's `prepare_media.py`. Media remain in ignored `full_review/` directories.
Graph annotations and scripts contain no bundled videos or extracted frames.

From this directory:

```bash
# Reproduce exactly the contact sheets named in the published graph manifests.
python3 rehydrate.py

# Independently recompute native/packet decoded-frame matches and check that
# sampled JPEGs reproduce the actual supplied model inputs byte-for-byte.
python3 verify_timing.py

# Check source hashes, references, inspected-anchor membership, PTS, causal
# availability, complete coverage and baseline preservation; extract anchors.
python3 validate.py

# Exercise integrity guards, including future evidence and unresolved tasks.
python3 test_validation.py

# The original 20-video pilot validator must continue to pass.
python3 ../../validate.py
```

`rehydrate.py HA01` and `verify_timing.py HA01` support selected sources. Hash
checks intentionally enforce exact reviewed pixels and exact supplied JPEGs;
codec/encoder differences may require reproducing the original FFmpeg version.
`validation_report.json` records the completed local checks. Structural checks
and hashes do not independently establish the truth of a visual annotation.

To change annotations, inspect new evidence, update `annotations.json` and the
inspection records, run `build.py`, then run timing/graph checks. `review_media.py`
prepares new sheets with a pending-inspection status; preparation alone does not
mark them reviewed. Do not regenerate an authoritative review from uninspected
material.

Independent annotators, adjudicated boundaries, deadline justification and a
versioned scorer migration remain subsequent research steps.
