"""Stream-Eval-Bench: Evaluation environment for streaming video agents."""

__version__ = "0.2.0"

from stream_eval.core import (
    VideoPacket,
    Observation,
    StepResult,
    EpisodeResult,
    DeliverySchedule,
    ChronologicalSchedule,
    DelayedSchedule,
    TogetherSchedule,
    DropSchedule,
    StreamingEnvironment,
    BaseStreamingAgent,
    MockAgent,
    VLMStreamingAgent,
    GradioVLMBackend,
    LocalHuggingFaceBackend,
    OpenAICompatibleBackend,
    StreamEvaluator,
)
from stream_eval.usecases import (
    UseCase,
    get_usecase,
    list_usecases,
    register_usecase,
)

__all__ = [
    "VideoPacket",
    "Observation",
    "StepResult",
    "EpisodeResult",
    "DeliverySchedule",
    "ChronologicalSchedule",
    "DelayedSchedule",
    "TogetherSchedule",
    "DropSchedule",
    "StreamingEnvironment",
    "BaseStreamingAgent",
    "MockAgent",
    "VLMStreamingAgent",
    "GradioVLMBackend",
    "LocalHuggingFaceBackend",
    "OpenAICompatibleBackend",
    "StreamEvaluator",
    "UseCase",
    "get_usecase",
    "list_usecases",
    "register_usecase",
]
