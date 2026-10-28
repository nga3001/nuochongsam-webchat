---
title: "Chatbot Bình Vị Thái Minh — Nhật ký thay đổi từ v0.1 đến v1.0"
subtitle: "18/08/2026 → 03/09/2026 · 17 ngày · 45 bản phát hành"
---

# Cách đọc

Mỗi bản ghi: ngày giờ (giờ Việt Nam), tên bản, **vì sao làm** (sự cố / phản ánh / quyết định), **làm gì**, và hệ quả vận hành nếu có. Số phiên bản v0.5.x nhảy cóc ở vài chỗ là do hai phiên làm việc song song; một commit ghi nhầm "v0.5.37" hai lần (30/08 và 01/09) — bản nhìn ảnh 01/09 được gọi lại là v0.5.38 trong tài liệu này. Nguồn: `git log` repo `binhvi-webchat` + biên bản dự án.

# Giai đoạn 1 — Web chat test nội bộ (18–22/08)

## v0.1 — 18/08/2026
Bản đầu tiên, kế thừa kiến trúc não KingsUp (LLM lo hội thoại, tool lo fact, một file JSON là nguồn chân lý). FastAPI + Claude tool-use với 4 tool `kb_lookup`, `compliance_check`, `recommend`, `build_order`; SQLite lưu hội thoại/tin/feedback; giao diện chat kiểu Messenger `/c/{secret}` với 👍👎; trang admin `/a/{key}` xem hội thoại, xuất Excel, tải/cập nhật KB không cần code; demo mode khi thiếu API key. KB là bản tạm dựng từ thông tin công khai.

## v0.2 — 20/08/2026
Não dựng lại từ ba nguồn: tài liệu chuẩn nhãn hàng "Tài liệu Bình Vị.docx", 51 hội thoại thật của nhân viên page Thảo Dược Cho Dạ Dày Khỏe, và cơ chế bot Meta Sahemul. KB chính thức (liều 2 lần × 2–3 viên trước ăn 30 phút, cách thuốc khác 1 giờ – sắt 2 giờ, trẻ từ 2 tuổi, ngừng 2–4 tuần trước test HP, tá dược, nghiên cứu ĐH Y HN – Quân Y 103). Chương trình khách mới vs đơn tái. Safety mở rộng (lactose, trẻ < 2, ADR nặng BLOCK; HP dương tính, bệnh nền, ADR nhẹ, trẻ 2–11 CAUTION). Slot-filling đơn hàng. Strip markdown ở tầng code. Giọng điệu theo nhân viên thật, hiểu tiếng Việt không dấu, câu bản lề "từng dùng Bình Vị chưa?".

## v0.3 — 20/08/2026
Trang chat tách 2 cửa sổ: khung chat + "Trung tâm huấn luyện chatbot AI Thái Minh" (chọn model, tên tester, ghi chú, form góp ý). Góp ý lưu DB có chống spam, admin duyệt rồi mới sửa KB. **Trả lời như người thật**: tách một câu trả lời thành nhiều tin ngắn kèm hiệu ứng đang gõ, tối đa 4 tin, `[QR]` dính tin cuối. Admin có tab Góp ý + sheet Excel "Góp ý huấn luyện".

## Vòng test 1 — 20/08 (10 tester, 25 hội thoại, 264 tin, 43 tốt / 11 lỗi)
Báo cáo bản 1.2 và **6 quyết định của anh Na ngày 21/08**: combo 2 = 1.025.000đ (tài liệu ghi 655k là lỗi nhập liệu); chê giá không quy đổi giá/ngày, chỉ nhấn quà khách mới; gửi nguyên 5 ảnh review kèm câu "cảm nhận cá nhân"; hoàn tiền chưa có chính sách → nói thật; khách cũ/tích điểm/câu khó → xin SĐT chuyển nhân viên; điểm bán trả lời chung các chuỗi lớn + hotline.

## v0.4 — 21/08/2026 16:31 (commit đầu tiên lên GitHub)
KB theo Kịch bản bổ sung + 6 quyết định: bảng KM 3 combo khách mới, quy tắc kênh nhà thuốc, cấm chia nhỏ giá, Rule 6–9 chuyển nhân viên với cờ 📞 trên admin, bot gửi ảnh sản phẩm/đánh giá (7 ảnh trong `static/img`). Cùng ngày Railway nối GitHub: commit lên `main` là tự deploy, bỏ hẳn cách upload tar.

## v0.4.1 / v0.4.2 — 21–22/08/2026 — Sửa lỗi bot trả lời rỗng
Triệu chứng: ~40 % lượt sau khi model gọi tool (nhất là tra giá) trả về bong bóng trắng. Gốc lỗi: model nói text **kèm** khối tool_use ở vòng 1, engine cũ chỉ bóc text vòng cuối nên phần đã nói bị bỏ, vòng 2 model coi như đã trả lời → rỗng. Vá: gom text mọi vòng (`collected`), `get_history` lọc tin rỗng, `MAX_TOKENS` 2048, rescue `tool_choice=none`, `FALLBACK_TEXT`, dòng `_debug` trong tool_trace. Test 7/7 lượt có nội dung.

# Giai đoạn 2 — Nối Pancake, lên page thật, A/B test (23–26/08)

## v0.5 → v0.5.10 — 23–26/08/2026 (hướng B: bot ngồi sau Pancake)
Chuỗi bản đóng gói zip (v0.5, 0.5.1 … 0.5.10) trước khi chuyển sang push GitHub:

- **v0.5 / v0.5.1 (25/08 sáng)**: `pancake_adapter.py` nhận webhook Pancake, gửi tin `reply_inbox`, gắn thẻ, assign, unread; polling dự phòng; dedupe; gom tin 45 s; từ khoá test `#tm`; công tắc `kill/enabled/poll/test_only`; **A/B test bot vs người** chia hash customer_id, đổi tỉ lệ từ admin, đo response time và SĐT 2 nhóm, loại ca lai tạp; xưng danh dược sĩ (Rule 2c); SĐT là lưới đỡ (5g); nhiều model (Sonnet/Haiku/GPT/DeepSeek) + router `auto` + lớp che PII; SLA watcher. Tờ trình 9 điểm + 6 kịch bản anh Na duyệt 24–25/08 (nới rule chia giá 5i).
- **v0.5.2 → v0.5.5 (25/08)**: sửa dần theo dò API thật (token qua query param, rate 5 req/s/page, tag id, `_was_sent_by_bot` đối chiếu DB, `#tm` mở khoá, admin `pancake_release`).
- **v0.5.6 + v0.5.6-hub (25/08 15:00–16:00)**: phát hiện webhook Pancake **dùng chung cả gói LK398Y** → xây **hub** `route_event` + `PANCAKE_FORWARD_MAP` chuyển event page Vương Bảo sang n8n của Huyền Anh. Sự cố hai phiên cùng sửa đè nhau → hợp nhất thành v0.5.8.
- **v0.5.9 (25/08 17:00)**: hotfix `db.py`/`main.py` thiếu hàm (`pancake_bot_sent_recent`, `pancake_release`).
- **v0.5.10 (26/08 sáng)**: assign ưu tiên người trực tuyến (đọc `is_online`, cache 60 s); quà combo 2 lọ đổi thành 1 hộp Bổ gan Thái Minh + 1 hộp 20 viên (anh Na duyệt 25/08).
- 25/08: **wipe volume** `/data` theo lệnh anh Na để bắt đầu sạch cho test nội bộ (backup Excel vòng 1, vòng 2 trên máy).

## 26/08/2026 — GO-LIVE trên page thật + 8 bản trong ngày
- **v0.5.11 (10:02)**: gắn thẻ "Bot" ngay tin đầu nhóm bot để chống ca lai tạp.
- **v0.5.12 (10:28)**: gắn bù thẻ cho ca cũ bằng cờ `ab_tagged:<conv>`.
- **v0.5.13 (10:53)**: **van ngược lọc tin tự động** — tin từ page không có uid/admin_name (welcome ad, auto-reply) là `page_auto`, không tính là sale → thời gian phản hồi nhóm người trở về thật. Trade-off: sale trả lời từ FB inbox gốc không qua Pancake sẽ không bị bắt → quy tắc đội: trả lời QUA PANCAKE hoặc gắn thẻ.
- **v0.5.14 (11:10)**: **mốc đo A/B** 10:53:23 26/08 (không xoá data cũ); trang báo cáo đầy đủ `/a/{key}/ab` (2 card, tiến độ mẫu, bảng theo ngày, ca lai tạp kèm lý do); Excel `ab_export.xlsx` 3 sheet. Thông báo đội CSKH chạy thử đã gửi.
- **v0.5.15 (15:58)**: sự cố ca chị Vì Trúc — khách trả sticker 👍 sau khi bot đọc lại đơn, bot im vì tin không có chữ, mất đơn 205k. Vá: sticker = đồng ý (đưa vào não), ảnh/tệp = chuyển người 1 câu + thẻ + assign. **Engine nhịp theo đuổi 3 nhịp** (30 phút / 5 giờ / 21 giờ, có SĐT thì hết nhịp 1 + 30' là giao người gọi), công tắc `followup` bật ngay, mốc `fu_start_ts` hiện trên trang A/B. 32 case offline pass.
- **v0.5.16 (17:05)**: **khoá theo dõi `/w/{watchkey}`** cho nhân viên (chỉ báo cáo + dừng bot) và **kill switch 2 bước** ghi tên người bấm; test dừng/bật thật 97 giây không mất tin.
- **v0.5.17 (17:30)**: lỗ hổng 1 — ca người tiếp quản BẰNG THẺ vẫn đếm là ca sạch nhóm bot. Vá: thẻ chuyển người trên ca `grp=bot, state=bot_active` → `ab_contaminate`; ngoại lệ ca bot tự chuyển (`returned`) không loại; thêm cổng loại/bỏ loại tay `ab_flag`.
- **v0.5.18 + 18b (tối)**: **bảng tình trạng bot** đèn xanh/vàng/đỏ đầu trang A/B, nhật ký dịch tiếng Việt, tự làm mới 30 s; nhịp tim `hb_ts` trong `_sla_loop`. Bài học: so mốc "đã nhận tin" với mọi event `reply` kể cả skip, để không đỏ oan khi nhân viên nhảy vào giữa lúc gom tin.

## 27/08/2026
- **v0.5.19 (22:00)**: lỗ hổng 2 — ca khách gửi ảnh không chữ (Thuỷ Hoàng), nhân viên báo giá ngoài Pancake → ca vẫn nhóm bot với 0 lượt trả lời, kéo bot xuống 97,9 %. Vá: khách gửi ảnh/tệp → loại khỏi A/B **cả hai nhóm** (bot cố ý không đoán nội dung ảnh nên không có cơ hội bán).
- **v0.5.20 (22:00)**: Huyền Anh đổi n8n sang self-host sau WAF/Cloudflare → POST từ Railway 403 vì User-Agent `Python-urllib`. Vá: thêm UA trình duyệt + Accept vào `_forward`.
- **v0.5.21**: lưu SĐT thật cả 2 nhóm A/B, nới regex SĐT, trang/Excel có cột SĐT, backfill lô cũ.

## 28/08/2026 — Kế hoạch 28 việc / 4 đợt và Đợt 1
Kế hoạch `Ke-hoach-chinh-sua-bot-BinhVi-v0.5.19-v0.6.xlsx` gộp 4 nguồn (đo đơn hàng, cửa sổ Meta 7 ngày cho ads, đề xuất CSKH, so sánh bot Vương Bảo). Anh Na chốt 6/6 quyết định: nhà thuốc hỏi thăm 1 lần không giá; nhịp ads 30p/1d/3d không D+6, organic 1h/8h; chào tên chỉ khi tên FB hợp lệ, không đoán giới tính; danh sách ngoài chỉ định gửi sau; hoãn tách KB sang Sheet; hạ gom tin 45→12 s làm ngay.

- **v0.5.22 + 22b (16:29–16:45) — ĐỢT 1, 7 việc**: A1 bỏ SĐT khỏi trang A/B và `/w/` (Excel chỉ admin tải); A2 "Nothing to update!" = no-op; A3 FB #551 → thẻ "Ko gửi được", dừng nhịp, loại khỏi tử số (ca #551 spam retry 223 lần/4 giờ tự dập ngay khi bản mới lên); A4 rà log 48 h phân 3 loại; A5 gom tin 12 s + mốc; A6 nghỉ 1,5–2 s giữa các tin; A7 khách gửi trần SĐT → chuyển người ngay; 22b thêm `/api/admin/logs`.
- **v0.5.23**: bỏ bảng SĐT khỏi trang, cuộn xem ngày/ca lai tạp cũ, ghi chú tỉ lệ SĐT + cỡ mẫu; probe nhận query string + base POS.
- **v0.5.24 (D2)**: đo chốt đơn theo hội thoại, quét POS bằng api_key, nạp đơn tay.
- **v0.5.25**: **anh Na chốt bỏ chỉ số đơn** ("số liệu này không đáng tin") — 600 đơn Pancake không có sản phẩm/tiền, 8/20 đơn tự sinh cùng giây với tin đầu. Gỡ khỏi 2 card; hạ tầng đơn giữ trong code, không hiển thị. Hướng đo chốt đơn: thu SĐT → đối chiếu hệ thống bán hàng thật (có cả hoàn/huỷ).
- **v0.5.26 (19:45)**: lỗ hổng 3 — sale gõ tay **trước** khi ca vào `ab_stats` → UPDATE không chạm dòng nào, cờ loại rơi mất, ca quay lại nhóm bot với "bot không trả lời". Vá: kiểm tra `state == human_claimed` ngay sau `ab_in`. Bài học chung: mọi `ab_contaminate` chạy trước `ab_in` đều vô hiệu.

## 29/08/2026 — Phần B, Phần C, D1: 10 bản trong ngày
- **v0.5.27 (09:55) — PHẦN B**: kiểm chứng nền tảng trước (API trả `ad_ids`/`post_id`/`gender`; Pancake **không** chặn gửi sau 24 h; số liệu 96 h: nhịp 1 11 %, nhịp 2 4,8 %, nhịp 3 2,2 %). B1 nguồn ca ads/post/organic (webhook hint + quét 10 phút); B2 cửa sổ 7 ngày ads / 24 h organic; B3 nhịp ads 30p–1d–3d, organic 1h–8h; B4 im lặng 0h–7h30; B5 Ko PH theo cửa sổ thật; B8 câu nhịp mới; B9 thẻ `[PHARMACY]` + hỏi thăm 21 h 1 lần + sửa rule 5b. 34 test pass.
- **v0.5.28**: vá 4 lỗ guardrail 12 ca: Rule 3 cấm tự khẳng định tương tác thuốc kê đơn (→ mức 3); 5h ADR "tạm ngừng" + thẻ mức 4 ngay tin đầu; 5e nói "chuyển bộ phận" bắt buộc kèm thẻ; `/api/chat` trả `handoffs` + `pharmacy` để chấm tự động.
- **v0.5.29**: **sự cố khe deploy** — Railway kẹt 50 phút (incident GCP), khách đang chốt đơn nhắn đúng lúc swap container, tin nằm trong RAM mất; đèn đỏ bắt được, cứu bằng replay webhook. Vá gốc: `flush_all_batches()` + hook `shutdown` trả lời vét mọi ca đang gom khi nhận SIGTERM.
- **v0.5.30 — PHẦN C**: C2 chống lặp 2 lớp (code difflib ≥ 0,9 + rule 5k); C3 hỏi đúng một lần (5m); C4 chào tên có điều kiện `valid_fb_name` (họ Việt ở đầu); C5 giới tính thật vào prompt qua "HỒ SƠ KHÁCH" (5n). Nghiệm thu sống: hỏi giá lần 2 chỉ còn 1 câu ngắn + câu hỏi mới. 24 test pass.
- **v0.5.31**: bỏ dòng "🚫 Không gửi được" khỏi card A/B theo yêu cầu anh Na (số vẫn trong Excel).
- **v0.5.32 (11:50)**: 6 lỗi handshake TLS Railway→pages.fm trong 11 phút (không mất khách nhờ fu loop tự retry). Vá: `_api` retry 1 lần sau 2 s với lỗi mạng (không retry HTTPError, tránh gửi đôi).
- **v0.5.33 (19:50)**: CSKH phản ánh bot báo "ưu đãi chỉ dành cho khách mới" mà không hỏi khách đã dùng chưa. Truy vết: câu bản lề chỉ nằm trong ghi chú KB từ v0.4, chưa bao giờ là rule cứng → lỗi xác suất ~45 % (5/11 ca). Vá: **rule 5p** — phải biết loại khách trước khi nêu ưu đãi; khách cũ → xin SĐT + handoff mức 2; kb `need_now` chú thích. 4 ca nghiệm thu đạt.
- **v0.5.34 → v0.5.36 (20:00–21:02) — D1 TRẢ LỜI BÌNH LUẬN**: test thật cơ chế với comment "#tm cho anh xin giá nhé" (anh Na xác nhận thấy cả private reply và reply công khai) → code nhánh `handle_comment`: nhắn riêng trước, thành công thì trả lời công khai 1 câu; gieo lịch sử vào inbox mới; guards (page tự comment, không chữ, giờ im lặng, dedup, trần 30/giờ); v0.5.35 A/B 50/50 tầng comment hash theo khách; v0.5.36 comment bị FB gỡ → `cmt_gone` xám không phải lỗi. **Đại trà từ 21:02 29/08.** 15 test pass.

## 30/08/2026
- **v0.5.37 (11:35)**: đèn đỏ oan — comment "Xin giá" được D1 xử lý đúng nhưng log dưới event `messaging` không có `reply` → bảng tình trạng báo "tin nhóm BOT 21 phút chưa trả lời". Vá `_health`: loại entry `"event": "comment"` khỏi tử số; lỗi comment thật vẫn nổi đèn qua `cmt_fail`.
- Hạ tầng: **chuyển sang push GitHub bằng git thẳng từ máy anh Na** (clone ở `repo\binhvi-webchat`, PAT nhúng remote), bỏ hẳn quy trình web UI + click toạ độ (5–10 phút/lần, hay lỗi).

## 01/09/2026
- **v0.5.38 (commit ghi "v0.5.37", b8a9755) — BOT NHÌN ẢNH/STICKER**: anh Na chọn mức "nhìn để phục vụ". `_attach_urls` bóc ≤ 3 link ảnh/sticker; marker `IMG_SEE`/`STICKER_SEE`; ảnh vào Claude qua image block; **rule 5q**: sticker theo cảm xúc thật, ảnh vỏ hộp → tư vấn, hoá đơn → tích điểm, đơn thuốc/nội soi/phiếu khám → không tư vấn theo ảnh, chuyển dược sĩ; van `vision` mặc định bật. 9 test pass.
- **v0.5.39**: tệp đính kèm phân loại thoại/video/PDF, ghi nhận đúng loại + note nhân viên, vẫn chuyển người 100 % (anh Na chốt không mở tệp; chỉ ~1 tệp/ngày). Push git đầu tiên từ máy anh Na (vài giây).

## 03/09/2026 — ngày cuối trước đóng gói
- **v0.5.40 (10:38)**: ca Huệ Lê (ads) — Pancake hiện NỮ + tên chuẩn nhưng bot vẫn "anh/chị". Truy vết: webhook Pancake **thường không mang `page_customer`**; `_src_loop` 10 phút quá chậm so với 25 s bot trả lời; `_src_sync_once` bỏ qua ca ads dù thiếu gender. Vá: `_profile_fetch_once` hỏi API đúng 1 lần lúc trả lời tin đầu (cờ `prof:<conv>`, lỗi mạng thì thử lại tin sau); src_sync không bỏ qua ca ads thiếu gender.
- **v0.5.41 (10:50)**: **anh Na đổi rule tên** — gọi nguyên tên Facebook nếu giống tên Việt ("chị Huệ Lê"), không tách họ/tên; họ Việt ở đầu hoặc cuối đều nhận; tên rút gọn ca cũ tự nâng lên tên đầy đủ.
- **v0.5.42 (12:38)**: (1) **Messenger gửi được ảnh thật** — từ khi nối Pancake, thẻ `[IMG]` bị lược trước khi gửi nên bot nói "em gửi ảnh" mà không có ảnh; vá bằng `upload_contents` → `content_ids`, gửi rời chữ/ảnh (API không nhận cả hai), cache content_id, ảnh không tính vào bộ đếm reply A/B. (2) **Vá vision sticker**: Anthropic tải ảnh theo url tôn trọng robots.txt, sticker ở fbcdn bị chặn → 400 → bot im; giờ server tự tải, gửi base64, ảnh hỏng/quá 3 MB thì bỏ. (3) Đường lùi: provider lỗi khi có ảnh → thử lại không ảnh; một tấm ảnh hỏng không bao giờ làm chết cả lượt.

# v1.0 — 03/09/2026 — Đóng gói chính thức
Đóng băng tại commit `3b0613c` (= v0.5.42), tag `v1.0`, không đổi hành vi. Kèm bộ tài liệu bàn giao: danh sách chức năng, nhật ký này, hướng dẫn sử dụng cho người, hướng dẫn cho AI, hướng dẫn nhân bản sang sản phẩm khác.

# Số liệu vận hành mốc bàn giao (tham khảo)
Từ mốc đo 10:53 26/08 đến 29/08 tối: nhóm BOT 136 ca sạch, trả lời 100 %, trung vị ~1 phút, có SĐT ~9,6 %; nhóm NGƯỜI 141 ca, 97,8 %, trung vị ~8,6 phút, có SĐT ~8,5 %; 20 ca lai tạp đã loại (6 ca có SĐT). Chênh lệch SĐT nghiêng về bot nhưng cần ~1.800 ca/nhóm mới đủ căn cứ thống kê — trang A/B tự tính cỡ mẫu. Chốt đơn thật sẽ đo bằng đối chiếu sheet "SĐT" với hệ thống bán hàng.

# Bài học kỹ thuật xuyên suốt (giữ cho các bản sau)
1. Agent tool-use tự viết phải **gom text của mọi vòng**, không chỉ vòng cuối (v0.4.2).
2. Mọi lệnh loại ca A/B phải chạy **sau** khi dòng số liệu tồn tại (3 lỗ hổng v0.5.17/19/26).
3. Webhook Pancake **tối giản và dùng chung cả gói**: không tin payload có đủ trường; hub bắt buộc; kiểm chứng bằng API trước khi code (B1, B6, D1, v0.5.40).
4. Deploy là khe mất tin — luôn có hook shutdown + đèn đỏ + quy trình replay (v0.5.29).
5. Không để một thành phần phụ (ảnh, sticker, comment) làm chết lượt trả lời chính hoặc báo đỏ oan (v0.5.37, v0.5.42).
6. Đổi prompt → chạy bộ guardrail 12 ca trước khi push; lỗi xác suất (như 5p) chỉ lộ khi soi log thật nhiều ca.
7. Push xong phải verify bằng hành vi live (số dòng, toggle mới được nhận, log event mới), đừng tin màn hình deploy.
