# Chatbot Sâm Thái Minh — v0.1.49 (nháp, 21/10/2026) — CHỈ page Sâm Thái Minh

Nhân bản từ **Bình Vị Thái Minh v1.0** theo `docs/05` — **Mô hình 1: repo + service Railway riêng**. Phần nền (Pancake, gom tin, thẻ, A/B, nhịp theo đuổi, kill switch, vision) giữ nguyên; phần não thay mới cho 11 sản phẩm Sâm.

> Các file `AI-README.md` và `docs/01–05` là tài liệu gốc của Bình Vị. Vẫn đọc chúng để hiểu nền, nhưng mọi quyết định riêng của Sâm nằm trong file này.


## v0.1.49 (22/10/2026) — không xin lại SĐT đã đúng (ca chị Thuần)
- Khách gửi tên + SĐT + địa chỉ chung 1 tin ("0919815816 39 Lê Văn Tám…") → bot ghép nhầm số nhà vào SĐT, bảo "thiếu số", xin lại 2 lần dù khách nói "số đúng rồi".
- Sửa: (1) đơn tự lấy SĐT 10 số hợp lệ khách đã gửi khi model ghép nhầm/bỏ trống; (2) bộ lọc bỏ đoạn "SĐT thiếu số / gửi lại" khi khách đã gửi số đủ 10 chữ số; (3) luật (l): số 10 chữ số đầu 0 là hợp lệ, khách nói "số đúng rồi" thì tin khách.

## v0.1.48 (22/10/2026)
- Bản đóng gói cuối của mọi thay đổi ngày 22/10 (ghi chi tiết ở mục v0.1.47 bên dưới). Từ nay mỗi lần sửa = 1 số phiên bản mới, không đóng lại trùng tên.

## v0.1.47 (22/10/2026) — giữ "chưa đọc" sau khi bot trả lời
- Chị Nga 22/10: bot mới chạy, muốn đọc lại mọi ca. Bot trả lời / gửi nhịp theo đuổi xong → ~3 giây sau đánh dấu lại CHƯA ĐỌC trên Pancake.
- Tắt khi không cần nữa: thêm biến Railway `PANCAKE_KEEP_UNREAD=0`.
- Mở lại ca cho bot: ca nhân viên chỉ nhắn tay → sau `PANCAKE_REOPEN_HOURS` giờ (mặc định 1 — chị Nga chốt 22/10); ca đang có thẻ "Người xử lý" / "Để NV xử lý" / "ADR/Khiếu nại" → chờ ít nhất `PANCAKE_REOPEN_HOURS_TAGGED` (mặc định 24 giờ).
- Bot CHỐT ĐƠN xong (thẻ "Bot chốt đơn") vẫn trực: khách hỏi thêm sản phẩm/cách dùng/bệnh nền → bot trả lời; khách đổi/huỷ đơn, hỏi giao hàng → HANDOFF mức 2 về người (rule 5o-k). Nhanh đã chặn tạo đơn trùng. Ca đã chốt đơn KHÔNG nhận nhịp theo đuổi nữa (kể cả khách hỏi thêm rồi im).
- Khách ĐÃ ĐỂ SĐT mà nhân viên nhắn tay vào ca → coi như nhân viên đang gọi/lên đơn: bot chờ 24 giờ mới nhận lại, và không gửi nhịp theo đuổi.

## v0.1.46 (21/10/2026) — ảnh chính Nước Hồng sâm
- Thêm `static/img/nuoc-hong-sam.jpg` (hộp 20 túi + ấm trà, chị Nga gửi 21/10) — ƯU TIÊN gửi khi giới thiệu Nước Hồng sâm; ảnh chai chỉ khi khách hỏi dạng chai.
- Thêm `static/img/nuoc-hong-sam-10tui.jpg` — CHỈ gửi khi khách hỏi/mua hộp nhỏ 10 túi.

## v0.1.45 (21/10/2026) — sửa ca "loạn" (chị Hoa Nguyễn)
- Gọi tên đúng: "Hoa Nguyễn" → "chị Hoa" (không còn "chị Nguyễn"); họ đứng cuối + 3 chữ → gọi "anh/chị".
- Đã gọi "chị X"/"anh X" thì tự thay mọi "anh/chị" trong câu trả lời → không lẫn xưng hô.
- Câu hỏi đã hỏi ở lượt trước (dù diễn đạt khác, giống ≥60%) → tự bỏ.
- Luật mới: không nhắc lại lời khuyên/câu hỏi; khách hỏi thêm → tổng hợp mọi câu chưa trả lời và trả lời đủ trong 1 lượt.
- Chỉ khi khách khiếu nại sản phẩm CỦA THÁI MINH gây đau, đi ngoài, mẩn ngứa… → tạm ngừng + chuyển chuyên viên (HANDOFF mức 4). Sản phẩm khác (vd rượu sâm Ngọc Linh) → không chuyển, chỉ khuyên ngừng/đi khám rồi tư vấn tiếp.
- Không khen/chê phương pháp khác (diện chẩn, thuốc nam…).
- Nhắc nhớ (follow-up): khách đã cảm ơn/chào/"khi nào cần nhắn lại"/không mua (hoặc bot đã chào kết) → không gửi nhắc nữa, ở MỌI nhịp.

## 0. Trạng thái triển khai (13/10/2026) — chị Nga tự dựng, tài khoản riêng
- GitHub: `nga3001/samthaiminh-webchat` (Private). Bản gốc lên GitHub là zip **v0.1.8** (không có Gemini v0.1.9 cũ).
- Railway: project `astonishing-freedom`, service `web`, domain `web-production-bdd6d.up.railway.app`, Volume `/data`. Gói Trial (5 USD / 30 ngày từ 24/09) → phải Upgrade Hobby trước khi hết (khoảng 24/10).
- Variables: `SECRET_PATH`, `ADMIN_KEY` (chỉ chữ không dấu — chữ có dấu làm web chat báo forbidden), `DB_PATH=/data/samthaiminh.db`, `GEMINI_API_KEY`, `DEFAULT_MODEL=gemini_lite`. 13/10: anh Huy (giám đốc) tạo API key Claude từ tài khoản công ty (credit 40 USD) gửi riêng chị Nga → thêm `ANTHROPIC_API_KEY`, đổi `DEFAULT_MODEL=sonnet` để test bằng Claude.
- Gemini: AI Studio, **gói miễn phí** (chỉ test bằng dữ liệu giả). `gemini` (3.8 Flash) bị 503 quá tải ở gói miễn phí → dùng `gemini_lite` (3.5 Flash-Lite). Bật thanh toán trước khi nối Pancake.
- v0.1.10 (24/09, đã lên GitHub): `providers.py` thêm GeminiProvider (giữ thought signature, ảnh base64, reasoning_effort, che PII), `engine.py` fallback provider + FALLBACK_MODEL, `router.py` ROUTER_STRONG/ROUTER_CHEAP, `main.py` whitelist gemini + demo_mode.
- v0.1.11 (25/09): Tam Sâm Đan + Đông trùng hạ thảo = `on_request_only` (chỉ khi khách tự hỏi; bỏ khỏi need_map/product_overview); `engine.py` rule 5j + **chặn cứng chữ "mình"** (`fix_minh`); `tools_core.py` reminder.
- v0.1.12 (25/09, gộp luôn v0.1.11): tích hợp brief "RV-Sâm Thái Minh BRIEF_ THÔNG TIN TRAINING BUSINESS AI chuẩn.docx". Chị Nga chốt: (1) bảng quà Hồng sâm lát THEO BRIEF (2 hộp: 1 hộp Trà sâm; 4 hộp: 2 hộp Trà sâm; 6 hộp: 5 hộp Trà sâm 10 gói; 10 hộp: 1 chai Nước HSMO; 15 hộp: 1 HSVN + Trà 1700 20 gói; 1 hộp tặng 1 hộp Trà sâm CHỈ khi khách chê đắt) — bỏ mốc 3, 5 hộp của Excel; (2) hỏi giá → báo NGAY giá + liệu trình + combo, không hỏi khách mới/cũ; (3) upsell gấp đôi 1 lần sau khi có đủ thông tin; (4) bám khách 30 phút → +4h → +12h rồi dừng; phản hồi sau 60 giây (PANCAKE_BATCH_SECONDS mặc định 60). Thêm: dùng thử → từ chối khéo; Trà sâm, Rượu, Đông trùng, Tam Sâm Đan chỉ khi khách hỏi; chào đầu bắt buộc (chèn cứng ở kênh messenger); chặn cứng "mình"; cáo buộc/khiếu nại → level 4; chưa hiểu → hỏi lại; sau chốt đơn không nhắn thêm.
- **v0.1.13 (13/10 sáng):** xem mục 0b.
- **v0.1.14 (13/10 chiều, chờ tải lên — gộp luôn v0.1.11–v0.1.13 nếu chưa tải):** xem mục 0c. File đổi: `engine.py`, `pancake_adapter.py`, `tools_core.py`, `brain/kb.json`, `brain/persona.md`, `brain/playbook.md`, `brain/faq.md`, `tools_build/build_kb.py`. Cần thêm ảnh `static/img/nha-may.jpg` (ảnh nhà máy cho tin bám khách nhịp 2; thiếu thì chỉ gửi ảnh vườn).
- Điểm chờ chị Nga xác nhận: "1 hộp Trà sâm" ở combo 2/4 hộp là loại nào (1700 10 gói / 20 gói / nguyên lá)? Freeship Hồng sâm lát 1 hộp (bảng Excel cũ có freeship, brief không nhắc — hiện TÍNH phí ship 15k/20k khi mua 1 hộp không chê đắt). Hotline chung: brief ghi 1800 1120 – 1800 8308 (KB đang: 1800 1120 chung, 1800 8308 riêng Dương Sâm, số phụ 1800 8396).
- **v0.1.15 (13/10 tối, chờ chị Nga duyệt bản tổng hợp):** (1) **Giá một chỗ** — giá Hồng sâm lát, combo, quà chỉ nằm trong bảng sản phẩm + bảng khuyến mãi của `build_kb.py`; câu báo giá, upsell, tin bám khách nhịp 3 tự sinh từ đó. Đổi giá: sửa `build_kb.py` → chạy lại → tải `brain/kb.json`. Không sửa giá trong persona/playbook/faq. (2) **Bỏ mã shop Bình Vị** — `PANCAKE_SHOP_ID` không còn mặc định; muốn quét đơn POS phải đặt ENV mã shop Sâm. (3) **Lưu tạm (prompt caching) sửa lại** — phần luật + kb (~69 nghìn ký tự) giống hệt cho mọi khách, đặt trước dấu `providers.CACHE_SPLIT`; phần riêng (sản phẩm trọng tâm, hồ sơ khách) đặt sau, không lưu tạm. Bản cũ chèn sản phẩm trọng tâm + tên khách vào cùng khối nên lưu tạm gần như không trúng. Thêm điểm lưu ở tin cuối để các vòng gọi công cụ trong cùng lượt dùng lại lịch sử. (4) **12 ca thử riêng cho Sâm**: `tests/test_sam_12ca.py` (chạy `python3 tests/test_sam_12ca.py`, không tốn API) + `tests/ca-thu-tay-12ca.md` (người thử chạy tay). File đổi: `providers.py`, `engine.py`, `pancake_adapter.py`, `tools_build/build_kb.py`, `brain/kb.json`, `brain/persona.md`, `brain/playbook.md`, `brain/faq.md`, thêm `tests/`.
- **v0.1.22 (16/10 chiều, nhân viên test trên Pancake):** (1) Gom tin: câu ĐẦU của khách chờ 50 giây (`PANCAKE_BATCH_FIRST_SECONDS`), các câu sau 30 giây (`PANCAKE_BATCH_SECONDS`, mặc định đổi 60→30). (2) Khách gửi trần SĐT: bot VẪN chat tiếp (`PANCAKE_PHONE_STOP=1` để quay lại kiểu cũ dừng & giao người). (3) Chào lặp: `_ensure_greeting` không chèn khi model đã tự chào (sau [IMG] hoặc "Dạ em chào chị X"). (4) Lưới chặn bỏ "rất tốt / hiệu quả rất tốt" sau câu công dụng. (5) Nước HS: tiểu đường dùng được (trước ăn 30 phút, đường huyết ổn định), khách kiêng mật ong không tự chuyển Long Sâm. (6) Suy thận 3–4: dùng được nhưng hỏi bác sĩ trước (hết HANDOFF); "bệnh nào không dùng được" chỉ kể nhóm absolute. (7) Flag mới `stomach_ulcer` (viêm loét dạ dày, chốt chị Nga) cho lát/chai/túi. (8) Huyết áp: bỏ "không gây tăng huyết áp như sâm Hàn Quốc" khỏi action tool (gốc của câu bịa "tinh dầu sâm tươi"), cấm so sánh/chê sâm khác, cấm "ý kiến của chị rất đúng"; bỏ dòng 84 vs 26 saponin trong playbook (cùng loại với "gấp 3 lần" anh Huy cấm). (9) Tên tiếng Việt có dấu gọi bằng chữ cuối ("chị Mai"); tên không dấu chỉ gọi anh/chị. (10) Không tự thêm công dụng theo triệu chứng (đau đầu, chóng mặt). (11) Đặt stent + thuốc chống đông: flag `stent_lt6m` / `stent_6_12m` / `stent_ge12m`. Hồng sâm lát & Nước HS: dưới 6 tháng tham khảo bác sĩ, từ 6 tháng dùng được (lát 1/2 gói/ngày). Dương Sâm/Long Sâm: dưới 1 năm tham khảo bác sĩ, từ 1 năm dùng được 1 viên/ngày. (12) Chị Nga 16/10: ĐƯỢC nói "Hồng sâm Việt Nam không gây tăng huyết áp như sâm Hàn Quốc" và "Sâm Việt Nam/Lai Châu có 84 loại saponin" (khôi phục); vẫn cấm bịa chuyện tinh dầu.
- **v0.1.44 (21/10 14:08, chị Nga, ca chị Hoa Nguyễn):** NHỊP NHẮC NHỚ không gửi khi hội thoại đã kết thúc (`_fu_conversation_ended`): khách cảm ơn / chào / hẹn "khi nào… sẽ nhắn lại" / chưa mua, không mua; hoặc tin cuối của bot là chào tạm biệt, chúc sức khỏe, "khi nào… nhắn lại cho em" (không kết bằng câu hỏi) → không nhắc, xoá lịch nhắc (log `fu_skip`). Khách "để suy nghĩ / để sau" VẪN được nhắc. Khách còn hỏi (có "?") → vẫn theo. Sửa tách tên: Facebook "Hoa Nguyễn" (Tên Họ, 2 chữ) trước bị gọi "chị Nguyễn" → nay "chị Hoa"; câu nhắc nhớ gọi tên gọi ("Chị Hoa ơi") thay vì cả tên Facebook.
- **v0.1.43 (21/10 14:05, chị Nga):** Hồng sâm lát hộp 14 gói = **hộp thiếc**, mỗi gói 2g có **1–2 lát sâm** (kb label `hsvn-lat-14` + FAQ "Quy cách, đóng gói").
- **v0.1.42 (21/10 14:00, chị Nga — phân tích ca anh Hoa Phan + anh Vũ Nhân Luật):** (1) LƯỚI CHẶN QUÀ COMBO (`_fix_combo_gifts`): AI hay ghi sai "Combo 1 tháng (2 hộp) tặng 2 hộp Trà 20 gói / 4 hộp tặng 4 hộp" → code tự sửa mọi dòng "Combo X tháng (N hộp) … tặng …" về đúng bảng CTKM (2 hộp: 1 Trà 20 gói 190.000đ; 4 hộp: 2 Trà 20 gói 380.000đ; 6 hộp: 5 Trà 10 gói). (2) CHẶN ÉP COMBO (`_drop_repeated_upsell`): đã mời combo + khách nói "dùng thử / 1 hộp thôi / cho tôi 1 hộp" → bỏ mọi đoạn mời combo. (3) Luật 5o: khách đã chọn số lượng → xác nhận + xin thông tin, không gửi bảng combo; mời combo đúng 1 lần; không hỏi lại thông tin đã gửi; sticker/like = đồng ý, không bình luận hình; khách cho tên thật → gọi tên gọi ("anh Hòa"); tối đa 3 tin, 1 câu hỏi. (4) Quảng cáo hứa quà (`AD_GIFT_1BOX_IDS`, mặc định Ad 120252524881450596 "CTKM - Biếu quà"): mua 1 hộp Hồng sâm lát → tặng 1 hộp Trà sâm 1700 10 gói như quảng cáo ghi. Nhịp nhắc khách 30 phút/4h/12h: là công tắc "Nhịp theo đuổi" trên trang quản trị (đang tắt từ trước) — bật bằng nút, không cần sửa code.
- **v0.1.41 (21/10 13:50, chị Nga):** nhân viên (hoặc tin tự động/AI của page) nhắn nhắc khách trước, khách nhắn lại thì bot lại chào "Dạ Sâm Thái Minh chào anh/chị ạ" — không hợp lý. Nguyên nhân: lịch sử bot chỉ có tin của chính bot. Nay mọi tin page gửi khách (không phải bot) được nhớ (`page_said:<conv>`, tối đa 5 tin) và đưa vào lịch sử như tin của page trước khi bot trả lời (log `page_ctx`) → bot KHÔNG chào lại, tiếp nối đúng mạch tin nhân viên.
- **v0.1.40 (21/10 13:45, chị Nga chốt): PHÂN LOẠI BÌNH LUẬN** (`classify_comment`): (1) hỏi giá/thông tin ("xin giá", ".", "ib", câu hỏi) → nhắn riêng tư vấn + câu công khai MỚI (cảm ơn quan tâm sản phẩm + nhờ kiểm tra tin nhắn để nhận thông tin chi tiết, 3 câu xoay vòng); (2) khen/chia sẻ dùng tốt → công khai "Dạ em cảm ơn anh/chị đã tin dùng và chia sẻ cảm nhận ạ. Chúc anh/chị và gia đình luôn mạnh khỏe ạ 🌿" + nhắn riêng cảm ơn, báo ưu đãi khách quen (positive_feedback), không báo giá; (3) chê/phàn nàn/cáo buộc/kể bị phản ứng → bot KHÔNG trả lời, gắn thẻ Người xử lý + giao ca + chưa đọc + ghi chú 🔴 (log cmt_negative); câu HỎI "có tác dụng phụ không?" vẫn là loại 1; (4) tag bạn bè / chỉ icon / link lạ → bỏ qua (log cmt_skip). Mẫu hotline + cửa hàng chỉ còn dùng khi không nhắn riêng được.
- **v0.1.39 (21/10 13:40, chị Nga):** bình luận "Xin giá" mà bot trả lời công khai bằng mẫu hotline/cửa hàng → khách tưởng không được chat. Nay: nhắn riêng THÀNH CÔNG thì câu công khai CHỈ dùng 3 mẫu "đã nhắn tin riêng, anh/chị kiểm tra Messenger"; mẫu hotline + cửa hàng CHỈ dùng khi không nhắn riêng được.
- **v0.1.38 (21/10, chị Nga: khách bình luận bài viết chưa được bot trả lời):** tính năng TRẢ LỜI BÌNH LUẬN (có sẵn từ Bình Vị, mặc định TẮT, chưa có nút trên trang quản trị) nay bật bằng biến Railway: `PANCAKE_COMMENT=1` (bật), `PANCAKE_COMMENT_TEST=1` (chỉ trả lời bình luận có #tm — để thử) / `0` (trả lời mọi bình luận). Luồng: khách bình luận → bot nhắn riêng 1 tin tư vấn (Facebook chỉ cho 1 tin) → trả lời công khai 1 câu mời xem tin nhắn (mẫu chị Nga 13/10, không nêu giá) → khách nhắn lại thì luồng inbox thường tiếp quản. Trần 30 bình luận/giờ (`CMT_RATE_MAX`). Ngày 21/10: bot chạy thật lại lúc 12:20 sau khi chị Nga tạo tài khoản thanh toán riêng (thẻ tín dụng công ty) và nạp trả trước 5 triệu.
- **v0.1.37 (19/10 16:11, chị Nga: TÁCH bot Dương Sâm sang repo/bot riêng):** bản này CHỈ cho page Sâm Thái Minh = v0.1.33 + bảng CTKM Dương Sâm Linh Đan mới (dòng v0.1.35 bên dưới, áp dụng mọi nhãn — khách page Sâm Thái Minh hỏi mua Dương Sâm vẫn báo đúng quà). KHÔNG có: FAQ Dương Sâm của công ty, lời chào/xưng hô riêng page Dương Sâm, tách FAQ theo page, liều/nhà máy/suy thận cấp mới của Dương Sâm — các phần đó nằm ở bot Dương Sâm riêng. FAQ Dương Sâm trong bot này giữ nguyên 3 dòng cũ.
- **v0.1.35 (19/10 15:10, chị Nga gửi bảng CTKM DSLĐ 01/07–31/12/2026, mọi nhãn):** Dương Sâm Linh Đan khách mới: 1 hộp không quà; 2 hộp 1 Trà sâm 10 gói; 3 hộp 2 Trà 10 gói; 6 hộp khách chọn 1 chai Nước HSMO HOẶC 2 hộp Bổ Gan Thái Minh + 1 Trà 10 gói; 9 hộp 2 chai Nước HSMO. Khách cũ (có bảng riêng → bot tự chốt, không chuyển người): 4 hộp 2 Trà 10 gói + 1 Bổ Gan (Multi vitamin C đã hết → thay Bổ Gan); 7 hộp 1 chai Nước HSMO + 1 Bổ Gan 30 viên; 10 hộp 1 hộp DSLĐ + 1 Trà 10 gói; 15 hộp 1 hộp DSLĐ + 1 chai Nước HSMO; số lượng nằm giữa → quà mốc khách cũ thấp hơn (chị Nga 15:22: "để khách không thiệt quà": 5 = mốc 4, 8 = mốc 7, 11–14 = mốc 10), riêng 2, 3, 6, 9 hộp giữ quà bảng khách mới (nhiều hơn). FAQ nhóm 8: thông tin quà Bổ Gan Thái Minh (công dụng, đối tượng, ngày 4 viên chia 2 lần).
- **19/10 (bật thanh toán):** Gemini tài khoản mới bắt TRẢ TRƯỚC — chưa nạp → lỗi `gemini 402`. Trần cấp 1: 250 USD/tháng; lên cấp 2 khi đã chi ≥100 USD và ≥3 ngày. Chỉ quản trị tài khoản thanh toán (chị Hà) nạp được. ADMIN_KEY chỉ dùng chữ không dấu + số.
- **v0.1.33 (17/10 12:10, chạy thật gói miễn phí):** (1) Engine: lỗi quá giới hạn (429/RESOURCE_EXHAUSTED/503) → chờ 8 giây rồi 15 giây thử lại trước khi sang FALLBACK_MODEL. (2) Vòng gọi tool sau bị lỗi mà đã có phần chữ → vẫn gửi phần đã có + [HANDOFF … | | 2] thay vì im. (3) `pancake_adapter`: engine trả lỗi → gắn thẻ Bot + Người xử lý, giao ca, đánh chưa đọc, ghi chú "Bot lỗi AI…" và mark_returned để nhân viên trả lời ngay (trước đây khách bị bỏ lơ không ai biết).
- **v0.1.32 (17/10, chị Nga duyệt):** 4 câu chốt đơn mới sau báo giá Hồng sâm lát (`price_quote_hsvn`): ① chọn combo 1 tháng hay 3 tháng (câu chính), ② khuyên đủ liệu trình 3 tháng + COD, ③ chỉ cần nhắn tên/SĐT/địa chỉ, ④ mua biếu bố mẹ; xoay vòng, không lặp.
- **v0.1.31 (17/10, chạy thật):** tách TÊN GỌI từ tên Facebook (`call_name` trong `pancake_adapter.py`): giới tính lấy từ hồ sơ Pancake, không có thì theo tên đệm Thị/Văn; tên có dấu → chữ cuối, tên không dấu đảo kiểu Facebook ("Ngoan Do Thi") → chữ đầu khi phía sau có họ phổ biến. Hồ sơ gửi engine dòng `GỌI KHÁCH: "chị Ngoan"`; `_ensure_greeting` chào "Dạ Sâm Thái Minh chào chị Ngoan ạ.". Không chắc giới tính/tên → vẫn "anh/chị".
- **v0.1.30 (17/10):** `static/index.html` (trang chat thử): sửa lỗi bộ gõ tiếng Việt gửi lặp chữ cuối (bỏ qua Enter khi `isComposing`/keyCode 229, chặn tin chỉ là chữ cuối của tin vừa gửi trong 1,5 giây); menu model đổi sang Gemini Flash-Lite / Gemini 3.8 Flash; câu chào mở đầu bỏ "Em là chuyên viên tư vấn". `static/admin.html`: tiêu đề page "Sâm Thái Minh" (bỏ tên page Bình Vị), "3·Dược sĩ" → "3·Chuyên viên", log mới reopen/no_reopen/ảnh.
- **v0.1.29 (17/10, chị Nga test web):** lưới chặn LẶP `_drop_repeats` trong engine (áp dụng cả web lẫn Messenger): bỏ đoạn giống ≥85% đoạn bot đã gửi trong 6 tin gần nhất (vd gửi lại giá/cách dùng sau khi xin lỗi), 2 câu hỏi liền nhau chỉ giữ câu cuối. Prompt: khách sửa xưng hô ("tôi là chị") → xin lỗi 1 câu, đổi xưng hô, tiếp chủ đề, không gửi lại thông tin cũ.
- **16/10 16:45 — anh Huy CHỐT AI: Gemini 3.5 Flash-Lite** (`DEFAULT_MODEL=gemini_lite`, giống Bình Vị). Còn chờ: bật thanh toán Gemini (thẻ công ty), nâng gói Railway trước ~24/10.
- **v0.1.28 (16/10, 16:40, chị Nga):** câu chuẩn `diabetes_honey` — khách lo Nước HS có mật ong ảnh hưởng tiểu đường: "dùng được, vì Sâm Việt Nam có Rg1, Rd hỗ trợ kiểm soát đường huyết; chỉ cần dùng trước ăn 30 phút". Giờ làm việc chốt 08h–21h mọi ngày.
- **v0.1.27 (16/10, 16:30, chị Nga):** GIỜ LÀM VIỆC `PANCAKE_WORK_HOURS` (giờ VN, mặc định `08:00-21:00` — chị Nga chốt 16/10: mọi ngày kể cả T7, CN). Ngoài giờ: hồ sơ khách gửi engine thêm dòng "THỜI ĐIỂM: NGOÀI GIỜ LÀM VIỆC" → khi chuyển nhân viên / khách để SĐT / chốt đơn bot dùng câu chuẩn `off_hours`: "Dạ hiện đã ngoài giờ làm việc, nhân viên sẽ nhắn lại anh/chị từ 08h00 sáng mai ạ. Trong lúc chờ, anh/chị cần hỏi gì em hỗ trợ ngay ạ." Riêng CHỐT ĐƠN xong ngoài giờ: câu `off_hours_order` "Dạ em đã ghi nhận đơn hàng của anh/chị rồi ạ. Hiện đã ngoài giờ làm việc, sáng mai từ 08h00 bên em sẽ liên hệ xác nhận và hỗ trợ gửi đơn cho anh/chị ạ."
- **v0.1.26 (16/10, 16:20, chị Nga):** khách NÓI RÕ muốn chat với người → câu chuẩn `human_request`, chuyển ngay không bắt để SĐT ([HANDOFF: khách muốn chat với người | | 2]); ca này đặt cờ `no_reopen:<conv>` → KHÔNG tự mở lại cho bot sau 24h (khác ca bot tự chuyển). Chưa có câu ngoài giờ làm việc — chờ chị Nga chốt giờ làm việc.
- **v0.1.25 (16/10, 16:10, chị Nga):** MỞ LẠI CA ĐÃ CHUYỂN NGƯỜI — trước đây (thiết kế Bình Vị) ca đã trả về người thì bot rút vĩnh viễn, khách cũ hôm sau nhắn lại bot im. Nay nếu nhân viên KHÔNG gõ tay gì trong ca quá `PANCAKE_REOPEN_HOURS` giờ (mặc định 24; đặt 0 = tắt tính năng) thì lần tới khách nhắn, bot tiếp nhận lại (log `reopen`), thẻ "Người xử lý" cũ không còn chặn. Nhân viên gõ tay lại → bot rút như cũ; bot tự chuyển người lần nữa → tính lại mốc. Cài bằng cách bọc `db.pancake_is_blocked / pancake_is_human / pancake_claim_human / pancake_mark_returned` trong `pancake_adapter.py` (mốc `human_at:<conv>`, `reopen_at:<conv>` trong settings) — không sửa `db.py`. Ca cũ chưa có mốc giờ (trước bản này) → mở lại ngay khi khách nhắn.
- **v0.1.24 (16/10, 15:50):** (1) ẢNH KHÔNG HIỆN: content_id Pancake hết hạn sau vài giờ mà code cũ cache vĩnh viễn → khách chỉ thấy ô xám "meta_… Xem". Nay cache kèm mốc giờ, quá `PANCAKE_IMG_CID_TTL` (mặc định 1800 giây) thì upload lại. (2) Ảnh đã gửi trong hội thoại không gửi lại (lưu `imgs_sent:<conv>`), trừ khi khách báo không xem được / xin gửi lại. (3) Bỏ dòng đệm "Vâng chị X ạ" đứng đầu tin. (4) Đã bật Webhook Pancake 16/10 → `PANCAKE_POLL=0`.
- **v0.1.23 (16/10, 15:30):** Chị Nga sửa bảng an toàn trên tài liệu Bộ não 16/10: Dương Sâm huyết áp cao → hỏi chỉ số, ≤150 dùng được, >150 chuyển; Nước HS suy thận 3–4 → dùng được, hỏi bác sĩ trước; Hồng sâm lát mới ghép thận → chuyển chuyên viên (HANDOFF level 3, không còn ở nhóm absolute); hộp 50 gói ĐÃ CÓ HÀNG, không có CTKM.
- **v0.1.21 (16/10, chị Nga test trên Pancake):** (1) tiểu đường + Hồng sâm lát: bot lẫn với liều thuốc chống đông ("1/2 gói, nửa còn lại cất tủ lạnh") → KB + prompt ghi rõ 1 gói/ngày chia sáng 1/2 + trưa 1/2, cấm câu tủ lạnh; câu báo giá theo liều riêng. (2) Lưới chặn cuối `_fix_banned_phrases`: "thấm sâu" → "hấp thu tốt", "cải thiện tiểu đường" → "hỗ trợ kiểm soát đường huyết"; bỏ "thấm sâu" khỏi mẫu báo giá persona. (3) Tên Facebook không dấu/kiểu nước ngoài → không gọi tên, không gọi "chị + tên" khi chưa rõ giới tính. (4) Câu ghi nhận khi khách gửi trần SĐT (`PHONE_ACK`, `pancake_adapter.py`): "Dược sĩ bên em sẽ gọi lại" → "Chuyên viên tư vấn bên em sẽ gọi lại". Đã nối Pancake 16/10 bằng PANCAKE_POLL=1 (chưa có Webhook), chế độ thử #tm.
- **v0.1.20 (16/10, chị Nga):** mỗi khi mời chuyển sang Nước Hồng sâm (chê đắt, ngân sách hạn chế, xin dùng thử) → ƯU TIÊN mời **dạng túi** (gói 20 túi, giá + ưu đãi hsmo-tui từ tool); KHÔNG nhắc dạng chai, khách hỏi chai mới tư vấn chai 175ml. need_map `tiet_kiem_de_uong` đổi core sang túi. File đổi: `engine.py`, `tools_build/build_kb.py`, `brain/kb.json`, `brain/playbook.md`, test.
- **v0.1.19 (16/10, chị Nga test):** khách chê đắt KÈM ý thôi không mua ("đắt quá thôi", "thôi không mua nữa", "để sau") → mời NGAY Nước Hồng sâm mật ong (`price_objection_switch`), không đợi 2 lần thuyết phục, chưa xin SĐT; vẫn từ chối mới soft ask SĐT. Bỏ "chê đắt rồi thôi" khỏi danh sách S2 (soft ask). Đang tư vấn chính Nước HS mà chê đắt → gợi ý hộp 10 túi. File đổi: `engine.py`, `tools_build/build_kb.py`, `brain/kb.json`, `brain/playbook.md`, test.
- **v0.1.18 (16/10) — 2 lớp chặn trong code** (theo lỗi bot Bình Vị gặp với Gemini Flash-Lite, chị Trà/anh Na báo): (a) `engine.check_order_fields`: SĐT/địa chỉ đưa vào build_order phải xuất hiện trong tin khách (SĐT khớp số, địa chỉ ≥ 60% chữ) — không khớp thì bỏ trường, build_order trả `guard_notes` + `ready_to_confirm=False`, bot hỏi lại khách; (b) `engine.strip_internal`: bỏ đoạn có dấu hiệu nháp/kế hoạch nội bộ (tên tool, 'Thinking:', 'Tôi sẽ gọi...', thẻ <think>) trước khi gửi khách; số đoạn bỏ ghi vào debug `leak_dropped`. Test 16 ca. File đổi: `engine.py`, `tests/test_sam_12ca.py`, README.
- **15/10 — CHỐT AI: dùng Gemini** (anh Huy, vì bên Thái Minh đã so sánh). Trước khi nối Pancake: bật thanh toán Gemini (thẻ công ty), đặt `DEFAULT_MODEL=gemini` (3.8 Flash) + `FALLBACK_MODEL=gemini_lite`. `ANTHROPIC_API_KEY`, `MODEL_SONNET`, `MODEL_HAIKU` không cần. Đang hỏi chị Trà, anh Na bản Gemini bên Bình Vị dùng để đồng bộ.
- **v0.1.17 (15/10, góp ý anh Huy qua chị Nga — 16 mục):** bỏ "Thái Minh tự trồng", "gấp 3 lần sâm Hàn Quốc", "MR2 chiếm 50%", "chống khối u", "nguồn gốc minh bạch từ vườn đến nhà máy"; giá trị nói: MR2 sâm Hàn không có, công trình chuyển giao từ VIGH (Viện Nghiên cứu Sâm và Dược liệu Việt Nam), Hồng sâm dễ hấp thu/bảo quản hơn sâm tươi, kiểm soát nghiêm ngặt chất lượng đầu vào; câu ung thư, huyết áp (nói mềm), không có mùi sâm (tinh dầu vs saponin), tăng giá (giữ chất lượng đầu ra), chai nhựa (bỏ "cao cấp"), xác nhận đơn ("bên em sẽ gọi"), upsell (câu đệm "lời hơn mua lẻ"), người hay máy (trợ lý tư vấn, hỏi lại thì nói thật), cần chuyên môn (không nhắc dược sĩ); thăm vườn: Sìn Hồ farm, xin SĐT khách, bỏ homestay/số cá nhân; bảng an toàn: thuốc tây/kháng sinh cách 2 giờ, mất ngủ dùng sáng/trưa mọi sản phẩm, phình động mạch chủ khuyên hỏi bác sĩ (cho phép thì dùng), Dương/Long Sâm huyết áp cao/thấp chỉ dùng khi đã ổn định bằng thuốc, Long Sâm huyết áp chưa ổn định → chuyển, **đang cho con bú KHÔNG dùng bất kỳ sản phẩm nào**; FAQ mới: hóa đơn VAT (giá đã gồm VAT, cá nhân và công ty). Script mới trong kb: `no_ginseng_smell`, `vat_invoice`, `breastfeeding`. Câu nhận ảnh/PDF: "nhờ chuyên viên xem giúp". Test 15 ca. File đổi: `tools_build/build_kb.py`, `brain/*`, `engine.py`, `pancake_adapter.py`, `tests/test_sam_12ca.py`, README.
- **v0.1.16 (14/10, chị Nga duyệt bộ não trên tài liệu "Bộ não bot Sâm Thái Minh — bản duyệt"):** chào "Dạ Sâm Thái Minh chào anh/chị ạ", không xưng dược sĩ (anh Huy chốt 14/10), khách hỏi em là ai → chuyên viên tư vấn; tối đa 1 icon/dòng; không cho khách bóc hàng dùng thử; liệu trình cơ bản 3 tháng + câu chốt mới; câu giới thiệu 4 dòng mới (khoảng 31.000đ/ngày); Hồng sâm lát ngậm dưới lưỡi 3–5 phút; thêm gói Nước Hồng sâm túi 10 túi 330.000đ (chỉ khi khách hỏi); Hồng sâm lát 50 gói, Trà nguyên lá 40g hết hàng; Nước HS túi mua 1 không quà; ship Trà/Tam Sâm Đan/Đông trùng dưới 1 triệu 20.000đ (`shipping.threshold_*`); bảng an toàn Dương Sâm, Long Sâm mới (huyết áp, ung thư, chống đông ≥6 tháng... dùng được; có thai, cho con bú không; Long Sâm trẻ em không); Nước HS dùng được với chống đông ≥6 tháng; mẹ sau sinh dưới 6 tháng chưa dùng (flag mới `postpartum_lt6m`); tai biến do xuất huyết mọi trường hợp chuyển; **CTKM khách cũ** Hồng sâm lát hộp 14 gói (`programs.returning_customer`, build_order customer_type=returning tự chốt; sản phẩm khác chưa có bảng → chuyển nhân viên); điểm bán qua link samthaiminh.com/diem-ban; 2 vườn sâm (Lai Châu, Lâm Đồng); tin nhắc nhịp 2 có mẫu riêng cho Dương/Long Sâm (không nhắc nhà máy Thái Minh Hi-tech; Dương Sâm gửi 2 ảnh sản xuất Dương Sâm, Long Sâm gửi ảnh vườn); ảnh mới static/img: nha-may, nha-may-2, vuon-sam-lai-chau (chỉ khi khách tự hỏi chuyến thăm Thủ tướng), duong-sam-vien, duong-sam-dong-goi — nhớ thêm 5 mã này vào IMG_MAP trong main.py nếu muốn hiện trên web chat thử. Test: `tests/test_sam_12ca.py` nay 14 ca. File đổi: `tools_build/build_kb.py`, `brain/*`, `tools_core.py`, `engine.py`, `pancake_adapter.py`, `tests/test_sam_12ca.py`.
- Còn sót Bình Vị: chữ "BV" ở avatar và nhãn "Model mặc định (Sonnet)" trong `static/index.html` — chờ chị gửi file để sửa.

## 0b. v0.1.13 — chị Nga chốt 13/10/2026
| # | Chốt | Làm ở đâu |
|---|---|---|
| 1 | Khách nhắn → **1 phút sau** bot mới trả lời (khách nhắn thêm trong 1 phút thì gộp, tính 1 phút từ tin cuối). Chỉ trên page Facebook; web test trả lời ngay. Ngoại lệ giữ nguyên: khách gửi TRẦN SĐT → bot ghi nhận ngay và chuyển người gọi. | `pancake_adapter.py` `PANCAKE_BATCH_SECONDS` mặc định 60 (đã có từ v0.1.12) |
| 2 | **Tập trung tư vấn** Hồng sâm lát + Nước Hồng sâm (chai, túi), Dương Sâm, Long Sâm. Tam Sâm Đan, Trà sâm, Đông trùng (và Rượu sâm, Sâm tươi) chỉ khi khách hỏi. | `engine.py` rule 0 + 5j; `kb.json` role |
| 3 | Khách hỏi chung chung chưa rõ sản phẩm → **trả lời theo bài viết / quảng cáo khách bấm vào**. Khách vãng lai → page Sâm Thái Minh: Hồng sâm lát; page Dương Sâm Linh Đan: Dương Sâm Linh Đan. | `engine.py` `focus_block()` + ENV `PAGE_FOCUS_PRODUCT`; `pancake_adapter.py` `_save_origin`, `_focus_of`, ENV `POST_PRODUCT_MAP` |
| 4 | FAQ: chai 175ml là **chai nhựa** cao cấp (thực phẩm & dược phẩm), nhẹ, bền, chống va đập. Đã bỏ chữ "an toàn tuyệt đối" và "bạn" khỏi câu gốc (trái luật cấm từ + xưng hô). | `faq.md`, `kb.json` `scripts_approved.bottle_material`, `packaging` |
| 5 | **Huyết áp cao, thấp, ổn định hay chưa** đều dùng được Hồng sâm Thái Minh (lát, chai, túi) — hỗ trợ ổn định huyết áp. Thêm flag `hypotension`. Dương Sâm, Long Sâm giữ nguyên (huyết áp dao động chưa kiểm soát vẫn không dùng). | `build_kb.py` `BP_CAU`; `engine.py` 2b; `scripts_approved.bp_question` |
| 6 | **Bỏ câu "không phải thuốc, không thay thế thuốc chữa bệnh"** trong tư vấn thường. Chỉ khi khách nói đang dùng **thuốc tây** chữa bệnh nền → khuyên duy trì thuốc + dùng kết hợp sản phẩm Sâm để bồi bổ (1 lần). Khách hỏi thẳng "thay thuốc / bỏ thuốc được không" → vẫn trả lời thật: không thay thuốc. | `engine.py` 2 + 2b; `disclaimer_required=False`; `scripts_approved.maintain_meds` |

**Cấu hình mới (Railway Variables):**
- `POST_PRODUCT_MAP` — bài viết/quảng cáo → sản phẩm. Ví dụ: `1234567890=hsvn_lat; 9876543210=hsmo_tui; 120211234567890=duong_sam`. Số bên trái: ID bài viết (dãy số cuối link bài) hoặc Ad ID (Ads Manager). Bên phải: `hsvn_lat, hsmo_chai, hsmo_tui, duong_sam, long_sam, tam_sam_dan, dong_trung, tra_1700, tra_nguyen_la, ruou_sam, sam_tuoi`. Bài/quảng cáo không có trong danh sách → bot dùng mặc định của page.
- `PAGE_FOCUS_PRODUCT` — sản phẩm mặc định cho khách vãng lai. Không đặt = `hsvn_lat` (page Sâm Thái Minh). Service phục vụ page Dương Sâm Linh Đan đặt `duong_sam`.
- Bot hiện chỉ phục vụ **1 page / 1 service** (`PANCAKE_PAGE_ID`). Muốn nối thêm page Dương Sâm Linh Đan: tạo service thứ 2 từ cùng repo (Variables riêng: `PANCAKE_PAGE_ID`, `PANCAKE_PAGE_TOKEN`, `DB_PATH` riêng, `PAGE_FOCUS_PRODUCT=duong_sam`), và vì Pancake chỉ có 1 URL webhook cho cả gói, service Sâm đặt `PANCAKE_FORWARD_MAP=<page_id_Dương_Sâm>=https://<domain_service_2>/webhook/<path>` để chuyển tiếp.

## 0c. v0.1.14 — bộ quy tắc chị Nga gửi 13/10 chiều (đã trả lời đủ điểm A–J)
| Nhóm | Chốt | Làm ở đâu |
|---|---|---|
| Định dạng | Không quá 3 câu liền; đúng 1 câu hỏi mỗi lượt; từ mở đầu xoay vòng Dạ → Vâng anh/chị ạ → Anh/chị ơi → Dạ vâng → vào thẳng; icon 🎁 ✅ 😊 🌿 💚 ✨ tối đa 2/dòng; không bôi đậm (Messenger không hiển thị); không dùng lại nguyên câu; tránh "không thể"; kết thúc bằng cảm ơn/chúc sức khỏe | `engine.py` rule 8, `persona.md` |
| Ngữ cảnh | Khóa sản phẩm; xưng anh/chị theo lời khách | `engine.py` rule 8 |
| Ảnh (C) | Lượt đầu kèm 2 ảnh sản phẩm khách hỏi | `engine.py` 5f |
| Danh mục (D) | "Bên em có gì" → 4 dòng chính | `product_overview` (giữ) |
| Báo giá | Đúng 3 phần, 3 câu chốt luân phiên, không gói lẻ trừ chê đắt/dùng thử | `price_quote_hsvn`, 5p |
| Quà | Chê đắt mua 1 hộp: Trà 1700 10 gói (120k); combo 1 tháng: 1 hộp Trà 20 gói; combo 2 tháng: 2 hộp Trà 20 gói (380k); combo 3 tháng: 5 hộp Trà 10 gói | `build_kb.py` RULES |
| Ship | Hồng sâm dạng nước 1 chai/hộp 15k/20k, từ 2 freeship; mọi sản phẩm khác freeship từ 1 hộp; giao HN 1–2 ngày, tỉnh 3–4 ngày | `build_kb.py` shipping, `tools_core.py` build_order (sửa lỗi cũ: SKU freeship bị bỏ qua quà) |
| Upsell | 1 hộp → Combo 1 tháng; 2 hộp → Combo 2 tháng; 1 lần | `upsell_double`, `tools_core.py` |
| Chê đắt | Thuyết phục ≥2 lần ý khác nhau rồi mới chuyển Hồng sâm dạng nước (2 câu mẫu) | 5c, `price_objection_switch` |
| Khách khen | Không báo giá/ép combo; hỏi có muốn tham khảo ưu đãi khách quen → xin SĐT | `positive_feedback` |
| MR2 (A) | "MR2 chiếm tới 50% saponin toàn phần; nhiều nghiên cứu của Đại học Dược Kyoto (Nhật Bản) cho thấy MR2 hỗ trợ chống khối u ung thư, hỗ trợ ức chế quá trình phân bào của tế bào ung thư". Cấm "kháng ung thư", "trị liệu" | 2b, `disease_question` |
| Ung thư (F) | Người đang hóa trị/điều trị dùng được Hồng sâm (flag `cancer_treatment`); sản phẩm khác → chuyển dược sĩ | `build_kb.py` |
| Suy thận (G) | Độ 1–2 dùng được; độ 3–4 chuyển chuyên viên (`kidney_failure_1_2`, `kidney_failure_3_4`) | `build_kb.py`, `tools_core.py` |
| Bệnh khác (H) | Viêm khớp dạng thấp, tuyến giáp, tiền sử tai biến dùng được Hồng sâm; mới tai biến dùng thuốc chống đông < 6 tháng → chuyển; bệnh chưa có tài liệu → `disease_no_guidance` | `build_kb.py` |
| "mình" (I) | Mọi câu mẫu đổi "mình" → "anh/chị" | scripts |
| Hàng giả (J) | Trấn an bằng kiểm tra hàng trước khi trả tiền + giấy công bố + uy tín Thái Minh; không nói đổi trả | `reassure_fake` |
| Câu mẫu mới | `no_info`, `disease_no_guidance`, `deep_consult`, `accusation`, `closing`; mẫu xác nhận đơn (tên ngắn "Hồng sâm dạng lát/nước") | `build_kb.py`, `tools_core.py` |
| Bám khách (E) | 30 phút / +4 giờ / +12 giờ theo 3 mẫu của chị Nga, tự chèn tên + anh/chị; nhịp 2 kèm ảnh nhà máy + vườn sâm; nhịp 3 với sản phẩm khác Hồng sâm lát dùng câu chung | `pancake_adapter.py` `_fu_text`, `FU_IMG2` |

## 1. Đã thay đổi so với Bình Vị v1.0

| File | Thay đổi |
|---|---|
| `brain/kb.json` | Viết lại: 11 sản phẩm, 17 SKU, 42 dòng khuyến mại, chống chỉ định từng sản phẩm. **Sinh bằng `tools_build/build_kb.py` — không sửa tay.** |
| `brain/persona.md`, `playbook.md`, `faq.md` | Viết lại cho Sâm. Gồm xưng hô bác/ông/bà ↔ cháu, cách chọn sản phẩm theo người dùng, FAQ viết lại theo rule "hỗ trợ". |
| `tools_core.py` | Đa sản phẩm. `compliance_check` nhận `product_id` và có thêm verdict `NO_GUIDANCE` (tài liệu chưa có hướng dẫn → chuyển dược sĩ). `recommend` trả sản phẩm chính kèm phương án thay thế. `build_order` áp quà theo bậc số lượng của từng sản phẩm; chặn hàng hết; ship 15k/20k/freeship/"nhân viên xác nhận"; sâm tươi và rượu hũ chuyển nhân viên. |
| `engine.py` | Schema 4 tool và system prompt cho Sâm. Rule riêng: 0 (sản phẩm tập trung + trọng tâm, v0.1.13), 2b (tác dụng liên quan bệnh luôn dạng "hỗ trợ"; huyết áp; duy trì thuốc chỉ khi khách dùng thuốc tây), 2c (không nói dối là người khi khách hỏi thật), 5b (cửa hàng 92 Trung Kính), 5f (17 mã ảnh; ảnh có người là ảnh quảng cáo, không phải review), 5j (sản phẩm chỉ-khi-khách-hỏi), 5n (xưng cháu), 5p (ưu đãi chỉ khách mới). |
| `router.py` | Bộ từ khóa định tuyến Haiku/Sonnet cho Sâm. |
| `main.py`, `pancake_adapter.py`, `static/*.html` | Đổi tên hiển thị, `SECRET_PATH` và webhook path mặc định, câu theo đuổi. **`PANCAKE_PAGE_ID` không còn giá trị mặc định (bắt buộc đặt ENV).** Bỏ 7 ảnh Bình Vị, thay 17 ảnh Sâm (static/img, < 250KB/ảnh). v0.1.13: lưu nguồn bài viết/quảng cáo, truyền sản phẩm trọng tâm vào engine. |
| `providers.py`, `engine.py` (v0.1.9) | Thêm **Google Gemini** (`gemini` = Flash, `gemini_lite` = Flash-Lite) qua cổng tương thích OpenAI của Google. Giữ "thought signature" của Gemini 3 giữa các vòng tool, gửi ảnh dạng base64, che SĐT/địa chỉ trước khi gửi Google. Model chính lỗi → tự chạy lại bằng model dự phòng (`FALLBACK_MODEL`). Chế độ `auto` chọn được model mạnh/rẻ qua `ROUTER_STRONG`/`ROUTER_CHEAP`. |
| `brain/kb.json`, `faq.md`, `playbook.md` (v0.1.10, 24/09) | **Hồng sâm mật ong dạng chai dùng chung số công bố với dạng túi: 11/CNCTHAIMINH/2025.** Bot trả lời được số công bố cho cả chai và túi (trước đây dạng chai chuyển nhân viên). |
| `tests/test_samthaiminh_offline.py` | 136 kiểm tra offline: prompt, rule "hỗ trợ", ảnh, khớp schema, 13 ca an toàn, 9 ca đơn hàng, luồng Pancake, 19 ca Gemini (giả lập API). Chạy: `python3 tests/test_samthaiminh_offline.py`. Lưu ý v0.1.13: ca test nào kiểm "phải có câu không phải thuốc" hoặc "huyết áp chưa kiểm soát → NO_GUIDANCE với Hồng sâm" cần sửa theo chốt 13/10. |

Prompt caching: v0.1.15 tách system prompt thành khối tĩnh (lưu tạm) + khối riêng hội thoại sau `providers.CACHE_SPLIT`. Thêm luật mới thì đặt vào `build_system_prompt()` (phần tĩnh), KHÔNG chèn tên khách / dữ liệu riêng vào đó.

## 2. Quyết định đã chốt (chị Nga, 23/09–13/10/2026)
- **Tên bot:** Sâm Thái Minh.
- **Xưng danh:** chào bằng tên thương hiệu "Sâm Thái Minh", không xưng dược sĩ (14/10).
- **Xưng hô:** gọi anh/chị, xưng em; KHÔNG BAO GIỜ gọi khách là "mình". Khách tự xưng bác/ông/bà/cô/chú → gọi lại đúng danh xưng đó, xưng cháu.
- **Ưu đãi:** chỉ cho khách mới. Khách cũ → xin SĐT, chuyển nhân viên.
- **Nhà thuốc:** có nhưng ít điểm bán. Khuyến khích đặt qua page hoặc mua tại cửa hàng 92 Trung Kính, Cầu Giấy, Hà Nội.
- **Triển khai:** service Railway riêng.
- **Cho con bú:** Hồng sâm dạng nước dùng được; Hồng sâm lát, Tam Sâm Đan, Đông trùng hạ thảo không dùng.
- **Chống chỉ định:** Tam Sâm Đan và Đông trùng không dùng cho phụ nữ có thai, trẻ em (Tam Sâm Đan: dưới 12 tuổi).
- **Số liệu:** 84 saponin; MR2 lên tới 50% saponin toàn phần.
- **Hàng hóa:** Tam Sâm Đan chỉ bán hộp 30 viên. Trà nguyên lá chỉ còn loại 100g. Sâm tươi đang có hàng. Hotline Dương Sâm: 1800 8308.
- **13/10:** xem mục 0b (1 phút; tập trung 4 dòng; sản phẩm trọng tâm theo bài/quảng cáo/page; chai nhựa; huyết áp; bỏ câu "không phải thuốc" mặc định).

## 3. Cần nhãn hàng chốt thêm trước khi go-live
**Đã chốt 23/09:**
- Câu về bệnh luôn dạng "hỗ trợ ...". (Phần "+ không phải thuốc, không thay thế thuốc điều trị" đã bỏ theo chốt 13/10 — chỉ khuyên duy trì thuốc khi khách đang dùng thuốc tây.)
- Chuyến thăm của Thủ tướng (18/11/2023): chỉ trả lời khi khách tự hỏi.
- Khách hỏi thật "người hay máy": bot nói là trợ lý tư vấn tự động, mời gặp nhân viên.
- Đổi trả: bot không trả lời, chuyển chuyên viên.
- CTKM khách mới: 23/09/2026 → 31/12/2026 (hết hạn bot tự ngừng báo quà).
- Miễn phí ship: 2 chai Hồng sâm chai; toàn bộ Rượu sâm và Sâm tươi.
- Rượu sâm: chai 650ml 30 độ, bình 4 lít 32 độ; không bán cho dưới 18 tuổi, có thai, cho con bú.
- Đông trùng hạ thảo: dùng được từ 6 tuổi (liều cho trẻ do dược sĩ tư vấn).
- Giấy tờ: Dương Sâm 3496/2024/ĐKSP; Long Sâm 6193/2024/ĐKSP; Hồng sâm túi 11/CNCTHAIMINH/2025.
- Người duyệt nội dung: chị Nga.
- Hũ rượu 3,5 lít: 32 độ. Dương Sâm: tên thành phần theo bản công bố "Cao Tích dương".

**Đã chốt 24/09:**
- **Hồng sâm mật ong dạng nước: chai và túi dùng CHUNG số công bố 11/CNCTHAIMINH/2025** (thay cho ghi chú cũ "chai và túi khác số công bố").

**Còn mở:**
1. **Chị Nga duyệt nội dung** `brain/kb.json`, `persona.md`, `playbook.md`, `faq.md` (trạng thái: chờ duyệt).
2. **Số công bố Trà sâm (1700, nguyên lá) và Rượu sâm:** chưa có — bot chuyển nhân viên khi khách hỏi.
3. **Ảnh còn thiếu:** hũ/bình rượu nguyên cây; ảnh review khách thật (có đồng ý).
4. **Liều Đông trùng hạ thảo cho trẻ 6–11 tuổi** (nếu muốn bot tự trả lời thay vì chuyển dược sĩ).
5. **(13/10) Danh sách bài viết / quảng cáo → sản phẩm** để điền `POST_PRODUCT_MAP`.
6. **(13/10) Page Dương Sâm Linh Đan** có dùng bot này không (cần service thứ 2 + quyền page trên Pancake).
7. **(13/10, chị Nga giữ quyết định) Bỏ câu "không phải thuốc":** Dương Sâm, Long Sâm, Tam Sâm Đan, Đông trùng là thực phẩm bảo vệ sức khỏe — quy định quảng cáo yêu cầu câu này trên nội dung quảng cáo; nên xin pháp chế/anh Huy xác nhận tư vấn qua tin nhắn có cần không.
8. **(13/10, chưa trả lời) Huyết áp chưa ổn định:** cân nhắc giữ 1 câu an toàn khi khách tả triệu chứng huyết áp nguy hiểm (đau đầu dữ dội, chóng mặt, tức ngực, huyết áp rất cao) → khuyên đi khám ngay.

## 4. Triển khai — tài khoản RIÊNG của nhãn Sâm (chốt 23/09)
Bot Sâm chạy độc lập: Railway riêng, Pancake riêng, API key Claude riêng. **Không** đi qua hub/`PANCAKE_FORWARD_MAP` của Bình Vị (để trống biến này, trừ khi nối thêm page Dương Sâm Linh Đan của chính nhãn Sâm — xem mục 0b).

**A. Tạo tài khoản**
1. GitHub: tạo kho **Private** `samthaiminh-webchat`, tải toàn bộ thư mục này lên. Không đưa token/khóa vào code.
2. Railway (railway.app): đăng ký bằng tài khoản GitHub, chọn gói trả phí (gói dùng thử sẽ tắt service khi hết credit).
3. Claude API (console.anthropic.com): tạo tài khoản công ty, nạp tiền, tạo API key. Đặt giới hạn chi tiêu tháng để kiểm soát.
4. Pancake: tài khoản/gói riêng có quyền **Webhook + Public API**; đăng nhập bằng **Facebook** của người quản trị page Sâm (đăng nhập email thì token không thấy page).

**B. Dựng bot, test trên web (chưa cần Pancake)**
5. Railway → New → Deploy from GitHub repo → chọn kho → thêm Volume gắn `/data` → Settings → Networking → Generate Domain.
6. Variables: `ANTHROPIC_API_KEY`, `SECRET_PATH`, `ADMIN_KEY`, `WATCH_KEY` (chuỗi tự đặt, khó đoán), `DB_PATH=/data/samthaiminh.db`, `DEFAULT_MODEL=auto` → Deploy.
7. Mở `https://<domain>/c/<SECRET_PATH>` để chat thử; quản trị `https://<domain>/a/<ADMIN_KEY>`. Cả đội test + chạy guardrail 12 ca (viết lại ca 5, 7, 11 theo Sâm: mẹ cho con bú hỏi Hồng sâm lát; người dùng thuốc chống đông; "có chữa ung thư không").

**C. Nối page Facebook qua Pancake riêng**
8. Trong Pancake: thêm page Sâm; tạo 6 thẻ đúng tên (chốt 14/10): Bot, Bot chốt đơn, Người xử lý, ADR/Khiếu nại, Ko gửi được, Ko PH (không cần Nhóm người khi chạy 100%); lấy `page_access_token` ở Cài đặt → Công cụ (**không** bấm "Tạo Token"); lấy page ID và ID nhân viên trực, dược sĩ.
9. Railway Variables thêm: `PANCAKE_PAGE_ID`, `PANCAKE_PAGE_TOKEN`, `PANCAKE_ASSIGN_IDS`, `PANCAKE_PHARMACIST_IDS`, `PANCAKE_WEBHOOK_PATH` (chuỗi khó đoán), `PANCAKE_TEST_ONLY=1`, `PANCAKE_TEST_KEYWORD=#tm`, `POST_PRODUCT_MAP` (v0.1.13) → Deploy.
10. Trong Pancake bật Webhook, dán địa chỉ nhận tin: `https://<domain>/webhook/<PANCAKE_WEBHOOK_PATH>`; bật sự kiện "Tin nhắn" và "Hội thoại".
11. Chạy thử 1–2 ngày: nhân viên nhắn page từ nick cá nhân, tin bắt đầu `#tm`; kiểm tra trả lời, thẻ, giao ca, ảnh. Thử thêm: bấm "Gửi tin nhắn" từ 1 bài viết đã khai báo trong `POST_PRODUCT_MAP`, hỏi "giá bao nhiêu" → bot phải báo giá đúng sản phẩm của bài.
12. Go-live: `PANCAKE_TEST_ONLY=0`, bật A/B 50/50 trên trang quản trị. Sự cố → nút tắt khẩn (kill switch) trên trang quản trị.

**Chi phí tham khảo (tài liệu bàn giao Bình Vị):** Claude API khoảng 145–155 USD/tháng cho ~10.000 hội thoại khi bật prompt caching (đã bật sẵn); Railway khoảng 10–20 USD/tháng. Giá Pancake theo gói — hỏi Pancake.

## 4b. Dùng Gemini cho rẻ (tuỳ chọn, thêm 23/09)
Bot chạy được bằng Claude, Gemini, hoặc **lai** cả hai. Đổi bằng biến Railway, không sửa code.

**Lấy khoá Gemini**
1. Vào aistudio.google.com, đăng nhập Google của công ty → Get API key → Create API key (tạo trong một Google Cloud project mới).
2. **Bật thanh toán (Paid tier)** cho project đó. Bản miễn phí: Google được dùng nội dung để cải tiến sản phẩm → không dùng cho tin nhắn khách thật. Bản trả phí thì không.
3. Đặt ngân sách/cảnh báo chi tiêu trong Google Cloud Billing.

**3 cách cấu hình (Railway Variables)**
| Cách | Biến | Ghi chú |
|---|---|---|
| A. Lai (khuyên dùng) | `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `DEFAULT_MODEL=auto`, `ROUTER_STRONG=sonnet`, `ROUTER_CHEAP=gemini_lite` | Câu đơn giản (giá, liều, cảm ơn) → Gemini Flash-Lite rẻ nhất. Câu an toàn, bệnh nền, phản đối, chốt đơn → Claude. |
| B. Toàn Gemini | `GEMINI_API_KEY`, `DEFAULT_MODEL=gemini_auto` (hoặc `gemini`) | Rẻ nhất. Nên giữ thêm `ANTHROPIC_API_KEY` + `FALLBACK_MODEL=sonnet` để Google lỗi thì Claude đỡ. |
| C. Toàn Claude | như mục 4 | Như hiện tại. |

Biến phụ: `GEMINI_MODEL` (mặc định `gemini-3.8-flash`), `GEMINI_MODEL_LITE` (mặc định `gemini-3.5-flash-lite`), `GEMINI_REASONING=low`, `GEMINI_MAX_TOKENS=4096`, `PII_MASK_EXTERNAL=1` (giữ nguyên: che SĐT/địa chỉ trước khi gửi Google).

**Giá tham khảo (USD / 1 triệu token, tra ngày 23/09/2026 — kiểm tra lại trước khi chốt)**
| Model | Vào | Vào đã cache | Ra |
|---|---|---|---|
| Claude Sonnet 4.5 (mặc định hiện tại) | 3 | 0,30 | 15 |
| Claude Sonnet 5 | 2 | 0,20 | 10 |
| Claude Haiku 4.5 | 1 | 0,10 | 5 |
| Gemini 3.8 Flash — đến 31/12/2026 | 0,75 | 0,075 | 3,75 |
| Gemini 3.8 Flash — từ 01/01/2027 | 1,50 | 0,15 | 7,50 |
| Gemini 3.5 Flash-Lite | 0,30 | 0,03 | 2,50 |

Ước tính thô mỗi lượt gọi (prompt ~15k token đã cache + 2k token mới; trả lời ~300 token, Gemini cộng thêm token "suy nghĩ"): Sonnet 4.5 ≈ 1,5 cent; Haiku ≈ 0,5; Gemini Flash ≈ 0,6 (năm 2027 ≈ 1,1); Flash-Lite ≈ 0,3. Nghĩa là: **Flash-Lite rẻ ~5 lần Sonnet; Gemini Flash chỉ ngang Haiku**. Số thật phụ thuộc cách tách token tiếng Việt và tỉ lệ cache — chạy thử 1 tuần rồi đọc hoá đơn thật.

**Bắt buộc trước khi cho Gemini trả lời khách thật**
- Prompt và guardrail được viết và thử trên Claude. Chạy lại 12 ca guardrail + ~20 câu hỏi thật trên web test cho **từng** model định dùng (chọn model trong ô "Model AI"). Soi kỹ: chữ "hỗ trợ" khi nói về bệnh, chặn đúng có thai/cho con bú/trẻ em, không nêu quà khi chưa biết khách mới, xưng hô không "mình", thẻ [HANDOFF]/[IMG].
- Chưa chạy với API Gemini thật (test offline dùng API giả lập). Lỗi hay gặp nhất là mất "thought signature" ở vòng tool thứ 2 — đã xử lý, nhưng cần xác nhận trên web test.

## 5. Kiểm tra đã làm
**23/09/2026**
- **Khuyến mại:** 43/43 dòng trong `kb.json` khớp bảng Excel, gồm giá combo = số lượng × đơn giá, quà và freeship. (Từ 25/09 còn 42 dòng sau khi đổi bảng quà Hồng sâm lát theo brief.)
- **Test offline:** 136/136 PASS (gồm 19 ca Gemini giả lập).
- **Chưa test được:** chưa chạy với Claude API thật (môi trường dựng không có API key), chưa chạy server FastAPI. Hai phần này làm ở bước 6 trên web test.

**24/09/2026 (v0.1.10)**
- Sinh lại `kb.json` bằng `build_kb.py`: 11 sản phẩm, 17 SKU, khuyến mại không đổi; `hsmo_chai.registration` và `hsmo_tui.registration` cùng ghi 11/CNCTHAIMINH/2025.

**13/10/2026 (v0.1.13)**
- Sinh lại `kb.json`: 11 sản phẩm, 17 SKU, 42 dòng khuyến mại (không đổi); 5 dòng chính (`hsvn_lat, hsmo_chai, hsmo_tui, duong_sam, long_sam`) và 6 dòng chỉ-khi-khách-hỏi; Hồng sâm lát/chai/túi có CAUTION "dùng được" cho `hypertension, hypotension, bp_uncontrolled`.
- Kiểm tra bằng module giả lập (không gọi API thật): web test → sản phẩm trọng tâm mặc định `hsvn_lat`; `PAGE_FOCUS_PRODUCT=duong_sam` → Dương Sâm; khách từ bài viết có trong `POST_PRODUCT_MAP` → đúng sản phẩm (cả dạng `PAGEID_POSTID`); khách từ Ad ID → đúng sản phẩm; bài không khai báo → mặc định page; setting admin `post_product_map` đè ENV; `BATCH_SECONDS=60`. `engine.py`, `pancake_adapter.py` biên dịch không lỗi.
- Chưa chạy bộ 136 test offline (bộ code nguồn đầy đủ không có trong phiên này) — chạy lại khi ghép vào repo.

**13/10/2026 chiều (v0.1.14)**
- `kb.json` sinh lại: 42 dòng khuyến mại; freeship mọi SKU trừ `hsmo-chai`, `hsmo-tui`; flag mới `cancer_treatment, kidney_failure_1_2, kidney_failure_3_4, rheumatoid_arthritis, thyroid, stroke_history`.
- `build_order` kiểm 9 ca: 1 hộp lát (freeship, không quà, có lời mời lên 2 hộp); 1 hộp chê đắt (Trà 10 gói); 2 hộp (Trà 20 gói, 2.840.000đ, freeship); chai 1 tỉnh 20k, chai 1 Cầu Giấy 15k, chai 2 freeship + quà; túi 1 20k + quà; trà 1 freeship; Dương Sâm 1 freeship.
- `compliance_check` kiểm 12 ca: huyết áp thấp/chưa ổn định Hồng sâm → CAUTION dùng được; Dương Sâm huyết áp chưa ổn định → BLOCK; ung thư đang điều trị Hồng sâm → CAUTION dùng được, Long Sâm → CAUTION chuyển dược sĩ; suy thận 1–2 → dùng được, 3–4 → chuyển; tuyến giáp Dương Sâm → NO_GUIDANCE.
- Tin bám khách: kiểm điền tên "Chị Trịnh Thị Chanh" / "Anh/chị", nhịp 3 theo sản phẩm trọng tâm.

## 0d. v0.1.15 — 13/10 tối (chờ chị Nga duyệt nội dung)
- Huyết áp: bot giải thích "Hồng sâm có thể hỗ trợ điều hòa tuần hoàn và chức năng mạch máu, giảm độ cứng của động mạch, từ đó hỗ trợ giúp ổn định huyết áp; người đang dùng thuốc huyết áp vẫn dùng thuốc hằng ngày theo chỉ định bác sĩ".
- Tai biến do xuất huyết (flag `stroke_hemorrhagic`) → chuyển chuyên viên, mọi sản phẩm.
- Bình luận dưới bài: nhắn riêng (chào, trả lời, mời mua nếu phù hợp) + trả lời công khai (mời xem tin nhắn / mẫu hotline 1800 1120 + cửa hàng 92 Trung Kính). Nhắn riêng lỗi → chỉ trả lời công khai mẫu hotline. Vẫn TẮT mặc định (`pancake_comment`).
- **Đẩy đơn lên Nhanh** (`nhanh.py`): khách xác nhận đơn (HANDOFF level 1) → tạo đơn qua Open API v3 `POST https://pos.open.nhanh.vn/v3.0/order/add` (trạng thái mặc định Mới, chuyên viên vẫn gọi xác nhận). Quà map được mã thì lên đơn giá 0đ, không map được thì ghi ở ghi chú. Chống trùng bằng `channel.appOrderId`. Hội thoại #tm không đẩy (trừ `NHANH_ALLOW_TEST=1`). Lỗi → ghi log `nhanh_fail` + thêm ca chuyển người "Đẩy đơn Nhanh lỗi — lên đơn tay".
  - Cài đặt: (1) tài khoản giám đốc Nhanh bật "Cho phép kết nối Open API" (Cài đặt chung > Cài đặt Open API); (2) tạo app ở https://open.nhanh.vn, Redirect URL = `https://<domain bot>/` ; lấy appId, secretKey; (3) mở `https://nhanh.vn/oauth?appId=<appId>&returnLink=https://<domain bot>/`, đăng nhập, cấp quyền đơn hàng + kho → trình duyệt chuyển về địa chỉ có `?accessCode=...`; (4) trong 10 phút đặt Railway Variables `NHANH_APP_ID`, `NHANH_SECRET_KEY`, `NHANH_ACCESS_CODE`, `NHANH_PRODUCT_MAP`, `NHANH_ENABLED=1` → Deploy; bot tự đổi lấy accessToken (hạn 1 năm) — xem log `nhanh_token`.
  - Chưa kiểm với tài khoản Nhanh thật. Địa chỉ đang gửi dạng chữ (không kèm mã tỉnh/huyện/xã); nếu Nhanh đòi mã địa chỉ thì cần thêm bước tra mã. Tài liệu API Nhanh chuyển sang https://developers.nhanh.group từ 23/09/2026 — kiểm lại đường dẫn khi cài.
