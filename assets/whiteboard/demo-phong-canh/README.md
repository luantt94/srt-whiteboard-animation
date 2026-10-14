# Ví dụ: `demo-phong-canh` (dự án mẫu đầy đủ)

Dự án mẫu **"phong cảnh"** gồm 2 cảnh — đây là ví dụ **duy nhất trong repo đã
đi hết toàn bộ quy trình** của Skill: có phụ đề, có chú thích vùng, có video
từng cảnh, video ghép, và cả bản thêm giọng đọc + khắc phụ đề. Dùng để bấm
thử mọi tính năng của **SRT Whiteboard Studio** (`python app/launch.py`) mà
không cần tự chuẩn bị gì — xem hướng dẫn đầy đủ ở
[`docs/HUONG_DAN_APP.md`](../../../docs/HUONG_DAN_APP.md).

## Câu chuyện

> Buổi sáng, mặt trời nhô lên sau ngọn núi. Một cái cây nhỏ đứng lặng bên sườn
> đồi. Trưa đến, ngôi nhà nhỏ hiện ra giữa đồng. Một chú chim bay ngang qua
> đám mây trắng.

4 dòng phụ đề trên được `parse_srt.py` gộp thành **2 cảnh × 8.6 giây**
(`scenes.json`): cảnh 1 = mặt trời + cây, cảnh 2 = ngôi nhà + chim.

## Nội dung thư mục

| File | Vai trò |
|---|---|
| `demo.srt` | Phụ đề nguồn, 4 dòng tiếng Việt. |
| `scenes.json` | Kết quả `parse_srt.py` đã lưu sẵn: 4 `cues` gộp thành 2 `scenes`, mỗi scene có `sceneDurationMs`. |
| `scene-01-binh-minh.png` | Line-art cảnh 1 (1280×720, nền `#F5EBD7`): núi, mặt trời, cây — vẽ bằng `QPainter`, không chữ, nét xám tối giản. |
| `scene-01-binh-minh.annotation.json` | Chú thích 3 vùng của cảnh 1 (xem bảng bên dưới). |
| `scene-02-ngoi-nha.png` | Line-art cảnh 2: mây, ngôi nhà, chim. |
| `scene-02-ngoi-nha.annotation.json` | Chú thích 3 vùng của cảnh 2. |
| `scene-01-binh-minh-whiteboard.mp4`, `scene-02-ngoi-nha-whiteboard.mp4` | Video đã render của **từng cảnh riêng**. |
| `demo-phong-canh-final.mp4` | Video sau khi **ghép 2 cảnh** bằng `merge_scenes.py` — câm, không phụ đề. |
| `demo-phong-canh-final-av.mp4` | Bản **thêm giọng đọc TTS + khắc phụ đề** từ `demo-phong-canh-final.mp4`, làm bằng `scripts/postprocess_video.py`. |

PNG và annotation **cùng tên gốc** (`scene-01-binh-minh.png` ↔
`scene-01-binh-minh.annotation.json`) — quy ước bắt buộc để app tự ghép cặp
đúng ảnh.

## Chi tiết chú thích từng cảnh

### Cảnh 1 — `scene-01-binh-minh` (bối cảnh buổi sáng)

| `sequence` | `id` | `narrativeRole` | Vùng (px) | `startMs` → `durationMs` |
|---|---|---|---|---|
| 1 | `sun` | bối cảnh bầu trời | `x:110 y:60 w:310 h:300` | 300 → 2400 |
| 2 | `mountain` | chủ thể chính | `x:330 y:285 w:620 h:400` | 2900 → 2800 |
| 3 | `tree` | phản ứng / khép cảnh | `x:975 y:270 w:245 h:400` | 5900 → 2400 |

`canvas` = 1280×720, `sceneDurationMs` = 8600ms. Thứ tự vẽ **mặt trời → núi →
cây** đi theo đúng mạch 2 câu phụ đề của cảnh: "mặt trời nhô lên sau núi" rồi
"cây nhỏ đứng bên sườn đồi".

### Cảnh 2 — `scene-02-ngoi-nha` (buổi trưa)

| `sequence` | `id` | `narrativeRole` | Vùng (px) | `startMs` → `durationMs` |
|---|---|---|---|---|
| 1 | `cloud` | bối cảnh bầu trời | `x:120 y:55 w:470 h:270` | 300 → 2400 |
| 2 | `house` | chủ thể chính | `x:440 y:300 w:445 h:385` | 2900 → 2900 |
| 3 | `bird` | hành động / khép cảnh | `x:890 y:100 w:335 h:250` | 6000 → 2200 |

Cả hai cảnh đều không dùng `protectedRegions` vì 3 vùng nằm tách biệt, không
chồng lấn — một ví dụ "đơn giản nhất có thể" để đọc hiểu cấu trúc
`annotation.json` trước khi làm ví dụ phức tạp hơn (so sánh với
[`examples/scene-01-monkey-mountain-banana.annotation.json`](../../../examples/README.md)).

## Dùng lại dự án này

**Qua app (khuyến nghị):**

```bash
python app/launch.py      # hoặc nhấp đúp run_app.bat (Windows) / ./run_app.sh
```

Lần đầu mở app sẽ tự nạp sẵn dự án này ở tab "⚡ Nhanh" — nạp lại bất kỳ lúc
nào bằng nút **"Dùng ảnh mẫu để thử"** hoặc menu *Trợ giúp → Nạp dự án mẫu*.
Vì đã có sẵn `demo-phong-canh-final-av.mp4`, khung phát video hiện kết quả
ngay mà chưa cần bấm **TẠO VIDEO NGAY**.

**Qua dòng lệnh (để hiểu rõ từng script):**

```bash
ENV_PY=$(python scripts/prepare_env.py --check | tail -1 | cut -d= -f2)

# Render lại một cảnh
"$ENV_PY" scripts/render_stream_whiteboard.py \
  assets/whiteboard/demo-phong-canh/scene-01-binh-minh.png \
  assets/whiteboard/demo-phong-canh/scene-01-binh-minh.annotation.json \
  assets/whiteboard/demo-phong-canh/scene-01-binh-minh-whiteboard.mp4 \
  assets/drawing-hand.png

# Ghép 2 cảnh
"$ENV_PY" scripts/merge_scenes.py \
  --inputs assets/whiteboard/demo-phong-canh/scene-01-binh-minh-whiteboard.mp4 \
           assets/whiteboard/demo-phong-canh/scene-02-ngoi-nha-whiteboard.mp4 \
  --output assets/whiteboard/demo-phong-canh/demo-phong-canh-final.mp4

# (Tuỳ chọn, cần ffmpeg) thêm giọng đọc TTS + khắc phụ đề
"$ENV_PY" scripts/postprocess_video.py \
  --video assets/whiteboard/demo-phong-canh/demo-phong-canh-final.mp4 \
  --output assets/whiteboard/demo-phong-canh/demo-phong-canh-final-av.mp4 \
  --tts-srt assets/whiteboard/demo-phong-canh/demo.srt --tts-group scene \
  --scenes assets/whiteboard/demo-phong-canh/scenes.json \
  --burn-srt assets/whiteboard/demo-phong-canh/demo.srt
```

**Tạo lại từ đầu (xoá sạch rồi vẽ lại):**

```bash
python examples/make_demo_project.py
```

Lệnh trên ghi đè lại `demo.srt`, `scenes.json`, 2 ảnh PNG và 2 file
annotation về đúng trạng thái gốc — không đụng tới các file video đã render
sẵn. Xem thêm chi tiết về script này ở
[`examples/README.md`](../../../examples/README.md).
