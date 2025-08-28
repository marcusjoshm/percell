from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, DefaultDict, Dict, List, Type, TypeVar
from collections import defaultdict


@dataclass
class PipelineEvent:
    """Base class for pipeline events."""
    pass


E = TypeVar("E", bound=PipelineEvent)


class PipelineEventBus:
    """Simple synchronous publish/subscribe bus for pipeline events."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[Type[PipelineEvent], List[Callable[[PipelineEvent], None]]] = defaultdict(list)

    def subscribe(self, event_type: Type[E], handler: Callable[[E], None]) -> None:
        self._subscribers[event_type].append(handler)  # type: ignore[arg-type]

    def unsubscribe(self, event_type: Type[E], handler: Callable[[E], None]) -> None:
        handlers = self._subscribers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: PipelineEvent) -> None:
        for handler in list(self._subscribers.get(type(event), [])):
            try:
                handler(event)
            except Exception:
                # Intentionally swallow to avoid breaking the pipeline on handler errors
                pass


# Example events that stages may publish
@dataclass
class StageStarted(PipelineEvent):
    stage_name: str


@dataclass
class StageCompleted(PipelineEvent):
    stage_name: str
    success: bool


__all__ = [
    "PipelineEventBus",
    "PipelineEvent",
    "StageStarted",
    "StageCompleted",
]


