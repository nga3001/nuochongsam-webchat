# 12 ca thử tay — bot Nước Hồng sâm (v0.4.0)

Chạy trên web chat của service đã đặt `PAGE_FOCUS_PRODUCT=hsmo_tui`. Mỗi ca mở hội thoại mới.

| # | Khách nhắn | Bot phải | Bot KHÔNG được |
|---|---|---|---|
| 1 | "Giá sao em" | Chào + báo giá Nước Hồng sâm túi: câu dẫn 620.000đ/hộp 20 túi → 3 combo 2/4/6 hộp → 1 câu chốt; kèm ảnh | Báo giá Hồng sâm lát; gọi "Combo 1 tháng" |
| 2 | "Bố tôi 72 tuổi huyết áp cao uống được không" | "Dạ bác dùng được ạ" + câu huyết áp mềm, cách thuốc 2 tiếng | Tự giới thiệu Hồng sâm lát / Long Sâm |
| 3 | "Có loại nào tốt hơn, đậm đặc hơn không em" | Giới thiệu Hồng sâm lát (hàm lượng cao, nguyên chất) + so sánh ngắn với dạng nước | Liệt kê Trà sâm, Tam Sâm Đan, Đông trùng |
| 4 | "Bên em có những sản phẩm gì" | Nước Hồng sâm trước, rồi 3 dòng: lát, Long Sâm, Dương Sâm; 1 câu hỏi nhu cầu | Liệt kê tầng 3 |
| 5 | "Có Đông trùng hạ thảo không" | Tư vấn Đông trùng đầy đủ (khách hỏi đích danh) | Từ chối hoặc lái ngay về Nước Hồng sâm |
| 6 | "Đắt quá" (2 lần) rồi "thôi" | Lần 1 giá trị, lần 2 ý khác, rồi mời hộp 10 túi 330.000đ; vẫn từ chối → xin SĐT 1 lần | Mời Trà sâm; chuyển sang sản phẩm khác |
| 7 | "Cho chị dùng thử được không" | Chưa có dùng thử; gợi ý hộp 10 túi, kiểm hàng rồi thanh toán | Hứa mẫu thử / hoàn tiền |
| 8 | "Chị bị tiểu đường, có mật ong uống được không" | Dùng được (Rg1, Rd hỗ trợ kiểm soát đường huyết); 1 túi buổi sáng trước ăn 30 phút | Chuyển sang Long Sâm |
| 9 | "Chị đang cho con bú" | Câu chuẩn cho con bú: chưa dùng sản phẩm nào; mời mua làm quà người thân | Gợi ý sản phẩm khác cho mẹ; nói "lợi sữa" |
| 10 | "Lấy 1 hộp, Lan 0912345678, 12 Lê Lợi Hà Đông Hà Nội" | Tổng hợp đơn: 620.000đ + ship 15.000đ = 635.000đ, không mời trong tin này; khách "ok" → ghi nhận + mời lên combo 2 hộp đúng 1 lần | Mời lên gói 2 lần; xin lại SĐT |
| 11 | "Chồng chị yếu sinh lý có sản phẩm nào không" | Giới thiệu Dương Sâm Linh Đan (nhu cầu NHS không đáp ứng), tế nhị | Nói Nước Hồng sâm cải thiện sinh lý |
| 12 | Khách im sau báo giá | Nhịp 3 gửi lại 3 combo Nước Hồng sâm + 1800 1120 | Gửi combo Hồng sâm lát |

## Ca thêm v0.5.0 (luồng báo giá mới)
13. **Hỏi giá lần đầu** — nhắn "nước hồng sâm giá bao nhiêu" ở 4 cuộc chat mới → khoảng 3 cuộc nhận: giá 620.000đ/hộp 20 túi + "nên dùng đều… sau khoảng 2 hộp đầu" + đoạn phù hợp + ĐÚNG 1 câu hỏi sức khỏe, chưa có bảng combo; 1 cuộc nhận bảng combo 2/4/6 hộp ngay.
14. **Trả lời câu hỏi sức khỏe** — sau ca 13 nhắn "anh hay mệt, có huyết áp" → bot nói cách dùng an toàn cho huyết áp, gửi bảng combo 2/4/6 hộp, chốt gợi ý combo 6 hộp. Không nhắc Hồng sâm lát, không gọi "combo 1 tháng".
15. **Hỏi thẳng ưu đãi** — "có combo ưu đãi gì không" → bảng combo ngay (kiểu trình bày đổi giữa các cuộc chat), giá/quà đúng bảng.
16. **Khách cũ** — "chị dùng nước hồng sâm bên em rồi, giờ mua tiếp 3 hộp" → bảng khách cũ; 3 hộp tặng 3 hộp Trà sâm 1700 (10 gói), không ghi "khách hàng mới".
