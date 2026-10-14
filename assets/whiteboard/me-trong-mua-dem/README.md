# Ví dụ: `me-trong-mua-dem` (Ảnh gốc theo chủ đề — để test app)

6 ảnh line-art **tự vẽ gốc** (script `examples/make_song_theme_images.py`),
lấy cảm hứng từ chủ đề chung "mẹ · mưa đêm · che chở · vượt gian khó" —
**không sao chép lời hay nội dung của bất kỳ bài hát cụ thể nào**. Dùng để
thử app: chọn 6 ảnh này trong tab "⚡ Nhanh", xem auto-detect tách đối tượng,
kéo sắp thứ tự, chỉnh thời gian từng đối tượng, ghép thành video.

| File | Nội dung |
|---|---|
| `scene-01-den-khuya.png` | Đèn dầu toả sáng trong đêm tĩnh lặng, vầng trăng khuyết, chiếc ghế đẩu. |
| `scene-02-me-che-mua.png` | Dáng người đội nón lá đứng cạnh mái tranh che hai hình người nhỏ đang ngủ, mưa rơi. |
| `scene-03-me-qua-suoi.png` | Dáng người lội qua dòng suối giữa hai triền đồi, trời mưa. |
| `scene-04-me-dan-loi.png` | Dáng người đi theo lối mòn qua đồi núi ban đêm, trăng sao. |
| `scene-05-gio.png` | Hình ảnh ẩn dụ: vệt xoáy gió cuốn theo vài chiếc lá. |
| `scene-06-nuoc.png` | Hình ảnh ẩn dụ: dòng nước chảy hiền hoà, gợn sóng lan toả. |

## Về phần lời / phụ đề

Thư mục này **cố tình không có file `.srt`** — phần lời bài hát (nếu bạn
dùng để minh hoạ một bài hát có bản quyền) do bạn tự chuẩn bị/chép vào file
`.srt` riêng, không phải nội dung tôi tạo ra. Khi có file `.srt`, chọn nó ở
mục "2. Phụ đề" trong tab ⚡ Nhanh — các cảnh sẽ tự khớp thời lượng theo mốc
thời gian trong đó.

## Tạo lại / chỉnh sửa

```bash
python examples/make_song_theme_images.py
```

Chạy lại để phục hồi 6 ảnh gốc, hoặc mở file script để chỉnh màu sắc/bố cục
theo ý bạn (các hàm vẽ: `_lamp`, `_mother_figure`, `_rain`, `_roof`,
`_stream`, `_hill`, `_wind_spiral`, `_river`…).
