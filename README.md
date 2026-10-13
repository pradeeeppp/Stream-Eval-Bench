# Stream-Eval-Bench

Research prototype for evaluating historical-evidence updates in streaming video understanding. Intended research direction: CVPR. This repository does **not** establish a novel streaming-specific failure or contain a finished benchmark.

## Streaming Agent Environment (`stream_eval`)

The repository includes a modular, extensible **Agent Environment** for running streaming video evaluation experiments.

### Key Architecture:
- **`StreamingEnvironment`**: Simulates live video streams step-by-step with arrival watermarking (`latest_capture_boundary`) and state memory management.
- **Schedules (`DeliverySchedule`)**:
  - `chronological`: Packets arrive strictly ordered by capture time ($t_1 \to t_2 \to \dots$).
  - `delayed`: Simulates out-of-order / network latency ($t_2 \to t_1$), isolating whether late-arriving past evidence causes historical updates without corrupting current state.
  - `together`: Batch control where all evidence arrives simultaneously.
  - `drop`: Simulates network packet loss.
- **Pluggable Agent Backends (`BaseStreamingAgent`)**:
  - `MockAgent`: Fast deterministic baselines (`oracle`, `recency_bias`, `no_revision`, `intermediate_error`).
  - `VLMStreamingAgent`: Connects to Gradio spaces (Qwen3-VL demo), local HuggingFace models (`Qwen2.5-VL`, `Qwen3-VL`), or OpenAI-compatible vision endpoints.
- **Evaluation Metrics (`StreamEvaluator`)**:
  - **Historical Update Accuracy**: Did late-arriving past evidence update unobserved fields to ground truth?
  - **Recency Preservation Rate**: Was latest capture-time state preserved when older footage arrived?
  - **Trajectory Fidelity**: Step-by-step state adherence across the entire episode.
  - **JSON Schema Adherence & Timing**.

### Quick Start:

```bash
# Install package
pip install -e .

# Run all conditions on the table assembly task with an oracle agent
stream-eval --usecase table_assembly_tray --condition all --agent mock-oracle

# Test a simulated failure mode (e.g. failure to revise history)
stream-eval --usecase table_assembly_tray --condition delayed --agent mock-no-revision

# Run multi-packet camera part detachment sequence
stream-eval --usecase camera_detachment --condition all --agent mock-oracle

# Run Python quickstart tutorial
python examples/quickstart_experiment.py
```

## Start here

| Directory | Contents | Status |
|---|---|---|
| `experiments/two_clip_diagnostic/` | Five-call arrival-order test, exact MP4 inputs, prompts, responses, protocol, and runnable script | Complete; all three final conditions correct; one intermediate chronological error |
| `experiments/evidence_revision_pilot/direct_revision/` | Corrected controlled still-image evaluation, inputs, model manifest, diagnostics, tests, and results | Complete saved pilot; not a streaming-specific finding |
| `experiments/evidence_revision_pilot/streaming_trial/` | Earlier sampled-video protocol, preparation scripts, local/hosted runners, and saved partial outputs | Historical incomplete attempt; do not treat as a completed paired evaluation |
| `experiments/evidence_revision_pilot/` | Initial acquisition scripts, source metadata, provenance, baseline code, and historical logs | Earlier exploratory work; see corrected pilot for authoritative image-update results |

Read [latest results](experiments/two_clip_diagnostic/RESULTS.md) and [protocol](experiments/two_clip_diagnostic/README.md). The latest experiment used a public demo declaring Qwen3-VL-235B-A22B-Instruct. With supplied capture times and explicit instructions, it correctly updated the past while preserving the latest state in one two-clip example. No population-level reliability or novelty claim follows.

## Run the latest diagnostic

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r experiments/two_clip_diagnostic/requirements.txt
python experiments/two_clip_diagnostic/run.py
```

The runner resumes existing results, which are already complete in this checkout. For a fresh run, copy the diagnostic directory to a separate location and remove **that copy's** `results.json` and `experiment_record.json`, if present. Invoke the script five times; each invocation executes one pending call. Retain the published results unchanged. Hosted service availability and decoding settings are not controlled.

The local image pilot has separate pinned dependencies and reproduction instructions in its README. Do not assume the older Qwen2-VL and newer Qwen3-VL runners share a compatible environment.

## Research integrity

- `direct_revision/results/invalidated_cached/` is retained as an audit trail only. Those runs used an invalid feature-caching optimization and must not be pooled with corrected results.
- The earlier streaming directory is a recovered partial checkpoint. Later unsaved runs were lost and are not reconstructed here.
- Sampled four-frame packets are not equivalent to continuous livestream evaluation. Replay detection, event association, and long-stream performance remain untested in the completed two-clip experiment.
- No model weights, generated tensor caches, Python caches, credentials, or duplicate recovery bundles are committed.

See [third-party provenance](THIRD_PARTY.md). The repository's MIT license does not relicense third-party dataset material or copied reference code.
