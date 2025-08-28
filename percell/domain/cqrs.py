from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar


C = TypeVar("C")
R = TypeVar("R")
Q = TypeVar("Q")
S = TypeVar("S")


class CommandHandler(ABC, Generic[C, R]):
    @abstractmethod
    def handle(self, command: C) -> R:  # pragma: no cover - interface
        ...


class QueryHandler(ABC, Generic[Q, S]):
    @abstractmethod
    def handle(self, query: Q) -> S:  # pragma: no cover - interface
        ...


@dataclass(frozen=True)
class CreateCellMaskCommand:
    source_path: str
    params_json: str


@dataclass(frozen=True)
class GetAnalysisResultsQuery:
    output_dir: str


