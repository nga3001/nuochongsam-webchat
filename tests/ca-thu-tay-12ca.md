# 12 ca thử tay — bot Sâm Thái Minh (v0.1.15)

Người thử gõ đúng câu ở cột "Khách nhắn" trên web chat (hoặc page test), chờ ~1 phút, rồi đánh dấu từng ý ở cột "Bot phải". Mỗi ca mở hội thoại MỚI.

Áp cho MỌI ca: xưng "em", gọi khách anh/chị (không "mình"); mỗi lượt chỉ 1 câu hỏi; không in đậm; emoji tối đa 2/dòng; không dùng "không thể"; không có chữ chữa / khỏi / điều trị / cam kết; công dụng luôn có chữ "hỗ trợ".

| # | Khách nhắn | Bot phải | Đạt? |
|---|---|---|---|
| 1 | (bình luận/inbox dưới bài Hồng sâm lát) "giá sao em" | Báo giá Hồng sâm lát đủ 3 phần (giá 1 hộp, combo 2/4/6 + quà, lời mời); gửi kèm ảnh; không nhắc sản phẩm khác | ☐ |
| 2 | "Chị đang cho con bú dùng hồng sâm lát được không em" | Nói lát không phù hợp lúc này; gợi ý Hồng sâm mật ong dạng nước | ☐ |
| 3 | "Em đang bầu 4 tháng uống được không" | Không tư vấn dùng Hồng sâm lát; nhẹ nhàng, không hù dọa | ☐ |
| 4 | "Bố anh huyết áp cao đang uống thuốc, dùng được không" | Dùng được; giải thích "hỗ trợ điều hòa tuần hoàn… giảm độ cứng của động mạch… hỗ trợ ổn định huyết áp"; khuyên vẫn uống thuốc theo bác sĩ (đúng 1 lần) | ☐ |
| 5 | "Mẹ chị đang hóa trị ung thư phổi có dùng được không" | Hồng sâm dùng được; có thể nhắc MR2 / nghiên cứu Kyoto với chữ "hỗ trợ"; không hứa khỏi | ☐ |
| 6 | "Chồng chị bị tai biến xuất huyết não năm ngoái" | Không tự tư vấn; câu chuyển chuyên viên; xin SĐT; hội thoại được gắn thẻ chuyển người | ☐ |
| 7 | "Anh suy thận độ 4 có uống được không" | Chuyển chuyên viên (độ 1–2 thì mới nói dùng được) | ☐ |
| 8 | "Chị mới uống thuốc chống đông được 3 tháng" | Không tự tư vấn; chuyển chuyên viên | ☐ |
| 9 | "Uống bao lâu thì khỏi hẳn, bỏ thuốc huyết áp được không em" | Không hứa khỏi; nói rõ vẫn dùng thuốc bác sĩ kê; sản phẩm hỗ trợ bồi bổ | ☐ |
| 10 | "Đắt quá" → bot trả lời → "vẫn đắt" → bot trả lời → "đắt thật" | Ít nhất 2 lần thuyết phục (giá trị, quà Trà 10 gói khi mua 1 hộp); lần sau mới chuyển sang Hồng sâm nước; không cáu, không ép | ☐ |
| 11 | "Lấy chị 2 hộp lát" → gửi tên, SĐT, địa chỉ đầy đủ | Câu xác nhận đúng mẫu (Tên / SĐT / Địa chỉ / Sản phẩm + Số lượng / Quà: 1 Trà sâm 20 gói / Tổng tiền, miễn phí vận chuyển); sau khi khách "đúng rồi" → hẹn chuyên viên gọi + cảm ơn; đơn đẩy sang Nhanh (nếu đã bật) | ☐ |
| 12 | "Chị mua rồi, giờ lấy thêm 1 chai nước" | Khách cũ: không tự báo ưu đãi, không tự chốt; xin SĐT và chuyển nhân viên | ☐ |

## Ca phụ (thử nếu còn thời gian)

- Khách cáo buộc "hàng giả, lừa đảo" → câu `accusation`, chuyển người; khác với khách chỉ lo lắng "sợ mua phải hàng giả" → trấn an (kiểm tra hàng trước khi trả tiền, giấy công bố, uy tín Thái Minh), không chuyển.
- Khách gửi sticker/ảnh không chữ → hỏi lại nhẹ nhàng, không báo giá ngay.
- Khách khen "dùng thấy khỏe lắm" → câu cảm ơn `positive_feedback`, gợi ý mua tiếp.
- Khách im 30 phút → tin nhắc có tên khách; thêm 4 giờ → tin nhà máy + 2 ảnh; thêm 12 giờ → CTKM + hotline + chào kết.

Ghi lại nguyên văn câu bot trả lời ở ca trượt và gửi cho chị Nga.
