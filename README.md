# Sâm Thái Minh — Chatbot tư vấn & chốt đơn

Bot tư vấn bán hàng cho page Facebook **Sâm Thái Minh** (qua Pancake), xưng "dược sĩ tư vấn của Sâm Thái Minh". Nhân bản khung kỹ thuật từ bot Bình Vị Thái Minh v1.0 (Dược phẩm Thái Minh), phần nội dung ("bộ não") viết mới cho 11 sản phẩm Sâm.

- **Phiên bản:** v0.1.16 (14/10/2026) — chị Nga duyệt nội dung bộ não.
- **Đọc trước:** `README-samthaiminh.md` (mọi quyết định riêng của Sâm, lịch sử phiên bản, cấu hình Railway, Nhanh).
- **Bộ não:** thư mục `brain/` — `persona.md` (giọng văn), `playbook.md` (quy trình bán), `faq.md`, `kb.json` (sản phẩm, giá, quà, bảng an toàn, câu chuẩn).
- **Sửa giá / quà / bảng an toàn:** sửa `tools_build/build_kb.py` rồi chạy lại để sinh `brain/kb.json` — không sửa tay `kb.json`.
- **Kiểm tra:** `python3 tests/test_sam_12ca.py` (không tốn API); phiếu thử tay `tests/ca-thu-tay-12ca.md`.
- **Chạy:** Railway (project `astonishing-freedom`, service `web`). Biến chính: `ANTHROPIC_API_KEY`, `DEFAULT_MODEL`, `SECRET_PATH`, `ADMIN_KEY`, `DB_PATH`, `PANCAKE_PAGE_ID`, `PANCAKE_PAGE_TOKEN`, `PAGE_FOCUS_PRODUCT`, `POST_PRODUCT_MAP`, `NHANH_*`.

Các file `README-huong-dan.md`, `AI-README.md`, `docs/01–05` là tài liệu gốc của bot Bình Vị — vẫn đúng cho phần khung kỹ thuật (Pancake, gom tin, thẻ chuyển người, A/B, kill switch).
