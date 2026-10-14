#!/usr/bin/env python3
"""
Tạo dữ liệu mẫu để chạy thử SRT Whiteboard Studio ngay lập tức.

Sinh ra thư mục assets/whiteboard/demo-phong-canh/ gồm:
  - demo.srt                     phụ đề tiếng Việt (4 dòng, 2 cảnh)
  - scenes.json                  kết quả phân cảnh dựng sẵn (2 cảnh)
  - scene-01-binh-minh.png       line-art cảnh 1 (mặt trời · núi · cây)
  - scene-01-binh-minh.annotation.json
  - scene-02-ngoi-nha.png        line-art cảnh 2 (mây · ngôi nhà · chim)
  - scene-02-ngoi-nha.annotation.json

Ảnh được vẽ bằng QPainter (nét xám tối giản trên nền giấy vàng kem #F5EBD7,
không chữ) đúng tinh thần quy chuẩn hình ảnh của skill.

Chạy: python examples/make_demo_project.py
"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPolygonF
from PySide6.QtCore import QPointF

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "whiteboard" / "demo-phong-canh"

W, H = 1280, 720
PAPER = QColor("#F5EBD7")
INK = QColor(60, 60, 60)


def _new_painter() -> tuple[QImage, QPainter]:
    img = QImage(W, H, QImage.Format_RGB32)
    img.fill(PAPER)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(INK)
    pen.setWidthF(5.0)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    return img, p


def _sun(p: QPainter, cx: int, cy: int, r: int) -> None:
    p.drawEllipse(QPointF(cx, cy), r, r)
    import math
    for i in range(8):
        a = i * math.pi / 4
        x0 = cx + math.cos(a) * (r + 14)
        y0 = cy + math.sin(a) * (r + 14)
        x1 = cx + math.cos(a) * (r + 44)
        y1 = cy + math.sin(a) * (r + 44)
        p.drawLine(QPointF(x0, y0), QPointF(x1, y1))


def _mountain(p: QPainter, x: int, y: int, w: int, h: int) -> None:
    poly = QPolygonF([
        QPointF(x, y + h),
        QPointF(x + w * 0.42, y),
        QPointF(x + w * 0.62, y + h * 0.34),
        QPointF(x + w * 0.78, y + h * 0.14),
        QPointF(x + w, y + h),
    ])
    p.drawPolyline(poly)
    p.drawLine(QPointF(x + w * 0.30, y + h * 0.42),
               QPointF(x + w * 0.42, y))
    p.drawLine(QPointF(x + w * 0.42, y),
               QPointF(x + w * 0.52, y + h * 0.30))


def _tree(p: QPainter, x: int, y: int, w: int, h: int) -> None:
    trunk_w = w * 0.16
    p.drawRect(QRectF(x + w / 2 - trunk_w / 2, y + h * 0.55, trunk_w, h * 0.45))
    p.drawEllipse(QRectF(x, y, w, h * 0.62))


def _cloud(p: QPainter, x: int, y: int, w: int, h: int) -> None:
    p.drawEllipse(QRectF(x, y + h * 0.30, w * 0.5, h * 0.7))
    p.drawEllipse(QRectF(x + w * 0.24, y, w * 0.5, h))
    p.drawEllipse(QRectF(x + w * 0.5, y + h * 0.26, w * 0.5, h * 0.72))


def _house(p: QPainter, x: int, y: int, w: int, h: int) -> None:
    body = QRectF(x, y + h * 0.34, w, h * 0.66)
    p.drawRect(body)
    roof = QPolygonF([
        QPointF(x - w * 0.06, y + h * 0.34),
        QPointF(x + w / 2, y),
        QPointF(x + w * 1.06, y + h * 0.34),
    ])
    p.drawPolyline(roof)
    p.drawRect(QRectF(x + w * 0.40, y + h * 0.62, w * 0.20, h * 0.38))
    p.drawRect(QRectF(x + w * 0.12, y + h * 0.46, w * 0.18, h * 0.18))


def _bird(p: QPainter, x: int, y: int, w: int, h: int) -> None:
    path_pts = [
        QPointF(x, y + h * 0.5),
        QPointF(x + w * 0.25, y),
        QPointF(x + w * 0.5, y + h * 0.5),
        QPointF(x + w * 0.75, y),
        QPointF(x + w, y + h * 0.5),
    ]
    p.drawPolyline(QPolygonF(path_pts))


def _element(eid, label, seq, role, subtitle, region, start, dur):
    x, y, w, h = region
    return {
        "id": eid,
        "label": label,
        "sequence": seq,
        "narrativeRole": role,
        "subtitle": subtitle,
        "type": "structure",
        "region": {"x": x, "y": y, "width": w, "height": h},
        "reveal": {
            "direction": "top_to_bottom",
            "startMs": start,
            "durationMs": dur,
            "maskPaddingPx": 20,
            "protectedRegions": [],
        },
        "handPath": {
            "start": [x + w // 2, y + int(h * 0.1)],
            "end": [x + w // 2, y + int(h * 0.9)],
            "easing": "easeInOut",
        },
    }


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # ── Cảnh 1: bình minh ──
    img1, p1 = _new_painter()
    _mountain(p1, 340, 300, 600, 380)
    _sun(p1, 250, 190, 90)
    _tree(p1, 980, 280, 230, 380)
    p1.end()
    img1.save(str(OUT / "scene-01-binh-minh.png"))

    ann1 = {
        "sceneId": "scene-01",
        "canvas": {"width": W, "height": H},
        "storyBasis": "Buổi sáng, mặt trời nhô lên sau ngọn núi; một cái cây "
                      "nhỏ đứng lặng bên sườn đồi.",
        "sceneDurationMs": 8600,
        "elements": [
            _element("sun", "Mặt trời", 1, "bối cảnh bầu trời",
                     "Buổi sáng, mặt trời nhô lên sau ngọn núi.",
                     (110, 60, 310, 300), 300, 2400),
            _element("mountain", "Ngọn núi", 2, "chủ thể chính",
                     "Buổi sáng, mặt trời nhô lên sau ngọn núi.",
                     (330, 285, 620, 400), 2900, 2800),
            _element("tree", "Cái cây", 3, "phản ứng / khép cảnh",
                     "Một cái cây nhỏ đứng lặng bên sườn đồi.",
                     (975, 270, 245, 400), 5900, 2400),
        ],
    }
    (OUT / "scene-01-binh-minh.annotation.json").write_text(
        json.dumps(ann1, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ── Cảnh 2: ngôi nhà ──
    img2, p2 = _new_painter()
    _house(p2, 470, 340, 380, 320)
    _cloud(p2, 150, 90, 400, 190)
    _bird(p2, 940, 150, 240, 150)
    p2.end()
    img2.save(str(OUT / "scene-02-ngoi-nha.png"))

    ann2 = {
        "sceneId": "scene-02",
        "canvas": {"width": W, "height": H},
        "storyBasis": "Trưa đến, ngôi nhà nhỏ hiện ra giữa đồng; một chú chim "
                      "bay ngang qua đám mây trắng.",
        "sceneDurationMs": 8600,
        "elements": [
            _element("cloud", "Đám mây", 1, "bối cảnh bầu trời",
                     "Một chú chim bay ngang qua đám mây trắng.",
                     (120, 55, 470, 270), 300, 2400),
            _element("house", "Ngôi nhà", 2, "chủ thể chính",
                     "Trưa đến, ngôi nhà nhỏ hiện ra giữa đồng.",
                     (440, 300, 445, 385), 2900, 2900),
            _element("bird", "Chú chim", 3, "hành động / khép cảnh",
                     "Một chú chim bay ngang qua đám mây trắng.",
                     (890, 100, 335, 250), 6000, 2200),
        ],
    }
    (OUT / "scene-02-ngoi-nha.annotation.json").write_text(
        json.dumps(ann2, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ── demo.srt ──
    srt = (
        "1\n00:00:00,000 --> 00:00:04,300\n"
        "Buổi sáng, mặt trời nhô lên sau ngọn núi.\n\n"
        "2\n00:00:04,300 --> 00:00:08,600\n"
        "Một cái cây nhỏ đứng lặng bên sườn đồi.\n\n"
        "3\n00:00:08,600 --> 00:00:13,000\n"
        "Trưa đến, ngôi nhà nhỏ hiện ra giữa đồng.\n\n"
        "4\n00:00:13,000 --> 00:00:17,200\n"
        "Một chú chim bay ngang qua đám mây trắng.\n"
    )
    (OUT / "demo.srt").write_text(srt, encoding="utf-8")

    # ── scenes.json dựng sẵn (2 cảnh) ──
    cues = [
        {"index": 1, "startMs": 0, "endMs": 4300, "durMs": 4300,
         "text": "Buổi sáng, mặt trời nhô lên sau ngọn núi."},
        {"index": 2, "startMs": 4300, "endMs": 8600, "durMs": 4300,
         "text": "Một cái cây nhỏ đứng lặng bên sườn đồi."},
        {"index": 3, "startMs": 8600, "endMs": 13000, "durMs": 4400,
         "text": "Trưa đến, ngôi nhà nhỏ hiện ra giữa đồng."},
        {"index": 4, "startMs": 13000, "endMs": 17200, "durMs": 4200,
         "text": "Một chú chim bay ngang qua đám mây trắng."},
    ]
    scenes = [
        {"sceneIndex": 1, "startMs": 0, "endMs": 8600, "sceneDurationMs": 8600,
         "cueRange": [1, 2],
         "text": "Buổi sáng, mặt trời nhô lên sau ngọn núi. "
                 "Một cái cây nhỏ đứng lặng bên sườn đồi."},
        {"sceneIndex": 2, "startMs": 8600, "endMs": 17200,
         "sceneDurationMs": 8600, "cueRange": [3, 4],
         "text": "Trưa đến, ngôi nhà nhỏ hiện ra giữa đồng. "
                 "Một chú chim bay ngang qua đám mây trắng."},
    ]
    (OUT / "scenes.json").write_text(
        json.dumps({"cues": cues, "scenes": scenes}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Đã tạo dữ liệu mẫu tại: {OUT}")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name}")


if __name__ == "__main__":
    build()
