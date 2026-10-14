# Ví dụ: `sample-01-mat-troi` (Mặt trời mọc)

> **Đây là nguyên liệu thô**, chưa qua chú thích: chỉ có phụ đề + 2 ảnh
> line-art, **chưa có** `annotation.json` hay video render sẵn. Dùng thư mục
> này để tự luyện tập từ **bước 3 trở đi** của quy trình trong `SKILL.md`
> (chú thích vùng → preview → render → ghép). Nếu muốn xem một ví dụ đã làm
> **xong toàn bộ** quy trình, xem
> [`assets/whiteboard/demo-phong-canh/`](../demo-phong-canh/README.md).
>
> Ảnh tạo bằng `python examples/make_sample_gallery.py` — chạy lại script đó
> bất kỳ lúc nào để phục hồi về đúng trạng thái gốc.

## Câu chuyện (4 dòng phụ đề → 2 cảnh)

| # | Thời gian | Phụ đề |
|---|---|---|
| 1 | 00:00:00,000 → 00:00:04,500 | Buổi sáng sớm, mặt trời bắt đầu nhô lên sau dãy núi. |
| 2 | 00:00:04,500 → 00:00:09,000 | Vài chú chim bay về phía ánh nắng ấm áp. |
| 3 | 00:00:09,000 → 00:00:13,500 | Nắng lên cao, cả bầu trời bừng sáng rực rỡ. |
| 4 | 00:00:13,500 → 00:00:18,000 | Những đám mây trắng trôi nhẹ ngang qua đỉnh núi. |

Dòng 1-2 ứng với **cảnh 1** (`scene-01`, 0-9000ms), dòng 3-4 ứng với **cảnh 2**
(`scene-02`, 9000-18000ms) — đúng quy ước "2 dòng phụ đề gộp thành 1 cảnh"
như `demo-phong-canh`.

## Nội dung thư mục

| File | Kích thước | Mô tả |
|---|---|---|
| `demo.srt` | — | Phụ đề 4 dòng ở trên. |
| `scene-01-mat-troi.png` | 1280×720 | Dãy núi zig-zag; mặt trời (cam) vừa ló lên đúng khe núi giữa; **2 cánh chim** bay ở hai bên phía trên — 3 nhóm chủ thể. |
| `scene-02-mat-troi.png` | 1280×720 | Cùng dãy núi, mặt trời đã lên hẳn phía trên với đủ tia sáng; thêm **2 cụm mây** (viền xanh) hai bên và **một cái cây** góc dưới phải — 4 nhóm chủ thể. |

## Gợi ý chú thích (annotation)

Chỉ là gợi ý về **thứ tự/vai trò**; toạ độ `region` chính xác cần tự đo trên
ảnh thật (xem nguyên tắc trong `SKILL.md`: phải xem ảnh gốc, không đoán).

**Cảnh 1** (`sceneId: scene-01`, gợi ý `sceneDurationMs: 9000`):

1. `mountain` — bối cảnh (dãy núi, trải ngang gần hết chiều rộng, nửa dưới khung hình). *Khớp phụ đề dòng 1.*
2. `sun` — chủ thể chính (mặt trời đang ló, chính giữa, ngay trên khe núi). *Khớp phụ đề dòng 1.*
3. `birds` — phản ứng / điểm nhấn (2 cánh chim bay ở nửa trên ảnh, có thể gộp 1 vùng hoặc tách `bird-left`/`bird-right`). *Khớp phụ đề dòng 2.*

**Cảnh 2** (`sceneId: scene-02`):

1. `mountain` — bối cảnh (giữ nguyên vị trí như cảnh 1).
2. `sun` — chủ thể chính (mặt trời đã lên cao, đủ tia sáng). *Khớp phụ đề dòng 3.*
3. `clouds` — bối cảnh bổ sung (2 cụm mây hai bên, có thể tách trái/phải). *Khớp phụ đề dòng 4.*
4. `tree` — điểm nhấn kết (cây góc dưới phải, vẽ sau cùng).

## Các bước biến ví dụ này thành video hoàn chỉnh

1. **Phân tích phụ đề** (tuỳ chọn, SRT đã chia sẵn 2 cảnh):
   ```bash
   python scripts/parse_srt.py assets/whiteboard/sample-01-mat-troi/demo.srt \
     --target-sec 9 --min-sec 5 --max-sec 12
   ```
2. **Tạo `annotation.json`** cho từng ảnh theo gợi ý ở trên — có thể gõ tay
   theo mẫu trong `SKILL.md` (mục "Ví dụ cấu hình"), hoặc mở app Studio
   (`python app/launch.py`) → tab 2 → **Tạo annotation mẫu cho ảnh đang
   chọn** để có điểm khởi đầu rồi chỉnh lại vùng.
3. **Mở bảng Preview** để chỉnh vùng/thứ tự/thời gian bằng kéo-thả:
   mở `assets/preview.html` bằng Chrome/Edge → "Mở thư mục" →
   chọn thư mục `assets/whiteboard/sample-01-mat-troi/` → kéo khung, đổi thứ
   tự, sửa thời gian → bấm "Lưu" để ghi đè `.annotation.json`.
4. **Xuất ảnh kiểm tra vùng**:
   ```bash
   python scripts/render_annotation_preview.py \
     assets/whiteboard/sample-01-mat-troi/scene-01-mat-troi.png \
     assets/whiteboard/sample-01-mat-troi/scene-01-mat-troi.annotation.json \
     assets/whiteboard/sample-01-mat-troi/scene-01-mat-troi.regions.png
   ```
5. **Render từng cảnh** (cần interpreter trong `.venv`, lấy từ
   `python scripts/prepare_env.py --check`):
   ```bash
   <ENV_PY> scripts/render_stream_whiteboard.py \
     assets/whiteboard/sample-01-mat-troi/scene-01-mat-troi.png \
     assets/whiteboard/sample-01-mat-troi/scene-01-mat-troi.annotation.json \
     assets/whiteboard/sample-01-mat-troi/scene-01-mat-troi-whiteboard.mp4 \
     assets/drawing-hand.png --ink-path grid --color-fill contour-wipe
   ```
   Lặp lại cho `scene-02-mat-troi`.
6. **Ghép 2 cảnh**:
   ```bash
   <ENV_PY> scripts/merge_scenes.py \
     --inputs assets/whiteboard/sample-01-mat-troi/scene-01-mat-troi-whiteboard.mp4 \
              assets/whiteboard/sample-01-mat-troi/scene-02-mat-troi-whiteboard.mp4 \
     --output assets/whiteboard/sample-01-mat-troi/sample-01-mat-troi-final.mp4
   ```
7. **(Tuỳ chọn, cần `ffmpeg`)** thêm giọng đọc TTS + khắc phụ đề bằng
   `scripts/postprocess_video.py`, hoặc đơn giản hơn là dùng tab "⚡ Nhanh"
   của app Studio (chọn 2 ảnh + file `demo.srt` này, bật TTS).

Toàn bộ quy trình đầy đủ (bao gồm chốt xác nhận từng bước) được mô tả trong
[`SKILL.md`](../../../SKILL.md).
