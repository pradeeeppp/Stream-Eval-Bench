# Third-party provenance

The original repository MIT license applies to original project code; it does not grant rights to third-party source videos, derived frames, model artifacts, or reference app code.

## Data samples

The original pilots' PNG frames and small MP4 packets derive from three HoloAssist sessions redistributed through `lmms-lab/EgoIT-99K`, pinned revision `a57f1f2078a7b01ea87014050fdb3afe169e54f1`. Dataset permissions and conditions remain those of the original providers. Consult their terms before further redistribution or use. This repository does not claim ownership of the source recordings.

- Source redistribution: https://huggingface.co/datasets/lmms-lab/EgoIT-99K/tree/a57f1f2078a7b01ea87014050fdb3afe169e54f1/HoloAssist
- Exact session URLs, timestamps, hashes, and acquisition records are preserved under `experiments/evidence_revision_pilot/`.
- Full HoloAssist source recordings are downloaded on demand rather than included. Model weights are not included.

## Twenty-video HoloAssist diagnostic

The current source register is `experiments/holoassist_20/online_pilot_v0/sources.json`.
The tracked `experiments/holoassist_20/data/holoassist20-inputs.tar.gz` contains
160 evaluated JPEG frames and 20 contact sheets, with recorded hashes. Source
movies remain ignored. Dataset-specific attribution and the publisher-specified
data license are retained in `experiments/holoassist_20/online_pilot_v0/ATTRIBUTION.md`
and `experiments/holoassist_20/data/LICENSE-CDLA-Permissive-2.0.txt`.
The mirrored source bytes have not been compared with the official archive.

## Legacy MV-Bench-mini selection

The older `experiments/hf_hard_prototype/videos/` contains 25 tracked video files;
they are separate from the HoloAssist input bundle. The acquisition code references
`firstep-ai/MV-Bench-mini`; its historical manifest does not pin a source revision
or record content hashes. This cleanup preserves that material and does not
establish a new rights audit or retrospective-revision qualification for it.
See the experiment README and `scripts/legacy/README.md` for its recorded scope.

## Reference hosted application

`experiments/evidence_revision_pilot/streaming_trial/hosted/app.py` and its original `README.md` are copied reference material from Qwen's public demo, **not original project code**:

- https://huggingface.co/spaces/Qwen/Qwen3-VL-235B-A22B-Instruct-Demo/tree/eb7f245e2c0d3b573dd8ed6addca9b7f6af26847
- The upstream card declares Apache-2.0. Preserve upstream attribution and applicable license conditions.
- The app is retained to document the service interface and declared backend used during the experiment; live deployment behavior may differ.
