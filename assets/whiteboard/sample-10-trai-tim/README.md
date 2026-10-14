# Ví dụ: `sample-10-trai-tim` (Hai người, một trái tim)

> **Đây là nguyên liệu thô**, chưa qua chú thích: chỉ có phụ đề + 2 ảnh
> line-art, **chưa có** `annotation.json` hay video render sẵn. Dùng thư mục
> này để tự luyện tập từ **bước 3 trở đi** của quy trình trong `SKILL.md`.
> Ví dụ đã làm xong toàn bộ quy trình: xem
> [`assets/whiteboard/demo-phong-canh/`](../demo-phong-canh/README.md).
>
> Ảnh tạo bằng `python examples/make_sample_gallery.py` — chạy lại script đó
> bất kỳ lúc nào để phục hồi về đúng trạng thái gốc.

## Câu chuyện (4 dòng phụ đề → 2 cảnh)

| # | Thời gian | Phụ đề |
|---|---|---|
| 1 | 00:00:00,000 → 00:00:04,500 | Hai người đứng cách xa nhau, mỗi người một hướng riêng. |
| 2 | 00:00:04,500 → 00:00:09,000 | Một cơn gió thổi qua, mang theo chút se lạnh. |
| 3 | 00:00:09,000 → 00:00:13,500 | Họ xích lại gần nhau hơn, trái tim yêu thương kết nối cả hai. |
| 4 | 00:00:13,500 → 00:00:18,000 | Những bông hoa nhỏ nở rộ xung quanh, chúc mừng khoảnh khắc ấy. |

Dòng 1-2 → **cảnh 1** (`scene-01`), dòng 3-4 → **cảnh 2** (`scene-02`), mỗi
cảnh 9000ms.

## Nội dung thư mục

| File | Kích thước | Mô tả |
|---|---|---|
| `demo.srt` | — | Phụ đề 4 dòng ở trên. |
| `scene-01-trai-tim.png` | 1280×720 | Hai hình người que đứng ở hai mép trái/phải khung hình; **vài nét gió** (đường xiên xanh) ở giữa — 3 nhóm chủ thể, khoảng cách lớn giữa hai người. |
| `scene-02-trai-tim.png` | 1280×720 | Hai hình người que xích lại gần hơn (gần giữa khung); **một trái tim đỏ** ở chính giữa; **4 cụm hoa nhỏ** (đỏ/cam) rải hai bên dưới — 3 nhóm chủ thể. |

## Gợi ý chú thích (annotation)

Chỉ là gợi ý về **thứ tự/vai trò**; toạ độ `region` chính xác cần tự đo trên
ảnh thật.

**Cảnh 1** (`sceneId: scene-01`, gợi ý `sceneDurationMs: 9000`):

1. `person-left` — bối cảnh (người bên trái). *Khớp phụ đề dòng 1.*
2. `person-right` — bối cảnh tiếp nối (người bên phải). *Khớp phụ đề dòng 1.*
3. `wind` — chi tiết (vài nét gió ở giữa, vẽ sau cùng). *Khớp phụ đề dòng 2.*

**Cảnh 2** (`sceneId: scene-02`) — ảnh nguồn khác cảnh 1 (vị trí 2 người thay
đổi, thêm trái tim + hoa), chú thích độc lập:

1. `person-left` — bối cảnh (người bên trái, nay gần giữa hơn).
2. `person-right` — bối cảnh (người bên phải, nay gần giữa hơn).
3. `heart` — chủ thể chính / kết quả (trái tim đỏ, chính giữa). *Khớp phụ đề dòng 3.*
4. `flowers` — điểm nhấn kết (4 cụm hoa hai bên dưới, vẽ sau cùng). *Khớp phụ đề dòng 4.*

## Các bước biến ví dụ này thành video hoàn chỉnh

1. **Phân tích phụ đề** (tuỳ chọn, SRT đã chia sẵn 2 cảnh):
   ```bash
   python scripts/parse_srt.py assets/whiteboard/sample-10-trai-tim/demo.srt \
     --target-sec 9 --min-sec 5 --max-sec 12
   ```
2. **Tạo `annotation.json`** theo gợi ý trên (gõ tay theo mẫu trong
   `SKILL.md`, hoặc dùng app Studio tab 2 → **Tạo annotation mẫu cho ảnh đang
   chọn**).
3. **Mở bảng Preview** (`assets/preview.html`, Chrome/Edge) → "Mở thư mục"
   → chọn `assets/whiteboard/sample-10-trai-tim/` → chỉnh vùng/thứ tự/thời
   gian → "Lưu".
4. **Xuất ảnh kiểm tra vùng**:
   ```bash
   python scripts/render_annotation_preview.py \
     assets/whiteboard/sample-10-trai-tim/scene-01-trai-tim.png \
     assets/whiteboard/sample-10-trai-tim/scene-01-trai-tim.annotation.json \
     assets/whiteboard/sample-10-trai-tim/scene-01-trai-tim.regions.png
   ```
5. **Render từng cảnh**:
   ```bash
   <ENV_PY> scripts/render_stream_whiteboard.py \
     assets/whiteboard/sample-10-trai-tim/scene-01-trai-tim.png \
     assets/whiteboard/sample-10-trai-tim/scene-01-trai-tim.annotation.json \
     assets/whiteboard/sample-10-trai-tim/scene-01-trai-tim-whiteboard.mp4 \
     assets/drawing-hand.png --ink-path grid --color-fill contour-wipe
   ```
   Lặp lại cho `scene-02-trai-tim`. `<ENV_PY>` lấy từ
   `python scripts/prepare_env.py --check`.
6. **Ghép 2 cảnh**:
   ```bash
   <ENV_PY> scripts/merge_scenes.py \
     --inputs assets/whiteboard/sample-10-trai-tim/scene-01-trai-tim-whiteboard.mp4 \
              assets/whiteboard/sample-10-trai-tim/scene-02-trai-tim-whiteboard.mp4 \
     --output assets/whiteboard/sample-10-trai-tim/sample-10-trai-tim-final.mp4
   ```
7. **(Tuỳ chọn, cần `ffmpeg`)** thêm giọng đọc + khắc phụ đề qua
   `scripts/postprocess_video.py` hoặc tab "⚡ Nhanh" của app Studio.

Quy trình đầy đủ (gồm các điểm dừng xác nhận bắt buộc) xem ở
[`SKILL.md`](../../../SKILL.md).
