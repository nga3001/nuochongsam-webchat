"""Ca thử riêng cho bot Sâm Thái Minh (v0.1.17) — kiểm ở mức CÔNG CỤ và LUẬT, không gọi API.

Chạy:  python3 tests/test_sam_12ca.py      (hoặc: pytest tests/test_sam_12ca.py)
Phần hội thoại thật (giọng văn, số câu hỏi, ảnh...) xem file tests/ca-thu-tay-12ca.md — người thử chạy tay trên web chat.

Mỗi ca kiểm 2 lớp:
  1. Công cụ trả đúng (compliance_check / build_order / kb) — đây là chỗ bot lấy dữ liệu, sai ở đây thì bot chắc chắn sai.
  2. Luật trong system prompt có câu chỉ dẫn tương ứng — nếu ai đó lỡ xoá luật, ca thử báo đỏ.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import tools_core as t  # noqa: E402

KB = t.load_kb()
ADDR = "12 Lê Lợi, Hà Đông, Hà Nội"
PHONE = "0912345678"


def _prompt():
    try:
        import engine
        return engine.build_system_prompt()
    except Exception as e:  # thiếu db/router khi chạy lẻ → bỏ qua lớp 2
        print(f"   (bỏ qua kiểm luật prompt: {e.__class__.__name__})")
        return None


PROMPT = _prompt()


def _has(*words):
    if PROMPT is None:
        return
    for w in words:
        assert w in PROMPT, f"system prompt thiếu: {w!r}"


def _verdict(flag, pid):
    return t.compliance_check([flag], pid)


def _actions(r):
    return " ".join(h.get("action", "") for h in r["absolute_hits"] + r["caution_hits"])


# 1 ─ Khách hỏi chung "giá sao em" dưới bài Hồng sâm lát → báo giá lát, 3 phần, combo + quà
def test_01_hoi_gia_chung_chung():
    q = KB["scripts_approved"]["price_quote_hsvn"]
    price = t.fmt_vnd(KB["products"]["hsvn_lat"]["packages"][0]["price_retail"])
    assert price in q, "báo giá phải lấy đúng giá trong kb (gom giá một chỗ)"
    assert "Trà sâm" in q
    if PROMPT is not None:
        import engine
        assert "Hồng sâm" in engine.focus_block("hsvn_lat", "post")


# 2 ─ (15/10) Mẹ đang cho con bú → KHÔNG dùng bất kỳ sản phẩm nào, không gợi ý Hồng sâm nước
def test_02_cho_con_bu():
    for pid in KB["products"]:
        assert _verdict("breastfeeding", pid)["verdict"] == "BLOCK", pid
    assert "cai sữa" in KB["scripts_approved"]["breastfeeding"]
    _has("KHÔNG dùng BẤT KỲ sản phẩm nào")


# 3 ─ Bà bầu → không dùng lát
def test_03_co_thai():
    assert _verdict("pregnant", "hsvn_lat")["verdict"] == "BLOCK"


# 4 ─ Huyết áp cao đang uống thuốc → dùng được, giải thích cơ chế, khuyên duy trì thuốc (1 lần)
def test_04_huyet_ap_dang_uong_thuoc():
    for f in ("hypertension", "hypotension", "bp_uncontrolled"):
        assert _verdict(f, "hsvn_lat")["verdict"] == "CAUTION"
        assert "Dùng được" in _actions(_verdict(f, "hsvn_lat"))
    bp = KB["scripts_approved"]["bp_question"]
    assert "một phần hỗ trợ" in bp and "bác sĩ" in bp and "2 tiếng" in bp      # 15/10: nói mềm, cách thuốc 2 tiếng
    assert "duy trì" in KB["scripts_approved"]["maintain_meds"] and "2 tiếng" in KB["scripts_approved"]["maintain_meds"]


# 5 ─ Bố đang hóa trị → Hồng sâm, Dương/Long Sâm dùng được; Tam Sâm Đan thì chuyển (chưa có hướng dẫn)
def test_05_hoa_tri():
    assert "Dùng được" in _actions(_verdict("cancer_treatment", "hsvn_lat"))
    assert "disease_no_guidance" in _actions(_verdict("cancer_treatment", "tam_sam_dan"))   # 14/10: Dương/Long Sâm dùng được
    assert "MR2" in KB["scripts_approved"]["disease_question"]


# 6 ─ Tai biến do xuất huyết → không tự tư vấn, chuyển chuyên viên
def test_06_tai_bien_xuat_huyet():
    for pid in KB["products"]:
        a = _actions(_verdict("stroke_hemorrhagic", pid))
        assert "HANDOFF" in a or "disease_no_guidance" in a, pid


# 7 ─ Suy thận: độ 1–2 dùng được, độ 3–4 chuyển chuyên viên
def test_07_suy_than():
    assert "Dùng được" in _actions(_verdict("kidney_failure_1_2", "hsvn_lat"))
    assert "bác sĩ" in _actions(_verdict("stent_lt6m", "hsvn_lat"))
    assert "1/2 gói" in _actions(_verdict("stent_6_12m", "hsvn_lat"))
    assert "Dùng được" in _actions(_verdict("stent_6_12m", "hsmo_tui")) or "dùng được" in _actions(_verdict("stent_6_12m", "hsmo_tui"))
    assert "bác sĩ" in _actions(_verdict("stent_6_12m", "duong_sam"))
    assert "1 viên" in _actions(_verdict("stent_ge12m", "long_sam"))
    assert "150" in _actions(_verdict("hypertension", "duong_sam"))
    assert "hỏi ý kiến bác sĩ" in _actions(_verdict("kidney_failure_3_4", "hsmo_tui"))
    assert "HANDOFF" in _actions(_verdict("kidney_transplant_recent", "hsvn_lat"))
    au = _actions(_verdict("stomach_ulcer", "hsvn_lat"))   # 16/10: loét dạ dày
    assert "còn triệu chứng đau" in au and "ổn định" in au
    a34 = _actions(_verdict("kidney_failure_3_4", "hsvn_lat"))   # 16/10: dùng được nhưng hỏi bác sĩ trước
    assert "hỏi ý kiến bác sĩ" in a34 and "HANDOFF" not in a34


# 8 ─ Đang uống thuốc chống đông 3 tháng → chuyển chuyên viên
def test_08_chong_dong_duoi_6_thang():
    assert "HANDOFF" in _actions(_verdict("anticoagulant_lt6m", "hsvn_lat"))


# 9 ─ "Uống có khỏi hẳn không, bỏ thuốc được không" → cấm hứa chữa khỏi, không khuyên bỏ thuốc
def test_09_chua_khoi_bo_thuoc():
    _has("CẤM TUYỆT ĐỐI", "không bảo khách bỏ thuốc")


# 10 ─ Chê đắt nhiều lần → quà mốc 1 hộp chỉ khi chê đắt; sau ≥2 lần thuyết phục chuyển Hồng sâm nước
def test_10_che_dat():
    thuong = t.build_order([{"sku": "hsvn-lat-14", "qty": 1}], "A", PHONE, ADDR)
    assert thuong["promo_applied"] == []
    che = t.build_order([{"sku": "hsvn-lat-14", "qty": 1}], "A", PHONE, ADDR, price_objection=True)
    assert "10 gói" in che["promo_applied"][0]["gift"]
    assert KB["scripts_approved"]["price_objection_switch"] and "NGAY KHI" in KB["scripts_approved"]["price_objection_switch"]
    _sw = KB["scripts_approved"]["price_objection_switch"]
    assert "dạng túi" in _sw and "dạng nước tinh chất" not in _sw, "v0.1.20: mời Nước HS dạng túi"
    assert KB["need_map"]["tiet_kiem_de_uong"]["core"] == "hsmo_tui"
    _has("MỜI NƯỚC HỒNG SÂM = DẠNG TÚI")
    _has("KHÁCH CHÊ ĐẮT VÀ MUỐN DỪNG")   # 16/10: chê đắt + thôi → mời Nước Hồng sâm ngay, chưa xin SĐT


# 11 ─ Chốt 2 hộp lát đủ thông tin → freeship, quà Trà 20 gói, câu xác nhận đúng mẫu chị Nga
def test_11_chot_don_day_du():
    o = t.build_order([{"sku": "hsvn-lat-14", "qty": 2}], "Trịnh Thị Chanh", PHONE, ADDR)
    assert o["ready_to_confirm"] and o["ship_fee"] == 0
    assert "20 gói" in o["promo_applied"][0]["gift"]
    for k in ("Tên khách hàng", "Số điện thoại", "Địa chỉ nhận hàng", "Sản phẩm + Số lượng",
              "Quà tặng kèm", "Tổng tiền đơn hàng"):
        assert k in o["confirm_text"], k
    o4 = t.build_order([{"sku": "hsvn-lat-14", "qty": 4}], "A", PHONE, ADDR)
    assert "2 hộp Trà sâm" in o4["promo_applied"][0]["gift"]
    thieu = t.build_order([{"sku": "hsvn-lat-14", "qty": 1}], "A", PHONE, "")
    assert not thieu["ready_to_confirm"] and "address" in thieu["missing_info"]


# 12 ─ Hồng sâm nước 1 chai mất ship, từ 2 chai miễn ship; khách cũ → không tự chốt, chuyển người
def test_12_ship_nuoc_va_khach_cu():
    assert t.build_order([{"sku": "hsmo-chai", "qty": 1}], "A", PHONE, ADDR)["ship_fee"] > 0
    assert t.build_order([{"sku": "hsmo-chai", "qty": 2}], "A", PHONE, ADDR)["ship_fee"] == 0
    # v0.1.16 (14/10): khách cũ — Hồng sâm lát có bảng quà riêng, bot tự chốt; sản phẩm chưa có bảng → chuyển nhân viên
    r = t.build_order([{"sku": "hsvn-lat-14", "qty": 2}], "A", PHONE, ADDR, customer_type="returning")
    assert "Heviho" in r["promo_applied"][0]["gift"] and r["program"] == "returning_customer"
    r5 = t.build_order([{"sku": "hsvn-lat-14", "qty": 6}], "A", PHONE, ADDR, customer_type="returning")
    assert "8 hộp viên ngậm Heviho" in r5["promo_applied"][0]["gift"]       # 6 hộp áp mốc 5
    assert t.build_order([{"sku": "hsmo-chai", "qty": 1}], customer_type="returning")["handoff_required"]


# 13 ─ (14/10) Ship Trà / Tam Sâm Đan / Đông trùng: dưới 1 triệu 20.000đ, từ 1 triệu miễn phí; Dương Sâm 1 hộp miễn ship
def test_13_ship_nguong_1_trieu():
    assert t.build_order([{"sku": "tamsamdan-30", "qty": 1}], "A", PHONE, ADDR)["ship_fee"] == 20000
    assert t.build_order([{"sku": "dongtrung-30", "qty": 2}], "A", PHONE, ADDR)["ship_fee"] == 0
    assert t.build_order([{"sku": "duongsam-10", "qty": 1}], "A", PHONE, ADDR)["ship_fee"] == 0
    assert "error" in t.build_order([{"sku": "tra-nguyenla-40", "qty": 1}], "A", PHONE, ADDR)   # hết hàng


# 14 ─ (14/10) Bảng an toàn mới: mẹ sau sinh dưới 6 tháng, Dương/Long Sâm, tai biến xuất huyết
def test_14_an_toan_moi():
    assert _verdict("postpartum_lt6m", "hsmo_tui")["verdict"] == "CAUTION"      # 15/10: sau sinh không cho con bú dùng được ngay
    assert _verdict("postpartum_lt6m", "hsvn_lat")["verdict"] == "BLOCK"
    assert _verdict("bp_uncontrolled", "duong_sam")["verdict"] == "CAUTION"
    assert "Dùng được" in _actions(_verdict("cancer_treatment", "long_sam"))
    assert _verdict("pregnant", "long_sam")["verdict"] == "BLOCK"
    assert _verdict("child_any", "long_sam")["verdict"] == "BLOCK"
    assert "Dùng được" in _actions(_verdict("anticoagulant_ge6m", "hsmo_chai"))
    assert "HANDOFF" in _actions(_verdict("stroke_hemorrhagic", "duong_sam"))


# 15 ─ (15/10) Góp ý anh Huy: bỏ tự trồng / gấp 3 lần / 50%; thuốc tây cách 2 giờ; Long Sâm HA chưa ổn định chuyển; FAQ mới
def test_15_gop_y_anh_huy():
    sa = KB["scripts_approved"]
    import re
    for k in ("price_why", "origin", "reassure_fake", "disease_question"):
        # chỉ soi phần bot NÓI với khách: câu bắt đầu bằng 'Dạ ...' (bỏ phần dặn nội bộ "KHÔNG nói ...")
        said = re.findall(r"'(Dạ[^']*)'", sa[k]) or [re.sub(r"KHÔNG nói '[^']*'", "", sa[k])]
        for txt in said:
            for bad in ("tự trồng", "gấp khoảng 3 lần", "50%", "chống khối u", "minh bạch từ vườn"):
                assert bad not in txt, (k, bad)
    assert "MR2 mà sâm Hàn Quốc không có" in sa["price_why"] and "VIGH" in sa["price_why"]
    assert "nhà máy Thái Minh" in sa["origin"] and "Lâm Đồng" in sa["origin"]      # 15/10: câu chính + câu vườn khi hỏi thẳng
    assert "2 giờ" in _actions(_verdict("antibiotic", "hsvn_lat")) and "2 giờ" in _actions(_verdict("antibiotic", "long_sam"))
    assert "HANDOFF" in _actions(_verdict("bp_uncontrolled", "long_sam"))
    assert "bác sĩ" in _actions(_verdict("aortic_aneurysm", "hsmo_chai"))
    assert "sáng/trưa" in _actions(_verdict("insomnia", "duong_sam"))
    assert "homestay" not in sa["farm_visit"].replace("KHÔNG nhắc homestay", "") and "SĐT" in sa["farm_visit"]
    assert "dược sĩ" not in sa["expert_referral"]
    assert "bao gồm VAT" in sa["vat_invoice"] and "Saponin" in sa["no_ginseng_smell"]
    assert "có quà, lời hơn mua lẻ" in sa["upsell_double"] and "quà tặng tốt nhất" in sa["upsell_double"] and "MUA 15 TẶNG 1" in sa["upsell_double"] and "KHÔNG nói 'giảm giá'" in sa["upsell_double"] and "bên em sẽ gọi" in sa["order_after_confirm"]
    assert "ĐÚNG NGUYÊN VĂN" in sa["upsell_double"] and "thấm sâu" in sa["upsell_double"]
    _has("XƯNG HÔ THEO TÊN", "ĐÚNG NGUYÊN VĂN")


# 16 ─ (16/10) 2 lớp chặn theo kinh nghiệm bot Bình Vị: SĐT/địa chỉ phải lấy từ tin khách; lọc nháp nội bộ
def test_16_lop_chan():
    try:
        import engine as e
    except Exception as ex:
        print(f"   (bỏ qua test_16: {ex.__class__.__name__})"); return
    u = ["Chị Nga, đội 3 thôn Đông, Thanh Tùng, Thanh Miện, Hải Dương", "sđt 0912 345 678"]
    ok, notes = e.check_order_fields({"phone": "0912345678", "addr": "Đội 3 thôn Đông, Thanh Tùng, Thanh Miện, Hải Dương"}, u)
    assert ok["phone"] and ok["addr"] and not notes
    bad, notes = e.check_order_fields({"phone": "0987654321", "addr": "12 Lê Lợi, Hà Đông, Hà Nội"}, u)
    assert bad["phone"] is None and bad["addr"] is None and len(notes) == 2
    clean, n = e.strip_internal("Dạ em chào chị ạ.\n\nTôi sẽ gọi build_order để tính.\n\nThinking: khách mua 2 hộp\n\nCombo 2 hộp ạ.")
    assert n == 2 and "build_order" not in clean and "Combo 2 hộp" in clean
    assert e.strip_internal("Dạ Hồng sâm lát dùng buổi sáng ạ.\n\nAnh/chị đang dùng thuốc gì không ạ?")[1] == 0
    _has("guard_notes", "KHÔNG tự điền")
    # v0.1.21 (16/10): liều tiểu đường không lẫn chống đông; lưới chặn cụm cấm
    import engine as _e
    d = KB["products"]["hsvn_lat"]["dosage"]["diabetes"] if "products" in KB else ""
    assert (not d) or ("trưa 1/2" in d and "tủ lạnh" in d)
    assert "thấm sâu" not in _e._fix_banned_phrases("Liệu trình 3 tháng để dưỡng chất thấm sâu.")
    assert "kiểm soát đường huyết" in _e._fix_banned_phrases("hỗ trợ cải thiện mỡ máu, tiểu đường ạ")
    _has("LIỀU RIÊNG = CHÉP ĐÚNG", "Phuong Anh Nguyen")
    assert "KHÔNG bắt để SĐT" in KB["scripts_approved"]["human_request"]
    _has("KHÁCH MUỐN CHAT VỚI NGƯỜI")
    import pancake_adapter as _pa
    assert _pa.call_name("Ngoan Do Thi") == "chị Ngoan" and _pa.call_name("Nguyễn Văn Hùng") == "anh Hùng"
    assert _pa.call_name("Phuong Anh Nguyen") == ""
    assert "Rg1, Rd" in KB["scripts_approved"]["diabetes_honey"] and "trước ăn 30 phút" in KB["scripts_approved"]["diabetes_honey"]
    _src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pancake_adapter.py"), encoding="utf-8").read()
    assert "Dược sĩ bên em" not in _src and "dược sĩ xem" not in _src, "câu gửi khách không được nhắc dược sĩ"



# 17 ─ (25/10, ca Sâm Lê) lưới lọc bản nháp KHÔNG được làm mất dòng combo 2, 3 tháng; quà/giá combo luôn đúng bảng
def test_17_combo_khong_mat_dong():
    try:
        import engine as e
    except Exception as ex:
        print(f"   (bỏ qua test_17: {ex.__class__.__name__})"); return
    q = KB["scripts_approved"]["price_quote_hsvn"]
    lines = [l for l in q.split("'") if "Combo" in l and "hộp)" in l][:3]
    txt = "Chương trình tri ân khách hàng mới:\n" + "\n".join(lines)
    clean, _ = e.strip_internal(txt)
    for l in lines:
        assert l in clean, l
    bad = "✅ Combo 2 tháng (4 hộp) – 5.000.000đ – tặng 4 hộp Trà sâm"
    fixed, _ = e._fix_prices(e._fix_combo_gifts(bad))
    assert "5.680.000đ" in fixed and "2 hộp Trà sâm 1700 loại 20 gói" in fixed

if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    bad = 0
    for n, f in tests:
        try:
            f()
            print(f"ĐẠT   {n}")
        except AssertionError as e:
            bad += 1
            print(f"TRƯỢT {n}: {e}")
    print(f"\n{len(tests) - bad}/{len(tests)} ca đạt")
    sys.exit(1 if bad else 0)
