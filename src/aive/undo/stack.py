"""Undo / Redo edit history."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class EditState(Generic[T]):
    label: str
    data: T
    timestamp: float = 0.0


class UndoStack(Generic[T]):
    def __init__(self, max_depth: int = 100) -> None:
        self.max_depth = max_depth
        self._undo: list[EditState[T]] = []
        self._redo: list[EditState[T]] = []
        self._current: T | None = None

    def push(self, state: T, label: str = "") -> None:
        if self._current is not None:
            self._undo.append(EditState(label=label, data=deepcopy(self._current)))
            if len(self._undo) > self.max_depth:
                self._undo.pop(0)
        self._redo.clear()
        self._current = deepcopy(state)

    def undo(self) -> T | None:
        if not self._undo:
            return None
        if self._current is not None:
            self._redo.append(EditState(label="", data=deepcopy(self._current)))
        prev = self._undo.pop()
        self._current = deepcopy(prev.data)
        return self._current

    def redo(self) -> T | None:
        if not self._redo:
            return None
        if self._current is not None:
            self._undo.append(EditState(label="", data=deepcopy(self._current)))
        nxt = self._redo.pop()
        self._current = deepcopy(nxt.data)
        return self._current

    @property
    def can_undo(self) -> bool:
        return len(self._undo) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo) > 0

    @property
    def current(self) -> T | None:
        return self._current
