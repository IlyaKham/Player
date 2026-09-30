"""Модуль с реализацией плейлиста."""

from __future__ import annotations

from typing import Optional, Union

from .composition import Composition
from .linked_list import LinkedList
from .linked_list_item import LinkedListItem


ListItemOrData = Union[Composition, LinkedListItem]


class PlayList(LinkedList):
    """Плейлист на основе двусвязного списка.

    Переход между композициями выполняется по кругу:
    после последнего трека идёт первый,
    перед первым треком идёт последний.
    """

    def __init__(
        self,
        first_item: Optional[ListItemOrData] = None,
    ) -> None:
        """Создать плейлист."""
        super().__init__(first_item)

        self._current_item: Optional[LinkedListItem] = (
            self._first_item
        )

    @property
    def current(self) -> Optional[Composition]:
        """Получить текущую композицию."""
        if self._current_item is None:
            return None

        return self._current_item.data

    def play_all(self, item: ListItemOrData) -> None:
        """Начать проигрывание с указанной композиции.

        Args:
            item: Композиция или узел.

        Raises:
            ValueError: Если композиция отсутствует.
        """
        node = self.find_node(item)

        if node is None:
            raise ValueError(
                "Элемент не найден в плейлисте"
            )

        self._current_item = node

    def next_track(self) -> Optional[Composition]:
        """Перейти к следующему треку по кругу."""
        if self._first_item is None:
            self._current_item = None
            return None

        if self._current_item is None:
            self._current_item = self._first_item

        elif self._current_item.next_item is not None:
            self._current_item = self._current_item.next_item

        else:
            self._current_item = self._first_item

        return self.current

    def previous_track(self) -> Optional[Composition]:
        """Перейти к предыдущему треку по кругу."""
        if self._last_item is None:
            self._current_item = None
            return None

        if self._current_item is None:
            self._current_item = self._last_item

        elif self._current_item.previous_item is not None:
            self._current_item = self._current_item.previous_item

        else:
            self._current_item = self._last_item

        return self.current

    def remove(self, item: ListItemOrData) -> None:
        """Удалить композицию из плейлиста.

        Если удаляется текущий трек, текущим становится
        следующий трек, а если его нет — предыдущий.
        """
        node = self.find_node(item)

        if node is None:
            raise ValueError(
                "Элемент не найден в плейлисте"
            )

        was_current = node is self._current_item

        next_item = node.next_item
        previous_item = node.previous_item

        super().remove(node)

        if self._size == 0:
            self._current_item = None
            return

        if was_current:
            if next_item is not None:
                self._current_item = next_item
            else:
                self._current_item = previous_item

    def append_left(self, item: ListItemOrData) -> None:
        """Добавить композицию в начало."""
        was_empty = len(self) == 0

        super().append_left(item)

        if was_empty:
            self._current_item = self._first_item

    def append_right(self, item: ListItemOrData) -> None:
        """Добавить композицию в конец."""
        was_empty = len(self) == 0

        super().append_right(item)

        if was_empty:
            self._current_item = self._first_item
