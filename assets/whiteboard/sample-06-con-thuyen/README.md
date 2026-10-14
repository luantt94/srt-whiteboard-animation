# Ví dụ: `sample-06-con-thuyen` (Con thuyền ra khơi)

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
| 1 | 00:00:00,000 → 00:00:04,500 | Con thuyền nhỏ đậu yên bình bên bờ cát. |
| 2 | 00:00:04,500 → 00:00:09,000 | Chú hải âu bay lượn trên bầu trời xanh. |
| 3 | 00:00:09,000 → 00:00:13,500 | Thuyền giương buồm ra khơi, vượt qua từng con sóng. |
| 4 | 00:00:13,500 → 00:00:18,000 | Ánh mặt trời lấp lánh trên mặt biển rộng lớn. |

Dòng 1-2 → **cảnh 1** (`scene-01`), dòng 3-4 → **cảnh 2** (`scene-02`), mỗi
cảnh 9000ms.

## Nội dung thư mục

| File | Kích thước | Mô tả |
|---|---|---|
| `demo.srt` | — | Phụ đề 4 dòng ở trên. |
| `scene-01-con-thuyen.png` | 1280×720 | Đường bờ cát ngang khung hình; thuyền buồm neo bên trái; **một chú hải âu** (hình chữ V) bay phía trên; vài **viên sỏi** (oval nhỏ) rải bên phải — 4 nhóm chủ thể, chưa có sóng. |
| `scene-02-con-thuyen.png` | 1280×720 | **Mặt trời** toả nắng góc trên phải; thuyền buồm trôi giữa khung; phía dưới là dải **sóng biển** (đường lượn sóng) trải kín chiều rộng — 3 nhóm chủ thể. |

## Gợi ý chú thích (annotation)

Chỉ là gợi ý về **thứ tự/vai trò**; toạ độ `region` chính xác cần tự đo trên
ảnh thật.

**Cảnh 1** (`sceneId: scene-01`, gợi ý `sceneDurationMs: 9000`):

1. `shore` — bối cảnh (đường bờ cát, trải ngang khung hình).
2. `boat` — chủ thể chính (thuyền buồm, bên trái, trên đường bờ). *Khớp phụ đề dòng 1.*
3. `seagull` — chi tiết (hải âu bay phía trên). *Khớp phụ đề dòng 2.*
4. `pebbles` — điểm nhấn nền (vài viên sỏi bên phải, vẽ sau cùng).

**Cảnh 2** (`sceneId: scene-02`) — ảnh nguồn khác hoàn toàn cảnh 1 (bối cảnh
đổi từ bờ sang biển khơi), chú thích độc lập:

1. `sun` — bối cảnh (mặt trời góc trên phải). *Khớp phụ đề dòng 4.*
2. `waves` — bối cảnh (toàn bộ dải sóng phía dưới khung hình). *Khớp phụ đề dòng 3.*
3. `boat` — chủ thể chính / kết quả (thuyền, nay trôi giữa sóng, vẽ sau cùng). *Khớp phụ đề dòng 3.*

## Các bước biến ví dụ này thành video hoàn chỉnh

1. **Phân tích phụ đề** (tuỳ chọn, SRT đã chia sẵn 2 cảnh):
   ```bash
   python scripts/parse_srt.py assets/whiteboard/sample-06-con-thuyen/demo.srt \
     --target-sec 9 --min-sec 5 --max-sec 12
   ```
2. **Tạo `annotation.json`** theo gợi ý trên (gõ tay theo mẫu trong
   `SKILL.md`, hoặc dùng app Studio tab 2 → **Tạo annotation mẫu cho ảnh đang
   chọn**).
3. **Mở bảng Preview** (`assets/preview.html`, Chrome/Edge) → "Mở thư mục"
   → chọn `assets/whiteboard/sample-06-con-thuyen/` → chỉnh vùng/thứ tự/thời
   gian → "Lưu".
4. **Xuất ảnh kiểm tra vùng**:
   ```bash
   python scripts/render_annotation_preview.py \
     assets/whiteboard/sample-06-con-thuyen/scene-01-con-thuyen.png \
     assets/whiteboard/sample-06-con-thuyen/scene-01-con-thuyen.annotation.json \
     assets/whiteboard/sample-06-con-thuyen/scene-01-con-thuyen.regions.png
   ```
5. **Render từng cảnh**:
   ```bash
   <ENV_PY> scripts/render_stream_whiteboard.py \
     assets/whiteboard/sample-06-con-thuyen/scene-01-con-thuyen.png \
     assets/whiteboard/sample-06-con-thuyen/scene-01-con-thuyen.annotation.json \
     assets/whiteboard/sample-06-con-thuyen/scene-01-con-thuyen-whiteboard.mp4 \
     assets/drawing-hand.png --ink-path grid --color-fill contour-wipe
   ```
   Lặp lại cho `scene-02-con-thuyen`. `<ENV_PY>` lấy từ
   `python scripts/prepare_env.py --check`.
6. **Ghép 2 cảnh**:
   ```bash
   <ENV_PY> scripts/merge_scenes.py \
     --inputs assets/whiteboard/sample-06-con-thuyen/scene-01-con-thuyen-whiteboard.mp4 \
              assets/whiteboard/sample-06-con-thuyen/scene-02-con-thuyen-whiteboard.mp4 \
     --output assets/whiteboard/sample-06-con-thuyen/sample-06-con-thuyen-final.mp4
   ```
7. **(Tuỳ chọn, cần `ffmpeg`)** thêm giọng đọc + khắc phụ đề qua
   `scripts/postprocess_video.py` hoặc tab "⚡ Nhanh" của app Studio.

Quy trình đầy đủ (gồm các điểm dừng xác nhận bắt buộc) xem ở
[`SKILL.md`](../../../SKILL.md).
