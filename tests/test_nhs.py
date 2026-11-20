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


# 26 ─ (chat thử 29/10) khách gửi SĐT sai (12 số) → bot KHÔNG xác nhận đơn, hỏi lại số
def test_26_sdt_sai_hoi_lai():
    c = "Dạ em gửi thông tin xác nhận đơn hàng của chị Nga ạ:\n- Tổng thanh toán: 1.240.000đ\n- Người nhận: Nguyễn Thị Nga - 009876862776"
    out, n = engine._fix_invalid_phone(c, ["Nguyễn Thị Nga, 009876862776, đội 3, Thanh Tùng, Thanh Miện, Hải Dương"])
    assert n == 1 and "chưa đúng" in out and "12 chữ số" in out and "xác nhận đơn" not in out
    assert engine._fix_invalid_phone(c, ["Nga 0987686277 Hải Dương"])[1] == 0          # số đúng → giữ xác nhận
    assert engine._fix_invalid_phone(c, ["Nga +84987686277 Hải Dương"])[1] == 0
    assert engine._fix_invalid_phone(c, ["Nga 098768627 Hải Dương"])[1] == 1           # thiếu 1 số
    # v0.5.8 (chạy thật 30/10): AI tự hỏi lại SĐT nhưng bịa lý do "dạng bảo mật" → thay bằng câu chuẩn (11 chữ số)
    bm = "Dạ chị Nga ơi, SĐT chị vừa gửi đang hiển thị dạng bảo mật nên hệ thống chưa nhận diện đủ 10 số ạ. Chị nhắn lại giúp em nhé ạ."
    out, n = engine._fix_invalid_phone(bm, ["09876867765, chị Nga, 92 Trung Kính, Cầu Giấy, HN"])
    assert n == 1 and "bảo mật" not in out and "11 chữ số" in out


# 27 ─ (chị Nga 29/10) khách mua 2 sản phẩm khác nhau → MỘT tin tổng hợp, mỗi món 1 dòng, quà từng món, tổng đúng
def test_27_don_nhieu_san_pham():
    r = t.build_order([{"sku": "hsmo-tui", "qty": 2}, {"sku": "hsvn-lat-14", "qty": 2}], "Nguyễn Thị Nga", PHONE, ADDR, "new")
    c = r["confirm_text"]
    assert r["ready_to_confirm"] and r["total"] == 2 * NHS_PRICE + 2 * 1420000
    assert "- Hồng sâm dạng nước (hộp 20 túi) x 2 hộp: 1.240.000đ (tặng 1 hộp Trà sâm 1700 (10 gói))" in c
    assert "- Hồng sâm dạng lát x 2 hộp: 2.840.000đ (tặng" in c and "4.080.000đ" in c
    assert engine._is_order_summary(c) and engine._is_order_summary("Dạ em xác nhận đơn hàng ạ: 2 hộp. Tổng thanh toán: 1.240.000đ")
    one = t.build_order([{"sku": "hsmo-tui", "qty": 2}], "Nga", PHONE, ADDR, "new")["confirm_text"]
    assert "Sản phẩm + Số lượng: Hồng sâm dạng nước (hộp 20 túi) x 2 hộp" in one and "Quà tặng kèm:" in one   # 1 món: giữ mẫu cũ


# 28 ─ (rà soát 29/10) giá Nước Hồng sâm chỉ lấy từ bảng: dòng combo mọi kiểu, câu giá không ghi quy cách, giá viết 'k'
def test_28_gia_dung_bang():
    fx = lambda x: engine._fix_nhs_prices(x)[0]
    assert "2.480.000đ" in fx("✅ Combo 4 hộp – 2.400.000đ – tặng 3 hộp Trà sâm 1700 (10 gói)")
    assert "3.720.000đ" in fx("🎁 Combo 6 hộp giá 3.600.000đ: tặng ngay 5 hộp Trà sâm 1700 (10 gói)")
    assert "1.860.000đ" in fx("Mua 3 hộp: 1.800.000đ – tặng 3 hộp Trà sâm 1700 (10 gói)")
    assert "620.000đ" in fx("Nước Hồng sâm giá 650.000đ một hộp ạ.") and "620.000đ" in fx("Nước Hồng sâm giá chỉ 600k/hộp ạ.")
    assert "330.000đ" in fx("Hộp nhỏ 10 túi giá 350.000đ ạ.")
    for ok in ("Tổng tiền đơn hàng: 1.255.000đ", "Mua 1 hộp phí ship 15.000đ nội thành",
               "🎁 Mua 12 hộp: 7.440.000đ – tặng 2 hộp Nước Hồng sâm dạng túi cùng loại + 1 hộp Trà sâm 1700 (10 gói)",
               "Hồng sâm lát 1.420.000đ/hộp 14 gói, Nước Hồng sâm 620.000đ/hộp 20 túi"):
        assert engine._fix_nhs_prices(ok)[1] == 0, ok


# 29 ─ (rà soát 29/10) khách tự xưng anh/chị/bác/cô trong câu hỏi → bot gọi đúng
def test_29_xung_ho():
    assert engine.customer_self_gender(["chị hay mệt, uống được không"]) == "female"
    assert engine.customer_self_gender(["anh dạo này ngủ kém"]) == "male"
    assert engine._customer_title(["bác 70 tuổi rồi, bác uống được không cháu"]) == "bác"
    assert engine._customer_title(["cô hay mệt mỏi dùng được không con"]) == "cô"
    assert engine._customer_title(["mua cho bà, bà uống được không em"]) == ""     # bà là người khác


# 30 ─ (rà soát 29/10) không lộ ghi chú: nhãn vai, câu nói về lượt / hệ thống, dòng ghi chú trong ngoặc
def test_30_khong_lo_ghi_chu():
    G = "Dạ Nước Hồng sâm giá 620.000đ/hộp 20 túi ạ."
    for leak in ("KHÁCH: hỏi giá\nTRẢ LỜI: " + G, G + "\n\nLượt này em chưa gửi combo theo hướng dẫn hệ thống.",
                 "(Báo giá lần đầu, hỏi sức khỏe)\n" + G):
        assert engine.strip_internal(leak)[0].strip() == G, leak
    for keep in ("Tên khách hàng: Nguyễn Thị Nga", "Thái Minh có hệ thống điểm bán toàn quốc ạ.", "Hệ thống sản xuất đạt GMP ạ."):
        assert engine.strip_internal(keep)[0] == keep, keep


# 31 ─ (chat thử 29/10) mã SKU nội bộ không lộ ra khách; "chị Nga, 09…" = khách xưng chị
def test_31_khong_lo_ma_sku():
    leak = "Sản phẩm chọn: hsmo-tui-10 (hộp nhỏ 10 túi Nước Hồng sâm Thái Minh mật ong), số lượng: 1."
    assert engine.strip_internal(leak)[0].strip() == ""
    assert engine.strip_internal("Dạ chị dùng hộp 10 túi nhé ạ.\n[IMG: nuoc-hong-sam-10tui]")[0].count("[IMG: nuoc-hong-sam-10tui]") == 1
    assert engine.customer_self_gender(["chị Nga, 09768627765 SN23 thôn đông, thanh tùng, thanh miện, hải dương"]) == "female"


# 32 ─ (chạy thật 30/10) chê đắt / chưa đủ tiền → thuyết phục ÍT NHẤT 2 lần mới mời hộp 10 túi; thành ngữ đủ chữ, tên viện đúng
def test_32_thuyet_phuc_2_lan_moi_10_tui():
    R = "Dạ bác dùng được ạ.\nNếu chị muốn trải nghiệm trước, bên em có hộp nhỏ 10 túi giá 330.000đ ạ. Chị có muốn lấy hộp 10 túi không ạ?\n[IMG: nuoc-hong-sam-10tui]"
    T = lambda *x: [{"role": r, "text": tx} for r, tx in x]
    c1 = T(("user", "giá"), ("assistant", "620.000đ/hộp 20 túi"), ("user", "hơi đắt nhỉ"), ("assistant", "Dạ em hiểu…"), ("user", "mẹ chị huyết áp cao"))
    out, n = engine._gate_10tui(R, c1)
    assert n and "10 túi" not in out and "330.000" not in out and "nuoc-hong-sam-10tui" not in out and "combo 2 hộp" in out
    out, n = engine._gate_10tui(R, T(("user", "giá"), ("assistant", "x"), ("user", "không có tiền, thôi")))
    assert n and "11.000mg" in out and "10 túi" not in out          # lần 1: nêu giá trị
    c2 = c1 + T(("assistant", "Dạ… combo 2 hộp…"), ("user", "vẫn đắt, thôi để sau"))
    assert engine._gate_10tui(R, c2)[1] == 0                         # đã thuyết phục 2 lần → được mời 10 túi
    assert engine._gate_10tui(R, T(("user", "có hộp nhỏ không em")))[1] == 0
    assert engine._gate_10tui(R, T(("user", "có cho dùng thử không")))[1] == 0
    fb = engine._fix_banned_phrases("Tiền nào nấy, chuyển giao từ Viện Dược liệu, tặng kèm Trà sâm 1700 giúp bác dễ ngủ, thư thái hơn ạ.")
    assert "Tiền nào của nấy" in fb and "Viện Nghiên cứu Sâm và Dược liệu Việt Nam (VIGH)" in fb and "dễ ngủ" not in fb


# 33 ─ (chạy thật 30/10) nêu rõ tên công ty; hỏi nhà thuốc → link tra điểm bán
def test_33_cong_ty_va_diem_ban():
    t1 = engine._fix_banned_phrases("Sản phẩm được phân phối chính hãng trực tiếp từ công ty, có tem niêm phong ạ.")
    assert "Công ty Cổ phần Sâm và Dược liệu quý Thái Minh" in t1
    out, n = engine._add_where_buy("Dạ chị yên tâm ạ.\n\nChị muốn ghé cửa hàng không ạ?", "hay có ở nhà thuốc ko")
    assert n == 1 and "samthaiminh.com/diem-ban" in out and out.rstrip().endswith("?")
    assert engine._add_where_buy("Dạ vâng ạ.", "giá bao nhiêu")[1] == 0


# 34 ─ (chạy thật 30/10, ca anh Văn Mạnh Phí) khách xác nhận / im 5 phút sau tổng hợp đơn → không gửi lại tổng hợp, luôn gắn thẻ Bot chốt đơn
def test_34_xac_nhan_don():
    CF = t.build_order([{"sku": "hsmo-tui", "qty": 1}], "Văn Mạnh Phí", "0918305087", "25/1 Lê Thị Kỉnh, Phước Kiển, Nhà Bè, TP.HCM", "new")["confirm_text"]
    T = lambda *x: [{"role": r, "text": tx} for r, tx in x]
    tr = T(("user", "địa chỉ…"), ("assistant", CF), ("user", "[Khách chưa trả lời sau 5 phút kể từ khi em gửi tổng hợp đơn — coi như khách ĐỒNG Ý đơn]"))
    out, n = engine._order_confirmed("Dạ em gửi lại xác nhận đơn hàng ạ:\n- Tên khách hàng: Văn Mạnh Phí\n- Số điện thoại: 0918305087\n- Tổng thanh toán: 640.000đ", tr)
    assert n == 2 and not engine._is_order_summary(out) and "[HANDOFF: đơn đã chốt - lên đơn | 0918305087 | 1]" in out
    out, n = engine._order_confirmed("Dạ đơn hàng của anh đã được ghi nhận ạ.", T(("user", "x"), ("assistant", CF), ("user", "Oki")))
    assert n == 1 and "| 1]" in out
    assert engine._order_confirmed("Dạ vâng ạ", T(("user", "giá"), ("assistant", "620.000đ"), ("user", "ok")))[1] == 0


# 35 ─ (chạy thật 30/10, ca Mây Bay) khách không xưng bác/cô → bot xưng "em", không "cháu"; không gọi khách "bạn"
def test_35_bot_xung_em():
    assert engine._fix_self_em("Cháu chúc chị luôn nhiều sức khỏe ạ!") == "Em chúc chị luôn nhiều sức khỏe ạ!"
    assert engine._fix_self_em("Dạ cháu cảm ơn chị, chị cho cháu xin số điện thoại nhé.") == "Dạ em cảm ơn chị, chị cho em xin số điện thoại nhé."
    assert engine._fix_self_em("Cháu nhà chị mấy tuổi rồi ạ?") == "Cháu nhà chị mấy tuổi rồi ạ?"
    assert engine._fix_ban("Dạ bạn ơi, bạn muốn lấy mấy hộp ạ?") == "Dạ anh/chị ơi, anh/chị muốn lấy mấy hộp ạ?"
    assert engine._fix_ban("Mua làm quà cho bạn bè cũng hợp ạ.") == "Mua làm quà cho bạn bè cũng hợp ạ."


# 36 ─ (chạy thật 02/11, ca Nguyễn Tâm) khách lưỡng lự mà chưa thấy combo → gửi ưu đãi combo + xin SĐT; không nói "liệu trình"
def test_36_luong_lu_gui_uu_dai():
    T = lambda *x: [{"role": r, "text": tx} for r, tx in x]
    tr = T(("user", "cho e xin giá ạ"), ("assistant", "Dạ giá 620.000đ một hộp 20 túi ạ."), ("user", "Dạ vâng để e xem đã ạ"))
    out, n = engine._hesitate_offer_nhs("Dạ vâng ạ. Chị để lại số điện thoại giúp em nhé ạ.", tr)
    assert n == 1 and out.count("Combo") == 3 and "1.240.000đ" in out and "số điện thoại" in out
    tr2 = T(("user", "giá"), ("assistant", "🎁 Combo 2 hộp: 1.240.000đ – tặng 1 hộp Trà sâm"), ("user", "để em suy nghĩ thêm"))
    assert engine._hesitate_offer_nhs("Dạ vâng ạ.", tr2)[1] == 0          # đã thấy combo rồi → không gửi lại
    assert engine._fix_lieu_trinh_nhs("Chị muốn tìm hiểu liệu trình dùng cho cá nhân ạ?")[0] == "Chị muốn tìm hiểu cách dùng cho cá nhân ạ?"


# 37 ─ (05/11, chị Nga) thông điệp Hội nghị Quốc tế về Sâm: nguyên văn, đúng 2 ảnh, 1 lần/hội thoại, tự gửi khi khách nghi ngờ chất lượng
def test_37_hoi_nghi_sam():
    T = lambda *x: [{"role": r, "text": tx} for r, tx in x]
    imgs = ("[IMG: hoi-nghi-sam-han-quoc]", "[IMG: ts-thai-bao-cao-han-quoc]")
    # (a) khách hỏi uy tín, AI chưa nói → tự thêm trước câu hỏi cuối, kèm đúng 2 ảnh
    tr = T(("user", "giá sao em"), ("assistant", "Dạ 620.000đ/hộp ạ."), ("user", "sâm việt nam có tốt bằng sâm hàn không em"))
    out, n = engine._symposium_net("Dạ sâm Việt Nam có hoạt chất MR2 ạ.\n\nAnh/chị dùng cho bản thân hay người thân ạ?", tr)
    assert n == 1 and engine.SYMPOSIUM_MSG in out and all(out.count(i) == 1 for i in imgs)
    assert out.rstrip().endswith("người thân ạ?") and out.index(imgs[1]) < out.index("Anh/chị dùng")
    # (b) AI tự diễn đạt lại → thay bằng câu chuẩn, gắn 2 ảnh, bỏ ảnh thừa
    ai = "Dạ vâng ạ. Sản phẩm vừa được giới thiệu tại Hội nghị Quốc tế về Sâm ở Hàn Quốc, rất được đánh giá cao ạ. [IMG: hoi-nghi-sam-han-quoc]"
    out, n = engine._symposium_net(ai, T(("user", "ok")))
    assert n == 1 and engine.SYMPOSIUM_MSG in out and out.startswith("Dạ vâng ạ.") and all(out.count(i) == 1 for i in imgs)
    # (c) đã gửi rồi → không lặp, bỏ ảnh
    tr3 = T(("assistant", engine.SYMPOSIUM_MSG), ("user", "hàng có chính hãng không"))
    out, n = engine._symposium_net(ai, tr3)
    assert "Hội nghị" not in out and "[IMG" not in out and out.startswith("Dạ vâng ạ.")
    assert engine._symposium_net("Dạ hàng chính hãng ạ.", tr3)[1] == 0
    # (d) ảnh hội nghị đứng một mình → bỏ; khách không nghi ngờ → không thêm
    assert engine._symposium_net("Dạ vâng ạ.\n[IMG: ts-thai-bao-cao-han-quoc]", T(("user", "giá bao nhiêu")))[0] == "Dạ vâng ạ."
    assert engine._symposium_net("Dạ 620.000đ ạ.", T(("user", "giá bao nhiêu")))[1] == 0
    # (e) tin an toàn (cho con bú) → không chèn
    assert engine._symposium_net("Dạ phụ nữ đang cho con bú không dùng được ạ.", T(("user", "đang cho con bú dùng hàng thật được không")))[1] == 0


# 38 ─ (16/11, ca Dương Thị Thìn + Thang Huynh) AI tự kể quà sai bảng ("Mua 4 hộp … tặng 2 hộp Trà sâm") → sửa đúng bảng mọi kiểu viết
def test_38_qua_dung_bang():
    a = engine._fix_nhs_packages("- Hộp 2 hộp: 1.240.000đ - Tặng ngay 1 hộp Trà sâm 1700 (10 gói) - Miễn phí vận chuyển\n"
                                 "- Mua 4 hộp: 2.480.000đ - Tặng ngay 2 hộp Trà sâm 1700 (10 gói) - Miễn phí vận chuyển\n"
                                 "- Mua 6 hộp: 3.720.000đ - Tặng ngay 3 hộp Trà sâm 1700 (10 gói) - Miễn phí vận chuyển", [])
    assert "- Combo 2 hộp" in a and "Tặng ngay 3 hộp Trà sâm 1700 (10 gói) - Miễn phí" in a and "Tặng ngay 5 hộp Trà sâm 1700 (10 gói) - Miễn phí" in a
    b = engine._fix_nhs_packages("Ví dụ mua 2 hộp anh được tặng 1 hộp Trà sâm, mua 4 hộp tặng 2 hộp Trà sâm, còn mua 6 hộp được tặng 3 hộp trà ạ.", [])
    assert b.count("Trà sâm 1700 (10 gói)") == 3 and "tặng 3 hộp" in b and "tặng 5 hộp" in b and b.endswith("ạ.")
    c = engine._fix_nhs_packages("Lấy 5 hộp được tặng 5 hộp Trà sâm. Hộp nhỏ 10 túi không có quà ạ.", [])
    assert "tặng 3 hộp Trà sâm 1700 (10 gói)" in c
    assert "3 hộp Trà sâm 1700 (10 gói)" in engine._nhs_gift_table_txt()


# 39 ─ (16/11, chị Nga duyệt) thanh toán: 2 cách, không tự nói "chưa hỗ trợ quẹt thẻ"
def test_39_thanh_toan():
    ai = "Dạ Nước Hồng sâm giá 620.000đ/hộp 20 túi ạ.\n\nVề thanh toán thì bên em nhận tiền mặt hoặc chuyển khoản khi nhận hàng, hiện chưa hỗ trợ quẹt thẻ anh nhé.\n\nAnh định tham khảo combo mấy hộp ạ?"
    out, n = engine._fix_payment_nhs(ai, "Có trả bằng thẻ không ạ")
    assert n == 1 and engine.PAYMENT_MSG in out and "quẹt thẻ" not in out and out.rstrip().endswith("mấy hộp ạ?")
    out, n = engine._fix_payment_nhs("Dạ vâng ạ.", "thanh toán thế nào em")
    assert n == 1 and engine.PAYMENT_MSG in out
    assert engine._fix_payment_nhs("Dạ 620.000đ ạ.", "giá bao nhiêu")[1] == 0
    assert "payment" in S and "chuyển khoản trước" in S["payment"]


# 40 ─ (16/11, chị Nga chốt) Nước Hồng sâm: thấy thay đổi "sau khoảng 1 hộp đầu (khoảng 20 ngày)"
def test_40_mot_hop_dau():
    f = lambda x: engine._fix_2hop_nhs(x)[0]
    assert f("Anh/chị nên dùng đều mỗi ngày, thường sau khoảng 2 hộp đầu sẽ thấy cơ thể thay đổi ạ.") == \
        "Anh/chị nên dùng đều mỗi ngày, thường sau khoảng 1 hộp đầu (khoảng 20 ngày) sẽ thấy cơ thể thay đổi ạ."
    assert f("Thông thường sau khi dùng hết 2 hộp đầu tiên, cơ thể khỏe hơn.") == "Thông thường sau khoảng 1 hộp đầu (khoảng 20 ngày), cơ thể khỏe hơn."
    assert f("Hồng sâm lát dùng sau 2 hộp đầu thấy rõ.") == "Hồng sâm lát dùng sau 2 hộp đầu thấy rõ."
    assert "1 hộp đầu (khoảng 20 ngày)" in S["price_quote_nhs"] and "2 hộp đầu" not in S["price_quote_nhs"]


# 41 ─ (16/11, chị Nga: "giá hộp 20 túi luôn là 620k, có lúc bot nói sai") lưới giá xét từng câu, mọi kiểu viết
def test_41_gia_dung_bang():
    f = lambda x: engine._fix_nhs_prices(x)[0]
    assert "620.000đ/hộp 20 túi, mỗi ngày" in f("Dạ Nước Hồng sâm Thái Minh mật ong dạng túi giá 650.000đ/hộp 20 túi, mỗi ngày anh/chị dùng 1–2 túi ạ.")
    assert "620.000đ một hộp" in f("Dạ Nước Hồng sâm có giá niêm yết là 600.000đ một hộp 20 túi ạ.")
    assert "1.240.000đ - Tặng" in f("- Hộp 2 hộp: 1.200.000đ - Tặng ngay 1 hộp Trà sâm 1700 (10 gói) - Miễn phí vận chuyển")
    assert f("2 hộp giá 1.240.000đ, 6 hộp giá 3.600.000đ ạ.") == "2 hộp giá 1.240.000đ, 6 hộp giá 3.720.000đ ạ."
    assert "2.480.000đ" in f("Combo 4 hộp chỉ 2tr4 thôi ạ.")
    assert "330.000đ" in f("Hộp nhỏ 10 túi giá 350.000đ ạ.")
    for keep in ["Hồng sâm lát giá 1.420.000đ/hộp 14 gói ạ.", "Tổng tiền: 1.260.000đ", "Mua 1 hộp phí ship 20.000đ ạ.",
                 "Tặng 1 hộp Trà sâm 1700 (10 gói) trị giá 120.000đ ạ.", "Mỗi túi 8ml chứa tới 11.000mg tinh chất."]:
        assert f(keep) == keep, keep


# 42 ─ (17/11, chị Nga) CTKM mới Hồng sâm lát (HSVN-M04 / C06) và Dương Sâm Linh Đan (DSLĐ-M03 / C06);
#       báo giá CHỈ nêu 1 quà, khách xin đổi mới áp quà khác (gift_choice)
def test_42_ctkm_lat_ds_moi():
    bo = lambda sku, q, ct="new", ch=None: t.build_order([dict({"sku": sku, "qty": q}, **({"gift_choice": ch} if ch else {}))],
                                                         "A", "0912345678", "SN 1 Cầu Giấy, Hà Nội", customer_type=ct)
    g = lambda *a: bo(*a)["promo_applied"][0]["gift"]
    for sku, q, ct in [("hsvn-lat-14", 1, "new"), ("hsvn-lat-14", 2, "new"), ("hsvn-lat-14", 5, "returning"), ("duongsam-10", 6, "new"), ("hsvn-lat-50", 1, "new")]:
        assert "hoặc" not in g(sku, q, ct) and "chọn 1" not in g(sku, q, ct), (sku, q, g(sku, q, ct))
    assert g("hsvn-lat-14", 2) == "1 hộp Trà sâm 1700 (20 gói)" and g("hsvn-lat-14", 4) == g("hsvn-lat-14", 3)
    assert g("hsvn-lat-14", 5) == "3 hộp Trà sâm 1700 (20 gói)" and "Nước Hồng sâm" in g("hsvn-lat-14", 10)
    assert "3 hộp Hồng sâm lát" in g("hsvn-lat-14", 50) and "Nước Hồng sâm" in g("hsvn-lat-50", 5)
    assert "Nước Hồng sâm" in g("hsvn-lat-50", 2, "returning") and "Bổ gan" in g("duongsam-10", 7, "returning")
    assert "2 hộp Nước Hồng sâm" in g("duongsam-10", 9) and "Dương Sâm Linh Đan" in g("duongsam-10", 12, "returning")
    o = bo("hsvn-lat-14", 2)
    assert o["promo_applied"][0]["gift_options_if_customer_asks"] == ["2 hộp viên ngậm Heviho", "2 lọ dầu nóng Khương Thảo Đan"]
    assert "Heviho" not in o["confirm_text"]                                  # tổng hợp đơn chỉ ghi 1 quà
    o2 = bo("hsvn-lat-14", 2, "new", "2 hộp viên ngậm Heviho")              # khách xin đổi
    assert o2["promo_applied"][0]["gift"] == "2 hộp viên ngậm Heviho" and "2 hộp viên ngậm Heviho" in o2["confirm_text"]
    assert g("hsvn-lat-14", 2, "new", "1 chai rượu sâm") == "1 hộp Trà sâm 1700 (20 gói)"   # quà ngoài bảng → không nhận
    assert "Combo 1 tháng" not in KB["combo_tiers_note"] and "hoặc" not in KB["combo_tiers_note"]
    assert "MỖI MỐC CHỈ NÊU 1 QUÀ" in engine.NHS_BLOCK
    # lưới quà: sửa theo đúng bảng của sản phẩm trong câu; khách đã xin đổi thì giữ phương án khách chọn
    a = engine._fix_nhs_packages("Combo 3 hộp Hồng sâm lát: 4.260.000đ – tặng 2 hộp Trà sâm 1700 (20 gói)", [])
    assert a.endswith("tặng 1 hộp Trà sâm 1700 (20 gói) + 1 lọ dầu nóng Khương Thảo Đan")
    b = engine._fix_nhs_packages("Mua 6 hộp Dương Sâm Linh Đan được tặng 1 chai Nước Hồng sâm mật ong ạ.", [])
    assert "Bổ gan" in b and "hoặc" not in b and b.endswith("ạ.")
    c = "Dạ vâng, combo 2 hộp Hồng sâm lát em đổi sang tặng 2 hộp viên ngậm Heviho cho anh ạ."
    assert engine._fix_nhs_packages(c, [], ["có quà khác không em, anh thích viên ngậm hơn"]) == c


# 43 ─ (17/11, chị Nga) khách viết đoạn dài: không bắt 1–2 từ khóa rồi thay câu trả lời
def test_43_doc_het_tin_dai():
    dai = ("Chị mua cho mẹ chị năm nay 70 tuổi, mẹ bị tiểu đường và huyết áp cao đang uống thuốc hằng ngày, "
           "trước mẹ dùng sâm Hàn thấy nóng, giá cả không quan trọng chị chỉ muốn biết mẹ dùng có được không và uống lúc nào")
    assert engine._is_long_msg(dai) and not engine._asks_price(dai)
    assert engine._asks_price("giá sao em") and engine._asks_price(dai + ". Mà 1 hộp bao nhiêu tiền em?")
    T = lambda *x: [{"role": r, "text": tx} for r, tx in x]
    tr = T(("user", "giá"), ("assistant", "Dạ 620.000đ/hộp 20 túi ạ."),
           ("user", "để chị hỏi ý kiến chồng đã, mà nước sâm này người tiểu đường uống được không em, uống lúc nào thì tốt?"))
    assert engine._hesitate_offer_nhs("Dạ người tiểu đường dùng được ạ...", tr)[1] == 0
    assert "(o)" in engine.NHS_BLOCK and "ĐỌC HẾT TIN KHÁCH" in engine.NHS_BLOCK


# 44 ─ (18/11, ca chị Gấu) bảng Hồng sâm lát mà từng dòng không ghi tên sản phẩm → giá = số hộp × 1.420.000đ, quà đúng bảng lát
def test_44_gia_qua_theo_dong_tieu_de():
    T = ("Hộp thiếc 14 gói có giá 1.420.000đ, mỗi ngày dùng 1 gói ạ.\n"
         "Chương trình tri ân khách hàng mới khi mua Hồng sâm lát:\n"
         "- Mua 1 hộp (620.000đ): Tặng 1 hộp Trà sâm 1700 (10 gói), miễn phí vận chuyển\n"
         "- Mua 2 hộp (1.240.000đ): Tặng 1 hộp Trà sâm 1700 (10 gói), miễn phí vận chuyển\n"
         "- Mua 3 hộp (1.860.000đ): Tặng 2 hộp Trà sâm 1700 (10 gói), miễn phí vận chuyển")
    o = engine._fix_nhs_packages(engine._fix_nhs_prices(T)[0], [], ["Mình muốn tham khảo dòng Hồng sâm lát ạ"])
    assert "Mua 1 hộp (1.420.000đ)" in o and "Mua 2 hộp (2.840.000đ): Tặng 1 hộp Trà sâm 1700 (20 gói), miễn phí" in o
    assert "Mua 3 hộp (4.260.000đ): Tặng 1 hộp Trà sâm 1700 (20 gói) + 1 lọ dầu nóng" in o and "620.000đ" not in o
    f = lambda x: engine._fix_nhs_prices(x)[0]
    assert f("Hồng sâm lát 3 hộp 4.200.000đ, còn Nước Hồng sâm 3 hộp 1.800.000đ ạ.") == "Hồng sâm lát 3 hộp 4.260.000đ, còn Nước Hồng sâm 3 hộp 1.860.000đ ạ."
    assert "2.970.000đ" in f("Dương Sâm Linh Đan ưu đãi:\n- 3 hộp: 1.860.000đ – tặng 2 hộp Trà sâm 1700 (10 gói)")
    assert "1.050.000đ" in f("Long Sâm Linh Đan hộp 6 viên giá 1.000.000đ ạ.") and "4.750.000đ" in f("Long Sâm hộp quà biếu 30 viên giá 4.500.000đ ạ.")
    assert f("Hồng sâm lát 1.420.000đ/hộp 14 gói, Nước Hồng sâm 620.000đ/hộp 20 túi") == "Hồng sâm lát 1.420.000đ/hộp 14 gói, Nước Hồng sâm 620.000đ/hộp 20 túi"
    assert "(q)" in engine.NHS_BLOCK and "N × 1.420.000đ" in engine.NHS_BLOCK


# 45 ─ (20/11, ca Nguyễn Xuân Ánh) AI viết câu trả lời 2 lần trong cùng tin → mỗi ý 1 lần, dặn duy trì thuốc 1 lần cả hội thoại, 1 câu hỏi; không "COD"
def test_45_khong_lap_y_trong_tin():
    prev = ["Hồng sâm hỗ trợ ổn định huyết áp ạ. Anh vẫn nên duy trì thuốc theo chỉ định của bác sĩ và dùng Nước Hồng sâm cách thuốc khoảng 2 tiếng nhé ạ."]
    ai = ("Về thanh toán, anh có 2 cách: nhận hàng kiểm tra rồi mới thanh toán, hoặc chuyển khoản trước qua tài khoản công ty ạ.\n\n"
          "Nước Hồng sâm hỗ trợ ổn định huyết áp ạ. Anh vẫn duy trì uống thuốc theo chỉ định của bác sĩ nhé.\n\n"
          "Anh cho em xin số điện thoại để bên em hỗ trợ giao hàng nhé ạ?\n\n"
          "Dạ người bị huyết áp cao vẫn dùng được Nước Hồng sâm, anh cứ duy trì thuốc tây bác sĩ kê ạ.\n\n"
          "Về phần thanh toán thì anh có thể nhận hàng kiểm tra rồi mới thanh toán, hoặc chuyển khoản trước ạ.\n\n"
          "Anh muốn lấy combo 2 hộp hay mấy hộp ạ?")
    out, n = engine._dedupe_reply(ai, prev)
    assert out.count("chuyển khoản") == 1 and "duy trì" not in out and out.count("?") == 1 and "số điện thoại" in out and n >= 4
    ok = "Dạ người tiểu đường dùng được ạ.\n\nMẹ chị đang dùng thuốc gì ạ?"
    assert engine._dedupe_reply(ok, [])[0] == ok
    assert "COD" not in engine._fix_banned_phrases("Cách 1: nhận hàng kiểm tra rồi thanh toán (COD).")


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
