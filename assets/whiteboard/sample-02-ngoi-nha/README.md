# Ví dụ: `sample-02-ngoi-nha` (Ngôi nhà bên gốc cây)

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
| 1 | 00:00:00,000 → 00:00:04,500 | Bên gốc cây xanh có một khoảng đất trống yên bình. |
| 2 | 00:00:04,500 → 00:00:09,000 | Một chú chó nhỏ chạy ngang qua bãi cỏ. |
| 3 | 00:00:09,000 → 00:00:13,500 | Một ngôi nhà nhỏ xinh được dựng lên cạnh gốc cây. |
| 4 | 00:00:13,500 → 00:00:18,000 | Khói bay lên từ ống khói, có người đang trên đường về nhà. |

Dòng 1-2 → **cảnh 1** (`scene-01`), dòng 3-4 → **cảnh 2** (`scene-02`), mỗi
cảnh 9000ms.

## Nội dung thư mục

| File | Kích thước | Mô tả |
|---|---|---|
| `demo.srt` | — | Phụ đề 4 dòng ở trên. |
| `scene-01-ngoi-nha.png` | 1280×720 | Một cây (tán tròn + thân) đứng bên trái; **một chú chó nhỏ** (thân oval + đầu tròn + 4 chân) đang chạy ở giữa khung — 2 nhóm chủ thể, còn khoảng đất trống bên phải. |
| `scene-02-ngoi-nha.png` | 1280×720 | Cây giữ nguyên bên trái; bên phải là **ngôi nhà** (mái, tường, 2 cửa sổ, cửa chính — màu xanh), có **khói bay lên từ ống khói**, và **một người (hình que)** đang đi tới gần nhà — 4 nhóm chủ thể. |

## Gợi ý chú thích (annotation)

Chỉ là gợi ý về **thứ tự/vai trò**; toạ độ `region` chính xác cần tự đo trên
ảnh thật.

**Cảnh 1** (`sceneId: scene-01`, gợi ý `sceneDurationMs: 9000`):

1. `tree` — bối cảnh (cây bên trái khung hình). *Khớp phụ đề dòng 1.*
2. `dog` — chủ thể chính (chú chó, chạy ngang giữa khung). *Khớp phụ đề dòng 2.*

**Cảnh 2** (`sceneId: scene-02`):

1. `tree` — bối cảnh kế thừa (cây, giữ nguyên vị trí như cảnh 1).
2. `house` — chủ thể chính (ngôi nhà, mái + tường + cửa sổ + cửa chính). *Khớp phụ đề dòng 3.*
3. `smoke` — chi tiết (khói bay lên từ ống khói, vẽ sau nhà). *Khớp phụ đề dòng 4.*
4. `person` — phản ứng / kết (người đi về nhà, bên phải, vẽ sau cùng). *Khớp phụ đề dòng 4.*

## Các bước biến ví dụ này thành video hoàn chỉnh

1. **Phân tích phụ đề** (tuỳ chọn, SRT đã chia sẵn 2 cảnh):
   ```bash
   python scripts/parse_srt.py assets/whiteboard/sample-02-ngoi-nha/demo.srt \
     --target-sec 9 --min-sec 5 --max-sec 12
   ```
2. **Tạo `annotation.json`** theo gợi ý trên (gõ tay theo mẫu trong
   `SKILL.md`, hoặc dùng app Studio tab 2 → **Tạo annotation mẫu cho ảnh đang
   chọn** làm điểm khởi đầu).
3. **Mở bảng Preview** (`assets/preview.html`, Chrome/Edge) → "Mở thư mục"
   → chọn `assets/whiteboard/sample-02-ngoi-nha/` → chỉnh vùng, thứ tự, thời
   gian bằng kéo-thả → "Lưu".
4. **Xuất ảnh kiểm tra vùng**:
   ```bash
   python scripts/render_annotation_preview.py \
     assets/whiteboard/sample-02-ngoi-nha/scene-01-ngoi-nha.png \
     assets/whiteboard/sample-02-ngoi-nha/scene-01-ngoi-nha.annotation.json \
     assets/whiteboard/sample-02-ngoi-nha/scene-01-ngoi-nha.regions.png
   ```
5. **Render từng cảnh**:
   ```bash
   <ENV_PY> scripts/render_stream_whiteboard.py \
     assets/whiteboard/sample-02-ngoi-nha/scene-01-ngoi-nha.png \
     assets/whiteboard/sample-02-ngoi-nha/scene-01-ngoi-nha.annotation.json \
     assets/whiteboard/sample-02-ngoi-nha/scene-01-ngoi-nha-whiteboard.mp4 \
     assets/drawing-hand.png --ink-path grid --color-fill contour-wipe
   ```
   Lặp lại cho `scene-02-ngoi-nha`. `<ENV_PY>` lấy từ
   `python scripts/prepare_env.py --check`.
6. **Ghép 2 cảnh**:
   ```bash
   <ENV_PY> scripts/merge_scenes.py \
     --inputs assets/whiteboard/sample-02-ngoi-nha/scene-01-ngoi-nha-whiteboard.mp4 \
              assets/whiteboard/sample-02-ngoi-nha/scene-02-ngoi-nha-whiteboard.mp4 \
     --output assets/whiteboard/sample-02-ngoi-nha/sample-02-ngoi-nha-final.mp4
   ```
7. **(Tuỳ chọn, cần `ffmpeg`)** thêm giọng đọc + khắc phụ đề qua
   `scripts/postprocess_video.py` hoặc tab "⚡ Nhanh" của app Studio.

Quy trình đầy đủ (gồm các điểm dừng xác nhận bắt buộc) xem ở
[`SKILL.md`](../../../SKILL.md).
