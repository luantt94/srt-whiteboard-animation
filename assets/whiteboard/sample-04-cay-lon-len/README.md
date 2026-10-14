# Ví dụ: `sample-04-cay-lon-len` (Hạt giống lớn thành cây)

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
| 1 | 00:00:00,000 → 00:00:04,500 | Một hạt giống nhỏ bé được gieo xuống đất. |
| 2 | 00:00:04,500 → 00:00:09,000 | Giọt mưa và ánh nắng giúp hạt giống nảy mầm. |
| 3 | 00:00:09,000 → 00:00:13,500 | Theo thời gian, hạt giống lớn lên thành cây to với trái chín đỏ. |
| 4 | 00:00:13,500 → 00:00:18,000 | Một chú chim nhỏ đậu trên cành hót vang. |

Dòng 1-2 → **cảnh 1** (`scene-01`), dòng 3-4 → **cảnh 2** (`scene-02`), mỗi
cảnh 9000ms.

## Nội dung thư mục

| File | Kích thước | Mô tả |
|---|---|---|
| `demo.srt` | — | Phụ đề 4 dòng ở trên. |
| `scene-01-cay-lon.png` | 1280×720 | Một ụ đất nhỏ ở giữa-dưới khung, hạt giống (chấm cam) ngay phía trên; **mặt trời** góc trên phải; **3 giọt mưa** rơi giữa khung — bố cục tối giản, nhiều khoảng trống chủ ý (đúng tinh thần "hạt giống nhỏ bé"), 5 nhóm chủ thể. |
| `scene-02-cay-lon.png` | 1280×720 | Một cây trưởng thành ở giữa khung: tán lá lớn điểm 6 chấm đỏ (quả chín), thân cây thẳng; **một cành cây** và **một chú chim** bên phải — 4 nhóm chủ thể. |

## Gợi ý chú thích (annotation)

Chỉ là gợi ý về **thứ tự/vai trò**; toạ độ `region` chính xác cần tự đo trên
ảnh thật.

**Cảnh 1** (`sceneId: scene-01`, gợi ý `sceneDurationMs: 9000`):

1. `soil-seed` — chủ thể chính (ụ đất + hạt giống, giữa-dưới khung). *Khớp phụ đề dòng 1.*
2. `sun` — bối cảnh (mặt trời góc trên phải). *Khớp phụ đề dòng 2.*
3. `rain` — chi tiết (3 giọt mưa, vẽ sau cùng). *Khớp phụ đề dòng 2.*

**Cảnh 2** (`sceneId: scene-02`) — ảnh nguồn khác hoàn toàn cảnh 1 (đã là cây
trưởng thành), chú thích độc lập:

1. `trunk-crown` — chủ thể chính (thân + tán lá cây, chiếm phần lớn khung
   hình, chính giữa). *Khớp phụ đề dòng 3.*
2. `fruits` — kết quả (các chấm đỏ là trái chín, rải trên tán lá — vẽ sau để
   mô phỏng "trái chín" xuất hiện khi cây đã lớn). *Khớp phụ đề dòng 3.*
3. `bird` — điểm nhấn kết (chim đậu trên cành, bên phải, vẽ sau cùng). *Khớp phụ đề dòng 4.*

## Các bước biến ví dụ này thành video hoàn chỉnh

1. **Phân tích phụ đề** (tuỳ chọn, SRT đã chia sẵn 2 cảnh):
   ```bash
   python scripts/parse_srt.py assets/whiteboard/sample-04-cay-lon-len/demo.srt \
     --target-sec 9 --min-sec 5 --max-sec 12
   ```
2. **Tạo `annotation.json`** theo gợi ý trên (gõ tay theo mẫu trong
   `SKILL.md`, hoặc dùng app Studio tab 2 → **Tạo annotation mẫu cho ảnh đang
   chọn**).
3. **Mở bảng Preview** (`assets/preview.html`, Chrome/Edge) → "Mở thư mục"
   → chọn `assets/whiteboard/sample-04-cay-lon-len/` → chỉnh vùng/thứ tự/thời
   gian → "Lưu".
4. **Xuất ảnh kiểm tra vùng**:
   ```bash
   python scripts/render_annotation_preview.py \
     assets/whiteboard/sample-04-cay-lon-len/scene-01-cay-lon.png \
     assets/whiteboard/sample-04-cay-lon-len/scene-01-cay-lon.annotation.json \
     assets/whiteboard/sample-04-cay-lon-len/scene-01-cay-lon.regions.png
   ```
5. **Render từng cảnh**:
   ```bash
   <ENV_PY> scripts/render_stream_whiteboard.py \
     assets/whiteboard/sample-04-cay-lon-len/scene-01-cay-lon.png \
     assets/whiteboard/sample-04-cay-lon-len/scene-01-cay-lon.annotation.json \
     assets/whiteboard/sample-04-cay-lon-len/scene-01-cay-lon-whiteboard.mp4 \
     assets/drawing-hand.png --ink-path grid --color-fill contour-wipe
   ```
   Lặp lại cho `scene-02-cay-lon`. `<ENV_PY>` lấy từ
   `python scripts/prepare_env.py --check`.
6. **Ghép 2 cảnh**:
   ```bash
   <ENV_PY> scripts/merge_scenes.py \
     --inputs assets/whiteboard/sample-04-cay-lon-len/scene-01-cay-lon-whiteboard.mp4 \
              assets/whiteboard/sample-04-cay-lon-len/scene-02-cay-lon-whiteboard.mp4 \
     --output assets/whiteboard/sample-04-cay-lon-len/sample-04-cay-lon-len-final.mp4
   ```
7. **(Tuỳ chọn, cần `ffmpeg`)** thêm giọng đọc + khắc phụ đề qua
   `scripts/postprocess_video.py` hoặc tab "⚡ Nhanh" của app Studio.

Quy trình đầy đủ (gồm các điểm dừng xác nhận bắt buộc) xem ở
[`SKILL.md`](../../../SKILL.md).
