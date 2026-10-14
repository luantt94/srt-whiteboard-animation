# Ví dụ: `sample-09-xe-dap` (Xe đạp lăn bánh)

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
| 1 | 00:00:00,000 → 00:00:04,500 | Chiếc xe đạp đang đứng yên, chờ đợi một chuyến đi. |
| 2 | 00:00:04,500 → 00:00:09,000 | Một giỏ hoa nhỏ được treo phía trước ghi đông. |
| 3 | 00:00:09,000 → 00:00:13,500 | Xe đạp lăn bánh băng băng, gió thổi tung bay phía sau. |
| 4 | 00:00:13,500 → 00:00:18,000 | Hai bên đường, hàng cây lướt qua vun vút. |

Dòng 1-2 → **cảnh 1** (`scene-01`), dòng 3-4 → **cảnh 2** (`scene-02`), mỗi
cảnh 9000ms.

## Nội dung thư mục

| File | Kích thước | Mô tả |
|---|---|---|
| `demo.srt` | — | Phụ đề 4 dòng ở trên. |
| `scene-01-xe-dap.png` | 1280×720 | Xe đạp (2 bánh + khung + ghi đông) đứng giữa khung; **một giỏ hoa nhỏ** (hình thang + cụm hoa đỏ/cam) treo trên ghi đông — 2 nhóm chủ thể. |
| `scene-02-xe-dap.png` | 1280×720 | Xe đạp (giữ nguyên, có thêm **người lái** đơn giản) đang chạy; **vài vạch gió** (nét xanh) phía sau; **2 cây** hai bên đường mô phỏng "lướt qua vun vút" — 4 nhóm chủ thể. |

## Gợi ý chú thích (annotation)

Chỉ là gợi ý về **thứ tự/vai trò**; toạ độ `region` chính xác cần tự đo trên
ảnh thật.

**Cảnh 1** (`sceneId: scene-01`, gợi ý `sceneDurationMs: 9000`):

1. `bicycle` — chủ thể chính (xe đạp, chính giữa khung hình). *Khớp phụ đề dòng 1.*
2. `basket-flower` — chi tiết (giỏ hoa trên ghi đông, vẽ sau). *Khớp phụ đề dòng 2.*

**Cảnh 2** (`sceneId: scene-02`) — ảnh nguồn khác cảnh 1 (thêm người lái, cây
hai bên, vệt gió), chú thích độc lập:

1. `roadside-trees` — bối cảnh (2 cây hai bên đường). *Khớp phụ đề dòng 4.*
2. `bicycle-rider` — chủ thể chính (xe đạp + người lái, chính giữa). *Khớp phụ đề dòng 3.*
3. `wind` — kết quả / hiệu ứng (vạch gió phía sau, vẽ sau cùng). *Khớp phụ đề dòng 3.*

## Các bước biến ví dụ này thành video hoàn chỉnh

1. **Phân tích phụ đề** (tuỳ chọn, SRT đã chia sẵn 2 cảnh):
   ```bash
   python scripts/parse_srt.py assets/whiteboard/sample-09-xe-dap/demo.srt \
     --target-sec 9 --min-sec 5 --max-sec 12
   ```
2. **Tạo `annotation.json`** theo gợi ý trên (gõ tay theo mẫu trong
   `SKILL.md`, hoặc dùng app Studio tab 2 → **Tạo annotation mẫu cho ảnh đang
   chọn**).
3. **Mở bảng Preview** (`assets/preview.html`, Chrome/Edge) → "Mở thư mục"
   → chọn `assets/whiteboard/sample-09-xe-dap/` → chỉnh vùng/thứ tự/thời
   gian → "Lưu".
4. **Xuất ảnh kiểm tra vùng**:
   ```bash
   python scripts/render_annotation_preview.py \
     assets/whiteboard/sample-09-xe-dap/scene-01-xe-dap.png \
     assets/whiteboard/sample-09-xe-dap/scene-01-xe-dap.annotation.json \
     assets/whiteboard/sample-09-xe-dap/scene-01-xe-dap.regions.png
   ```
5. **Render từng cảnh**:
   ```bash
   <ENV_PY> scripts/render_stream_whiteboard.py \
     assets/whiteboard/sample-09-xe-dap/scene-01-xe-dap.png \
     assets/whiteboard/sample-09-xe-dap/scene-01-xe-dap.annotation.json \
     assets/whiteboard/sample-09-xe-dap/scene-01-xe-dap-whiteboard.mp4 \
     assets/drawing-hand.png --ink-path grid --color-fill contour-wipe
   ```
   Lặp lại cho `scene-02-xe-dap`. `<ENV_PY>` lấy từ
   `python scripts/prepare_env.py --check`.
6. **Ghép 2 cảnh**:
   ```bash
   <ENV_PY> scripts/merge_scenes.py \
     --inputs assets/whiteboard/sample-09-xe-dap/scene-01-xe-dap-whiteboard.mp4 \
              assets/whiteboard/sample-09-xe-dap/scene-02-xe-dap-whiteboard.mp4 \
     --output assets/whiteboard/sample-09-xe-dap/sample-09-xe-dap-final.mp4
   ```
7. **(Tuỳ chọn, cần `ffmpeg`)** thêm giọng đọc + khắc phụ đề qua
   `scripts/postprocess_video.py` hoặc tab "⚡ Nhanh" của app Studio.

Quy trình đầy đủ (gồm các điểm dừng xác nhận bắt buộc) xem ở
[`SKILL.md`](../../../SKILL.md).
