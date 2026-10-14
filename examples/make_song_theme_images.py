#!/usr/bin/env python3
"""
Vẽ 6 ảnh line-art GỐC (không dùng lời bài hát nào) lấy cảm hứng từ chủ đề
"mẹ - mưa đêm - che chở - vượt gian khó" để thử nghiệm app: đèn khuya, mẹ che
mưa cho con ngủ, mẹ lội qua suối, mẹ dẫn lối qua đồi núi, gió, dòng nước.

Ghi vào assets/whiteboard/me-trong-mua-dem/ — chỉ có ảnh, KHÔNG có file .srt
hay bất kỳ chữ nào (phụ đề do người dùng tự viết/chép, không sao chép lời bài
hát có bản quyền vào đây).

Chạy: python examples/make_song_theme_images.py
"""
from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPolygonF

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "whiteboard" / "me-trong-mua-dem"

W, H = 1280, 720
PAPER = QColor("#F5EBD7")
INK = QColor(60, 60, 60)
ORANGE = QColor(214, 124, 43)
BLUE = QColor(74, 108, 176)


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


def _ground(p: QPainter, y: float = H - 86) -> None:
    _pen(p, INK, 5.0)
    p.drawLine(QPointF(0, y), QPointF(W, y))


def _moon_crescent(p: QPainter, cx: float, cy: float, r: float, color: QColor = INK) -> None:
    _pen(p, color, 4.0)
    path = QPainterPath()
    path.arcMoveTo(QRectF(cx - r, cy - r, 2 * r, 2 * r), 60)
    path.arcTo(QRectF(cx - r, cy - r, 2 * r, 2 * r), 60, 260)
    inner = r * 0.78
    path.arcTo(QRectF(cx - inner + r * 0.35, cy - inner, 2 * inner, 2 * inner), 320, -260)
    p.drawPath(path)


def _star(p: QPainter, cx: float, cy: float, r_outer: float, color: QColor = BLUE) -> None:
    _pen(p, color, 2.5)
    r_inner = r_outer * 0.45
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = r_outer if i % 2 == 0 else r_inner
        pts.append(QPointF(cx + r * math.cos(ang), cy + r * math.sin(ang)))
    p.drawPolygon(QPolygonF(pts))


def _lamp(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    """Đèn dầu kiểu cổ: đế tròn, thân bầu, bóng kính, ngọn lửa cam."""
    _pen(p, INK, 4.5)
    base_r = w * 0.32
    base_cy = y + h * 0.92
    p.drawEllipse(QPointF(x + w / 2, base_cy), base_r, base_r * 0.28)
    p.drawLine(QPointF(x + w * 0.42, base_cy), QPointF(x + w * 0.42, y + h * 0.66))
    p.drawLine(QPointF(x + w * 0.58, base_cy), QPointF(x + w * 0.58, y + h * 0.66))
    bowl_rect = QRectF(x + w * 0.2, y + h * 0.46, w * 0.6, h * 0.22)
    p.drawEllipse(bowl_rect)
    p.drawLine(QPointF(x + w * 0.44, y + h * 0.46), QPointF(x + w * 0.44, y + h * 0.3))
    p.drawLine(QPointF(x + w * 0.56, y + h * 0.46), QPointF(x + w * 0.56, y + h * 0.3))
    glass = QRectF(x + w * 0.3, y + h * 0.02, w * 0.4, h * 0.3)
    p.drawRoundedRect(glass, 6, 6)
    _pen(p, ORANGE, 3.5)
    flame = QPainterPath()
    cx = x + w / 2
    fy = y + h * 0.22
    flame.moveTo(cx, fy)
    flame.cubicTo(QPointF(cx - w * 0.1, fy - h * 0.08), QPointF(cx - w * 0.06, fy - h * 0.2), QPointF(cx, fy - h * 0.24))
    flame.cubicTo(QPointF(cx + w * 0.06, fy - h * 0.2), QPointF(cx + w * 0.1, fy - h * 0.08), QPointF(cx, fy))
    p.drawPath(flame)


def _light_rays(p: QPainter, cx: float, cy: float, r0: float, r1: float, n: int = 10,
                color: QColor = ORANGE) -> None:
    _pen(p, color, 2.2)
    for i in range(n):
        a = -math.pi * 0.85 + i * (math.pi * 1.7) / (n - 1)
        x0, y0 = cx + math.cos(a) * r0, cy + math.sin(a) * r0
        x1, y1 = cx + math.cos(a) * r1, cy + math.sin(a) * r1
        p.drawLine(QPointF(x0, y0), QPointF(x1, y1))


def _stool(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    _pen(p, INK, 4.0)
    p.drawLine(QPointF(x, y), QPointF(x + w, y))
    p.drawLine(QPointF(x + w * 0.1, y), QPointF(x + w * 0.02, y + h))
    p.drawLine(QPointF(x + w * 0.9, y), QPointF(x + w * 0.98, y + h))


def _mother_figure(p: QPainter, cx: float, top_y: float, height: float,
                    color: QColor = INK, arms_out: bool = True) -> None:
    """Dáng người đội nón lá, mặc áo dài đơn giản — biểu tượng chung vẽ bằng
    nét/khối hình học tối giản (đầu tròn + nón hình nón + thân chữ A + chân),
    không mô phỏng người thật hay nhân vật cụ thể nào."""
    _pen(p, color, 4.0)
    head_r = height * 0.07
    head_cy = top_y + height * 0.16
    p.drawEllipse(QPointF(cx, head_cy), head_r, head_r)

    hat_w, hat_h = height * 0.30, height * 0.11
    hat_top_y = head_cy - head_r * 1.6
    hat = QPolygonF([
        QPointF(cx, hat_top_y), QPointF(cx - hat_w / 2, hat_top_y + hat_h),
        QPointF(cx + hat_w / 2, hat_top_y + hat_h),
    ])
    p.drawPolyline(hat)
    p.drawLine(QPointF(cx - hat_w / 2, hat_top_y + hat_h), QPointF(cx + hat_w / 2, hat_top_y + hat_h))

    neck_y = head_cy + head_r * 1.1
    shoulder_w = height * 0.2
    hem_w = height * 0.46
    hem_y = top_y + height * 0.86
    body = QPolygonF([
        QPointF(cx - shoulder_w / 2, neck_y), QPointF(cx + shoulder_w / 2, neck_y),
        QPointF(cx + hem_w / 2, hem_y), QPointF(cx - hem_w / 2, hem_y),
    ])
    p.drawPolyline(body)
    p.drawLine(QPointF(cx - shoulder_w / 2, neck_y), QPointF(cx - hem_w / 2, hem_y))
    if arms_out:
        arm_y = neck_y + height * 0.12
        p.drawLine(QPointF(cx - shoulder_w / 2, arm_y), QPointF(cx - hem_w * 0.62, arm_y + height * 0.1))
        p.drawLine(QPointF(cx + shoulder_w / 2, arm_y), QPointF(cx + hem_w * 0.62, arm_y + height * 0.1))
    p.drawLine(QPointF(cx - hem_w * 0.18, hem_y), QPointF(cx - hem_w * 0.22, top_y + height))
    p.drawLine(QPointF(cx + hem_w * 0.18, hem_y), QPointF(cx + hem_w * 0.22, top_y + height))


def _rain(p: QPainter, x: float, y: float, w: float, h: float, n: int = 16,
          color: QColor = BLUE) -> None:
    _pen(p, color, 2.2)
    for i in range(n):
        rx = x + w * (i / (n - 1))
        ry = y + (h * 0.3 if i % 2 else 0)
        p.drawLine(QPointF(rx, ry), QPointF(rx - h * 0.12, ry + h * 0.55))


def _roof(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    """Mái tranh đơn sơ che phía trên — không phải nhà cụ thể, chỉ là chỗ trú."""
    _pen(p, INK, 4.5)
    poly = QPolygonF([
        QPointF(x, y + h), QPointF(x + w / 2, y), QPointF(x + w, y + h),
    ])
    p.drawPolyline(poly)
    for i in range(1, 5):
        yy = y + h * (0.25 * i)
        xx0 = x + (w / 2 - 0) * (i * 0.0)
        p.drawLine(QPointF(x + w * 0.08 * i, y + h * (1 - 0.0)), QPointF(x + w * 0.08 * i, y + h))
    _pen(p, INK, 2.0)
    for i in range(6):
        t = i / 5
        xx = x + w * 0.1 + w * 0.8 * t
        yy = y + h * (1 - abs(t - 0.5) * 1.4)
        p.drawLine(QPointF(xx, max(y, yy)), QPointF(xx, y + h))


def _sleeping_child(p: QPainter, x: float, y: float, w: float, h: float) -> None:
    _pen(p, INK, 3.5)
    p.drawEllipse(QPointF(x + w * 0.18, y + h * 0.4), w * 0.13, w * 0.13)
    path = QPainterPath()
    path.moveTo(x + w * 0.3, y + h * 0.5)
    path.quadTo(QPointF(x + w * 0.65, y), QPointF(x + w, y + h * 0.3))
    path.quadTo(QPointF(x + w * 0.65, y + h), QPointF(x + w * 0.3, y + h * 0.5))
    p.drawPath(path)


def _stream(p: QPainter, x: float, y: float, w: float, h: float, rows: int = 5,
            color: QColor = BLUE) -> None:
    _pen(p, color, 3.0)
    for r in range(rows):
        yy = y + r * h / rows
        path = QPainterPath()
        path.moveTo(x, yy)
        n = 7
        for i in range(n):
            x1 = x + w * (i + 0.5) / n
            x2 = x + w * (i + 1) / n
            amp = 9 if i % 2 == 0 else -9
            path.quadTo(QPointF(x1, yy + amp), QPointF(x2, yy))
        p.drawPath(path)


def _hill(p: QPainter, x: float, y: float, w: float, h: float, color: QColor = INK) -> None:
    _pen(p, color, 4.0)
    path = QPainterPath()
    path.moveTo(x, y + h)
    path.quadTo(QPointF(x + w * 0.5, y), QPointF(x + w, y + h))
    p.drawPath(path)


def _path_dashes(p: QPainter, pts: list[tuple[float, float]], color: QColor = INK) -> None:
    _pen(p, color, 3.0)
    pen = p.pen()
    pen.setStyle(Qt.DashLine)
    p.setPen(pen)
    poly = QPolygonF([QPointF(x, y) for x, y in pts])
    p.drawPolyline(poly)


def _wind_spiral(p: QPainter, cx: float, cy: float, r_max: float, turns: float = 2.6,
                  color: QColor = BLUE) -> None:
    _pen(p, color, 3.5)
    path = QPainterPath()
    steps = 140
    first = True
    for i in range(steps + 1):
        t = i / steps
        a = t * turns * 2 * math.pi
        r = r_max * t
        x = cx + math.cos(a) * r
        y = cy + math.sin(a) * r * 0.75
        if first:
            path.moveTo(x, y)
            first = False
        else:
            path.lineTo(x, y)
    p.drawPath(path)


def _leaf(p: QPainter, cx: float, cy: float, size: float, angle: float, color: QColor = INK) -> None:
    _pen(p, color, 2.5)
    p.save()
    p.translate(cx, cy)
    p.rotate(angle)
    path = QPainterPath()
    path.moveTo(0, 0)
    path.quadTo(QPointF(size * 0.3, -size * 0.35), QPointF(size, 0))
    path.quadTo(QPointF(size * 0.3, size * 0.35), QPointF(0, 0))
    p.drawPath(path)
    p.restore()


def _ripple(p: QPainter, cx: float, cy: float, radii: list[float], color: QColor = BLUE) -> None:
    _pen(p, color, 2.5)
    for r in radii:
        p.drawEllipse(QPointF(cx, cy), r, r * 0.42)


def _river(p: QPainter, x: float, y: float, w: float, h: float, color: QColor = BLUE) -> None:
    _pen(p, color, 3.0)
    for row in range(4):
        yy = y + row * h / 4
        path = QPainterPath()
        path.moveTo(x, yy)
        n = 8
        for i in range(n):
            x1 = x + w * (i + 0.5) / n
            x2 = x + w * (i + 1) / n
            amp = 7 if i % 2 == 0 else -7
            path.quadTo(QPointF(x1, yy + amp), QPointF(x2, yy))
        p.drawPath(path)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. Đèn khuya — tĩnh lặng ngồi nhớ lại
    img, p = _new_painter()
    _lamp(p, 540, 300, 200, 320)
    _light_rays(p, 640, 400, 90, 150, n=10)
    _moon_crescent(p, 1080, 150, 60, color=BLUE)
    _stool(p, 420, 600, 140, 90)
    _ground(p)
    p.end()
    img.save(str(OUT / "scene-01-den-khuya.png"))

    # 2. Mẹ che mưa cho con ngủ dưới mái tranh
    img, p = _new_painter()
    _roof(p, 420, 260, 440, 220)
    _sleeping_child(p, 470, 470, 150, 90)
    _sleeping_child(p, 650, 470, 150, 90)
    _mother_figure(p, 1000, 220, 380, arms_out=True)
    _rain(p, 0, 0, W, 260, n=22)
    _ground(p)
    p.end()
    img.save(str(OUT / "scene-02-me-che-mua.png"))

    # 3. Mẹ lội qua con suối giữa mưa
    img, p = _new_painter()
    _hill(p, 0, 380, 500, 260)
    _hill(p, 700, 400, 580, 240)
    _stream(p, 140, 560, 1000, 120)
    _mother_figure(p, 640, 320, 300, arms_out=False)
    _rain(p, 0, 0, W, 300, n=20)
    p.end()
    img.save(str(OUT / "scene-03-me-qua-suoi.png"))

    # 4. Mẹ dẫn lối qua đồi núi trong đêm
    img, p = _new_painter()
    _hill(p, -60, 420, 700, 260, color=INK)
    _hill(p, 520, 360, 820, 320, color=INK)
    for cx, cy in [(120, 90), (260, 60), (980, 70), (1140, 130), (60, 180)]:
        _star(p, cx, cy, 10)
    _moon_crescent(p, 1040, 150, 70, color=BLUE)
    _path_dashes(p, [(300, 640), (430, 560), (560, 600), (680, 500), (800, 540)])
    _mother_figure(p, 430, 380, 260, arms_out=False)
    p.end()
    img.save(str(OUT / "scene-04-me-dan-loi.png"))

    # 5. Gió (ẩn dụ) — vệt xoáy nhẹ cuốn theo vài chiếc lá
    img, p = _new_painter()
    _wind_spiral(p, 500, 340, 220, turns=2.4)
    _wind_spiral(p, 880, 420, 150, turns=1.8, color=INK)
    for cx, cy, a in [(760, 260, 20), (920, 300, -30), (640, 480, 60), (300, 200, 10)]:
        _leaf(p, cx, cy, 46, a)
    _ground(p)
    p.end()
    img.save(str(OUT / "scene-05-gio.png"))

    # 6. Nước (ẩn dụ) — dòng chảy hiền hoà, gợn sóng loang
    img, p = _new_painter()
    _river(p, 0, 420, W, 220)
    _ripple(p, 420, 300, [20, 40, 62, 86])
    _ripple(p, 900, 220, [16, 32, 50])
    _hill(p, 60, 120, 420, 180, color=INK)
    p.end()
    img.save(str(OUT / "scene-06-nuoc.png"))

    print(f"Đã tạo 6 ảnh gốc (không chứa lời bài hát) tại: {OUT}")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name}")


if __name__ == "__main__":
    build()
