#!/usr/bin/env python3
"""
Bảng Preview nhúng trực tiếp trong app (thay cho assets/preview.html mở
trình duyệt): xem và chỉnh vùng (`region`), thứ tự vẽ (`sequence`), thời gian
(`startMs`/`durationMs`) và phụ đề (`subtitle`) của từng khối trong file
`<tên>.annotation.json`, rồi lưu đè lại — mọi thao tác thực hiện ngay trong
cửa sổ Studio, không cần Chrome/Edge.

Logic "lộ dần theo khung chữ nhật" (mô phỏng thứ tự vẽ) được dựng lại tương
đương bản JS trong preview.html: mỗi khối được clip theo khung tiến độ, sau
đó các khối phía sau + protectedRegions của chính nó bị "khoét" trong suốt để
không lộ nét trước thời điểm.

Widget này độc lập với whiteboard_studio.py (không import ngược) — chỉ cần
gọi set_project() để nạp một thư mục dự án.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPlainTextEdit, QPushButton, QSizePolicy, QSlider,
    QSpinBox, QSplitter, QVBoxLayout, QWidget,
)

DIRECTIONS = [
    ("top_to_bottom", "Từ trên xuống"),
    ("bottom_to_top", "Từ dưới lên"),
    ("left_to_right", "Từ trái sang phải"),
    ("right_to_left", "Từ phải sang trái"),
]
PAPER_FALLBACK = QColor("#F5EBD7")
COLOR_FOCUS = QColor("#3b82f6")
COLOR_NORMAL = QColor("#e97036")


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def detect_regions(png: Path, max_regions: int = 10) -> list[dict]:
    """Tự dò các cụm nét vẽ tách biệt trong ảnh (so màu với nền giấy) để gợi
    ý vùng (`region`) ban đầu cho annotation — không hoàn hảo (vật thể nào
    chạm/gần nhau sẽ bị gộp làm một), chỉ là điểm khởi đầu để người dùng tự
    kéo chỉnh lại. Trả về list đã sắp trái→phải; rỗng nếu không dò được gì
    (ảnh trắng, thiếu OpenCV…) — khi đó bên gọi tự dùng phương án dự phòng.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        return []
    img = cv2.imread(str(png), cv2.IMREAD_COLOR)
    if img is None:
        return []
    h, w = img.shape[:2]
    if h < 10 or w < 10:
        return []

    pts = [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]
    paper = np.array([img[y, x] for x, y in pts], dtype=np.int32).mean(axis=0)
    diff = np.abs(img.astype(np.int16) - paper.astype(np.int16)).sum(axis=2)
    mask = (diff > 40).astype(np.uint8) * 255

    # Cắt bỏ các dòng/cột kẻ dài gần hết khung (chân trời, mặt đất…) để
    # chúng không nối liền các vật thể lẽ ra tách biệt thành một khối.
    row_sum = (mask > 0).sum(axis=1)
    mask[row_sum > w * 0.5, :] = 0
    col_sum = (mask > 0).sum(axis=0)
    mask[:, col_sum > h * 0.5] = 0

    num, _labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    min_area = w * h * 0.0008
    frags: list[list[int]] = []
    for i in range(1, num):
        x, y, bw, bh, area = stats[i]
        if area < min_area:
            continue
        frags.append([int(x), int(y), int(bw), int(bh), int(area)])
    if not frags:
        return []
    if len(frags) > 400:  # chặn bùng nổ O(n²) với ảnh quá nhiều chi tiết nhỏ
        frags.sort(key=lambda f: -f[4])
        frags = frags[:400]

    n = len(frags)
    gap = max(16, round(min(w, h) * 0.025))
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    changed = True
    while changed:
        changed = False
        for i in range(n):
            ax, ay, aw, ah, _ = frags[i]
            for j in range(i + 1, n):
                if find(i) == find(j):
                    continue
                bx, by, bw2, bh2, _ = frags[j]
                if not (bx + bw2 < ax - gap or bx > ax + aw + gap or
                        by + bh2 < ay - gap or by > ay + ah + gap):
                    union(i, j)
                    changed = True

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    regions = []
    for idxs in groups.values():
        x1 = min(frags[i][0] for i in idxs)
        y1 = min(frags[i][1] for i in idxs)
        x2 = max(frags[i][0] + frags[i][2] for i in idxs)
        y2 = max(frags[i][1] + frags[i][3] for i in idxs)
        regions.append({
            "x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1,
            "area": sum(frags[i][4] for i in idxs),
        })

    if len(regions) > max_regions:
        regions.sort(key=lambda r: -r["area"])
        regions = regions[:max_regions]

    regions.sort(key=lambda r: r["x"] + r["width"] / 2)
    return regions


_SCENE_IMAGE_GLOBS = ("*.png", "*.jpg", "*.jpeg")


def _list_scene_pngs(project: Path) -> list[Path]:
    if not project or not project.is_dir():
        return []
    out = []
    for pat in _SCENE_IMAGE_GLOBS:
        out += [p for p in project.glob(pat) if not p.name.endswith(".regions.png")]
    return sorted(out)


def _default_cfg(name: str, img: QImage) -> dict:
    return {
        "sceneId": name,
        "canvas": {"width": img.width(), "height": img.height()},
        "sceneDurationMs": 8000,
        "elements": [],
    }


def _load_cfg(png: Path, ann: Path, img: QImage) -> dict:
    cfg = None
    if ann.exists():
        try:
            cfg = json.loads(ann.read_text(encoding="utf-8"))
        except Exception:
            cfg = None
    if not isinstance(cfg, dict):
        cfg = _default_cfg(png.stem, img)
    if not isinstance(cfg.get("elements"), list):
        cfg["elements"] = []
    # canvas luôn khớp đúng kích thước pixel thật của ảnh (yêu cầu SKILL.md)
    cfg["canvas"] = {"width": img.width(), "height": img.height()}
    cfg.setdefault("sceneId", png.stem)
    cfg.setdefault("sceneDurationMs", 8000)
    for i, el in enumerate(cfg["elements"]):
        el.setdefault("id", el.get("label") or f"region_{i + 1}")
        el.setdefault("label", "")
        el.setdefault("subtitle", "")
        el.setdefault("narrativeRole", "")
        el.setdefault("type", "object")
        el.setdefault("sequence", i + 1)
        el.setdefault("region", {"x": 0, "y": 0, "width": 10, "height": 10})
        rev = el.setdefault("reveal", {})
        rev.setdefault("direction", "top_to_bottom")
        rev.setdefault("startMs", 0)
        rev.setdefault("durationMs", 1000)
        rev.setdefault("maskPaddingPx", 20)
        rev.setdefault("protectedRegions", [])
        el.setdefault("handPath", {})
    return cfg


def _sample_paper(img: QImage) -> QColor:
    try:
        w, h = img.width(), img.height()
        if w < 6 or h < 6:
            return QColor(PAPER_FALLBACK)
        pts = [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]
        r = g = b = 0
        for x, y in pts:
            c = img.pixelColor(x, y)
            r += c.red()
            g += c.green()
            b += c.blue()
        return QColor(r // 4, g // 4, b // 4)
    except Exception:
        return QColor(PAPER_FALLBACK)


def _end_ms(el: dict) -> float:
    rev = el["reveal"]
    return rev["startMs"] + rev["durationMs"]


def _total_ms(cfg: dict) -> float:
    elements = cfg.get("elements", [])
    max_end = max((_end_ms(e) for e in elements), default=0)
    return max(cfg.get("sceneDurationMs", 0), max_end + 500, 1000)


def _reveal_rect(el: dict, p: float) -> tuple[float, float, float, float]:
    r = el["region"]
    x, y, w, h = r["x"], r["y"], r["width"], r["height"]
    d = el["reveal"]["direction"]
    if d == "left_to_right":
        return x, y, x + w * p, y + h
    if d == "right_to_left":
        return x + w * (1 - p), y, x + w, y + h
    if d == "bottom_to_top":
        return x, y + h * (1 - p), x + w, y + h
    return x, y, x + w, y + h * p  # top_to_bottom (mặc định)


def _handles(r: dict) -> dict[str, tuple[float, float]]:
    x, y, w, h = r["x"], r["y"], r["width"], r["height"]
    return {
        "tl": (x, y), "t": (x + w / 2, y), "tr": (x + w, y), "r": (x + w, y + h / 2),
        "br": (x + w, y + h), "b": (x + w / 2, y + h), "bl": (x, y + h), "l": (x, y + h / 2),
    }


def render_reveal_frame(cfg: dict, source: QImage, paper: QColor, time_ms: float) -> QImage | None:
    """Vẽ 1 khung hình xem trước kiểu 'lộ dần theo thời gian' từ annotation —
    không cần render video thật (ffmpeg/hand-drawing), nên gần như tức thì.
    Dùng chung cho PreviewEditor (sửa từng cảnh) và quick_preview.py (xem
    nhanh cả dự án nhiều cảnh)."""
    w, h = cfg["canvas"]["width"], cfg["canvas"]["height"]
    if w <= 0 or h <= 0:
        return None
    elements = cfg.get("elements", [])

    img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
    img.fill(paper)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing, True)

    done = max((_end_ms(e) for e in elements), default=0)
    if not elements or time_ms >= done + 500:
        painter.drawImage(0, 0, source)
    else:
        ordered = sorted(elements, key=lambda e: e["reveal"]["startMs"])
        layer = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
        layer.fill(Qt.transparent)
        lp = QPainter(layer)
        lp.setRenderHint(QPainter.Antialiasing, True)
        for i, el in enumerate(ordered):
            rev = el["reveal"]
            p = clamp((time_ms - rev["startMs"]) / max(rev["durationMs"], 1), 0.0, 1.0)
            if p <= 0:
                continue
            rx, ry, rx2, ry2 = _reveal_rect(el, p)
            lp.save()
            lp.setClipRect(QRectF(rx, ry, rx2 - rx, ry2 - ry))
            lp.drawImage(0, 0, source)
            lp.restore()
            lp.save()
            lp.setCompositionMode(QPainter.CompositionMode_Clear)
            for later in ordered[i + 1:]:
                r = later["region"]
                lp.fillRect(QRectF(r["x"], r["y"], r["width"], r["height"]), Qt.black)
            for pr in rev.get("protectedRegions", []):
                lp.fillRect(QRectF(pr["x"], pr["y"], pr["width"], pr["height"]), Qt.black)
            lp.restore()
        lp.end()
        painter.drawImage(0, 0, layer)
    painter.end()
    return img


def _sync_hand_path(el: dict) -> None:
    r = el["region"]
    d = el["reveal"]["direction"]
    cx, cy = r["x"] + r["width"] / 2, r["y"] + r["height"] / 2
    if d == "left_to_right":
        end = [r["x"] + r["width"], r["y"] + r["height"] / 2]
    elif d == "right_to_left":
        end = [r["x"], r["y"] + r["height"] / 2]
    elif d == "bottom_to_top":
        end = [r["x"] + r["width"] / 2, r["y"]]
    else:
        end = [r["x"] + r["width"] / 2, r["y"] + r["height"]]
    hp = el.setdefault("handPath", {})
    hp["start"] = [cx, cy]
    hp["end"] = end
    hp.setdefault("easing", "easeInOut")


class Canvas(QWidget):
    """Vùng vẽ: hiển thị ảnh + khung vùng, nhận chuột để kéo/đổi cỡ."""

    def __init__(self, editor: "PreviewEditor") -> None:
        super().__init__()
        self.editor = editor
        self.setMinimumSize(320, 180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.fillRect(self.rect(), QColor("#14161a"))
        frame = self.editor.render_frame()
        if frame is not None:
            target = self.editor.image_target_rect(self.size(), frame.size())
            painter.drawImage(target, frame)
        painter.end()

    def mousePressEvent(self, ev) -> None:  # noqa: N802
        pt = self.editor.widget_to_image(self, ev.position())
        if pt is not None:
            self.editor.on_canvas_press(pt)

    def mouseMoveEvent(self, ev) -> None:  # noqa: N802
        pt = self.editor.widget_to_image(self, ev.position())
        if pt is not None:
            self.editor.on_canvas_move(pt)

    def mouseReleaseEvent(self, ev) -> None:  # noqa: N802
        self.editor.on_canvas_release()


class PreviewEditor(QWidget):
    """Bảng chỉnh annotation nhúng trong app — tương đương assets/preview.html."""

    scene_saved = Signal(str)  # phát ra đường dẫn .png khi lưu xong 1 cảnh

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project: Path | None = None
        self.scene_entries: list[dict] = []
        self.idx = -1
        self.selected = 0
        self.time_ms = 0.0
        self.playing = False
        self.show_overlay = True
        self.dirty: set[int] = set()
        self._drag: dict | None = None
        self._updating_fields = False
        self._last_tick = 0.0

        self._build_ui()

        self._play_timer = QTimer(self)
        self._play_timer.setInterval(33)
        self._play_timer.timeout.connect(self._tick)

        self._show_hint("Chưa chọn thư mục dự án.")

    # ──────────────────────────────────────────────────────
    # Dựng giao diện
    # ──────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        top = QHBoxLayout()
        self.scene_combo = QComboBox()
        self.scene_combo.currentIndexChanged.connect(self._on_scene_changed)
        self.btn_prev = QPushButton("‹")
        self.btn_prev.setFixedWidth(32)
        self.btn_prev.clicked.connect(lambda: self._load_scene(self.idx - 1))
        self.btn_next = QPushButton("›")
        self.btn_next.setFixedWidth(32)
        self.btn_next.clicked.connect(lambda: self._load_scene(self.idx + 1))
        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(self.reload_project)
        self.overlay_chk = QCheckBox("Khung vùng")
        self.overlay_chk.setChecked(True)
        self.overlay_chk.toggled.connect(self._on_overlay_toggle)
        self.dirty_label = QLabel()
        self.dirty_label.setStyleSheet("color:#e0a800; font-weight:600;")
        top.addWidget(QLabel("Cảnh:"))
        top.addWidget(self.scene_combo, 1)
        top.addWidget(self.btn_prev)
        top.addWidget(self.btn_next)
        top.addWidget(btn_refresh)
        top.addWidget(self.overlay_chk)
        top.addStretch(1)
        top.addWidget(self.dirty_label)
        root.addLayout(top)

        splitter = QSplitter(Qt.Horizontal)

        self.stack_left = QWidget()
        left_lay = QVBoxLayout(self.stack_left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        self.hint_label = QLabel()
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setWordWrap(True)
        self.canvas = Canvas(self)
        left_lay.addWidget(self.hint_label)
        left_lay.addWidget(self.canvas)
        self.canvas.hide()
        splitter.addWidget(self.stack_left)

        side = QWidget()
        side.setMinimumWidth(300)
        side.setMaximumWidth(380)
        side_lay = QVBoxLayout(side)

        side_lay.addWidget(QLabel("<b>Khối vẽ</b> — kéo để đổi thứ tự"))
        self.elem_list = QListWidget()
        self.elem_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.elem_list.currentRowChanged.connect(self._on_list_select)
        self.elem_list.model().rowsMoved.connect(self._on_rows_moved)
        side_lay.addWidget(self.elem_list, 1)

        row_btns = QHBoxLayout()
        btn_add = QPushButton("+ Thêm khối")
        btn_add.clicked.connect(self._add_element)
        self.btn_del = QPushButton("Xoá khối đã chọn")
        self.btn_del.clicked.connect(self._delete_element)
        row_btns.addWidget(btn_add)
        row_btns.addWidget(self.btn_del)
        side_lay.addLayout(row_btns)

        form_box = QGroupBox("Khối đang chọn")
        form = QFormLayout(form_box)
        self.f_label = QLineEdit()
        self.f_label.editingFinished.connect(self._apply_fields)
        self.f_x = QSpinBox()
        self.f_y = QSpinBox()
        self.f_w = QSpinBox()
        self.f_h = QSpinBox()
        for sb in (self.f_x, self.f_y, self.f_w, self.f_h):
            sb.setRange(0, 20000)
            sb.valueChanged.connect(self._apply_fields)
        self.f_w.setMinimum(1)
        self.f_h.setMinimum(1)
        self.f_dir = QComboBox()
        for value, label in DIRECTIONS:
            self.f_dir.addItem(label, value)
        self.f_dir.currentIndexChanged.connect(self._apply_fields)
        self.f_start = QSpinBox()
        self.f_start.setRange(0, 600000)
        self.f_start.setSingleStep(100)
        self.f_start.valueChanged.connect(self._apply_fields)
        self.f_end = QSpinBox()
        self.f_end.setRange(100, 600000)
        self.f_end.setSingleStep(100)
        self.f_end.valueChanged.connect(self._apply_fields)
        self.f_dur = QLabel("0 ms")
        form.addRow("Tên", self.f_label)
        form.addRow("x", self.f_x)
        form.addRow("y", self.f_y)
        form.addRow("Rộng", self.f_w)
        form.addRow("Cao", self.f_h)
        form.addRow("Hướng", self.f_dir)
        form.addRow("Bắt đầu (ms)", self.f_start)
        form.addRow("Kết thúc (ms)", self.f_end)
        form.addRow("Thời lượng (ms)", self.f_dur)
        side_lay.addWidget(form_box)

        side_lay.addWidget(QLabel("Phụ đề"))
        self.f_sub = QPlainTextEdit()
        self.f_sub.setMaximumHeight(70)
        self.f_sub.setPlaceholderText("Phụ đề tương ứng với vùng này…")
        self.f_sub.textChanged.connect(self._apply_subtitle)
        side_lay.addWidget(self.f_sub)

        splitter.addWidget(side)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        root.addWidget(splitter, 1)

        bottom = QHBoxLayout()
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedWidth(40)
        self.btn_play.clicked.connect(self._toggle_play)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.sliderPressed.connect(self._pause)
        self.slider.valueChanged.connect(self._on_slider)
        self.time_label = QLabel("0.00s / 0.00s")
        self.time_label.setMinimumWidth(120)
        bottom.addWidget(self.btn_play)
        bottom.addWidget(self.slider, 1)
        bottom.addWidget(self.time_label)
        root.addLayout(bottom)

        self._set_controls_enabled(False)
        self._update_fields_from_selected()

    # ──────────────────────────────────────────────────────
    # Nạp dự án / cảnh
    # ──────────────────────────────────────────────────────
    def set_project(self, project: Path | None) -> None:
        """Gọi khi dự án đang mở thay đổi. Không tự nạp lại nếu đang có thay
        đổi chưa lưu, để tránh mất chỉnh sửa đang dang dở."""
        self.project = project
        if self.dirty:
            return
        self.reload_project()

    def reload_project(self) -> None:
        prev_name = (
            self.scene_entries[self.idx]["name"]
            if 0 <= self.idx < len(self.scene_entries) else None
        )
        self._pause()
        self.scene_entries = []
        self.idx = -1
        self.dirty.clear()
        if not self.project or not self.project.is_dir():
            self._show_hint("Chưa chọn thư mục dự án.")
            self.scene_combo.clear()
            return
        for png in _list_scene_pngs(self.project):
            img = QImage(str(png))
            if img.isNull():
                continue
            img = img.convertToFormat(QImage.Format_ARGB32_Premultiplied)
            ann = png.with_suffix(".annotation.json")
            cfg = _load_cfg(png, ann, img)
            self.scene_entries.append({
                "name": png.stem, "png": png, "ann": ann, "cfg": cfg,
                "has_config": ann.exists(), "image": img, "paper": _sample_paper(img),
            })
        self.scene_combo.blockSignals(True)
        self.scene_combo.clear()
        for i, e in enumerate(self.scene_entries):
            suffix = "" if e["has_config"] else " (chưa chú thích)"
            self.scene_combo.addItem(f"{i + 1}. {e['name']}{suffix}")
        self.scene_combo.blockSignals(False)
        if not self.scene_entries:
            self._show_hint(
                "Thư mục dự án chưa có ảnh .png nào.\n"
                "Thêm ảnh line-art ở tab 2 rồi bấm \"Làm mới\"."
            )
            return
        self._show_canvas()
        start_idx = 0
        if prev_name:
            for i, e in enumerate(self.scene_entries):
                if e["name"] == prev_name:
                    start_idx = i
                    break
        self._load_scene(start_idx)

    def select_scene_by_name(self, name: str) -> None:
        for i, e in enumerate(self.scene_entries):
            if e["name"] == name:
                self._load_scene(i)
                return

    def select_element(self, scene_name: str, element_id: str) -> None:
        """Mở đúng cảnh rồi chọn sẵn 1 khối theo id — dùng khi bấm vào một
        đoạn trên timeline (tab ⚡ Nhanh) để sửa nhanh."""
        self.select_scene_by_name(scene_name)
        els = self._current_elements()
        for i, el in enumerate(els):
            if el.get("id") == element_id:
                self.selected = i
                self._update_fields_from_selected()
                self.canvas.update()
                return

    def has_unsaved(self) -> bool:
        return bool(self.dirty)

    def current_scene_png(self) -> Path | None:
        if 0 <= self.idx < len(self.scene_entries):
            return self.scene_entries[self.idx]["png"]
        return None

    def _show_hint(self, text: str) -> None:
        self.hint_label.setText(text)
        self.hint_label.show()
        self.canvas.hide()
        self._set_controls_enabled(False)
        self._update_fields_from_selected()
        self._update_dirty_label()

    def _show_canvas(self) -> None:
        self.hint_label.hide()
        self.canvas.show()

    def _set_controls_enabled(self, enabled: bool) -> None:
        for w in (self.overlay_chk, self.btn_play, self.slider, self.btn_prev, self.btn_next):
            w.setEnabled(enabled)

    def _on_scene_changed(self, index: int) -> None:
        if index < 0 or index == self.idx:
            return
        self._load_scene(index)

    def _load_scene(self, index: int) -> None:
        if not (0 <= index < len(self.scene_entries)):
            return
        self._pause()
        self.idx = index
        self.selected = 0
        self.time_ms = 0.0
        self.scene_combo.blockSignals(True)
        self.scene_combo.setCurrentIndex(index)
        self.scene_combo.blockSignals(False)
        self._refresh_list()
        self._update_fields_from_selected()
        self._set_controls_enabled(True)
        self._update_dirty_label()
        self._set_time(0.0)

    # ──────────────────────────────────────────────────────
    # Render khung hình (khung xem trước dạng lộ-dần hình chữ nhật)
    # ──────────────────────────────────────────────────────
    def render_frame(self) -> QImage | None:
        if not (0 <= self.idx < len(self.scene_entries)):
            return None
        entry = self.scene_entries[self.idx]
        cfg = entry["cfg"]
        elements = cfg.get("elements", [])
        done = max((_end_ms(e) for e in elements), default=0)
        # Đứng yên ở mốc 0 (chưa bấm Play) vẫn hiện ảnh hoàn chỉnh, không rỗng.
        time_ms = (done + 500) if (not self.playing and self.time_ms <= 0) else self.time_ms
        img = render_reveal_frame(cfg, entry["image"], entry.get("paper", PAPER_FALLBACK), time_ms)
        if img is None:
            return None
        if self.show_overlay and elements:
            painter = QPainter(img)
            painter.setRenderHint(QPainter.Antialiasing, True)
            self._draw_overlay(painter, elements)
            painter.end()
        return img

    def _draw_overlay(self, painter: QPainter, elements: list[dict]) -> None:
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(18)
        painter.setFont(font)
        for i, el in enumerate(elements):
            r = el["region"]
            focus = i == self.selected
            color = COLOR_FOCUS if focus else COLOR_NORMAL
            fill = QColor(color)
            fill.setAlpha(30 if focus else 18)
            pen = QPen(color, 5 if focus else 3)
            if not focus:
                pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(QBrush(fill))
            painter.drawRect(QRectF(r["x"], r["y"], r["width"], r["height"]))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(r["x"] + 18, r["y"] + 18), 15, 15)
            painter.setPen(QPen(Qt.white))
            painter.drawText(
                QRectF(r["x"], r["y"], 36, 36), Qt.AlignCenter, str(i + 1)
            )
            if focus:
                painter.setPen(QPen(color, 3))
                painter.setBrush(QBrush(Qt.white))
                for hx, hy in _handles(r).values():
                    painter.drawRect(QRectF(hx - 10, hy - 10, 20, 20))

    # ──────────────────────────────────────────────────────
    # Ánh xạ toạ độ widget <-> ảnh
    # ──────────────────────────────────────────────────────
    def image_target_rect(self, widget_size: QSize, img_size: QSize) -> QRectF:
        ww, wh = widget_size.width(), widget_size.height()
        iw, ih = img_size.width(), img_size.height()
        if iw <= 0 or ih <= 0 or ww <= 0 or wh <= 0:
            return QRectF(0, 0, 0, 0)
        scale = min(ww / iw, wh / ih)
        tw, th = iw * scale, ih * scale
        return QRectF((ww - tw) / 2, (wh - th) / 2, tw, th)

    def widget_to_image(self, canvas_widget: QWidget, pos: QPointF) -> QPointF | None:
        if not (0 <= self.idx < len(self.scene_entries)):
            return None
        cfg = self.scene_entries[self.idx]["cfg"]
        iw, ih = cfg["canvas"]["width"], cfg["canvas"]["height"]
        target = self.image_target_rect(canvas_widget.size(), QSize(iw, ih))
        if target.width() <= 0 or target.height() <= 0:
            return None
        x = (pos.x() - target.x()) / target.width() * iw
        y = (pos.y() - target.y()) / target.height() * ih
        return QPointF(x, y)

    # ──────────────────────────────────────────────────────
    # Chuột trên canvas: chọn / kéo di chuyển / kéo đổi cỡ
    # ──────────────────────────────────────────────────────
    def on_canvas_press(self, pt: QPointF) -> None:
        if not (0 <= self.idx < len(self.scene_entries)):
            return
        elements = self.scene_entries[self.idx]["cfg"]["elements"]
        for i in range(len(elements) - 1, -1, -1):
            r = elements[i]["region"]
            if (r["x"] - 16 <= pt.x() <= r["x"] + r["width"] + 16
                    and r["y"] - 16 <= pt.y() <= r["y"] + r["height"] + 16):
                self.selected = i
                handle = None
                for name, (hx, hy) in _handles(r).items():
                    if abs(pt.x() - hx) <= 16 and abs(pt.y() - hy) <= 16:
                        handle = name
                        break
                self._drag = {"handle": handle or "move", "start": pt, "orig": dict(r)}
                self._update_fields_from_selected()
                self.canvas.update()
                return

    def on_canvas_move(self, pt: QPointF) -> None:
        if not self._drag or not (0 <= self.idx < len(self.scene_entries)):
            return
        elements = self.scene_entries[self.idx]["cfg"]["elements"]
        if not (0 <= self.selected < len(elements)):
            return
        el = elements[self.selected]
        r = el["region"]
        base = self._drag["orig"]
        start = self._drag["start"]
        dx, dy = pt.x() - start.x(), pt.y() - start.y()
        cfg = self.scene_entries[self.idx]["cfg"]
        W, H = cfg["canvas"]["width"], cfg["canvas"]["height"]
        handle = self._drag["handle"]
        min_size = 20
        if handle == "move":
            r["x"] = round(clamp(base["x"] + dx, 0, W - base["width"]))
            r["y"] = round(clamp(base["y"] + dy, 0, H - base["height"]))
        else:
            left, right = base["x"], base["x"] + base["width"]
            top, bottom = base["y"], base["y"] + base["height"]
            if "l" in handle:
                left = clamp(base["x"] + dx, 0, right - min_size)
            if "r" in handle:
                right = clamp(base["x"] + base["width"] + dx, left + min_size, W)
            if "t" in handle:
                top = clamp(base["y"] + dy, 0, bottom - min_size)
            if "b" in handle:
                bottom = clamp(base["y"] + base["height"] + dy, top + min_size, H)
            r["x"], r["y"] = round(left), round(top)
            r["width"], r["height"] = round(right - left), round(bottom - top)
        _sync_hand_path(el)
        self._mark_dirty()
        self._update_fields_from_selected()
        self.canvas.update()

    def on_canvas_release(self) -> None:
        self._drag = None

    # ──────────────────────────────────────────────────────
    # Danh sách khối (kéo-thả đổi thứ tự)
    # ──────────────────────────────────────────────────────
    def _current_elements(self) -> list[dict]:
        if not (0 <= self.idx < len(self.scene_entries)):
            return []
        return self.scene_entries[self.idx]["cfg"]["elements"]

    def _refresh_list(self) -> None:
        self.elem_list.blockSignals(True)
        self.elem_list.clear()
        for i, el in enumerate(self._current_elements()):
            item = QListWidgetItem(self._item_text(i, el))
            item.setData(Qt.UserRole, el.get("id"))
            self.elem_list.addItem(item)
        if 0 <= self.selected < self.elem_list.count():
            self.elem_list.setCurrentRow(self.selected)
        self.elem_list.blockSignals(False)

    @staticmethod
    def _item_text(i: int, el: dict) -> str:
        start_s = el["reveal"].get("startMs", 0) / 1000
        label = el.get("label") or "(chưa đặt tên)"
        return f"#{i + 1}  {start_s:.1f}s   {label}"

    def _refresh_list_texts(self) -> None:
        elements = self._current_elements()
        for i in range(min(self.elem_list.count(), len(elements))):
            self.elem_list.item(i).setText(self._item_text(i, elements[i]))

    def _on_list_select(self, row: int) -> None:
        if row < 0 or row == self.selected:
            return
        self.selected = row
        self._update_fields_from_selected()
        self.canvas.update()

    def _on_rows_moved(self, *_args) -> None:
        elements = self._current_elements()
        if not elements:
            return
        by_id = {el.get("id"): el for el in elements}
        new_order = []
        for i in range(self.elem_list.count()):
            key = self.elem_list.item(i).data(Qt.UserRole)
            if key in by_id:
                new_order.append(by_id[key])
        if len(new_order) != len(elements):
            return
        for i, el in enumerate(new_order):
            el["sequence"] = i + 1
        self.scene_entries[self.idx]["cfg"]["elements"] = new_order
        self.selected = max(0, self.elem_list.currentRow())
        self._mark_dirty()
        self._refresh_list_texts()
        self._update_fields_from_selected()
        self.canvas.update()

    # ──────────────────────────────────────────────────────
    # Thêm / xoá khối
    # ──────────────────────────────────────────────────────
    def _add_element(self) -> None:
        if not (0 <= self.idx < len(self.scene_entries)):
            return
        cfg = self.scene_entries[self.idx]["cfg"]
        elements = cfg["elements"]
        W, H = cfg["canvas"]["width"], cfg["canvas"]["height"]
        seq = len(elements) + 1
        last_end = max((_end_ms(e) for e in elements), default=300)
        new_id = f"region_{seq}_{int(time.time() * 1000) % 100000}"
        el = {
            "id": new_id, "label": "Khối mới", "sequence": seq, "narrativeRole": "",
            "type": "object", "subtitle": "",
            "region": {
                "x": round(W * 0.1), "y": round(H * 0.1),
                "width": round(W * 0.25), "height": round(H * 0.3),
            },
            "reveal": {
                "direction": "top_to_bottom", "startMs": round(last_end) + 200,
                "durationMs": 2000, "maskPaddingPx": 22, "protectedRegions": [],
            },
            "handPath": {},
        }
        _sync_hand_path(el)
        elements.append(el)
        self.selected = len(elements) - 1
        self._mark_dirty()
        self._refresh_list()
        self._update_fields_from_selected()
        self.canvas.update()

    def _delete_element(self) -> None:
        elements = self._current_elements()
        if not (0 <= self.selected < len(elements)):
            return
        elements.pop(self.selected)
        for i, el in enumerate(elements):
            el["sequence"] = i + 1
        self.selected = max(0, self.selected - 1)
        self._mark_dirty()
        self._refresh_list()
        self._update_fields_from_selected()
        self.canvas.update()

    # ──────────────────────────────────────────────────────
    # Form bên phải (khối đang chọn)
    # ──────────────────────────────────────────────────────
    def _update_fields_from_selected(self) -> None:
        elements = self._current_elements()
        has_sel = 0 <= self.selected < len(elements)
        for w in (
            self.f_label, self.f_x, self.f_y, self.f_w, self.f_h,
            self.f_dir, self.f_start, self.f_end, self.f_sub,
        ):
            w.setEnabled(has_sel)
        self.btn_del.setEnabled(has_sel)
        self._updating_fields = True
        try:
            if has_sel:
                el = elements[self.selected]
                r, rev = el["region"], el["reveal"]
                self.f_label.setText(el.get("label", ""))
                self.f_x.setValue(int(r["x"]))
                self.f_y.setValue(int(r["y"]))
                self.f_w.setValue(int(r["width"]))
                self.f_h.setValue(int(r["height"]))
                i = self.f_dir.findData(rev.get("direction", "top_to_bottom"))
                self.f_dir.setCurrentIndex(max(i, 0))
                start, dur = int(rev.get("startMs", 0)), int(rev.get("durationMs", 0))
                self.f_start.setValue(start)
                self.f_end.setValue(start + dur)
                self.f_dur.setText(f"{dur} ms")
                self.f_sub.blockSignals(True)
                self.f_sub.setPlainText(el.get("subtitle", ""))
                self.f_sub.blockSignals(False)
            else:
                self.f_label.clear()
                for sb in (self.f_x, self.f_y, self.f_w, self.f_h, self.f_start, self.f_end):
                    sb.setValue(sb.minimum())
                self.f_dur.setText("0 ms")
                self.f_sub.blockSignals(True)
                self.f_sub.clear()
                self.f_sub.blockSignals(False)
        finally:
            self._updating_fields = False
        self.elem_list.blockSignals(True)
        if 0 <= self.selected < self.elem_list.count():
            self.elem_list.setCurrentRow(self.selected)
        self.elem_list.blockSignals(False)

    def _apply_fields(self) -> None:
        if self._updating_fields:
            return
        elements = self._current_elements()
        if not (0 <= self.selected < len(elements)):
            return
        el = elements[self.selected]
        el["label"] = self.f_label.text()
        r = el["region"]
        r["x"] = max(0, self.f_x.value())
        r["y"] = max(0, self.f_y.value())
        r["width"] = max(1, self.f_w.value())
        r["height"] = max(1, self.f_h.value())
        el["reveal"]["direction"] = self.f_dir.currentData()
        start = max(0, self.f_start.value())
        end = max(start + 100, self.f_end.value())
        el["reveal"]["startMs"] = start
        el["reveal"]["durationMs"] = end - start
        self._updating_fields = True
        self.f_end.setValue(end)
        self.f_dur.setText(f"{end - start} ms")
        self._updating_fields = False
        _sync_hand_path(el)
        self._mark_dirty()
        self._refresh_list_texts()
        self.canvas.update()

    def _apply_subtitle(self) -> None:
        elements = self._current_elements()
        if not (0 <= self.selected < len(elements)):
            return
        elements[self.selected]["subtitle"] = self.f_sub.toPlainText()
        self._mark_dirty()

    # ──────────────────────────────────────────────────────
    # Khung hiển thị (checkbox)
    # ──────────────────────────────────────────────────────
    def _on_overlay_toggle(self, checked: bool) -> None:
        self.show_overlay = checked
        self.canvas.update()

    # ──────────────────────────────────────────────────────
    # Thanh thời gian / phát
    # ──────────────────────────────────────────────────────
    def _toggle_play(self) -> None:
        self._pause() if self.playing else self._play()

    def _play(self) -> None:
        if not (0 <= self.idx < len(self.scene_entries)):
            return
        cfg = self.scene_entries[self.idx]["cfg"]
        if self.time_ms >= _total_ms(cfg):
            self.time_ms = 0.0
        self.playing = True
        self.btn_play.setText("⏸")
        self._last_tick = time.monotonic()
        self._play_timer.start()

    def _pause(self) -> None:
        self.playing = False
        self.btn_play.setText("▶")
        self._play_timer.stop()

    def _tick(self) -> None:
        now = time.monotonic()
        dt_ms = (now - self._last_tick) * 1000
        self._last_tick = now
        self._set_time(self.time_ms + dt_ms)
        cfg = self.scene_entries[self.idx]["cfg"]
        if self.time_ms >= _total_ms(cfg):
            self._pause()

    def _set_time(self, v: float) -> None:
        if not (0 <= self.idx < len(self.scene_entries)):
            return
        cfg = self.scene_entries[self.idx]["cfg"]
        total = _total_ms(cfg)
        self.time_ms = clamp(v, 0.0, total)
        self.slider.blockSignals(True)
        self.slider.setValue(round(self.time_ms / total * 1000) if total else 0)
        self.slider.blockSignals(False)
        self.time_label.setText(f"{self.time_ms / 1000:.2f}s / {total / 1000:.2f}s")
        self.canvas.update()

    def _on_slider(self, val: int) -> None:
        if not (0 <= self.idx < len(self.scene_entries)):
            return
        self._pause()
        cfg = self.scene_entries[self.idx]["cfg"]
        total = _total_ms(cfg)
        self._set_time(val / 1000 * total)

    # ──────────────────────────────────────────────────────
    # Lưu
    # ──────────────────────────────────────────────────────
    def _mark_dirty(self) -> None:
        self.dirty.add(self.idx)
        self._update_dirty_label()

    def _update_dirty_label(self) -> None:
        self.dirty_label.setText("● Chưa lưu" if self.idx in self.dirty else "")

    def save_all_dirty(self) -> None:
        """Lưu mọi cảnh đang có thay đổi chưa lưu — gọi khi đóng cửa sổ
        Preview (tự lưu thay vì cần bấm nút Lưu)."""
        for i in sorted(self.dirty):
            self._save_scene(i)

    def discard_unsaved(self) -> None:
        """Bỏ hết thay đổi chưa lưu, nạp lại từ đĩa — dùng khi bấm Huỷ."""
        self.reload_project()

    def _save_scene(self, index: int) -> None:
        if not (0 <= index < len(self.scene_entries)):
            return
        entry = self.scene_entries[index]
        cfg = entry["cfg"]
        if cfg.get("elements"):
            cfg["sceneDurationMs"] = round(_total_ms(cfg))
        try:
            entry["ann"].write_text(
                json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            QMessageBox.warning(self, "Lưu thất bại", f"{entry['ann'].name}: {exc}")
            return
        entry["has_config"] = True
        self.dirty.discard(index)
        if index == self.idx:
            self._update_dirty_label()
        self.scene_combo.setItemText(index, f"{index + 1}. {entry['name']}")
        self.scene_saved.emit(str(entry["png"]))
