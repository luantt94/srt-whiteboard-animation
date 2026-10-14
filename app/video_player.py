#!/usr/bin/env python3
"""
Khung phát video nhúng ngay trong cửa sổ app (dùng QtMultimedia), để xem kết
quả render ngay sau khi xử lý xong — không cần mở trình phát ngoài.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget


def _fmt_time(ms: int) -> str:
    s = max(0, ms) // 1000
    return f"{s // 60:02d}:{s % 60:02d}"


class VideoPlayer(QWidget):
    """Widget phát video tối giản: khung hình + phát/tạm dừng + thanh tua."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._path: Path | None = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self.placeholder = QLabel("Video kết quả sẽ phát ở đây sau khi xử lý xong.")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setMinimumHeight(220)
        self.placeholder.setStyleSheet("color:#888; padding: 30px;")
        lay.addWidget(self.placeholder)

        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(260)
        lay.addWidget(self.video_widget)
        self.video_widget.hide()

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(self._on_state)
        self.player.errorOccurred.connect(self._on_error)

        controls = QHBoxLayout()
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedWidth(40)
        self.btn_play.setEnabled(False)
        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_replay = QPushButton("⟲")
        self.btn_replay.setFixedWidth(40)
        self.btn_replay.setEnabled(False)
        self.btn_replay.setToolTip("Phát lại từ đầu")
        self.btn_replay.clicked.connect(self._replay)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(100)
        self.btn_external = QPushButton("Mở bằng trình phát ngoài")
        self.btn_external.setEnabled(False)
        self.btn_external.clicked.connect(self._open_external)
        controls.addWidget(self.btn_play)
        controls.addWidget(self.btn_replay)
        controls.addWidget(self.slider, 1)
        controls.addWidget(self.time_label)
        controls.addWidget(self.btn_external)
        lay.addLayout(controls)

    def load(self, path: Path, autoplay: bool = True) -> None:
        self._path = Path(path)
        self.placeholder.hide()
        self.video_widget.show()
        self.player.setSource(QUrl.fromLocalFile(str(self._path)))
        self.btn_play.setEnabled(True)
        self.btn_replay.setEnabled(True)
        self.btn_external.setEnabled(True)
        if autoplay:
            self.player.play()

    def clear(self) -> None:
        self._path = None
        self.player.stop()
        self.player.setSource(QUrl())
        self.video_widget.hide()
        self.placeholder.setText("Video kết quả sẽ phát ở đây sau khi xử lý xong.")
        self.placeholder.show()
        self.btn_play.setEnabled(False)
        self.btn_replay.setEnabled(False)
        self.btn_external.setEnabled(False)

    def _toggle_play(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            return
        dur = self.player.duration()
        if dur > 0 and self.player.position() >= dur - 50:
            self.player.setPosition(0)
        self.player.play()

    def _replay(self) -> None:
        self.player.setPosition(0)
        self.player.play()

    def _on_state(self, state: QMediaPlayer.PlaybackState) -> None:
        self.btn_play.setText(
            "⏸" if state == QMediaPlayer.PlaybackState.PlayingState else "▶"
        )

    def _on_position(self, pos: int) -> None:
        if not self.slider.isSliderDown():
            self.slider.setValue(pos)
        self.time_label.setText(f"{_fmt_time(pos)} / {_fmt_time(self.player.duration())}")

    def _on_duration(self, dur: int) -> None:
        self.slider.setRange(0, dur)

    def _on_error(self, _error, error_string: str) -> None:
        if error_string:
            self.placeholder.setText(f"Không phát được video:\n{error_string}")
            self.placeholder.show()
            self.video_widget.hide()

    def _open_external(self) -> None:
        if self._path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._path)))
