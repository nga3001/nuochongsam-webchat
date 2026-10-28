# HƯỚNG DẪN CHO AI — Chatbot Bình Vị Thái Minh v1.0

> File này dành cho một AI/agent (Claude, Cowork, Claude Code, hoặc mô hình khác) được giao **đọc, sửa, mở rộng hoặc nhân bản** chatbot này. Đọc hết trước khi chạm vào code. Bản sao của file nằm ở gốc repo với tên `AI-README.md`; tài liệu cho người ở `docs/`.

## 0. Tóm tắt 60 giây

- **Là gì:** bot tư vấn – bán hàng TPBVSK Bình Vị Thái Minh, chạy trên Messenger + bình luận của page Facebook qua Pancake, kèm web test nội bộ. Python/FastAPI, SQLite, Claude API tool-use. Không dùng framework agent ngoài.
- **Đang chạy thật** trên page "Thảo Dược Cho Dạ Dày Khỏe" (page_id 103084702507557) với khách thật, A/B 50/50 với nhân viên. Mọi lỗi lên production ảnh hưởng doanh số và uy tín — **an toàn khách > doanh số > tốc độ sửa**.
- **Nguồn chân lý nội dung:** `brain/kb.json`. Không hard-code giá/liều/quà vào prompt hay code.
- **Deploy:** push lên `main` của GitHub `anhhn-ship-it/binhvi-webchat` → Railway tự build ~2–3 phút. Không có staging. Bù lại có: hook shutdown vét tin, kill switch, bảng tình trạng, `#tm` để test trên page thật mà không lẫn số liệu.
- **Người quyết định:** anh Na (CEO). Các quyết định đã chốt liệt kê ở mục 7 — **không lật lại** nếu không được anh Na yêu cầu.

## 1. Bản đồ mã nguồn

```
binhvi-webchat/
├── main.py              # FastAPI: route web test, admin, webhook, trang A/B, bảng tình trạng, Excel (1.454 dòng)
├── pancake_adapter.py   # Toàn bộ logic kênh Pancake: webhook, hub, gom tin, gửi chữ/ảnh, thẻ, assign,
│                        #   van ngược, A/B, nhịp theo đuổi, nhà thuốc, bình luận, hồ sơ khách, vision (2.197 dòng)
├── engine.py            # System prompt (Rule 1-7, 5b-5q) + vòng tool-use + bóc thẻ [HANDOFF]/[PHARMACY]/[IMG]/[QR]
│                        #   + tách tin + gom text mọi vòng + đường lùi khi ảnh lỗi (443 dòng)
├── tools_core.py        # 4 tool: kb_lookup, compliance_check, recommend, build_order — đọc kb.json (276 dòng)
├── providers.py         # AnthropicProvider (image block base64), OpenAICompatProvider (GPT/DeepSeek), registry
├── router.py            # Định tuyến auto: keyword → haiku/sonnet
├── pii.py               # Che SĐT/địa chỉ khi gửi model ngoài Anthropic
├── db.py                # SQLite schema + helper (500 dòng) — xem lưu ý 4.3 trước khi sửa
├── brain/
│   ├── kb.json          # NGUỒN CHÂN LÝ: _meta, products, need_map, compliance, shipping, pharmacy_policy,
│   │                    #   programs, combo_tiers, customer_segments, escalation, scripts_approved, phone_rules
│   ├── persona.md       # Giọng điệu, xưng hô, format Messenger
│   ├── playbook.md      # Quy trình 7 bước, xử lý phản đối
│   └── faq.md           # FAQ theo tài liệu CSKH
├── static/index.html    # Web chat test  ·  static/admin.html  # Admin  ·  static/img/*.jpg  # 7 ảnh sản phẩm/đánh giá
├── requirements.txt · Procfile · .gitignore · README.md · README-huong-dan.md
```

### Luồng một tin nhắn Messenger
`POST /webhook/pancake-wh-binhvi` → `route_event` (hub: page khác → `_forward` sang URL trong `FORWARD_MAP`; page mình → tiếp) → `handle_event` (dedupe · `page_auto` · `type=COMMENT → handle_comment` · van ngược `_sync_human_tag`/sale gõ tay · `ab_in` chia nhóm · nhóm người return · `_bare_phone` → `_phone_handoff` · attachment: `_attach_kind` → ảnh/sticker lấy url (vision) hoặc `_attach_handoff` · `_enqueue`) → sau `BATCH_SECONDS` (12 s) `_flush` → `_respond` (lấy history, gắn `images` vào tin user cuối, `_profile_of` → `engine.chat(history, profile=…)` → bóc handoff/pharmacy/img → `_too_similar` chống lặp → `send_message` từng phần, nghỉ `PART_GAP` → `send_images` → thẻ/assign/unread/lead/`ab_reply` → `_fu_touch`).

### Vòng nền (thread daemon, start trong `main.startup`)
`_sla_loop` 60 s (nhịp tim `hb_ts` + SLA handoff) · `_poll_loop` 25 s (dự phòng webhook) · `_fu_loop` 60 s (nhịp theo đuổi + `_pharm_check_once`) · `_src_loop` 600 s (nguồn ads/organic, gender, tên) · `_orders_loop` (POS — không dùng). `shutdown` → `flush_all_batches()`.

### Thẻ ẩn trong câu trả lời của model (hệ thống bóc, khách không thấy)
`[HANDOFF: lý do | SĐT | level 1-4]` → thẻ Pancake theo `TAG_BY_LEVEL`, assign, unread, bảng handoff, SLA. `[PHARMACY]` → `_pharm_mark`. `[IMG: id]` → web render `<img>`, Messenger `send_images`. `[QR: a | b | c]` → gợi ý nhanh web, bị lược trên Messenger.

### Trạng thái runtime nằm trong bảng `settings` (key → value)
`pancake_kill/enabled/poll/test_only/followup/comment/comment_test/vision/ab_percent` (van) · `ab_start_ts`, `fu_start_ts`, `batch12_ts` (mốc) · `hb_ts` · `watch_key` · theo hội thoại: `fu:<conv>` JSON {t,n,ph,ls}, `fu_ph:<conv>`, `src:<conv>`, `gender:<conv>`, `name:<conv>`, `prof:<conv>`, `ab_tagged:<conv>`, `ab_att:<conv>`, `ab_unreach:<conv>`, `ab_flag:<conv>`, `cmt:<inbox>`, `pk_content:<img_id>`. Xoá/sửa setting là cách điều khiển không cần deploy.

### Sự kiện `webhook_log` (dùng để chẩn đoán)
Bình thường: `messaging`, `reply`, `fu_sent`, `fu_close`, `src_sync`, `profile`, `vision_in`, `img_sent`, `cmt_priv/cmt_reply/cmt_seed`, `toggle`, `poll_baseline`, `forward_ok`. Cảnh báo (dim): `page_auto`, `human_tag`, `sale_typed`, `cmt_human`, `cmt_gone`, `api_noop`, `dedup_part`, `send_unreach`, `ab_contaminate`, `ab_flag`. Lỗi (vào đèn đỏ `HEALTH_ERR`): `error`, `send_fail`, `api_fail`, `cmt_fail`, `forward_err`, `img_upload_fail`, `img_send_fail`, `sla_overdue`.

## 2. Quy tắc bất biến khi sửa

1. **Không đổi nội dung tư vấn trong code.** Giá, quà, liều, câu chuẩn → `kb.json`. Hành vi → rule trong `engine.py`. Kênh → `pancake_adapter.py`.
2. **Mọi thay đổi hành vi phải qua guardrail 12 ca** (docs/03 Phần C) trên web test trước khi push. Đổi prompt mà không chạy guardrail đã từng để lọt lỗi 45 % (rule 5p).
3. **Không gộp nhiều thay đổi hành vi vào một bản** khi A/B đang chạy. Một bản = một mục đích, tên commit `v1.0.x: <việc>`.
4. **Ghi mốc** (`db.set_setting("<tên>_ts", now)`) cho thay đổi ảnh hưởng số liệu và hiện lên trang A/B.
5. **Đường lùi bắt buộc:** không thành phần phụ nào (ảnh, sticker, comment, tên khách, API Pancake lỗi) được làm chết lượt trả lời chính hoặc báo đỏ oan. Mẫu: `_vision_fallback`, `_cmt_gone`, `_is_noop`, `_is_neterr`.
6. **Không retry lệnh gửi khi nhận HTTPError** (nguy cơ gửi đôi); chỉ retry lỗi mạng/429.
7. **Không lưu URL ảnh/SĐT thô vào nơi hiển thị công khai**; trang `/w/` và `/a/…/ab` không hiện SĐT.
8. **Thêm van loại ca A/B → đặt SAU `db.ab_in`** (3 lỗ hổng đã dạy: UPDATE trước khi có dòng là vô hiệu).
9. **Test offline trước** bằng stub (mẫu ở mục 5); suite cũ ~200 case phải pass (`test_v0515`, `test_phanB`, `test_phanC`, `test_flush`, `test_d1cmt`, `test_neterr`, `test_vision`, `test_attkind`, `test_hole3` — nằm trên máy anh Na, không trong repo; nên đưa vào `tests/` ở v1.1).
10. **Verify sau deploy bằng hành vi live**, không tin màn hình: `/healthz`, toggle mới được chấp nhận, log event mới xuất hiện, `#tm` test.

## 3. Quy trình sửa & deploy (chuẩn v1.0)

```bash
cd "$HOME/mnt/Chatbot/repo/binhvi-webchat"     # trên máy anh Na (device_bash) — cloud container KHÔNG ra được GitHub
git pull -q
# sửa bằng sed/python read-modify-write; KHÔNG gõ lại file từ output bị cắt
python3 -m py_compile main.py pancake_adapter.py engine.py   # syntax
# chạy test offline (mục 5)
git add -A && git commit -m "v1.0.x: <việc>" && git push origin main
git log --oneline -1
```
Sau 2–3 phút: mở `/healthz`, bảng tình trạng, nhắn `#tm` vào page. Ghi biên bản vào memory/nhật ký.

Bẫy môi trường (đã gặp, đừng tốn thời gian lại):
- Folder mount trên máy anh Na **cấm xoá file** → git lỗi `could not lock config file`/`index.lock`. Xin `device_request_delete_permission` cho `D:\Claude\Chatbot` (quyền chỉ sống 1 phiên), hoặc `mv .git/index.lock .git/index.lock.stale`. Warning "unable to unlink tmp_obj" vô hại.
- Cloud container và device_bash **không tới được** `railway.app` lẫn `pages.fm` (proxy 403/000). Đọc log/probe/POST admin qua **trình duyệt** (Claude in Chrome hoặc trình duyệt tích hợp) bằng `fetch()` same-origin từ tab mở domain Railway, thêm `{cache:'no-store'}` — WebFetch trả cache cũ và cắt `/api/admin/logs` ~2000 dòng.
- KB upload qua admin bị ghi đè khi redeploy → sửa KB lâu dài trong repo.
- Railway ENV đổi qua UI Variables → tick ✓ → **Deploy**; đọc lại `/api/admin/pancake` để chắc.
- Đừng bao giờ copy folder `repo\` ra ngoài — remote URL chứa token.

## 4. Pancake API — những gì đã kiểm chứng thật

- Base `https://pages.fm/api/public_api/v1` (và `/v2` cho conversations phân trang). Token qua **query param** `page_access_token` (lấy sẵn ở Cài đặt → Công cụ, không "Tạo Token"). Rate 5 req/s/page (`_throttle`).
- Gửi tin: `POST /pages/{page}/conversations/{cid}/messages?customer_id=…` body `{"action":"reply_inbox","message":"…"}`. Gửi ảnh: `POST /pages/{page}/upload_contents` (multipart `file`) → `id`; rồi body `{"action":"reply_inbox","content_ids":[…]}` — **`message` và `content_ids` loại trừ nhau** (gửi cả hai → 500). Tối đa 30 content_ids.
- Thẻ: `{"action":"add","tag_id":N}` — id đọc từ `GET /pages/{page}/tags` (cache `_refresh_tags`). Assign `{"assignee_ids":[…]}`. Unread `{}`. Note **không hỗ trợ**.
- Conversations: `GET /pages/{page}/conversations?since=<unix>&until=<unix>&type=INBOX|COMMENT` (since **bắt buộc**, dạng ngày chữ trả rỗng); mỗi conv có `ad_ids`, `post_id`, `page_customer.gender`, `from.name`. **Không có endpoint 1 conversation**; filter `customer_id` bị bỏ qua → phải quét list.
- Webhook payload **thường tối giản** (không `page_customer`, không `ad_ids`) — chỉ thi thoảng đầy đủ. Không thiết kế dựa vào trường tuỳ chọn của webhook.
- Comment: conv_id `{POST_ID}_{COMMENT_ID}`, post_id `{PAGE_ID}_{POST_ID}`. Trả lời công khai `{"action":"reply_comment","message","message_id"}`; nhắn riêng `{"action":"private_replies","message","message_id","post_id"}` (thiếu `post_id` → lỗi 100). FB chỉ cho **1** private reply/comment. Comment bị FB gỡ → `(#100, 33) Unsupported post request`.
- Không chặn gửi sau 24 h ở tầng Pancake (đã thử ca im 3,7 ngày); tuân thủ cửa sổ Meta là việc của mình: ads 7 ngày, organic 24 h.
- Pancake tách INBOX/COMMENT thành 2 conversation → cùng khách có 2 dòng, không phải bug. Đơn hàng không ở public API page mà ở POS `pos.pancake.vn/api/v1/shops/{shop}/orders` (page token không dùng được) — và đã quyết định **không dùng**.
- Pancake tự tắt webhook khi > 80 % lỗi trong 30 phút & ≥ 300 request lỗi → polling là lưới đỡ; sự kiện "Hội thoại" phải giữ bật.
- Cổng tiện: `GET /api/admin/pancake_probe?key=&cid=&method=&path=&qs=&base=&raw_body=` gọi tay API Pancake từ server (giờ trả về UTC).

## 5. Test offline — mẫu stub

```python
# tests/_stub.py — chạy pancake_adapter mà không có FastAPI/Pancake thật
import os, sys, types, tempfile
os.environ["DB_PATH"] = tempfile.mktemp(suffix=".db")
fastapi = types.ModuleType("fastapi"); fastapi.FastAPI = lambda *a, **k: None   # nếu import main
sys.modules.setdefault("fastapi", fastapi)
import db, pancake_adapter as pa
db.init(); db.set_setting("pancake_test_only", "0")          # không thì _may_send=False
sent = []
pa._api = lambda method, path, params=None, body=None, base=None, **k: (sent.append((method, path, body)) or {"success": True, "id": "m_1"})
pa.engine = types.SimpleNamespace(chat=lambda h, model_key=None, profile=None: {"reply": "Dạ em chào mình ạ", "handoffs": [], "pharmacy": False})
payload = {"event_type": "messaging", "conversation": {"id": "P_C1", "type": "INBOX", "customer_id": "u1"},
           "message": {"id": "m1", "message": "giá bao nhiêu", "from": {"uid": None}}}
pa.handle_event(payload); pa._flush("P_C1")                   # gọi _flush TAY — InstantTimer trong _enqueue sẽ deadlock
assert any(b and b.get("action") == "reply_inbox" for _, _, b in sent)
```
Nhớ: stub `engine.chat` phải nhận `profile=None` (ảnh đi trong `history[-1]["images"]`, không phải tham số); `_flush` gọi tay; sticker thật có `message` rỗng + `attachments:[{"type":"sticker"}]`, `from.uid=None`.

## 6. Cách chẩn đoán nhanh một ca

1. Lấy conv_id (đuôi ≥ 6 ký tự đủ cho `ab_flag`; đầy đủ dạng `103084702507557_<số>`).
2. `/api/admin/logs?key=&hours=24&q=<đuôi conv>` → chuỗi event theo thời gian: có `messaging` mà không `reply` = bot im; `page_auto`/`sale_typed`/`human_tag` = người đã tiếp quản; `send_unreach` = #551; `dedup_part` = câu bị cắt vì trùng; `profile` = đã bù hồ sơ.
3. Đọc tin thật: `pancake_probe?cid=<conv>&method=GET` (UTC +7).
4. Web test tái hiện: POST `/api/chat` với cùng lời khách, đọc `tool_trace` + `_debug` (stop_reason, rounds, `_vision_fallback`).
5. Nếu tin rơi trong khe deploy: replay bằng POST payload messaging (id thật) vào `/webhook/pancake-wh-binhvi`; dedupe là RAM nên sau restart replay được.

## 7. Quyết định đã chốt của anh Na — KHÔNG tự đảo

| Ngày | Quyết định |
|---|---|
| 21/08 | 6 điểm vòng 1: combo 2 = 1.025k; chê giá không chia giá/ngày; gửi nguyên 5 ảnh review; chưa có chính sách hoàn tiền; khách cũ/tích điểm → xin SĐT chuyển người; điểm bán trả lời chung chuỗi lớn + hotline |
| 24–25/08 | Tờ trình 9 điểm; nới 5i (được trả lời phép tính khách hỏi); xưng dược sĩ tư vấn; SĐT là lưới đỡ; quà combo 2 lọ = Bổ gan TM + hộp 20v |
| 25/08 | Webhook dùng chung cả gói → hub bắt buộc; wipe volume bắt đầu sạch |
| 26/08 | Mốc đo A/B 10:53, không xoá data cũ; ảnh/tệp → chuyển người, sticker → hiểu; 3 nhịp theo đuổi bật ngay; khoá theo dõi riêng + kill switch 2 bước |
| 28/08 | Bỏ chỉ số đơn Pancake; nhịp ads 30p/1d/3d không D+6, organic 1h/8h; nhà thuốc hỏi thăm 1 lần không giá; không đoán giới tính; hoãn KB Google Sheet; gom tin 12 s |
| 29/08 | Đại trà trả lời bình luận, A/B 50/50 tầng comment; bỏ dòng "Không gửi được" khỏi card |
| 01/09 | Vision mức "nhìn để phục vụ"; không mở tệp thoại/video/PDF |
| 03/09 | Gọi nguyên tên Facebook nếu giống tên Việt, không tách họ/tên |

## 8. Việc mở cho v1.1 (thứ tự gợi ý)
Đưa test suite vào `tests/` trong repo · C1 danh sách ngoài chỉ định (cơ chế có, chờ danh sách) · tắt polling sau khi webhook ổn · nghiệm thu thật v0.5.40–42 · D4 tool tra đơn khi có API bán hàng thật · tách cấu hình nhãn hàng (page_id, KB, ảnh, tên thẻ) ra một file để nhân bản (xem docs/05).

## 9. Khi bạn là AI làm việc với anh Na
Xưng "em"/tên trợ lý, gọi "anh Na"; trả lời tiếng Việt; góc nhìn CEO (tác động doanh số, rủi ro khách, nguồn lực). Trước khi sửa: đọc memory dự án + `git log` xem phiên khác vừa làm gì; nhiều phiên song song đã từng đè nhau. Không hỏi xác nhận thừa cho việc kỹ thuật thường quy, nhưng **phải hỏi** khi: đổi hành vi với khách, đổi số liệu A/B, wipe dữ liệu, chi tiền (Railway/API), gửi tin thật ra ngoài chế độ `#tm`. Kết quả file: trung gian → `Data trung gian`, chạy được/bàn giao → `Kết quả`.
