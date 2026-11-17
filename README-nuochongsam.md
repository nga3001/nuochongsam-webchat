# Bot Nước Hồng sâm Thái Minh — v0.5.16 (17/11/2026)

## v0.5.16 — báo giá chỉ nêu 1 quà (chị Nga 17/11)
- Bảng quà Hồng sâm lát / Dương Sâm có nhiều phương án: build_kb tách `gift` = phương án ĐẦU của bảng (quà mặc định) và `gift_options` = các phương án đổi.
- Báo giá, tổng hợp đơn chỉ ghi 1 quà. Khách xin đổi / hỏi quà khác → bot mới đưa các phương án; khách chọn → build_order với `items[].gift_choice`
  (chỉ nhận đúng phương án trong bảng; quà ngoài bảng → giữ quà mặc định). build_order trả `gift_options_if_customer_asks`.
- Lưới quà giữ phương án khách đã xin đổi (khách có nói đổi / thay / chọn / quà khác).
- Test: test_nhs 43/43 (ca 42 viết lại), test_sam_12ca 17/17 (ca 10, 11, 12 theo quà mặc định mới), test_potential_nhs 10/10.


## v0.5.15 — thẻ "KH tiềm năng", CTKM mới Hồng sâm lát + Dương Sâm, đọc hết tin dài (17/11)
- Khách CHƯA để SĐT, CHƯA chốt đơn, có 1 trong 5 dấu hiệu → gắn thẻ **KH tiềm năng** (1 lần / hội thoại), bot vẫn chat bình thường:
  1. Lưỡng lự: "để chị suy nghĩ đã", "hỏi ý kiến chồng", "để sau", "cuối tháng / lương về chị lấy".
  2. Hỏi sâu sau khi đã báo giá: combo tặng gì, ship mấy ngày, thanh toán thế nào, cách dùng sao.
  3. Chê đắt nhưng vẫn hỏi tiếp ("đắt quá" rồi "có bớt không em?").
  4. Nhắn qua lại với bot từ 3 lượt trong cùng một ngày (giờ VN).
  5. Nói muốn mua ("lấy 2 hộp"), bot xin SĐT + địa chỉ, khách im → kiểm lúc nhịp nhắc nhớ 1.
- Tên thẻ đổi được bằng biến PANCAKE_TAG_POTENTIAL (mặc định "KH tiềm năng" — thẻ đã có sẵn trên Pancake).
- CTKM mới 17/11 (chị Nga) — Hồng sâm lát (HSVN-M04 khách mới, HSVN-C06 khách cũ; hộp 14 gói và 50 gói) và Dương Sâm Linh Đan (DSLĐ-M03 khách mới, DSLĐ-C06 khách cũ) nạp vào programs (build_kb.py). Bot Nước Hồng sâm CHỈ nói khi khách hỏi đúng sản phẩm đó (NHS_BLOCK (p)). Quà có 'hoặc' = khách chọn 1, ghi '(chọn 1)'. Combo Hồng sâm lát đổi tên 'Combo N hộp Hồng sâm lát' (2/3/5/6 hộp), bỏ 'combo 1/2/3 tháng'. Lát 1 hộp có quà (khách mới, 1 lần duy nhất), không còn điều kiện chê đắt. Mời lên gói lát: 1 → 2 hộp, 2 → 3 hộp. Dương Sâm khách cũ: mốc 4/7/10/15 theo C06; 1/2/3/6/9 theo bảng khách mới (cách chốt 19/10). Lưới quà `_fix_nhs_packages` nhận câu nói về Hồng sâm lát / Dương Sâm và sửa theo bảng của đúng sản phẩm đó.
- Đọc hết tin dài (chị Nga 17/11): `_is_long_msg`, `_asks_price` — tin dài chỉ coi là hỏi giá khi có câu hỏi giá rõ ('bao nhiêu', 'giá thế nào', 'báo giá' hoặc câu có chữ giá kèm dấu hỏi); không chèn câu giá, không thay câu trả lời bằng bảng ưu đãi khi khách vừa lưỡng lự vừa hỏi ý khác; không tự chèn thông điệp Hội nghị chỉ vì tin dài nhắc 'sâm Hàn'. Lời dặn NHS_BLOCK (o): đọc toàn bộ, trả lời đủ từng ý theo thứ tự.
- Test: tests/test_potential_nhs.py 10/10; test_nhs 43/43; test_sam_12ca 17/17 (ca 10 cập nhật theo bảng lát mới).


## v0.5.14 — quà đúng bảng + thanh toán (ca thật Dương Thị Thìn, Thang Huynh 16/11)
- AI kể quà sai ("Mua 4 hộp … tặng 2 hộp Trà sâm", nhầm bảng Hồng sâm lát). Bảng quà Nước Hồng sâm nay nằm thẳng trong lời dặn (NHS_BLOCK (m), sinh từ kb.json).
- Lưới `_fix_nhs_packages` bắt MỌI kiểu viết "N hộp … tặng …" (gạch đầu dòng, câu văn), sửa quà theo mốc thấp hơn gần nhất; bỏ qua dòng hộp 10 túi / Hồng sâm lát / khách cũ. "Hộp 2 hộp" → "Combo 2 hộp"; đoạn mở đầu chữ thường được viết hoa.
- Thanh toán (chị Nga duyệt 16/11): câu chuẩn `payment` — nhận hàng kiểm tra rồi mới thanh toán, hoặc chuyển khoản trước qua tài khoản công ty (nhận hàng 0 đồng). Lưới `_fix_payment_nhs` bỏ câu tự bịa ("chưa hỗ trợ quẹt thẻ", "chỉ nhận tiền mặt"). Khách chọn chuyển khoản trước → hẹn gửi số tài khoản khi gọi xác nhận + chuyển nhân viên.
- Chốt 16/11: Nước Hồng sâm thấy thay đổi "sau khoảng 1 hộp đầu (khoảng 20 ngày)" (thay "2 hộp đầu") ở câu khuyên báo giá, faq, persona, playbook; upsell_nhs bỏ câu đệm (6). Lưới `_fix_2hop_nhs` sửa câu AI tự viết "2 hộp đầu" (trừ câu nói về Hồng sâm lát). Liều giữ 1–2 túi/ngày.
- Giá (chị Nga 16/11: "hộp 20 túi luôn 620k, có lúc bot nói sai"): `_fix_nhs_prices` viết lại, xét TỪNG CÂU thay vì cả dòng. Trước đây cả dòng có chữ "mỗi ngày" / "miễn phí vận chuyển" bị bỏ qua → câu dẫn giá sai lọt; dòng "2 hộp: 1.200.000đ" không có chữ combo/mua bị ép về giá 1 hộp. Nay: số tiền sau "N hộp" / "x N" → N × giá hộp; trước "/hộp", "một hộp" → giá 1 hộp; đọc được "1tr2", "2tr48", "1 triệu 240"; không đụng tổng tiền, phí ship, trị giá quà, sản phẩm khác. Tin tổng hợp đơn của build_order giữ nguyên (đã kiểm 3 đơn mẫu).
- Tốc độ (theo bot lát v0.1.134): gom tin 10 giây cả tin đầu (trước 50s tin đầu / 30s tin sau); chế độ POLL hỏi Pancake 6 giây/lần (trước 25s) và tự trừ nửa chu kỳ hỏi khỏi thời gian chờ → tổng ≈ 10 giây + thời gian AI soạn. Railway: XOÁ PANCAKE_BATCH_SECONDS, PANCAKE_BATCH_FIRST_SECONDS, PANCAKE_POLL_SECONDS nếu còn (biến cũ đè mặc định mới).
- Test: test_nhs 41/41, test_sam_12ca 17/17, lát không đổi.


## v0.5.13 — thông điệp Hội nghị Quốc tế về Sâm (chị Nga duyệt 05/11)
- Câu chuẩn `symposium_trust` (nguyên văn đã duyệt; "cô chú" đổi theo cách gọi khách). Dùng cho Hồng sâm lát và Nước Hồng sâm.
- Luôn kèm đúng 2 ảnh: `static/img/hoi-nghi-sam-han-quoc.jpg` (toàn cảnh hội nghị) + `static/img/ts-thai-bao-cao-han-quoc.jpg` (Tiến sĩ Thái báo cáo, slide có sản phẩm). Tối đa 1 lần/hội thoại.
- Lưới code `_symposium_net`: AI tự diễn đạt → thay bằng câu chuẩn + gắn 2 ảnh; khách hỏi uy tín / chất lượng / nguồn gốc / hàng thật giả / so với sâm Hàn mà AI chưa nói → tự thêm; đã gửi rồi → bỏ lặp; ảnh hội nghị đứng một mình → bỏ. Không chèn vào tin tổng hợp đơn, tin chuyển người, tin an toàn.
- Prompt: NHS_BLOCK (l) + (d) cho phép 2 ảnh này; playbook thêm mục.
- Test: test_nhs 37/37 (thêm test_37_hoi_nghi_sam), test_sam_12ca 17/17, lát diff không đổi.


## v0.5.12 — khách lưỡng lự (ca thật Nguyễn Tâm 02/11)
- Khách hỏi giá, bot báo giá 1 hộp + hỏi sức khỏe, khách đáp "để em xem đã" → bot chỉ xin SĐT, khách chưa từng thấy ưu đãi combo. Nay: khách lưỡng lự ("để em xem / suy nghĩ / tham khảo / để sau") mà chưa được gửi bảng combo → bot gửi bảng combo 2/4/6 hộp + miễn ship + nhận hàng kiểm tra rồi mới trả tiền + xin SĐT nhẹ. Đã thấy combo rồi thì giữ câu của AI.
- Bot Nước Hồng sâm không nói "liệu trình" ("tìm hiểu liệu trình dùng" → "tìm hiểu cách dùng").

## v0.5.11 — khách để SĐT: nhân viên phải biết ngay để gọi ra (chị Nga: việc quan trọng nhất)
- Khách gửi SĐT hợp lệ (10 số) ở bất kỳ tin nào → bot gắn thẻ **Có SĐT** + giao nhân viên trực + đánh dấu chưa đọc NGAY; bot vẫn chat tiếp với khách. Mỗi số báo 1 lần / hội thoại (khách gửi số khác thì báo lại).
- Trước đây: khách để SĐT giữa chừng mà không chốt đơn → chỉ khi khách im sau nhắc nhớ mới chuyển người; khách chào cảm ơn rồi thôi thì có thể không ai gọi.
- Cần tạo thẻ tên đúng "Có SĐT" trên Pancake (hoặc đặt PANCAKE_TAG_PHONE = tên thẻ muốn dùng).

## v0.5.10 — rà lại xưng hô (ca thật Mây Bay: "Cháu chúc chị…")
- Khách không tự xưng bác/cô/chú/ông/bà → bot LUÔN xưng "em" (code đổi "Cháu chúc…", "cho cháu xin…", "bên cháu" → "em"); không đụng "cháu nhà chị", "cháu bé".
- Bot không gọi khách là "bạn" (đổi thành anh/chị rồi theo hồ sơ khách).
- Câu chuẩn code chèn khi khách xác nhận đơn cũng đổi xưng hô theo khách.
- Rà 13 tình huống xưng hô qua toàn bộ code (không rõ giới tính; hồ sơ Pancake chị Hoa / anh Tuấn; khách tự xưng chị, anh, bác, cô; "Cho cô hỏi giá"; mua cho mẹ; vợ tôi; khách tự xưng mình; khách gọi bot là chị; cháu nhà chị) — đều đúng.

## v0.5.9 — trả lời bình luận khi chạy chế độ POLL
- Bot Nước Hồng sâm nhận tin bằng chế độ tự hỏi Pancake (PANCAKE_POLL=1, giống bot Dương Sâm). Chế độ này trước đây CHỈ xét hội thoại tin nhắn (INBOX), bình luận không bao giờ tới bot (bình luận chỉ đi qua webhook) → bình luận "Ib" không được trả lời. Nay xét cả hội thoại bình luận khi PANCAKE_COMMENT=1. Lần đầu chạy thật cần thử bằng bình luận có #tm (PANCAKE_COMMENT_TEST=1) trước khi mở cho mọi bình luận.

## v0.5.8 — chạy thật trên page (30/10), chị Nga góp ý
- Khách chê đắt / chưa đủ tiền / không có tiền (kể cả "đắt quá thôi") → thuyết phục ÍT NHẤT 2 LẦN mua hộp 20 túi / combo; khách vẫn từ chối mới mời hộp nhỏ 10 túi. Code chặn lời mời 10 túi đến sớm (bỏ câu + ảnh hộp 10 túi, thay bằng lần thuyết phục tiếp theo). Khách tự hỏi hộp nhỏ / xin dùng thử thì vẫn giới thiệu 10 túi.
- Thành ngữ phải viết đủ chữ: "tiền nào nấy" → "tiền nào của nấy". Tên viện sai "Viện Dược liệu" → "Viện Nghiên cứu Sâm và Dược liệu Việt Nam (VIGH)". Không gán công dụng cho quà ("Trà sâm 1700 giúp bác dễ ngủ" → bỏ phần công dụng).
- SĐT khách gửi sai (thừa / thiếu số) → luôn trả lời bằng câu chuẩn nói rõ số đang có bao nhiêu chữ số (AI từng bịa lý do "số hiển thị dạng bảo mật" vì SĐT được che trước khi gửi AI).
- Nói về công ty phải nêu rõ tên ("từ công ty" → "từ Sâm Thái Minh (Công ty Cổ phần Sâm và Dược liệu quý Thái Minh, thuộc hệ thống Dược phẩm Thái Minh)"). Khách hỏi nhà thuốc / mua ở đâu → luôn kèm link https://samthaiminh.com/diem-ban.
- Khách xác nhận đơn ("ok", "oki", like) hoặc im 5 phút sau tin tổng hợp đơn → bot KHÔNG gửi lại tổng hợp đơn lần 2 (thay bằng câu chuẩn "bên em sẽ gọi điện lại để xác nhận đơn") và LUÔN gắn thẻ "Bot chốt đơn" (ca thật anh Văn Mạnh Phí 30/10: lặp xác nhận + không gắn thẻ).
- Trả lời bình luận: tin nhắn riêng theo combo 2/4/6 hộp, không nói "liệu trình / combo theo tháng".
- Khuyến nghị: đặt DEFAULT_MODEL=gemini (Gemini 3.8 Flash), FALLBACK_MODEL=gemini_lite — Flash-Lite viết tiếng Việt kém tự nhiên, hay bỏ chữ.
- Ca thử tự động: 33/33 (bot Nước Hồng sâm), 17/17 (bot lát).

## v0.5.7 — bot dừng giữa chừng khi chốt đơn (chat thử chị Nga)
- Khách gửi SĐT sai → bot hỏi lại → khách gửi lại SĐT đúng (chỉ số điện thoại) → AI viết ghi chú nội bộ "Sản phẩm chọn: hsmo-tui-10 …" rồi dừng. Nay: (1) mã sản phẩm nội bộ (hsmo-…, hsvn-…) và nhãn "Sản phẩm chọn:" bị chặn, không tới khách; (2) code ghép SĐT mới với địa chỉ ở tin trước → coi như đủ thông tin → bắt gọi công cụ lên đơn và gửi tin tổng hợp đơn.
- "chị Nga, 0976…" ở đầu tin → nhận là khách xưng chị (trước đây bot vẫn gọi "anh/chị").

## v0.5.6 — rà soát tổng thể (luật, giá, xưng hô, lộ ghi chú)
- **Luật:** rà 25 chỗ luật chung (viết cho bot lát) có thể làm bot Nước Hồng sâm nói sai ("liệu trình 3 tháng", "combo 1 tháng", upsell_double, đổi sang sản phẩm khác khi chê đắt / chưa đủ tiền, ảnh Hồng sâm lát khi mua cho bố mẹ…). NHS_BLOCK nay ghi đè rõ từng luật (a)–(j). Sửa 3 chỗ mâu thuẫn trong persona / playbook (giá 1 hộp, thứ tự mời lên gói, nhịp 2).
- **Giá:** thêm lưới giá riêng Nước Hồng sâm — dòng combo / mua N hộp mọi kiểu trình bày luôn = N × 620.000đ; câu giá không ghi quy cách hoặc viết "600k" → đúng bảng (20 túi 620.000đ, 10 túi 330.000đ, chai 550.000đ). Không đụng tổng đơn, phí ship, giá sản phẩm khác (đã có lưới riêng).
- **Xưng hô:** khách viết "chị hay mệt…", "anh dạo này ngủ kém…" → gọi chị / anh; "bác … uống được không cháu", "cô … con" → gọi bác / cô, xưng cháu.
- **Lộ ghi chú:** thêm chặn nhãn vai ("KHÁCH: … / TRẢ LỜI: …"), câu nói về "lượt này / hướng dẫn hệ thống / kịch bản", dòng ghi chú nằm trong ngoặc. Ảnh Hồng sâm lát / Long Sâm / Dương Sâm bị bỏ khi khách không hỏi.
- Chị Nga chốt 29/10: (1) mua 1 hộp 20 túi + 1 hộp 10 túi → VẪN tính phí ship (miễn ship khi từ 2 hộp cùng loại 20 túi); (2) giữ câu FAQ đã duyệt có chữ "giúp ăn ngon, ngủ ngon".
- Ca thử tự động: 30/30 (bot Nước Hồng sâm), 17/17 (bot lát); đầu ra bot lát giống hệt bản gốc.

## v0.5.5 — đơn nhiều sản phẩm
- Khách mua 2 sản phẩm khác nhau (vd 2 hộp Nước Hồng sâm + 2 hộp Hồng sâm lát) → 1 tin tổng hợp đơn, mỗi món 1 dòng: số lượng, thành tiền, quà riêng của món đó; tổng tiền và phí ship tính cho cả đơn. Đơn 1 món giữ mẫu cũ.
- AI tự viết tin tổng hợp đơn mà không gọi công cụ lên đơn (lỗi gặp khi chat thử bằng Gemini Flash-Lite) → code bắt gọi công cụ, gửi đúng bản tổng hợp của công cụ (đủ món, đúng quà, đúng tổng, kiểm tra SĐT / địa chỉ).

## v0.5.4 — SĐT sai thì hỏi lại
Chị Nga chat thử gửi "009876862776" (12 số) mà bot vẫn gửi xác nhận đơn. Nay code kiểm tra dãy số khách gửi: không đủ 10 số bắt đầu bằng 0 (hoặc +84) → bỏ tin xác nhận, hỏi lại số điện thoại (nói rõ số đó đang có bao nhiêu chữ số). Lỗi này dùng chung code nên cũng có ở bot Hồng sâm lát.

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
