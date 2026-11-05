# Evidence-graph improvement plan — all 20 pilot videos

Created 2026-11-02. Scope: all 20 existing source sessions and their existing
online-alert tasks. Deliver a reviewed graph for every task, a combined index,
reproducible evidence extraction and automated structural/timing validation.

## Execution order

1. **Freeze the baseline.** Record hashes of public/private tasks, legacy graphs
   and sources. Keep the previous DSLR review. Do not silently change evaluation
   labels, deadlines or published task instructions.
2. **Prepare traceable review material.** Verify each MP4 hash, enumerate decoded
   frame PTS, inspect a whole-clip overview sampled about every five seconds,
   and inspect the existing candidate interval at approximately 0.5-second steps.
   Use native-frame inspection near uncertain boundaries and higher-resolution
   anchors when small objects or occlusion require it. Record exactly what was
   inspected; sampled review is not exhaustive full-rate annotation.
3. **Review every task visually.** Identify target objects, checked pre-event
   evidence, transition/uncertainty, a conservative positive anchor, corroboration
   and relevant distractors or subsequent state changes. Search earlier sampled
   context for possible earlier occurrences; never certify first occurrence from
   sparse sampling alone. Flag unsupported object identity or event wording.
4. **Build typed graphs.** Separate entities, observations, supported state
   claims, event occurrences and alert decisions. Use typed support/temporal
   edges, stable occurrence IDs, uncertainty and evidence availability. Record
   later state changes without erasing history. Add negative examples only when
   actually observed; do not invent a distractor or a causal explanation.
5. **Verify the clocks.** Separate native source PTS from legacy 1 FPS packet
   labels. Verify relevant packet/source mappings against decoded frame hashes
   and reproduce relevant supplied JPEGs. Keep deadline provenance explicit;
   policy deadlines are not physical event boundaries. Do not let future
   corroboration become a dependency of an earlier decision.
6. **Validate and deliver.** Check all source hashes, graph references, supporting
   evidence, frame PTS, packet mappings, decision availability and complete 20-task
   coverage. Re-run the legacy validator and prove baseline files unchanged.
   Publish a per-video status/findings table and unresolved annotation issues.

## Acceptance criteria

- A reviewed graph and readable review for each of 20 tasks, even if the correct
  conclusion is that the task needs revision or its event boundary is uncertain.
- Every observation points to an exact decoded frame index and source PTS.
- Each positive event claim has visual evidence, or is explicitly unresolved.
- Distinguish observed negative evidence from occlusion/unknown.
- Decision evidence must be available in the supplied stream at decision time.
- Independent annotation/adjudication remains outstanding and is never described
  as completed. Exact physical onset, intent, task success and causation are not
  inferred from an isolated frame.
- Revised graphs remain private annotation proposals. The legacy scorer does not
  consume them until a separately documented scoring migration is implemented.

## Progress

Execution status and video-level findings are maintained in `batch_v1/STATUS.md`.

Completed: all 20 visual reviews and graphs, 104 native anchors, 223 verified
packet mappings, per-video reports and combined index. Automated graph/timing
consistency checks and the original pilot validator pass; five integrity
regression tests pass. See `batch_v1/validation_report.json` for the audit.
Independent annotation and scoring migration remain explicitly outside this
completed assistant-review pass.
