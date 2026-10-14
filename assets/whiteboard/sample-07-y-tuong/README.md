# Ví dụ: `sample-07-y-tuong` (Ý tưởng loé lên)

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
| 1 | 00:00:00,000 → 00:00:04,500 | Một chiếc bóng đèn chưa sáng, như một ý tưởng còn dang dở. |
| 2 | 00:00:04,500 → 00:00:09,000 | Một dấu chấm hỏi lớn hiện lên bên cạnh, đầy băn khoăn. |
| 3 | 00:00:09,000 → 00:00:13,500 | Bỗng dưng ý tưởng loé lên, chiếc bóng đèn bừng sáng rực rỡ. |
| 4 | 00:00:13,500 → 00:00:18,000 | Những tia sáng nhỏ lấp lánh bay quanh, như niềm vui vỡ oà. |

Dòng 1-2 → **cảnh 1** (`scene-01`), dòng 3-4 → **cảnh 2** (`scene-02`), mỗi
cảnh 9000ms.

## Nội dung thư mục

| File | Kích thước | Mô tả |
|---|---|---|
| `demo.srt` | — | Phụ đề 4 dòng ở trên. |
| `scene-01-y-tuong.png` | 1280×720 | Một bóng đèn (nét xám, chưa sáng) bên trái; **một dấu chấm hỏi lớn** (nét cong + chấm) bên phải — 2 chủ thể, bố cục tối giản. |
| `scene-02-y-tuong.png` | 1280×720 | Bóng đèn nay viền cam với đủ tia sáng ("bừng sáng"), chính giữa; **5 hình lấp lánh** (dấu sao nhỏ 4 cánh) rải quanh — 2 nhóm chủ thể. |

## Gợi ý chú thích (annotation)

Chỉ là gợi ý về **thứ tự/vai trò**; toạ độ `region` chính xác cần tự đo trên
ảnh thật.

**Cảnh 1** (`sceneId: scene-01`, gợi ý `sceneDurationMs: 9000`):

1. `bulb` — chủ thể chính (bóng đèn, bên trái). *Khớp phụ đề dòng 1.*
2. `question-mark` — phản ứng (dấu chấm hỏi, bên phải, vẽ sau). *Khớp phụ đề dòng 2.*

**Cảnh 2** (`sceneId: scene-02`) — ảnh nguồn khác cảnh 1 (bóng đèn đổi màu,
dấu hỏi biến mất, thêm tia lấp lánh):

1. `bulb` — chủ thể chính (bóng đèn, nay màu cam, chính giữa). *Khớp phụ đề dòng 3.*
2. `sparkles` — kết quả / hiệu ứng (các tia lấp lánh quanh bóng đèn, vẽ sau cùng — có thể gộp 1 vùng hoặc tách từng cái). *Khớp phụ đề dòng 4.*

## Các bước biến ví dụ này thành video hoàn chỉnh

1. **Phân tích phụ đề** (tuỳ chọn, SRT đã chia sẵn 2 cảnh):
   ```bash
   python scripts/parse_srt.py assets/whiteboard/sample-07-y-tuong/demo.srt \
     --target-sec 9 --min-sec 5 --max-sec 12
   ```
2. **Tạo `annotation.json`** theo gợi ý trên (gõ tay theo mẫu trong
   `SKILL.md`, hoặc dùng app Studio tab 2 → **Tạo annotation mẫu cho ảnh đang
   chọn**).
3. **Mở bảng Preview** (`assets/preview.html`, Chrome/Edge) → "Mở thư mục"
   → chọn `assets/whiteboard/sample-07-y-tuong/` → chỉnh vùng/thứ tự/thời
   gian → "Lưu".
4. **Xuất ảnh kiểm tra vùng**:
   ```bash
   python scripts/render_annotation_preview.py \
     assets/whiteboard/sample-07-y-tuong/scene-01-y-tuong.png \
     assets/whiteboard/sample-07-y-tuong/scene-01-y-tuong.annotation.json \
     assets/whiteboard/sample-07-y-tuong/scene-01-y-tuong.regions.png
   ```
5. **Render từng cảnh**:
   ```bash
   <ENV_PY> scripts/render_stream_whiteboard.py \
     assets/whiteboard/sample-07-y-tuong/scene-01-y-tuong.png \
     assets/whiteboard/sample-07-y-tuong/scene-01-y-tuong.annotation.json \
     assets/whiteboard/sample-07-y-tuong/scene-01-y-tuong-whiteboard.mp4 \
     assets/drawing-hand.png --ink-path grid --color-fill contour-wipe
   ```
   Lặp lại cho `scene-02-y-tuong`. `<ENV_PY>` lấy từ
   `python scripts/prepare_env.py --check`.
6. **Ghép 2 cảnh**:
   ```bash
   <ENV_PY> scripts/merge_scenes.py \
     --inputs assets/whiteboard/sample-07-y-tuong/scene-01-y-tuong-whiteboard.mp4 \
              assets/whiteboard/sample-07-y-tuong/scene-02-y-tuong-whiteboard.mp4 \
     --output assets/whiteboard/sample-07-y-tuong/sample-07-y-tuong-final.mp4
   ```
7. **(Tuỳ chọn, cần `ffmpeg`)** thêm giọng đọc + khắc phụ đề qua
   `scripts/postprocess_video.py` hoặc tab "⚡ Nhanh" của app Studio.

Quy trình đầy đủ (gồm các điểm dừng xác nhận bắt buộc) xem ở
[`SKILL.md`](../../../SKILL.md).
