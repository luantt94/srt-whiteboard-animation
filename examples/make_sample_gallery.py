#!/usr/bin/env python3
"""
Tạo lại 10 thư mục "nguyên liệu thô" trong assets/whiteboard/sample-01..10
với ảnh nhiều đối tượng hơn (3-5 chủ thể/cảnh thay vì 1-2) và phụ đề dài hơn
(4 dòng / chủ đề thay vì 2 dòng), để luyện chú thích thực tế hơn.

Mỗi chủ đề vẫn giữ đúng 2 ảnh (scene-01, scene-02) + demo.srt, đúng quy ước
thư mục của Skill — chỉ làm phong phú thêm nội dung bên trong từng ảnh/phụ đề.
Không tạo annotation.json hay video (các thư mục này vẫn là nguyên liệu thô,
để người dùng tự luyện chú thích — xem README.md trong từng thư mục).

Chạy: python examples/make_sample_gallery.py
"""
from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPolygonF

ROOT = Path(__file__).resolve().parent.parent
OUT_ROOT = ROOT / "assets" / "whiteboard"

W, H = 1280, 720
PAPER = QColor("#F5EBD7")
INK = QColor(60, 60, 60)
ORANGE = QColor(214, 124, 43)
BLUE = QColor(74, 108, 176)
RED = QColor(178, 60, 55)


# ──────────────────────────────────────────────────────────────
# Painter cơ bản
# ──────────────────────────────────────────────────────────────
def _new_painter() -> tuple[QImage, QPainter]:
    img = QImage(W, H, QImage.Format_RGB32)
    img.fill(PAPER)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    _pen(p, INK, 5.0)
    return img, p


def _pen(p: QPainter, color: QColor, width: float) -> None:
    pen = QPen(color)
    pen.setWidthF(width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)


# ──────────────────────────────────────────────────────────────
# Các khối vẽ dùng chung (doodle tối giản, không chữ)
# ──────────────────────────────────────────────────────────────
def _sun(p: QPainter, cx: float, cy: float, r: float, color: QColor = ORANGE,
         width: float = 4.0) -> None:
    _pen(p, color, width)
    p.drawEllipse(QPointF(cx, cy), r, r)
    for i in range(8):
        a = i * math.pi / 4
        x0, y0 = cx + math.cos(a) * (r + 10), cy + math.sin(a) * (r + 10)
        x1, y1 = cx + math.cos(a) * (r + 32), cy + math.sin(a) * (r + 32)
        p.drawLine(QPointF(x0, y0), QPointF(x1, y1))


def _moon(p: QPainter, cx: float, cy: float, r: float, color: QColor = INK,
          width: float = 4.0) -> None:
    _pen(p, color, width)
    path = QPainterPath()
    path.arcMoveTo(QRectF(cx - r, cy - r, 2 * r, 2 * r), 60)
    path.arcTo(QRectF(cx - r, cy - r, 2 * r, 2 * r), 60, 260)
    inner = r * 0.78
    path.arcTo(QRectF(cx - inner + r * 0.35, cy - inner, 2 * inner, 2 * inner), 320, -260)
    p.drawPath(path)


def _star(p: QPainter, cx: float, cy: float, r_outer: float, color: QColor = BLUE,
          width: float = 3.0) -> None:
    _pen(p, color, width)
    r_inner = r_outer * 0.45
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = r_outer if i % 2 == 0 else r_inner
        pts.append(QPointF(cx + r * math.cos(ang), cy + r * math.sin(ang)))
    p.drawPolygon(QPolygonF(pts))


def _mountain(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    _pen(p, INK, 5.0)
    poly = QPolygonF([
        QPointF(x, y + h), QPointF(x + w * 0.42, y), QPointF(x + w * 0.62, y + h * 0.34),
        QPointF(x + w * 0.78, y + h * 0.14), QPointF(x + w, y + h),
    ])
    p.drawPolyline(poly)


def _tree(p: QPainter, x: float, y: float, w: float, h: float,
          color: QColor = INK, width: float = 5.0) -> None:
    _pen(p, color, width)
    trunk_w = w * 0.16
    p.drawRect(QRectF(x + w / 2 - trunk_w / 2, y + h * 0.55, trunk_w, h * 0.45))
    p.drawEllipse(QRectF(x, y, w, h * 0.62))


def _cloud(p: QPainter, x: float, y: float, w: float, h: float,
           color: QColor = INK, width: float = 4.0) -> None:
    _pen(p, color, width)
    p.drawEllipse(QRectF(x, y + h * 0.30, w * 0.5, h * 0.7))
    p.drawEllipse(QRectF(x + w * 0.24, y, w * 0.5, h))
    p.drawEllipse(QRectF(x + w * 0.5, y + h * 0.26, w * 0.5, h * 0.72))


def _house(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    _pen(p, INK, 5.0)
    body = QRectF(x, y + h * 0.34, w, h * 0.66)
    p.drawRect(body)
    roof = QPolygonF([
        QPointF(x - w * 0.06, y + h * 0.34), QPointF(x + w / 2, y),
        QPointF(x + w * 1.06, y + h * 0.34),
    ])
    p.drawPolyline(roof)
    _pen(p, BLUE, 4.0)
    p.drawRect(QRectF(x + w * 0.40, y + h * 0.62, w * 0.20, h * 0.38))
    p.drawRect(QRectF(x + w * 0.12, y + h * 0.46, w * 0.18, h * 0.18))
    p.drawRect(QRectF(x + w * 0.70, y + h * 0.46, w * 0.18, h * 0.18))


def _chimney_smoke(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    _pen(p, INK, 3.0)
    p.drawRect(QRectF(x, y + h * 0.65, w * 0.18, h * 0.35))
    for i, dx in enumerate((0.0, 0.35, -0.1)):
        cx = x + w * (0.1 + dx)
        cy = y + h * (0.5 - i * 0.22)
        p.drawEllipse(QPointF(cx, cy), w * 0.14, w * 0.14)


def _bird_v(p: QPainter, x: float, y: float, w: float, h: float,
            color: QColor = INK, width: float = 3.0) -> None:
    _pen(p, color, width)
    pts = [
        QPointF(x, y + h * 0.5), QPointF(x + w * 0.25, y), QPointF(x + w * 0.5, y + h * 0.5),
        QPointF(x + w * 0.75, y), QPointF(x + w, y + h * 0.5),
    ]
    p.drawPolyline(QPolygonF(pts))


def _stick_person(p: QPainter, cx: float, top_y: float, height: float,
                   color: QColor = INK, width: float = 4.0) -> None:
    _pen(p, color, width)
    head_r = height * 0.12
    p.drawEllipse(QPointF(cx, top_y + head_r), head_r, head_r)
    body_top = top_y + head_r * 2
    body_bot = top_y + height * 0.62
    p.drawLine(QPointF(cx, body_top), QPointF(cx, body_bot))
    arm_y = top_y + height * 0.33
    p.drawLine(QPointF(cx, arm_y), QPointF(cx - height * 0.18, arm_y + height * 0.12))
    p.drawLine(QPointF(cx, arm_y), QPointF(cx + height * 0.18, arm_y + height * 0.12))
    p.drawLine(QPointF(cx, body_bot), QPointF(cx - height * 0.15, top_y + height))
    p.drawLine(QPointF(cx, body_bot), QPointF(cx + height * 0.15, top_y + height))


def _wind_lines(p: QPainter, x: float, y: float, w: float, h: float, n: int = 3,
                 color: QColor = BLUE, width: float = 3.0) -> None:
    _pen(p, color, width)
    for i in range(n):
        yy = y + h * (i / max(n - 1, 1))
        p.drawLine(QPointF(x, yy), QPointF(x + w * (0.6 + 0.1 * i), yy + h * 0.04))


def _dog(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    _pen(p, INK, 4.0)
    body = QRectF(x + w * 0.15, y + h * 0.35, w * 0.65, h * 0.35)
    p.drawEllipse(body)
    head_c = QPointF(x + w * 0.85, y + h * 0.35)
    p.drawEllipse(head_c, w * 0.14, w * 0.14)
    p.drawPolyline(QPolygonF([
        QPointF(head_c.x() - w * 0.05, head_c.y() - w * 0.12),
        QPointF(head_c.x() - w * 0.12, head_c.y() - w * 0.22),
    ]))
    for dx in (0.22, 0.45, 0.6, 0.78):
        lx = x + w * dx
        p.drawLine(QPointF(lx, y + h * 0.68), QPointF(lx - w * 0.03, y + h * 0.85))
    p.drawLine(QPointF(x + w * 0.1, y + h * 0.45), QPointF(x - w * 0.08, y + h * 0.3))


def _raindrop(p: QPainter, cx: float, cy: float, size: float,
              color: QColor = BLUE) -> None:
    _pen(p, color, 3.0)
    path = QPainterPath()
    path.moveTo(cx, cy - size)
    path.quadTo(cx + size * 0.55, cy + size * 0.2, cx, cy + size)
    path.quadTo(cx - size * 0.55, cy + size * 0.2, cx, cy - size)
    p.drawPath(path)


def _owl(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    _pen(p, INK, 4.0)
    p.drawEllipse(QRectF(x, y + h * 0.15, w, h * 0.75))
    p.drawPolyline(QPolygonF([
        QPointF(x + w * 0.18, y + h * 0.18), QPointF(x + w * 0.1, y), QPointF(x + w * 0.3, y + h * 0.12),
    ]))
    p.drawPolyline(QPolygonF([
        QPointF(x + w * 0.82, y + h * 0.18), QPointF(x + w * 0.9, y), QPointF(x + w * 0.7, y + h * 0.12),
    ]))
    p.drawEllipse(QPointF(x + w * 0.35, y + h * 0.45), w * 0.1, w * 0.1)
    p.drawEllipse(QPointF(x + w * 0.65, y + h * 0.45), w * 0.1, w * 0.1)
    _pen(p, ORANGE, 3.0)
    p.drawPolyline(QPolygonF([
        QPointF(x + w * 0.46, y + h * 0.58), QPointF(x + w * 0.5, y + h * 0.68),
        QPointF(x + w * 0.54, y + h * 0.58),
    ]))


def _branch(p: QPainter, x: float, y: float, w: float) -> None:
    _pen(p, INK, 4.0)
    p.drawLine(QPointF(x, y), QPointF(x + w, y))


def _shooting_star(p: QPainter, cx: float, cy: float, length: float,
                    color: QColor = ORANGE) -> None:
    _pen(p, color, 3.0)
    p.drawLine(QPointF(cx, cy), QPointF(cx - length, cy + length * 0.4))
    p.setBrush(color)
    p.drawEllipse(QPointF(cx, cy), 7, 7)
    p.setBrush(Qt.NoBrush)


def _umbrella(p: QPainter, x: float, y: float, w: float, h: float,
              color: QColor = RED) -> None:
    _pen(p, color, 4.0)
    cx, cy, a, b = x + w / 2, y + h, w / 2, h
    rect = QRectF(x, y, w, h * 2)
    path = QPainterPath()
    path.arcMoveTo(rect, 180)
    path.arcTo(rect, 180, -180)
    p.drawPath(path)
    canopy_bottom = y + h
    for dx in (0.17, 0.38, 0.62, 0.83):
        ax = x + w * dx
        ratio = (ax - cx) / a
        top_y = cy - b * math.sqrt(max(0.0, 1 - ratio * ratio))
        p.drawLine(QPointF(ax, top_y), QPointF(ax, canopy_bottom))
    _pen(p, INK, 3.0)
    p.drawLine(QPointF(cx, canopy_bottom), QPointF(cx, canopy_bottom + h * 0.9))
    p.drawLine(
        QPointF(cx, canopy_bottom + h * 0.9),
        QPointF(cx + h * 0.22, canopy_bottom + h * 0.78),
    )


def _question_mark(p: QPainter, x: float, y: float, size: float,
                    color: QColor = INK) -> None:
    _pen(p, color, 5.0)
    s = size
    path = QPainterPath()
    path.moveTo(x, y + s * 0.22)
    path.cubicTo(QPointF(x, y - s * 0.05), QPointF(x + s * 0.35, y - s * 0.05),
                 QPointF(x + s * 0.5, y + s * 0.1))
    path.cubicTo(QPointF(x + s * 0.72, y + s * 0.28), QPointF(x + s * 0.72, y + s * 0.5),
                 QPointF(x + s * 0.5, y + s * 0.58))
    path.cubicTo(QPointF(x + s * 0.3, y + s * 0.65), QPointF(x + s * 0.3, y + s * 0.72),
                 QPointF(x + s * 0.3, y + s * 0.78))
    p.drawPath(path)
    p.drawLine(QPointF(x + s * 0.3, y + s * 0.92), QPointF(x + s * 0.3, y + s * 1.08))
    p.drawEllipse(QPointF(x + s * 0.3, y + s * 1.2), size * 0.045, size * 0.045)


def _sparkle(p: QPainter, cx: float, cy: float, r: float, color: QColor = ORANGE) -> None:
    _pen(p, color, 3.0)
    p.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))
    p.drawLine(QPointF(cx, cy - r), QPointF(cx, cy + r))
    p.drawLine(QPointF(cx - r * 0.6, cy - r * 0.6), QPointF(cx + r * 0.6, cy + r * 0.6))
    p.drawLine(QPointF(cx - r * 0.6, cy + r * 0.6), QPointF(cx + r * 0.6, cy - r * 0.6))


def _dust(p: QPainter, x: float, y: float, w: float, h: float, n: int = 5) -> None:
    _pen(p, INK, 2.5)
    for i in range(n):
        cx = x + w * (i / max(n - 1, 1)) + (10 if i % 2 else -10)
        cy = y + h * (0.3 + 0.4 * ((i * 37) % 10) / 10)
        p.drawEllipse(QPointF(cx, cy), 3.0, 3.0)


def _magnifier(p: QPainter, x: float, y: float, r: float, color: QColor = INK) -> None:
    _pen(p, color, 5.0)
    p.drawEllipse(QPointF(x, y), r, r)
    p.drawLine(
        QPointF(x + r * 0.72, y + r * 0.72), QPointF(x + r * 1.5, y + r * 1.5)
    )


def _flower(p: QPainter, cx: float, cy: float, r: float, color: QColor = RED) -> None:
    _pen(p, color, 2.5)
    for i in range(5):
        a = i * 2 * math.pi / 5
        px, py = cx + math.cos(a) * r, cy + math.sin(a) * r
        p.drawEllipse(QPointF(px, py), r * 0.55, r * 0.55)
    _pen(p, ORANGE, 2.5)
    p.drawEllipse(QPointF(cx, cy), r * 0.35, r * 0.35)


def _basket(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    _pen(p, INK, 4.0)
    poly = QPolygonF([
        QPointF(x, y), QPointF(x + w, y), QPointF(x + w * 0.85, y + h), QPointF(x + w * 0.15, y + h),
    ])
    p.drawPolyline(poly)
    p.drawLine(QPointF(x + w * 0.15, y + h), QPointF(x, y))


def _bicycle(p: QPainter, x: float, y: float, w: float, h: float,
             with_rider: bool = False, with_basket: bool = False) -> None:
    _pen(p, INK, 5.0)
    r = min(w * 0.22, h * 0.42)
    wheel1 = QPointF(x + r, y + h - r)
    wheel2 = QPointF(x + w - r, y + h - r)
    p.drawEllipse(wheel1, r, r)
    p.drawEllipse(wheel2, r, r)
    seat = QPointF(x + w * 0.42, y + h * 0.28)
    pedal = QPointF(x + w * 0.3, y + h - r)
    handle = QPointF(x + w * 0.78, y + h * 0.3)
    p.drawPolyline(QPolygonF([pedal, seat, handle]))
    p.drawLine(pedal, wheel1)
    p.drawLine(handle, wheel2)
    p.drawLine(seat, QPointF((wheel1.x() + wheel2.x()) / 2, y + h - r))
    if with_basket:
        _basket(p, handle.x() - w * 0.05, handle.y() - h * 0.22, w * 0.14, h * 0.14)
        _flower(p, handle.x() + w * 0.02, handle.y() - h * 0.28, w * 0.04, RED)
    if with_rider:
        head = QPointF(handle.x() + w * 0.02, y - h * 0.08)
        p.drawEllipse(head, h * 0.11, h * 0.11)
        p.drawLine(QPointF(head.x(), head.y() + h * 0.11), handle)
        p.drawLine(QPointF(head.x() - w * 0.12, head.y() + h * 0.2), QPointF(head.x() + w * 0.12, head.y() + h * 0.2))


def _boat(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    _pen(p, INK, 5.0)
    hull = QPolygonF([
        QPointF(x, y + h * 0.7), QPointF(x + w, y + h * 0.7),
        QPointF(x + w * 0.82, y + h), QPointF(x + w * 0.18, y + h),
    ])
    p.drawPolyline(hull)
    mast = QPointF(x + w * 0.35, y + h * 0.7)
    p.drawLine(mast, QPointF(mast.x(), y))
    p.drawPolyline(QPolygonF([
        QPointF(mast.x(), y), QPointF(mast.x() + w * 0.42, y + h * 0.42), QPointF(mast.x(), y + h * 0.42),
    ]))


def _waves(p: QPainter, x: float, y: float, w: float, h: float, rows: int = 4,
           color: QColor = BLUE) -> None:
    _pen(p, color, 3.0)
    for r in range(rows):
        yy = y + r * h / rows
        path = QPainterPath()
        path.moveTo(x, yy)
        n = 6
        for i in range(n):
            x0 = x + w * i / n
            x1 = x + w * (i + 0.5) / n
            x2 = x + w * (i + 1) / n
            amp = 10 if i % 2 == 0 else -10
            path.quadTo(QPointF(x1, yy + amp), QPointF(x2, yy))
        p.drawPath(path)


def _lightbulb(p: QPainter, cx: float, cy: float, r: float, lit: bool) -> None:
    color = ORANGE if lit else INK
    _pen(p, color, 4.0)
    if lit:
        for i in range(8):
            a = i * math.pi / 4
            x0, y0 = cx + math.cos(a) * (r + 10), cy + math.sin(a) * (r + 10)
            x1, y1 = cx + math.cos(a) * (r + 30), cy + math.sin(a) * (r + 30)
            p.drawLine(QPointF(x0, y0), QPointF(x1, y1))
    p.drawEllipse(QPointF(cx, cy), r, r)
    base_w = r * 0.56
    p.drawPolyline(QPolygonF([
        QPointF(cx - base_w / 2, cy + r), QPointF(cx - base_w / 2, cy + r * 1.5),
        QPointF(cx + base_w / 2, cy + r * 1.5), QPointF(cx + base_w / 2, cy + r),
    ]))
    p.drawLine(QPointF(cx - base_w * 0.4, cy + r * 1.75), QPointF(cx + base_w * 0.4, cy + r * 1.75))


def _book_closed(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    _pen(p, INK, 5.0)
    p.drawRoundedRect(QRectF(x, y, w, h), 6, 6)
    p.drawLine(QPointF(x + w / 2, y), QPointF(x + w / 2, y + h))


def _book_open(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    _pen(p, INK, 5.0)
    cx = x + w / 2
    left = QPolygonF([QPointF(x, y), QPointF(cx, y + h * 0.3), QPointF(cx, y + h * 0.7), QPointF(x, y + h)])
    right = QPolygonF([QPointF(x + w, y), QPointF(cx, y + h * 0.3), QPointF(cx, y + h * 0.7), QPointF(x + w, y + h)])
    p.drawPolyline(left)
    p.drawPolyline(right)
    _pen(p, INK, 1.6)
    for i in range(4):
        ly = y + h * (0.35 + i * 0.12)
        p.drawLine(QPointF(x + w * 0.1, ly), QPointF(cx - w * 0.06, ly - (h * 0.015) * i))
        p.drawLine(QPointF(cx + w * 0.06, ly - (h * 0.015) * i), QPointF(x + w * 0.9, ly))


def _heart(p: QPainter, cx: float, cy: float, size: float, color: QColor = RED) -> None:
    _pen(p, color, 4.0)
    path = QPainterPath()
    path.moveTo(cx, cy + size * 0.35)
    path.cubicTo(QPointF(cx - size * 0.6, cy - size * 0.25), QPointF(cx - size * 0.3, cy - size * 0.7),
                 QPointF(cx, cy - size * 0.25))
    path.cubicTo(QPointF(cx + size * 0.3, cy - size * 0.7), QPointF(cx + size * 0.6, cy - size * 0.25),
                 QPointF(cx, cy + size * 0.35))
    p.drawPath(path)


def _ground(p: QPainter, y: float = H - 86) -> None:
    _pen(p, INK, 5.0)
    p.drawLine(QPointF(0, y), QPointF(W, y))


# ──────────────────────────────────────────────────────────────
# 10 chủ đề — mỗi chủ đề: 2 ảnh (scene-01/02) + 4 dòng phụ đề
# ──────────────────────────────────────────────────────────────
def _srt(cues: list[str]) -> str:
    out, t = [], 0
    step = 4500
    for i, text in enumerate(cues, start=1):
        start, end = t, t + step
        out.append(
            f"{i}\n{_ts(start)} --> {_ts(end)}\n{text}\n"
        )
        t = end
    return "\n".join(out)


def _ts(ms: int) -> str:
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _write(folder: str, base: str, cues: list[str],
           draw1, draw2) -> None:
    out = OUT_ROOT / folder
    out.mkdir(parents=True, exist_ok=True)
    img1, p1 = _new_painter()
    draw1(p1)
    p1.end()
    img1.save(str(out / f"scene-01-{base}.png"))
    img2, p2 = _new_painter()
    draw2(p2)
    p2.end()
    img2.save(str(out / f"scene-02-{base}.png"))
    (out / "demo.srt").write_text(_srt(cues), encoding="utf-8")
    print(f"  {folder}: scene-01-{base}.png, scene-02-{base}.png, demo.srt")


def build() -> None:
    print(f"Ghi vào: {OUT_ROOT}")

    # 1. Mặt trời mọc
    def s1(p):
        _mountain(p, 160, 300, 960, 334)
        _sun(p, 640, 230, 70)
        _bird_v(p, 180, 140, 120, 60)
        _bird_v(p, 940, 170, 110, 55)
    def s2(p):
        _mountain(p, 160, 300, 960, 334)
        _sun(p, 640, 190, 95)
        _cloud(p, 120, 90, 260, 120, color=BLUE, width=3.0)
        _cloud(p, 880, 110, 240, 110, color=BLUE, width=3.0)
        _tree(p, 1040, 360, 160, 260)
        _ground(p)
    _write(
        "sample-01-mat-troi", "mat-troi",
        [
            "Buổi sáng sớm, mặt trời bắt đầu nhô lên sau dãy núi.",
            "Vài chú chim bay về phía ánh nắng ấm áp.",
            "Nắng lên cao, cả bầu trời bừng sáng rực rỡ.",
            "Những đám mây trắng trôi nhẹ ngang qua đỉnh núi.",
        ], s1, s2,
    )

    # 2. Ngôi nhà bên gốc cây
    def s1(p):
        _tree(p, 160, 300, 260, 340)
        _dog(p, 560, 480, 220, 120)
        _ground(p)
    def s2(p):
        _tree(p, 160, 300, 260, 340)
        _house(p, 560, 330, 420, 330)
        _chimney_smoke(p, 900, 260, 70, 160)
        _stick_person(p, 1140, 470, 160)
        _ground(p)
    _write(
        "sample-02-ngoi-nha", "ngoi-nha",
        [
            "Bên gốc cây xanh có một khoảng đất trống yên bình.",
            "Một chú chó nhỏ chạy ngang qua bãi cỏ.",
            "Một ngôi nhà nhỏ xinh được dựng lên cạnh gốc cây.",
            "Khói bay lên từ ống khói, có người đang trên đường về nhà.",
        ], s1, s2,
    )

    # 3. Mây và mưa
    def s1(p):
        _cloud(p, 180, 90, 320, 150)
        _cloud(p, 760, 60, 300, 140)
        _tree(p, 980, 340, 220, 300)
        _wind_lines(p, 1000, 300, 160, 70, n=3)
        _ground(p)
    def s2(p):
        _cloud(p, 180, 70, 340, 160, color=BLUE, width=4.0)
        _cloud(p, 720, 50, 320, 150, color=BLUE, width=4.0)
        for cx in range(160, 1180, 90):
            _raindrop(p, cx, 320 + (cx % 3) * 40, 14)
        _umbrella(p, 500, 420, 220, 130)
        _stick_person(p, 560, 560, 120)
        _stick_person(p, 660, 560, 120)
        _ground(p)
    _write(
        "sample-03-may-mua", "may-mua",
        [
            "Những đám mây trắng nhẹ trôi qua trên bầu trời.",
            "Một cơn gió thổi làm hàng cây nghiêng ngả.",
            "Mây đen kéo đến và những hạt mưa bắt đầu rơi.",
            "Một chiếc ô che cho hai người bạn cùng đi dưới mưa.",
        ], s1, s2,
    )

    # 4. Hạt giống lớn thành cây
    def s1(p):
        _ground(p, y=560)
        _pen(p, QColor(90, 70, 50), 4.0)
        p.drawEllipse(QPointF(640, 560), 90, 34)
        _sun(p, 980, 180, 90)
        _raindrop(p, 520, 260, 30)
        _raindrop(p, 600, 320, 24)
        _raindrop(p, 440, 340, 20)
        _pen(p, ORANGE, 3.0)
        p.drawEllipse(QPointF(640, 536), 13, 13)
    def s2(p):
        _ground(p, y=560)
        _tree(p, 480, 180, 320, 400)
        for cx, cy in [(560, 280), (640, 250), (710, 300), (600, 340), (680, 360), (540, 320)]:
            _pen(p, RED, 2.5)
            p.drawEllipse(QPointF(cx, cy), 9, 9)
        _branch(p, 860, 260, 160)
        _bird_v(p, 900, 220, 90, 46, color=INK, width=3.0)
    _write(
        "sample-04-cay-lon-len", "cay-lon",
        [
            "Một hạt giống nhỏ bé được gieo xuống đất.",
            "Giọt mưa và ánh nắng giúp hạt giống nảy mầm.",
            "Theo thời gian, hạt giống lớn lên thành cây to với trái chín đỏ.",
            "Một chú chim nhỏ đậu trên cành hót vang.",
        ], s1, s2,
    )

    # 5. Bầu trời đêm
    def s1(p):
        _mountain(p, 160, 380, 960, 260)
        _moon(p, 980, 180, 70)
        _branch(p, 180, 420, 220)
        _owl(p, 220, 300, 120, 130)
        _ground(p, y=640)
    def s2(p):
        _mountain(p, 160, 380, 960, 260)
        _moon(p, 980, 180, 70, color=BLUE)
        import random
        random.seed(5)
        placed, tries = [], 0
        while len(placed) < 14 and tries < 400:
            tries += 1
            cx, cy = random.randint(80, 1200), random.randint(60, 340)
            if math.hypot(cx - 220, cy - 90) < 120:
                continue
            placed.append((cx, cy))
        for cx, cy in placed:
            _star(p, cx, cy, random.choice([10, 14, 18]))
        _shooting_star(p, 220, 90, 150)
        _ground(p, y=640)
    _write(
        "sample-05-bau-troi-dem", "bau-troi-dem",
        [
            "Khi hoàng hôn buông xuống, mặt trăng dần hiện ra.",
            "Một chú cú nhỏ đậu trên cành cây khô.",
            "Màn đêm buông xuống, muôn vàn vì sao lấp lánh trên bầu trời.",
            "Một ngôi sao băng vụt qua, mang theo một điều ước.",
        ], s1, s2,
    )

    # 6. Con thuyền ra khơi
    def s1(p):
        _ground(p, y=560)
        _boat(p, 240, 420, 260, 140)
        _bird_v(p, 760, 140, 120, 60)
        for cx in (900, 970, 1040):
            p.drawEllipse(QPointF(cx, 540), 20, 9)
    def s2(p):
        _sun(p, 1080, 130, 80)
        _boat(p, 540, 300, 240, 130)
        _waves(p, 0, 470, W, 180, rows=4)
    _write(
        "sample-06-con-thuyen", "con-thuyen",
        [
            "Con thuyền nhỏ đậu yên bình bên bờ cát.",
            "Chú hải âu bay lượn trên bầu trời xanh.",
            "Thuyền giương buồm ra khơi, vượt qua từng con sóng.",
            "Ánh mặt trời lấp lánh trên mặt biển rộng lớn.",
        ], s1, s2,
    )

    # 7. Ý tưởng loé lên
    def s1(p):
        _lightbulb(p, 500, 340, 90, lit=False)
        _question_mark(p, 740, 240, 180)
    def s2(p):
        _lightbulb(p, 600, 320, 100, lit=True)
        for cx, cy in [(860, 220), (920, 340), (380, 260), (340, 400), (780, 480)]:
            _sparkle(p, cx, cy, 16)
    _write(
        "sample-07-y-tuong", "y-tuong",
        [
            "Một chiếc bóng đèn chưa sáng, như một ý tưởng còn dang dở.",
            "Một dấu chấm hỏi lớn hiện lên bên cạnh, đầy băn khoăn.",
            "Bỗng dưng ý tưởng loé lên, chiếc bóng đèn bừng sáng rực rỡ.",
            "Những tia sáng nhỏ lấp lánh bay quanh, như niềm vui vỡ oà.",
        ], s1, s2,
    )

    # 8. Cuốn sách mở ra
    def s1(p):
        _book_closed(p, 540, 280, 200, 160)
        _dust(p, 520, 220, 260, 60, n=6)
        p2 = p
        _pen(p2, INK, 3.0)
        p2.drawLine(QPointF(460, 460), QPointF(820, 460))
    def s2(p):
        _book_open(p, 360, 260, 560, 200)
        _magnifier(p, 980, 300, 70)
    _write(
        "sample-08-cuon-sach", "cuon-sach",
        [
            "Một cuốn sách đang khép lại, chứa đựng bao điều bí ẩn.",
            "Bụi nhẹ bay lên khi cuốn sách được nhấc lên khỏi kệ.",
            "Sách được mở ra, từng trang chữ dần hiện lên trước mắt.",
            "Một chiếc kính lúp xuất hiện, soi rõ từng con chữ.",
        ], s1, s2,
    )

    # 9. Xe đạp lăn bánh
    def s1(p):
        _ground(p, y=560)
        _bicycle(p, 460, 300, 360, 260, with_basket=True)
    def s2(p):
        _ground(p, y=560)
        _tree(p, 60, 300, 150, 260)
        _tree(p, 1070, 300, 150, 260)
        _bicycle(p, 460, 300, 360, 260, with_rider=True)
        _wind_lines(p, 220, 360, 180, 90, n=3)
    _write(
        "sample-09-xe-dap", "xe-dap",
        [
            "Chiếc xe đạp đang đứng yên, chờ đợi một chuyến đi.",
            "Một giỏ hoa nhỏ được treo phía trước ghi đông.",
            "Xe đạp lăn bánh băng băng, gió thổi tung bay phía sau.",
            "Hai bên đường, hàng cây lướt qua vun vút.",
        ], s1, s2,
    )

    # 10. Hai người, một trái tim
    def s1(p):
        _stick_person(p, 260, 260, 220)
        _stick_person(p, 1020, 260, 220)
        _wind_lines(p, 560, 300, 160, 80, n=3)
        _ground(p, y=560)
    def s2(p):
        _stick_person(p, 480, 260, 220)
        _stick_person(p, 800, 260, 220)
        _heart(p, 640, 330, 90)
        for cx, cy in [(300, 520), (980, 520), (200, 460), (1080, 460)]:
            _flower(p, cx, cy, 16)
        _ground(p, y=560)
    _write(
        "sample-10-trai-tim", "trai-tim",
        [
            "Hai người đứng cách xa nhau, mỗi người một hướng riêng.",
            "Một cơn gió thổi qua, mang theo chút se lạnh.",
            "Họ xích lại gần nhau hơn, trái tim yêu thương kết nối cả hai.",
            "Những bông hoa nhỏ nở rộ xung quanh, chúc mừng khoảnh khắc ấy.",
        ], s1, s2,
    )

    print("Xong.")


if __name__ == "__main__":
    build()
