"""Точка входа в приложение музыкального плеера."""

from __future__ import annotations

import sys

from PyQt5.QtWidgets import QApplication

from player_gui import PlayerWindow


def main() -> None:
    """Создать приложение и запустить главное окно."""
    app = QApplication(sys.argv)

    window = PlayerWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()