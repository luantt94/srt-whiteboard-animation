#!/usr/bin/env python3
"""
Timeline kiểu CapCut cho tab "⚡ Nhanh": hiển thị các cảnh theo đúng tỉ lệ
thời gian, bên dưới là dải đối tượng của từng cảnh (kéo thân để đổi thời
điểm bắt đầu, kéo 2 đầu để đổi thời lượng), dải chữ overlay (thêm/kéo/sửa)
và dải âm thanh (xem trước file đã chọn).

Widget tự đọc/ghi trực tiếp từng file `<tên>.annotation.json` trong dự án —
độc lập với preview_widget.PreviewEditor (bảng chỉnh chi tiết mở khi bấm vào
1 khối); cả hai luôn đọc lại từ đĩa khi mở nên không cần đồng bộ bộ nhớ dùng
chung.
"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QInputDialog, QLabel, QMessageBox, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

PX_PER_SEC = 40.0
RULER_H = 20
SCENE_H = 56
OBJ_H = 28
TEXT_H = 28
AUDIO_H = 24
GAP = 4
PALETTE = [QColor(c) for c in (
    "#3b82f6", "#e97036", "#22c55e", "#a855f7", "#ef4444",
    "#06b6d4", "#eab308", "#ec4899", "#14b8a6", "#f97316",
)]
HANDLE_PX = 7


_SCENE_IMAGE_GLOBS = ("*.png", "*.jpg", "*.jpeg")


def _list_scene_pngs(project: Path) -> list[Path]:
    if not project or not project.is_dir():
        return []
    out = []
    for pat in _SCENE_IMAGE_GLOBS:
        out += [p for p in project.glob(pat) if not p.name.endswith(".regions.png")]
    return sorted(out)


def _load_cfg(ann: Path) -> dict:
    cfg = None
    if ann.exists():
        try:
            cfg = json.loads(ann.read_text(encoding="utf-8"))
        except Exception:
            cfg = None
    if not isinstance(cfg, dict):
        cfg = {"sceneDurationMs": 8000, "elements": []}
    if not isinstance(cfg.get("elements"), list):
        cfg["elements"] = []
    cfg.setdefault("sceneDurationMs", 8000)
    for el in cfg["elements"]:
        el.setdefault("reveal", {})
        el["reveal"].setdefault("startMs", 0)
        el["reveal"].setdefault("durationMs", 1000)
        el.setdefault("label", "")
        el.setdefault("id", "obj")
    return cfg


def _probe_audio_duration_ms(path: Path) -> int | None:
    try:
        import av
        with av.open(str(path)) as c:
            if c.duration:
                return round(c.duration / 1000)
    except Exception:
        return None
    return None


class _Scene:
    __slots__ = ("png", "ann", "cfg")

    def __init__(self, png: Path, ann: Path, cfg: dict) -> None:
        self.png = png
        self.ann = ann
        self.cfg = cfg

    @property
    def duration_ms(self) -> float:
        els = self.cfg.get("elements", [])
        max_end = max((e["reveal"]["startMs"] + e["reveal"]["durationMs"] for e in els), default=0)
        return max(float(self.cfg.get("sceneDurationMs", 0)), max_end + 500, 1000)


class TimelineCanvas(QWidget):
    """Vùng vẽ thật sự của timeline — chứa trong TimelineWidget (có thanh cuộn)."""

    scene_clicked = Signal(str)
    object_clicked = Signal(str, str)
    scenes_reordered = Signal(list)
    changed = Signal()

    def __init__(self, parent: "TimelineWidget") -> None:
        super().__init__(parent)
        self.owner = parent
        self.setMouseTracking(True)
        self.setMinimumHeight(RULER_H + SCENE_H + OBJ_H + TEXT_H + AUDIO_H + GAP * 5)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._drag: dict | None = None
        self._hit_scenes: list[tuple[QRectF, int]] = []
        self._hit_objs: list[tuple[QRectF, int, int]] = []
        self._hit_texts: list[tuple[QRectF, int]] = []
        self._sel_obj: tuple[int, int] | None = None
        self._sel_text: int | None = None

    # ── bố cục / toạ độ ──
    def _total_ms(self) -> float:
        return max(sum(s.duration_ms for s in self.owner.scenes), 1000.0)

    def _px_per_ms(self) -> float:
        return PX_PER_SEC / 1000.0

    def _scene_starts(self) -> list[float]:
        t = 0.0
        out = []
        for s in self.owner.scenes:
            out.append(t)
            t += s.duration_ms
        return out

    def sizeHint(self):  # noqa: N802
        from PySide6.QtCore import QSize
        w = max(400, round(self._total_ms() * self._px_per_ms()) + 20)
        return QSize(w, self.minimumHeight())

    def _relayout(self) -> None:
        """QScrollArea (setWidgetResizable=False) không tự co giãn canvas
        theo sizeHint() khi nội dung đổi — phải tự resize() tay, nếu không
        các cảnh/khối nằm sau điểm rộng cũ sẽ bị cắt mất (chỉ thấy 1 ảnh)."""
        self.resize(self.sizeHint())
        self.updateGeometry()

    # ── vẽ ──
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#14161a"))
        ppm = self._px_per_ms()
        total = self._total_ms()
        y = 0
        self._draw_ruler(painter, 0, total, ppm)
        y += RULER_H + GAP
        self._hit_scenes = self._draw_scenes(painter, y, ppm)
        y += SCENE_H + GAP
        self._hit_objs = self._draw_objects(painter, y, ppm)
        y += OBJ_H + GAP
        self._hit_texts = self._draw_texts(painter, y, ppm)
        y += TEXT_H + GAP
        self._draw_audio(painter, y, ppm, total)
        painter.end()

    def _draw_ruler(self, p: QPainter, _x0: float, total_ms: float, ppm: float) -> None:
        p.setPen(QPen(QColor("#5b6270"), 1))
        font = QFont()
        font.setPixelSize(10)
        p.setFont(font)
        step_s = 1 if total_ms < 20000 else (2 if total_ms < 60000 else 5)
        s = 0
        while s * 1000 <= total_ms + 1:
            x = s * 1000 * ppm
            p.drawLine(QPointF(x, RULER_H - 6), QPointF(x, RULER_H))
            p.drawText(QPointF(x + 2, RULER_H - 7), f"{s}s")
            s += step_s

    def _draw_scenes(self, p: QPainter, y: float, ppm: float) -> list[tuple[QRectF, int]]:
        hits = []
        starts = self._scene_starts()
        for i, sc in enumerate(self.owner.scenes):
            x = starts[i] * ppm
            w = max(2.0, sc.duration_ms * ppm)
            rect = QRectF(x, y, w, SCENE_H)
            focus = i == self.owner.selected_scene
            p.setPen(QPen(QColor("#3b82f6") if focus else QColor("#3a3f4a"), 2 if focus else 1))
            p.setBrush(QBrush(QColor("#22262e")))
            p.drawRect(rect)
            pix = self.owner.thumb(sc.png)
            if pix is not None and w > 10:
                target = QRectF(x + 1, y + 1, min(w - 2, SCENE_H * 16 / 9), SCENE_H - 2)
                p.drawPixmap(target, pix, QRectF(pix.rect()))
            p.setPen(QPen(QColor("#dbe6ff")))
            p.drawText(QRectF(x + 4, y + SCENE_H - 16, w - 8, 14), Qt.AlignLeft | Qt.AlignVCenter,
                       f"{i + 1}. {sc.png.stem}")
            hits.append((rect, i))
        return hits

    def _draw_objects(self, p: QPainter, y: float, ppm: float) -> list[tuple[QRectF, int, int]]:
        hits = []
        starts = self._scene_starts()
        fm = QFontMetrics(p.font())
        for si, sc in enumerate(self.owner.scenes):
            base_x = starts[si] * ppm
            for oi, el in enumerate(sc.cfg.get("elements", [])):
                rev = el["reveal"]
                x = base_x + rev["startMs"] * ppm
                w = max(4.0, rev["durationMs"] * ppm)
                rect = QRectF(x, y, w, OBJ_H)
                color = PALETTE[oi % len(PALETTE)]
                sel = self._sel_obj == (si, oi)
                p.setPen(QPen(QColor("#ffffff") if sel else color.darker(130), 2 if sel else 1))
                p.setBrush(QBrush(color.lighter(120) if sel else color))
                p.drawRoundedRect(rect, 3, 3)
                label = el.get("label") or f"#{oi + 1}"
                elided = fm.elidedText(label, Qt.ElideRight, max(4, int(w) - 6))
                p.setPen(QPen(Qt.white))
                p.drawText(rect.adjusted(3, 0, -3, 0), Qt.AlignLeft | Qt.AlignVCenter, elided)
                hits.append((rect, si, oi))
        return hits

    def _draw_texts(self, p: QPainter, y: float, ppm: float) -> list[tuple[QRectF, int]]:
        hits = []
        fm = QFontMetrics(p.font())
        for i, item in enumerate(self.owner.texts):
            x = item["startMs"] * ppm
            w = max(4.0, item["durationMs"] * ppm)
            rect = QRectF(x, y, w, TEXT_H)
            sel = self._sel_text == i
            p.setPen(QPen(QColor("#ffffff") if sel else QColor("#b88a2a"), 2 if sel else 1))
            p.setBrush(QBrush(QColor("#f5c84a") if sel else QColor("#d6a521")))
            p.drawRoundedRect(rect, 3, 3)
            elided = fm.elidedText("“" + item["text"] + "”", Qt.ElideRight, max(4, int(w) - 6))
            p.setPen(QPen(QColor("#222")))
            p.drawText(rect.adjusted(3, 0, -3, 0), Qt.AlignLeft | Qt.AlignVCenter, elided)
            hits.append((rect, i))
        return hits

    def _draw_audio(self, p: QPainter, y: float, ppm: float, total_ms: float) -> None:
        if not self.owner.audio_path:
            p.setPen(QPen(QColor("#5b6270")))
            p.drawText(QRectF(0, y, 200, AUDIO_H), Qt.AlignLeft | Qt.AlignVCenter,
                       "(chưa chọn âm thanh)")
            return
        dur = self.owner.audio_duration_ms or total_ms
        w = max(4.0, min(dur, total_ms) * ppm)
        rect = QRectF(0, y, w, AUDIO_H)
        p.setPen(QPen(QColor("#1f8a5f"), 1))
        p.setBrush(QBrush(QColor("#1f8a5f")))
        p.drawRoundedRect(rect, 3, 3)
        p.setPen(QPen(Qt.white))
        p.drawText(rect.adjusted(4, 0, -4, 0), Qt.AlignLeft | Qt.AlignVCenter,
                   Path(self.owner.audio_path).name)

    # ── chuột: chọn / kéo ──
    def mousePressEvent(self, ev) -> None:  # noqa: N802
        pos = ev.position()
        for rect, oi_global, _ in []:
            pass
        for rect, si, oi in reversed(self._hit_objs):
            if rect.adjusted(-2, 0, 2, 0).contains(pos):
                self._sel_obj = (si, oi)
                self._sel_text = None
                handle = self._edge_handle(rect, pos.x())
                self._drag = {
                    "kind": "object", "scene": si, "obj": oi, "handle": handle,
                    "start_x": pos.x(), "orig_start": self.owner.scenes[si].cfg["elements"][oi]["reveal"]["startMs"],
                    "orig_dur": self.owner.scenes[si].cfg["elements"][oi]["reveal"]["durationMs"],
                    "moved": False,
                }
                self.update()
                return
        for rect, i in reversed(self._hit_texts):
            if rect.adjusted(-2, 0, 2, 0).contains(pos):
                self._sel_text = i
                self._sel_obj = None
                handle = self._edge_handle(rect, pos.x())
                self._drag = {
                    "kind": "text", "idx": i, "handle": handle, "start_x": pos.x(),
                    "orig_start": self.owner.texts[i]["startMs"],
                    "orig_dur": self.owner.texts[i]["durationMs"], "moved": False,
                }
                self.update()
                return
        for rect, i in reversed(self._hit_scenes):
            if rect.contains(pos):
                self.owner.selected_scene = i
                self._drag = {"kind": "scene", "scene": i, "start_x": pos.x(), "moved": False}
                self.update()
                return
        self._sel_obj = None
        self._sel_text = None
        self.update()

    @staticmethod
    def _edge_handle(rect: QRectF, x: float) -> str:
        if abs(x - rect.left()) <= HANDLE_PX:
            return "left"
        if abs(x - rect.right()) <= HANDLE_PX:
            return "right"
        return "move"

    def mouseMoveEvent(self, ev) -> None:  # noqa: N802
        pos = ev.position()
        if not self._drag:
            self._update_cursor(pos)
            return
        dx = pos.x() - self._drag["start_x"]
        if abs(dx) > 3:
            self._drag["moved"] = True
        ppm = self._px_per_ms()
        dms = dx / ppm

        if self._drag["kind"] == "object":
            si, oi = self._drag["scene"], self._drag["obj"]
            els = self.owner.scenes[si].cfg["elements"]
            rev = els[oi]["reveal"]
            lo = els[oi - 1]["reveal"]["startMs"] + els[oi - 1]["reveal"]["durationMs"] if oi > 0 else 0
            hi = els[oi + 1]["reveal"]["startMs"] if oi + 1 < len(els) else None
            if self._drag["handle"] == "move":
                new_start = self._drag["orig_start"] + dms
                new_start = max(lo, new_start)
                if hi is not None:
                    new_start = min(new_start, hi - self._drag["orig_dur"])
                rev["startMs"] = round(new_start)
            elif self._drag["handle"] == "left":
                new_start = max(lo, self._drag["orig_start"] + dms)
                new_end = self._drag["orig_start"] + self._drag["orig_dur"]
                new_start = min(new_start, new_end - 300)
                rev["startMs"] = round(new_start)
                rev["durationMs"] = round(new_end - new_start)
            else:  # right
                new_dur = self._drag["orig_dur"] + dms
                new_dur = max(300.0, new_dur)
                if hi is not None:
                    new_dur = min(new_dur, hi - rev["startMs"])
                rev["durationMs"] = round(new_dur)
            self._relayout()
            self.update()

        elif self._drag["kind"] == "text":
            i = self._drag["idx"]
            item = self.owner.texts[i]
            total = self._total_ms()
            prev_end = self.owner.texts[i - 1]["startMs"] + self.owner.texts[i - 1]["durationMs"] if i > 0 else 0
            next_start = self.owner.texts[i + 1]["startMs"] if i + 1 < len(self.owner.texts) else total
            if self._drag["handle"] == "move":
                new_start = self._drag["orig_start"] + dms
                new_start = max(prev_end, min(new_start, next_start - self._drag["orig_dur"]))
                item["startMs"] = round(new_start)
            elif self._drag["handle"] == "left":
                new_start = max(prev_end, self._drag["orig_start"] + dms)
                new_end = self._drag["orig_start"] + self._drag["orig_dur"]
                new_start = min(new_start, new_end - 300)
                item["startMs"] = round(new_start)
                item["durationMs"] = round(new_end - new_start)
            else:
                new_dur = max(300.0, self._drag["orig_dur"] + dms)
                new_dur = min(new_dur, next_start - item["startMs"])
                item["durationMs"] = round(new_dur)
            self.update()

        elif self._drag["kind"] == "scene":
            si = self._drag["scene"]
            starts = self._scene_starts()
            cx = pos.x()
            order = list(range(len(self.owner.scenes)))
            cur_pos = starts[si] * ppm + (self.owner.scenes[si].duration_ms * ppm) / 2 + dx
            new_idx = si
            acc = 0.0
            for i, sc in enumerate(self.owner.scenes):
                w = sc.duration_ms * ppm
                if acc <= cur_pos < acc + w:
                    new_idx = i
                    break
                acc += w
            else:
                new_idx = len(self.owner.scenes) - 1
            if new_idx != si:
                scenes = self.owner.scenes
                scenes.insert(new_idx, scenes.pop(si))
                self._drag["scene"] = new_idx
                self.owner.selected_scene = new_idx
                self._drag["start_x"] = pos.x()
                self._relayout()
            self.update()

    def _update_cursor(self, pos: QPointF) -> None:
        for rect, _si, _oi in reversed(self._hit_objs):
            if rect.adjusted(-2, 0, 2, 0).contains(pos):
                h = self._edge_handle(rect, pos.x())
                self.setCursor(Qt.SizeHorCursor if h != "move" else Qt.OpenHandCursor)
                return
        for rect, _i in reversed(self._hit_texts):
            if rect.adjusted(-2, 0, 2, 0).contains(pos):
                h = self._edge_handle(rect, pos.x())
                self.setCursor(Qt.SizeHorCursor if h != "move" else Qt.OpenHandCursor)
                return
        self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, ev) -> None:  # noqa: N802
        if not self._drag:
            return
        drag = self._drag
        self._drag = None
        if not drag["moved"]:
            if drag["kind"] == "object":
                el = self.owner.scenes[drag["scene"]].cfg["elements"][drag["obj"]]
                self.object_clicked.emit(str(self.owner.scenes[drag["scene"]].png), el.get("id", ""))
            elif drag["kind"] == "text":
                self.owner.edit_text(drag["idx"])
            elif drag["kind"] == "scene":
                self.scene_clicked.emit(str(self.owner.scenes[drag["scene"]].png))
            self.update()
            return
        if drag["kind"] == "object":
            self.owner.save_scene(drag["scene"])
            self.changed.emit()
        elif drag["kind"] == "text":
            self.owner.save_texts()
            self.changed.emit()
        elif drag["kind"] == "scene":
            self.owner.commit_reorder()
            self.changed.emit()
        self.update()


class TimelineWidget(QWidget):
    """Khung ngoài: thanh cuộn ngang + canvas + hàng nút (thêm/xoá chữ)."""

    scene_clicked = Signal(str)
    object_clicked = Signal(str, str)
    scenes_reordered = Signal(list)
    scene_removed = Signal(str)
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project: Path | None = None
        self.scenes: list[_Scene] = []
        self.texts: list[dict] = []
        self.audio_path: str = ""
        self.audio_duration_ms: int | None = None
        self.selected_scene = -1
        self._thumbs: dict[str, object] = {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFixedHeight(RULER_H + SCENE_H + OBJ_H + TEXT_H + AUDIO_H + GAP * 5 + 4)
        self.canvas = TimelineCanvas(self)
        self.canvas.scene_clicked.connect(self.scene_clicked)
        self.canvas.object_clicked.connect(self.object_clicked)
        self.canvas.changed.connect(self.changed)
        scroll.setWidget(self.canvas)
        lay.addWidget(scroll)

        row = QHBoxLayout()
        hint = QLabel(
            "Kéo khối cảnh để đổi thứ tự · kéo thân/2 đầu khối đối tượng hoặc "
            "chữ để đổi thời gian · bấm (không kéo) để sửa"
        )
        hint.setStyleSheet("color:#8b929c; font-size:11px;")
        btn_del_scene = QPushButton("🗑 Xoá ảnh đã chọn")
        btn_del_scene.setToolTip(
            "Xoá hẳn ảnh (cảnh) đang chọn trên timeline khỏi dự án — xoá cả "
            "annotation và video đã render của riêng cảnh đó."
        )
        btn_del_scene.setStyleSheet("QPushButton{color:#ff6b6b;}")
        btn_del_scene.clicked.connect(self.remove_selected_scene)
        btn_add_text = QPushButton("+ Thêm chữ")
        btn_add_text.clicked.connect(self.add_text)
        btn_del_text = QPushButton("Xoá chữ đã chọn")
        btn_del_text.clicked.connect(self.delete_selected_text)
        row.addWidget(hint, 1)
        row.addWidget(btn_del_scene)
        row.addWidget(btn_add_text)
        row.addWidget(btn_del_text)
        lay.addLayout(row)

    # ── nạp / lưu ──
    def reload(self, project: Path | None) -> None:
        self.project = project
        self.scenes = []
        self._thumbs.clear()
        if project and project.is_dir():
            for png in _list_scene_pngs(project):
                ann = png.with_suffix(".annotation.json")
                self.scenes.append(_Scene(png, ann, _load_cfg(ann)))
            tpath = project / "texts.json"
            if tpath.exists():
                try:
                    data = json.loads(tpath.read_text(encoding="utf-8"))
                    self.texts = data.get("items", [])
                except Exception:
                    self.texts = []
            else:
                self.texts = []
        else:
            self.texts = []
        if self.selected_scene >= len(self.scenes):
            self.selected_scene = len(self.scenes) - 1
        self.canvas._relayout()
        self.canvas.update()

    def set_audio(self, path: str) -> None:
        self.audio_path = path
        self.audio_duration_ms = _probe_audio_duration_ms(Path(path)) if path else None
        self.canvas.update()

    def thumb(self, png: Path):
        key = str(png)
        if key not in self._thumbs:
            from PySide6.QtGui import QPixmap
            pix = QPixmap(str(png))
            self._thumbs[key] = None if pix.isNull() else pix
        return self._thumbs[key]

    def save_scene(self, idx: int) -> None:
        if not (0 <= idx < len(self.scenes)):
            return
        sc = self.scenes[idx]
        try:
            sc.ann.write_text(json.dumps(sc.cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "Lưu thất bại", f"{sc.ann.name}: {exc}")

    def save_texts(self) -> None:
        if not self.project:
            return
        path = self.project / "texts.json"
        try:
            path.write_text(
                json.dumps({"items": self.texts}, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            QMessageBox.warning(self, "Lưu thất bại", f"texts.json: {exc}")

    def commit_reorder(self) -> None:
        self.scenes_reordered.emit([s.png for s in self.scenes])

    # ── xoá cảnh (ảnh) ──
    # Đuôi ảnh thật có thể là .png/.jpg/.jpeg nên xoá riêng bằng sc.png; đây
    # chỉ là các file phụ luôn có đuôi cố định đi kèm.
    _SCENE_AUX_EXTS = (".annotation.json", ".regions.png", "-whiteboard.mp4")

    def remove_selected_scene(self) -> None:
        idx = self.selected_scene
        if not (0 <= idx < len(self.scenes)):
            QMessageBox.information(
                self, "Chưa chọn ảnh",
                "Bấm chọn 1 ảnh (cảnh) trên timeline trước khi xoá."
            )
            return
        sc = self.scenes[idx]
        if QMessageBox.question(
            self, "Xoá ảnh này?",
            f"Xoá hẳn \"{sc.png.name}\" khỏi dự án?\n\n"
            "Annotation và video riêng của cảnh này (nếu đã render) cũng sẽ bị "
            "xoá. Video ghép cũ (nếu có) không tự cập nhật — cần bấm TẠO VIDEO "
            "NGAY lại. Không thể hoàn tác.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        stem = sc.png.stem
        files_to_remove = [sc.png] + [
            self.project / f"{stem}{ext}" for ext in self._SCENE_AUX_EXTS
        ]
        for f in files_to_remove:
            if f.exists():
                try:
                    f.unlink()
                except OSError as exc:
                    QMessageBox.warning(self, "Xoá thất bại", f"{f.name}: {exc}")
        removed_name = sc.png.name
        self.scenes.pop(idx)
        self._thumbs.pop(str(sc.png), None)
        if self.selected_scene >= len(self.scenes):
            self.selected_scene = len(self.scenes) - 1
        self.canvas._sel_obj = None
        self.canvas._relayout()
        self.canvas.update()
        self.scene_removed.emit(removed_name)
        self.changed.emit()

    # ── chữ overlay ──
    def add_text(self) -> None:
        if not self.project:
            QMessageBox.information(self, "Chưa có dự án", "Hãy chọn ảnh trước.")
            return
        text, ok = QInputDialog.getText(self, "Thêm chữ", "Nội dung chữ hiện trên video:")
        text = (text or "").strip()
        if not ok or not text:
            return
        total = max(self.canvas._total_ms(), 1000.0)
        last_end = max((it["startMs"] + it["durationMs"] for it in self.texts), default=0)
        start = min(last_end, max(0, total - 3000))
        dur = min(3000, max(500, total - start))
        self.texts.append({"id": f"text-{len(self.texts) + 1}", "text": text,
                            "startMs": round(start), "durationMs": round(dur)})
        self.save_texts()
        self.canvas._sel_text = len(self.texts) - 1
        self.canvas.update()
        self.changed.emit()

    def edit_text(self, idx: int) -> None:
        if not (0 <= idx < len(self.texts)):
            return
        item = self.texts[idx]
        text, ok = QInputDialog.getText(self, "Sửa chữ", "Nội dung:", text=item["text"])
        if ok and (text or "").strip():
            item["text"] = text.strip()
            self.save_texts()
            self.canvas.update()
            self.changed.emit()

    def delete_selected_text(self) -> None:
        i = self.canvas._sel_text
        if i is None or not (0 <= i < len(self.texts)):
            QMessageBox.information(self, "Chưa chọn", "Bấm chọn 1 đoạn chữ trên timeline trước.")
            return
        self.texts.pop(i)
        self.canvas._sel_text = None
        self.save_texts()
        self.canvas.update()
        self.changed.emit()
