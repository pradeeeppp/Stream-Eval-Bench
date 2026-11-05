"""Run the frozen 20-video protocol on CUDA, MPS or CPU into a fresh directory."""
import argparse
import importlib.metadata
import json
import os
import platform
import random
import shutil
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('HF_HUB_DISABLE_IMPLICIT_TOKEN', '1')

from input_bundle import verify_inputs
from protocol import CONFIG, HERE, PHASES, digest, prompt_for, score_episode


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def select_device(requested, torch):
    if requested == 'auto':
        requested = 'cuda:0' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
    device = torch.device(requested)
    if device.type == 'cuda':
        if not torch.cuda.is_available() or (device.index or 0) >= torch.cuda.device_count():
            raise ValueError('Requested CUDA device is unavailable; check the installed PyTorch CUDA build')
    elif device.type == 'mps':
        if not torch.backends.mps.is_available():
            raise ValueError('Requested MPS device is unavailable')
    elif device.type != 'cpu':
        raise ValueError('Supported devices: cuda[:N], mps, cpu or auto')
    return str(device)


def signatures(cases_path, revision, device, device_map, environment):
    return {'cases_sha256': digest(cases_path), 'protocol_sha256': digest(HERE / 'protocol.py'),
            'runner_sha256': digest(Path(__file__)), 'model_revision': revision,
            'device': device, 'device_map': device_map, 'config': CONFIG,
            'environment': environment}


def initialize_run(destination, signature, model_info, input_root=HERE):
    destination = destination.resolve()
    baseline = HERE.resolve()
    runs_root = baseline.parent / 'runs'
    if destination == runs_root or runs_root not in destination.parents:
        raise ValueError(f'Run directories must be beneath {runs_root}; baseline outputs cannot be overwritten')
    manifest_path = destination / 'execution_manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest['signatures'] != signature:
            raise ValueError('Run configuration, code or environment changed; choose a new --run-dir')
        if digest(destination / 'cases.json') != signature['cases_sha256']:
            raise ValueError('Saved case manifest changed')
        for key, filename in [('protocol_sha256', 'protocol.py'), ('runner_sha256', 'runner.py')]:
            if digest(destination / 'code' / filename) != signature[key]:
                raise ValueError('Recorded code snapshot changed')
        return manifest
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Output directory is nonempty and has no execution manifest')
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'code').mkdir()
    (destination / 'responses').mkdir()
    shutil.copyfile(HERE / 'cases.json', destination / 'cases.json')
    shutil.copyfile(HERE / 'protocol.py', destination / 'code/protocol.py')
    shutil.copyfile(Path(__file__), destination / 'code/runner.py')
    save(destination / 'model_manifest.json', model_info)
    manifest = {'started_utc': utc(), 'signatures': signature,
                'input_root': str(input_root.resolve()),
                'code_paths': {'protocol_sha256': 'code/protocol.py', 'runner_sha256': 'code/runner.py'},
                'official_model': model_info, 'benchmark_requests_planned': 100,
                'independent_annotation': False, 'baseline_directory': str(HERE)}
    save(manifest_path, manifest)
    return manifest


class Backend:
    def __init__(self, model_path, device, device_map):
        import torch
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
        self.torch = torch
        torch.manual_seed(CONFIG['seed'])
        self.processor = AutoProcessor.from_pretrained(model_path, local_files_only=True, use_fast=False)
        self.processor.video_processor.size = {'shortest_edge': CONFIG['min_pixels_per_frame'],
                                               'longest_edge': CONFIG['max_pixels_per_frame']}
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_path, local_files_only=True, dtype=torch.float16,
            device_map='auto' if device_map == 'auto' else {'': device},
            low_cpu_mem_usage=True, attn_implementation=CONFIG['attention']).eval()
        self.device = str(self.model.device)
        mapping = getattr(self.model, 'hf_device_map', {'': device})
        self.placement = {name: str(value) for name, value in mapping.items()}

    def synchronize(self):
        if self.device.startswith('cuda'):
            for index in range(self.torch.cuda.device_count()):
                self.torch.cuda.synchronize(index)
        elif self.device.startswith('mps'):
            self.torch.mps.synchronize()

    def generate(self, prompt, videos, fps):
        import hashlib
        torch = self.torch
        messages = [{'role': 'user', 'content':
                     [{'type': 'video'} for _ in videos] + [{'type': 'text', 'text': prompt}]}]
        rendered = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[rendered], videos=videos, fps=fps, do_sample_frames=False,
                                return_tensors='pt').to(self.device)
        inputs['pixel_values_videos'] = inputs['pixel_values_videos'].to(dtype=self.model.dtype)
        self.synchronize()
        started = time.perf_counter()
        with torch.inference_mode():
            result = self.model.generate(**inputs, max_new_tokens=CONFIG['max_new_tokens'],
                                         do_sample=False, num_beams=1, use_cache=True)
        self.synchronize()
        generated = result[:, inputs['input_ids'].shape[1]:]
        response = self.processor.batch_decode(generated, skip_special_tokens=True,
                                               clean_up_tokenization_spaces=False)[0].strip()
        seconds = inputs.get('second_per_grid_ts')
        metadata = {'generation_seconds': time.perf_counter() - started,
                    'input_tokens': int(inputs['input_ids'].shape[1]),
                    'generated_tokens': int(generated.shape[1]),
                    'video_grid_thw': inputs['video_grid_thw'].cpu().tolist(),
                    'second_per_grid_ts': seconds.cpu().tolist() if isinstance(seconds, torch.Tensor) else seconds,
                    'rendered_prompt_sha256': hashlib.sha256(rendered.encode()).hexdigest()}
        del inputs, result, generated
        if self.device.startswith('mps'):
            torch.mps.empty_cache()
        return response, metadata


def packet_inputs(case, phase, input_root=HERE):
    import numpy as np
    from PIL import Image
    videos, rates, hashes = [], [], []
    for packet_id in PHASES[phase]['current']:
        packet = case['packets'][packet_id]
        frames = []
        for frame in packet['frames']:
            path = input_root / frame['path']
            if digest(path) != frame['sha256']:
                raise ValueError(f'Input changed: {path}')
            with Image.open(path) as image:
                frames.append(np.asarray(image.convert('RGB')))
            hashes.append({'packet_id': packet_id, **frame})
        videos.append(np.stack(frames))
        rates.append(packet['sampled_fps'])
    return videos, rates, hashes


def execute(destination, cases, backend, max_calls=None, selected=None):
    completed_now = 0
    for case in cases:
        sid = case['case_id']
        if selected and sid not in selected:
            continue
        path = destination / 'responses' / f'{sid}.json'
        record = json.loads(path.read_text()) if path.exists() else {'case_id': sid, 'steps': {}, 'created_utc': utc()}
        conditions = ['joint', 'chronological', 'delayed']
        random.Random(f"{CONFIG['seed']}:{sid}").shuffle(conditions)
        phases = [phase for condition in conditions for phase in
                  (['joint'] if condition == 'joint' else [condition + '_0', condition + '_1'])]
        for phase in phases:
            if record['steps'].get(phase, {}).get('status') == 'ok':
                continue
            if max_calls is not None and completed_now >= max_calls:
                return completed_now
            predecessor = PHASES[phase]['previous']
            previous = record['steps'][predecessor]['raw_response'] if predecessor else None
            prompt = prompt_for(case, phase, previous)
            videos, rates, frames = packet_inputs(case, phase)
            print(f'{sid} {phase}: generating...', flush=True)
            started = utc()
            try:
                response, metadata = backend.generate(prompt, videos, rates)
            except Exception as error:
                directory = destination / 'infrastructure_errors'
                directory.mkdir(exist_ok=True)
                save(directory / f'{sid}_{phase}_{time.time_ns()}.json',
                     {'case_id': sid, 'phase': phase, 'started_utc': started,
                      'error': repr(error), 'traceback': traceback.format_exc(),
                      'prompt': prompt, 'input_frames': frames})
                raise
            record['steps'][phase] = {'status': 'ok', 'started_utc': started, 'completed_utc': utc(),
                                      'phase': phase, 'current_packets': PHASES[phase]['current'],
                                      'arrived_packets': PHASES[phase]['arrived'], 'prompt': prompt,
                                      'previous_memory': previous, 'raw_response': response,
                                      'input_frames': frames, **metadata}
            record['analysis'] = score_episode(case, record['steps'])
            save(path, record)
            completed_now += 1
            print(f'{sid} {phase}: {response}', flush=True)
    return completed_now


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--device', default='auto', help='auto, cuda[:N], mps or cpu')
    parser.add_argument('--device-map', choices=['single', 'auto'], default='single')
    parser.add_argument('--cache-dir', type=Path, default=HERE.parent / '.model_cache/hub')
    parser.add_argument('--offline', action='store_true', help='Use an already cached pinned checkpoint')
    parser.add_argument('--cases', nargs='+')
    parser.add_argument('--max-calls', type=int)
    parser.add_argument('--dry-run', action='store_true', help='Validate inputs and print plan; no model or output writes')
    parser.add_argument('--smoke', action='store_true', help='Save only a separate synthetic-video infrastructure check')
    args = parser.parse_args()
    cases = json.loads((HERE / 'cases.json').read_text())
    if args.cases and set(args.cases) - {case['case_id'] for case in cases}:
        parser.error('Unknown case ID')
    if args.max_calls is not None and args.max_calls < 0:
        parser.error('--max-calls must be nonnegative')
    verify_inputs()
    if args.dry_run:
        print(json.dumps({'validated_inputs': 180, 'source_videos_needed': False,
                          'benchmark_requests_planned': 5 * len(args.cases or cases),
                          'model_revision': json.loads((HERE / 'model_manifest.json').read_text())['revision'],
                          'run_directory': str(args.run_dir.resolve()), 'device': args.device}, indent=2))
        return
    import torch
    from huggingface_hub import snapshot_download
    device = select_device(args.device, torch)
    if args.device_map == 'auto' and not device.startswith('cuda'):
        parser.error('--device-map auto is supported for CUDA only')
    package_names = ['torch', 'torchvision', 'transformers', 'accelerate', 'Pillow', 'numpy', 'safetensors']
    environment = {'packages': {name: importlib.metadata.version(name) for name in package_names},
                   'python': platform.python_version(), 'platform': platform.platform(),
                   'torch_cuda_runtime': torch.version.cuda,
                   'gpus': [{'index': index, 'name': torch.cuda.get_device_name(index),
                             'memory_bytes': torch.cuda.get_device_properties(index).total_memory}
                            for index in range(torch.cuda.device_count())]}
    original = json.loads((HERE / 'model_manifest.json').read_text())
    model_info = {key: original[key] for key in ['model_id', 'revision', 'weights']}
    model_info['status'] = 'pinned_for_rerun'
    signature = signatures(HERE / 'cases.json', original['revision'], device, args.device_map, environment)
    destination = args.run_dir.resolve()
    initialize_run(destination, signature, model_info)
    cache_path = snapshot_download(original['model_id'], revision=original['revision'],
                                   cache_dir=args.cache_dir, local_files_only=args.offline,
                                   allow_patterns=['*.safetensors', '*.json', '*.txt', '*.model', '*.jinja'])
    print(f'Loading {original["model_id"]} on {device}...', flush=True)
    backend = Backend(cache_path, device, args.device_map)
    placement_path = destination / 'model_placement.json'
    if placement_path.exists() and json.loads(placement_path.read_text()) != backend.placement:
        raise ValueError('Model placement changed; use a new run directory')
    save(placement_path, backend.placement)
    smoke_path = destination / 'infrastructure_smoke.json'
    if not smoke_path.exists():
        import numpy as np
        red = np.zeros((4, 56, 56, 3), dtype=np.uint8)
        red[:, :, :, 0] = 255
        prompt = 'What is the dominant color in this video? Answer with one word.'
        raw, metadata = backend.generate(prompt, [red], [10.0])
        save(smoke_path, {'time_utc': utc(), 'prompt': prompt, 'input': 'four constant red RGB frames, 56x56',
                          'raw_response': raw, 'is_benchmark_request': False, **metadata})
    if not args.smoke:
        count = execute(destination, cases, backend, args.max_calls, args.cases)
        print(f'Saved {count} new benchmark responses in {destination}', flush=True)
    steps = [step for path in (destination / 'responses').glob('*.json')
             for step in json.loads(path.read_text())['steps'].values()]
    save(destination / 'execution_summary.json',
         {'status': 'complete' if len(steps) == 100 else 'incomplete', 'updated_utc': utc(),
          'benchmark_requests': len(steps), 'benchmark_requests_planned': 100,
          'generation_seconds': sum(step['generation_seconds'] for step in steps),
          'generated_token_limit_hits': sum(step['generated_tokens'] == CONFIG['max_new_tokens'] for step in steps)})


if __name__ == '__main__':
    main()
