---
name: srt-whiteboard-animation
description: Biến phụ đề SRT thành video hoạt hình vẽ tay trên bảng trắng nền giấy vàng kem ấm: đọc phụ đề → đưa ra chiến lược ảnh minh hoạ → sau khi xác nhận thì tạo ảnh line-art thống nhất phong cách → chú thích phân vùng theo ngữ nghĩa tường thuật → chỉnh sửa ở bảng Preview → render ra MP4. Cách dàn dựng vẫn dùng kiểu che/lộ theo phân vùng (annotation.json / sequence / startMs / protectedRegions), nhưng cách "xuống mực" trong mỗi vùng đổi thành nét vẽ liên tục kiểu stream (ink→color theo khung xương/lưới). Kích hoạt khi người dùng cung cấp phụ đề SRT và yêu cầu "biến phụ đề thành video vẽ tay bảng trắng/nét vẽ liên tục", "tạo hoạt hình bảng trắng từ SRT", "vẽ tay theo phân cảnh phụ đề".
---

# Hoạt hình bảng trắng từ SRT (dàn dựng bằng mask + vẽ kiểu stream)

Biến phụ đề SRT thành hoạt hình vẽ tay trên bảng trắng: **cách dàn dựng** vẫn dùng kiểu che/lộ theo phân vùng (lộ dần từng vùng theo thứ tự tường thuật, vùng chưa bắt đầu thì ẩn hoàn toàn, vùng chồng lấn được bảo vệ bằng `protectedRegions`); **cách vẽ** đổi thành nét vẽ liên tục kiểu stream — trong phạm vi mặt nạ cho phép của mỗi vùng, đầu bút trượt liên tục theo khung xương/lưới để xuống mực (bắt đầu nét `ink` → tô màu `color`), tất cả các vùng dùng chung một khung vẽ bền vững, vùng đã vẽ xong vẫn giữ nguyên trên khung vẽ. Toàn bộ nội dung hướng tới người dùng — thuyết minh, phân cảnh, cấu hình và giao diện — phải dùng tiếng Việt.

Khác với kiểu nhảy khung từng ô hoặc xoá theo hình chữ nhật: nét vẽ của skill này **liên tục mượt mà**; khác với stream vẽ nguyên cả ảnh: skill này vẽ lần lượt theo **phân vùng tường thuật từ phụ đề**, có thể kiểm soát thứ tự xuất hiện và thời gian của từng phần tử.

## Thông số mặc định khi triển khai

| Mục | Yêu cầu mặc định |
|---|---|
| Nền giấy | Ảnh tạo ra dùng màu giấy cũ vàng kem ấm (khuyến nghị `#F5EBD7`); khi render, lấy mẫu màu nền từ vùng lùi vào từ 4 góc ảnh gốc để tô nền, cấm dùng trắng tinh. |
| Cách vẽ | Mỗi vùng vẽ nét liên tục kiểu stream: bắt đầu bằng `ink` (phủ nét line-art) → tô thêm `color` (khôi phục màu gốc); tỉ trọng `ink:color = 2:1`. |
| Đường đi nét vẽ | `--ink-path grid` (lưới, mặc định, ổn định) hoặc `skeleton` (bám khung xương, hợp với ảnh line-art nét rõ). |
| Phong cách tô màu | `--color-fill contour-wipe` (quét theo đường viền, mặc định) hoặc `brush` (tô theo quỹ đạo nét vẽ). |
| Vùng chưa vẽ | Mặt nạ cho phép của mỗi vùng = hình chữ nhật `region` trừ đi "các vùng phía sau + protectedRegions"; vùng chưa bắt đầu thì ẩn hoàn toàn. |
| Nguồn thời lượng | `sceneDurationMs` của mỗi ảnh lấy từ khoảng thời gian phụ đề của cảnh đó (khuyến nghị 25–35 giây/cảnh). |
| Khung chỉnh sửa | Bảng Preview mặc định hiển thị toàn bộ khung chỉnh sửa đánh số; khung chỉnh sửa không thuộc nội dung hình ảnh của video. |

## Quy chuẩn hình ảnh thống nhất khi tạo ảnh (bắt buộc)

Ảnh nguồn của mọi cảnh phải tuân theo cùng một ngôn ngữ hình ảnh; trước khi tạo ảnh, đưa đầy đủ các yêu cầu dưới đây vào prompt tạo ảnh, sau khi tạo xong kiểm tra lại từng điều:

- **Phong cách & bố cục:** Minh hoạ vẽ tay tối giản, phong cách phác thảo bút chì thuần tuý, thẩm mỹ doodle tiết chế kiểu Notion. Lấy việc truyền đạt khái niệm làm chính, không theo đuổi tả thực; bố cục đơn giản, nền sạch, nhiều khoảng trống, cảm giác tổng thể nhẹ nhàng rõ ràng, nét vẽ/nhân vật/bảng màu nhất quán trong cả series.
- **Màu sắc & chất liệu:** Nền giấy màu kem `#F5EBD7`, nét phác thảo màu xám đậm; chỉ được dùng màu đỏ, cam, xanh dương làm điểm nhấn khái niệm với liều lượng ít. Không được dùng màu nhấn khác, bảng màu độ bão hoà cao hay kết cấu phức tạp.
- **Nhân vật & đối tượng:** Thể hiện đối tượng bằng đường viền đơn giản, ít nét vẽ và nhiều khoảng trống, nhấn mạnh mối quan hệ/sự thay đổi/khái niệm cốt lõi, chứ không phải tỉ lệ thật, chất liệu hay chi tiết.
- **Tuyệt đối cấm:** Bất kỳ chữ, từ, chữ cái, số, font chữ hay nhãn nào trong ảnh nguồn của cảnh; cảm giác tả thực, chi tiết như ảnh chụp, hiệu ứng 3D, chất liệu tranh vẽ; cảnh phức tạp, nền dày đặc, trang trí rườm rà và hình ảnh độ bão hoà cao.
- **Ngoại lệ cho tay vẽ:** Nếu người dùng nói rõ chữ trên thân bút là nhãn hiệu của họ và yêu cầu giữ lại, có thể giữ nguyên nhãn đó trên thân bút trong `drawing-hand.png`; nó không thuộc chữ trong ảnh nguồn của cảnh, cũng không cần xoá hay vẽ lại. Khi chưa có yêu cầu rõ ràng từ người dùng, vẫn xử lý theo nguyên tắc không có chữ trong khung hình.

## Chốt xác nhận (bắt buộc)

Trong quy trình mặc định, **sau khi hoàn thành mỗi bước đều phải dừng lại và chờ người dùng xác nhận rõ ràng** mới được bắt đầu bước tiếp theo. Trước khi được xác nhận, không được tạo ảnh, chú thích, bản xem trước, video hay file ghép của bước sau; không được coi "chưa trả lời", "sự cho phép chung chung từ trước" hay "người dùng không phản đối" là đã xác nhận. Khi người dùng yêu cầu sửa lại bước trước, chỉ làm lại đúng bước đó, rồi lại chờ xác nhận sau khi hoàn thành.

Hành động liên đới duy nhất là: **ngay sau khi tạo xong file chú thích (annotation JSON), phải tự động mở bảng Preview và nạp luôn thư mục chứa file JSON đó**; đây thuộc về phần bàn giao của bước 3, không cần chờ xác nhận riêng cho việc "mở bảng Preview". Nếu File System Access API của trình duyệt yêu cầu thao tác tay của người dùng, hãy dùng giao diện trình duyệt để chọn đúng thư mục đã xác định sẵn; không được vì vậy mà xin thêm xác nhận từ người dùng hoặc đổi thành để người dùng tự mở bảng Preview.

## Quy trình làm việc

1. **Đọc phụ đề, đưa ra chiến lược (chưa tạo ảnh).** Dùng `scripts/parse_srt.py` để phân tích SRT thành các dòng phụ đề và đề xuất phân cảnh theo 25–35 giây/cảnh. Từ đó đưa ra chiến lược ảnh minh hoạ: số thứ tự cảnh, ý chính cần truyền tải, chủ thể hình ảnh, khoảng phụ đề tương ứng và `sceneDurationMs` của từng cảnh. Mỗi cảnh chỉ truyền tải một ý chính. **Xong thì dừng lại, chờ người dùng xác nhận chiến lược.**
2. **Tạo ảnh line-art.** Chỉ sau khi người dùng xác nhận chiến lược, mới theo "Quy chuẩn hình ảnh thống nhất" để tạo lần lượt từng ảnh cảnh dạng line-art tỉ lệ 16:9, nền giấy cũ vàng kem ấm `#F5EBD7`, giữa các chủ thể chừa đủ khoảng trống để tiện tách vùng tự động; không được tạo chữ, ảnh chụp phức tạp, đối tượng chồng lấn hay yếu tố trái quy chuẩn. **Xong thì dừng lại, trình bày ảnh line-art và chờ người dùng xác nhận.**
3. **Đọc phụ đề trước, xem ảnh sau, rồi chú thích và mở bảng Preview.** Chỉ sau khi người dùng xác nhận ảnh line-art, mới đọc phụ đề tương ứng với ảnh đó, sau đó thực sự xem ảnh, và lấy kích thước pixel gốc của ảnh; không được chỉ dựa vào phụ đề để đoán hình, cũng không được chỉ sắp xếp máy móc theo vị trí trên ảnh. Trước tiên rút ra các sự kiện tường thuật trong phụ đề, rồi ánh xạ các chủ thể nhìn thấy trong ảnh vào từng sự kiện, sắp xếp thứ tự vẽ theo trình tự ngữ nghĩa "dựng bối cảnh → nhân vật/vật thể chính → hành động xung đột hoặc biến chuyển → phản ứng/kết quả". Sau đó tạo file `<tên ảnh>.annotation.json`. Ngay sau khi tạo xong, mở `assets/preview.html` bằng trình duyệt mặc định, rồi dùng nút "Mở thư mục" của bảng Preview để nạp toàn bộ `<tên>.png` + `<tên>.annotation.json` trong **thư mục chứa file chú thích đó**; không được chỉ đưa đường dẫn file hoặc yêu cầu người dùng tự thao tác. **Sau khi bảng Preview đã nạp xong thư mục thì dừng lại, chờ người dùng xác nhận chú thích và nội dung xem trước.**
4. **Tạo ảnh xem trước theo vùng.** Chỉ sau khi người dùng xác nhận chú thích và nội dung xem trước, mới dùng `render_annotation_preview.py` để xuất ảnh kiểm tra đánh số/hướng vẽ, đối chiếu xem phân vùng có khớp thứ tự tường thuật không, các vùng có nằm trong khung ảnh không, chủ thể chồng lấn đã được bảo vệ bằng `protectedRegions` chưa. **Xong thì dừng lại, chờ người dùng xác nhận ảnh xem trước.**
5. **Chỉnh sửa và lưu trong bảng Preview.** Chỉ sau khi người dùng xác nhận ảnh xem trước, mới chỉnh sửa trong bảng Preview đã mở sẵn và đã nạp đúng thư mục: mặc định (khi chưa phát) hiển thị ảnh đầy đủ cùng khung các vùng; khung vẽ là **bản đại diện dạng hình chữ nhật**: kéo 4 cạnh/4 góc của khung để đổi `region`, bên phải chỉnh tên/hướng/**bắt đầu (ms)/kết thúc (ms)** (thời lượng = kết thúc − bắt đầu, chỉ đọc) và **phụ đề**, kéo danh sách khối để **đổi thứ tự** (tự động sắp lại `sequence`), chọn một khối sẽ tự động làm nổi bật phụ đề tương ứng; kéo thanh thời gian hoặc bấm phát để xem hiệu ứng lộ dần (vùng chưa bắt đầu sẽ không hiển thị); `direction` chỉ ảnh hưởng tới bản đại diện này. Sau khi chỉnh xong, bấm "Lưu cảnh này/Lưu tất cả" để ghi đè lại file `.annotation.json` gốc (gồm cả `subtitle` của mỗi vùng, và căn `sceneDurationMs` theo thời điểm kết thúc của vùng cuối + 0.5s). **Sau khi lưu thì dừng lại, chờ người dùng xác nhận chú thích và thời lượng cuối cùng.**
6. **Render thành phim bằng dòng lệnh.** Chỉ sau khi người dùng xác nhận chú thích và thời lượng cuối cùng, mới dùng `render_stream_whiteboard.py` để xuất MP4 full nét cho từng cảnh, kiểm tra ngẫu nhiên 3 mốc thời gian: mở đầu, giữa một khối bất kỳ có chồng lấn, và kết thúc. **Xong thì dừng lại, chờ người dùng xác nhận video thành phẩm.**
7. **Ghép nhiều cảnh (chỉ áp dụng khi có nhiều cảnh).** Chỉ sau khi người dùng đã xác nhận video thành phẩm của từng cảnh riêng lẻ, mới dùng `merge_scenes.py` để ghép theo đúng thứ tự thành một video duy nhất. **Xong thì dừng lại, chờ người dùng xác nhận video ghép cuối cùng.**

## Quy ước thư mục

Tạo trong thư mục dự án của người dùng:

```text
assets/whiteboard/<tên dự án>/
  scene-01-<tên>.png
  scene-01-<tên>.annotation.json     # cùng tên với file png
  scene-01-<tên>-whiteboard.mp4      # video thành phẩm
  scene-01-<tên>-preview.mp4         # đoạn xem trước thật (do bảng Preview tạo, độ nét thấp)
```

Ảnh và file cấu hình phải cùng tên: `foo.png` tương ứng với `foo.annotation.json`. Bảng Preview dựa vào đó để tự động nạp cấu hình.

## Sắp xếp theo ngữ nghĩa và chú thích theo từng pixel (bắt buộc thực hiện)

1. **Căn cứ để đọc:** Trước khi chú thích, phải có đồng thời cả phụ đề lẫn ảnh gốc đã được xem qua. Thiếu một trong hai thì phải hỏi lại trước, không được tạo chú thích.
2. **Căn cứ để sắp thứ tự:** `sequence`, `startMs` và `label` phải phản ánh đúng trình tự sự kiện trong phụ đề, chứ không chỉ xếp theo trái→phải, trên→dưới hay mức độ nổi bật thị giác.
3. **Căn cứ về toạ độ:** Mỗi khối xuất `x`, `y`, `width`, `height` là số nguyên pixel theo hệ toạ độ ảnh gốc; gốc toạ độ ở góc trên-trái, cấm dùng toạ độ theo phần trăm/tỉ lệ/ước lượng hoặc bỏ qua kích thước. `canvas.width`/`canvas.height` phải bằng đúng kích thước pixel của ảnh gốc.
4. **Các trường của khối:** Mỗi phần tử gồm `sequence`, `narrativeRole`, `subtitle`, `region`, `reveal`, `handPath`. `narrativeRole` dùng tiếng Việt để mô tả vai trò tường thuật của khối đó trong phụ đề; `subtitle` lưu đoạn phụ đề tương ứng với vùng đó (lấy từ SRT, phục vụ liên kết trong bảng Preview và các mục đích sau này); `sequence` đánh số liên tục bắt đầu từ 1.
5. **Kiểm tra:** Trước khi tạo ảnh xem trước, kiểm tra từng vùng xem có nằm trong khung ảnh không, có phủ đúng chủ thể nhìn thấy tương ứng không, có khớp với sự kiện trong phụ đề không; với chủ thể chồng lấn, dùng `protectedRegions` để bảo vệ trước khi vẽ khối đó.

## Mô hình thời gian (dành riêng cho cách vẽ stream)

- **Tổng thời lượng mỗi cảnh** `sceneDurationMs` lấy từ khoảng thời gian phụ đề của cảnh đó (giá trị `scenes[].sceneDurationMs` do `parse_srt.py` tính).
- **Các vùng vẽ tuần tự:** Cách vẽ stream mô phỏng một cây bút đang di chuyển, nên các vùng trong cùng một cảnh phải **diễn ra lần lượt theo thời gian** (`startMs` không chồng lấn): vùng tiếp theo bắt đầu từ `startMs + durationMs` của vùng trước đó (+ có thể thêm 100–300ms nghỉ). Nếu `startMs` bị chồng lấn, renderer vẫn xử lý theo đúng thứ tự, nhưng về mặt hình ảnh sẽ không còn là vẽ song song nữa.
- **Trong mỗi vùng là ink→color:** `durationMs` của mỗi vùng được chia theo tỉ lệ `ink:color = 2:1` thành đoạn bắt đầu nét và đoạn tô màu. `durationMs` do **thời gian bắt đầu/kết thúc** trên bảng Preview quyết định (kết thúc − bắt đầu), có thể căn theo đúng thời lượng phụ đề tương ứng của vùng đó; cũng có thể dùng công thức 150 pixel/giây × khoảng cách nét vẽ để ước lượng ban đầu.
- **Dừng lại ngắm kết thúc:** Sau khi tất cả các vùng vẽ xong, tự động kéo dài thêm cho đủ `sceneDurationMs`, và đảm bảo giữ nguyên ảnh gốc đầy đủ ít nhất 0.5 giây ở cuối.
- Trong cách vẽ stream, `reveal.direction` **không quyết định nét vẽ thật** (nét vẽ được tự động sinh ra từ khung xương/lưới), chỉ dùng để minh hoạ trên bản đại diện hình chữ nhật của bảng Preview; giữ lại trường này là để bảng Preview có thể hoạt động.

## Bất biến của mặt nạ (tầng dàn dựng, bắt buộc thực hiện)

- Tại thời điểm `t`, một khối chỉ được hiển thị các pixel sau khi `reveal.startMs ≤ t` và không vượt quá tiến độ vẽ hiện tại; bất kỳ nét vẽ/vùng tô/hình ảnh nào của khối chưa bắt đầu đều không được xuất hiện.
- **Mặt nạ cho phép** của mỗi vùng = hình chữ nhật `region` trừ đi toàn bộ `region` của **các khối phía sau**, rồi trừ tiếp `reveal.protectedRegions` của chính khối đó. Nét vẽ stream bị giới hạn trong mặt nạ cho phép này, nên các vùng phía sau sẽ không bị lộ nét trước thời điểm của chúng.
- `protectedRegions` dùng cùng hệ toạ độ pixel nguyên của ảnh gốc giống như `region`, áp dụng cho trường hợp hình chữ nhật quá lớn, chủ thể chồng lấn, hoặc nét ở nền có thể bị lộ ra ngoài ý muốn.
- Renderer đã hiện thực hoá cơ chế "giới hạn nét vẽ trong mặt nạ cho phép → các vùng phía sau và vùng được bảo vệ tự nhiên không bị động tới" theo đúng thứ tự; bản đại diện hình chữ nhật của bảng Preview minh hoạ cùng cách dàn dựng này bằng phép trừ `destination-out` tương đương.

## Ví dụ cấu hình

```json
{
  "sceneId": "scene-01",
  "canvas": { "width": 1672, "height": 941 },
  "storyBasis": "Tóm tắt sự kiện phụ đề của cảnh này",
  "sceneDurationMs": 9000,
  "elements": [
    {
      "id": "rockery",
      "label": "Cảnh núi đá giả",
      "sequence": 1,
      "narrativeRole": "Phần dựng bối cảnh mở đầu câu chuyện",
      "subtitle": "Trên núi khỉ, một chú khỉ con ngồi trên đỉnh núi đá giả, tay cầm quả chuối.",
      "type": "structure",
      "region": { "x": 20, "y": 120, "width": 540, "height": 780 },
      "reveal": { "direction": "top_to_bottom", "startMs": 300, "durationMs": 2600, "maskPaddingPx": 22, "protectedRegions": [] },
      "handPath": { "start": [290, 130], "end": [290, 890], "easing": "easeInOut" }
    }
  ]
}
```

> `direction` / `handPath` chỉ dùng cho bản đại diện hình chữ nhật của bảng Preview; nét vẽ trong video thành phẩm do stream tự động sinh ra, không cần tinh chỉnh thủ công.

## Sử dụng các script

Toàn bộ script render chạy bằng trình thông dịch `.venv` có sẵn trong skill (để cô lập dependency).

1. **Chuẩn bị môi trường** (lần đầu hoặc khi thiếu dependency):
   ```bash
   python scripts/prepare_env.py --check   # Kiểm tra; nếu thành công, dòng cuối in ra ENV_PY=<đường dẫn>, lưu lại để dùng sau
   python scripts/prepare_env.py           # Nếu thiếu thì tạo .venv và cài opencv-python/numpy/av
   ```
2. **Phân tích phụ đề + đề xuất phân cảnh:**
   ```bash
   python scripts/parse_srt.py <file.srt> --target-sec 30 --min-sec 25 --max-sec 35
   ```
3. **Ảnh xem trước đánh số vùng:**
   ```bash
   python scripts/render_annotation_preview.py <ảnh> <file_chú_thích> <đường_dẫn_ảnh_xem_trước>
   ```
4. **Bảng Preview (không cần server):** Mở trực tiếp `assets/preview.html` bằng Chrome / Edge, bấm "Mở thư mục" để chọn thư mục → nạp toàn bộ ảnh + file chú thích cùng tên → kéo thả chỉnh sửa → bấm "Lưu" để ghi đè lại file gốc. Việc ghi đè cần File System Access API (Chrome/Edge); trình duyệt khác thì tải file về rồi tự ghi đè thủ công. Việc render vẫn thực hiện qua dòng lệnh (bước 5 bên dưới).
5. **Render thành phim cho một cảnh:**
   ```bash
   <ENV_PY> scripts/render_stream_whiteboard.py <ảnh> <file_chú_thích> <output.mp4> assets/drawing-hand.png \
       [--ink-path grid|skeleton] [--color-fill contour-wipe|brush] [--total-ms <mili_giây>]
   ```
   Khi không truyền `--total-ms`, giá trị `sceneDurationMs` trong file chú thích sẽ được dùng. Dòng cuối cùng in ra `OUTPUT=<đường dẫn>`.
6. **Ghép nhiều cảnh:**
   ```bash
   <ENV_PY> scripts/merge_scenes.py --inputs canh1.mp4 canh2.mp4 canh3.mp4 --output final.mp4
   ```

## Kiểm tra chất lượng

Xác nhận trước/sau khi render:

- Khung hình đầu tiên là nền giấy cũ vàng kem ấm sạch sẽ, chưa lộ nét vẽ nào trước thời điểm.
- Đã đọc phụ đề tương ứng và thực sự xem qua ảnh gốc; `canvas` khớp với kích thước pixel của ảnh gốc, mọi `region` đều là toạ độ pixel nguyên và nằm trong khung ảnh.
- `sequence`, `startMs` khớp với thứ tự sự kiện trong phụ đề; số thứ tự/nhãn/vùng trên ảnh xem trước đều lấy từ cùng một file chú thích JSON.
- Kiểm tra ở 3 mốc thời gian: mở đầu, giữa một khối bất kỳ có chồng lấn, và sau khi tất cả các khối đã vẽ xong — khối chưa vẽ thì không được hiển thị, vùng bảo vệ chồng lấn không bị lộ ra, khung hình cuối hiển thị đầy đủ ảnh gốc.
- Đầu bút bám sát nét vẽ đang tiến hành; với ảnh line-art có nét rõ ràng, có thể dùng `--ink-path skeleton` để nét vẽ bám sát hơn.
- Sau khi tất cả các khối vẽ xong, giữ nguyên ảnh gốc đầy đủ ít nhất 0.5 giây.
- Sau khi ghép nhiều cảnh, thứ tự và thời lượng phải khớp với phân cảnh phụ đề.

Nếu cần chỉnh lại hiệu ứng, hãy chỉnh chú thích (vùng/thứ tự/thời gian) trong bảng Preview (`assets/preview.html`) và lưu lại trước, rồi mới render bằng dòng lệnh; không nên render đi render lại một cách tuỳ tiện mà không có cơ sở chỉnh sửa trước.
