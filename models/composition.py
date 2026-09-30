"""Модуль с реализацией музыкальной композиции."""

from __future__ import annotations


class Composition:
    """Музыкальная композиция.

    Attributes:
        name: Название композиции.
        artist: Исполнитель.
        path: Путь к аудиофайлу.
    """

    name: str
    artist: str
    path: str

    def __init__(
        self,
        name: str = "",
        artist: str = "",
        path: str = "",
    ) -> None:
        """Создать композицию.

        Args:
            name: Название композиции.
            artist: Исполнитель.
            path: Путь к аудиофайлу.
        """
        self.name = name
        self.artist = artist
        self.path = path

    def __repr__(self) -> str:
        """Вернуть строковое представление композиции."""
        if self.artist:
            return f"{self.artist} — {self.name}"
        return self.name

    def __eq__(self, other: object) -> bool:
        """Сравнить две композиции.

        Композиции считаются одинаковыми, если совпадают название
        и исполнитель.
        """
        if not isinstance(other, Composition):
            return NotImplemented

        return (
            self.name,
            self.artist,
        ) == (
            other.name,
            other.artist,
        )

    def __hash__(self) -> int:
        """Вернуть хеш композиции."""
        return hash((self.name, self.artist))