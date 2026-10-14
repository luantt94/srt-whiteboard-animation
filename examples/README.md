# Ví dụ: `examples/`

Thư mục này gồm **ba thứ khác nhau**, đừng nhầm lẫn:

1. **`make_demo_project.py`** — script Python tự vẽ ra một dự án mẫu 2 cảnh
   (không cần ảnh AI, không cần mạng) và ghi vào
   `assets/whiteboard/demo-phong-canh/`. Xem chi tiết dự án đó ở
   [`assets/whiteboard/demo-phong-canh/README.md`](../assets/whiteboard/demo-phong-canh/README.md).
2. **`make_sample_gallery.py`** — script Python vẽ lại cả 10 thư mục
   `assets/whiteboard/sample-01..10` (nguyên liệu thô để luyện chú thích):
   mỗi chủ đề 2 ảnh nhiều đối tượng hơn (3-5 nhóm chủ thể/cảnh) + `demo.srt`
   4 dòng phụ đề. Xem mục lục ở
   [`assets/whiteboard/README.md`](../assets/whiteboard/README.md).
3. **Bộ ảnh "khỉ núi tranh chuối"** (`scene-01-monkey-mountain*`) — ví dụ
   trình diễn (showcase) được dùng làm ảnh demo trong [`README.md`](../README.md)
   ở gốc repo, minh hoạ kết quả cuối cùng mà Skill tạo ra trông như thế nào.

## 1. `make_demo_project.py` — trình tạo dự án mẫu

```bash
python examples/make_demo_project.py
```

Script dùng `PySide6.QtGui.QPainter` để tự vẽ 2 ảnh line-art (mặt trời/núi/cây
và mây/nhà/chim) lên nền giấy kem `#F5EBD7`, rồi ghi ra:

- `assets/whiteboard/demo-phong-canh/demo.srt`
- `assets/whiteboard/demo-phong-canh/scenes.json`
- `assets/whiteboard/demo-phong-canh/scene-01-binh-minh.png` +
  `.annotation.json`
- `assets/whiteboard/demo-phong-canh/scene-02-ngoi-nha.png` +
  `.annotation.json`

Chạy lại script **bất kỳ lúc nào** sẽ ghi đè các file trên về đúng trạng thái
ban đầu (hữu ích nếu bạn lỡ sửa hỏng dự án mẫu khi thực hành). Script **không**
đụng tới các file video (`*-whiteboard.mp4`, `*-final.mp4`, `*-final-av.mp4`)
đã có sẵn trong thư mục đó — muốn tái tạo video phải tự render lại bằng các
script trong `scripts/` hoặc bằng app Studio.

Cần `PySide6` đã cài (app `python app/launch.py` tự cài vào `.venv` trong lần
chạy đầu; hoặc `pip install PySide6` thủ công nếu chỉ muốn chạy riêng script
này).

## 2. `make_sample_gallery.py` — trình tạo 10 thư mục nguyên liệu thô

```bash
python examples/make_sample_gallery.py
```

Vẽ lại (bằng `QPainter`, không cần mạng) cả 10 thư mục
`assets/whiteboard/sample-01-mat-troi` … `sample-10-trai-tim`: mỗi chủ đề 2
ảnh line-art 1280×720 (3-5 nhóm chủ thể/cảnh, ví dụ mặt trời+núi+chim+mây+cây)
và 1 file `demo.srt` 4 dòng phụ đề (ghép thành 2 cảnh 9 giây). Các thư mục
này **không có** `annotation.json` hay video — dùng để luyện chú thích, xem
mục lục đầy đủ + bảng gợi ý chú thích từng chủ đề ở
[`assets/whiteboard/README.md`](../assets/whiteboard/README.md).

Chạy lại script **bất kỳ lúc nào** sẽ ghi đè cả 20 ảnh + 10 file `demo.srt` về
đúng trạng thái gốc (hữu ích nếu bạn lỡ sửa hỏng khi thực hành chú thích).
Cũng cần `PySide6` như script ở mục 1.

## 3. Bộ ảnh "khỉ núi tranh chuối" — ví dụ trình diễn

| File | Mô tả |
|---|---|
| `scene-01-monkey-mountain.png` | Ảnh minh hoạ màu hoàn chỉnh (1672×941) — khỉ con ngồi trên núi đá giả ăn chuối, khỉ lớn nhảy tới giật chuối, khỉ con chạy theo khóc, 3 bạn nhỏ đứng vỗ tay cười. Đây là ảnh gốc được dùng làm link "xem PNG" trong README chính. |
| `scene-01-monkey-mountain-banana.png` | Cùng bố cục, nhưng là bản **line-art sạch** (ít màu, chỉ điểm vàng/cam ở quả chuối) — đây mới là ảnh nguồn thật sự dùng để render, đi kèm `*.annotation.json`. |
| `scene-01-monkey-mountain-banana.annotation.json` | Chú thích 3 vùng theo đúng mạch tường thuật: `left` (khỉ con cầm chuối trên núi — bối cảnh) → `center` (khỉ lớn nhảy tới giật chuối — xung đột) → `right` (các bạn nhỏ vỗ tay cười — phản ứng/kết quả). `canvas` = 1672×941, khớp đúng kích thước ảnh. |
| `scene-01-monkey-mountain-banana-whiteboard.mp4` | Video kết quả render đầy đủ (nét vẽ stream + tô màu) từ ảnh + annotation ở trên. |
| `scene-01-monkey-mountain-banana-whiteboard.gif` | Bản GIF dung lượng nhỏ của video trên, tiện nhúng vào tài liệu / chat. |
| `scene-01-monkey-mountain-stream.gif` | GIF demo được README chính nhúng trực tiếp để minh hoạ hiệu ứng "nét vẽ liên tục kiểu stream". |

### Xem lại / render lại ví dụ này

Chú thích đã có sẵn, nên có thể render lại ngay mà không cần làm lại bước 1-5
của quy trình trong `SKILL.md`:

```bash
# Chuẩn bị môi trường (lần đầu)
python scripts/prepare_env.py --check
python scripts/prepare_env.py          # in ra ENV_PY=<đường dẫn interpreter>

# Render lại MP4 từ ảnh + annotation có sẵn
<ENV_PY> scripts/render_stream_whiteboard.py \
  examples/scene-01-monkey-mountain-banana.png \
  examples/scene-01-monkey-mountain-banana.annotation.json \
  examples/scene-01-monkey-mountain-banana-whiteboard.mp4 \
  assets/drawing-hand.png \
  --ink-path grid --color-fill contour-wipe
```

Muốn xem thử cách chia vùng/thứ tự, mở `assets/preview.html` trong Chrome/Edge
→ "Mở thư mục" → chọn thư mục `examples/` → bảng Preview sẽ nạp
cặp `scene-01-monkey-mountain-banana.png` + `.annotation.json`.

### Dùng làm ví dụ tham khảo khi tự làm dự án mới

Đây là ví dụ tốt để xem cách viết `annotation.json` cho ảnh **1 cảnh có nhiều
nhân vật chồng lấn theo chiều ngang** (3 nhóm nhân vật tách biệt rõ ràng theo
trục x, không cần `protectedRegions` vì các vùng không giao nhau). So sánh với
[`assets/whiteboard/demo-phong-canh/`](../assets/whiteboard/demo-phong-canh/README.md)
để thấy ví dụ một **dự án nhiều cảnh** hoàn chỉnh (2 cảnh, có `scenes.json`,
có ghép video và thêm giọng đọc).
