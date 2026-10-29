"""Engine tools — Sâm Thái Minh (nhân bản từ Bình Vị v1.0, mở rộng ĐA SẢN PHẨM).
Đọc brain/kb.json (nguồn chân lý duy nhất). Stdlib only.
LLM KHÔNG được tự bịa số liệu — mọi giá/liều/an toàn/tổng đơn lấy từ đây.
v0.1.14 (13/10/2026, chị Nga): freeship mọi sản phẩm từ 1 hộp trừ Hồng sâm dạng nước (vẫn áp quà);
mẫu xác nhận đơn mới (tên ngắn); upsell 1 hộp → 2 hộp, 2 hộp → 4 hộp; thêm flag chưa có hướng dẫn.
"""
import json
import os
import re
import threading

_BRAIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brain")
_KB_PATH = os.path.join(_BRAIN_DIR, "kb.json")
_lock = threading.Lock()


def load_kb():
    with _lock, open(_KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_kb(data: dict):
    with _lock, open(_KB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# v0.3.0 (23/10): page Dương Sâm (ENV PAGE_FOCUS_PRODUCT=duong_sam) đọc bộ não riêng brain/duongsam/ nếu có; kb.json dùng chung
IS_DS = (os.environ.get("PAGE_FOCUS_PRODUCT") or "").strip().lower() == "duong_sam"
# v0.4.0 (26/10): bot Nước Hồng sâm (ENV PAGE_FOCUS_PRODUCT=hsmo_tui hoặc hsmo_chai) đọc bộ não riêng brain/nuochongsam/
IS_NHS = (os.environ.get("PAGE_FOCUS_PRODUCT") or "").strip().lower() in ("hsmo_tui", "hsmo_chai")
# Bot NHS: sản phẩm chính + 3 dòng cao cấp được nói khi khách hỏi sản phẩm khác (tầng 2)
NHS_PREMIUM = ("hsvn_lat", "long_sam", "duong_sam")


def load_brain_file(name: str) -> str:
    path = os.path.join(_BRAIN_DIR, name)
    if IS_DS and os.path.exists(os.path.join(_BRAIN_DIR, "duongsam", name)):
        path = os.path.join(_BRAIN_DIR, "duongsam", name)
    if IS_NHS and os.path.exists(os.path.join(_BRAIN_DIR, "nuochongsam", name)):
        path = os.path.join(_BRAIN_DIR, "nuochongsam", name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def fmt_vnd(n):
    return f"{n:,.0f}đ".replace(",", ".")


def find_package(kb, sku):
    for pid, p in kb["products"].items():
        for pkg in p.get("packages", []):
            if pkg["sku"] == sku:
                return p, pkg
    return None, None


# ---------------------------------------------------------------- helpers
def _pid(kb, arg):
    """Nhận product id, sku hoặc tên gọi khác (aka) → product id."""
    a = (arg or "").strip().lower()
    if not a:
        return None
    if a in kb["products"]:
        return a
    for pid, p in kb["products"].items():
        if any(k["sku"] == a for k in p.get("packages", [])):
            return pid
    for pid, p in kb["products"].items():
        names = [p["name"].lower()] + [x.lower() for x in p.get("aka", [])]
        if any(a == n or a in n for n in names):
            return pid
    return None


def _pkg_view(k):
    d = {"sku": k["sku"], "label": k["label"], "price": fmt_vnd(k["price_retail"]),
         "in_stock": k.get("in_stock", True)}
    if k.get("note"):
        d["note"] = k["note"]
    return d


# ---------------------------------------------------------------- kb_lookup
def kb_lookup(command: str, arg: str = "") -> dict:
    kb = load_kb()
    if command == "products":
        return {"products": [{
            "id": pid, "name": p["name"], "type": p.get("type"), "summary": p["summary"], "role": p.get("role"),
            "packages": [_pkg_view(k) for k in p["packages"]],
        } for pid, p in kb["products"].items()],
            "overview_script": kb.get("scripts_approved", {}).get("product_overview"),
            "reminder": "role=on_request_only (Tam Sâm Đan, Đông trùng hạ thảo, Trà sâm, Rượu sâm, Sâm tươi): KHÔNG chủ động giới thiệu, KHÔNG gợi ý thay thế — chỉ tư vấn khi khách TỰ hỏi đích danh hoặc khách đến từ bài viết/quảng cáo của chính sản phẩm đó."}
    if command == "product":
        pid = _pid(kb, arg)
        if not pid:
            return {"error": f"unknown product '{arg}'", "valid": list(kb["products"])}
        p = dict(kb["products"][pid])
        p["compliance"] = kb["compliance"]["products"].get(pid, {})
        return p
    if command == "price":
        pid = _pid(kb, arg) if arg else None
        if arg and not pid:
            return {"error": f"unknown product/sku '{arg}'", "valid": list(kb["products"])}
        rows = []
        for xid, p in kb["products"].items():
            if pid and xid != pid:
                continue
            for k in p["packages"]:
                if arg and arg.lower() == k["sku"]:
                    rows = [dict(product=p["name"], **_pkg_view(k))]
                    break
                rows.append(dict(product=p["name"], **_pkg_view(k)))
        return {"price_list": rows, "shipping": kb.get("shipping", {}).get("fee_display"),
                "reminder": "Hàng in_stock=false: báo 'tạm hết hàng', gợi ý quy cách khác. Báo giá theo scripts_approved.price_quote_hsvn (3 phần, 1 câu chốt)."}
    if command == "dosage":
        pid = _pid(kb, arg)
        if not pid:
            return {"error": "cần product id", "valid": list(kb["products"])}
        p = kb["products"][pid]
        return {"product": p["name"], "dosage": p.get("dosage", {})}
    if command == "programs":
        pid = _pid(kb, arg) if arg else None
        progs = {}
        for k, v in kb["programs"].items():
            if not v.get("active"):
                continue
            v = dict(v)
            if pid and "rules" in v:
                skus = {x["sku"] for x in kb["products"][pid]["packages"]}
                v["rules"] = [r for r in v["rules"] if r["if_sku"] in skus]
            progs[k] = v
        inactive = {k: v.get("note", "") for k, v in kb["programs"].items() if not v.get("active")}
        if not _promo_active(kb):
            progs.pop("new_customer", None)
            inactive["new_customer"] = "Chương trình khách mới đã HẾT HẠN (" + kb["programs"]["new_customer"].get("period_display", "") + ") — không hứa quà, chuyển nhân viên báo chương trình mới."
        return {"active_programs": progs, "inactive_do_not_promise": inactive, "shipping": kb.get("shipping", {}),
                "reminder": "Ưu đãi CHỈ cho KHÁCH MỚI (chưa từng mua Sâm Thái Minh). Khách TỰ nói đã từng mua → khách cũ, chuyển nhân viên."}
    if command == "shipping":
        return kb.get("shipping", {})
    if command == "brand":
        return kb["_meta"]
    if command == "pharmacy":
        return kb.get("pharmacy_policy", {"error": "no pharmacy policy"})
    if command == "scripts":
        return kb.get("scripts_approved", {})
    return {"error": f"unknown command '{command}'",
            "valid": ["products", "product", "price", "dosage", "programs", "shipping", "brand", "pharmacy", "scripts"]}


# ---------------------------------------------------------- compliance_check
# Flag hợp lệ nhưng tài liệu KHÔNG có hướng dẫn cho sản phẩm đó → NO_GUIDANCE (không tự khẳng định).
_NO_GUIDANCE_FLAGS = {"pregnant", "breastfeeding", "child_under3", "child_under6", "child_6_11", "child_under12", "child_any",
                      "under18", "anticoagulant_ge6m", "anticoagulant_lt6m", "kidney_transplant_recent", "thalassemia",
                      "aortic_aneurysm", "bp_uncontrolled",
                      # v0.1.14 (chốt 13/10): bệnh chưa có tài liệu cho sản phẩm đó → không tự tư vấn
                      "kidney_failure_3_4", "rheumatoid_arthritis", "thyroid", "stroke_history", "cancer_treatment",
                      "stroke_hemorrhagic", "postpartum_lt6m", "kidney_failure_acute", "liver_disease"}


def compliance_check(flags: list, product_id: str = "") -> dict:
    kb = load_kb()
    comp = kb["compliance"]
    flags = set(f.strip() for f in (flags or []) if f and f.strip())
    pid = _pid(kb, product_id)
    if not pid:
        return {"error": f"cần product_id hợp lệ (sản phẩm đang tư vấn)", "valid": list(kb["products"])}
    rules = comp["products"].get(pid, {"absolute": [], "caution": []})
    all_flags = set(comp.get("all_flags", []))
    abs_keys = {r["key"] for r in rules.get("absolute", [])}
    cau_keys = {r["key"] for r in rules.get("caution", [])}
    hit_absolute = [r for r in rules.get("absolute", []) if r["key"] in flags]
    hit_caution = [r for r in rules.get("caution", []) if r["key"] in flags]
    no_guidance = sorted(f for f in flags if f in all_flags and f not in abs_keys and f not in cau_keys
                         and f in _NO_GUIDANCE_FLAGS)
    unknown = sorted(f for f in flags if f not in all_flags)

    if hit_absolute:
        verdict, message = "BLOCK", "KHÔNG dùng / KHÔNG bán sản phẩm này cho khách. Làm đúng action từng mục; gợi ý sản phẩm khác nếu action có nêu."
    elif no_guidance:
        verdict, message = "NO_GUIDANCE", comp.get("unknown_action", "")
    elif hit_caution:
        verdict, message = "CAUTION", "Tư vấn được nhưng làm đúng action từng mục (liều riêng / chuyển chuyên môn nếu action yêu cầu)."
    else:
        verdict, message = "OK", "Không phát hiện chống chỉ định trong tài liệu. Được tư vấn/chốt đơn."

    p = kb["products"][pid]
    return {
        "product": p["name"], "verdict": verdict, "message": message,
        "absolute_hits": hit_absolute, "caution_hits": hit_caution, "no_guidance_flags": no_guidance,
        "unknown_flags": unknown, "valid_flags": sorted(all_flags),
        "disclaimer_required": comp_disclaimer(kb, pid),
        "reminder": ("Bệnh/tình trạng KHÔNG có trong valid_flags và không có trong tài liệu → KHÔNG suy luận, dùng "
                     "scripts_approved.disease_no_guidance. Mọi công dụng luôn có chữ 'hỗ trợ'. An toàn khách > doanh số."),
    }


def comp_disclaimer(kb, pid):
    p = kb["products"][pid]
    return kb["_meta"]["disclaimer"] if p.get("disclaimer_required") else None


# ------------------------------------------------------------------ recommend
def _today():
    import datetime
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat()
    except Exception:
        return datetime.date.today().isoformat()


def _promo_active(kb, today=None):
    p = kb["programs"]["new_customer"]
    d = today or _today()
    return bool(p.get("active")) and p.get("valid_from", "0000") <= d <= p.get("valid_to", "9999")


def _gift_for(kb, sku, qty, today=None, price_objection=False, program="new_customer"):
    """v0.1.12: dòng có condition=price_objection (Hồng sâm lát 1 hộp — brief 25/09) CHỈ áp khi khách chê đắt.
    v0.1.16: program="returning_customer" → bảng quà khách cũ (chị Nga 14/10)."""
    prog = kb["programs"].get(program) or {}
    if program == "new_customer":
        if not _promo_active(kb, today):
            return None
    elif not prog.get("active"):
        return None
    rules = [r for r in prog.get("rules", []) if r["if_sku"] == sku and r["min_qty"] <= qty
             and (not r.get("condition") or (r["condition"] == "price_objection" and price_objection))]
    return max(rules, key=lambda r: r["min_qty"]) if rules else None


def recommend(need_tags: list, budget: str = "normal") -> dict:
    kb = load_kb()
    need_map = kb["need_map"]
    tags = [t.strip() for t in (need_tags or []) if t and t.strip()]
    valid = [t for t in tags if t in need_map]
    invalid = [t for t in tags if t not in need_map]
    if not valid:
        return {"error": "no valid need_tags", "invalid": invalid, "valid": list(need_map)}
    n = need_map[valid[0]]
    pids = [n["core"]] + [x for x in n.get("alt", []) if x != n["core"]]
    premium_note = None
    if IS_NHS and n["core"] not in ("duong_sam", "tra_1700", "tra_nguyen_la"):
        # v0.4.0: bot Nước Hồng sâm — NHS luôn là sản phẩm chính; dòng cao cấp (lát / Long Sâm) chỉ là phương án khi KHÁCH hỏi loại khác
        main = "hsmo_chai" if (os.environ.get("PAGE_FOCUS_PRODUCT") or "").strip().lower() == "hsmo_chai" else "hsmo_tui"
        prem = [x for x in pids if x in NHS_PREMIUM]
        pids = [main] + prem[:1]
        premium_note = ("Bot Nước Hồng sâm: giới thiệu Nước Hồng sâm là sản phẩm CHÍNH. Phương án cao cấp trong alternatives CHỈ nói khi khách "
                        "CHỦ ĐỘNG hỏi loại khác / tốt hơn / cao cấp hơn (scripts_approved.upgrade_premium); khách không hỏi → KHÔNG nhắc.")
    out = []
    for pid in pids:
        p = kb["products"][pid]
        sku = p["recommended_package"]
        pkg = next(k for k in p["packages"] if k["sku"] == sku)
        tiers = {}
        levels = [r["min_qty"] for r in kb["programs"]["new_customer"]["rules"] if r["if_sku"] == sku] or [1]
        pick = {"basic": 1, "standard": next((q for q in levels if q >= 2), 1), "premium": next((q for q in levels if q >= 5), max(levels))}
        for name, q in pick.items():
            g = _gift_for(kb, sku, q)
            tiers[name] = {"qty": q, "label": f"{q} x {pkg['label']}", "total_display": fmt_vnd(pkg["price_retail"] * q),
                           "gift_new_customer": (g or {}).get("gift") or ("chỉ tặng khi khách chê đắt: " + next(
                               (r["gift"] for r in kb["programs"]["new_customer"]["rules"]
                                if r["if_sku"] == sku and r["min_qty"] == q and r.get("condition")), "") or "không có quà"),
                           "freeship_new_customer": (g or {}).get("freeship")}
        out.append({"product_id": pid, "product": p["name"], "summary": p["summary"], "package": _pkg_view(pkg), "tiers": tiers})
    return {
        "needs_matched": [need_map[t]["label"] for t in valid], "invalid_tags": invalid,
        "note_for_need": " ".join(x for x in (n.get("note"), premium_note) if x) or None,
        "core_product": out[0], "alternatives": out[1:],
        "recommended_tier": "basic" if budget == "low" else ("premium" if budget == "high" else "standard"),
        "rules": "Giới thiệu SẢN PHẨM CHÍNH trước (tối đa 1 sản phẩm thay thế nếu khách chê giá/không hợp). "
                 "Báo combo theo tháng; gói lẻ 1 hộp chỉ khi khách chê đắt/muốn dùng thử. Luôn chạy compliance_check(product_id) trước khi chốt.",
    }


# ---------------------------------------------------------------- build_order
def _phone_valid(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone or "")
    return len(digits) == 10 and digits.startswith("0")


def _addr_complete(addr: str) -> bool:
    """Địa chỉ cần đủ 3 phần: số nhà/đường, phường/xã, tỉnh/thành."""
    if not addr:
        return False
    parts = [p for p in re.split(r"[,;\n]", addr) if p.strip()]
    return len(parts) >= 3 or len(addr.split()) >= 6


def _ship_fee(kb, addr):
    sh = kb.get("shipping", {})
    a = (addr or "").lower()
    if "hà nội" in a or "ha noi" in a or "hn" in a.split():
        if any(k.lower() in a for k in sh.get("hn_inner_keywords", [])):
            return sh.get("fee_hn_inner", 15000), "Hà Nội nội thành"
    if not addr:
        return None, "chưa có địa chỉ"
    return sh.get("fee_other", 20000), "ngoại thành Hà Nội / tỉnh khác"


HANDOFF_SKUS = {"samtuoi-kg", "ruou-hu-35", "ruou-hu-4"}


# v0.1.97 (28/10, rà soát giá): tên ngắn theo QUY CÁCH — trước đây đơn Nước Hồng sâm hộp 10 túi in "(hộp 20 túi)", Long Sâm 30 viên / Hồng sâm 50 gói
# không ghi quy cách → khách và lưới tổng tiền hiểu nhầm loại hộp.
PKG_SHORT = {"hsvn-lat-50": "Hồng sâm dạng lát (hộp 50 gói)", "hsmo-tui": "Hồng sâm dạng nước (hộp 20 túi)", "hsmo-tui-10": "Hồng sâm dạng nước (hộp 10 túi)",
             "hsmo-chai": "Hồng sâm dạng nước (chai 175ml)", "longsam-6": "Long Sâm Linh Đan (hộp 6 viên)", "longsam-30": "Long Sâm Linh Đan (hộp 30 viên)",
             "tra1700-20": "Trà sâm 1700 (hộp 20 túi lọc)", "tra1700-10": "Trà sâm 1700 (hộp 10 túi lọc)",
             "tra-nguyenla-100": "Trà sâm nguyên lá (hộp 100g)", "tra-nguyenla-40": "Trà sâm nguyên lá (hộp 40g)",
             "ruou-650": "Rượu sâm (chai 650ml)", "ruou-hu-35": "Rượu sâm (hũ 3,5 lít)", "ruou-hu-4": "Rượu sâm (bình 4 lít)"}


def build_order(items: list, name: str = None, phone: str = None, addr: str = None,
                customer_type: str = "unknown", price_objection: bool = False) -> dict:
    kb = load_kb()
    # v0.1.12 (brief 25/09): báo ưu đãi ngay, không bắt hỏi khách mới/cũ → chưa rõ thì coi là khách MỚI;
    # chỉ khi khách TỰ nói đã từng mua mới là returning.
    if customer_type not in ("new", "returning"):
        customer_type = "new"
    # v0.1.16 (chị Nga 14/10): khách cũ có bảng quà riêng (hiện chỉ Hồng sâm lát hộp 14 gói). Sản phẩm khác
    # chưa có bảng khách cũ → giữ cách cũ: xin SĐT, nhân viên báo chương trình.
    ret_prog = kb["programs"].get("returning_customer") or {}
    ret_skus = {r["if_sku"] for r in ret_prog.get("rules", [])} if ret_prog.get("active") else set()
    if customer_type == "returning" and not all(((it.get("sku") or "").strip().lower() in ret_skus) for it in (items or [{}])):
        need_phone = not (phone and _phone_valid(phone))
        return {
            "handoff_required": True, "reason": "returning_customer_no_table",
            "action": ("Khách đã từng mua Sâm Thái Minh, sản phẩm này CHƯA có bảng ưu đãi khách cũ — KHÔNG tự báo quà, KHÔNG tự chốt. "
                       "Nói có chương trình ưu đãi dành riêng cho khách hàng thân thiết. "
                       + ("Xin số điện thoại: 'Anh/chị cho em xin lại số điện thoại, em chuyển chuyên viên kiểm tra "
                          "và báo chương trình ưu đãi dành riêng cho khách hàng thân thiết sớm ạ.'" if need_phone else
                          "Đã có SĐT — 'Em chuyển chuyên viên kiểm tra và báo chương trình ưu đãi dành riêng cho anh/chị sớm ạ.'")
                       + " Chèn [HANDOFF: khách cũ mua tiếp | SĐT | 2] CUỐI tin."),
        }
    lines_items, errors, goods_total, handoff_skus = [], [], 0, []
    for it in items or []:
        sku, qty = (it.get("sku", "") or "").strip().lower(), int(it.get("qty", 1))
        p, pkg = find_package(kb, sku)
        if not pkg:
            errors.append(f"SKU không hợp lệ: {sku}")
            continue
        if not pkg.get("in_stock", True):
            errors.append(f"{p['name']} {pkg['label']} đang TẠM HẾT HÀNG — mời khách chọn quy cách khác")
            continue
        if qty < 1:
            errors.append(f"Số lượng không hợp lệ: {sku}")
            continue
        sub = pkg["price_retail"] * qty
        goods_total += sub
        if sku in HANDOFF_SKUS:
            handoff_skus.append(sku)
        lines_items.append({"product": p["name"], "short_name": PKG_SHORT.get(pkg["sku"]) or p.get("short_name") or p["name"],
                            "product_id": p["id"], "sku": pkg["sku"], "label": pkg["label"],
                            "unit": pkg.get("unit_name", "hộp"),
                            "qty": qty, "unit_price_display": fmt_vnd(pkg["price_retail"]),
                            "subtotal": sub, "subtotal_display": fmt_vnd(sub)})
    if errors:
        return {"error": "invalid order", "details": errors}
    if not lines_items:
        return {"error": "empty order"}

    # --- quà theo bảng khuyến mại (CHỈ khách mới), áp riêng từng sản phẩm ---
    promos, ship_states, big = [], [], []
    free_skus = set(kb.get("shipping", {}).get("free_ship_skus", []))
    promo_on = _promo_active(kb)
    prog_key = "returning_customer" if customer_type == "returning" else "new_customer"
    sh = kb.get("shipping", {})
    thr_skus = set(sh.get("threshold_skus", []))
    thr_total = sum(li["subtotal"] for li in lines_items if li["sku"] in thr_skus)
    for li in lines_items:
        g = _gift_for(kb, li["sku"], li["qty"], price_objection=bool(price_objection) and customer_type == "new", program=prog_key)
        if g:
            if g.get("gift"):
                promos.append({"sku": li["sku"], "gift": g["gift"], "tier_qty": g["min_qty"],
                               # v0.5.1 (28/10, chị Nga): khách cũ Nước Hồng sâm hưởng CT tốt nhất — ghi CT để nhân viên lên đơn đúng mã
                               "program": g.get("apply_program") or prog_key, **({"nhanh_code": g["nhanh_code"]} if g.get("nhanh_code") else {})})
            top = max(r["min_qty"] for r in kb["programs"][prog_key]["rules"] if r["if_sku"] == li["sku"])
            # v0.3.0: page Dương Sâm — khách mới từ 10 hộp nhận quà mốc 9 hộp, KHÔNG chuyển nhân viên xin thêm ưu đãi
            if li["qty"] > top and not (IS_DS and li["sku"] == "duongsam-10" and customer_type == "new"):
                big.append(li["sku"])
        # v0.1.16 (chị Nga 14/10): Trà sâm, Tam Sâm Đan, Đông trùng — đơn (các sp này) dưới 1 triệu phí ship cố định, từ 1 triệu miễn phí
        if li["sku"] in thr_skus:
            ship_states.append(True if thr_total >= sh.get("threshold", 1000000) else "thr")
            continue
        # v0.1.14 (chốt 13/10): mọi sản phẩm trừ Hồng sâm dạng nước miễn phí ship từ 1 hộp — VẪN áp quà ở trên
        if li["sku"] in free_skus:
            ship_states.append(True)
        elif g:
            ship_states.append(g.get("freeship"))
        else:
            has_rules = any(r["if_sku"] == li["sku"] for r in kb["programs"]["new_customer"]["rules"])
            ship_states.append(False if (customer_type == "new" and has_rules) else None)
    # phí ship: có ÍT NHẤT một dòng freeship → miễn phí cả đơn; có dòng 'chưa rõ' → nhân viên xác nhận
    fee, zone = _ship_fee(kb, addr)
    if any(s is True for s in ship_states):
        ship_fee, ship_text = 0, "Miễn phí vận chuyển"
    elif ship_states and all(s == "thr" for s in ship_states):
        f = sh.get("threshold_fee", 20000)
        ship_fee, ship_text = f, f"phí vận chuyển {fmt_vnd(f)} (đơn dưới {fmt_vnd(sh.get('threshold', 1000000))})"
    elif any(s is None for s in ship_states) or fee is None:
        ship_fee, ship_text = None, "phí vận chuyển nhân viên xác nhận khi gọi lên đơn"
    else:
        ship_fee, ship_text = fee, f"phí vận chuyển {fmt_vnd(fee)} ({zone})"
    total = goods_total + (ship_fee or 0)

    missing, warnings = [], []
    if not name:
        missing.append("name")
    if not phone:
        missing.append("phone")
    elif not _phone_valid(phone):
        warnings.append("SĐT chưa hợp lệ (cần 10 số, bắt đầu bằng 0) — hỏi lại khách.")
    if not addr:
        missing.append("address")
    elif not _addr_complete(addr):
        warnings.append("Địa chỉ chưa đủ 3 phần (số nhà/đường, phường/xã, tỉnh/thành) — hỏi thêm phần thiếu.")

    # v0.1.14 (chốt 13/10): mẫu xác nhận đơn của chị Nga, tên sản phẩm ngắn gọn
    prod_txt = "; ".join(f"{i['short_name']} x {i['qty']} {i['unit']}" for i in lines_items)
    gift_txt = "; ".join(pr["gift"] for pr in promos) or "Không có"
    lines = ["Dạ em cảm ơn thông tin của anh/chị. Em xin phép xác nhận lại thông tin đơn hàng ạ:", ""]
    lines.append(f"Tên khách hàng: {name or '(chưa có)'}")
    lines.append(f"Số điện thoại: {phone or '(chưa có)'}")
    lines.append(f"Địa chỉ nhận hàng: {addr or '(chưa có)'}")
    if len(lines_items) > 1:
        # v0.5.5 (29/10, chị Nga): khách mua ≥ 2 sản phẩm khác nhau → MỘT đơn, mỗi món 1 dòng (số lượng, thành tiền, quà riêng từng món)
        lines.append("Sản phẩm + Số lượng:")
        for i in lines_items:
            g = "; ".join(pr["gift"] for pr in promos if pr["sku"] == i["sku"])
            lines.append(f"- {i['short_name']} x {i['qty']} {i['unit']}: {i['subtotal_display']}" + (f" (tặng {g})" if g else ""))
    else:
        lines.append(f"Sản phẩm + Số lượng: {prod_txt}")
        lines.append(f"Quà tặng kèm: {gift_txt}")
    lines.append(f"Tổng tiền đơn hàng: {fmt_vnd(total)} ({ship_text})")
    lines.append("")
    lines.append("Anh/chị kiểm tra giúp em thông tin đã đúng chưa ạ?")

    handoff = None
    if handoff_skus:
        handoff = "Đơn có Sâm tươi / Rượu hũ nguyên cây → sau khi khách xác nhận, báo nhân viên gọi lại chốt (cân/đóng gói thực tế) + [HANDOFF: đơn lớn - sâm tươi/rượu hũ | SĐT | 2]."
    elif big:
        handoff = "Số lượng vượt bậc quà cao nhất → áp quà bậc cao nhất, mời khách để nhân viên xin thêm ưu đãi: [HANDOFF: đơn lớn ngoài combo | SĐT | 2]."
    disclaimers = sorted({kb["_meta"]["disclaimer"] for i in lines_items if kb["products"][i["product_id"]].get("disclaimer_required")})
    lat_qty = sum(li["qty"] for li in lines_items if li["sku"] == "hsvn-lat-14")
    upsell = None
    if lat_qty in (1, 2) and customer_type == "new":
        # v0.1.15: giá/quà lấy từ bảng khuyến mại (không ghi cứng) — 1 hộp → mời 2 hộp; 2 hộp → mời 4 hộp
        tq = 2 if lat_qty == 1 else 4
        _, lpkg = find_package(kb, "hsvn-lat-14")
        r = next((x for x in kb["programs"]["new_customer"]["rules"]
                  if x["if_sku"] == "hsvn-lat-14" and x["min_qty"] == tq and not x.get("condition")), None)
        if r and lpkg:
            upsell = (f"Chốt 13/10: đơn {lat_qty} hộp Hồng sâm lát, ĐÃ ĐỦ tên/SĐT/địa chỉ → (chốt 25/10) gửi confirm_text TRƯỚC, KHÔNG mời trong tin đó; khách XÁC NHẬN đúng → lượt sau ghi nhận đơn + [HANDOFF: đơn đã chốt - lên đơn | SĐT | 1] và mời ĐÚNG 1 LẦN lên "
                      f"{r.get('label') or 'combo'} ({tq} hộp {fmt_vnd(lpkg['price_retail'] * tq)} tặng {r['gift']}) — "
                      "scripts_approved.upsell_double ('nếu anh/chị giữ đơn cũ thì em gửi đi luôn ạ'). Khách đồng ý → build_order lại + confirm_text mới + [HANDOFF: khách đổi đơn lên gói lớn | SĐT | 2]; không đồng ý → giữ đơn.")
    ds_qty = sum(li["qty"] for li in lines_items if li["sku"] == "duongsam-10")
    if IS_DS and customer_type == "new" and 1 <= ds_qty <= 8:
        # v0.3.0 (page Dương Sâm, duyệt 21/10): 1–2 hộp → mời 3; 3–5 → mời 6; 6–8 → mời 9 (đúng 1 lần)
        tq = 3 if ds_qty <= 2 else (6 if ds_qty <= 5 else 9)
        _, dpkg = find_package(kb, "duongsam-10")
        r = next((x for x in kb["programs"]["new_customer"]["rules"]
                  if x["if_sku"] == "duongsam-10" and x["min_qty"] == tq and not x.get("condition")), None)
        if r and dpkg and ds_qty != tq:
            upsell = (f"Page Dương Sâm: đơn {ds_qty} hộp, ĐÃ ĐỦ tên/SĐT/địa chỉ → (chốt 25/10) gửi confirm_text TRƯỚC, KHÔNG mời trong tin đó; khách XÁC NHẬN đúng → lượt sau ghi nhận đơn + [HANDOFF: đơn đã chốt - lên đơn | SĐT | 1] và mời ĐÚNG 1 LẦN lên "
                      f"{r.get('label') or 'liệu trình'} ({tq} hộp {fmt_vnd(dpkg['price_retail'] * tq)} tặng {r['gift']}). "
                      "('nếu anh/chị giữ đơn cũ thì em gửi đi luôn ạ'). Khách đồng ý → build_order lại + confirm_text mới + [HANDOFF: khách đổi đơn lên gói lớn | SĐT | 2]; không đồng ý → giữ đơn.")
    nhs_sku = "hsmo-chai" if any(li["sku"] == "hsmo-chai" for li in lines_items) else "hsmo-tui"
    nhs_qty = sum(li["qty"] for li in lines_items if li["sku"] == nhs_sku)
    if IS_NHS and customer_type == "new" and 1 <= nhs_qty <= 5:
        # v0.4.0 (bot Nước Hồng sâm): 1 hộp → mời 2; 2–3 → mời 4; 4–5 → mời 6 (đúng 1 lần, sau khi khách xác nhận đơn)
        tq = 2 if nhs_qty == 1 else (4 if nhs_qty <= 3 else 6)
        _, npkg = find_package(kb, nhs_sku)
        r = next((x for x in kb["programs"]["new_customer"]["rules"]
                  if x["if_sku"] == nhs_sku and x["min_qty"] == tq and not x.get("condition")), None)
        if r and npkg:
            unit = "chai" if nhs_sku == "hsmo-chai" else "hộp"
            upsell = (f"Bot Nước Hồng sâm: đơn {nhs_qty} {unit}, ĐÃ ĐỦ tên/SĐT/địa chỉ → gửi confirm_text TRƯỚC, KHÔNG mời trong tin đó; khách XÁC NHẬN đúng → lượt sau ghi nhận đơn + [HANDOFF: đơn đã chốt - lên đơn | SĐT | 1] và mời ĐÚNG 1 LẦN lên "
                      f"combo {tq} {unit} ({fmt_vnd(npkg['price_retail'] * tq)}, tặng {r['gift']}, miễn phí vận chuyển) — scripts_approved.upsell_nhs "
                      "('nếu anh/chị giữ đơn cũ thì em gửi đi luôn ạ'). Khách đồng ý → build_order lại + confirm_text mới + [HANDOFF: khách đổi đơn lên gói lớn | SĐT | 2]; không đồng ý → giữ đơn.")
    return {
        "items": lines_items, "goods_total": goods_total, "ship_fee": ship_fee,
        "total": total, "total_display": fmt_vnd(total),
        "promo_applied": promos,
        "customer": {"name": name, "phone": phone, "address": addr, "customer_type": customer_type},
        "missing_info": missing, "warnings": warnings,
        "ready_to_confirm": not missing and not warnings,
        "confirm_text": "\n".join(lines),
        "handoff_note": handoff, "disclaimer_to_mention": disclaimers,
        "promo_period": kb["programs"][prog_key].get("period_display"),
        "program": prog_key,
        "promo_expired": (customer_type == "new" and not promo_on) or None,
        "delivery_time": kb.get("shipping", {}).get("delivery_time"),
        "after_confirm": ("Sau khi khách xác nhận: 'Dạ, anh/chị chú ý điện thoại giúp em, trong ngày hôm nay sẽ có chuyên viên "
                          "của Sâm Thái Minh gọi điện lại để xác nhận chính xác trước khi gửi đơn đi ạ.' (khách nói không cần gọi lại → "
                          "'Dạ vâng, em ghi chú đóng gói và gửi hàng đi ngay cho anh/chị ạ.') + lời cảm ơn/chúc sức khỏe "
                          "+ [HANDOFF: đơn đã chốt - lên đơn | SĐT | 1]. SAU ĐÓ KHÔNG chủ động nhắn thêm."),
        "upsell_hint": upsell,
    }
