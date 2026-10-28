---
title: "Hướng dẫn phát triển chatbot cho sản phẩm khác của Thái Minh"
subtitle: "Nhân bản từ nền Bình Vị v1.0 — Vương Bảo, Tràng Phục Linh, Khương Thảo Đan, Bổ Gan, KingsUp… (03/09/2026)"
---

# 1. Tư tưởng: một nền, nhiều "não"

Bình Vị v1.0 được thiết kế để phần **nền** (kênh Pancake, gom tin, thẻ, A/B, nhịp theo đuổi, bảng tình trạng, kill switch, vision, gửi ảnh) dùng chung cho mọi nhãn, còn phần **não** (KB, persona, playbook, FAQ, ảnh, danh sách nhân viên trực) là của riêng từng sản phẩm. Thực tế đến v1.0 hai phần này vẫn nằm trong cùng một repo và còn vài chỗ hard-code (page_id mặc định, tên "Bình Vị" trong prompt, tên thẻ Pancake, tên file ảnh). Nhân bản nhãn thứ hai vì thế gồm hai bước: **(a) tách cấu hình nhãn ra một chỗ**, rồi **(b) điền cấu hình cho nhãn mới**. Làm (a) một lần cho tất cả nhãn về sau.

Ước lượng công sức cho nhãn thứ hai: tách cấu hình 1 ngày; dựng KB + kịch bản 2–3 ngày (phụ thuộc tài liệu nhãn); test nội bộ 2 ngày; nối Pancake + chạy `#tm` 1 ngày; A/B 2 tuần. Nhãn thứ ba trở đi bỏ được bước tách, còn ~1 tuần đến lúc go-live.

# 2. Hai mô hình triển khai — chọn trước khi bắt đầu

| | **Mô hình 1: Mỗi nhãn một service** | **Mô hình 2: Một service, nhiều nhãn (multi-tenant)** |
|---|---|---|
| Cách làm | Fork repo → đổi cấu hình → deploy service Railway riêng, DB riêng | Thêm bảng `brands`; mọi hàm nhận `brand` từ page_id; một DB, một domain |
| Ưu | Cô lập hoàn toàn: lỗi/deploy/kill switch nhãn này không chạm nhãn kia; A/B, số liệu, khoá riêng; làm được ngay với code v1.0 | Một chỗ vận hành; sửa nền 1 lần cho tất cả; rẻ hơn khi > 5 nhãn |
| Nhược | Sửa nền phải cherry-pick sang từng repo; N service Railway (~5 USD/tháng/service) | Phải tái cấu trúc adapter (2.200 dòng) — rủi ro cho bot Bình Vị đang chạy; một lỗi kéo cả cụm |
| Điểm chung bắt buộc | **Webhook Pancake là chung cả gói LK398Y** → chỉ có **một URL** nhận event của mọi page. Cần một **hub** phân luồng theo `page_id` | Hub nằm sẵn trong service |

**Khuyến nghị:** dùng **Mô hình 1** cho 2–4 nhãn đầu, với hub hiện có của Bình Vị làm cổng vào duy nhất (`PANCAKE_FORWARD_MAP` đã đang chuyển tiếp page Vương Bảo sang n8n — thêm nhãn mới chỉ là thêm một cặp `page_id=url`). Khi hub bắt đầu thành điểm nghẽn hoặc số nhãn > 5 thì cân nhắc gộp về Mô hình 2. Đây cũng là lý do anh Na hoãn tách KB sang Google Sheet: chỉ đáng làm khi có nhãn thứ hai.

# 3. Bước (a) — tách cấu hình nhãn ra khỏi code (làm một lần)

Mục tiêu: một thư mục `brand/` (hoặc file `brand.json`) chứa **mọi thứ khác nhau giữa các nhãn**; code chỉ đọc từ đó. Danh sách chỗ cần tách trong v1.0:

| Nơi hiện tại | Nội dung đang gắn với Bình Vị | Chuyển thành |
|---|---|---|
| `pancake_adapter.py` dòng 51 | `PANCAKE_PAGE_ID` mặc định 103084702507557 | ENV bắt buộc, không mặc định |
| `pancake_adapter.py` `IMG_FILES`, `static/img/` | 7 ảnh `san-pham`, `vien-uong`, `danhgia-1..5` | `brand/images.json` {id: file, mô tả} + folder ảnh nhãn; prompt 5f đọc danh sách id từ đây |
| `pancake_adapter.py` `TAG_*`, `TAG_BY_LEVEL` | Tên thẻ "Bot", "Bot chốt đơn", "Chuyển TV", "TV chuyên môn", "RED FLAG", "Nhóm người", "Ko gửi được", "Ko PH", "Người xử lý" | Giữ **cùng tên thẻ** trên mọi page (đơn giản nhất) hoặc map trong `brand.json` |
| `pancake_adapter.py` câu mẫu | `STICKER_TEXT`, `ATT_ACK`, `PHONE_ACK`, `PH_MSG`, `FU_MSG`, `CMT_PUBLIC`, `CMT_PROFILE` | `brand/messages.json`; ENV vẫn ghi đè được |
| `engine.py` system prompt | Tên nhãn "Bình Vị Thái Minh", cụm bệnh lý (dạ dày/thực quản 2b), rule 5b nhà thuốc, ví dụ `[QR]`, danh sách ảnh 5f | Template với biến `{brand_name}`, `{product_class}`, `{domain_rules}`; phần **rule chung** (1, 2, 2c, 3, 4, 5e, 5g, 5h, 5k, 5m, 5n, 5p, 5q, 6, 7) giữ nguyên cho mọi nhãn; phần **rule riêng** (2b, 5b, 5c/5i, 5d, 5f) đọc từ `brand/rules.md` |
| `router.py` | Keyword bệnh dạ dày, HP, nội soi | `brand/router_keywords.json` (simple/complex) |
| `tools_core.py` | Đọc `brain/kb.json` cố định; `need_map`, `compliance` theo cấu trúc Bình Vị | Giữ **schema** kb.json làm chuẩn chung (mục 4); chỉ đổi đường dẫn theo brand |
| `main.py` | Tiêu đề trang, tên bot trên web test/admin, `AB_START_DEFAULT` | `brand.json` + setting `ab_start_ts` |
| `db.py` | Không có gì riêng nhãn | Không đổi |

Nguyên tắc khi tách: **không đổi hành vi Bình Vị** — sau khi tách, chạy lại toàn bộ test offline + guardrail 12 ca, so từng câu trả lời với bản trước. Đóng bản đó là v1.1.0 của nền.

# 4. Bước (b) — dựng nhãn mới: checklist 10 mục

## 4.1 Tài liệu đầu vào (xin nhãn hàng trước, thiếu là dừng)
Tài liệu chuẩn sản phẩm (thành phần, công dụng theo GPQC, liều, đối tượng, chống chỉ định, tá dược), số XNCB/GPQC, bảng giá + quy cách, **bảng ưu đãi chính thức đã duyệt** (khách mới/khách cũ), chính sách hoàn tiền/đổi trả (có hay chưa), hotline, danh sách điểm bán/chuỗi, kịch bản CSKH đang dùng, 30–50 hội thoại thật của page, ảnh sản phẩm + ảnh đánh giá được phép dùng, danh sách nhân viên trực (Pancake user id) và dược sĩ.

## 4.2 KB `kb.json` — giữ đúng schema Bình Vị
```
_meta            brand, company, hotline, registration{xncb, gpqc}, disclaimer, status (ghi phiên bản KB)
products.<id>    name, type (TPBVSK/thuốc/mỹ phẩm), summary, key_ingredients, excipients_notes, benefits,
                 evidence + evidence_rule, dosage{attack, maintain, course, forgot}, packages[{sku,label,units,price_retail}],
                 recommended_package, need_tags
need_map         <tag>: {keywords, products, note}      ← triệu chứng/nhu cầu → gói
compliance       product_class, words_allowed, words_banned, price_talk_rules, <product>.{block, caution}
shipping         fee_single, freeship_with_promo, cod_note
pharmacy_policy  rule + 4 câu chuẩn
programs         new_customer{active, rules[]}, returning_customer{active:false, handoff:true}, loyalty_points, money_back{active}, big_order
combo_tiers      basic/standard/premium
customer_segments
escalation       handoff_rules, levels{1..4}, adr_7_fields, hotline
scripts_approved identity, expert_referral, ..., need_now, soft_ask_phone
phone_rules      principle, S1_order, S2_exit, S3_escalation, no_self_close
```
Điền từ tài liệu; chỗ chưa có quyết định để `active:false` và ghi rõ trong `note` (bot sẽ nói thật "chưa có chính sách"). Mọi con số trong KB phải có người của nhãn ký duyệt — lỗi 655k/1.025k của Bình Vị là do tài liệu gốc sai.

## 4.3 Bốn tool — thường không cần sửa
`kb_lookup`, `compliance_check`, `recommend`, `build_order` đọc theo schema; chỉ cần kiểm tra `compliance_check` có đủ nhóm rủi ro của sản phẩm mới (ví dụ Vương Bảo: bệnh tuyến tiền liệt kèm bí tiểu cấp, đang dùng thuốc chẹn alpha; Bổ gan: men gan cao do thuốc, viêm gan virus đang điều trị). Nhóm BLOCK/CAUTION là nơi dược sĩ nhãn hàng phải rà.

## 4.4 Persona, playbook, FAQ
Sao chép cấu trúc `brain/*.md` của Bình Vị, đổi nội dung theo khách hàng mục tiêu (Vương Bảo: nam trung niên, xưng "bác/anh"; KingsUp: nam, kênh Zalo cấm emoji và bảng — xem `KingsUp-Sale-Agent-Goi-nghien-cuu.zip`). Giữ các nguyên tắc chung: hỏi giá là báo giá ngay + 1 câu khai thác; câu bản lề khách mới/cũ; SĐT là lưới đỡ; không tự khai AI.

## 4.5 Prompt riêng nhãn (`brand/rules.md`)
Viết lại các rule đặc thù: cụm từ cấm theo GPQC (tương tự 2b "niêm mạc thực quản"), kịch bản nhà thuốc (5b) nếu nhãn có kênh OTC, rule chia giá (5c/5i) theo chính sách nhãn, danh sách ảnh (5f). Không đụng rule chung.

## 4.6 Ảnh
Tối đa ~7 ảnh, JPG < 1 MB, đặt tên id không dấu (`san-pham`, `danhgia-1`). Ảnh đánh giá phải có sự đồng ý của khách; câu kèm "cảm nhận cá nhân, hiệu quả tuỳ cơ địa" giữ nguyên.

## 4.7 Pancake
Page mới phải **có trong tài khoản Pancake** đang giữ gói (đăng nhập bằng Facebook, không phải email — nếu không token có `fb_id=null` và không thấy page), bật toggle Webhook trên page (tốn **2 slot** của gói — kiểm tra slot còn trống với người quản trị gói LK398Y trước). Tạo đủ **9 thẻ** cùng tên như Bình Vị (Bot, Bot chốt đơn, Chuyển TV, TV chuyên môn, RED FLAG, Nhóm người, Người xử lý/Để NV xử lý, Ko gửi được, Ko PH). Lấy `page_access_token` ở Cài đặt → Công cụ (không bấm Tạo Token). Lấy user id nhân viên trực qua `GET /pages/{page}/users`. Thêm `page_id=https://<service-nhãn-mới>/webhook/<path>` vào `PANCAKE_FORWARD_MAP` của hub Bình Vị.

## 4.8 Service Railway
New service từ repo fork → Variables: bộ ENV như docs/03 mục B6 với `PANCAKE_PAGE_ID`, `PANCAKE_PAGE_TOKEN`, `PANCAKE_ASSIGN_IDS`, khoá mới (`SECRET_PATH`, `ADMIN_KEY`, `WATCH_KEY`), `DB_PATH=/data/<nhãn>.db` + Volume gắn `/data`. Bật `test_only=1`, `enabled=1` để chỉ trả lời `#tm` lúc đầu.

## 4.9 Test — theo đúng đường Bình Vị đã đi
1. **Vòng 1 nội bộ** trên web test: 8–10 tester × 2–3 hội thoại theo 6 kịch bản (khách mới hỏi giá, chê đắt, bệnh nền, khách cũ, khiếu nại, hỏi điểm bán); chấm 👍👎 + góp ý; báo cáo lỗi theo nhóm; **lãnh đạo nhãn chốt** từng điểm mở.
2. **Guardrail 12 ca** (docs/03 Phần C) — viết lại ca 5, 7, 11 theo bệnh lý của nhãn.
3. **Vòng 2 trên page thật với `#tm`** 1–2 ngày: nhân viên nhắn từ nick cá nhân; kiểm tra thẻ, assign, ảnh gửi được, sticker, nhịp theo đuổi (đặt tạm `PANCAKE_FU_ORG=120,300` để không phải chờ).
4. **Go-live A/B**: `test_only=0`, `ab_percent=50`, ghi mốc `ab_start_ts`, gửi link `/w/` và thông báo đội CSKH (mẫu `Thong-bao-doi-CSKH-chay-thu-bot-BinhVi.docx`), 3 quy tắc đội (docs/03 A2). Theo dõi bảng tình trạng ngày đầu liên tục.
5. **Kết luận** khi trang A/B báo đủ mẫu; đo chốt đơn bằng SĐT đối chiếu hệ thống bán hàng.

## 4.10 Bàn giao
Tài liệu bàn giao tối thiểu như bộ này: danh sách chức năng (chỉ phần khác Bình Vị), nhật ký thay đổi, hướng dẫn CSKH 1 trang, ENV, quyết định đã chốt của lãnh đạo nhãn.

# 5. Những khác biệt theo kênh cần tính trước

| Kênh | Khác gì so với Messenger qua Pancake | Ảnh hưởng đến nền |
|---|---|---|
| Zalo OA (qua Pancake) | Không có cửa sổ ads 7 ngày; Zalo OA có giới hạn tin chủ động/ngày; không sticker FB; format cấm emoji/bảng (kinh nghiệm KingsUp) | Đặt `FU_*` riêng; tắt vision sticker; persona khác |
| TikTok Shop chat (Pancake) | Hội thoại gắn đơn hàng sàn; khách hỏi vận đơn nhiều | Cần tool tra đơn (D4) trước khi bật |
| Shopee chat | API Shopee riêng, không qua Pancake public API | Adapter mới; chỉ dùng lại engine + KB |
| Website live-chat | Không có thẻ/assign; cần UI riêng | Dùng lại `static/index.html` + handoff sang email/Zalo |

# 6. Lỗi Bình Vị đã trả giá — đừng trả lần hai

1. **Payload webhook không đủ trường** → thiết kế dựa vào API kéo về, webhook chỉ là tín hiệu (v0.5.40).
2. **Tin không có chữ** (sticker/ảnh) từng làm bot im và mất đơn (v0.5.15) — test sticker ngay vòng `#tm`.
3. **Số liệu A/B đẹp giả** vì ca người tiếp quản không bị loại (3 lỗ hổng) — mọi van loại phải chạy sau `ab_in`; luôn có bảng loại tay.
4. **Khe deploy mất tin** → giữ hook shutdown; đèn đỏ + replay.
5. **Câu bản lề khách mới/cũ chỉ nằm trong ghi chú KB** → lỗi xác suất 45 %: quy tắc bán hàng quan trọng phải là rule cứng có test (5p).
6. **Kênh khác chặn User-Agent Python** (n8n/WAF) → mọi HTTP ra ngoài mang UA trình duyệt.
7. **Anthropic tải ảnh theo URL tôn trọng robots.txt** → server tự tải, gửi base64.
8. **Đơn trên Pancake không đáng tin** làm thước đo → thu SĐT, đối chiếu hệ thống bán hàng thật.
9. **Hai phiên AI sửa cùng file** đè nhau → một nhánh, `git pull` trước, memory ghi ai đang làm gì.
10. **Không chạy guardrail khi đổi prompt** → lỗi lên khách thật.

# 7. Mẫu kế hoạch 3 tuần cho nhãn thứ hai (ví dụ Vương Bảo)

| Tuần | Việc | Đầu ra | Người chốt |
|---|---|---|---|
| 1 | Tách cấu hình nhãn (v1.1.0 nền) · thu tài liệu Vương Bảo · dựng `kb.json` + `brain/` · ảnh · fork repo, service Railway, `#tm` | Bot chạy demo trên web test; KB có chữ ký duyệt | Anh Na + PM nhãn + dược sĩ |
| 2 | Vòng test 1 nội bộ (10 tester) · báo cáo + chốt điểm mở · sửa v0.x · guardrail 12 ca | Báo cáo vòng 1; bản v0.4 tương đương | Anh Na |
| 3 | Nối Pancake page Vương Bảo (thay bot n8n hiện tại hoặc chạy song song theo page) · `#tm` 2 ngày · go-live A/B 50/50 · thông báo CSKH · theo dõi | Trang A/B có mốc; link `/w/` cho đội | Anh Na + Huyền Anh |
| 4–5 | A/B chạy, sửa nhỏ theo log, kết luận | Báo cáo A/B | Anh Na |

Ghi chú riêng Vương Bảo: hiện đang có bot n8n của Huyền Anh trên page 110542681967611 với 2 workflow và một số điểm học được (`So-sanh-bot-VuongBao-vs-BinhVi-28-08-2026.docx`); khi thay bằng nền Bình Vị, giữ nguyên `FORWARD_MAP` để không mất dữ liệu về n8n cho tới khi chuyển hẳn.
