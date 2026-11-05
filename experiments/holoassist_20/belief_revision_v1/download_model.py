"""Download the requested official checkpoint and pin its resolved revision."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE.parent / '.model_cache'
os.environ['HF_HOME'] = str(CACHE / 'hf_home')
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
from huggingface_hub import HfApi, snapshot_download

MODEL_ID = 'Qwen/Qwen2.5-VL-3B-Instruct'


def main():
    manifest_path = HERE / 'model_manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        revision = manifest['revision']
    else:
        info = HfApi(token=False).model_info(MODEL_ID)
        revision = info.sha
        manifest = {'model_id': MODEL_ID, 'revision': revision,
                    'requested_model': 'Qwen2.5-VL-3B, matching the supplied PDF',
                    'download_started_utc': datetime.now(timezone.utc).isoformat(),
                    'weights': 'official unquantized checkpoint', 'status': 'downloading'}
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Downloading {MODEL_ID} at revision {revision}', flush=True)
    path = snapshot_download(MODEL_ID, revision=revision, token=False,
                             local_dir=CACHE / 'qwen2_5_vl_3b', max_workers=4,
                             allow_patterns=['*.safetensors', '*.json', '*.txt', '*.model',
                                             '*.jinja', 'README.md'])
    manifest.update(status='download_complete', local_path=str(Path(path).resolve()),
                    download_completed_utc=datetime.now(timezone.utc).isoformat())
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print('Official checkpoint download complete.', flush=True)


if __name__ == '__main__':
    main()
