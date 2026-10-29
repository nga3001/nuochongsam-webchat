# Bot Nước Hồng sâm Thái Minh — v0.5.3 (29/10/2026)

## v0.5.3 — chạy thật trên Railway (project miraculous-alignment, service "Nước Hồng Sâm")
- Lỗi chị Nga gặp khi chat thử: khách hỏi giá → bot báo 620.000đ; khách kể "mua cho mẹ bị HA cao, tiểu đường" → bot nhắc lại nguyên câu giá. Nay: đã báo giá ở lượt trước và khách không hỏi lại giá → bỏ câu giá lặp, gửi bảng combo luôn, không hỏi thêm câu sức khỏe.
- Trang chat thử / quản trị đổi tên thành "Nước Hồng Sâm", câu chào mở đầu của bot Nước Hồng sâm.

## v0.5.2 — sửa 3 lỗi phát hiện khi chạy thử 22 câu (lỗi có cả ở bot Hồng sâm lát v0.1.107, cùng code)
1. Lưới "lời chúc đúng buổi" thay "ngủ ngon hơn" (công dụng) thành "nhiều sức khỏe" khi nhắn ban ngày → nay chỉ bắt lời CHÚC ngủ ngon.
2. Lưới "không tự cho là mua cho bố mẹ" xóa mất câu "Nếu chị muốn mua làm quà bồi bổ cho bố mẹ hoặc người thân…" trong câu chuẩn cho con bú / có thai → nay giữ câu mời mua làm quà.
3. Lưới "không để hội thoại lửng lơ" chèn "Anh/chị có muốn em gửi giá…" sau tin báo không dùng được (có thai, cho con bú) hoặc tin đang xin SĐT → nay không chèn.

Dựng trên bot Sâm Thái Minh **v0.1.107** (Hồng sâm lát, bản đầy đủ 28/10). **Cùng một bộ code**, bật chế độ Nước Hồng sâm bằng 1 biến Railway. Bot Hồng sâm lát và bot Dương Sâm không đổi hành vi: 17/17 ca thử cũ vẫn đạt, và đã so từng chữ đầu ra các lưới báo giá / khai thác / quà khách cũ / thời gian dùng của chế độ lát và Dương Sâm với bản gốc v0.1.107 — giống hệt.

## 0a. v0.5.1 — khách cũ hưởng chương trình tốt nhất (chị Nga chốt 28/10)
Khách cũ muốn mua → áp CT khách cũ hoặc khách mới, lấy CT có khuyến mại tốt nhất. Bảng khách cũ của bot đã gộp sẵn (so giá trị quà: Trà sâm 1700 10 gói 120.000đ, Nước Hồng sâm hộp 20 túi 620.000đ):

| Số hộp | Quà khách cũ được nhận | Theo CT |
|---|---|---|
| 1 | Không quà, tính phí ship | — |
| 2 | 2 hộp Trà sâm 1700 (10 gói) | Khách cũ (NHS-C06) |
| 3–5 | 3 hộp Trà sâm 1700 (10 gói) | Khách cũ (4–5 hộp hai CT bằng nhau) |
| 6–9 | 5 hộp Trà sâm 1700 (10 gói) | Khách mới |
| 10–11 | 1 hộp Nước Hồng sâm túi + 3 hộp Trà sâm 1700 (10 gói) | Khách mới |
| 12 | 2 hộp Nước Hồng sâm túi + 1 hộp Trà sâm 1700 (10 gói) | Khách cũ (NHS-C06) |
| trên 12 | Quà mốc 12 + chuyển nhân viên xin thêm ưu đãi | Khách cũ |

Đơn chốt ghi rõ CT áp dụng (`program`, `nhanh_code` trong `promo_applied` của build_order) để nhân viên lên đơn đúng mã trên Nhanh. Ca thử tự động: **24/24 đạt**.

## 0. Mới ở v0.5.0 — học theo bản v0.1.107
Mọi sửa lỗi v0.1.85 → v0.1.107 của bot Hồng sâm lát (chống lộ ghi chú 4 lớp, không mất giá / không cụt tin, nhớ điều khách đã nói, không hỏi lại, nhắc nhớ mới…) đã có sẵn vì bot Nước Hồng sâm chạy chung code. Phần nào chỉ viết cho Hồng sâm lát thì em làm bản tương ứng cho Nước Hồng sâm:

| Tính năng bản lát | Bản Nước Hồng sâm |
|---|---|
| Hỏi giá lần đầu: 3/4 khách nhận giá 1 hộp + câu khuyên + 1 câu hỏi sức khỏe, 1/4 nhận combo ngay (v0.1.106) | Giống vậy: "620.000đ/hộp 20 túi…" + "Anh/chị nên dùng đều mỗi ngày, thường sau khoảng 2 hộp đầu sẽ thấy cơ thể thay đổi: ăn ngon, ngủ tốt, cơ thể khỏe khoắn, tỉnh táo ạ." + đoạn phù hợp + 1 câu hỏi sức khỏe. Khách hỏi thẳng combo / ưu đãi / vội / hỏi lại giá → gửi bảng combo luôn |
| Đoạn phù hợp Ⓐ/Ⓑ/Ⓒ (ngủ kém, ăn không ngon) | Ⓐ mệt mỏi, căng thẳng, ngủ không sâu + vị mật ong dễ uống, túi nhỏ tiện mang theo · Ⓑ bản ngắn · Ⓒ mua cho bố mẹ (không phải nhai hay sắc nấu). Không lặp đoạn đã nói |
| 8 kiểu bảng combo xoay vòng | 8 kiểu cho combo 2/4/6 hộp, giá + quà vẫn lấy từ bảng khuyến mại |
| 9 câu chốt theo tình huống | 9 câu: hỏi chọn, gợi ý combo 6 hộp (khách kể mệt / bệnh), 2 hộp hay 6 hộp, bắt đầu nhẹ, mua cho cả nhà / biếu bố mẹ, chốt nhẹ (khách vội / hỏi lại), hỏi người dùng, yên tâm nhận hàng (khách lo mua online) |
| Câu khai thác K1–K8, khơi gợi D1–D4 (v0.1.107 hỏi thẳng "anh/chị") | Bộ riêng `price_probe_nhs`, `price_discovery_nhs`. Khách trả lời → bot ghi nhận 1 câu rồi gửi bảng combo Nước Hồng sâm |
| Quà khách cũ đúng bảng (lưới v0.1.91) | Dùng bảng khách cũ Nước Hồng sâm (2 → 2 Trà sâm, 3 → 3 Trà sâm, 12 → 2 hộp Nước Hồng sâm + 1 Trà sâm); lưới quà khách mới không ép ngược lại khi đang báo khách cũ |
| Sửa số tháng dùng (v0.1.92) | 1 hộp 20 túi = 10–20 ngày. AI ghi "6 hộp dùng 6 tháng" → sửa thành "60–120 ngày" |
| Báo giá dự phòng khi lỗi (v0.1.104) | Chỉ hộp 20 túi + bảng combo, không liệt kê hộp 10 túi |

Thêm 6 ca thử tự động (tests/test_nhs.py: **23/23 đạt**).

## 1. Cách bật
Service Railway mới cho page Nước Hồng sâm, đặt biến:
```
PAGE_FOCUS_PRODUCT=hsmo_tui
```
(`hsmo_chai` nếu page bán dạng chai — nhưng dạng chai sắp ngừng, nên dùng `hsmo_tui`.)

Các bước còn lại giống DOC-TRUOC.md mục 2–3: tạo repo từ template repo Sâm, up các file trong gói này, page Pancake mới đủ thẻ Bot, Bot chốt đơn, Người xử lý, ADR/Khiếu nại, Ko gửi được, Ko PH, B4; thêm page vào `PANCAKE_FORWARD_MAP` ở service Sâm.

## 2. Bot làm gì
| Tầng | Sản phẩm | Bot nói khi nào |
|---|---|---|
| 1 — chủ lực | Nước Hồng sâm Thái Minh mật ong dạng túi | Luôn: chào, tư vấn, báo giá, chốt đơn |
| 2 — cao cấp hơn | Hồng sâm lát, Long Sâm Linh Đan, Dương Sâm Linh Đan | Chỉ khi khách chủ động hỏi sản phẩm khác / loại tốt hơn / cao cấp hơn / hỏi đích danh |
| 3 — chỉ khi hỏi | Trà sâm, Tam Sâm Đan, Đông trùng hạ thảo, Rượu sâm, Sâm tươi | Chỉ khi khách hỏi đích danh (Trà sâm vẫn nhắc khi báo quà) |

- **Chào:** "Dạ Sâm Thái Minh chào anh/chị ạ. Anh/chị đang tìm hiểu Nước Hồng sâm Thái Minh để bồi bổ cho bản thân hay mua cho người thân ạ?" + ảnh hộp 20 túi.
- **Báo giá (luồng mới v0.5.0, xem mục 0):** 620.000đ/hộp 20 túi, 1–2 túi/ngày → (đa số khách) 1 câu hỏi sức khỏe trước → 3 combo khách mới (giá, quà lấy từ kb.json):
  - Combo 2 hộp: 1.240.000đ – tặng 1 hộp Trà sâm 1700 (10 gói)
  - Combo 4 hộp: 2.480.000đ – tặng 3 hộp Trà sâm 1700 (10 gói)
  - Combo 6 hộp: 3.720.000đ – tặng 5 hộp Trà sâm 1700 (10 gói)
  - ✅ Từ 2 hộp miễn phí vận chuyển → 1 câu chốt (9 câu, chọn theo tình huống).
- **Chê đắt:** lần 1 nêu giá trị → lần 2 ý khác → mời hộp nhỏ 10 túi (330.000đ) → vẫn từ chối thì xin SĐT. Không mời Trà sâm.
- **Xin dùng thử:** chưa có chương trình, gợi ý hộp 10 túi.
- **Mời lên gói (1 lần, sau khi khách xác nhận đơn):** 1 hộp → 2; 2–3 hộp → 4; 4–5 hộp → 6.
- **Khách cũ Nước Hồng sâm** (chốt 26/10, mã Nhanh 2026/TP-TBBL.NHS-C06; 28/10: hưởng CT tốt nhất, xem mục 0a). Bot báo bảng gộp và chốt đơn luôn, không báo bảng combo khách mới.
- **Nhắc nhớ nhịp 3:** gửi lại 3 combo Nước Hồng sâm + tổng đài 1800 1120.
- **Bình luận:** báo giá theo 3 combo; không dùng quảng cáo "mua 1 hộp lát tặng trà".

Giữ nguyên từ bot Hồng sâm lát: xưng hô và gọi tên, an toàn (có thai, cho con bú, trẻ dưới 3 tuổi không dùng; tiểu đường 1 túi buổi sáng…), huyết áp nói mềm, chuyển nhân viên, xác nhận đơn, nhớ SĐT, đọc toàn bộ hội thoại Pancake, các lưới chặn.

## 2b. Sửa lỗi (v0.4.2) — đã có cả 3 sửa lỗi v0.1.82–84 của bot Hồng sâm lát + lỗi tương tự riêng Nước Hồng sâm
- **v0.1.82 → bot NHS:** khách nói "lấy 1 hộp" → đơn luôn là hộp 20 túi (620.000đ). Hộp nhỏ 10 túi chỉ khi khách nhắc "10 túi / hộp nhỏ" hoặc đồng ý lời mời hộp 10 túi; dạng chai chỉ khi khách nhắc chai. AI tự ghi "hộp 10 túi" trong tổng hợp đơn → code sửa về 20 túi và tính lại tổng tiền (lưới nhận cả dòng "Tổng thanh toán"). Vẫn giữ sửa lỗi hộp 50 gói cho Hồng sâm lát.
- **v0.1.83 → bot NHS:** "dùng thử combo 2 hộp / dùng thử hộp 10 túi" không còn bị hiểu là ung thư; "đã đầy đủ" không còn là dạ dày. Lưới chặn nhắc sản phẩm khác của bot NHS cũng chuyển sang khớp nguyên từ: tên "Nguyen Lan" không còn bị hiểu là khách hỏi "trà nguyên lá".
- **v0.1.84:** "ĐT, đt, dt, sđt" = số điện thoại, không phải Đông trùng (và không mở khóa giới thiệu Đông trùng).

Test sau khi up (bot NHS):
1. Nhắn "Mình dùng thử combo 2 hộp nhé" → bot xin tên, SĐT, địa chỉ để lên đơn.
2. Nhắn "lấy 1 hộp" kèm thông tin → tin xác nhận ghi hộp 20 túi, 620.000đ + phí ship (Hà Nội nội thành 15.000đ).
3. Nhắn "ĐT của anh 0912…" → bot hiểu là số điện thoại.

## 2c. FAQ mới (v0.4.4, chị Nga gửi và duyệt 26/10)
4 câu trong brain/nuochongsam/faq.md (nhóm 1b): thành phần nổi bật (84 saponin, MR2, tính bình), không cần pha chế (xé túi uống ngay), ngủ đủ mà dậy vẫn mệt, công dụng cho thần sắc nữ giới. Công dụng/điểm mạnh mới cũng có trong kb.json. Câu "thời điểm dùng cho mẹ (đêm dậy hút sữa)" đã BỎ — không dùng cho phụ nữ đang cho con bú; khách nói hút sữa / vắt sữa = đang cho con bú → không dùng sản phẩm nào.

## 2d. Bảng thông tin sản phẩm (v0.4.5, chị Nga gửi 26/10)
Đã đối chiếu: giá, quy cách, cách dùng, liều tiểu đường, thành phần, hotline, loại công bố KHỚP dữ liệu cũ. Đã cập nhật: công dụng (thêm nâng cao miễn dịch, an thần dễ ngủ, phòng ngừa xơ vữa động mạch…, bot vẫn mở bằng "hỗ trợ"), đối tượng dùng (thêm thận hư, chức năng sinh lý kém, chân tay lạnh, kéo dài tuổi thọ), tên khoa học. Phụ nữ cho con bú: nhãn ghi "hỏi bác sĩ" nhưng bot giữ luật chặt hơn đã chốt — KHÔNG dùng.

## 3. File đã thêm / sửa
| File | Thay đổi |
|---|---|
| `brain/nuochongsam/persona.md`, `playbook.md`, `faq.md` | **Mới** — bộ não riêng bot Nước Hồng sâm (code tự đọc khi bật chế độ) |
| `tools_build/build_kb.py` → `brain/kb.json` | Thêm câu chuẩn: `price_quote_nhs` (v0.5.0: đủ đoạn phù hợp, 8 kiểu, 9 câu chốt), `price_probe_nhs`, `price_discovery_nhs`, `price_why_nhs`, `price_objection_nhs`, `trial_request_nhs`, `product_overview_nhs`, `upgrade_premium`, `upsell_nhs`, `greeting_nhs`; `focus_policy.nhs_tiers`. Giá/quà sinh từ bảng sản phẩm + bảng khuyến mại. |
| `engine.py` | v0.5.0: `_shape_nhs_quote` (báo giá lần đầu, đoạn phù hợp, 8 kiểu bảng, 9 câu chốt), câu khai thác/khơi gợi theo sản phẩm, quà khách cũ + `returning_note` theo bảng Nước Hồng sâm, `_fix_duration_nhs`, báo giá dự phòng. Từ v0.4: `IS_NHS`, khối luật `NHS_BLOCK` (ưu tiên hơn luật chung), lưới sửa giá/quà dòng "Combo N hộp", lưới bỏ đoạn tự nhắc sản phẩm tầng 2/3 khi khách không hỏi |
| `tools_core.py` | Đọc bộ não `brain/nuochongsam/`; `recommend` luôn trả Nước Hồng sâm là sản phẩm chính; gợi ý mời lên gói Nước Hồng sâm |
| `pancake_adapter.py` | Nhắc nhớ nhịp 3 riêng; báo giá dưới bình luận theo combo 2/4/6; tắt mặc định quảng cáo "1 hộp lát tặng trà" |
| `tests/test_nhs.py` | 23 ca thử tự động (23/23 đạt) |
| `tests/ca-thu-tay-nhs.md` | **Mới** — 12 ca thử tay trên web chat |

Đổi giá/quà Nước Hồng sâm: sửa `P["hsmo_tui"]` hoặc `RULES` trong `tools_build/build_kb.py` → chạy `python3 tools_build/build_kb.py`.

## 4. Điểm em tự quyết, cần chị Nga duyệt
1. **3 combo chính là 2 / 4 / 6 hộp** (giống nhịp 2/4/6 của Hồng sâm lát). Mốc 3 hộp và 10 hộp vẫn có quà theo bảng, chỉ nói khi khách hỏi đúng số đó.
2. **Không gọi combo là "1 tháng / 2 tháng / 3 tháng"** vì 1 hộp 20 túi dùng 10–20 ngày tùy 1 hay 2 túi/ngày. Nếu chị muốn có liệu trình theo tháng (vd "Combo 1 tháng = 2 hộp"), báo em đổi.
3. **Câu kỳ vọng "sau khoảng 2 hộp đầu"** — mượn từ câu đã duyệt chung của Hồng sâm. v0.5.0 thêm: đoạn phù hợp Ⓐ/Ⓑ/Ⓒ, 8 kiểu bảng, 9 câu chốt, câu khai thác/khơi gợi Nước Hồng sâm là em soạn theo khuôn bản lát — chị duyệt câu chữ trong `price_quote_nhs`, `price_probe_nhs`, `price_discovery_nhs` (tools_build/build_kb.py).
4. **Chê đắt → hộp nhỏ 10 túi**, không chuyển sản phẩm khác.
5. **Lời chào giữ tên "Sâm Thái Minh"**. Nếu page tên khác (vd "Nước Hồng sâm Thái Minh"), báo em đổi.
6. **Câu nêu giá trị khi chê đắt** (`price_why_nhs`): 11.000mg tinh chất/10ml, MR2, VIGH, uy tín Thái Minh — đều có sẵn trong tài liệu, chỉ ghép lại.
7. ~~Bảng khách cũ~~ — đã chốt 28/10: 1 hộp không quà + phí ship; khách cũ hưởng CT tốt nhất (mục 0a).
