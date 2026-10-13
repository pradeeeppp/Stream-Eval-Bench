"""Use case registry and built-in streaming benchmark tasks."""

from stream_eval.usecases.registry import (
    UseCase,
    register_usecase,
    get_usecase,
    list_usecases,
)
import stream_eval.usecases.table_assembly
import stream_eval.usecases.table_components
import stream_eval.usecases.camera_detachment
import stream_eval.usecases.camera_mount
import stream_eval.usecases.printer_operations

__all__ = [
    "UseCase",
    "register_usecase",
    "get_usecase",
    "list_usecases",
]
