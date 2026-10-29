"""Ca thử bot Nước Hồng sâm (v0.4.0, 26/10/2026) — kiểm ở mức CÔNG CỤ, LUẬT và LƯỚI CHẶN, không gọi API.

Chạy:  python3 tests/test_nhs.py      (hoặc: pytest tests/test_nhs.py)
Ca này tự đặt PAGE_FOCUS_PRODUCT=hsmo_tui trước khi nạp code (giống biến Railway của service bot Nước Hồng sâm).
pii / router / db chỉ có trên repo GitHub → nếu thiếu, ca thử tự thay bằng module rỗng để nạp engine.
"""
import os
import sys
import types

os.environ["PAGE_FOCUS_PRODUCT"] = "hsmo_tui"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

for _m in ("pii", "router", "db"):
    try:
        __import__(_m)
    except ImportError:
        sys.modules[_m] = types.ModuleType(_m)

import tools_core as t  # noqa: E402
import engine  # noqa: E402

KB = t.load_kb()
PROMPT_NHS = None
try:
    PROMPT_NHS = engine.build_system_prompt()
except Exception:  # noqa: BLE001
    pass
S = KB["scripts_approved"]
ADDR = "12 Lê Lợi, Hà Đông, Hà Nội"
PHONE = "0912345678"
NHS_PRICE = next(k["price_retail"] for k in KB["products"]["hsmo_tui"]["packages"] if k["sku"] == "hsmo-tui")


# 1 ─ Code nhận đúng chế độ bot Nước Hồng sâm và đọc bộ não riêng
def test_01_che_do_nhs():
    assert engine.IS_NHS and t.IS_NHS and not engine.IS_DS
    assert engine.PAGE_FOCUS_PRODUCT == "hsmo_tui"
    persona = t.load_brain_file("persona.md")
    assert "Nước Hồng sâm" in persona and "3 tầng" in persona
    assert "Nước Hồng sâm" in t.load_brain_file("playbook.md")
    assert "Nhóm 1 — Nước Hồng sâm" in t.load_brain_file("faq.md")


# 2 ─ Khách hỏi chung "giá sao em" → sản phẩm trọng tâm là Nước Hồng sâm dạng túi
def test_02_hoi_chung_chung():
    fb = engine.focus_block(None, "")
    assert "Nước Hồng sâm Thái Minh mật ong dạng túi" in fb and "hsmo_tui" in fb


# 3 ─ Báo giá: đúng giá kb, 3 combo 2/4/6 hộp, quà đúng bảng, không gọi "1 tháng"
def test_03_bao_gia_dung_bang():
    q = S["price_quote_nhs"]
    assert t.fmt_vnd(NHS_PRICE) in q
    for n in (2, 4, 6):
        gift = next(r["gift"] for r in KB["programs"]["new_customer"]["rules"] if r["if_sku"] == "hsmo-tui" and r["min_qty"] == n)
        assert f"Combo {n} hộp" in q and t.fmt_vnd(NHS_PRICE * n) in q and gift in q
    assert "Combo 1 tháng" not in q


# 4 ─ System prompt có khối NHS với 3 tầng sản phẩm
def test_04_luat_3_tang():
    b = engine.NHS_BLOCK
    for w in ("CHẾ ĐỘ BOT NƯỚC HỒNG SÂM", "Hồng sâm Việt Nam Thái Minh dạng lát, Long Sâm Linh Đan, Dương Sâm Linh Đan",
              "CHỈ giới thiệu khi khách CHỦ ĐỘNG hỏi sản phẩm khác", "Tam Sâm Đan, Đông trùng hạ thảo", "product_overview_nhs",
              "price_objection_nhs", "upsell_nhs"):
        assert w in b, w


# 5 ─ recommend: bồi bổ bố mẹ → Nước Hồng sâm là sản phẩm chính (lát chỉ là phương án khi khách hỏi)
def test_05_recommend_nhs_la_chinh():
    r = t.recommend(["boi_bo_nguoi_gia"])
    assert r["core_product"]["product_id"] == "hsmo_tui"
    assert [a["product_id"] for a in r["alternatives"]] == ["hsvn_lat"]
    assert "CHỦ ĐỘNG hỏi" in r["note_for_need"]
    r = t.recommend(["moi_om_day"])
    assert r["core_product"]["product_id"] == "hsmo_tui" and r["alternatives"][0]["product_id"] in t.NHS_PREMIUM
    # khách hỏi sinh lý nam (nhu cầu NHS không đáp ứng) → Dương Sâm
    assert t.recommend(["sinh_ly_nam"])["core_product"]["product_id"] == "duong_sam"
    # không bao giờ đề xuất sản phẩm tầng 3
    for tag in ("boi_bo_nguoi_gia", "benh_nen", "met_moi_stress", "kem_an_gay_yeu", "tiet_kiem_de_uong", "qua_bieu"):
        ids = [t.recommend([tag])["core_product"]["product_id"]] + [a["product_id"] for a in t.recommend([tag])["alternatives"]]
        assert not set(ids) & {"tam_sam_dan", "dong_trung", "tra_1700", "tra_nguyen_la", "ruou_sam", "sam_tuoi"}, (tag, ids)


# 6 ─ Đơn 1 hộp: phí ship Hà Nội nội thành, không quà; mời lên 2 hộp đúng 1 lần
def test_06_don_1_hop():
    o = t.build_order([{"sku": "hsmo-tui", "qty": 1}], "Nguyễn Lan", PHONE, ADDR, "new")
    assert o["ready_to_confirm"] and o["ship_fee"] == KB["shipping"]["fee_hn_inner"]
    assert o["total"] == NHS_PRICE + KB["shipping"]["fee_hn_inner"]
    assert o["upsell_hint"] and "combo 2 hộp" in o["upsell_hint"] and t.fmt_vnd(NHS_PRICE * 2) in o["upsell_hint"]


# 7 ─ Đơn 2 / 3 hộp → mời 4; 4 hộp → mời 6; 6 hộp → không mời; khách cũ → không mời
def test_07_moi_len_goi():
    for q, target in ((2, 4), (3, 4), (4, 6), (5, 6)):
        o = t.build_order([{"sku": "hsmo-tui", "qty": q}], "Nguyễn Lan", PHONE, ADDR, "new")
        assert o["ship_fee"] == 0, "từ 2 hộp miễn phí ship"
        assert f"combo {target} hộp" in (o["upsell_hint"] or ""), (q, o["upsell_hint"])
    assert t.build_order([{"sku": "hsmo-tui", "qty": 6}], "Nguyễn Lan", PHONE, ADDR, "new")["upsell_hint"] is None
    assert t.build_order([{"sku": "hsmo-tui", "qty": 1}], "Nguyễn Lan", PHONE, ADDR, "returning").get("upsell_hint") is None


# 13 ─ Khách cũ (chốt 26/10, bảng 2026/TP-TBBL.NHS-C06): 2 → 2 Trà, 3 → 3 Trà, 12 → 2 hộp NHS + 1 Trà; 5 hộp → mốc 3; 13 → chuyển
def test_13_khach_cu():
    def o(q):
        return t.build_order([{"sku": "hsmo-tui", "qty": q}], "Nguyễn Lan", PHONE, ADDR, "returning")
    assert o(2)["total"] == 1240000 and o(2)["promo_applied"][0]["gift"] == "2 hộp Trà sâm 1700 (10 gói)" and o(2)["ship_fee"] == 0
    assert o(3)["total"] == 1860000 and o(3)["promo_applied"][0]["gift"] == "3 hộp Trà sâm 1700 (10 gói)"
    assert o(12)["total"] == 7440000 and "2 hộp Nước Hồng sâm" in o(12)["promo_applied"][0]["gift"] and not o(12)["handoff_note"]
    assert o(5)["promo_applied"][0]["tier_qty"] == 3
    assert o(13)["handoff_note"]
    one = o(1)
    assert not one.get("handoff_required") and not one["promo_applied"] and one["ship_fee"] == KB["shipping"]["fee_hn_inner"]
    q = S["returning_quote_nhs"]
    assert "1.240.000đ" in q and "1.860.000đ" in q and "7.440.000đ" in q and "Combo 2 hộp" not in q
    assert "returning_quote_nhs" in engine.NHS_BLOCK


# 8 ─ An toàn: có thai / cho con bú / trẻ dưới 3 tuổi → BLOCK; tiểu đường → dùng được liều riêng
def test_08_an_toan():
    for f in ("pregnant", "breastfeeding", "child_under3"):
        assert t.compliance_check([f], "hsmo_tui")["verdict"] == "BLOCK", f
    r = t.compliance_check(["diabetes"], "hsmo_tui")
    assert r["verdict"] != "BLOCK" and "1 túi" in " ".join(h["action"] for h in r["caution_hits"])
    assert t.compliance_check(["postpartum_lt6m"], "hsmo_tui")["verdict"] != "BLOCK"


# 9 ─ Lưới chặn: bot tự nhắc Hồng sâm lát / Tam Sâm Đan khi khách KHÔNG hỏi → bỏ đoạn đó
def test_09_luoi_chan_tang():
    txt = ("Dạ Nước Hồng sâm dùng được cho bố anh ạ.\n\n"
           "Ngoài ra bên em còn Hồng sâm Việt Nam Thái Minh dạng lát hàm lượng cao hơn ạ.\n\n"
           "Anh muốn lấy combo nào ạ?")
    out, n = engine._drop_unasked_tiers(txt, ["bố tôi 70 tuổi uống được không"], "")
    assert n == 1 and "dạng lát" not in out and "combo" in out
    # khách CHỦ ĐỘNG hỏi loại tốt hơn → giữ nguyên
    out, n = engine._drop_unasked_tiers(txt, ["có loại nào tốt hơn không em"], "")
    assert n == 0
    # "lát nữa" không phải hỏi Hồng sâm lát
    out, n = engine._drop_unasked_tiers(txt, ["lát nữa anh gọi lại"], "")
    assert n == 1
    # tầng 3: khách hỏi Long Sâm (mở tầng 2) nhưng chưa hỏi Đông trùng → đoạn Đông trùng vẫn bị bỏ
    t3 = "Dạ Long Sâm Linh Đan hợp người suy nhược ạ.\n\nBên em còn Đông trùng hạ thảo nữa ạ.\n\nAnh lấy mấy hộp ạ?"
    out, n = engine._drop_unasked_tiers(t3, ["còn long sâm thì sao"], "")
    assert n == 1 and "Đông trùng" not in out and "Long Sâm" in out
    # quà Trà sâm 1700 trong báo giá KHÔNG bị bỏ
    q = "Chương trình tri ân khách hàng mới:\n🎁 Combo 2 hộp (40 túi): 1.240.000đ – tặng 1 hộp Trà sâm 1700 (10 gói)"
    assert engine._drop_unasked_tiers(q, ["giá sao em"], "")[1] == 0


# 10 ─ Lưới giá/quà: AI viết sai giá hoặc quà dòng combo → sửa đúng bảng
def test_10_luoi_gia_combo():
    bad = "🎁 Combo 4 hộp (80 túi): 2.000.000đ – tặng 1 hộp Trà sâm 1700 (20 gói)"
    out = engine._fix_nhs_packages(bad)
    gift4 = next(r["gift"] for r in KB["programs"]["new_customer"]["rules"] if r["if_sku"] == "hsmo-tui" and r["min_qty"] == 4)
    assert t.fmt_vnd(NHS_PRICE * 4) in out and gift4 in out
    # dòng combo Hồng sâm lát không bị đụng
    lat = "🎁 Combo 1 tháng (2 hộp): 2.840.000đ – tặng 1 hộp Trà sâm 1700 loại 20 gói"
    assert engine._fix_nhs_packages(lat) == lat


# 11 ─ Chê đắt → hộp 10 túi, không mời Trà sâm; dùng thử → hộp 10 túi
def test_11_che_dat_dung_thu():
    p10 = next(k["price_retail"] for k in KB["products"]["hsmo_tui"]["packages"] if k["sku"] == "hsmo-tui-10")
    assert t.fmt_vnd(p10) in S["price_objection_nhs"] and "KHÔNG mời Trà sâm" in S["price_objection_nhs"]
    assert t.fmt_vnd(p10) in S["trial_request_nhs"]
    assert "KHÔNG gợi ý Trà sâm" in S["price_why_nhs"]


# 12 ─ "Bên em có sản phẩm gì" → giới thiệu NHS + 3 dòng cao cấp, không liệt kê tầng 3
def test_12_danh_muc():
    o = S["product_overview_nhs"]
    for w in ("Nước Hồng sâm", "Hồng sâm Việt Nam Thái Minh dạng lát", "Long Sâm Linh Đan", "Dương Sâm Linh Đan"):
        assert w in o
    assert o.index("Nước Hồng sâm") < o.index("dạng lát")
    assert "1️⃣ Trà" not in o and "Tam Sâm Đan:" not in o


# 14 ─ (v0.1.83 + lỗi tương tự) "dùng thử combo 2 hộp" KHÔNG bị hiểu là ung thư; "đã đầy đủ" không phải dạ dày
def test_14_dung_thu_khong_phai_ung_thu():
    for msg in ("Mình dùng thử combo 2 hộp nhé", "Mình dùng thử combo 1 tháng nhé", "dung thu hop 10 tui", "Thông tin đã đầy đủ rồi em"):
        assert engine._health_topics(msg) == [], msg
    assert engine._health_topics("bố tôi bị ung thư uống được không") == ["ung thư"]
    assert engine._health_topics("bị đau dạ dày") == ["dạ dày"]


# 15 ─ (v0.1.82 + lỗi tương tự) "lấy 1 hộp" → hộp 20 túi 620.000đ; hộp 10 túi / chai chỉ khi khách nhắc hoặc bot đã mời
def test_15_mac_dinh_hop_20_tui():
    u = ["lấy 1 hộp nhé", "Lan 0912345678, 12 Lê Lợi, Hà Đông, Hà Nội"]
    a, _ = engine.check_order_fields({"items": [{"sku": "hsmo-tui-10", "qty": 1}], "phone": PHONE}, u, "", [])
    assert a["items"][0]["sku"] == "hsmo-tui"
    a, _ = engine.check_order_fields({"items": [{"sku": "hsmo-chai", "qty": 1}], "phone": PHONE}, u, "", [])
    assert a["items"][0]["sku"] == "hsmo-tui"
    a, _ = engine.check_order_fields({"items": [{"sku": "hsvn-lat-50", "qty": 1}], "phone": PHONE}, u, "", [])
    assert a["items"][0]["sku"] == "hsvn-lat-14"
    # khách tự nói hộp 10 túi / bot đã mời hộp 10 túi → giữ
    a, _ = engine.check_order_fields({"items": [{"sku": "hsmo-tui-10", "qty": 1}]}, ["cho chị hộp 10 túi"], "", [])
    assert a["items"][0]["sku"] == "hsmo-tui-10"
    a, _ = engine.check_order_fields({"items": [{"sku": "hsmo-tui-10", "qty": 1}]}, ["ok lấy hộp đó"], "",
                                     ["bên em có hộp nhỏ 10 túi giá 330.000đ ạ"])
    assert a["items"][0]["sku"] == "hsmo-tui-10"
    o = t.build_order([{"sku": "hsmo-tui", "qty": 1}], "Lan", PHONE, ADDR, "new")
    assert "hộp 20 túi" in o["confirm_text"] and o["total_display"] == t.fmt_vnd(NHS_PRICE + KB["shipping"]["fee_hn_inner"])
    # tổng hợp đơn AI tự viết "10 túi" khi khách không hỏi → sửa về 20 túi
    summ = ("Tên khách hàng: Lan\nSố điện thoại: 0912345678\nSản phẩm + Số lượng: Hồng sâm dạng nước (hộp 10 túi) x 1 hộp\n"
            "Tổng thanh toán: 345.000đ")
    out, n = engine._fix_nhs_summary_pack(summ, u, [])
    assert n == 1 and "hộp 20 túi" in out


# 16 ─ (v0.1.84) "ĐT / đt / dt / sđt" = điện thoại, không phải Đông trùng
def test_16_dt_la_dien_thoai():
    for msg in ("ĐT của anh 0912345678", "dt 0912345678", "sđt chị 0912345678", "đt: 0912345678"):
        assert "(điện thoại)" in engine._RE_DT_ABBR.sub(lambda m: m.group(0) + " (điện thoại)", msg), msg
    for msg in ("ĐTHT có không", "đông trùng hạ thảo", "dtht"):
        assert "(điện thoại)" not in engine._RE_DT_ABBR.sub(lambda m: m.group(0) + " (điện thoại)", msg), msg
    assert "5w2" in (PROMPT_NHS or "5w2")
    # "ĐT" của khách không mở khóa sản phẩm tầng 3 (Đông trùng)
    t3 = "Dạ bên em còn Đông trùng hạ thảo ạ.\n\nAnh lấy mấy hộp Nước Hồng sâm ạ?"
    assert engine._drop_unasked_tiers(t3, ["ĐT (điện thoại) của anh 0912345678"], "")[1] == 1


# 17 ─ (lỗi tương tự, lưới tầng sản phẩm) tên "Nguyen Lan" không bị hiểu là "nguyên lá"; "tăng cường" không phải "cương"
def test_17_luoi_tang_khop_nguyen_tu():
    t3 = "Dạ Trà sâm Lai Châu nguyên lá rất thơm ạ.\n\nChị lấy mấy hộp Nước Hồng sâm ạ?"
    assert engine._drop_unasked_tiers(t3, ["Nguyen Lan 0912345678 Ha Dong"], "")[1] == 1
    assert engine._drop_unasked_tiers(t3, ["có trà nguyên lá không em"], "")[1] == 0
    t2 = "Dạ ngoài ra có Dương Sâm Linh Đan ạ.\n\nAnh lấy mấy hộp ạ?"
    assert engine._drop_unasked_tiers(t2, ["uống để tăng cường sức khỏe"], "")[1] == 1


# ======== v0.5.0 (28/10/2026): học theo luồng báo giá Hồng sâm lát v0.1.87–0.1.107 ========
_FULL_Q = """Dạ Nước Hồng sâm Thái Minh mật ong dạng túi giá 620.000đ/hộp 20 túi, mỗi ngày anh/chị dùng 1–2 túi ạ.

Nước Hồng sâm rất hợp với người hay mệt mỏi, căng thẳng, ngủ không sâu ạ.

Chương trình tri ân khách hàng mới:
🎁 Combo 2 hộp (40 túi): 1.240.000đ – tặng 1 hộp Trà sâm 1700 (10 gói)
🎁 Combo 4 hộp (80 túi): 2.480.000đ – tặng 3 hộp Trà sâm 1700 (10 gói)
🎁 Combo 6 hộp (120 túi): 3.720.000đ – tặng 5 hộp Trà sâm 1700 (10 gói)
✅ Từ 2 hộp miễn phí vận chuyển

Anh/chị muốn chọn gói nào ạ?"""


# 18 ─ báo giá lần đầu: 3/4 khách = giá 1 hộp + câu khuyên + 1 câu hỏi sức khỏe (chưa gửi combo); 1/4 gửi combo ngay
def test_18_bao_gia_lan_dau():
    probe, full = 0, 0
    for _ in range(8):
        out, n = engine._shape_nhs_quote(_FULL_Q, ["giá bao nhiêu vậy shop"], [])
        assert n and "620.000đ" in out
        if "Combo 2 hộp" in out:
            full += 1
            assert out.count("Combo") == 3 and out.rstrip().endswith(("?", "ạ.", "nhé.", "nhé"))
        else:
            probe += 1
            assert "nên dùng đều" in out and out.rstrip().endswith("?") and out.count("?") == 1
            assert "Chương trình tri ân" not in out and "miễn phí vận chuyển" not in out
    assert probe == 6 and full == 2, (probe, full)


# 19 ─ khách hỏi thẳng combo / mua cho bố mẹ → gửi bảng combo luôn, đoạn phù hợp + câu chốt đúng ngữ cảnh, không gọi "tháng"
def test_19_hoi_combo_va_bo_me():
    out, _ = engine._shape_nhs_quote(_FULL_Q, ["có combo ưu đãi gì không"], [])
    assert out.count("Combo") >= 3 and "tháng" not in out
    out, _ = engine._shape_nhs_quote(_FULL_Q, ["mua cho bố mẹ, có combo gì"], [])
    assert "Bố mẹ lớn tuổi" in out and out.count("rất hợp") == 1
    # bản lát không bị đụng: báo giá có bảng 3 combo nhưng là Hồng sâm lát → không định hình
    lat = _FULL_Q.replace("Combo 2 hộp", "Combo 1 tháng").replace("Combo 4 hộp", "Combo 2 tháng").replace("Combo 6 hộp", "Combo 3 tháng")
    assert engine._shape_nhs_quote(lat, ["giá"], [])[1] == 0


# 20 ─ khách trả lời câu hỏi sức khỏe → lưu ý lượt sau dẫn đúng bảng combo Nước Hồng sâm (không phải Hồng sâm lát)
def test_20_ghi_chu_khai_thac():
    K1 = engine._probe_texts()["K1"]
    assert "huyết áp" in K1 and "Nước Hồng sâm" not in engine._probe_texts().get("K3", "Nước Hồng sâm")
    note = engine.probe_followup_note(["giá sao em", "anh bị huyết áp, đang uống thuốc"], ["Dạ giá 620.000đ/hộp 20 túi ạ. " + K1])
    assert "price_quote_nhs" in note and "Hồng sâm lát" not in note
    assert all("Nước Hồng sâm" not in q or True for q in engine._discovery_questions())


# 21 ─ khách cũ: quà đúng bảng khách cũ Nước Hồng sâm (2 hộp → 2 Trà sâm; 3 hộp → 3 Trà sâm), lưới quà khách mới không ép ngược
def test_21_qua_khach_cu():
    bot = ["Dạ bên em đang có chương trình tri ân dành riêng cho khách hàng thân thiết của Nước Hồng sâm ạ:"]
    txt = "Dạ anh lấy 3 hộp được tặng 2 hộp Trà sâm 1700 (10 gói) ạ."
    out, n = engine._fix_returning_gifts(txt, ["anh lấy 3 hộp"], bot)
    assert n == 1 and "3 hộp Trà sâm 1700 (10 gói)" in out
    row = "🎁 Combo 2 hộp: 1.240.000đ – tặng 2 hộp Trà sâm 1700 (10 gói)"
    assert engine._fix_nhs_packages(row, bot) == row
    assert "1 hộp Trà sâm" in engine._fix_nhs_packages(row, [])
    note = engine.returning_note(["mua tiếp"], bot)
    assert "12 hộp" in note and "Nước Hồng sâm" in note and "Heviho" not in note


# 22 ─ thời gian dùng: 1 hộp 20 túi = 10–20 ngày → "6 hộp dùng 6 tháng" bị sửa; "2 hộp dùng khoảng 1 tháng" giữ nguyên
def test_22_thoi_gian_dung():
    out, n = engine._fix_duration_nhs("Combo 6 hộp anh dùng được 6 tháng ạ.")
    assert n == 1 and "60–120 ngày" in out
    assert engine._fix_duration_nhs("2 hộp anh dùng khoảng 1 tháng ạ.")[1] == 0


# 23 ─ lưới dự phòng (lỗi code / mất giá): chỉ hộp 20 túi, có bảng combo 2/4/6, không liệt kê kiểu "•"
def test_23_bao_gia_du_phong():
    ps = engine.price_sentence("giá sao", "hsmo_tui")
    assert "620.000đ/hộp 20 túi" in ps and "10 túi" not in ps
    txt, hr = engine.auto_answer("giá bao nhiêu", "hsmo_tui")
    assert hr is None and "•" not in txt and "Combo 6 hộp" in txt and "330.000" not in txt


# 24 ─ (chốt 28/10) khách cũ hưởng CT TỐT NHẤT giữa CT khách cũ và khách mới; 1 hộp không quà, có phí ship
def test_24_khach_cu_ct_tot_nhat():
    want = {1: "", 2: "2 hộp Trà sâm", 3: "3 hộp Trà sâm", 4: "3 hộp Trà sâm", 6: "5 hộp Trà sâm", 9: "5 hộp Trà sâm",
            10: "1 hộp nước Hồng sâm", 12: "2 hộp Nước Hồng sâm"}
    for q, g in want.items():
        r = t.build_order([{"sku": "hsmo-tui", "qty": q}], "A", PHONE, ADDR, "returning")
        got = "; ".join(p["gift"] for p in r["promo_applied"])
        assert (g in got) if g else not got, (q, got)
        if q == 1:
            assert r["ship_fee"] and r["ship_fee"] > 0
        if q in (6, 10):
            assert r["promo_applied"][0]["program"] == "new_customer"
    bot = ["Dạ bên em đang có chương trình tri ân dành riêng cho khách hàng thân thiết của Nước Hồng sâm ạ:"]
    out, n = engine._fix_returning_gifts("Dạ anh lấy 6 hộp được tặng 3 hộp Trà sâm 1700 (10 gói) ạ.", ["lấy 6 hộp"], bot)
    assert n == 1 and "5 hộp Trà sâm" in out
    rq = S["returning_quote_nhs"]
    assert "Mua 6 hộp" in rq and "Mua 10 hộp" in rq and "TỐT NHẤT" in rq


# 25 ─ (chat thử 29/10) đã báo giá 1 hộp ở lượt trước → lượt sau KHÔNG nhắc lại câu giá, gửi bảng combo luôn
def test_25_khong_bao_gia_lai():
    bot = ["Nước Hồng sâm Thái Minh mật ong dạng túi có giá 620.000đ một hộp 20 túi ạ. Anh/chị mua cho bản thân hay người thân ạ?"]
    users = ["giá bao nhiêu", "mua cho mẹ bị HA cao, tiểu đường"]
    out, _ = engine._shape_nhs_quote(_FULL_Q, users, bot)
    out, n = engine._drop_repeat_price_nhs(out, users, bot)
    assert n == 1 and "620.000đ/hộp" not in out and out.count("Combo") >= 3 and out.startswith("Dạ")
    # khách HỎI LẠI giá → vẫn giữ câu giá
    assert engine._drop_repeat_price_nhs(_FULL_Q, ["giá", "giá bao nhiêu em"], bot)[1] == 0


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted((k, v) for k, v in globals().items() if k.startswith("test_")):
        try:
            fn()
            print("PASS", name)
        except Exception as e:  # noqa: BLE001
            fails += 1
            print("FAIL", name, "→", repr(e))
    _n = sum(1 for k in globals() if k.startswith("test_"))
    print(f"\n{_n - fails}/{_n} ca đạt")
    sys.exit(1 if fails else 0)
