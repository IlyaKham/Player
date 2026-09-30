"""Графический интерфейс музыкального плеера."""

from __future__ import annotations

import os
import sys
from typing import Optional

import pygame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from linked_list import (
    Composition,
    PlayList,
)


MUSIC_END = pygame.USEREVENT + 1


class AudioPlayer:
    """Обёртка над pygame.mixer.music.

    Микшер инициализируется лениво — только при первом
    воспроизведении. Это позволяет GUI запускаться даже
    при проблемах с аудиоустройством.
    """

    def __init__(self) -> None:
        """Создать аудиоплеер."""
        self._initialized = False
        self._paused = False
        self._init_error: Optional[str] = None

    @property
    def initialized(self) -> bool:
        """Вернуть состояние инициализации микшера."""
        return self._initialized

    @property
    def paused(self) -> bool:
        """Вернуть состояние паузы."""
        return self._paused

    def _initialize(self) -> bool:
        """Попытаться инициализировать pygame mixer."""
        if self._initialized:
            return True

        try:
            pygame.mixer.init()
            pygame.mixer.music.set_endevent(MUSIC_END)

            self._initialized = True
            self._init_error = None

            return True

        except pygame.error as exc:
            self._init_error = str(exc)

            print(
                "Не удалось инициализировать аудио: "
                f"{self._init_error}"
            )

            return False

    def play(self, path: str) -> bool:
        """Загрузить и проиграть аудиофайл."""
        if not path or not os.path.isfile(path):
            return False

        if not self._initialize():
            return False

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()

            self._paused = False

            return True

        except pygame.error as exc:
            print(
                f"Ошибка воспроизведения: {exc}"
            )

            return False

    def stop(self) -> None:
        """Остановить воспроизведение."""
        if not self._initialized:
            return

        pygame.mixer.music.stop()
        self._paused = False

    def toggle_pause(self) -> None:
        """Поставить воспроизведение на паузу или продолжить."""
        if not self._initialized:
            return

        if self._paused:
            pygame.mixer.music.unpause()
            self._paused = False
        else:
            pygame.mixer.music.pause()
            self._paused = True


class PlayerWindow(QMainWindow):
    """Главное окно музыкального плеера."""

    def __init__(self) -> None:
        """Инициализировать окно."""
        super().__init__()

        self.playlists: dict[str, PlayList] = {}
        self.current_playlist: Optional[PlayList] = None

        self.player = AudioPlayer()

        self.playlist_widget: QListWidget
        self.track_widget: QListWidget
        self.status_label: QLabel

        self._init_ui()
        self._start_pygame_watcher()

    def _init_ui(self) -> None:
        """Создать графический интерфейс."""
        self.setWindowTitle("Музыкальный плеер")

        self.setGeometry(
            100,
            100,
            900,
            600,
        )

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Horizontal)

        splitter.addWidget(
            self._build_playlists_panel()
        )

        splitter.addWidget(
            self._build_tracks_panel()
        )

        splitter.setSizes(
            [250, 650]
        )

        main_layout.addWidget(splitter)

    def _build_playlists_panel(self) -> QWidget:
        """Создать панель управления плейлистами."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        layout.addWidget(
            QLabel("Плейлисты:")
        )

        self.playlist_widget = QListWidget()

        self.playlist_widget.itemClicked.connect(
            self.on_playlist_selected
        )

        layout.addWidget(
            self.playlist_widget
        )

        buttons = QHBoxLayout()

        add_btn = QPushButton("Создать")
        add_btn.clicked.connect(
            self.create_playlist
        )

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(
            self.delete_playlist
        )

        buttons.addWidget(add_btn)
        buttons.addWidget(delete_btn)

        layout.addLayout(buttons)

        return panel

    def _build_tracks_panel(self) -> QWidget:
        """Создать панель управления композициями."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        layout.addWidget(
            QLabel("Композиции:")
        )

        self.track_widget = QListWidget()

        self.track_widget.itemDoubleClicked.connect(
            self.play_selected
        )

        layout.addWidget(
            self.track_widget
        )

        track_buttons = QHBoxLayout()

        buttons = (
            ("Добавить", self.add_track),
            ("Удалить", self.delete_track),
            ("↑", self.move_up),
            ("↓", self.move_down),
        )

        for text, handler in buttons:
            button = QPushButton(text)
            button.clicked.connect(handler)
            track_buttons.addWidget(button)

        layout.addLayout(track_buttons)

        control_buttons = QHBoxLayout()

        controls = (
            ("◀◀", self.previous_track),
            ("▶/❚❚", self.toggle_pause),
            ("■", self.stop_playback),
            ("▶▶", self.next_track),
        )

        for text, handler in controls:
            button = QPushButton(text)
            button.clicked.connect(handler)
            control_buttons.addWidget(button)

        layout.addLayout(control_buttons)

        play_button = QPushButton(
            "▶ Воспроизвести выбранный"
        )

        play_button.clicked.connect(
            self.play_selected
        )

        layout.addWidget(play_button)

        self.status_label = QLabel(
            "Текущий трек: —"
        )

        layout.addWidget(
            self.status_label
        )

        return panel

    def _start_pygame_watcher(self) -> None:
        """Запустить таймер проверки событий pygame."""
        self._timer = QTimer(self)

        self._timer.setInterval(200)

        self._timer.timeout.connect(
            self._poll_pygame_events
        )

        self._timer.start()

    def _poll_pygame_events(self) -> None:
        """Обработать завершение текущего трека."""
        if not self.player.initialized:
            return

        try:
            events = pygame.event.get()
        except pygame.error:
            return

        for event in events:
            if event.type != MUSIC_END:
                continue

            if self.current_playlist is None:
                continue

            self.current_playlist.next_track()

            self.update_status()
            self._sync_selection()
            self._play_current_audio()

    # ---------------------------------------------------------
    # Плейлисты
    # ---------------------------------------------------------

    def create_playlist(self) -> None:
        """Создать новый плейлист."""
        name, ok = QInputDialog.getText(
            self,
            "Создать плейлист",
            "Название:",
        )

        if not ok or not name.strip():
            return

        name = name.strip()

        if name in self.playlists:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Плейлист уже существует.",
            )
            return

        self.playlists[name] = PlayList()

        self.playlist_widget.addItem(name)

        self.playlist_widget.setCurrentRow(
            self.playlist_widget.count() - 1
        )

        self.current_playlist = self.playlists[name]

        self.refresh_tracks()

    def delete_playlist(self) -> None:
        """Удалить выбранный плейлист."""
        item = self.playlist_widget.currentItem()

        if item is None:
            return

        name = item.text()

        if (
            self.current_playlist
            is self.playlists.get(name)
        ):
            self.player.stop()

        del self.playlists[name]

        row = self.playlist_widget.row(item)

        self.playlist_widget.takeItem(row)

        if not self.playlists:
            self.current_playlist = None
            self.track_widget.clear()
            self.status_label.setText(
                "Текущий трек: —"
            )
            return

        new_row = min(
            row,
            self.playlist_widget.count() - 1,
        )

        self.playlist_widget.setCurrentRow(
            new_row
        )

        selected = (
            self.playlist_widget.item(new_row)
        )

        if selected is not None:
            self.on_playlist_selected(
                selected
            )

    def on_playlist_selected(
        self,
        item: QListWidgetItem,
    ) -> None:
        """Выбрать плейлист."""
        name = item.text()

        self.current_playlist = (
            self.playlists[name]
        )

        self.refresh_tracks()

    # ---------------------------------------------------------
    # Отображение треков
    # ---------------------------------------------------------

    def refresh_tracks(self) -> None:
        """Обновить список композиций."""
        self.track_widget.clear()

        if self.current_playlist is None:
            self.update_status()
            return

        for node in self.current_playlist:
            composition = node.data
            if composition is None:
                continue
            self.track_widget.addItem(
                f"{composition.artist} — "
                f"{composition.name}"
            )

        self.update_status()
        self._sync_selection()

    def update_status(self) -> None:
        """Обновить информацию о текущем треке."""
        if (
            self.current_playlist is not None
            and self.current_playlist.current is not None
        ):
            composition = (
                self.current_playlist.current
            )

            self.status_label.setText(
                "Текущий трек: "
                f"{composition.artist} — "
                f"{composition.name}"
            )
        else:
            self.status_label.setText(
                "Текущий трек: —"
            )

    def _sync_selection(self) -> None:
        """Синхронизировать выделение трека."""
        if self.current_playlist is None:
            return

        current = self.current_playlist.current

        if current is None:
            return

        for index in range(
            self.track_widget.count()
        ):
            if (
                self.current_playlist[index]
                == current
            ):
                self.track_widget.setCurrentRow(
                    index
                )
                return

    # ---------------------------------------------------------
    # Работа с композициями
    # ---------------------------------------------------------

    def add_track(self) -> None:
        """Добавить композицию."""
        if self.current_playlist is None:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Сначала выберите плейлист.",
            )
            return

        name, ok = QInputDialog.getText(
            self,
            "Добавить трек",
            "Название:",
        )

        if not ok or not name.strip():
            return

        artist, ok = QInputDialog.getText(
            self,
            "Добавить трек",
            "Исполнитель:",
        )

        if not ok:
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите аудиофайл",
            "",
            (
                "Аудио (*.mp3 *.ogg *.wav);;"
                "Все файлы (*.*)"
            ),
        )

        if not path:
            return

        composition = Composition(
            name=name.strip(),
            artist=artist.strip(),
            path=path,
        )

        self.current_playlist.append(
            composition
        )

        self.refresh_tracks()

    def delete_track(self) -> None:
        """Удалить выбранную композицию."""
        if self.current_playlist is None:
            return

        row = self.track_widget.currentRow()

        if row < 0:
            return

        composition = (
            self.current_playlist[row]
        )

        was_current = (
            self.current_playlist.current
            == composition
        )

        self.current_playlist.remove(
            composition
        )

        if was_current:
            self.player.stop()

        self.refresh_tracks()

    def move_up(self) -> None:
        """Переместить композицию вверх."""
        if self.current_playlist is None:
            return

        row = self.track_widget.currentRow()

        if row <= 0:
            return

        self._move(
            row,
            row - 1,
        )

    def move_down(self) -> None:
        """Переместить композицию вниз."""
        if self.current_playlist is None:
            return

        row = self.track_widget.currentRow()

        if (
            row < 0
            or row >= len(self.current_playlist) - 1
        ):
            return

        self._move(
            row,
            row + 1,
        )

    def _move(
        self,
        from_row: int,
        to_row: int,
    ) -> None:
        """Переместить композицию на другую позицию."""
        playlist = self.current_playlist

        if playlist is None:
            return

        if from_row == to_row:
            return

        node = playlist.find_node(
            playlist[from_row]
        )

        if node is None:
            return

        composition = playlist[from_row]

        playlist.remove(node)

        # После удаления снова строим позицию.
        # Так мы не работаем со старым target_node,
        # который мог изменить связи.
        if to_row <= 0:
            playlist.append_left(node)
        elif to_row >= len(playlist):
            playlist.append_right(node)
        else:
            previous = playlist.find_node(
                playlist[to_row - 1]
            )

            if previous is None:
                playlist.append_right(node)
            else:
                playlist.insert(
                    previous,
                    node,
                )

        playlist.play_all(composition)

        self.refresh_tracks()

        self.track_widget.setCurrentRow(
            to_row
        )

    # ---------------------------------------------------------
    # Воспроизведение
    # ---------------------------------------------------------

    def _play_current_audio(self) -> None:
        """Воспроизвести текущую композицию."""
        if self.current_playlist is None:
            return

        composition = (
            self.current_playlist.current
        )

        if composition is None:
            return

        if not composition.path:
            self.status_label.setText(
                "Текущий трек: "
                f"{composition.artist} — "
                f"{composition.name} "
                "(файл не задан)"
            )
            return

        if not os.path.isfile(
            composition.path
        ):
            QMessageBox.warning(
                self,
                "Ошибка",
                "Аудиофайл не найден:\n"
                f"{composition.path}",
            )
            return

        if not self.player.play(
            composition.path
        ):
            error = self.player._init_error

            if error:
                message = (
                    "Не удалось инициализировать "
                    "аудиосистему:\n\n"
                    f"{error}"
                )
            else:
                message = (
                    "Не удалось воспроизвести "
                    "аудиофайл."
                )

            QMessageBox.warning(
                self,
                "Ошибка воспроизведения",
                message,
            )

    def play_selected(self) -> None:
        """Воспроизвести выбранную композицию."""
        if self.current_playlist is None:
            return

        row = self.track_widget.currentRow()

        if row < 0:
            return

        composition = (
            self.current_playlist[row]
        )

        self.current_playlist.play_all(
            composition
        )

        self.update_status()
        self._play_current_audio()

    def play_current(self) -> None:
        """Воспроизвести текущую композицию."""
        if self.current_playlist is None:
            return

        if self.current_playlist.current is None:
            if len(self.current_playlist) == 0:
                return

            self.current_playlist.play_all(
                self.current_playlist[0]
            )

        self.update_status()
        self._play_current_audio()

    def toggle_pause(self) -> None:
        """Поставить воспроизведение на паузу."""
        self.player.toggle_pause()

    def stop_playback(self) -> None:
        """Остановить воспроизведение."""
        self.player.stop()

    def next_track(self) -> None:
        """Перейти к следующей композиции."""
        if self.current_playlist is None:
            return

        self.current_playlist.next_track()

        self.update_status()
        self._sync_selection()
        self._play_current_audio()

    def previous_track(self) -> None:
        """Перейти к предыдущей композиции."""
        if self.current_playlist is None:
            return

        self.current_playlist.previous_track()

        self.update_status()
        self._sync_selection()
        self._play_current_audio()

    def closeEvent(self, event) -> None:
        """Корректно закрыть аудиоплеер."""
        self.player.stop()

        if self.player.initialized:
            try:
                pygame.mixer.quit()
            except pygame.error:
                pass

        try:
            pygame.quit()
        except pygame.error:
            pass

        event.accept()


def main() -> None:
    """Запустить графическое приложение."""
    app = QApplication(sys.argv)

    window = PlayerWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
