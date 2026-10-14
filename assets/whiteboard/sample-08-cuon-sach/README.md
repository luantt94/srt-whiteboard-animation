# Ví dụ: `sample-08-cuon-sach` (Cuốn sách mở ra)

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
| 1 | 00:00:00,000 → 00:00:04,500 | Một cuốn sách đang khép lại, chứa đựng bao điều bí ẩn. |
| 2 | 00:00:04,500 → 00:00:09,000 | Bụi nhẹ bay lên khi cuốn sách được nhấc lên khỏi kệ. |
| 3 | 00:00:09,000 → 00:00:13,500 | Sách được mở ra, từng trang chữ dần hiện lên trước mắt. |
| 4 | 00:00:13,500 → 00:00:18,000 | Một chiếc kính lúp xuất hiện, soi rõ từng con chữ. |

Dòng 1-2 → **cảnh 1** (`scene-01`), dòng 3-4 → **cảnh 2** (`scene-02`), mỗi
cảnh 9000ms.

## Nội dung thư mục

| File | Kích thước | Mô tả |
|---|---|---|
| `demo.srt` | — | Phụ đề 4 dòng ở trên. |
| `scene-01-cuon-sach.png` | 1280×720 | Một cuốn sách khép (hình chữ nhật bo góc, chia đôi bởi gáy sách) ở giữa khung; **vài hạt bụi** (chấm nhỏ) bay phía trên; **một đường kệ sách** bên dưới — 3 nhóm chủ thể. |
| `scene-02-cuon-sach.png` | 1280×720 | Cuốn sách mở rộng thành hình "nơ bướm" (2 trang kẻ dòng chữ mô phỏng); **một chiếc kính lúp** (vòng tròn + tay cầm) bên phải — 3 nhóm chủ thể. |

## Gợi ý chú thích (annotation)

Chỉ là gợi ý về **thứ tự/vai trò**; toạ độ `region` chính xác cần tự đo trên
ảnh thật.

**Cảnh 1** (`sceneId: scene-01`, gợi ý `sceneDurationMs: 9000`):

1. `book-closed` — chủ thể chính (cuốn sách khép, chính giữa khung hình). *Khớp phụ đề dòng 1.*
2. `dust` — chi tiết (hạt bụi bay phía trên, vẽ sau). *Khớp phụ đề dòng 2.*

**Cảnh 2** (`sceneId: scene-02`) — ảnh nguồn khác cảnh 1 (sách đã mở rộng),
chú thích độc lập, gợi ý tách theo **trái → phải** để mô phỏng hiệu ứng lật mở
dần:

1. `page-left` — trang bên trái (nửa trái cuốn sách mở, gồm các dòng kẻ chữ). *Khớp phụ đề dòng 3.*
2. `page-right` — trang bên phải (nửa phải, vẽ sau để tạo cảm giác "mở ra" tiếp nối từ trang trái). *Khớp phụ đề dòng 3.*
3. `magnifier` — điểm nhấn kết (kính lúp bên phải, vẽ sau cùng). *Khớp phụ đề dòng 4.*

## Các bước biến ví dụ này thành video hoàn chỉnh

1. **Phân tích phụ đề** (tuỳ chọn, SRT đã chia sẵn 2 cảnh):
   ```bash
   python scripts/parse_srt.py assets/whiteboard/sample-08-cuon-sach/demo.srt \
     --target-sec 9 --min-sec 5 --max-sec 12
   ```
2. **Tạo `annotation.json`** theo gợi ý trên (gõ tay theo mẫu trong
   `SKILL.md`, hoặc dùng app Studio tab 2 → **Tạo annotation mẫu cho ảnh đang
   chọn**).
3. **Mở bảng Preview** (`assets/preview.html`, Chrome/Edge) → "Mở thư mục"
   → chọn `assets/whiteboard/sample-08-cuon-sach/` → chỉnh vùng/thứ tự/thời
   gian → "Lưu".
4. **Xuất ảnh kiểm tra vùng**:
   ```bash
   python scripts/render_annotation_preview.py \
     assets/whiteboard/sample-08-cuon-sach/scene-01-cuon-sach.png \
     assets/whiteboard/sample-08-cuon-sach/scene-01-cuon-sach.annotation.json \
     assets/whiteboard/sample-08-cuon-sach/scene-01-cuon-sach.regions.png
   ```
5. **Render từng cảnh**:
   ```bash
   <ENV_PY> scripts/render_stream_whiteboard.py \
     assets/whiteboard/sample-08-cuon-sach/scene-01-cuon-sach.png \
     assets/whiteboard/sample-08-cuon-sach/scene-01-cuon-sach.annotation.json \
     assets/whiteboard/sample-08-cuon-sach/scene-01-cuon-sach-whiteboard.mp4 \
     assets/drawing-hand.png --ink-path grid --color-fill contour-wipe
   ```
   Lặp lại cho `scene-02-cuon-sach`. `<ENV_PY>` lấy từ
   `python scripts/prepare_env.py --check`.
6. **Ghép 2 cảnh**:
   ```bash
   <ENV_PY> scripts/merge_scenes.py \
     --inputs assets/whiteboard/sample-08-cuon-sach/scene-01-cuon-sach-whiteboard.mp4 \
              assets/whiteboard/sample-08-cuon-sach/scene-02-cuon-sach-whiteboard.mp4 \
     --output assets/whiteboard/sample-08-cuon-sach/sample-08-cuon-sach-final.mp4
   ```
7. **(Tuỳ chọn, cần `ffmpeg`)** thêm giọng đọc + khắc phụ đề qua
   `scripts/postprocess_video.py` hoặc tab "⚡ Nhanh" của app Studio.

Quy trình đầy đủ (gồm các điểm dừng xác nhận bắt buộc) xem ở
[`SKILL.md`](../../../SKILL.md).
