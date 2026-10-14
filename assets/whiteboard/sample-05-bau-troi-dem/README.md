# Ví dụ: `sample-05-bau-troi-dem` (Bầu trời đêm)

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
| 1 | 00:00:00,000 → 00:00:04,500 | Khi hoàng hôn buông xuống, mặt trăng dần hiện ra. |
| 2 | 00:00:04,500 → 00:00:09,000 | Một chú cú nhỏ đậu trên cành cây khô. |
| 3 | 00:00:09,000 → 00:00:13,500 | Màn đêm buông xuống, muôn vàn vì sao lấp lánh trên bầu trời. |
| 4 | 00:00:13,500 → 00:00:18,000 | Một ngôi sao băng vụt qua, mang theo một điều ước. |

Dòng 1-2 → **cảnh 1** (`scene-01`), dòng 3-4 → **cảnh 2** (`scene-02`), mỗi
cảnh 9000ms.

## Nội dung thư mục

| File | Kích thước | Mô tả |
|---|---|---|
| `demo.srt` | — | Phụ đề 4 dòng ở trên. |
| `scene-01-bau-troi-dem.png` | 1280×720 | Dãy núi zig-zag; vầng trăng khuyết (nét cong hở) góc trên phải; **một cành cây khô** và **một chú cú** (2 mắt tròn + tai nhọn) đậu trên cành, bên trái — 4 nhóm chủ thể. |
| `scene-02-bau-troi-dem.png` | 1280×720 | Cùng dãy núi; trăng khuyết nay tô xanh dương; **14 ngôi sao** rải khắp bầu trời (hình sao 5 cánh); **một ngôi sao băng** (vệt chấm + đuôi) ở góc trên trái, tách riêng khỏi cụm sao — 4 nhóm chủ thể. |

## Gợi ý chú thích (annotation)

Chỉ là gợi ý về **thứ tự/vai trò**; toạ độ `region` chính xác cần tự đo trên
ảnh thật.

**Cảnh 1** (`sceneId: scene-01`, gợi ý `sceneDurationMs: 9000`):

1. `mountain` — bối cảnh (dãy núi, trải ngang nửa dưới khung hình).
2. `moon` — chủ thể chính (trăng khuyết, góc trên phải). *Khớp phụ đề dòng 1.*
3. `branch` — bối cảnh phụ (cành cây khô, bên trái).
4. `owl` — điểm nhấn (chú cú đậu trên cành, vẽ sau cùng). *Khớp phụ đề dòng 2.*

**Cảnh 2** (`sceneId: scene-02`) — ảnh nguồn khác cảnh 1 (trăng đổi màu, thêm
sao), chú thích độc lập:

1. `mountain` — bối cảnh (giữ vị trí như cảnh 1).
2. `moon` — chủ thể chính (trăng, nay màu xanh dương đậm hơn).
3. `stars` — kết quả / bối cảnh bầu trời (toàn bộ các ngôi sao rải rác — có
   thể gộp 1 vùng lớn bao trùm bầu trời). *Khớp phụ đề dòng 3.*
4. `shooting-star` — điểm nhấn kết (sao băng góc trên trái, vẽ sau cùng). *Khớp phụ đề dòng 4.*

## Các bước biến ví dụ này thành video hoàn chỉnh

1. **Phân tích phụ đề** (tuỳ chọn, SRT đã chia sẵn 2 cảnh):
   ```bash
   python scripts/parse_srt.py assets/whiteboard/sample-05-bau-troi-dem/demo.srt \
     --target-sec 9 --min-sec 5 --max-sec 12
   ```
2. **Tạo `annotation.json`** theo gợi ý trên (gõ tay theo mẫu trong
   `SKILL.md`, hoặc dùng app Studio tab 2 → **Tạo annotation mẫu cho ảnh đang
   chọn**).
3. **Mở bảng Preview** (`assets/preview.html`, Chrome/Edge) → "Mở thư mục"
   → chọn `assets/whiteboard/sample-05-bau-troi-dem/` → chỉnh vùng/thứ tự/
   thời gian → "Lưu".
4. **Xuất ảnh kiểm tra vùng**:
   ```bash
   python scripts/render_annotation_preview.py \
     assets/whiteboard/sample-05-bau-troi-dem/scene-01-bau-troi-dem.png \
     assets/whiteboard/sample-05-bau-troi-dem/scene-01-bau-troi-dem.annotation.json \
     assets/whiteboard/sample-05-bau-troi-dem/scene-01-bau-troi-dem.regions.png
   ```
5. **Render từng cảnh**:
   ```bash
   <ENV_PY> scripts/render_stream_whiteboard.py \
     assets/whiteboard/sample-05-bau-troi-dem/scene-01-bau-troi-dem.png \
     assets/whiteboard/sample-05-bau-troi-dem/scene-01-bau-troi-dem.annotation.json \
     assets/whiteboard/sample-05-bau-troi-dem/scene-01-bau-troi-dem-whiteboard.mp4 \
     assets/drawing-hand.png --ink-path grid --color-fill contour-wipe
   ```
   Lặp lại cho `scene-02-bau-troi-dem`. `<ENV_PY>` lấy từ
   `python scripts/prepare_env.py --check`.
6. **Ghép 2 cảnh**:
   ```bash
   <ENV_PY> scripts/merge_scenes.py \
     --inputs assets/whiteboard/sample-05-bau-troi-dem/scene-01-bau-troi-dem-whiteboard.mp4 \
              assets/whiteboard/sample-05-bau-troi-dem/scene-02-bau-troi-dem-whiteboard.mp4 \
     --output assets/whiteboard/sample-05-bau-troi-dem/sample-05-bau-troi-dem-final.mp4
   ```
7. **(Tuỳ chọn, cần `ffmpeg`)** thêm giọng đọc + khắc phụ đề qua
   `scripts/postprocess_video.py` hoặc tab "⚡ Nhanh" của app Studio.

Quy trình đầy đủ (gồm các điểm dừng xác nhận bắt buộc) xem ở
[`SKILL.md`](../../../SKILL.md).
