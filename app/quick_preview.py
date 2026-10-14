#!/usr/bin/env python3
"""
Xem nhanh kiểu CapCut: phát lại hiệu ứng "lộ dần" của toàn bộ dự án (nhiều
cảnh nối tiếp, phụ đề, chữ chèn, âm thanh nếu có chọn) ngay trong app — không
gọi ffmpeg/render_stream_whiteboard.py nên gần như tức thì. Đổi lại đây chỉ
là bản mô phỏng (không có nét vẽ tay/hand-drawing animation như video thành
phẩm thật) — dùng để kiểm tra nhanh thứ tự/thời gian trước khi bấm TẠO VIDEO
NGAY để render bản đầy đủ.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QTimer, QUrl
from PySide6.QtGui import QFont, QImage, QPainter, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget,
)

import preview_widget


def _fmt_time(ms: float) -> str:
    s = max(0, int(ms)) // 1000
    return f"{s // 60:02d}:{s % 60:02d}"


class _SceneEntry:
    __slots__ = ("png", "cfg", "image", "paper", "duration_ms")

    def __init__(self, png: Path, cfg: dict, image: QImage, paper) -> None:
        self.png = png
        self.cfg = cfg
        self.image = image
        self.paper = paper
        self.duration_ms = preview_widget._total_ms(cfg)


class QuickPreviewDialog(QDialog):
    """Cửa sổ xem nhanh — nạp lại từ đĩa mỗi lần mở, không giữ trạng thái cũ
    giữa các lần mở khác dự án (giống preview_widget/timeline_widget)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("👁 Xem nhanh")
        self.resize(900, 640)
        self.scenes: list[_SceneEntry] = []
        self.texts: list[dict] = []
        self.time_ms = 0.0
        self.playing = False
        self._scrubbing = False
        self._last_tick = 0.0

        lay = QVBoxLayout(self)
        self.frame_label = QLabel("Chưa có ảnh nào để xem thử.")
        self.frame_label.setAlignment(Qt.AlignCenter)
        self.frame_label.setMinimumHeight(360)
        self.frame_label.setStyleSheet("background:#14161a; color:#888;")
        lay.addWidget(self.frame_label, 1)

        self.caption_label = QLabel()
        self.caption_label.setAlignment(Qt.AlignCenter)
        self.caption_label.setWordWrap(True)
        self.caption_label.setMinimumHeight(30)
        self.caption_label.setStyleSheet(
            "color:#202020; background:#F5EBD7; padding:6px; font-size:13px;"
        )
        lay.addWidget(self.caption_label)

        controls = QHBoxLayout()
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedWidth(40)
        self.btn_play.clicked.connect(self._toggle_play)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.sliderPressed.connect(self._on_scrub_start)
        self.slider.sliderMoved.connect(self._on_scrub_move)
        self.slider.sliderReleased.connect(self._on_scrub_end)
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(100)
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.close)
        controls.addWidget(self.btn_play)
        controls.addWidget(self.slider, 1)
        controls.addWidget(self.time_label)
        controls.addWidget(btn_close)
        lay.addLayout(controls)

        hint = QLabel(
            "Xem thử hiệu ứng lộ dần + phụ đề + chữ chèn + âm thanh ngay "
            "trong app, không cần đợi render — video thành phẩm (TẠO VIDEO "
            "NGAY) sẽ có thêm nét vẽ tay thật."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#8b929c; font-size:11px;")
        lay.addWidget(hint)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)

    # ── nạp dự án ──
    def reload(self, project: Path | None, audio_path: str) -> None:
        self._pause()
        self.scenes = []
        self.texts = []
        self.time_ms = 0.0
        if project and project.is_dir():
            for png in preview_widget._list_scene_pngs(project):
                img = QImage(str(png))
                if img.isNull():
                    continue
                img = img.convertToFormat(QImage.Format_ARGB32_Premultiplied)
                ann = png.with_suffix(".annotation.json")
                cfg = preview_widget._load_cfg(png, ann, img)
                paper = preview_widget._sample_paper(img)
                self.scenes.append(_SceneEntry(png, cfg, img, paper))
            tpath = project / "texts.json"
            if tpath.exists():
                try:
                    data = json.loads(tpath.read_text(encoding="utf-8"))
                    self.texts = data.get("items", [])
                except (OSError, ValueError):
                    self.texts = []
        self.slider.setRange(0, round(self._total_ms()))
        if audio_path and Path(audio_path).exists():
            self.player.setSource(QUrl.fromLocalFile(str(Path(audio_path).resolve())))
        else:
            self.player.setSource(QUrl())
        self._render(0.0)

    def _total_ms(self) -> float:
        return max(sum(s.duration_ms for s in self.scenes), 1000.0)

    def _scene_starts(self) -> list[float]:
        t = 0.0
        out = []
        for s in self.scenes:
            out.append(t)
            t += s.duration_ms
        return out

    # ── phát / tạm dừng / tua ──
    def _toggle_play(self) -> None:
        self._pause() if self.playing else self._play()

    def _play(self) -> None:
        if not self.scenes:
            return
        if self.time_ms >= self._total_ms():
            self.time_ms = 0.0
        self.playing = True
        self.btn_play.setText("⏸")
        if self.player.source().isValid():
            self.player.setPosition(round(self.time_ms))
            self.player.play()
        self._last_tick = time.monotonic()
        self._timer.start()

    def _pause(self) -> None:
        self.playing = False
        self.btn_play.setText("▶")
        self._timer.stop()
        if self.player.source().isValid():
            self.player.pause()

    def _tick(self) -> None:
        now = time.monotonic()
        dt_ms = (now - self._last_tick) * 1000
        self._last_tick = now
        total = self._total_ms()
        new_t = self.time_ms + dt_ms
        if new_t >= total:
            self._render(total)
            self._pause()
            return
        self._render(new_t)

    def _on_scrub_start(self) -> None:
        self._scrubbing = True
        if self.playing:
            self._pause()

    def _on_scrub_move(self, val: int) -> None:
        self._render(float(val))

    def _on_scrub_end(self) -> None:
        self._scrubbing = False
        if self.player.source().isValid():
            self.player.setPosition(round(self.time_ms))

    # ── vẽ khung hình ──
    def _render(self, time_ms: float) -> None:
        self.time_ms = max(0.0, min(time_ms, self._total_ms()))
        if not self.scenes:
            self.frame_label.setText("Chưa có ảnh nào để xem thử.")
            self.caption_label.clear()
            return
        starts = self._scene_starts()
        si = 0
        for i, s0 in enumerate(starts):
            if self.time_ms >= s0:
                si = i
        scene = self.scenes[si]
        local_t = self.time_ms - starts[si]
        img = preview_widget.render_reveal_frame(scene.cfg, scene.image, scene.paper, local_t)
        if img is not None:
            self._draw_text_overlays(img)
            pix = QPixmap.fromImage(img)
            self.frame_label.setPixmap(
                pix.scaled(self.frame_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        elements = scene.cfg.get("elements", [])
        started = [e for e in elements if e["reveal"]["startMs"] <= local_t]
        self.caption_label.setText(started[-1].get("subtitle", "") if started else "")
        self._update_slider()
        self.time_label.setText(f"{_fmt_time(self.time_ms)} / {_fmt_time(self._total_ms())}")

    def _draw_text_overlays(self, img: QImage) -> None:
        active = [
            t for t in self.texts
            if t.get("startMs", 0) <= self.time_ms < t.get("startMs", 0) + t.get("durationMs", 0)
        ]
        if not active:
            return
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        font = QFont()
        font.setPixelSize(max(20, img.height() // 18))
        font.setBold(True)
        painter.setFont(font)
        y = img.height() * 0.08
        row_h = img.height() * 0.12
        for t in active:
            rect = QRectF(0, y, img.width(), row_h)
            painter.setPen(Qt.black)
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                painter.drawText(rect.translated(dx, dy), Qt.AlignHCenter | Qt.AlignTop, t.get("text", ""))
            painter.setPen(Qt.white)
            painter.drawText(rect, Qt.AlignHCenter | Qt.AlignTop, t.get("text", ""))
            y += row_h
        painter.end()

    def _update_slider(self) -> None:
        if self._scrubbing:
            return
        self.slider.blockSignals(True)
        self.slider.setValue(round(self.time_ms))
        self.slider.blockSignals(False)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._render(self.time_ms)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._pause()
        super().closeEvent(event)
