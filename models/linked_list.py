"""Реализация кольцевого двусвязного списка."""

from __future__ import annotations

from typing import Any, Iterator, Optional

from .linked_list_item import LinkedListItem


class LinkedList:
    """Список узлов с доступом к началу и концу."""

    def __init__(self, first_item: Any = None) -> None:
        self._first_item: Optional[LinkedListItem] = None
        self._last_item: Optional[LinkedListItem] = None
        self._size = 0
        self._iter_current: Optional[LinkedListItem] = None
        self._iter_left = 0
        if first_item is None:
            return
        if isinstance(first_item, LinkedListItem):
            current = first_item
            seen: set[int] = set()
            nodes: list[LinkedListItem] = []
            while current is not None and id(current) not in seen:
                seen.add(id(current))
                nodes.append(current)
                current = current.next_item
            self._first_item = nodes[0]
            self._last_item = nodes[-1]
            self._size = len(nodes)
            for index, node in enumerate(nodes):
                node.previous_item = nodes[index - 1]
                node.next_item = nodes[(index + 1) % len(nodes)]
        else:
            self.append_right(first_item)

    @property
    def first_item(self) -> Optional[LinkedListItem]:
        """Первый узел."""
        return self._first_item

    @property
    def last(self) -> Optional[LinkedListItem]:
        """Последний узел."""
        return self._last_item

    def _nodes(self) -> Iterator[LinkedListItem]:
        """Перебрать узлы один раз, начиная с первого."""
        node = self._first_item
        for _ in range(self._size):
            if node is None:
                return
            yield node
            node = node.next_item

    @staticmethod
    def _wrap(item: Any) -> LinkedListItem:
        return item if isinstance(item, LinkedListItem) else LinkedListItem(item)

    def find_node(self, item: Any) -> Optional[LinkedListItem]:
        """Найти узел по нему самому или по его данным."""
        for node in self._nodes():
            if node is item or node.data == item:
                return node
        return None

    def append_left(self, item: Any) -> None:
        """Добавить данные в начало списка."""
        node = self._wrap(item)
        if self._size == 0:
            node._next = node
            node._previous = node
            self._first_item = self._last_item = node
        else:
            node._previous = self._last_item
            node._next = self._first_item
            self._last_item._next = node
            self._first_item._previous = node
            self._first_item = node
        self._size += 1

    def append_right(self, item: Any) -> None:
        """Добавить данные в конец списка."""
        node = self._wrap(item)
        if self._size == 0:
            self.append_left(node)
            return
        node._previous = self._last_item
        node._next = self._first_item
        self._last_item._next = node
        self._first_item._previous = node
        self._last_item = node
        self._size += 1

    def append(self, item: Any) -> None:
        """Добавить данные в конец списка."""
        self.append_right(item)

    def remove(self, item: Any) -> None:
        """Удалить узел или первое совпадение данных."""
        node = self.find_node(item)
        if node is None:
            raise ValueError("Элемент не найден в списке")
        if self._size == 1:
            self._first_item = self._last_item = None
        else:
            node.previous_item._next = node.next_item
            node.next_item._previous = node.previous_item
            if node is self._first_item:
                self._first_item = node.next_item
            if node is self._last_item:
                self._last_item = node.previous_item
        node._next = node._previous = None
        self._size -= 1

    def insert(self, previous: LinkedListItem, item: Any) -> None:
        """Вставить данные после узла previous."""
        previous_node = self.find_node(previous)
        if previous_node is None:
            raise ValueError("Предыдущий элемент не найден в списке")
        if previous_node is self._last_item:
            self.append_right(item)
            return
        node = self._wrap(item)
        node._previous = previous_node
        node._next = previous_node.next_item
        previous_node.next_item._previous = node
        previous_node._next = node
        self._size += 1

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[LinkedListItem]:
        """Вернуть итератор по узлам списка."""
        self._iter_current = self._first_item
        self._iter_left = self._size
        return self

    def __next__(self) -> LinkedListItem:
        """Вернуть следующий узел для цикла for."""
        if self._iter_left == 0 or self._iter_current is None:
            raise StopIteration
        node = self._iter_current
        self._iter_current = node.next_item
        self._iter_left -= 1
        return node

    def __getitem__(self, index: int) -> Any:
        """Получить данные узла по индексу."""
        if index < 0:
            index += self._size
        if not 0 <= index < self._size:
            raise IndexError("Индекс вне диапазона")
        for position, node in enumerate(self._nodes()):
            if position == index:
                return node.data
        raise IndexError("Индекс вне диапазона")

    def __contains__(self, item: object) -> bool:
        """Проверить, есть ли элемент в списке."""
        return self.find_node(item) is not None

    def __reversed__(self) -> Iterator[Any]:
        """Перебрать данные от последнего элемента к первому."""
        node = self._last_item
        for _ in range(self._size):
            if node is not None:
                yield node.data
                node = node.previous_item
