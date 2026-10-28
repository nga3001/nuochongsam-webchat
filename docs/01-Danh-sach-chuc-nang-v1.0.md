---
title: "Chatbot Bình Vị Thái Minh — Danh sách chức năng bản chính thức v1.0"
subtitle: "Bàn giao 03/09/2026 · Công ty Cổ phần Dược phẩm Thái Minh"
---

# 1. Thông tin bản phát hành

| Mục | Giá trị |
|---|---|
| Tên bản | **Chatbot Bình Vị Thái Minh v1.0** (đóng gói từ v0.5.42) |
| Mã nguồn gốc | GitHub `anhhn-ship-it/binhvi-webchat`, nhánh `main`, commit `3b0613c` (03/09/2026 12:38 giờ VN), tag `v1.0` |
| Hạ tầng chạy | Railway (service "web", volume 500 MB gắn `/data`), tự build & deploy khi có commit lên `main` |
| Kênh khách hàng | Facebook Messenger + bình luận của page **Thảo Dược Cho Dạ Dày Khỏe** (page_id 103084702507557), đi qua Pancake (gói LK398Y) |
| Kênh nội bộ | Web chat test `/c/{SECRET_PATH}` · Trang admin `/a/{ADMIN_KEY}` · Trang theo dõi cho nhân viên `/w/{WATCH_KEY}` |
| Mô hình AI | Anthropic Claude (Sonnet 4.5 mặc định, Haiku 4.5 cho câu đơn giản ở chế độ auto); có sẵn cổng ChatGPT/DeepSeek để thử nghiệm, kèm lớp che PII |
| Ngôn ngữ / công nghệ | Python 3 · FastAPI · SQLite · openpyxl · Claude API tool-use; không phụ thuộc framework agent bên ngoài |
| Kích cỡ mã | ~5.900 dòng: `main.py` 1.454 · `pancake_adapter.py` 2.197 · `engine.py` 443 · `db.py` 500 · `tools_core.py` 276 · `providers.py` 246 · `router.py` 36 · `pii.py` 79 · `brain/` 683 |

Bản v1.0 **không thay đổi hành vi** so với v0.5.42 đang chạy trên page thật — đây là mốc đóng băng để bàn giao, đặt tên chính thức và làm gốc cho việc nhân bản sang sản phẩm khác. Mọi thay đổi tiếp theo sẽ đánh số v1.0.x (sửa lỗi) hoặc v1.1 (thêm chức năng).

# 2. Kiến trúc tổng thể

Hệ thống gồm bốn lớp xếp chồng, mỗi lớp là một file Python riêng để có thể sửa độc lập:

1. **Lớp kênh** (`pancake_adapter.py`, `main.py`): nhận webhook từ Pancake, phân luồng theo page (hub), gom tin, gọi não, gửi trả lời (chữ và ảnh), gắn thẻ/giao việc trên Pancake, chạy các vòng nền (nhịp theo đuổi, SLA, quét nguồn, nhịp tim).
2. **Lớp não** (`engine.py`, `providers.py`, `router.py`, `pii.py`): dựng system prompt từ `brain/`, gọi Claude theo vòng tool-use, bóc thẻ ẩn (`[HANDOFF]`, `[PHARMACY]`, `[IMG]`, `[QR]`), tách một câu trả lời thành nhiều tin nhắn ngắn.
3. **Lớp tri thức & công cụ** (`brain/kb.json`, `tools_core.py`): nguồn chân lý duy nhất về giá, quy cách, liều, chống chỉ định, chương trình khuyến mại, kịch bản đã duyệt; bốn tool để mô hình *tra* thay vì *bịa*.
4. **Lớp dữ liệu & giám sát** (`db.py`, trang admin, trang A/B): SQLite lưu hội thoại, tin, handoff, lead, nhật ký webhook, số liệu A/B, cài đặt runtime; trang báo cáo và bảng tình trạng đọc trực tiếp từ đây.

# 3. Danh sách chức năng theo nhóm

## 3.1 Não tư vấn – bán hàng (engine + brain)

| # | Chức năng | Mô tả ngắn | Có từ |
|---|---|---|---|
| A1 | Tư vấn theo tài liệu chuẩn nhãn hàng | Công dụng, thành phần, liều tấn công/duy trì, liệu trình, quy cách, tá dược, nghiên cứu, số đăng ký — tất cả lấy từ `kb.json` qua tool `kb_lookup`; cấm bịa số liệu (Rule 1) | v0.2 |
| A2 | Tuân thủ TPBVSK | Chỉ dùng từ "hỗ trợ", cấm cụm "bảo vệ niêm mạc thực quản", không chẩn đoán, không bảo bỏ thuốc bác sĩ, luôn có câu miễn trừ khi cần (Rule 2, 2b, 4) | v0.2 |
| A3 | Xưng danh "dược sĩ tư vấn của nhãn hàng" | Không tự khai là AI/trợ lý ảo; bị truy hỏi thì chuyển kịch bản dược sĩ chuyên môn + xin SĐT (Rule 2c) | v0.5.1 |
| A4 | Safety gate `compliance_check` | Bắt buộc chạy trước khi chốt đơn hoặc khi khách lộ yếu tố rủi ro: thai/cho con bú, trẻ dưới 2 tuổi, bất dung nạp lactose, ADR nặng (BLOCK); HP dương tính, bệnh nền nặng, ADR nhẹ, trẻ 2–11 (CAUTION) | v0.1, mở rộng v0.2 |
| A5 | Gợi ý gói `recommend` 3 tầng | basic / standard / premium theo nhu cầu (need_map 12 tag: trào ngược, viêm loét, ợ hơi, HP…) | v0.1 |
| A6 | Lên đơn `build_order` | Validate SĐT (10 số, đầu 0) + địa chỉ 3 phần, chỉ hỏi phần thiếu, tự áp quà tặng + phí ship theo loại khách, `ready_to_confirm` gate | v0.2 |
| A7 | Bảng ưu đãi khách mới chính thức (3 combo) | 1 lọ 80v tặng 1 hộp 20v = 655k · 1 lọ + 2 hộp tặng 1 hộp = 1.025k · 2 lọ tặng Bổ gan TM + 1 hộp 20v = 1.310k; đều freeship; cấm suy diễn quà ngoài bảng | v0.4, đổi quà 25/08 |
| A8 | Rule 5p — ưu đãi theo loại khách | Trước khi nêu quà phải biết khách mới hay đã dùng; chưa biết → giá niêm yết + câu bản lề "mình đã từng dùng Bình Vị chưa ạ?"; khách cũ → không báo ưu đãi, xin SĐT chuyển nhân viên | v0.5.33 |
| A9 | Quy tắc giá (5c, 5i) | Cấm tự chia nhỏ giá theo ngày/viên để thuyết phục; được trả lời phép tính khách hỏi (giá lẻ mỗi lọ, tổng đơn) | v0.4 / 24/08 |
| A10 | Kịch bản chê đắt, sàn TMĐT rẻ hơn, hoàn tiền, khách cũ/tích điểm, điểm bán | Theo 6 quyết định vòng test 1 và Tờ trình 9 điểm (chuỗi Long Châu/Pharmacity/An Khang + hotline 1800 6397; chưa có chính sách hoàn tiền → nói thật, nhấn COD kiểm hàng) | v0.4 |
| A11 | Kênh nhà thuốc (5b) + thẻ ẩn `[PHARMACY]` | Khách chọn mua tại nhà thuốc → câu chuẩn, không mời lại kênh online; hệ thống hẹn hỏi thăm đúng 1 lần sau ~21 giờ, không nêu giá/ưu đãi | v0.4, hỏi thăm v0.5.27 |
| A12 | Chuyển nhân viên 4 mức `[HANDOFF: lý do | SĐT | level]` (5e) | Mức 1 đơn đã chốt · 2 CSKH thường (SLA 15') · 3 dược sĩ (SLA 10') · 4 RED FLAG/ADR/khiếu nại/hàng giả (SLA 3'); thẻ ẩn, khách không thấy; quy tắc sắt: hễ nói "em chuyển bộ phận" là phải có thẻ | v0.4, siết v0.5.28 |
| A13 | Nghi ADR (5h) | Ngay tin đầu: khuyên "tạm ngừng" + thẻ mức 4; khai thác 7 trường ADR sau | v0.5.28 |
| A14 | SĐT là lưới đỡ (5g) | Không hội thoại nào kết thúc mà chưa thử xin SĐT một lần; kịch bản S1 đơn / S2 thoát / S3 chuyển | v0.5.1 |
| A15 | Gửi ảnh sản phẩm & đánh giá (5f) | Thẻ `[IMG: san-pham | vien-uong | danhgia-1..5]` → web test hiển thị ảnh; Messenger gửi **ảnh thật** qua Pancake `upload_contents` → `content_ids` (cache id, gửi rời chữ/ảnh) | v0.4 web, v0.5.42 Messenger |
| A16 | Bot **nhìn** ảnh/sticker khách gửi (5q) | Sticker hiểu đúng cảm xúc (👍 = đồng ý, buồn = hỏi han); ảnh vỏ hộp → tư vấn, không khẳng định thật/giả tuyệt đối; hoá đơn → kịch bản tích điểm; **đơn thuốc/nội soi/phiếu khám → không tư vấn theo ảnh, chuyển dược sĩ**; ảnh mờ → hỏi lại. Server tải ảnh, gửi base64 (tránh robots.txt fbcdn); ảnh hỏng → thử lại không ảnh, không bao giờ làm chết cả lượt | v0.5.38–42 |
| A17 | Tệp đính kèm không phải ảnh | Thoại/video/PDF → ghi nhận đúng loại + chuyển người 100% (anh Na chốt không mở tệp) | v0.5.39 |
| A18 | Hồ sơ khách (tên + giới tính) | Lấy `gender`, `from.name` từ webhook; thiếu thì hỏi API Pancake đúng 1 lần lúc trả lời tin đầu; chào **nguyên tên Facebook** nếu giống tên Việt ("chị Huệ Lê"), tuyệt đối không đoán giới tính từ tên (5n) | v0.5.30, sửa v0.5.40–41 |
| A19 | Chống lặp 2 lớp (5k) | Code so từng tin sắp gửi với 2 tin bot gần nhất (difflib ≥ 0.9) → bỏ tin trùng; prompt cấm mở đầu lặp | v0.5.30 |
| A20 | Hỏi đúng một lần (5m) | Mọi câu phân loại (mới/cũ, tình trạng) phải quét lại toàn hội thoại trước khi hỏi | v0.5.30 |
| A21 | Trả lời như người thật | Tách câu trả lời thành nhiều tin ngắn (≤ 4 tin/lượt), `[QR]` gợi ý nhanh dính tin cuối, strip markdown, nghỉ 1,5–2 s giữa các tin trên Messenger | v0.3, v0.5.22 |
| A22 | Không trả lời rỗng | Gom text của mọi vòng tool-use (không chỉ vòng cuối), rescue `tool_choice=none`, FALLBACK_TEXT | v0.4.2 |
| A23 | Chỉ làm một việc (Rule 6) | Từ chối lịch sự mọi yêu cầu ngoài tư vấn – bán Bình Vị (lập trình, viết văn, sản phẩm khác) | v0.1 |
| A24 | Định tuyến model `auto` | Câu giá/liều/chào hỏi → Haiku; câu bệnh nền, thai, ADR, chê giá, khiếu nại, HP… → Sonnet; câu chưa rõ → Sonnet | v0.5.1 |
| A25 | Che PII khi thử model ngoài | SĐT/địa chỉ đổi thành `[SĐT_1]`, `[ĐIACHI_1]` trước khi gửi ChatGPT/DeepSeek; khôi phục khi tool `build_order` chạy trên server | v0.5.1 |

## 3.2 Kênh Pancake / Messenger

| # | Chức năng | Mô tả ngắn | Có từ |
|---|---|---|---|
| B1 | Webhook hub dùng chung gói | Một URL `/webhook/pancake-wh-binhvi` nhận sự kiện của **mọi page trong gói LK398Y**; `PANCAKE_FORWARD_MAP` chuyển tiếp event của page Vương Bảo (110542681967611, 104977155912657) sang n8n; đếm `forward_ok/err`; gắn User-Agent trình duyệt để qua WAF | v0.5.6-hub, v0.5.20 |
| B2 | Polling dự phòng | Vòng `_poll_loop` 25 s quét hội thoại mới khi webhook rớt; dedupe theo message_id + conversation_id (RAM, TTL 1 giờ); có thể tắt từ admin | v0.5.1 |
| B3 | Gom tin 12 giây | Khách nhắn nhiều tin liên tiếp → gom một lượt trả lời; mốc đổi 45→12 s ghi trên trang A/B | v0.5.1, hạ v0.5.22 |
| B4 | Vét tin khi tắt máy | Hook `shutdown` trả lời ngay mọi ca đang gom trước khi Railway swap container → không mất tin trong khe deploy | v0.5.29 |
| B5 | Gửi tin `reply_inbox` + retry | Gửi từng tin, nghỉ giữa tin; retry 1 lần khi 429 hoặc lỗi mạng/TLS (không retry HTTPError để tránh gửi đôi) | v0.5.1, v0.5.32 |
| B6 | Thẻ Pancake tự động | Bot · Bot chốt đơn · Chuyển TV · TV chuyên môn · RED FLAG · Nhóm người · Ko gửi được · Ko PH; thẻ Bot gắn ngay tin đầu nhóm bot | v0.5.1–11, v0.5.22 |
| B7 | Giao việc ưu tiên người online | `assign` chọn trong `PANCAKE_ASSIGN_IDS` người đang online (cache 60 s), không ai online thì chia đều + log; kèm `mark_unread` | v0.5.10 |
| B8 | Van ngược — người tiếp quản | Sale gõ tay qua Pancake (có uid/admin_name) hoặc gắn thẻ "Người xử lý"/"Để NV xử lý" → bot rút khỏi ca; tin tự động của page (welcome ad, auto-reply) được lọc `page_auto`, không tính là sale | v0.5.1, v0.5.13 |
| B9 | Chế độ thử `#tm` | Hội thoại chứa từ khoá `#tm` luôn thuộc bot và miễn trừ A/B; `test_only=1` → chỉ trả lời ca `#tm` | v0.5.1 |
| B10 | FB #551 (khách chặn/không thể nhắn) | Phát hiện → thẻ "Ko gửi được", dừng nhịp, loại khỏi tử số "bot không trả lời" | v0.5.22 |
| B11 | Trần SĐT | Khách gửi tin chỉ có 1 SĐT → PHONE_ACK + thẻ Chuyển TV + assign + unread ngay, huỷ gom tin | v0.5.22 |
| B12 | "Nothing to update!" = no-op | Không ghi vào lỗi hệ thống | v0.5.22 |
| B13 | Cổng probe API Pancake cho admin | `/api/admin/pancake_probe` gọi tay bất kỳ API Pancake (method, path, qs, base POS) để tra/cứu ca | v0.5.9, v0.5.23 |

## 3.3 Nhịp theo đuổi (follow-up engine)

| # | Chức năng | Mô tả ngắn | Có từ |
|---|---|---|---|
| C1 | Nhận diện nguồn ca | `src:<conv>` = ads / post / organic từ `ad_ids`/`post_id` (webhook hint + quét API mỗi 10 phút); không hạ cấp ads | v0.5.27 |
| C2 | Cửa sổ theo nguồn | Ads: 7 ngày (chính sách Meta CTM); organic/post: 24 giờ | v0.5.27 |
| C3 | Nhịp ads 30 phút / 1 ngày / 3 ngày · organic 1 giờ / 8 giờ | Mỗi nhịp đúng 1 câu, đổi góc nội dung; câu chữ chỉnh theo số liệu 96 h (nhịp 1: 11 % phản hồi, nhịp 2: 4,8 %, nhịp 3 cũ 2,2 % → bỏ) | v0.5.15, v0.5.27 |
| C4 | Có SĐT → giao người sớm | Nhịp 1 + 30 phút ân hạn vẫn im → thẻ Chuyển TV + assign + handoff để nhân viên gọi | v0.5.15 |
| C5 | Giờ im lặng 0h00–7h30 | Không gửi nhịp/hỏi thăm trong khung này, dồn về 7h30 | v0.5.27 |
| C6 | Đóng ca "Ko PH" theo cửa sổ thật | Hết cửa sổ của nguồn mà khách im → thẻ Ko PH | v0.5.27 |
| C7 | Hỏi thăm ca nhà thuốc | Sau ~21 giờ hỏi "đã mua được hàng chưa" đúng 1 lần (quá 2 ngày bỏ); khách phản hồi → giao người; quay lại sớm → huỷ hẹn | v0.5.27 |
| C8 | Công tắc + mốc bật | `followup` bật/tắt từ admin; `fu_start_ts` hiện trên trang A/B để đọc số đúng | v0.5.15 |

## 3.4 Bình luận dưới bài đăng (D1)

| # | Chức năng | Mô tả ngắn | Có từ |
|---|---|---|---|
| D1 | Trả lời bình luận tự động | Nhắn riêng inbox (`private_replies`) tư vấn trước; thành công thì trả lời công khai 1 câu ngắn "đã nhắn riêng" (3 mẫu, không nêu giá) | v0.5.34 |
| D2 | Gieo hội thoại inbox | Lịch sử comment + tin bot ghi vào hội thoại inbox mới sinh → khách trả lời là bot tiếp quản như ca thường | v0.5.34 |
| D3 | A/B 50/50 tầng bình luận | Hash theo khách nên inbox sinh ra cùng nhóm; nhóm người nhường nhân viên (`cmt_human`) | v0.5.35 |
| D4 | Bảo vệ | Bỏ comment của chính page, không chữ, giờ im lặng, dedup, trần 30 bình luận/giờ; comment bị FB gỡ/ẩn → `cmt_gone` (không báo lỗi) | v0.5.34–36 |
| D5 | Van `comment`, `comment_test` | Bật/tắt và chế độ chỉ `#tm` từ admin | v0.5.34 |

## 3.5 A/B test bot vs người trực

| # | Chức năng | Mô tả ngắn | Có từ |
|---|---|---|---|
| E1 | Chia nhóm theo hash customer_id | Tỉ lệ `ab_percent` đổi từ admin (đang 50/50); nhóm người gắn thẻ "Nhóm người", nhân viên trực như cũ | v0.5.1 |
| E2 | Mốc đo | `ab_start_ts` (mặc định 10:53:23 26/08/2026); số liệu chỉ tính ca sau mốc, không xoá data cũ | v0.5.14 |
| E3 | Chỉ số | Số ca sạch, % bot/người trả lời, trung vị thời gian phản hồi, % có SĐT, tiến độ mẫu so với cỡ mẫu cần (`_sample_needed`) | v0.5.14 |
| E4 | Loại ca lai tạp tự động | Sale gõ tay · thẻ chuyển người trên ca bot đang active · khách gửi ảnh/tệp · FB #551 chưa từng trả lời · sale gõ trước khi ca vào số liệu — 3 lỗ hổng đã vá, ngoại lệ ca bot tự chuyển người (`returned`) không bị loại | v0.5.11–26 |
| E5 | Loại/bỏ loại tay | Bảng `ab_flag` trên trang admin (ghi tên người bấm, nhận đuôi id ≥ 6 ký tự) | v0.5.17 |
| E6 | Thu SĐT 2 nhóm | Regex SĐT trên tin khách gõ, lưu `leads`, backfill lô cũ; **đo chốt đơn = đối chiếu SĐT với hệ thống bán hàng thật** (anh Na chốt bỏ chỉ số đơn Pancake 28/08) | v0.5.21, v0.5.25 |
| E7 | Trang báo cáo `/a/{key}/ab` | 2 card tổng quan, bảng theo ngày × 2 nhóm, danh sách ca lai tạp kèm lý do, ẩn SĐT (chỉ ghi "✔ N số"), mobile-friendly | v0.5.14, v0.5.22 |
| E8 | Excel `ab_export.xlsx` (chỉ admin) | 4 sheet: Tổng quan / Theo ngày / Chi tiết từng hội thoại / SĐT (cột "Vào số liệu" tính/LOẠI) | v0.5.14–22 |

## 3.6 Giám sát, an toàn vận hành

| # | Chức năng | Mô tả ngắn | Có từ |
|---|---|---|---|
| F1 | Bảng tình trạng bot (đèn xanh/vàng/đỏ) | Đầu trang A/B, tự làm mới 30 s: nhịp tim máy chủ, sự kiện cuối, lỗi 15'/1h/24h, tin nhóm BOT chưa trả lời > 5', ca chờ người, công tắc; nhật ký 14 dòng đã dịch tiếng Việt | v0.5.18 |
| F2 | Nhịp tim `hb_ts` | `_sla_loop` ghi mỗi 60 s, mất > 180 s → đỏ | v0.5.18 |
| F3 | Kill switch 2 bước | Trên trang A/B và `/w/`, nhập tên → bấm 2 lần trong 5 s → bot dừng < 1 phút; ghi tên người bấm; bật lại được | v0.5.16 |
| F4 | Khoá theo dõi `/w/{WATCH_KEY}` | Nhân viên xem báo cáo + bấm dừng, **không** đổi được van khác, không tải Excel; khoá tự sinh lưu DB | v0.5.16 |
| F5 | SLA watcher | Handoff quá SLA theo mức → log `sla_overdue`, nhắc trên bảng tình trạng | v0.5.1 |
| F6 | Nhật ký webhook có lọc | `/api/admin/logs?hours=&event=&q=&limit=` (chỉ admin); mọi hành vi đều có event riêng (reply, fu_sent, cmt_priv, vision_in, img_sent, send_unreach, profile…) | v0.5.22b |
| F7 | Van runtime không cần deploy | `kill · enabled · poll · test_only · ab_percent · followup · comment · comment_test · vision` qua `/api/admin/pancake_toggle` | v0.5.1 → v0.5.38 |
| F8 | Quét nguồn & hồ sơ định kỳ | `_src_loop` 10 phút bù `src`/`gender`/tên cho ca đang chạy | v0.5.27, v0.5.40 |

## 3.7 Web chat test nội bộ & trang admin

| # | Chức năng | Mô tả ngắn | Có từ |
|---|---|---|---|
| G1 | Khung chat kiểu Messenger `/c/{secret}` | Hiệu ứng "đang gõ", tách bong bóng, hiển thị ảnh, 👍👎 mỗi lượt, chọn model (sonnet/haiku/auto/gpt/deepseek), tên người test, ghi chú test | v0.1–0.3, v0.5.1 |
| G2 | Trung tâm huấn luyện — góp ý | Form góp ý lưu `suggestions`, chống spam (10/người/10 phút), admin duyệt rồi mới sửa KB (human-in-the-loop) | v0.3 |
| G3 | Trang admin `/a/{key}` | Thống kê, danh sách hội thoại + tin + tool_trace + dòng `_debug`, tab Góp ý, ca chuyển nhân viên (📞, đánh dấu đã xử lý), khối Pancake (trạng thái, công tắc, release ca), Excel xuất log + góp ý | v0.1–v0.5.15 |
| G4 | Sửa KB không cần code | Tải/cập nhật `kb.json` từ admin, bot dùng ngay (lưu ý: redeploy từ GitHub sẽ ghi đè — sửa lâu dài phải sửa trong repo) | v0.1 |
| G5 | `/api/chat` trả `handoffs` + `pharmacy` | Dùng cho bộ guardrail 12 ca tự động trước mỗi lần đổi prompt | v0.5.28 |
| G6 | Demo mode | Không có `ANTHROPIC_API_KEY` → bot trả lời mẫu để xem giao diện | v0.1 |

## 3.8 Bảo mật & dữ liệu

| # | Chức năng | Mô tả ngắn |
|---|---|---|
| H1 | Ba lớp khoá | `SECRET_PATH` (web test) · `ADMIN_KEY` (toàn quyền) · `WATCH_KEY` (chỉ xem + dừng); nghi lộ → đổi ENV, link cũ chết ngay |
| H2 | Không lộ SĐT trên trang web | Trang A/B và `/w/` chỉ hiện số lượng; SĐT đầy đủ chỉ trong Excel admin |
| H3 | PII không rời hệ thống khi thử model ngoài | Xem A25 |
| H4 | Token không nằm trong repo | Toàn bộ khoá qua ENV Railway; `.gitignore` chặn `.env`, `data.db*` |
| H5 | Dữ liệu bền | SQLite trên volume `/data`; wipe volume là mất hẳn — trước khi wipe phải xuất Excel |

# 4. Những gì v1.0 cố ý KHÔNG làm (đã có quyết định)

- Không mở tệp thoại/video/PDF của khách (01/09): mở ra không đổi hành động (vẫn chuyển người) mà thêm rủi ro.
- Không tư vấn theo ảnh đơn thuốc/kết quả khám (26/08, 01/09): chuyển dược sĩ.
- Không hứa hoàn tiền (chưa có chính sách), không tự báo ưu đãi cho khách cũ (Rule 7).
- Không dùng đơn Pancake làm thước đo chốt đơn (28/08): đo bằng SĐT đối chiếu hệ thống bán hàng thật.
- Không đoán giới tính từ tên (28/08); không đề nghị "đặt lịch khám" (5d).
- Không tách KB giá/quà sang Google Sheet (hoãn 28/08) — chỉ làm khi nhân sang nhãn thứ hai.

# 5. Việc còn mở sau v1.0 (chuyển sang v1.1)

| Việc | Trạng thái | Cần gì |
|---|---|---|
| C1 — danh sách triệu chứng ngoài chỉ định | Cơ chế đã có, chờ danh sách | Anh Na gửi danh sách |
| D4 — tool tra đơn cũ cho bot | Chưa làm | Cổng POS/API bán hàng thật |
| D2 — nối đơn theo hội thoại | Hạ tầng còn trong code, không hiển thị | Chỉ khi có nguồn đơn đáng tin |
| Nghiệm thu thật v0.5.40–42 | Chờ nhân viên test | 1 sticker không phải đồng ý, 1 ảnh vỏ hộp, 1 đơn thuốc, 1 tin thoại, xin ảnh sản phẩm |
| Railway trial | Còn ít ngày/credit | Lên plan trả phí |
| Tắt polling song song | Đang chạy | Sau khi webhook ổn định 1–2 ngày nữa |
