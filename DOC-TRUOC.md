> **Cập nhật v0.5.0 (28/10/2026):** gói này nay là bot Sâm Thái Minh **v0.1.107** + lớp bot Nước Hồng sâm. Các phần mục 3.2 ghi "chỉ dành cho Hồng sâm lát" đã có bản riêng cho Nước Hồng sâm (đoạn phù hợp Ⓐ/Ⓑ/Ⓒ, 8 kiểu bảng combo, 9 câu chốt, mời lên gói, nhắc nhớ nhịp 3). Luật 0 đã được khối NHS_BLOCK ghi đè. Xem README-nuochongsam.md.

# Bot Sâm Thái Minh v0.1.81: bản hoàn chỉnh (26/10/2026), dùng làm nền cho bot Nước Hồng sâm

## 1. Trong gói có gì
- **Code:** engine.py, pancake_adapter.py, tools_core.py, nhanh.py, providers.py
- **Bộ não:** brain/persona.md, playbook.md, faq.md, kb.json. File kb.json sinh từ tools_build/build_kb.py; đổi giá/quà thì sửa build_kb.py rồi chạy lại.
- **Trang web:** static/index.html (chat thử), static/admin.html (quản trị), static/img (2 ảnh Nước Hồng sâm mới nhất)
- **Kiểm tra:** tests/test_sam_12ca.py (17 ca tự động), tests/ca-thu-tay-12ca.md (ca thử tay)
- **Tài liệu:**
  - docs/tong-hop-bot-sam-thai-minh.md: tổng hợp từ đầu đến nay + kết quả rà soát
  - docs/Huong-dan-nhan-vien-care-bot-Sam-Thai-Minh.docx
  - README-samthaiminh.md: nhật ký cũ + hướng dẫn dựng Railway/Pancake

## 2. Không có trong gói (lấy từ GitHub)
`main.py`, `db.py`, `router.py`, `pii.py`, `requirements.txt` và các ảnh sản phẩm cũ trong `static/img/` chỉ có trên repo `nga3001/samthaiminh-webchat`.

Cách lấy bộ đầy đủ:
1. Up v0.1.81 lên repo Sâm (nếu chưa up).
2. Trên repo Sâm bấm **Use this template** để tạo repo mới cho bot Nước Hồng sâm.
3. Up các file đã sửa riêng cho bot Nước Hồng sâm vào repo mới.

## 3. Lưu ý khi chuyển thành bot Nước Hồng sâm
1. **Biến Railway của service mới:** đặt `PAGE_FOCUS_PRODUCT=hsmo_tui` (dạng túi) hoặc `hsmo_chai` (dạng chai). Khách hỏi chung chung sẽ được trả lời theo sản phẩm này.
2. **Phần chỉ dành cho Hồng sâm lát** (bot Nước Hồng sâm cần tự soạn phần tương ứng nếu muốn có):
   - Đoạn "phù hợp với người ngủ kém…" (3 cách Ⓐ/Ⓑ/Ⓒ).
   - 4 kiểu bảng combo và 6 câu dẫn dắt chốt: nằm ở `price_quote_hsvn` trong `tools_build/build_kb.py`. Code `_shape_lat_quote` (engine.py) chỉ chạy khi báo giá có "1.420.000đ" + bảng 3 combo Hồng sâm lát.
   - Mời lên gói khi chốt đơn: Hồng sâm lát 1 → 2, 2 → 4 hộp (`upsell_hint` trong tools_core.py `build_order`).
   - Tin nhắc nhớ nhịp 3 có bảng combo Hồng sâm lát. Với sản phẩm khác, bot dùng câu chung (`_FU3_OTHER`).
3. **Luật 0 trong engine.py** đang cho bot chủ động tư vấn 4 dòng chính (Hồng sâm lát, Nước Hồng sâm, Dương Sâm, Long Sâm). Nếu bot Nước Hồng sâm chỉ tư vấn Nước Hồng sâm thì sửa luật này và persona/playbook.
4. **Phí ship Nước Hồng sâm** (đã có trong kb): mua 1 hộp tính 15.000đ nội thành Hà Nội, 20.000đ nơi khác; từ 2 hộp miễn phí.
5. **Các phần dùng chung cho mọi sản phẩm, đã sẵn:**
   - Xưng hô và gọi tên.
   - Nhớ số điện thoại khách, đọc toàn bộ hội thoại trên Pancake.
   - Xác nhận đơn: gửi tổng hợp đơn → khách ok/like hoặc im 5 phút → ghi nhận đơn, gắn thẻ Bot chốt đơn, mời lên gói.
   - Nhắc nhớ, thẻ B4, trả lời bình luận.
   - Các lưới chặn: giá, quà, ghi chú lọt ra cho khách, "tẩm gừng", chê hàng giả…
6. **Code có sẵn chế độ Dương Sâm** (`PAGE_FOCUS_PRODUCT=duong_sam`). Không đặt biến này thì chế độ đó không chạy.
7. **Pancake:** page mới cần đủ thẻ Bot, Bot chốt đơn, Người xử lý, ADR/Khiếu nại, Ko gửi được, Ko PH, B4. Webhook chung chuyển tiếp qua `PANCAKE_FORWARD_MAP` ở service Sâm.
