# Historical mock-labelled reports

The four existing JSON files named `Qwen2.5_VL_7B_*` and `Qwen2.5_VL_72B_*`
contain `agent_metadata.type = MockAgent` and `agent_name = MockAgent(oracle)`
in every episode. **They are oracle simulations, not measured Qwen 7B/72B results.**
Their original filenames and bytes are retained as provenance. Do not pool them
with the actual local Qwen2.5-VL-3B run or cite their scores as model capability.

The generic runner now requires explicit `--backend` selection. Mock outputs
record `evaluation_kind=mock_simulation`, `model_name=null`, the requested label
separately, and the actual agent metadata. Their default location is the ignored
`experiments/runs/mock_benchmarks/` directory, with `mock_*` filenames.

For the verified 20-video run, start with
[the archived experiment](../holoassist_20/belief_revision_v1/README.md).
For a new GPU execution, use its separate
[CUDA rerun procedure](../holoassist_20/belief_revision_v1/CUDA_RERUN.md).
