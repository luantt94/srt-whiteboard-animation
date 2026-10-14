#!/usr/bin/env python3
"""
SRT Whiteboard Studio — giao diện PySide6 gói toàn bộ quy trình của skill
srt-whiteboard-animation vào một cửa sổ:

  1. Phụ đề & phân cảnh   -> scripts/parse_srt.py
  2. Ảnh cảnh & annotation -> quản lý thư mục dự án, tạo annotation mẫu
  3. Chú thích & preview   -> assets/preview.html + scripts/render_annotation_preview.py
  4. Render từng cảnh       -> scripts/render_stream_whiteboard.py
  5. Ghép các cảnh          -> scripts/merge_scenes.py
  6. Âm thanh & phụ đề      -> scripts/postprocess_video.py (ffmpeg + edge-tts)

Khởi động qua: python app/launch.py  (hoặc run_app.bat / run_app.sh)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QSize, QTimer, QUrl, QSettings
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QFileDialog,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QScrollArea, QSpinBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout, QWidget,
)

import preview_widget
import quick_preview
import timeline_widget
import video_player

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
ASSETS = SKILL_ROOT / "assets"
PREVIEW_HTML = ASSETS / "preview.html"
HAND_PNG = ASSETS / "drawing-hand.png"
GUIDE = SKILL_ROOT / "docs" / "HUONG_DAN_APP.md"
MAKE_DEMO = SKILL_ROOT / "examples" / "make_demo_project.py"
DEFAULT_PROJECT_ROOT = SKILL_ROOT / "assets" / "whiteboard"
DEMO_PROJECT = DEFAULT_PROJECT_ROOT / "demo-phong-canh"
NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def utf8_env() -> dict[str, str]:
    """Ép tiến trình con Python xuất UTF-8 (script in tiếng Trung; stdout bị
    pipe nên Windows mặc định cp1252 và sẽ lỗi UnicodeEncodeError)."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


# ──────────────────────────────────────────────────────────────
# Môi trường
# ──────────────────────────────────────────────────────────────
def venv_python() -> Path:
    if os.name == "nt":
        return SKILL_ROOT / ".venv" / "Scripts" / "python.exe"
    return SKILL_ROOT / ".venv" / "bin" / "python"


def _can_import(py: str, modules: str) -> bool:
    try:
        return subprocess.run(
            [py, "-c", f"import {modules}"],
            capture_output=True, creationflags=NO_WINDOW,
        ).returncode == 0
    except Exception:
        return False


def detect_env_py() -> str | None:
    """Trình thông dịch có đủ cv2/numpy/av để chạy script render."""
    vp = venv_python()
    if vp.exists() and _can_import(str(vp), "cv2, numpy, av"):
        return str(vp)
    if _can_import(sys.executable, "cv2, numpy, av"):
        return sys.executable
    return None


def fmt_ms(ms: float) -> str:
    s = ms / 1000.0
    return f"{int(s // 60):02d}:{s % 60:05.2f}"


_SCENE_IMAGE_GLOBS = ("*.png", "*.jpg", "*.jpeg")


def list_scene_pngs(project: Path) -> list[Path]:
    if not project or not project.is_dir():
        return []
    out = []
    for pat in _SCENE_IMAGE_GLOBS:
        for p in project.glob(pat):
            if p.name.endswith(".regions.png"):
                continue
            out.append(p)
    return sorted(out)


def _image_size_fallback(png: Path) -> tuple[int, int] | None:
    """QImage đôi khi không đọc được 1 số ảnh (định dạng lạ, hệ màu CMYK,
    ảnh quá lớn vượt giới hạn cấp phát mặc định của Qt…) — dùng cv2 (đã có
    sẵn cho detect_regions) làm phương án dự phòng lấy kích thước, để vẫn
    tạo được annotation thay vì bỏ cuộc im lặng."""
    try:
        import cv2
    except ImportError:
        return None
    img = cv2.imread(str(png), cv2.IMREAD_COLOR)
    if img is None:
        return None
    h, w = img.shape[:2]
    return w, h


def build_sample_annotation(png: Path, idx: int, scenes: list[dict]) -> dict | None:
    """Annotation tự động: dò các cụm nét vẽ riêng biệt trong ảnh
    (preview_widget.detect_regions) và xếp mỗi cụm thành 1 khối, vẽ nối tiếp
    nhau trái→phải. Nếu không dò được gì (ảnh trắng, thiếu OpenCV…), dùng lại
    phương án dự phòng: 1 vùng phủ toàn ảnh."""
    img = QImage(str(png))
    if img.isNull():
        size = _image_size_fallback(png)
        if size is None:
            return None
        w, h = size
    else:
        w, h = img.width(), img.height()
    sc = scenes[idx] if idx < len(scenes) else {}
    dur = sc.get("sceneDurationMs") or 9000
    subtitle = sc.get("text", "")

    regions = preview_widget.detect_regions(png)
    elements = []
    if regions:
        n = len(regions)
        gap_ms = 150
        start0, tail = 300, 500
        avail = max(dur - start0 - tail - gap_ms * (n - 1), n * 900)
        step = avail / n
        t = float(start0)
        for i, r in enumerate(regions):
            seq = i + 1
            rx, ry, rw, rh = r["x"], r["y"], r["width"], r["height"]
            elements.append({
                "id": f"region-{seq}",
                "label": f"Đối tượng {seq}",
                "sequence": seq,
                "narrativeRole": "",
                "subtitle": subtitle,
                "type": "object",
                "region": {"x": rx, "y": ry, "width": rw, "height": rh},
                "reveal": {
                    "direction": "top_to_bottom",
                    "startMs": round(t),
                    "durationMs": round(step),
                    "maskPaddingPx": 18,
                    "protectedRegions": [],
                },
                "handPath": {
                    "start": [rx + rw // 2, ry + max(1, round(rh * 0.1))],
                    "end": [rx + rw // 2, ry + round(rh * 0.9)],
                    "easing": "easeInOut",
                },
            })
            t += step + gap_ms
        scene_dur = max(dur, round(t))
    else:
        elements.append({
            "id": "region-1",
            "label": "Vùng 1",
            "sequence": 1,
            "narrativeRole": "bối cảnh mở đầu",
            "subtitle": subtitle,
            "type": "structure",
            "region": {
                "x": int(w * 0.05), "y": int(h * 0.05),
                "width": int(w * 0.9), "height": int(h * 0.9),
            },
            "reveal": {
                "direction": "top_to_bottom",
                "startMs": 300,
                "durationMs": max(1500, dur - 800),
                "maskPaddingPx": 20,
                "protectedRegions": [],
            },
            "handPath": {
                "start": [w // 2, int(h * 0.1)],
                "end": [w // 2, int(h * 0.9)],
                "easing": "easeInOut",
            },
        })
        scene_dur = dur

    return {
        "sceneId": f"scene-{idx + 1:02d}",
        "canvas": {"width": w, "height": h},
        "storyBasis": subtitle,
        "sceneDurationMs": scene_dur,
        "elements": elements,
    }


# ──────────────────────────────────────────────────────────────
# Worker chạy lệnh nền, phát log theo dòng
# ──────────────────────────────────────────────────────────────
class CommandWorker(QThread):
    line = Signal(str)
    job_done = Signal(str, int)
    all_done = Signal()

    def __init__(self, jobs: list[tuple[str, list[str]]], cwd: str):
        super().__init__()
        self.jobs = jobs
        self.cwd = cwd
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        for label, argv in self.jobs:
            if self._stop:
                break
            self.line.emit(f"\n$ {subprocess.list2cmdline(argv)}\n")
            try:
                proc = subprocess.Popen(
                    argv, cwd=self.cwd, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                    errors="replace", creationflags=NO_WINDOW, env=utf8_env(),
                )
            except Exception as exc:  # noqa: BLE001
                self.line.emit(f"[lỗi] Không chạy được lệnh: {exc}")
                self.job_done.emit(label, -1)
                continue
            assert proc.stdout is not None
            for raw in proc.stdout:
                if self._stop:
                    proc.terminate()
                    break
                self.line.emit(raw.rstrip("\n"))
            proc.wait()
            self.job_done.emit(label, proc.returncode or 0)
        self.all_done.emit()


class _PreviewDialog(QDialog):
    """Cửa sổ Preview: tự lưu thay đổi khi đóng (nút "Đóng", phím Esc hay nút
    X trên thanh tiêu đề đều đi qua closeEvent này) — trừ khi đóng bằng nút
    "Huỷ" (đặt cờ discard trước khi gọi close())."""

    def __init__(self, parent: QWidget, on_close) -> None:
        super().__init__(parent)
        self._on_close = on_close
        self.discard_next_close = False

    def closeEvent(self, event) -> None:  # noqa: N802
        self._on_close(self.discard_next_close)
        self.discard_next_close = False
        event.accept()


# ──────────────────────────────────────────────────────────────
# Cửa sổ chính
# ──────────────────────────────────────────────────────────────
class Studio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SRT Whiteboard Studio")
        self.resize(1120, 820)

        self.settings = QSettings("srt-whiteboard-animation", "studio")
        self.env_py: str | None = detect_env_py()
        self.project: Path | None = None
        self.parsed: dict | None = None
        self.scenes: list[dict] = []
        self.worker: CommandWorker | None = None
        self._busy = False
        self.run_buttons: list[QPushButton] = []
        self._quick_final_video: Path | None = None
        self._srt_dirty = False
        self._quick_audio_path = ""
        self._quick_steps: list[tuple[str, int]] = []
        self._quick_total = 0
        self._quick_done = 0.0

        self._build_menu()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        root.addWidget(self._build_top_bar())

        # self.tabs giữ nội bộ toàn bộ control của quy trình chi tiết cũ
        # (scene_table, render_combo, merge_list, av_*…) để tái dùng —
        # nhưng KHÔNG hiển thị cho người dùng: giao diện chính giờ chỉ còn
        # đúng 1 màn hình "⚡ Nhanh".
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_subtitles(), "1 · Phụ đề & phân cảnh")
        self._project_tab_widget = self._tab_project()
        self.tabs.addTab(self._project_tab_widget, "2 · Ảnh cảnh & annotation")
        self._annotate_tab_widget = self._tab_annotate()
        self.tabs.addTab(self._annotate_tab_widget, "3 · Chú thích & preview")
        self.tabs.addTab(self._tab_render(), "4 · Render cảnh")
        self.tabs.addTab(self._tab_merge(), "5 · Ghép cảnh")
        self.tabs.addTab(self._tab_audio(), "6 · Âm thanh & phụ đề")
        self._fast_tab_widget = self._tab_quick()
        self.tabs.insertTab(0, self._fast_tab_widget, "⚡ Nhanh")

        self._build_preview_dialog()

        # Chuyển tab "⚡ Nhanh" ra làm nội dung chính duy nhất của cửa sổ
        # (gỡ nó khỏi self.tabs — các tab còn lại vẫn tồn tại ẩn phía sau).
        # QTabWidget tự ẩn mọi trang không phải tab đang chọn; dời sang
        # layout khác không tự hiện lại nên phải setVisible(True) tay.
        root.addWidget(self._fast_tab_widget, 1)
        self._fast_tab_widget.setVisible(True)

        root.addWidget(self._build_log_panel())

        last = self.settings.value("project", "")
        last_srt = self.settings.value("srt", "")
        if last and Path(last).is_dir():
            self.set_project(Path(last))
            if last_srt:
                self._set_srt_path(last_srt)
        elif DEMO_PROJECT.is_dir():
            self.load_demo(announce=False)

        self._refresh_env_label()

    # ── thanh menu ──
    def _build_menu(self) -> None:
        m = self.menuBar().addMenu("Trợ giúp")
        a_demo = QAction("Nạp dự án mẫu (demo)", self)
        a_demo.triggered.connect(lambda: self.load_demo(announce=True))
        m.addAction(a_demo)
        a_guide = QAction("Mở hướng dẫn sử dụng", self)
        a_guide.triggered.connect(self.open_guide)
        m.addAction(a_guide)
        a_skill = QAction("Mở thư mục skill", self)
        a_skill.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(SKILL_ROOT)))
        )
        m.addAction(a_skill)
        m.addSeparator()
        a_about = QAction("Giới thiệu", self)
        a_about.triggered.connect(
            lambda: QMessageBox.information(
                self, "Giới thiệu",
                "SRT Whiteboard Studio\n\nGiao diện tích hợp cho skill "
                "srt-whiteboard-animation: biến phụ đề SRT thành video vẽ tay "
                "bảng trắng nền giấy vàng kem.",
            )
        )
        m.addAction(a_about)

    # ── thanh trên: môi trường + dự án ──
    def _build_top_bar(self) -> QWidget:
        box = QGroupBox("Môi trường & dự án")
        lay = QVBoxLayout(box)

        row1 = QHBoxLayout()
        self.env_label = QLabel()
        self.env_label.setWordWrap(True)
        btn_env = QPushButton("Chuẩn bị / kiểm tra môi trường")
        btn_env.clicked.connect(self.prepare_env)
        self.run_buttons.append(btn_env)
        row1.addWidget(self.env_label, 1)
        row1.addWidget(btn_env)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        self.project_edit = QLineEdit()
        self.project_edit.setReadOnly(True)
        self.project_edit.setPlaceholderText("Chưa chọn thư mục dự án …")
        btn_pick = QPushButton("Chọn thư mục…")
        btn_pick.clicked.connect(self.pick_project)
        btn_new = QPushButton("Tạo dự án mới…")
        btn_new.clicked.connect(self.new_project)
        btn_open = QPushButton("Mở thư mục")
        btn_open.clicked.connect(
            lambda: self.project and QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self.project))
            )
        )
        row2.addWidget(QLabel("Dự án:"))
        row2.addWidget(self.project_edit, 1)
        row2.addWidget(btn_pick)
        row2.addWidget(btn_new)
        row2.addWidget(btn_open)
        lay.addLayout(row2)
        return box

    def load_demo(self, announce: bool = True) -> None:
        if not DEMO_PROJECT.is_dir():
            msg = ("Chưa có dự án mẫu. Mở terminal tại thư mục skill và chạy:\n\n"
                   f"    python {MAKE_DEMO.relative_to(SKILL_ROOT)}")
            if announce:
                self.warn(msg)
            else:
                self.append_log("[cảnh báo] " + msg.replace("\n", " "))
            return
        self.scenes = []
        self.parsed = None
        self.set_project(DEMO_PROJECT)
        srt = DEMO_PROJECT / "demo.srt"
        if srt.exists():
            self._set_srt_path(str(srt))
            self.av_srt.setText(str(srt))
        self.sp_target.setValue(9)
        self.sp_min.setValue(5)
        self.sp_max.setValue(12)
        self.append_log(f"[ok] Đã nạp dự án mẫu: {DEMO_PROJECT}")

    # ── Tab "⚡ Nhanh" (1 màn hình: chọn ảnh → xử lý → xem ngay) ──
    def _make_collapsible(self, title: str, content: QWidget,
                           expanded: bool = True) -> QWidget:
        """Bọc 1 widget trong khung có nút ▾/▸ để ẩn/hiện — gom bớt mục cài
        đặt đã xong, dành chỗ cho khung xem video."""
        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        header = QPushButton(("▾  " if expanded else "▸  ") + title)
        header.setCheckable(True)
        header.setChecked(expanded)
        header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet(
            "QPushButton{text-align:left; font-weight:600; padding:5px 4px; "
            "border:none; background:transparent;}"
            "QPushButton:hover{background:#1c1f26;}"
        )
        content.setVisible(expanded)

        def _toggle(checked: bool) -> None:
            content.setVisible(checked)
            header.setText(("▾  " if checked else "▸  ") + title)

        header.toggled.connect(_toggle)
        lay.addWidget(header)
        lay.addWidget(content)
        self._quick_section_headers.append(header)
        return wrapper

    def _quick_collapse_sections(self) -> None:
        """Tự ẩn các mục cài đặt sau khi tạo video xong, để khung xem video
        (với nút phát/phát lại) hiện ngay, không cần cuộn xuống."""
        for header in self._quick_section_headers:
            header.setChecked(False)

    def _tab_quick(self) -> QWidget:
        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        outer = QVBoxLayout(inner)
        self._quick_section_headers: list[QPushButton] = []

        intro = QLabel(
            "<h2>⚡ Tạo video nhanh</h2>"
            "<p>Chọn ảnh line-art (chọn nhiều ảnh = nhiều cảnh nối tiếp nhau), "
            "bấm <b>TẠO VIDEO NGAY</b> — xem tiến độ xử lý và video phát ngay "
            "bên dưới, không cần mở trình phát ngoài. File phụ đề .srt là "
            "<b>tuỳ chọn</b>: có thì video khớp đúng theo lời kể; không có "
            "thì app tự vẽ lần lượt từng ảnh với thời lượng mặc định. Có thể "
            "thêm nhạc nền / giọng đọc có sẵn, hoặc để app tự đọc bằng AI.</p>"
        )
        intro.setWordWrap(True)
        intro.setTextFormat(Qt.RichText)
        outer.addWidget(intro)

        box = QGroupBox()
        blay = QVBoxLayout(box)
        r1 = QHBoxLayout()
        self.quick_images_label = QLabel("Chưa chọn ảnh nào.")
        self.quick_images_label.setWordWrap(True)
        btn_pick_img = QPushButton("Chọn ảnh…")
        btn_pick_img.clicked.connect(self._fast_pick_images)
        btn_demo = QPushButton("Dùng ảnh mẫu để thử")
        btn_demo.clicked.connect(lambda: self.load_demo(announce=True))
        r1.addWidget(self.quick_images_label, 1)
        r1.addWidget(btn_pick_img)
        r1.addWidget(btn_demo)
        blay.addLayout(r1)

        tl_hint = QLabel(
            "Kéo khối <b>cảnh</b> để đổi thứ tự. Kéo thân/2 đầu khối "
            "<b>đối tượng</b> (xanh/cam…) hoặc khối <b>chữ</b> (vàng) để đổi "
            "thời gian ngay trên timeline. Bấm (không kéo) vào 1 khối để sửa "
            "nhanh chi tiết."
        )
        tl_hint.setWordWrap(True)
        tl_hint.setTextFormat(Qt.RichText)
        tl_hint.setStyleSheet("color:#9aa1ab; font-size:11px;")
        blay.addWidget(tl_hint)

        self.quick_timeline = timeline_widget.TimelineWidget()
        self.quick_timeline.scene_clicked.connect(self._on_timeline_scene_clicked)
        self.quick_timeline.object_clicked.connect(self._on_timeline_object_clicked)
        self.quick_timeline.scenes_reordered.connect(self._reorder_scenes)
        self.quick_timeline.scene_removed.connect(self._on_timeline_scene_removed)
        self.quick_timeline.changed.connect(self._on_timeline_changed)
        self._quick_thumb_paths: list[Path] = []
        blay.addWidget(self.quick_timeline)
        outer.addWidget(self._make_collapsible("1. Ảnh cảnh", box))
        self._quick_img_section_header = self._quick_section_headers[-1]

        box2 = QGroupBox()
        blay2 = QVBoxLayout(box2)
        r2 = QHBoxLayout()
        self.quick_srt_label = QLabel(
            "Chưa chọn file .srt — mỗi ảnh sẽ dùng thời lượng mặc định ~9s."
        )
        self.quick_srt_label.setWordWrap(True)
        btn_pick_srt = QPushButton("Chọn .srt…")
        btn_pick_srt.clicked.connect(self.pick_srt)
        btn_clear_srt = QPushButton("Bỏ chọn")
        btn_clear_srt.clicked.connect(self._fast_clear_srt)
        r2.addWidget(self.quick_srt_label, 1)
        r2.addWidget(btn_pick_srt)
        r2.addWidget(btn_clear_srt)
        blay2.addLayout(r2)

        self.srt_text_edit = QPlainTextEdit()
        self.srt_text_edit.setPlaceholderText(
            "Nội dung phụ đề hiện ở đây, sửa trực tiếp được.\n\n"
            "Định dạng .srt — số thứ tự, mốc thời gian, lời thoại, dòng trống:\n"
            "1\n00:00:00,000 --> 00:00:04,000\nDòng lời bình đầu tiên…\n\n"
            "2\n00:00:04,000 --> 00:00:08,000\nDòng tiếp theo…"
        )
        self.srt_text_edit.setMaximumHeight(150)
        self.srt_text_edit.textChanged.connect(self._on_srt_text_changed)
        blay2.addWidget(self.srt_text_edit)

        r2b = QHBoxLayout()
        self.srt_dirty_label = QLabel()
        self.srt_dirty_label.setStyleSheet("color:#e0a800; font-weight:600;")
        self.btn_srt_save = QPushButton("Lưu nội dung phụ đề")
        self.btn_srt_save.setEnabled(False)
        self.btn_srt_save.clicked.connect(self._save_srt_text)
        r2b.addWidget(self.srt_dirty_label)
        r2b.addStretch(1)
        r2b.addWidget(self.btn_srt_save)
        blay2.addLayout(r2b)
        outer.addWidget(self._make_collapsible("2. Phụ đề (tuỳ chọn)", box2))

        box3 = QGroupBox()
        blay3 = QVBoxLayout(box3)
        ra = QHBoxLayout()
        self.quick_audio_label = QLabel("🎵 Chưa chọn file nhạc / giọng đọc có sẵn.")
        self.quick_audio_label.setWordWrap(True)
        btn_pick_audio = QPushButton("+ Thêm file âm thanh…")
        btn_pick_audio.clicked.connect(self._fast_pick_audio)
        btn_clear_audio = QPushButton("Bỏ chọn")
        btn_clear_audio.clicked.connect(self._fast_clear_audio)
        ra.addWidget(self.quick_audio_label, 1)
        ra.addWidget(btn_pick_audio)
        ra.addWidget(btn_clear_audio)
        blay3.addLayout(ra)

        self.quick_tts = QCheckBox(
            "Hoặc tự đọc lời bình bằng giọng AI (TTS) — cần có file .srt ở "
            "mục 2, và cần ffmpeg"
        )
        self.quick_tts.setEnabled(False)
        self.quick_tts.toggled.connect(self._on_quick_tts_toggled)
        blay3.addWidget(self.quick_tts)
        rv = QHBoxLayout()
        self.quick_voice = QComboBox()
        self.quick_voice.addItems(
            ["vi-VN-HoaiMyNeural (nữ)", "vi-VN-NamMinhNeural (nam)"]
        )
        rv.addWidget(QLabel("Giọng đọc:"))
        rv.addWidget(self.quick_voice)
        rv.addStretch(1)
        blay3.addLayout(rv)
        outer.addWidget(self._make_collapsible("3. Âm thanh (tuỳ chọn)", box3))

        run_row = QHBoxLayout()
        btn_preview = QPushButton("👁 Xem nhanh")
        btn_preview.setMinimumHeight(48)
        btn_preview.setToolTip(
            "Xem thử ngay hiệu ứng lộ dần + phụ đề + chữ chèn + âm thanh "
            "trong app — gần như tức thì, không cần đợi render video thật."
        )
        btn_preview.clicked.connect(self._open_quick_preview)
        btn_go = QPushButton("🚀 TẠO VIDEO NGAY")
        btn_go.setMinimumHeight(48)
        btn_go.setStyleSheet("font-size: 15px; font-weight: bold;")
        btn_go.clicked.connect(self.quick_run)
        self.run_buttons.append(btn_go)
        run_row.addWidget(btn_preview, 1)
        run_row.addWidget(btn_go, 2)
        outer.addLayout(run_row)

        prog_row = QHBoxLayout()
        self.quick_progress = QProgressBar()
        self.quick_progress.setRange(0, 100)
        self.quick_progress.setValue(0)
        self.quick_progress.setTextVisible(True)
        self.quick_progress.setFormat("%p%")
        self.quick_progress_label = QLabel("Sẵn sàng.")
        self.quick_progress_label.setStyleSheet("font-weight:600;")
        self.quick_progress_label.setMinimumWidth(220)
        prog_row.addWidget(self.quick_progress, 1)
        prog_row.addWidget(self.quick_progress_label)
        outer.addLayout(prog_row)

        self.fast_player = video_player.VideoPlayer()
        outer.addWidget(self.fast_player, 1)

        scroll.setWidget(inner)
        root.addWidget(scroll)
        return w

    def _fast_new_project(self) -> None:
        DEFAULT_PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
        name = f"video-{datetime.now():%Y%m%d-%H%M%S}"
        p = DEFAULT_PROJECT_ROOT / name
        p.mkdir(parents=True, exist_ok=True)
        self.set_project(p)
        self.append_log(f"[ok] Đã tạo dự án mới: {p}")

    def _fast_pick_images(self) -> None:
        files = QFileDialog.getOpenFileNames(
            self, "Chọn ảnh line-art", str(self.project or SKILL_ROOT),
            "Ảnh (*.png *.jpg *.jpeg)",
        )[0]
        if not files:
            return
        if not self.project:
            self._fast_new_project()
        for f in files:
            dst = self.project / Path(f).name
            if Path(f).resolve() != dst.resolve():
                try:
                    shutil.copy2(f, dst)
                except OSError as exc:
                    self.append_log(f"[LỖI] Không sao chép được {Path(f).name}: {exc}")
                    continue
                self.append_log(f"[ok] Đã sao chép {dst.name}")
        self._auto_annotate_missing()
        self.refresh_all_scene_lists()
        self._quick_img_section_header.setChecked(True)

    def _auto_annotate_missing(self) -> int:
        """Tự nhận diện đối tượng + tạo annotation ngay cho ảnh nào trong dự
        án chưa có — gọi ngay khi nạp ảnh, không cần đợi tới lúc tạo video."""
        if not self.project:
            return 0
        created = 0
        for idx, png in enumerate(list_scene_pngs(self.project)):
            if png.with_suffix(".annotation.json").exists():
                continue
            try:
                ok = self._auto_annotate(png, idx)
            except Exception as exc:  # noqa: BLE001 — 1 ảnh lỗi không được chặn các ảnh khác
                self.append_log(f"[LỖI] Không tự nhận diện được {png.name}: {exc}")
                continue
            if ok:
                created += 1
        if created:
            self.append_log(
                f"[ok] Đã tự tạo {created} annotation (tự nhận diện đối tượng "
                "trong ảnh, xếp thứ tự trái→phải)."
            )
        return created

    def _fast_clear_srt(self) -> None:
        self._set_srt_path("")

    def _fast_pick_audio(self) -> None:
        f = QFileDialog.getOpenFileName(
            self, "Chọn file nhạc / giọng đọc", str(self.project or SKILL_ROOT),
            "Âm thanh (*.mp3 *.wav *.m4a *.aac *.ogg *.flac);;Tất cả (*.*)",
        )[0]
        if f:
            self._quick_audio_path = f
            self.quick_tts.setChecked(False)
            self._update_quick_labels()
            self.quick_timeline.set_audio(f)

    def _fast_clear_audio(self) -> None:
        self._quick_audio_path = ""
        self._update_quick_labels()
        self.quick_timeline.set_audio("")

    def _on_quick_tts_toggled(self, checked: bool) -> None:
        if checked and self._quick_audio_path:
            self._quick_audio_path = ""
            self._update_quick_labels()

    def _set_srt_path(self, path: str) -> None:
        """Đặt lại file .srt đang dùng + nạp nội dung của nó vào ô soạn thảo."""
        self.srt_edit.setText(path)
        self.settings.setValue("srt", path)
        self._load_srt_text(Path(path) if path else None)
        self._update_quick_labels()

    def _load_srt_text(self, path: Path | None) -> None:
        self.srt_text_edit.blockSignals(True)
        if path and path.exists():
            try:
                self.srt_text_edit.setPlainText(
                    path.read_text(encoding="utf-8", errors="replace")
                )
            except OSError as exc:
                self.srt_text_edit.setPlainText("")
                self.append_log(f"[cảnh báo] Không đọc được {path.name}: {exc}")
        else:
            self.srt_text_edit.setPlainText("")
        self.srt_text_edit.blockSignals(False)
        self._srt_dirty = False
        self._update_srt_dirty_label()

    def _on_srt_text_changed(self) -> None:
        self._srt_dirty = True
        self._update_srt_dirty_label()

    def _update_srt_dirty_label(self) -> None:
        self.srt_dirty_label.setText("● Chưa lưu" if self._srt_dirty else "")
        self.btn_srt_save.setEnabled(self._srt_dirty)

    def _save_srt_text(self) -> bool:
        """Ghi nội dung ô soạn thảo xuống file .srt; hỏi nơi lưu nếu chưa có."""
        text = self.srt_text_edit.toPlainText()
        path_str = self.srt_edit.text().strip()
        if not path_str:
            default_dir = self.project or DEFAULT_PROJECT_ROOT
            default_dir.mkdir(parents=True, exist_ok=True)
            f = QFileDialog.getSaveFileName(
                self, "Lưu file phụ đề .srt", str(default_dir / "subtitle.srt"),
                "Phụ đề (*.srt)",
            )[0]
            if not f:
                return False
            if not f.lower().endswith(".srt"):
                f += ".srt"
            path_str = f
        path = Path(path_str)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        except OSError as exc:
            self.warn(f"Không lưu được {path.name}: {exc}")
            return False
        self.srt_edit.setText(str(path))
        if not self.av_srt.text():
            self.av_srt.setText(str(path))
        self.settings.setValue("srt", str(path))
        self._srt_dirty = False
        self._update_srt_dirty_label()
        self._update_quick_labels()
        self.append_log(f"[ok] Đã lưu phụ đề: {path}")
        return True

    def _ensure_srt_saved(self) -> bool:
        """Tự lưu nội dung phụ đề nếu còn sửa dở trước khi xử lý/phân tích."""
        return self._save_srt_text() if self._srt_dirty else True

    def _fast_preload_result(self, project: Path) -> None:
        """Nếu dự án đã có sẵn video thành phẩm, hiện luôn trong khung phát."""
        for name in (f"{project.name}-final-av.mp4", f"{project.name}-final.mp4"):
            cand = project / name
            if cand.exists():
                self._quick_final_video = cand
                self.fast_player.load(cand, autoplay=False)
                return
        self._quick_final_video = None
        self.fast_player.clear()

    def _refresh_quick_thumbs(self) -> None:
        pngs = list_scene_pngs(self.project) if self.project else []
        if pngs == self._quick_thumb_paths and self.quick_timeline.project == self.project:
            return
        self._quick_thumb_paths = pngs
        self.quick_timeline.reload(self.project)

    def _on_timeline_scene_clicked(self, png_str: str) -> None:
        self.show_preview_tab(Path(png_str))

    def _on_timeline_object_clicked(self, png_str: str, element_id: str) -> None:
        self.preview_editor.reload_project()
        self.preview_editor.select_element(Path(png_str).stem, element_id)
        self._preview_dialog.show()
        self._preview_dialog.raise_()
        self._preview_dialog.activateWindow()

    def _on_timeline_changed(self) -> None:
        """Timeline đã tự ghi thay đổi (thời gian đối tượng/chữ) xuống đĩa —
        nạp lại bảng chỉnh chi tiết nếu đang mở để khỏi hiện dữ liệu cũ."""
        if not self.preview_editor.has_unsaved():
            self.preview_editor.reload_project()

    def _on_timeline_scene_removed(self, png_name: str) -> None:
        """Timeline đã tự xoá file của 1 ảnh (cảnh) khỏi đĩa — làm mới toàn
        bộ danh sách cảnh (combo render, danh sách ghép…) để không còn tham
        chiếu tới file đã xoá."""
        self.append_log(f"[ok] Đã xoá {png_name} khỏi dự án.")
        self.preview_editor.reload_project()
        self.refresh_all_scene_lists()

    def _reorder_scenes(self, new_order: list[Path]) -> None:
        """Đổi thứ tự cảnh bằng cách đánh lại số scene-XX- trong tên file
        (đổi qua tên tạm trước để tránh đè lẫn nhau khi đánh số lại)."""
        if not self.project or len(new_order) < 2:
            return
        # Đuôi ảnh thật có thể là .png/.jpg/.jpeg — chỉ các file phụ mới chắc
        # chắn đuôi cố định; ảnh gốc dùng đúng png.suffix của chính nó.
        aux_exts = (".annotation.json", ".regions.png", "-whiteboard.mp4")
        entries = []
        for png in new_order:
            m = re.match(r"^scene-\d+-(.*)$", png.stem)
            entries.append(m.group(1) if m else png.stem)
        temp_map: dict[tuple[int, str], Path] = {}
        for i, png in enumerate(new_order):
            if png.exists():
                tmp = self.project / f"__reorder_{i}{png.suffix}"
                png.rename(tmp)
                temp_map[(i, "__img__")] = tmp
            for ext in aux_exts:
                f = self.project / f"{png.stem}{ext}"
                if f.exists():
                    tmp = self.project / f"__reorder_{i}{ext}"
                    f.rename(tmp)
                    temp_map[(i, ext)] = tmp
        for i, suffix in enumerate(entries):
            new_stem = f"scene-{i + 1:02d}-{suffix}"
            new_scene_id = f"scene-{i + 1:02d}"
            img_tmp = temp_map.get((i, "__img__"))
            if img_tmp and img_tmp.exists():
                img_tmp.rename(self.project / f"{new_stem}{img_tmp.suffix}")
            for ext in aux_exts:
                tmp = temp_map.get((i, ext))
                if not tmp or not tmp.exists():
                    continue
                dest = self.project / f"{new_stem}{ext}"
                tmp.rename(dest)
                if ext == ".annotation.json":
                    try:
                        cfg = json.loads(dest.read_text(encoding="utf-8"))
                        cfg["sceneId"] = new_scene_id
                        dest.write_text(
                            json.dumps(cfg, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                    except (OSError, json.JSONDecodeError):
                        pass
        self.append_log(f"[ok] Đã đổi thứ tự {len(entries)} cảnh.")
        if not self.preview_editor.has_unsaved():
            self.preview_editor.reload_project()
        self.refresh_all_scene_lists()

    def _update_quick_labels(self) -> None:
        if not hasattr(self, "quick_images_label"):
            return
        n = len(list_scene_pngs(self.project)) if self.project else 0
        if n:
            suffix = f" (dự án: {self.project.name})" if self.project else ""
            self.quick_images_label.setText(f"Đã chọn {n} ảnh{suffix}.")
        else:
            self.quick_images_label.setText("Chưa chọn ảnh nào.")
        self._refresh_quick_thumbs()
        srt = self.srt_edit.text().strip() if hasattr(self, "srt_edit") else ""
        if srt:
            self.quick_srt_label.setText(f"Phụ đề: {srt}")
        else:
            self.quick_srt_label.setText(
                "Chưa chọn file .srt — mỗi ảnh sẽ dùng thời lượng mặc định ~9s."
            )
        if not hasattr(self, "quick_audio_label"):
            return
        has_audio_file = bool(self._quick_audio_path)
        if has_audio_file:
            self.quick_audio_label.setText(f"🎵 File âm thanh: {self._quick_audio_path}")
        else:
            self.quick_audio_label.setText("🎵 Chưa chọn file nhạc / giọng đọc có sẵn.")
        if self.quick_timeline.audio_path != self._quick_audio_path:
            self.quick_timeline.set_audio(self._quick_audio_path)
        self.quick_tts.setEnabled(bool(srt) and not has_audio_file)
        if not srt or has_audio_file:
            self.quick_tts.setChecked(False)

    # ── Tiến độ tab ⚡ Nhanh ──
    def _quick_progress_update(self, done: float, label: str) -> None:
        self._quick_done = done
        pct = int(min(100, max(0, done / self._quick_total * 100))) if self._quick_total else 0
        self.quick_progress.setValue(pct)
        self.quick_progress_label.setText(f"{label} ({pct}%)")

    def _quick_fail(self, msg: str) -> None:
        self.quick_progress_label.setText("Thất bại — xem Nhật ký.")
        self.warn(msg)

    def quick_run(self) -> None:
        if not self.project or not list_scene_pngs(self.project):
            self.warn("Hãy bấm \"Chọn ảnh…\" để thêm ít nhất 1 ảnh line-art trước.")
            return
        if not self._ensure_srt_saved():
            return
        srt = self.srt_edit.text().strip()
        if srt and not Path(srt).exists():
            self.warn("File .srt đã chọn không tồn tại. Bấm \"Bỏ chọn\" hoặc chọn lại.")
            return
        if self._quick_audio_path and not Path(self._quick_audio_path).exists():
            self.warn("File âm thanh đã chọn không tồn tại. Bấm \"Bỏ chọn\" hoặc chọn lại.")
            return
        if self._busy:
            self.warn("Đang có tác vụ chạy. Vui lòng đợi hoặc bấm \"Dừng tác vụ\".")
            return

        pngs = list_scene_pngs(self.project)
        self._quick_steps = [("Chuẩn bị môi trường", 1)]
        if srt:
            self._quick_steps.append(("Phân tích phụ đề", 1))
        self._quick_steps.append(("Tạo chú thích tự động", 1))
        self._quick_steps.append(("Vẽ từng cảnh", len(pngs)))
        if len(pngs) > 1:
            self._quick_steps.append(("Ghép các cảnh", 1))
        wants_post = bool(self._quick_audio_path) or (bool(srt) and self.quick_tts.isChecked())
        if wants_post:
            self._quick_steps.append(("Thêm âm thanh / phụ đề", 1))
        self._quick_total = sum(w for _, w in self._quick_steps)
        self._quick_done = 0.0

        self.fast_player.clear()
        self._quick_progress_update(0, "Bắt đầu…")
        self.append_log("\n===== 🚀 BẮT ĐẦU TẠO VIDEO TỰ ĐỘNG =====")
        self._quick_phase_env()

    def _quick_phase_env(self) -> None:
        self._quick_progress_update(self._quick_done, "Chuẩn bị môi trường…")
        if self.env_py:
            self._quick_done += 1
            self._quick_phase_parse()
            return
        self.append_log("[quick] Chưa có môi trường render, tự cài đặt…")

        def done():
            self.env_py = detect_env_py()
            self._refresh_env_label()
            self._quick_done += 1
            if not self.env_py:
                self._quick_fail("Không chuẩn bị được môi trường render. Xem nhật ký.")
                return
            self._quick_phase_parse()

        self.run_jobs(
            [("prepare_env", [sys.executable, str(SCRIPTS / "prepare_env.py")])],
            done_cb=done,
        )

    def _quick_phase_parse(self) -> None:
        srt = self.srt_edit.text().strip()
        if not srt:
            self.scenes = []
            self.parsed = None
            self.append_log(
                "[quick] Không có phụ đề — mỗi ảnh dùng thời lượng mặc định ~9s."
            )
            self._quick_phase_annotate()
            return
        self._quick_progress_update(self._quick_done, "Phân tích phụ đề…")
        py = self.env_py or sys.executable
        argv = [
            py, str(SCRIPTS / "parse_srt.py"), srt,
            "--target-sec", str(self.sp_target.value()),
            "--min-sec", str(self.sp_min.value()),
            "--max-sec", str(self.sp_max.value()),
        ]
        self.append_log("$ " + subprocess.list2cmdline(argv))
        try:
            res = subprocess.run(
                argv, capture_output=True, text=True, encoding="utf-8",
                errors="replace", creationflags=NO_WINDOW, env=utf8_env(),
            )
        except Exception as exc:  # noqa: BLE001
            self._quick_fail(f"Không chạy được parse_srt.py: {exc}")
            return
        if res.returncode != 0:
            self.append_log(res.stderr.strip())
            self._quick_fail("Phân tích phụ đề lỗi. Xem nhật ký.")
            return
        try:
            data = json.loads(res.stdout)
        except json.JSONDecodeError as exc:
            self._quick_fail(f"Không đọc được kết quả JSON: {exc}")
            return
        self.parsed = data
        self.scenes = data.get("scenes", [])
        self.populate_scene_table()
        out = self.project / "scenes.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.append_log(f"[ok] {len(self.scenes)} cảnh. Đã lưu {out.name}.")
        self._quick_done += 1
        self._quick_phase_annotate()

    def _quick_phase_annotate(self) -> None:
        self._quick_progress_update(self._quick_done, "Tạo chú thích tự động…")
        self._auto_annotate_missing()  # thường đã làm từ lúc nạp ảnh, đây chỉ để chắc chắn
        self.refresh_all_scene_lists()
        self._quick_done += 1
        self._quick_phase_render()

    def _quick_phase_render(self) -> None:
        pngs = self._render_ready_pngs()
        if not pngs:
            self._quick_fail("Không có cảnh nào để render (thiếu ảnh hoặc annotation).")
            return
        jobs = [self._render_job(p) for p in pngs]
        base_done = self._quick_done
        n = len(jobs)

        def progress_cb(done: int, total: int) -> None:
            self._quick_progress_update(base_done + done, f"Đang vẽ cảnh {done}/{total}…")

        def done_all():
            self._quick_done = base_done + n
            self._quick_phase_merge()

        self.run_jobs(jobs, done_cb=done_all, progress_cb=progress_cb)

    def _quick_phase_merge(self) -> None:
        self.refresh_all_scene_lists()
        vids = sorted(self.project.glob("*-whiteboard.mp4"))
        if not vids:
            self._quick_fail("Không có video cảnh nào được render thành công.")
            return
        if len(vids) == 1:
            self._quick_final_video = vids[0]
            self._quick_phase_audio()
            return
        self._quick_progress_update(self._quick_done, "Ghép các cảnh…")
        out_name = f"{self.project.name}-final.mp4"
        out = self.project / out_name
        self.merge_out.setText(out_name)
        argv = [
            self.env_py, str(SCRIPTS / "merge_scenes.py"),
            "--inputs", *[str(v) for v in vids], "--output", str(out),
        ]

        def done():
            self.refresh_merge_list()
            self._quick_done += 1
            if out.exists():
                self._quick_final_video = out
            else:
                self.append_log("[LỖI] Ghép cảnh thất bại — không có video để tiếp tục.")
                self._quick_final_video = None
            self._quick_phase_audio()

        self.run_jobs([(f"merge -> {out_name}", argv)], done_cb=done)

    def _quick_phase_audio(self) -> None:
        if not self._quick_final_video or not self._quick_final_video.exists():
            self._quick_finish()
            return
        srt = self.srt_edit.text().strip()
        audio_file = self._quick_audio_path
        use_file = bool(audio_file) and Path(audio_file).exists()
        use_tts = bool(srt) and self.quick_tts.isChecked() and not use_file
        texts_path = self.project / "texts.json"
        has_texts = False
        if texts_path.exists():
            try:
                has_texts = bool(json.loads(texts_path.read_text(encoding="utf-8")).get("items"))
            except (OSError, ValueError):
                has_texts = False
        if not use_file and not use_tts and not has_texts:
            self._quick_finish()
            return
        if shutil.which("ffmpeg") is None:
            self.append_log(
                "[cảnh báo] Không có ffmpeg trong PATH, bỏ qua bước âm thanh/"
                "phụ đề/chữ chèn. Video câm đã có ở bước trước."
            )
            self._quick_finish()
            return
        self._quick_progress_update(self._quick_done, "Thêm âm thanh / phụ đề…")
        src = self._quick_final_video
        out = self.project / f"{self.project.name}-voice.mp4"
        if out.resolve() == src.resolve():
            out = self.project / f"{self.project.name}-voice2.mp4"
        argv = [
            self.env_py, str(SCRIPTS / "postprocess_video.py"),
            "--video", str(src), "--output", str(out),
        ]
        pre_jobs: list[tuple[str, list[str]]] = []
        if use_file:
            argv += ["--audio-file", audio_file]
        else:
            voice = self.quick_voice.currentText().split()[0]
            argv += ["--tts-srt", srt, "--tts-voice", voice, "--tts-group", "scene"]
            sc = self.project / "scenes.json"
            if sc.exists():
                argv += ["--scenes", str(sc)]
            if not _can_import(self.env_py, "edge_tts"):
                pre_jobs.append(
                    ("cài edge-tts", [self.env_py, "-m", "pip", "install", "--quiet", "edge-tts"])
                )
        if srt:
            argv += ["--burn-srt", srt, "--sub-fontsize", "20", "--sub-margin-v", "46"]
        if has_texts:
            argv += ["--texts", str(texts_path)]

        def done():
            self._quick_done += 1
            if out.exists():
                self._quick_final_video = out
            else:
                self.append_log(
                    "[cảnh báo] Thêm âm thanh/phụ đề/chữ chèn thất bại — vẫn giữ video "
                    f"câm đã render: {src.name}"
                )
            self._quick_finish()

        self.run_jobs(
            pre_jobs + [("hậu kỳ (âm thanh + phụ đề)", argv)], done_cb=done
        )

    def _quick_finish(self) -> None:
        self.refresh_all_scene_lists()
        if self._quick_final_video and self._quick_final_video.exists():
            self._quick_progress_update(self._quick_total, "Hoàn tất!")
            self.append_log(f"[ok] ===== HOÀN TẤT: {self._quick_final_video} =====")
            self.fast_player.load(self._quick_final_video, autoplay=True)
            self._quick_collapse_sections()
        else:
            self.quick_progress_label.setText("Thất bại — xem Nhật ký.")
            self.append_log("[LỖI] ===== KHÔNG TẠO ĐƯỢC VIDEO — xem chi tiết lỗi ở nhật ký phía trên =====")
            self.warn(
                "Không tạo được video kết quả. Bấm \"▸ Nhật ký\" ở cuối cửa sổ "
                "để xem chi tiết lỗi."
            )

    # ── Tab 1 ──
    def _tab_subtitles(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        row = QHBoxLayout()
        self.srt_edit = QLineEdit()
        self.srt_edit.setPlaceholderText("Chọn file .srt …")
        btn_srt = QPushButton("Chọn .srt…")
        btn_srt.clicked.connect(self.pick_srt)
        row.addWidget(QLabel("File SRT:"))
        row.addWidget(self.srt_edit, 1)
        row.addWidget(btn_srt)
        lay.addLayout(row)

        row2 = QHBoxLayout()
        self.sp_target = QSpinBox()
        self.sp_target.setRange(5, 120)
        self.sp_target.setValue(30)
        self.sp_min = QSpinBox()
        self.sp_min.setRange(5, 120)
        self.sp_min.setValue(25)
        self.sp_max = QSpinBox()
        self.sp_max.setRange(5, 240)
        self.sp_max.setValue(35)
        row2.addWidget(QLabel("Mục tiêu (giây/cảnh):"))
        row2.addWidget(self.sp_target)
        row2.addWidget(QLabel("Tối thiểu:"))
        row2.addWidget(self.sp_min)
        row2.addWidget(QLabel("Tối đa:"))
        row2.addWidget(self.sp_max)
        btn_parse = QPushButton("Phân tích phụ đề")
        btn_parse.clicked.connect(self.run_parse)
        self.run_buttons.append(btn_parse)
        row2.addWidget(btn_parse)
        btn_save = QPushButton("Lưu scenes.json vào dự án")
        btn_save.clicked.connect(self.save_scenes_json)
        row2.addWidget(btn_save)
        row2.addStretch(1)
        lay.addLayout(row2)

        self.scene_table = QTableWidget(0, 5)
        self.scene_table.setHorizontalHeaderLabels(
            ["Cảnh", "Bắt đầu", "Kết thúc", "Thời lượng", "Nội dung phụ đề"]
        )
        self.scene_table.horizontalHeader().setStretchLastSection(True)
        self.scene_table.setColumnWidth(0, 55)
        self.scene_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        lay.addWidget(self.scene_table, 1)

        hint = QLabel(
            "Sau khi phân tích: xem lại bảng phân cảnh, chỉnh tham số nếu cần, "
            "rồi lưu scenes.json vào thư mục dự án để các bước sau dùng lại "
            "nội dung phụ đề và thời lượng mỗi cảnh."
        )
        hint.setWordWrap(True)
        lay.addWidget(hint)
        return w

    # ── Tab 2 ──
    def _tab_project(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        hint = QLabel(
            "Đặt ảnh line-art (PNG, nền #F5EBD7, không chữ) vào thư mục dự án "
            "theo quy ước tên: scene-01-<tên>.png, scene-02-<tên>.png …\n"
            "Mỗi ảnh cần một file cùng tên scene-01-<tên>.annotation.json."
        )
        hint.setWordWrap(True)
        lay.addWidget(hint)

        self.project_list = QListWidget()
        self.project_list.setIconSize(QSize(96, 54))
        lay.addWidget(self.project_list, 1)

        row = QHBoxLayout()
        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(self.refresh_project_list)
        btn_add = QPushButton("Thêm ảnh vào dự án…")
        btn_add.clicked.connect(self.add_images)
        btn_ann = QPushButton("Tạo annotation mẫu cho ảnh đang chọn")
        btn_ann.clicked.connect(self.make_sample_annotation)
        btn_prev = QPushButton("Mở bảng Preview (tab 3)")
        btn_prev.clicked.connect(lambda: self.show_preview_tab())
        row.addWidget(btn_refresh)
        row.addWidget(btn_add)
        row.addWidget(btn_ann)
        row.addWidget(btn_prev)
        row.addStretch(1)
        lay.addLayout(row)
        return w

    # ── Tab 3 ──
    def _tab_annotate(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        hint = QLabel(
            "Kéo khung để di chuyển, kéo 4 góc/4 cạnh để đổi cỡ vùng (<code>region</code>). "
            "Bên phải sửa chính xác toạ độ, hướng, <b>thời gian bắt đầu/kết thúc</b> và "
            "<b>phụ đề</b>; kéo danh sách khối để <b>đổi thứ tự vẽ</b>. Kéo thanh thời gian "
            "hoặc bấm phát để xem bản đại diện hình chữ nhật lộ dần (vùng chưa bắt đầu sẽ "
            "không hiện). Chỉnh xong nhớ bấm <b>Lưu cảnh này</b> / <b>Lưu tất cả</b>."
        )
        hint.setWordWrap(True)
        hint.setTextFormat(Qt.RichText)
        lay.addWidget(hint)

        self.preview_editor = preview_widget.PreviewEditor()
        self.preview_editor.scene_saved.connect(lambda _png: self.refresh_all_scene_lists())
        lay.addWidget(self.preview_editor, 1)

        row = QHBoxLayout()
        btn_regions = QPushButton("Xuất ảnh kiểm tra vùng (.regions.png)")
        btn_regions.clicked.connect(self.render_regions_preview)
        self.run_buttons.append(btn_regions)
        self.regions_view = QLabel()
        self.regions_view.setAlignment(Qt.AlignCenter)
        row.addWidget(btn_regions)
        row.addStretch(1)
        btn_browser = QPushButton("Mở trong trình duyệt (preview.html)")
        btn_browser.clicked.connect(self.open_preview_browser)
        row.addWidget(btn_browser)
        lay.addLayout(row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.regions_view)
        scroll.setMaximumHeight(160)
        scroll.setVisible(False)
        self._regions_scroll = scroll
        lay.addWidget(scroll)
        return w

    # ── Tab 4 ──
    def _tab_render(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        row = QHBoxLayout()
        self.render_combo = QComboBox()
        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(self.refresh_render_combo)
        row.addWidget(QLabel("Cảnh:"))
        row.addWidget(self.render_combo, 1)
        row.addWidget(btn_refresh)
        lay.addLayout(row)

        row2 = QHBoxLayout()
        self.cb_ink = QComboBox()
        self.cb_ink.addItems(["grid", "skeleton"])
        self.cb_fill = QComboBox()
        self.cb_fill.addItems(["contour-wipe", "brush"])
        self.sp_cap = QSpinBox()
        self.sp_cap.setRange(480, 2160)
        self.sp_cap.setSingleStep(120)
        self.sp_cap.setValue(1080)
        self.sp_total = QSpinBox()
        self.sp_total.setRange(0, 600000)
        self.sp_total.setSingleStep(500)
        self.sp_total.setValue(0)
        self.sp_total.setSpecialValueText("tự động")
        row2.addWidget(QLabel("Nét vẽ:"))
        row2.addWidget(self.cb_ink)
        row2.addWidget(QLabel("Tô màu:"))
        row2.addWidget(self.cb_fill)
        row2.addWidget(QLabel("Cạnh dài (px):"))
        row2.addWidget(self.sp_cap)
        row2.addWidget(QLabel("Tổng thời lượng (ms):"))
        row2.addWidget(self.sp_total)
        row2.addStretch(1)
        lay.addLayout(row2)

        row3 = QHBoxLayout()
        btn_one = QPushButton("Render cảnh này")
        btn_one.clicked.connect(self.render_one)
        self.run_buttons.append(btn_one)
        btn_all = QPushButton("Render tất cả cảnh")
        btn_all.clicked.connect(self.render_all)
        self.run_buttons.append(btn_all)
        btn_open = QPushButton("▶ Mở video cảnh này")
        btn_open.clicked.connect(self.open_scene_video)
        row3.addWidget(btn_one)
        row3.addWidget(btn_all)
        row3.addWidget(btn_open)
        row3.addStretch(1)
        lay.addLayout(row3)

        hint = QLabel(
            "Nét vẽ: grid ổn định cho mọi ảnh; skeleton bám sát line-art sạch. "
            "Tô màu: contour-wipe quét theo đường viền (mặc định); brush tô "
            "dọc quỹ đạo nét. Giảm \"Cạnh dài\" xuống 720 để render nháp nhanh. "
            "Video xuất ra: <thư mục dự án>/<tên cảnh>-whiteboard.mp4"
        )
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch(1)
        return w

    # ── Tab 5 ──
    def _tab_merge(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        lay.addWidget(QLabel(
            "Danh sách video *-whiteboard.mp4 trong dự án. Kéo để sắp xếp thứ "
            "tự ghép (trên xuống dưới)."
        ))
        self.merge_list = QListWidget()
        self.merge_list.setDragDropMode(QAbstractItemView.InternalMove)
        lay.addWidget(self.merge_list, 1)

        row = QHBoxLayout()
        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(self.refresh_merge_list)
        row.addWidget(btn_refresh)
        row.addWidget(QLabel("Tên file kết quả:"))
        self.merge_out = QLineEdit("final.mp4")
        row.addWidget(self.merge_out, 1)
        btn_merge = QPushButton("Ghép video")
        btn_merge.clicked.connect(self.run_merge)
        self.run_buttons.append(btn_merge)
        btn_open = QPushButton("▶ Mở kết quả")
        btn_open.clicked.connect(self.open_merged_video)
        row.addWidget(btn_merge)
        row.addWidget(btn_open)
        lay.addLayout(row)
        return w

    # ── Tab 6: âm thanh & phụ đề ──
    def _tab_audio(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        lay.addWidget(QLabel(
            "Renderer xuất video im lặng, không chữ. Tab này dùng ffmpeg để "
            "ghép tiếng và/hoặc khắc phụ đề. Cần có ffmpeg trong PATH."
        ))

        row = QHBoxLayout()
        self.av_video = QComboBox()
        btn_ref = QPushButton("Làm mới")
        btn_ref.clicked.connect(self.refresh_av_videos)
        row.addWidget(QLabel("Video nguồn:"))
        row.addWidget(self.av_video, 1)
        row.addWidget(btn_ref)
        lay.addLayout(row)

        # ── âm thanh ──
        gb_a = QGroupBox("Âm thanh")
        la = QVBoxLayout(gb_a)
        r0 = QHBoxLayout()
        self.av_mode = QComboBox()
        self.av_mode.addItems([
            "(Không thêm tiếng)",
            "Một file cho cả video",
            "Mỗi cảnh một file",
            "Tạo bằng TTS (edge-tts)",
        ])
        self.av_mode.currentIndexChanged.connect(self._av_mode_changed)
        r0.addWidget(QLabel("Chế độ:"))
        r0.addWidget(self.av_mode, 1)
        la.addLayout(r0)

        # mode 1: một file
        self.av_file_row = QWidget()
        rf = QHBoxLayout(self.av_file_row)
        rf.setContentsMargins(0, 0, 0, 0)
        self.av_file = QLineEdit()
        self.av_file.setPlaceholderText("Chọn file mp3 / wav / m4a …")
        btn_af = QPushButton("Chọn…")
        btn_af.clicked.connect(self._pick_av_file)
        rf.addWidget(QLabel("File:"))
        rf.addWidget(self.av_file, 1)
        rf.addWidget(btn_af)
        la.addWidget(self.av_file_row)

        # mode 2: mỗi cảnh một file
        self.av_scene_box = QWidget()
        rs = QVBoxLayout(self.av_scene_box)
        rs.setContentsMargins(0, 0, 0, 0)
        self.av_table = QTableWidget(0, 3)
        self.av_table.setHorizontalHeaderLabels(["Cảnh", "Mốc (s)", "File âm thanh"])
        self.av_table.horizontalHeader().setStretchLastSection(True)
        self.av_table.setColumnWidth(0, 160)
        self.av_table.setColumnWidth(1, 70)
        self.av_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.av_table.setMaximumHeight(160)
        rs.addWidget(self.av_table)
        btn_pick_scene = QPushButton("Chọn file cho dòng đang chọn…")
        btn_pick_scene.clicked.connect(self._pick_av_scene_file)
        rs.addWidget(btn_pick_scene)
        la.addWidget(self.av_scene_box)

        # mode 3: TTS
        self.av_tts_row = QWidget()
        rt = QHBoxLayout(self.av_tts_row)
        rt.setContentsMargins(0, 0, 0, 0)
        self.av_voice = QComboBox()
        self.av_voice.addItems(["vi-VN-HoaiMyNeural (nữ)", "vi-VN-NamMinhNeural (nam)"])
        self.av_tts_group = QComboBox()
        self.av_tts_group.addItems(["theo câu phụ đề", "theo cảnh"])
        rt.addWidget(QLabel("Giọng:"))
        rt.addWidget(self.av_voice)
        rt.addWidget(QLabel("Đọc:"))
        rt.addWidget(self.av_tts_group)
        rt.addStretch(1)
        la.addWidget(self.av_tts_row)
        lay.addWidget(gb_a)

        # ── phụ đề ──
        gb_s = QGroupBox("Phụ đề")
        ls = QVBoxLayout(gb_s)
        self.av_burn = QCheckBox("Khắc phụ đề từ file .srt lên video")
        ls.addWidget(self.av_burn)
        r1 = QHBoxLayout()
        self.av_srt = QLineEdit()
        self.av_srt.setPlaceholderText("Chọn file .srt (mốc thời gian của cả video)…")
        btn_srt = QPushButton("Chọn…")
        btn_srt.clicked.connect(self._pick_av_srt)
        r1.addWidget(QLabel("SRT:"))
        r1.addWidget(self.av_srt, 1)
        r1.addWidget(btn_srt)
        ls.addLayout(r1)
        r2 = QHBoxLayout()
        self.av_fontsize = QSpinBox()
        self.av_fontsize.setRange(10, 60)
        self.av_fontsize.setValue(20)
        self.av_marginv = QSpinBox()
        self.av_marginv.setRange(0, 300)
        self.av_marginv.setValue(46)
        r2.addWidget(QLabel("Cỡ chữ:"))
        r2.addWidget(self.av_fontsize)
        r2.addWidget(QLabel("Lề dưới (px):"))
        r2.addWidget(self.av_marginv)
        r2.addStretch(1)
        ls.addLayout(r2)
        lay.addWidget(gb_s)

        r3 = QHBoxLayout()
        r3.addWidget(QLabel("Tên file kết quả:"))
        self.av_out = QLineEdit("video-av.mp4")
        r3.addWidget(self.av_out, 1)
        btn_go = QPushButton("Xử lý")
        btn_go.clicked.connect(self.run_postprocess)
        self.run_buttons.append(btn_go)
        btn_open = QPushButton("▶ Mở kết quả")
        btn_open.clicked.connect(self._open_av_result)
        r3.addWidget(btn_go)
        r3.addWidget(btn_open)
        lay.addLayout(r3)
        lay.addStretch(1)

        self._av_mode_changed()
        return w

    # ── log panel ──
    def _build_log_panel(self) -> QWidget:
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)

        row = QHBoxLayout()
        self.status_label = QLabel("Sẵn sàng.")
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        btn_stop = QPushButton("Dừng tác vụ")
        btn_stop.clicked.connect(self.stop_worker)
        btn_toggle_log = QPushButton("▸  Nhật ký")
        btn_toggle_log.setCheckable(True)
        btn_toggle_log.setCursor(Qt.PointingHandCursor)
        btn_toggle_log.setStyleSheet(
            "QPushButton{text-align:left; border:none; background:transparent;}"
            "QPushButton:hover{background:#1c1f26;}"
        )
        row.addWidget(self.status_label, 1)
        row.addWidget(self.progress, 1)
        row.addWidget(btn_stop)
        row.addWidget(btn_toggle_log)
        outer.addLayout(row)

        log_box = QWidget()
        log_lay = QVBoxLayout(log_box)
        log_lay.setContentsMargins(0, 4, 0, 0)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(6000)
        self.log.setStyleSheet("font-family: Consolas, 'Courier New', monospace;")
        self.log.setMinimumHeight(180)
        log_lay.addWidget(self.log)
        clear_row = QHBoxLayout()
        btn_clear = QPushButton("Xóa nhật ký")
        btn_clear.clicked.connect(self.log.clear)
        clear_row.addStretch(1)
        clear_row.addWidget(btn_clear)
        log_lay.addLayout(clear_row)
        log_box.setVisible(False)

        def _toggle_log(checked: bool) -> None:
            log_box.setVisible(checked)
            btn_toggle_log.setText(("▾  " if checked else "▸  ") + "Nhật ký")

        btn_toggle_log.toggled.connect(_toggle_log)
        outer.addWidget(log_box)
        return container

    # ──────────────────────────────────────────────────────
    # Tiện ích chung
    # ──────────────────────────────────────────────────────
    def append_log(self, text: str) -> None:
        self.log.appendPlainText(text)
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def warn(self, msg: str) -> None:
        QMessageBox.warning(self, "Chú ý", msg)

    def _refresh_env_label(self) -> None:
        if self.env_py:
            self.env_label.setText(f"✔ Môi trường sẵn sàng: {self.env_py}")
        else:
            self.env_label.setText(
                "✘ Chưa có môi trường render. Bấm \"Chuẩn bị / kiểm tra môi "
                "trường\" (cài opencv-python, numpy, av, Pillow vào .venv)."
            )

    def require_env(self) -> bool:
        if not self.env_py:
            self.warn("Chưa chuẩn bị môi trường render. Bấm nút \"Chuẩn bị / "
                      "kiểm tra môi trường\" ở trên trước.")
            return False
        return True

    def require_project(self) -> bool:
        if not self.project:
            self.warn("Chưa chọn thư mục dự án.")
            return False
        return True

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.progress.setRange(0, 0 if busy else 1)
        if not busy:
            self.progress.setValue(0)
        for b in self.run_buttons:
            b.setEnabled(not busy)
        self.status_label.setText("Đang chạy…" if busy else "Sẵn sàng.")

    def run_jobs(self, jobs: list[tuple[str, list[str]]], done_cb=None,
                 progress_cb=None) -> None:
        if self._busy:
            self.warn("Đang có tác vụ chạy. Vui lòng đợi hoặc bấm \"Dừng tác vụ\".")
            return
        if not jobs:
            return
        self.set_busy(True)
        self.worker = CommandWorker(jobs, str(SKILL_ROOT))
        self.worker.line.connect(self.append_log)
        completed = 0

        def _job_done(label: str, rc: int) -> None:
            nonlocal completed
            completed += 1
            self.append_log(f"[{'OK' if rc == 0 else 'LỖI (' + str(rc) + ')'}] {label}")
            if progress_cb:
                progress_cb(completed, len(jobs))

        self.worker.job_done.connect(_job_done)

        def _finish():
            self.set_busy(False)
            self.append_log("— xong —")
            if done_cb:
                done_cb()

        self.worker.all_done.connect(_finish)
        self.worker.start()

    def stop_worker(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.append_log("[..] Đã yêu cầu dừng, đang kết thúc tiến trình…")

    # ──────────────────────────────────────────────────────
    # Môi trường & dự án
    # ──────────────────────────────────────────────────────
    def prepare_env(self) -> None:
        self.append_log("$ chuẩn bị môi trường (.venv)…")

        def done():
            self.env_py = detect_env_py()
            self._refresh_env_label()

        self.run_jobs(
            [("prepare_env", [sys.executable, str(SCRIPTS / "prepare_env.py")])],
            done_cb=done,
        )

    def pick_project(self) -> None:
        start = str(self.project or DEFAULT_PROJECT_ROOT if
                    (self.project or DEFAULT_PROJECT_ROOT).exists() else SKILL_ROOT)
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục dự án", start)
        if d:
            self.set_project(Path(d))

    def new_project(self) -> None:
        DEFAULT_PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
        d = QFileDialog.getSaveFileName(
            self, "Đặt tên thư mục dự án mới",
            str(DEFAULT_PROJECT_ROOT / "du-an-moi"),
        )[0]
        if not d:
            return
        p = Path(d)
        p.mkdir(parents=True, exist_ok=True)
        self.set_project(p)

    def set_project(self, p: Path) -> None:
        self.project = p
        self.project_edit.setText(str(p))
        self.settings.setValue("project", str(p))
        default_out = f"{p.name}-final.mp4"
        if self.merge_out.text() in ("", "final.mp4"):
            self.merge_out.setText(default_out)
        scenes_json = p / "scenes.json"
        if scenes_json.exists() and not self.scenes:
            try:
                data = json.loads(scenes_json.read_text(encoding="utf-8"))
                self.parsed = data
                self.scenes = data.get("scenes", [])
                self.populate_scene_table()
                self.append_log(f"[ok] Đã nạp {scenes_json}")
            except Exception as exc:  # noqa: BLE001
                self.append_log(f"[cảnh báo] Không đọc được scenes.json: {exc}")
        self.preview_editor.set_project(p)
        self._fast_preload_result(p)
        self._auto_annotate_missing()
        self.refresh_all_scene_lists()
        if hasattr(self, "_quick_img_section_header"):
            self._quick_img_section_header.setChecked(True)

    # ──────────────────────────────────────────────────────
    # Tab 1
    # ──────────────────────────────────────────────────────
    def pick_srt(self) -> None:
        start = self.srt_edit.text() or str(SKILL_ROOT)
        f = QFileDialog.getOpenFileName(
            self, "Chọn file SRT", start, "Phụ đề (*.srt);;Tất cả (*.*)"
        )[0]
        if f:
            self._set_srt_path(f)
            if not self.av_srt.text():
                self.av_srt.setText(f)

    def run_parse(self) -> None:
        if not self._ensure_srt_saved():
            return
        srt = self.srt_edit.text().strip()
        if not srt or not Path(srt).exists():
            self.warn("Chưa chọn file .srt hợp lệ.")
            return
        py = self.env_py or sys.executable
        argv = [
            py, str(SCRIPTS / "parse_srt.py"), srt,
            "--target-sec", str(self.sp_target.value()),
            "--min-sec", str(self.sp_min.value()),
            "--max-sec", str(self.sp_max.value()),
        ]
        self.append_log("$ " + subprocess.list2cmdline(argv))
        try:
            res = subprocess.run(
                argv, capture_output=True, text=True, encoding="utf-8",
                errors="replace", creationflags=NO_WINDOW, env=utf8_env(),
            )
        except Exception as exc:  # noqa: BLE001
            self.warn(f"Không chạy được parse_srt.py: {exc}")
            return
        if res.stderr.strip():
            self.append_log(res.stderr.strip())
        if res.returncode != 0:
            self.warn("parse_srt.py báo lỗi. Xem nhật ký.")
            return
        try:
            data = json.loads(res.stdout)
        except json.JSONDecodeError as exc:
            self.warn(f"Không đọc được kết quả JSON: {exc}")
            return
        self.parsed = data
        self.scenes = data.get("scenes", [])
        self.populate_scene_table()
        self.append_log(
            f"[ok] {len(data.get('cues', []))} dòng phụ đề, "
            f"{len(self.scenes)} cảnh đề xuất."
        )

    def populate_scene_table(self) -> None:
        self.scene_table.setRowCount(len(self.scenes))
        for i, sc in enumerate(self.scenes):
            dur = sc.get("sceneDurationMs", 0)
            vals = [
                str(sc.get("sceneIndex", i + 1)),
                fmt_ms(sc.get("startMs", 0)),
                fmt_ms(sc.get("endMs", 0)),
                f"{dur / 1000:.1f}s",
                sc.get("text", ""),
            ]
            for c, v in enumerate(vals):
                self.scene_table.setItem(i, c, QTableWidgetItem(v))

    def save_scenes_json(self) -> None:
        if not self.require_project():
            return
        if not self.parsed:
            self.warn("Chưa có kết quả phân tích để lưu.")
            return
        out = self.project / "scenes.json"
        out.write_text(
            json.dumps(self.parsed, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.append_log(f"[ok] Đã lưu {out}")
        self.warn(f"Đã lưu:\n{out}")

    # ──────────────────────────────────────────────────────
    # Tab 2
    # ──────────────────────────────────────────────────────
    def refresh_project_list(self) -> None:
        self.project_list.clear()
        if not self.project:
            return
        pngs = list_scene_pngs(self.project)
        if not pngs:
            self.project_list.addItem("(Chưa có ảnh .png nào trong thư mục dự án)")
            return
        for p in pngs:
            ann = p.with_suffix(".annotation.json")
            mp4 = p.with_name(p.stem + "-whiteboard.mp4")
            marks = []
            marks.append("✔ annotation" if ann.exists() else "✘ annotation")
            if mp4.exists():
                marks.append("✔ video")
            item = QListWidgetItem(f"{p.name}   [{'  '.join(marks)}]")
            item.setData(Qt.UserRole, str(p))
            pix = QPixmap(str(p))
            if not pix.isNull():
                item.setIcon(QIcon(pix.scaled(
                    96, 54, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )))
            self.project_list.addItem(item)

    def add_images(self) -> None:
        if not self.require_project():
            return
        files = QFileDialog.getOpenFileNames(
            self, "Chọn ảnh line-art (PNG)", str(SKILL_ROOT), "Ảnh (*.png)"
        )[0]
        import shutil
        for f in files:
            dst = self.project / Path(f).name
            if Path(f).resolve() != dst.resolve():
                shutil.copy2(f, dst)
                self.append_log(f"[ok] Đã sao chép {dst.name}")
        self.refresh_all_scene_lists()

    def _selected_project_png(self) -> Path | None:
        item = self.project_list.currentItem()
        if not item or not item.data(Qt.UserRole):
            return None
        return Path(item.data(Qt.UserRole))

    def make_sample_annotation(self) -> None:
        if not self.require_project():
            return
        png = self._selected_project_png()
        if not png:
            self.warn("Chọn một ảnh .png trong danh sách trước.")
            return
        ann_path = png.with_suffix(".annotation.json")
        if ann_path.exists():
            if QMessageBox.question(
                self, "Ghi đè?",
                f"{ann_path.name} đã tồn tại. Ghi đè bằng mẫu mới?",
            ) != QMessageBox.Yes:
                return
        pngs = list_scene_pngs(self.project)
        idx = pngs.index(png) if png in pngs else 0
        ann = build_sample_annotation(png, idx, self.scenes)
        if ann is None:
            self.warn("Không đọc được ảnh.")
            return
        ann_path.write_text(
            json.dumps(ann, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        w, h = ann["canvas"]["width"], ann["canvas"]["height"]
        self.append_log(f"[ok] Đã tạo {ann_path.name} ({w}×{h})")
        self.refresh_all_scene_lists()
        if QMessageBox.question(
            self, "Mở Preview?",
            "Đã tạo annotation mẫu (1 vùng phủ toàn ảnh).\n"
            "Mở tab Chú thích & Preview để chia vùng và chỉnh thời gian?",
        ) == QMessageBox.Yes:
            self.show_preview_tab(png)

    def _auto_annotate(self, png: Path, idx: int) -> bool:
        """Tự tạo annotation mẫu cho ảnh chưa có — dùng trong luồng 1-click."""
        ann = build_sample_annotation(png, idx, self.scenes)
        if ann is None:
            self.append_log(
                f"[LỖI] Không đọc được ảnh {png.name} (file hỏng hoặc định "
                "dạng không hỗ trợ) — chưa tạo được annotation cho ảnh này."
            )
            return False
        png.with_suffix(".annotation.json").write_text(
            json.dumps(ann, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True

    # ──────────────────────────────────────────────────────
    # Bảng chỉnh vùng vẽ / thứ tự / thời gian (mở ở cửa sổ riêng)
    # ──────────────────────────────────────────────────────
    def _build_preview_dialog(self) -> None:
        """Tách bảng Preview ra một cửa sổ riêng (không phải tab) — mở khi
        bấm vào một ảnh trong timeline ở tab ⚡ Nhanh. Đóng cửa sổ (nút Đóng,
        phím Esc, nút X) tự lưu thay đổi; nút Huỷ đóng mà không lưu."""
        dlg = _PreviewDialog(self, self._on_preview_dialog_closed)
        dlg.setWindowTitle("Chỉnh vùng vẽ · thứ tự · thời gian")
        dlg.resize(1080, 760)
        lay = QVBoxLayout(dlg)
        lay.addWidget(self.preview_editor, 1)
        row = QHBoxLayout()
        hint = QLabel("Đóng cửa sổ sẽ tự lưu thay đổi.")
        hint.setStyleSheet("color:#8b929c; font-size:11px;")
        row.addWidget(hint)
        row.addStretch(1)
        btn_cancel = QPushButton("Huỷ")
        btn_cancel.setToolTip("Đóng mà không lưu các thay đổi chưa lưu.")
        btn_cancel.clicked.connect(lambda: self._close_preview_dialog(discard=True))
        btn_close = QPushButton("Đóng")
        btn_close.setDefault(True)
        btn_close.clicked.connect(lambda: self._close_preview_dialog(discard=False))
        row.addWidget(btn_cancel)
        row.addWidget(btn_close)
        lay.addLayout(row)
        self._preview_dialog = dlg

    def _close_preview_dialog(self, discard: bool) -> None:
        self._preview_dialog.discard_next_close = discard
        self._preview_dialog.close()

    def _on_preview_dialog_closed(self, discard: bool) -> None:
        if discard:
            if self.preview_editor.has_unsaved():
                self.preview_editor.discard_unsaved()
        else:
            self.preview_editor.save_all_dirty()
        self.refresh_all_scene_lists()
        if self.quick_timeline.project == self.project:
            self.quick_timeline.reload(self.project)

    def show_preview_tab(self, png: Path | None = None) -> None:
        """Mở bảng Preview (cửa sổ riêng) và chọn đúng ảnh vừa bấm vào."""
        self.preview_editor.reload_project()
        if png:
            self.preview_editor.select_scene_by_name(png.stem)
        self._preview_dialog.show()
        self._preview_dialog.raise_()
        self._preview_dialog.activateWindow()

    def _open_quick_preview(self) -> None:
        """Mở cửa sổ "Xem nhanh" — mô phỏng hiệu ứng lộ dần ngay trong app,
        không cần đợi render video thật (xem quick_preview.py)."""
        if not self.project or not list_scene_pngs(self.project):
            self.warn("Chưa có ảnh nào để xem thử — chọn ảnh ở mục 1 trước.")
            return
        if not hasattr(self, "_quick_preview_dialog"):
            self._quick_preview_dialog = quick_preview.QuickPreviewDialog(self)
        self._quick_preview_dialog.reload(self.project, self._quick_audio_path)
        self._quick_preview_dialog.show()
        self._quick_preview_dialog.raise_()
        self._quick_preview_dialog.activateWindow()

    def open_preview_browser(self) -> None:
        """Dự phòng: mở bản preview.html chạy trong trình duyệt (Chrome/Edge)."""
        if not PREVIEW_HTML.exists():
            self.warn(f"Không tìm thấy {PREVIEW_HTML}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(PREVIEW_HTML)))
        if self.project:
            self.append_log(
                f"[..] Đã mở preview.html. Bấm \"Mở thư mục\" và chọn: {self.project}"
            )

    def _annotated_pngs(self) -> list[Path]:
        if not self.project:
            return []
        return [
            p for p in list_scene_pngs(self.project)
            if p.with_suffix(".annotation.json").exists()
        ]

    def render_regions_preview(self) -> None:
        if not self.require_env() or not self.require_project():
            return
        png = self.preview_editor.current_scene_png()
        ann = png.with_suffix(".annotation.json") if png else None
        if not png or not ann or not ann.exists():
            self.warn("Chọn một cảnh đã có annotation.json ở bảng Preview phía trên.")
            return
        out = png.with_name(png.stem + ".regions.png")
        argv = [
            self.env_py, str(SCRIPTS / "render_annotation_preview.py"),
            str(png), str(ann), str(out),
        ]

        def done():
            if out.exists():
                pix = QPixmap(str(out))
                self.regions_view.setPixmap(pix)
                self.regions_view.resize(pix.size())
                self._regions_scroll.setVisible(True)
                self.append_log(f"[ok] {out.name}")

        self.run_jobs([(f"regions:{png.name}", argv)], done_cb=done)

    # ──────────────────────────────────────────────────────
    # Tab 4
    # ──────────────────────────────────────────────────────
    def _render_ready_pngs(self) -> list[Path]:
        return self._annotated_pngs()

    def refresh_render_combo(self) -> None:
        cur = self.render_combo.currentText()
        self.render_combo.clear()
        for p in self._render_ready_pngs():
            self.render_combo.addItem(p.name, str(p))
        i = self.render_combo.findText(cur)
        if i >= 0:
            self.render_combo.setCurrentIndex(i)

    def _render_job(self, png: Path) -> tuple[str, list[str]]:
        ann = png.with_suffix(".annotation.json")
        out = png.with_name(png.stem + "-whiteboard.mp4")
        argv = [
            self.env_py, str(SCRIPTS / "render_stream_whiteboard.py"),
            str(png), str(ann), str(out), str(HAND_PNG),
            "--ink-path", self.cb_ink.currentText(),
            "--color-fill", self.cb_fill.currentText(),
            "--cap-long-edge", str(self.sp_cap.value()),
        ]
        if self.sp_total.value() > 0:
            argv += ["--total-ms", str(self.sp_total.value())]
        return (f"render:{png.name}", argv)

    def render_one(self) -> None:
        if not self.require_env() or not self.require_project():
            return
        path = self.render_combo.currentData()
        if not path:
            self.warn("Chọn một cảnh đã có annotation.json.")
            return
        self.run_jobs([self._render_job(Path(path))],
                      done_cb=self.refresh_all_scene_lists)

    def render_all(self) -> None:
        if not self.require_env() or not self.require_project():
            return
        pngs = self._render_ready_pngs()
        if not pngs:
            self.warn("Không có cảnh nào đủ điều kiện (cần PNG + annotation.json).")
            return
        self.run_jobs([self._render_job(p) for p in pngs],
                      done_cb=self.refresh_all_scene_lists)

    def open_scene_video(self) -> None:
        path = self.render_combo.currentData()
        if not path:
            return
        mp4 = Path(path).with_name(Path(path).stem + "-whiteboard.mp4")
        if not mp4.exists():
            self.warn(f"Chưa có video: {mp4.name}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(mp4)))

    # ──────────────────────────────────────────────────────
    # Tab 5
    # ──────────────────────────────────────────────────────
    def refresh_merge_list(self) -> None:
        existing = [
            self.merge_list.item(i).data(Qt.UserRole)
            for i in range(self.merge_list.count())
        ]
        self.merge_list.clear()
        if not self.project:
            return
        found = sorted(self.project.glob("*-whiteboard.mp4"))
        ordered = [Path(p) for p in existing if Path(p) in found]
        ordered += [p for p in found if p not in ordered]
        for p in ordered:
            item = QListWidgetItem(p.name)
            item.setData(Qt.UserRole, str(p))
            self.merge_list.addItem(item)

    def run_merge(self) -> None:
        if not self.require_env() or not self.require_project():
            return
        inputs = [
            self.merge_list.item(i).data(Qt.UserRole)
            for i in range(self.merge_list.count())
        ]
        if len(inputs) < 2:
            self.warn("Cần ít nhất 2 video để ghép.")
            return
        out_name = self.merge_out.text().strip() or f"{self.project.name}-final.mp4"
        out = self.project / out_name
        argv = [
            self.env_py, str(SCRIPTS / "merge_scenes.py"),
            "--inputs", *inputs, "--output", str(out),
        ]
        self.run_jobs([(f"merge -> {out_name}", argv)])

    def open_merged_video(self) -> None:
        if not self.project:
            return
        out_name = self.merge_out.text().strip() or f"{self.project.name}-final.mp4"
        out = self.project / out_name
        if not out.exists():
            self.warn(f"Chưa có file: {out.name}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(out)))

    # ──────────────────────────────────────────────────────
    # Tab 6 — âm thanh & phụ đề
    # ──────────────────────────────────────────────────────
    def _av_mode_changed(self) -> None:
        i = self.av_mode.currentIndex()
        self.av_file_row.setVisible(i == 1)
        self.av_scene_box.setVisible(i == 2)
        self.av_tts_row.setVisible(i == 3)
        if i == 2:
            self._populate_av_table()

    def refresh_av_videos(self) -> None:
        cur = self.av_video.currentText()
        self.av_video.clear()
        if not self.project:
            return
        vids = sorted(
            (p for p in self.project.glob("*.mp4") if "_raw" not in p.stem),
            key=lambda p: (0 if "final" in p.stem else 1, p.name),
        )
        for p in vids:
            self.av_video.addItem(p.name, str(p))
        j = self.av_video.findText(cur)
        if j >= 0:
            self.av_video.setCurrentIndex(j)
        if not self.av_srt.text() and self.srt_edit.text():
            self.av_srt.setText(self.srt_edit.text())

    def _populate_av_table(self) -> None:
        pngs = list_scene_pngs(self.project) if self.project else []
        keep = {}
        for r in range(self.av_table.rowCount()):
            it = self.av_table.item(r, 2)
            if it and it.data(Qt.UserRole):
                keep[self.av_table.item(r, 0).text()] = it.data(Qt.UserRole)
        self.av_table.setRowCount(len(pngs))
        for r, png in enumerate(pngs):
            start = self.scenes[r]["startMs"] if r < len(self.scenes) else 0
            self.av_table.setItem(r, 0, QTableWidgetItem(png.stem))
            self.av_table.setItem(r, 1, QTableWidgetItem(f"{start / 1000:.1f}"))
            cell = QTableWidgetItem(Path(keep[png.stem]).name if png.stem in keep else "—")
            if png.stem in keep:
                cell.setData(Qt.UserRole, keep[png.stem])
            self.av_table.setItem(r, 2, cell)

    def _pick_av_file(self) -> None:
        f = QFileDialog.getOpenFileName(
            self, "Chọn file âm thanh", str(self.project or SKILL_ROOT),
            "Âm thanh (*.mp3 *.wav *.m4a *.aac *.ogg *.flac);;Tất cả (*.*)",
        )[0]
        if f:
            self.av_file.setText(f)

    def _pick_av_scene_file(self) -> None:
        r = self.av_table.currentRow()
        if r < 0:
            self.warn("Chọn một dòng cảnh trong bảng trước.")
            return
        f = QFileDialog.getOpenFileName(
            self, f"Âm thanh cho {self.av_table.item(r, 0).text()}",
            str(self.project or SKILL_ROOT),
            "Âm thanh (*.mp3 *.wav *.m4a *.aac *.ogg *.flac);;Tất cả (*.*)",
        )[0]
        if f:
            cell = QTableWidgetItem(Path(f).name)
            cell.setData(Qt.UserRole, f)
            self.av_table.setItem(r, 2, cell)

    def _pick_av_srt(self) -> None:
        f = QFileDialog.getOpenFileName(
            self, "Chọn file SRT", str(self.project or SKILL_ROOT),
            "Phụ đề (*.srt);;Tất cả (*.*)",
        )[0]
        if f:
            self.av_srt.setText(f)

    def _av_output_path(self) -> Path | None:
        if not self.project:
            return None
        name = self.av_out.text().strip() or "video-av.mp4"
        if not name.lower().endswith(".mp4"):
            name += ".mp4"
        return self.project / name

    def run_postprocess(self) -> None:
        if not self.require_env() or not self.require_project():
            return
        if shutil.which("ffmpeg") is None:
            self.warn("Không tìm thấy ffmpeg trong PATH. Cài ffmpeg (bản có "
                      "libass) rồi thử lại.")
            return
        src = self.av_video.currentData()
        if not src or not Path(src).exists():
            self.warn("Chọn video nguồn (bấm Làm mới nếu danh sách trống).")
            return
        out = self._av_output_path()
        if Path(src).resolve() == out.resolve():
            self.warn("Tên file kết quả trùng video nguồn. Đổi tên khác.")
            return

        argv = [self.env_py, str(SCRIPTS / "postprocess_video.py"),
                "--video", src, "--output", str(out)]
        mode = self.av_mode.currentIndex()
        pre_jobs: list[tuple[str, list[str]]] = []

        if mode == 1:
            if not self.av_file.text() or not Path(self.av_file.text()).exists():
                self.warn("Chọn file âm thanh.")
                return
            argv += ["--audio-file", self.av_file.text()]
        elif mode == 2:
            clips = []
            for r in range(self.av_table.rowCount()):
                it = self.av_table.item(r, 2)
                if it and it.data(Qt.UserRole):
                    ms = int(float(self.av_table.item(r, 1).text()) * 1000)
                    clips.append(f"{ms}={it.data(Qt.UserRole)}")
            if not clips:
                self.warn("Chưa gán file âm thanh cho cảnh nào.")
                return
            argv += ["--audio-clip", *clips]
        elif mode == 3:
            srt = self.av_srt.text().strip()
            if not srt or not Path(srt).exists():
                self.warn("TTS cần file .srt (ô SRT ở phần Phụ đề).")
                return
            voice = self.av_voice.currentText().split()[0]
            group = "scene" if self.av_tts_group.currentIndex() == 1 else "cue"
            argv += ["--tts-srt", srt, "--tts-voice", voice, "--tts-group", group]
            if group == "scene":
                sc = self.project / "scenes.json"
                if not sc.exists():
                    self.warn("Đọc theo cảnh cần scenes.json (tab 1 → Lưu "
                              "scenes.json vào dự án).")
                    return
                argv += ["--scenes", str(sc)]
            if not _can_import(self.env_py, "edge_tts"):
                pre_jobs.append(("cài edge-tts", [
                    self.env_py, "-m", "pip", "install", "--quiet", "edge-tts"
                ]))

        if self.av_burn.isChecked():
            srt = self.av_srt.text().strip()
            if not srt or not Path(srt).exists():
                self.warn("Khắc phụ đề cần file .srt hợp lệ.")
                return
            argv += ["--burn-srt", srt,
                     "--sub-fontsize", str(self.av_fontsize.value()),
                     "--sub-margin-v", str(self.av_marginv.value())]
        elif mode == 0:
            self.warn("Chưa chọn gì để làm: bật khắc phụ đề hoặc chọn chế độ "
                      "âm thanh.")
            return

        self.run_jobs(pre_jobs + [(f"hậu kỳ -> {out.name}", argv)],
                      done_cb=self.refresh_all_scene_lists)

    def _open_av_result(self) -> None:
        out = self._av_output_path()
        if not out or not out.exists():
            self.warn("Chưa có file kết quả.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(out)))

    # ──────────────────────────────────────────────────────
    def refresh_all_scene_lists(self) -> None:
        self.refresh_project_list()
        self.refresh_render_combo()
        self.refresh_merge_list()
        self.refresh_av_videos()
        if self.av_mode.currentIndex() == 2:
            self._populate_av_table()
        self._update_quick_labels()

    def open_guide(self) -> None:
        if GUIDE.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(GUIDE)))
        else:
            self.warn(f"Không tìm thấy {GUIDE}")

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.preview_editor.has_unsaved():
            if QMessageBox.question(
                self, "Chưa lưu",
                "Có chỉnh sửa annotation chưa lưu ở tab Chú thích & Preview.\n"
                "Đóng app và bỏ qua các thay đổi đó?",
            ) != QMessageBox.Yes:
                event.ignore()
                return
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("SRT Whiteboard Studio")
    win = Studio()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
