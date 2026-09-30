"""Фасад для совместимости с тестами.

Позволяет импортировать классы напрямую:

    from linked_list import Composition, LinkedListItem, LinkedList, PlayList
"""

from models import (
    Composition,
    LinkedList,
    LinkedListItem,
    PlayList,
)

__all__ = [
    "Composition",
    "LinkedListItem",
    "LinkedList",
    "PlayList",
]