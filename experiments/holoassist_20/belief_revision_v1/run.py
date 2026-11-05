"""Resume an auditable 100-request local Qwen2.5-VL-3B diagnostic."""
import argparse
import importlib.metadata
import json
import os
import random
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('HF_HUB_DISABLE_IMPLICIT_TOKEN', '1')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

from protocol import CONFIG, HERE, PHASES, digest, prompt_for, score_episode


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


class Backend:
    def __init__(self, model_path, device):
        import torch
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
        self.torch, self.device = torch, device
        torch.manual_seed(CONFIG['seed'])
        if device == 'mps' and not torch.backends.mps.is_available():
            raise RuntimeError('Apple GPU is unavailable in this process; use the approved GPU execution context.')
        self.processor = AutoProcessor.from_pretrained(model_path, local_files_only=True, use_fast=False)
        self.processor.video_processor.size = {'shortest_edge': CONFIG['min_pixels_per_frame'],
                                               'longest_edge': CONFIG['max_pixels_per_frame']}
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_path, local_files_only=True, dtype=torch.float16,
            device_map={'': device}, low_cpu_mem_usage=True,
            attn_implementation=CONFIG['attention']).eval()

    def generate(self, prompt, videos, fps):
        torch = self.torch
        messages = [{'role': 'user', 'content':
                     [{'type': 'video'} for _ in videos] + [{'type': 'text', 'text': prompt}]}]
        rendered = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[rendered], videos=videos, fps=fps, do_sample_frames=False,
                                return_tensors='pt')
        inputs = inputs.to(self.device)
        if 'pixel_values_videos' in inputs:
            inputs['pixel_values_videos'] = inputs['pixel_values_videos'].to(dtype=self.model.dtype)
        if self.device == 'mps':
            torch.mps.synchronize()
        started = time.perf_counter()
        with torch.inference_mode():
            result = self.model.generate(**inputs, max_new_tokens=CONFIG['max_new_tokens'],
                                         do_sample=False, num_beams=1, use_cache=True)
        if self.device == 'mps':
            torch.mps.synchronize()
        generated = result[:, inputs['input_ids'].shape[1]:]
        response = self.processor.batch_decode(generated, skip_special_tokens=True,
                                               clean_up_tokenization_spaces=False)[0].strip()
        metadata = {'generation_seconds': time.perf_counter() - started,
                    'input_tokens': int(inputs['input_ids'].shape[1]),
                    'generated_tokens': int(generated.shape[1]),
                    'video_grid_thw': inputs['video_grid_thw'].cpu().tolist(),
                    'second_per_grid_ts': inputs.get('second_per_grid_ts'),
                    'rendered_prompt_sha256': __import__('hashlib').sha256(rendered.encode()).hexdigest()}
        if isinstance(metadata['second_per_grid_ts'], torch.Tensor):
            metadata['second_per_grid_ts'] = metadata['second_per_grid_ts'].cpu().tolist()
        del inputs, result, generated
        if self.device == 'mps':
            torch.mps.empty_cache()
        return response, metadata


def packet_inputs(case, phase):
    import numpy as np
    from PIL import Image
    videos, rates, hashes = [], [], []
    for packet_id in PHASES[phase]['current']:
        packet = case['packets'][packet_id]
        frames = []
        for frame in packet['frames']:
            path = HERE / frame['path']
            if digest(path) != frame['sha256']:
                raise ValueError(f'Input changed: {path}')
            frames.append(np.asarray(Image.open(path).convert('RGB')))
            hashes.append({'packet_id': packet_id, **frame})
        videos.append(np.stack(frames))
        rates.append(packet['sampled_fps'])
    return videos, rates, hashes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', choices=['mps', 'cpu'], default='mps')
    parser.add_argument('--cases', nargs='*')
    parser.add_argument('--max-calls', type=int)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    model_info = json.loads((HERE / 'model_manifest.json').read_text())
    if model_info['status'] != 'download_complete':
        raise RuntimeError('Checkpoint download is not complete.')
    cases = json.loads((HERE / 'cases.json').read_text())
    if len(cases) != 20 or any(c['packet_visual_review'] != 'reviewed_by_codex_2026_11_04' for c in cases):
        raise RuntimeError('The complete fixed packet set has not passed visual review.')
    signatures = {'cases_sha256': digest(HERE / 'cases.json'),
                  'protocol_sha256': digest(HERE / 'protocol.py'),
                  'runner_sha256': digest(HERE / 'run.py'), 'model_revision': model_info['revision'],
                  'device': args.device, 'config': CONFIG}
    manifest_path = HERE / 'execution_manifest.json'
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text())
        if existing['signatures'] != signatures:
            raise RuntimeError('Execution configuration changed. Archive the existing experiment before a new run.')
    else:
        packages = {name: importlib.metadata.version(name) for name in
                    ['torch', 'torchvision', 'transformers', 'accelerate', 'Pillow', 'numpy', 'safetensors']}
        save(manifest_path, {'started_utc': utc(), 'signatures': signatures, 'packages': packages,
                             'mps_cpu_fallback_enabled': True, 'official_model': model_info,
                             'benchmark_requests_planned': 100, 'independent_annotation': False})
    print('Loading the pinned Qwen2.5-VL-3B checkpoint...', flush=True)
    backend = Backend(model_info['local_path'], args.device)
    print('Model loaded.', flush=True)
    if args.smoke:
        import numpy as np
        red = np.zeros((4, 56, 56, 3), dtype=np.uint8)
        red[:, :, :, 0] = 255
        prompt = 'What is the dominant color in this video? Answer with one word.'
        response, metadata = backend.generate(prompt, [red], [10.0])
        save(HERE / 'infrastructure_smoke.json', {'time_utc': utc(), 'prompt': prompt,
             'input': 'four constant red RGB frames, 56x56', 'raw_response': response,
             'is_benchmark_request': False, **metadata})
        print(json.dumps({'smoke_response': response, **metadata}), flush=True)
        return
    completed_now = 0
    results_dir = HERE / 'responses'
    results_dir.mkdir(exist_ok=True)
    for case in cases:
        sid = case['case_id']
        if args.cases and sid not in args.cases:
            continue
        path = results_dir / f'{sid}.json'
        record = json.loads(path.read_text()) if path.exists() else {'case_id': sid, 'steps': {}, 'created_utc': utc()}
        conditions = ['joint', 'chronological', 'delayed']
        random.Random(f"{CONFIG['seed']}:{sid}").shuffle(conditions)
        phases = []
        for condition in conditions:
            phases += ['joint'] if condition == 'joint' else [condition + '_0', condition + '_1']
        for phase in phases:
            if phase in record['steps'] and record['steps'][phase].get('status') == 'ok':
                continue
            if args.max_calls is not None and completed_now >= args.max_calls:
                print('Reached this invocation call limit; saved work can be resumed.', flush=True)
                return
            predecessor = PHASES[phase]['previous']
            previous = record['steps'][predecessor]['raw_response'] if predecessor else None
            prompt = prompt_for(case, phase, previous)
            videos, rates, frame_metadata = packet_inputs(case, phase)
            print(f'{sid} {phase}: generating...', flush=True)
            started = utc()
            try:
                response, metadata = backend.generate(prompt, videos, rates)
            except Exception as exc:
                directory = HERE / 'infrastructure_errors'
                directory.mkdir(exist_ok=True)
                error_path = directory / f"{sid}_{phase}_{time.time_ns()}.json"
                save(error_path, {'case_id': sid, 'phase': phase, 'started_utc': started,
                                  'error': repr(exc), 'traceback': traceback.format_exc(),
                                  'prompt': prompt, 'input_frames': frame_metadata})
                raise
            record['steps'][phase] = {'status': 'ok', 'started_utc': started, 'completed_utc': utc(),
                                      'phase': phase, 'current_packets': PHASES[phase]['current'],
                                      'arrived_packets': PHASES[phase]['arrived'], 'prompt': prompt,
                                      'previous_memory': previous, 'raw_response': response,
                                      'input_frames': frame_metadata, **metadata}
            record['analysis'] = score_episode(case, record['steps'])
            save(path, record)
            completed_now += 1
            print(f'{sid} {phase}: {response} ({metadata["generation_seconds"]:.1f}s)', flush=True)
    print(f'Completed {completed_now} requests in this invocation.', flush=True)


if __name__ == '__main__':
    main()
