# Các ví dụ trong `assets/whiteboard/`

Mỗi thư mục con là một "dự án" theo đúng quy ước trong `SKILL.md`:
`assets/whiteboard/<tên dự án>/scene-0x-<tên>.png` đi kèm
`.annotation.json` cùng tên. Xem file `README.md` riêng trong từng thư mục để
biết chi tiết nội dung và cách dùng.

| Thư mục | Trạng thái | Mô tả |
|---|---|---|
| [`demo-phong-canh/`](demo-phong-canh/README.md) | ✅ Đầy đủ (annotation + video từng cảnh + video ghép + bản có giọng đọc) | Ví dụ 2 cảnh "mặt trời mọc → ngôi nhà ban trưa", dùng để bấm thử toàn bộ app Studio. |
| [`sample-01-mat-troi/`](sample-01-mat-troi/README.md) | 🧪 Nguyên liệu thô (chỉ SRT + 2 ảnh) | Mặt trời mọc sau dãy núi. |
| [`sample-02-ngoi-nha/`](sample-02-ngoi-nha/README.md) | 🧪 Nguyên liệu thô | Ngôi nhà được dựng lên bên gốc cây. |
| [`sample-03-may-mua/`](sample-03-may-mua/README.md) | 🧪 Nguyên liệu thô | Mây trắng chuyển thành mây đen và mưa. |
| [`sample-04-cay-lon-len/`](sample-04-cay-lon-len/README.md) | 🧪 Nguyên liệu thô | Hạt giống lớn thành cây có trái chín. |
| [`sample-05-bau-troi-dem/`](sample-05-bau-troi-dem/README.md) | 🧪 Nguyên liệu thô | Hoàng hôn chuyển sang đêm đầy sao. |
| [`sample-06-con-thuyen/`](sample-06-con-thuyen/README.md) | 🧪 Nguyên liệu thô | Thuyền rời bờ, ra khơi vượt sóng. |
| [`sample-07-y-tuong/`](sample-07-y-tuong/README.md) | 🧪 Nguyên liệu thô | Bóng đèn ý tưởng bừng sáng. |
| [`sample-08-cuon-sach/`](sample-08-cuon-sach/README.md) | 🧪 Nguyên liệu thô | Cuốn sách khép mở ra từng trang chữ. |
| [`sample-09-xe-dap/`](sample-09-xe-dap/README.md) | 🧪 Nguyên liệu thô | Xe đạp từ đứng yên đến lăn bánh trong gió. |
| [`sample-10-trai-tim/`](sample-10-trai-tim/README.md) | 🧪 Nguyên liệu thô | Hai người xa cách xích lại gần nhau qua một trái tim. |

**✅ Đầy đủ** = đã có sẵn `annotation.json` và video mẫu, dùng để xem/ chạy
thử ngay. **🧪 Nguyên liệu thô** = chỉ có `demo.srt` (4 dòng phụ đề → 2 cảnh)
+ 2 ảnh line-art mỗi chủ đề (1280×720, nền `#F5EBD7`, mỗi ảnh 2-5 nhóm chủ
thể), chưa có chú thích hay video — dùng để tự luyện toàn bộ quy trình chú
thích → preview → render → ghép (bước 3-7 trong `SKILL.md`), mỗi README riêng
đều có bảng 4 dòng phụ đề và gợi ý chú thích theo đúng nội dung ảnh của ví dụ
đó.

10 thư mục `sample-*` được tạo bằng `python examples/make_sample_gallery.py`
(vẽ bằng QPainter, không cần mạng) — chạy lại script này bất kỳ lúc nào để
phục hồi cả 10 thư mục về đúng trạng thái gốc nếu bạn lỡ sửa hỏng khi luyện
tập.

Quy trình đầy đủ và các quy chuẩn (hình ảnh, toạ độ, timing) nằm trong
[`SKILL.md`](../../SKILL.md). Ví dụ về một dự án 1 cảnh có nhiều nhân vật
chồng lấn theo chiều ngang: [`examples/`](../../examples/README.md).
