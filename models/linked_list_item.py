"""Узел кольцевого двусвязного списка."""

from __future__ import annotations

from typing import Any, Optional


class LinkedListItem:
    """Хранит данные и ссылки на соседние узлы."""

    def __init__(self, data: Any = None) -> None:
        self.data = data
        self._next: Optional[LinkedListItem] = None
        self._previous: Optional[LinkedListItem] = None

    @property
    def next_item(self) -> Optional[LinkedListItem]:
        """Следующий узел."""
        return self._next

    @next_item.setter
    def next_item(self, value: Optional[LinkedListItem]) -> None:
        self._next = value
        if value is not None and value._previous is not self:
            value._previous = self

    @property
    def previous_item(self) -> Optional[LinkedListItem]:
        """Предыдущий узел."""
        return self._previous

    @previous_item.setter
    def previous_item(self, value: Optional[LinkedListItem]) -> None:
        self._previous = value
        if value is not None and value._next is not self:
            value._next = self

    def __repr__(self) -> str:
        return f"LinkedListItem({self.data!r})"
