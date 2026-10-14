# Ví dụ: `sample-03-may-mua` (Mây đen và mưa)

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
| 1 | 00:00:00,000 → 00:00:04,500 | Những đám mây trắng nhẹ trôi qua trên bầu trời. |
| 2 | 00:00:04,500 → 00:00:09,000 | Một cơn gió thổi làm hàng cây nghiêng ngả. |
| 3 | 00:00:09,000 → 00:00:13,500 | Mây đen kéo đến và những hạt mưa bắt đầu rơi. |
| 4 | 00:00:13,500 → 00:00:18,000 | Một chiếc ô che cho hai người bạn cùng đi dưới mưa. |

Dòng 1-2 → **cảnh 1** (`scene-01`), dòng 3-4 → **cảnh 2** (`scene-02`), mỗi
cảnh 9000ms.

## Nội dung thư mục

| File | Kích thước | Mô tả |
|---|---|---|
| `demo.srt` | — | Phụ đề 4 dòng ở trên. |
| `scene-01-may-mua.png` | 1280×720 | Hai cụm mây (nét xám nhạt) ở nửa trên; **một cái cây** bên phải với **vài nét gió** (đường xiên xanh) thổi cạnh tán cây — 3 nhóm chủ thể. |
| `scene-02-may-mua.png` | 1280×720 | Hai cụm mây đã chuyển màu xanh đậm; một dải **hạt mưa** (giọt nước) phía dưới mây; **một chiếc ô đỏ** và **2 người (hình que)** đứng dưới ô, trên đường mặt đất — 5 nhóm chủ thể. |

## Gợi ý chú thích (annotation)

Chỉ là gợi ý về **thứ tự/vai trò**; toạ độ `region` chính xác cần tự đo trên
ảnh thật.

**Cảnh 1** (`sceneId: scene-01`, gợi ý `sceneDurationMs: 9000`):

1. `clouds` — bối cảnh (2 cụm mây, nửa trên khung hình). *Khớp phụ đề dòng 1.*
2. `tree` — chủ thể chính (cây bên phải). *Khớp phụ đề dòng 2.*
3. `wind` — chi tiết (các nét gió cạnh tán cây, vẽ sau cùng). *Khớp phụ đề dòng 2.*

**Cảnh 2** (`sceneId: scene-02`) — ảnh nguồn khác cảnh 1 (mây đổi màu, thêm
mưa/ô/người), chú thích độc lập:

1. `clouds-dark` — bối cảnh (2 cụm mây đậm màu). *Khớp phụ đề dòng 3.*
2. `rain` — chi tiết (dải hạt mưa phía dưới mây). *Khớp phụ đề dòng 3.*
3. `umbrella` — chủ thể chính (ô đỏ, chính giữa). *Khớp phụ đề dòng 4.*
4. `people` — kết quả (2 người đứng dưới ô, vẽ sau cùng — có thể tách `person-left`/`person-right`). *Khớp phụ đề dòng 4.*

## Các bước biến ví dụ này thành video hoàn chỉnh

1. **Phân tích phụ đề** (tuỳ chọn, SRT đã chia sẵn 2 cảnh):
   ```bash
   python scripts/parse_srt.py assets/whiteboard/sample-03-may-mua/demo.srt \
     --target-sec 9 --min-sec 5 --max-sec 12
   ```
2. **Tạo `annotation.json`** theo gợi ý trên (gõ tay theo mẫu trong
   `SKILL.md`, hoặc dùng app Studio tab 2 → **Tạo annotation mẫu cho ảnh đang
   chọn**).
3. **Mở bảng Preview** (`assets/preview.html`, Chrome/Edge) → "Mở thư mục"
   → chọn `assets/whiteboard/sample-03-may-mua/` → chỉnh vùng/thứ tự/thời
   gian → "Lưu".
4. **Xuất ảnh kiểm tra vùng**:
   ```bash
   python scripts/render_annotation_preview.py \
     assets/whiteboard/sample-03-may-mua/scene-01-may-mua.png \
     assets/whiteboard/sample-03-may-mua/scene-01-may-mua.annotation.json \
     assets/whiteboard/sample-03-may-mua/scene-01-may-mua.regions.png
   ```
5. **Render từng cảnh**:
   ```bash
   <ENV_PY> scripts/render_stream_whiteboard.py \
     assets/whiteboard/sample-03-may-mua/scene-01-may-mua.png \
     assets/whiteboard/sample-03-may-mua/scene-01-may-mua.annotation.json \
     assets/whiteboard/sample-03-may-mua/scene-01-may-mua-whiteboard.mp4 \
     assets/drawing-hand.png --ink-path grid --color-fill contour-wipe
   ```
   Lặp lại cho `scene-02-may-mua`. `<ENV_PY>` lấy từ
   `python scripts/prepare_env.py --check`.
6. **Ghép 2 cảnh**:
   ```bash
   <ENV_PY> scripts/merge_scenes.py \
     --inputs assets/whiteboard/sample-03-may-mua/scene-01-may-mua-whiteboard.mp4 \
              assets/whiteboard/sample-03-may-mua/scene-02-may-mua-whiteboard.mp4 \
     --output assets/whiteboard/sample-03-may-mua/sample-03-may-mua-final.mp4
   ```
7. **(Tuỳ chọn, cần `ffmpeg`)** thêm giọng đọc + khắc phụ đề qua
   `scripts/postprocess_video.py` hoặc tab "⚡ Nhanh" của app Studio.

Quy trình đầy đủ (gồm các điểm dừng xác nhận bắt buộc) xem ở
[`SKILL.md`](../../../SKILL.md).
