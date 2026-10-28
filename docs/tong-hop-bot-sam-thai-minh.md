# Bot Sâm Thái Minh: tổng hợp từ đầu đến v0.1.77 (25/10/2026)

## 1. Bot hiện tại
- **Đường đi của tin nhắn:** khách nhắn page Facebook → Pancake → Railway (service `web`, gói Hobby) → Gemini 3.5 Flash-Lite trả lời.
- **Mã nguồn:** repo GitHub `nga3001/samthaiminh-webchat`. Mỗi lần sửa có số phiên bản mới; up lên GitHub thì Railway tự chạy bản mới.
- **Dữ liệu sản phẩm (kb.json):** 11 sản phẩm, 18 mã hàng, 44 dòng khuyến mại. File này sinh từ `tools_build/build_kb.py`. Đổi giá/quà chỉ sửa ở đó, không sửa trong persona/playbook/faq.
- **Bot Dương Sâm:** đã tách riêng. Code của bot Sâm có sẵn chế độ Dương Sâm, chỉ bật khi đặt biến `PAGE_FOCUS_PRODUCT=duong_sam`.

## 2. Các mốc chính
| Giai đoạn | Nội dung |
|---|---|
| 23/09–13/10 (v0.1.8–0.1.15) | Tách từ bot Bình Vị, viết bộ não 11 sản phẩm. Thêm Gemini. Sản phẩm trọng tâm theo bài viết/quảng cáo. Nhịp nhắc nhớ 30 phút / +4 giờ / +12 giờ. Đẩy đơn sang Nhanh. Giá chỉ đặt một chỗ. |
| 14–17/10 (v0.1.16–0.1.33) | Duyệt bộ não. Không xưng dược sĩ. Bảng an toàn từng sản phẩm. Khách cũ có bảng quà riêng. Giờ làm việc 8h–21h. Mở lại ca cho bot. Gọi đúng tên khách. Chặn nói lặp. Nối Pancake chạy thật. |
| 19–21/10 (v0.1.35–0.1.49) | Bảng khuyến mại Dương Sâm. Trả lời bình luận (4 loại). Lưới tự sửa quà combo. Ảnh Nước Hồng sâm mới. Không xin lại số điện thoại. |
| 22–23/10 (v0.1.50–0.1.59) | Lưới tự sửa giá. Tổng đơn và phí ship đúng. Chào đúng buổi. Không mời rượu khi khách không hỏi. Không bán chịu. Cửa hàng mở 8h–21h. Không nhắc nhớ khi khách đã chào kết hoặc đã từ chối. Thẻ B4. Tin khách nổi chưa đọc. Bỏ câu "toàn bộ sâm trồng ở Sìn Hồ". Chỉ nói theo tài liệu. |
| 23/10 (v0.1.60–0.1.62) | Nhớ số điện thoại khách (kể cả tin cũ trên Pancake). Đơn đã chốt mà khách hỏi giao hàng → chuyển nhân viên. Chặn câu "tẩm gừng". Tự gắn ảnh sản phẩm ở lượt trả lời đầu. |
| 24/10 (v0.1.63–0.1.67) | Khách tự xưng cô/bác thì bot xưng cháu. Không lọt mã che "[ĐIACHI_n]". Không chào lại giữa hội thoại. Đoán giới tính từ hội thoại. Không đoán tên sản phẩm từ ảnh khách gửi. Không chê hàng hãng khác là giả. Không đáp lại sticker/lời chúc sau khi đã chào kết. |
| 25/10 (v0.1.68–0.1.77) | Khách nói dạng "viên" thì hỏi lại tên sản phẩm. Chặn ghi chú phân tích của AI lọt ra cho khách. Thêm đoạn "phù hợp với người ngủ kém…" (3 cách). 4 kiểu trình bày bảng combo + 6 cách dẫn dắt chốt. Xưng hô là bước cuối của mọi tin. Không gọi trống tên khách. Lấy giới tính từ Pancake. **Bot đọc toàn bộ hội thoại trên Pancake.** Trả lời bình luận gọn dòng. Sửa các lỗi tìm ra khi rà soát. |

## 3. Rà soát 25/10
Một lượt kiểm tra độc lập đã chạy thử toàn bộ các thay đổi từ v0.1.60 đến v0.1.76 bằng câu chữ tiếng Việt thật, tìm ra 13 lỗi. Tất cả đã sửa trong v0.1.77.

| # | Lỗi | Đã sửa |
|---|---|---|
| 1 | "chị gái tôi…", "Anh Hùng giới thiệu…", "Chị lên đơn cho em" bị hiểu là khách tự xưng → gọi sai anh/chị cả hội thoại | Chỉ tính khi khách nói về chính mình ("anh muốn mua", "cho chị hỏi", "sâm anh đang uống", "vợ tôi/chồng tôi") |
| 2 | "mua cho bà xem", "Ông bị tiểu đường…" bị hiểu là khách xưng bà/ông → bot xưng cháu | Chỉ tính "cho cô hỏi / bác muốn mua / chú lấy…" |
| 3 | Khách tên Hồng / An: "Hồng sâm" thành "Chị Hồng sâm", "An toàn" thành "Anh An toàn" | Chỉ thêm danh xưng khi tên đứng ở vị trí gọi (trước dấu câu, "ơi", "cho em", "nhé"…) |
| 4 | Chữ "không" bị đọc thành "ông" → bot tưởng khách mua cho bố mẹ, đoạn giới thiệu bị cắt cụt | So khớp nguyên từ |
| 5 | Sau lời chào kết, khách gửi ảnh hoặc "ok" khi đang chốt đơn bị bỏ qua | Ảnh không chữ luôn được xử lý. Đang chốt đơn thì "ok" là đồng ý. Tin bỏ qua vẫn để chưa đọc |
| 6 | "tiểu đường" bị coi là địa chỉ → bot tưởng khách đã gửi đủ thông tin | Bỏ "tiểu đường / đường huyết". Cần số nhà hoặc ≥ 2 từ địa chỉ |
| 7 | Bỏ câu "chúc bố mẹ" có thể làm tin trống hoặc cụt chữ | Chạy trước bước kiểm tra tin rỗng, giữ xuống dòng |
| 8 | "giao cho chị gái tôi 09…" → bot gọi "chị Tôi" | Có danh sách chữ không phải tên |
| 9 | "Cho anh hỏi giá" bị hiểu là xin ảnh (anh = ảnh) | Chỉ tính "gửi … xem / gửi ảnh / xin hình". Không chèn ảnh vào tin về đơn hàng, giao hàng, chuyển nhân viên, an toàn |
| 10 | Lưới chặn ghi chú xóa nhầm "Bước 1:" và làm xáo xuống dòng | Chỉ gỡ nhãn "Ý 1 / Phương án 1"; không đụng định dạng khi không bỏ gì |
| 11 | Bỏ câu chào giữa hội thoại xóa lẹm nội dung ("Dạ em chào chị, chị đợi em xíu ạ") | Chỉ bỏ câu chào đứng riêng |
| 12 | Câu chốt "gợi ý combo 3 tháng" không bao giờ được dùng | Sửa cách đọc câu mẫu |
| 13 | Địa chỉ không có số nhà ("Hà Đông, Hà Nội") bị mở che khi gửi AI | Giữ che khi có từ 2 tên riêng trở lên |

Kiểm tra sau sửa:
- 17/17 ca kiểm tra tự động đạt.
- Các đoạn thử của lượt rà soát chạy lại đều cho kết quả đúng.

## 4. Còn để ý
1. **Đổi khóa sau sự cố Railway (chưa làm):** đổi khóa Gemini trước, sau đó token Pancake, ADMIN_KEY, SECRET_PATH, đường dẫn webhook.
2. **Chưa kiểm chứng được trên dữ liệu thật** (phải test sau khi up, xem nhật ký trang quản trị):
   - "bot đọc N tin từ Pancake": tính năng đọc toàn bộ hội thoại.
   - "giới tính từ hội thoại Pancake" / "hồ sơ từ API — gender=…": lấy giới tính.
   - "lấy được SĐT cũ của khách từ Pancake": nhớ số điện thoại cũ.
3. **Chi phí:** bot đọc tối đa 60 tin mỗi lượt nên tốn Gemini hơn trước. Tắt bằng `PANCAKE_FULL_HISTORY=0`, giảm số tin bằng `PANCAKE_FULL_HISTORY_MAX`.
4. **Bot không tự nhìn được ảnh:** AI vẫn có thể đoán sai tên sản phẩm trong ảnh khách gửi. Code đã chặn câu chê hàng giả và luật đã bắt hỏi lại khi không đọc rõ tên, nhưng không chặn được hết.
5. **File `pii.py` (che số điện thoại/địa chỉ) chỉ có trên GitHub,** chưa được rà soát.
6. **Facebook chỉ cho page nhắn trong 24 giờ** kể từ tin cuối của khách, nên nhắc nhớ bước 4 giữ ở mốc ~16,5 giờ.
