"""Streaming Agent definitions and pluggable model backends."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
import json
import pathlib
from stream_eval.core.models import Observation


class BaseStreamingAgent(ABC):
    """Abstract base class for streaming video evaluation agents."""

    def __init__(self, name: str):
        self.name = name

    def reset(self) -> None:
        """Called before each new streaming episode."""
        pass

    @abstractmethod
    def act(self, observation: Observation) -> Union[str, Dict[str, Any]]:
        """Given current observation, generate state update/response."""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Returns metadata about agent architecture, model name, and decoding parameters."""
        return {"agent_name": self.name, "type": self.__class__.__name__}


class MockAgent(BaseStreamingAgent):
    """Mock agent for deterministic simulation, offline testing, and failure mode analysis."""

    def __init__(
        self,
        mode: str = "oracle",
        preset_answers: Optional[Dict[str, Any]] = None,
        custom_stepper: Optional[Callable[[Observation], Union[str, Dict[str, Any]]]] = None,
    ):
        """
        Modes:
          - 'oracle': Returns expected ground truth state for the step.
          - 'recency_bias': Overwrites older facts with latest observation.
          - 'no_revision': Refuses to update older facts upon receiving late packets.
          - 'intermediate_error': Mimics intermediate chronological error seen in Qwen3-VL 2-clip test.
          - 'invalid_json': Emits invalid unparseable text.
          - 'custom': Uses custom_stepper function.
        """
        super().__init__(f"MockAgent({mode})")
        self.mode = mode
        self.preset_answers = preset_answers or {}
        self.custom_stepper = custom_stepper

    def act(self, observation: Observation) -> Union[str, Dict[str, Any]]:
        if self.custom_stepper:
            return self.custom_stepper(observation)

        cond = observation.metadata.get("condition", "chronological")
        step = observation.step_index
        schema_keys = list(observation.schema.keys())

        if self.mode == "oracle":
            # Check preset first
            key = f"{cond}_{step}"
            if key in self.preset_answers:
                return self.preset_answers[key]
            # Try to fetch expected from usecase directly
            uc_id = observation.metadata.get("usecase_id")
            if uc_id:
                try:
                    from stream_eval.usecases.registry import get_usecase
                    uc = get_usecase(uc_id)
                    exp = uc.get_expected_state(
                        condition=cond,
                        step_index=step,
                        arrived_packet_ids=observation.metadata.get("arrived_packet_ids", []),
                    )
                    if exp:
                        return exp
                except Exception:
                    pass
            return {k: "yes" if "latest" in k else "no" for k in schema_keys}

        elif self.mode == "recency_bias":
            # Forgets earlier facts
            return {k: "yes" if "latest" in k else "unknown" for k in schema_keys}

        elif self.mode == "no_revision":
            # If delayed, leaves earlier as unknown
            return {k: "yes" if "latest" in k else "unknown" for k in schema_keys}

        elif self.mode == "intermediate_error":
            # Chronological step 0 produces error on latest; step 1 corrects it
            if cond == "chronological" and step == 0:
                return {"earlier": "no", "latest": "yes"}  # Intermediate error
            return {"earlier": "no", "latest": "yes"}

        elif self.mode == "invalid_json":
            return "I am thinking about this video and conclude the tray is on the table."

        return {k: "unknown" for k in schema_keys}


class GradioVLMBackend:
    """Backend connecting to HuggingFace Gradio public demo spaces."""

    def __init__(
        self,
        host: str = "https://qwen-qwen3-vl-235b-a22b-instruct-demo.hf.space",
        timeout: int = 60,
    ):
        self.host = host
        self.timeout = timeout
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from gradio_client import Client
                self._client = Client(self.host, hf_token=False, httpx_kwargs={"timeout": self.timeout}, verbose=False)
            except ImportError:
                raise ImportError("Please install gradio_client: pip install gradio_client")
        return self._client

    def generate(self, observation: Observation) -> str:
        from gradio_client import handle_file
        client = self._get_client()
        client.predict(api_name="/reset_state")

        for p in observation.packets:
            if p.video_path and pathlib.Path(p.video_path).exists():
                client.predict([], handle_file(str(p.video_path)), api_name="/add_file")
            elif p.frames:
                for f in p.frames:
                    if pathlib.Path(f).exists():
                        client.predict([], handle_file(str(f)), api_name="/add_file")

        prompt = observation.formatted_prompt()
        history = client.predict([], prompt, api_name="/add_text")
        reply = client.predict(history, api_name="/predict")
        response = reply[-1][1]
        return response


class LocalHuggingFaceBackend:
    """Backend using local PyTorch / Transformers model for vision-language generation."""

    def __init__(
        self,
        model_name_or_path: str = "Qwen/Qwen2.5-VL-7B-Instruct",
        device: str = "cpu",
        dtype: str = "bfloat16",
        max_new_tokens: int = 256,
    ):
        self.model_name_or_path = model_name_or_path
        self.device = device
        self.dtype = dtype
        self.max_new_tokens = max_new_tokens
        self._model = None
        self._processor = None

    def _load(self):
        if self._model is not None:
            return
        import torch
        from transformers import AutoProcessor, AutoModelForImageTextToText

        target_dtype = getattr(torch, self.dtype, torch.float32)
        self._processor = AutoProcessor.from_pretrained(self.model_name_or_path)
        self._model = AutoModelForImageTextToText.from_pretrained(
            self.model_name_or_path,
            torch_dtype=target_dtype,
            device_map=self.device,
        ).eval()

    def generate(self, observation: Observation) -> str:
        self._load()
        from PIL import Image

        prompt = observation.formatted_prompt()
        images = []
        for p in observation.packets:
            for f in p.frames:
                p_path = pathlib.Path(f)
                if p_path.exists():
                    images.append(Image.open(p_path).convert("RGB"))

        content = []
        for _ in images:
            content.append({"type": "image"})
        content.append({"type": "text", "text": prompt})

        messages = [{"role": "user", "content": content}]
        text_prompt = self._processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self._processor(text=[text_prompt], images=images if images else None, return_tensors="pt").to(self.device)

        import torch
        with torch.no_grad():
            generated_ids = self._model.generate(**inputs, max_new_tokens=self.max_new_tokens, do_sample=False)
        output_text = self._processor.batch_decode(
            generated_ids[:, inputs.input_ids.shape[1]:],
            skip_special_tokens=True,
        )[0]
        return output_text


class OpenAICompatibleBackend:
    """Backend connecting to OpenAI-compatible vision APIs (vLLM, Ollama, OpenAI, Azure)."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "dummy",
        model: str = "qwen-vl",
        temperature: float = 0.0,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        return self._client

    def generate(self, observation: Observation) -> str:
        import base64
        client = self._get_client()

        user_content: List[Dict[str, Any]] = []
        for p in observation.packets:
            for f in p.frames:
                path = pathlib.Path(f)
                if path.exists():
                    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    })

        user_content.append({"type": "text", "text": observation.formatted_prompt()})

        res = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": user_content}],
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )
        return res.choices[0].message.content or "{}"


class VLMStreamingAgent(BaseStreamingAgent):
    """General Vision-Language Model agent supporting multiple backends."""

    def __init__(
        self,
        name: str = "VLMStreamingAgent",
        backend: Optional[Union[GradioVLMBackend, LocalHuggingFaceBackend, OpenAICompatibleBackend, Callable]] = None,
    ):
        super().__init__(name)
        self.backend = backend

    def act(self, observation: Observation) -> str:
        if self.backend is None:
            raise ValueError("No backend configured for VLMStreamingAgent.")
        if hasattr(self.backend, "generate"):
            return self.backend.generate(observation)
        elif callable(self.backend):
            return self.backend(observation)
        else:
            raise TypeError(f"Unsupported backend: {type(self.backend)}")

    def get_metadata(self) -> Dict[str, Any]:
        meta = super().get_metadata()
        if hasattr(self.backend, "__class__"):
            meta["backend_type"] = self.backend.__class__.__name__
        if hasattr(self.backend, "host"):
            meta["host"] = self.backend.host
        if hasattr(self.backend, "model_name_or_path"):
            meta["model"] = self.backend.model_name_or_path
        return meta
