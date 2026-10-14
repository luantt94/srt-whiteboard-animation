# Hướng dẫn sử dụng SRT Whiteboard Studio

Giao diện PySide6 gói toàn bộ quy trình của skill **srt-whiteboard-animation**:
biến ảnh line-art (kèm phụ đề `.srt` tuỳ chọn) thành video vẽ tay trên bảng
trắng nền giấy vàng kem, mỗi đối tượng trong ảnh được vẽ lần lượt theo đúng
thứ tự bạn sắp xếp.

App chỉ còn **đúng một màn hình** (không còn các tab 1→6 kiểu cũ): chọn ảnh →
app **tự nhận diện ngay** các đối tượng cần vẽ trong từng ảnh → chỉnh thứ
tự/thời gian ngay trên **timeline kiểu CapCut** (kéo-giãn trực tiếp, không
cần mở hộp thoại) nếu muốn → bấm 1 nút → xem video ngay trong cửa sổ.

---

## 1. Yêu cầu

- **Windows / macOS / Linux** có sẵn **Python ≥ 3.9** (chỉ cần để khởi động;
  app tự tạo môi trường riêng).
- Kết nối mạng cho lần chạy đầu (tải `opencv-python`, `numpy`, `av`, `Pillow`,
  `PySide6` vào thư mục `.venv` của skill). `opencv-python` cũng là thứ app
  dùng để **tự nhận diện đối tượng** trong ảnh khi bạn chọn ảnh.
- `ffmpeg` trong PATH: *tùy chọn* cho bước ghép cảnh (không có thì app dùng
  PyAV), nhưng **bắt buộc** nếu muốn thêm âm thanh / khắc phụ đề — cần bản có
  libass.
- Chế độ tự đọc giọng AI (TTS) cần **kết nối mạng**; app tự cài `edge-tts`
  vào `.venv` trong lần dùng đầu.

---

## 2. Khởi động

| Hệ điều hành | Cách chạy |
|---|---|
| Windows | Nhấp đúp **`run_app.bat`** ở thư mục gốc dự án |
| macOS / Linux | `chmod +x run_app.sh` một lần, rồi `./run_app.sh` |
| Mọi nơi | `python app/launch.py` |

Lần đầu, `launch.py` sẽ tạo `.venv/`, cài `opencv-python`/`numpy`/`av`/
`Pillow`/`PySide6` vào đó, rồi mở cửa sổ Studio bằng trình thông dịch của
`.venv`. Các lần sau khởi động gần như tức thì.

---

## 3. Chạy thử ngay với dữ liệu mẫu

Lần đầu mở app (chưa có dự án nào lưu trước), app **tự nạp dự án mẫu**
`assets/whiteboard/demo-phong-canh/` — 2 ảnh + phụ đề đã điền sẵn. Vì dự án
mẫu đã có sẵn video thành phẩm, khung phát ở cuối màn hình **hiện video ngay**
mà chưa cần bấm gì. Nạp lại bất kỳ lúc nào bằng nút **"Dùng ảnh mẫu để thử"**
hoặc menu *Trợ giúp → Nạp dự án mẫu*.

Muốn tự chạy lại từ đầu (ghi đè video có sẵn): bấm **"Dùng ảnh mẫu để thử"**
rồi bấm **🚀 TẠO VIDEO NGAY** — xem mục 5 bên dưới.

Muốn tạo lại dữ liệu mẫu từ đầu: `python examples/make_demo_project.py`.
Kho còn 10 bộ ảnh mẫu khác (nhiều đối tượng hơn, chưa có chú thích) ở
`assets/whiteboard/sample-01..10` — xem
[`assets/whiteboard/README.md`](../assets/whiteboard/README.md).

---

## 4. Bố cục màn hình

- **Thanh trên – Môi trường & dự án**: *Chuẩn bị / kiểm tra môi trường* chạy
  `scripts/prepare_env.py`; *Dự án* là thư mục chứa ảnh + annotation + video
  (quy ước `assets/whiteboard/<tên-dự-án>/`) — app tự tạo một thư mục mới khi
  bạn chọn ảnh lần đầu, không cần tự tạo tay.
- **1. Ảnh cảnh**: chọn ảnh + timeline kiểu CapCut (4 dải: cảnh/đối tượng/
  chữ/âm thanh, kéo-giãn trực tiếp — mục 5).
- **2. Phụ đề** (tuỳ chọn): chọn/sửa nội dung `.srt`.
- **3. Âm thanh** (tuỳ chọn): file nhạc/giọng có sẵn, hoặc TTS.
- **Nút 👁 Xem nhanh** (xem thử tức thì, không cần chờ) và **🚀 TẠO VIDEO
  NGAY**, thanh tiến độ, khung phát video.
- **Dòng trạng thái ở cuối cửa sổ**: trạng thái + tiến trình + nút *Dừng tác
  vụ* + nút **▸ Nhật ký** (bấm để mở xem chi tiết lệnh/lỗi khi cần, mặc định
  ẩn cho gọn).

Mỗi mục 1/2/3 có nút ▾/▸ ở đầu để thu gọn/mở rộng. Sau khi tạo video xong, cả
3 mục tự thu gọn để khung video hiện ngay, không cần cuộn.

---

## 5. Quy trình

### Bước 1 — Chọn ảnh (app tự nhận diện ngay)

Bấm **"Chọn ảnh…"** (chọn nhiều ảnh = nhiều cảnh nối tiếp nhau trong video),
hoặc **"Dùng ảnh mẫu để thử"**. Ảnh line-art nền `#F5EBD7`, không chữ, nhiều
khoảng trắng (xem "Quy chuẩn hình ảnh" trong `SKILL.md`) sẽ cho kết quả nhận
diện tốt nhất.

Ngay khi ảnh được thêm vào, app **tự nhận diện các đối tượng** trong từng
ảnh (so màu với nền giấy, gộp các nét gần nhau thành từng khối) và xếp sẵn
theo thứ tự trái→phải — không cần đợi tới lúc tạo video. Đây chỉ là gợi ý
ban đầu, không hoàn hảo (vật thể chạm nhau có thể bị gộp làm một, vật thể
rời rạc có thể bị tách thành nhiều khối); bạn chỉnh lại ngay trên timeline
hoặc trong cửa sổ chi tiết (xem bước 2).

### Bước 2 — Timeline kiểu CapCut: sửa nhanh thứ tự & thời gian

Timeline hiện 4 dải xếp chồng theo đúng tỉ lệ thời gian thật:

| Dải | Nội dung | Thao tác |
|---|---|---|
| **Cảnh** (trên cùng) | 1 khối/ảnh, có ảnh thu nhỏ | **Kéo cả khối** sang vị trí khác để đổi **thứ tự cảnh** — app tự đánh lại số thứ tự trong tên file. Bấm (không kéo) để mở cửa sổ chi tiết. Bấm chọn 1 khối rồi bấm **"🗑 Xoá ảnh đã chọn"** (có hộp xác nhận) để xoá hẳn ảnh đó khỏi dự án, kể cả annotation và video riêng đã render. |
| **Đối tượng** | Mỗi khối màu = 1 vùng vẽ app đã nhận diện trong cảnh đang chọn | **Kéo thân khối** để đổi **thời điểm bắt đầu**; **kéo 2 đầu khối** để đổi **thời lượng** — kéo trực tiếp ngay trên timeline, không cần mở hộp thoại. App tự giữ các khối **nối tiếp nhau, không chồng thời gian** (kéo lố sẽ bị chặn lại ở khối liền kề). Bấm (không kéo) để mở cửa sổ chi tiết đúng khối đó (sửa tên, vùng `x/y/rộng/cao`, hướng vẽ, phụ đề…). |
| **Chữ** (màu vàng) | Chữ chèn lên video | Bấm **"+ Thêm chữ"** để thêm; kéo thân/2 đầu để đổi thời điểm/thời lượng hiện chữ; bấm (không kéo) để sửa nội dung; chọn 1 đoạn rồi bấm **"Xoá chữ đã chọn"** để xoá. |
| **Âm thanh** (màu xanh lá) | Xem trước độ dài file đã chọn ở mục 3 | Chỉ xem, không kéo — đổi file ở mục 3 bên dưới timeline. |

Thứ tự vùng vẽ nên theo mạch: **bối cảnh → nhân vật/vật thể chính → hành
động/biến hoá → phản ứng/kết quả**.

Nếu muốn sửa chi tiết hơn (thêm/xoá khối, gõ số chính xác…), bấm vào khối
cảnh hoặc khối đối tượng (không kéo) để mở cửa sổ **"Chỉnh vùng vẽ · thứ tự
· thời gian"**:

1. Kéo cả khung để di chuyển, kéo 4 góc/4 cạnh để chỉnh **vùng** (`region`).
2. Bên phải: kéo danh sách **Khối vẽ** để đổi **thứ tự vẽ**, hoặc bấm
   **+ Thêm khối** / **Xoá khối đã chọn** nếu auto-detect gộp/tách sai.
3. Sửa **Tên, x/y/Rộng/Cao, Hướng, Bắt đầu (ms)/Kết thúc (ms)** và ô
   **Phụ đề** của khối đang chọn.
4. Kéo thanh thời gian ở dưới hoặc bấm **▶** để xem thử hiệu ứng lộ dần.
5. Bấm **Đóng** (hoặc phím Esc / nút X) để **tự lưu** mọi thay đổi rồi đóng
   cửa sổ — không cần bấm nút lưu riêng. Muốn bỏ hết thay đổi vừa chỉnh, bấm
   **Huỷ** thay vì Đóng. Timeline bên ngoài tự cập nhật theo.

Nếu bỏ qua bước này hoàn toàn, lúc bấm **TẠO VIDEO NGAY**, app vẫn dùng đúng
kết quả auto-detect đã có từ bước 1 cho ảnh nào chưa chỉnh tay.

### Bước 3 — Phụ đề (tuỳ chọn)

Chọn file `.srt` có sẵn, hoặc gõ thẳng vào ô nội dung rồi bấm **"Lưu nội dung
phụ đề"**. Có phụ đề thì mỗi cảnh lấy đúng thời lượng theo mốc thời gian
tương ứng; không có thì mỗi ảnh dùng mặc định ~9 giây. Xem mục 7 nếu chưa có
file `.srt`.

### Bước 4 — Âm thanh (tuỳ chọn)

Chọn **một trong hai**: file nhạc/giọng đọc có sẵn (**"+ Thêm file âm
thanh…"**), hoặc tick **"Tự đọc lời bình bằng giọng AI (TTS)"** (cần có phụ
đề ở bước 3, và cần `ffmpeg`). Có phụ đề thì phụ đề cũng được khắc lên video
dù dùng nguồn âm thanh nào. File âm thanh đã chọn hiện thành dải màu xanh lá
ở cuối timeline (bước 2) để ước lượng độ dài so với video.

Chữ đã thêm trên dải **"Chữ"** của timeline (bước 2) cũng tự được khắc lên
video ở bước tạo video tiếp theo — kể cả khi không chọn âm thanh/phụ đề nào,
cần `ffmpeg` để thực hiện bước khắc chữ này.

### Bước 5 — Xem nhanh (không cần đợi render)

Bấm **"👁 Xem nhanh"** cạnh nút tạo video để mở cửa sổ xem thử **gần như tức
thì**: mô phỏng đúng hiệu ứng lộ dần, phụ đề, chữ chèn và âm thanh (nếu đã
chọn file âm thanh — TTS thì chưa có vì chưa tạo giọng đọc) ngay trong app,
không cần gọi ffmpeg hay vẽ video thật nên không phải chờ lâu. Có nút
Phát/Tạm dừng và thanh tua để kiểm tra nhanh thứ tự/thời gian trước khi tạo
video thật. Khác biệt duy nhất so với video thành phẩm: bản xem nhanh **chưa
có nét vẽ tay** (hand-drawing animation).

### Bước 6 — Tạo video thật

Bấm **🚀 TẠO VIDEO NGAY**. Thanh tiến độ hiện % và bước đang chạy (chuẩn bị
môi trường → phân tích phụ đề → tạo chú thích tự động → vẽ từng cảnh → ghép
→ thêm âm thanh). Xong thì video **tự phát ngay** trong khung bên dưới — bấm
**⟲** để phát lại từ đầu bất kỳ lúc nào.

Muốn sửa lại rồi tạo lại: mở lại mục 1/2/3 (bấm nút ▸ để mở), chỉnh, rồi bấm
**TẠO VIDEO NGAY** lần nữa.

---

## 6. Cấu trúc thư mục dự án

```text
assets/whiteboard/<tên-dự-án>/
├── scenes.json                       # kết quả phân tích SRT (nếu có SRT)
├── scene-01-<tên>.png                # ảnh line-art
├── scene-01-<tên>.annotation.json    # cùng tên với PNG (tự tạo hoặc tự chỉnh)
├── scene-01-<tên>-whiteboard.mp4     # video từng cảnh
├── texts.json                        # chữ chèn trên timeline (nếu có thêm)
├── <tên-dự-án>-final.mp4             # video ghép hoàn chỉnh
└── <tên-dự-án>-voice.mp4             # bản có thêm âm thanh/phụ đề/chữ (nếu dùng)
```

PNG và annotation **phải cùng tên gốc** — app dựa vào đó để ghép cặp. Đổi
thứ tự bằng cách kéo khối cảnh trong timeline (mục 5, bước 2) thay vì tự đổi
tên file tay, để các file đi kèm (annotation, video đã render) tự đi theo
đúng ảnh.

---

## 7. File SRT lấy ở đâu

SRT là file văn bản thuần, mở bằng Notepad. Mỗi khối gồm: số thứ tự → mốc
`bắt đầu --> kết thúc` → dòng lời → dòng trống.

```srt
1
00:00:00,000 --> 00:00:03,500
Con khỉ nhỏ ngồi trên đỉnh núi, tay cầm quả chuối.

2
00:00:03,500 --> 00:00:07,200
Một con khỉ lớn lao tới giật lấy quả chuối.
```

Cách tạo:

- **Gõ tay** trong Notepad, lưu đuôi `.srt`, encoding UTF-8 (hoặc gõ thẳng
  vào ô phụ đề trong app, bấm Lưu).
- **Từ audio bằng Whisper**: `pip install openai-whisper` rồi
  `whisper loi-binh.mp3 --output_format srt`.
- **Từ CapCut / Premiere / DaVinci Resolve / Subtitle Edit**: tạo caption rồi
  Export `.srt`.

---

## 8. Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| Dòng môi trường vẫn `✘` | Bấm lại *Chuẩn bị / kiểm tra môi trường*, mở **▸ Nhật ký** xem lỗi. Thường do mạng khi cài `pip`. |
| `launch.py` không mở được cửa sổ | Chạy `python app/launch.py` trong terminal để đọc thông báo lỗi. Trên Linux có thể thiếu thư viện hệ thống của Qt (`libxcb`, `libgl1`). |
| Auto-detect gộp nhiều vật thể làm một / tách một vật thể thành nhiều khối | Bình thường — thuật toán chỉ so màu nền, không hiểu ngữ nghĩa. Bấm vào ảnh đó, tự gộp/tách lại bằng cách sửa vùng, xoá/thêm khối (mục 5, bước 2). |
| Không nhận diện được đối tượng nào (chỉ ra 1 vùng phủ toàn ảnh) | Ảnh quá đơn giản/trắng, hoặc thiếu OpenCV trong môi trường — app tự dùng phương án dự phòng (1 vùng), vẫn chỉnh tay được bình thường. |
| Render rất chậm | Ảnh càng nhiều đối tượng càng lâu; cứ để app chạy, theo dõi % ở thanh tiến độ. |
| Ghép cảnh cảnh báo `ffmpeg` | Không sao — app tự chuyển sang PyAV (chậm hơn, có mã hóa lại). |
| Báo "Không tìm thấy ffmpeg" khi thêm âm thanh | Cài ffmpeg (bản full/có libass) và thêm vào PATH, mở lại app. |
| Chữ đã thêm trên timeline không hiện trong video | Cũng cần `ffmpeg` (giống phụ đề/âm thanh) — không có thì app bỏ qua bước này, giữ nguyên video câm. |
| TTS lỗi / treo | Cần mạng. Nếu vẫn lỗi 403, app tự nâng cấp `edge-tts` và thử lại 1 lần; nếu vẫn lỗi thì đổi sang chọn file âm thanh có sẵn. |
| Video không phát trong khung xem | Kiểm tra máy đã có codec H.264/AAC (thường có sẵn trên Windows/macOS hiện đại). Vẫn có thể bấm "Mở bằng trình phát ngoài" (VLC…). |

---

## 9. Kiểm tra chất lượng trước khi xuất bản

- Khung hình đầu là nền giấy vàng kem sạch, không lộ nét trước.
- `canvas` trong annotation bằng đúng kích thước pixel ảnh gốc; mọi `region`
  là số nguyên và nằm trong khung ảnh.
- Thứ tự & thời gian các khối khớp đúng mạch câu chuyện bạn muốn kể (tự kiểm
  tra lại sau auto-detect, vì thuật toán không hiểu nội dung).
- Ở đoạn giữa: vùng chưa tới lượt không hiện sớm.
- Kết cảnh dừng ít nhất 0,5 giây ở ảnh hoàn chỉnh.
- Video ghép đúng thứ tự các cảnh như trong timeline.
