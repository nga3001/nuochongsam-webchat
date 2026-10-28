"""Đẩy đơn chốt trong chat lên phần mềm Nhanh (nhanh.vn) — Sâm v0.1.15 (chị Nga yêu cầu 13/10/2026).

Luồng: bot gọi build_order → đơn đủ thông tin (ready_to_confirm) được NHỚ theo hội thoại → khách xác nhận,
bot chèn [HANDOFF: đơn đã chốt - lên đơn | SĐT | 1] → pancake_adapter gọi push_order() → tạo đơn trên Nhanh
qua Open API v3 (POST https://pos.open.nhanh.vn/v3.0/order/add). Chuyên viên vẫn gọi xác nhận như cũ;
đơn lên Nhanh ở trạng thái mặc định (Mới) để chuyên viên kiểm tra, chọn kho/vận chuyển rồi duyệt.

Chống trùng: Nhanh chặn trùng theo appId + channel.appOrderId; appOrderId = stm-<hội thoại>-<mã nội dung đơn>.
Chỉ chạy ở kênh Facebook (pancake_adapter), web test KHÔNG đẩy đơn.

ENV (Railway Variables):
  NHANH_ENABLED        "1" để bật đẩy đơn (mặc định TẮT). Trang admin đè được bằng setting "nhanh_enabled".
  NHANH_APP_ID         appId của app tạo ở open.nhanh.vn
  NHANH_BUSINESS_ID    businessId của shop (trả về khi lấy accessToken)
  NHANH_ACCESS_TOKEN   accessToken v3 (hạn 1 năm). HOẶC dùng cách lấy tự động bên dưới.
  NHANH_SECRET_KEY     secretKey của app — chỉ cần khi dùng NHANH_ACCESS_CODE
  NHANH_ACCESS_CODE    accessCode lấy từ thanh địa chỉ sau khi đăng nhập https://nhanh.vn/oauth?appId=...&returnLink=...
                       (hạn 10 phút). Bot đổi sang accessToken lúc khởi động, lưu vào DB (setting nhanh_token).
  NHANH_PRODUCT_MAP    mã SKU của bot = ID sản phẩm trên Nhanh, cách nhau dấu phẩy/chấm phẩy/xuống dòng.
                       Vd: hsvn-lat-14=12345678; hsmo-chai=12345679; tra1700-20=12345680; tra1700-10=12345681
                       (khai cả SKU Trà sâm để quà tặng lên đơn thành sản phẩm 0đ; thiếu thì quà ghi ở ghi chú đơn)
  NHANH_DEPOT_ID       (tuỳ chọn) ID kho — đơn có kho sẽ tính tạm giữ tồn
  NHANH_SALE_ID        (tuỳ chọn) ID nhân viên bán gắn cho đơn
  NHANH_SOURCE_NAME    (tuỳ chọn) tên nguồn đơn, mặc định "Chatbot Facebook Sâm Thái Minh"
  NHANH_ALLOW_TEST     "1" = hội thoại thử (#tm) cũng đẩy đơn, ghi chú "ĐƠN TEST - KHÔNG GIAO" (mặc định không đẩy)
"""
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request

import db

BASE = os.environ.get("NHANH_BASE", "https://pos.open.nhanh.vn/v3.0")
APP_ID = os.environ.get("NHANH_APP_ID", "").strip()
BUSINESS_ID = os.environ.get("NHANH_BUSINESS_ID", "").strip()
SOURCE_NAME = os.environ.get("NHANH_SOURCE_NAME", "Chatbot Facebook Sâm Thái Minh")


def _int_env(k):
    try:
        return int(os.environ.get(k, "").strip())
    except Exception:  # noqa: BLE001
        return None


DEPOT_ID = _int_env("NHANH_DEPOT_ID")
SALE_ID = _int_env("NHANH_SALE_ID")


def enabled() -> bool:
    v = db.get_setting("nhanh_enabled")
    if v is not None:
        return v == "1"
    return os.environ.get("NHANH_ENABLED", "0") == "1"


def allow_test() -> bool:
    return os.environ.get("NHANH_ALLOW_TEST", "0") == "1"


def _token() -> str:
    return (db.get_setting("nhanh_token") or os.environ.get("NHANH_ACCESS_TOKEN", "")).strip()


def _business_id() -> str:
    return (db.get_setting("nhanh_business_id") or BUSINESS_ID).strip()


def product_map() -> dict:
    raw = db.get_setting("nhanh_product_map")
    if raw is None:
        raw = os.environ.get("NHANH_PRODUCT_MAP", "")
    out = {}
    for part in re.split(r"[,;\n]", raw or ""):
        if "=" in part:
            k, v = part.split("=", 1)
            k, v = k.strip().lower(), v.strip()
            if k and v.isdigit():
                out[k] = int(v)
    return out


def _post(path: str, body: dict, auth: bool = True, query: dict = None) -> dict:
    q = {"appId": APP_ID}
    if auth:
        q["businessId"] = _business_id()
    q.update(query or {})
    url = f"{BASE}{path}?" + "&".join(f"{k}={v}" for k, v in q.items())
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = _token()
    req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as ex:
        try:
            return json.loads(ex.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            return {"code": 0, "errorCode": f"HTTP_{ex.code}", "messages": str(ex)}
    except Exception as ex:  # noqa: BLE001
        return {"code": 0, "errorCode": "NETWORK", "messages": str(ex)}


# ------------------------------------------------------------- lấy / kiểm tra accessToken
def init_token() -> dict:
    """Gọi 1 lần lúc khởi động. Có NHANH_ACCESS_CODE (+ NHANH_SECRET_KEY) mà mã đó chưa dùng → đổi lấy accessToken,
    lưu DB (sống qua redeploy). Cảnh báo trong log khi token còn dưới 30 ngày."""
    code = os.environ.get("NHANH_ACCESS_CODE", "").strip()
    secret = os.environ.get("NHANH_SECRET_KEY", "").strip()
    if code and secret and APP_ID and db.get_setting("nhanh_code_used") != code:
        r = _post("/app/getaccesstoken", {"accessCode": code, "secretKey": secret}, auth=False)
        db.set_setting("nhanh_code_used", code)
        if r.get("code") == 1 and (r.get("data") or {}).get("accessToken"):
            d = r["data"]
            db.set_setting("nhanh_token", d["accessToken"])
            if d.get("businessId"):
                db.set_setting("nhanh_business_id", str(d["businessId"]))
            if d.get("expiredAt"):
                db.set_setting("nhanh_token_exp", str(d["expiredAt"]))
            db.log_webhook("nhanh_token", f"đã lấy accessToken Nhanh — businessId={d.get('businessId')}, "
                                          f"kho={d.get('depotIds')}, hết hạn={d.get('expiredAt')}")
        else:
            db.log_webhook("nhanh_fail", f"đổi accessCode lỗi (mã chỉ sống 10 phút, dùng 1 lần): "
                                         f"{json.dumps(r, ensure_ascii=False)[:300]}")
    try:
        exp = float(db.get_setting("nhanh_token_exp") or 0)
        if exp and exp - time.time() < 30 * 86400:
            db.log_webhook("nhanh_warn", f"accessToken Nhanh sắp hết hạn ({time.strftime('%d/%m/%Y', time.localtime(exp))}) "
                                         f"— cần đăng nhập cấp quyền lại để lấy token mới")
    except Exception:  # noqa: BLE001
        pass
    return {"enabled": enabled(), "has_token": bool(_token()), "business_id": _business_id(),
            "mapped_skus": sorted(product_map())}


# ------------------------------------------------------------- nhớ đơn & đẩy đơn
def remember_order(conv_id: str, order: dict):
    """Lưu kết quả build_order mới nhất đã đủ thông tin (gọi từ pancake_adapter sau mỗi lượt bot)."""
    if order and order.get("ready_to_confirm") and order.get("items"):
        keep = {k: order.get(k) for k in ("items", "promo_applied", "customer", "ship_fee", "total", "goods_total")}
        db.set_setting("nhanh_last_order:" + conv_id, json.dumps(keep, ensure_ascii=False))


# Quà tặng (chữ trong bảng khuyến mại) → SKU của bot → ID Nhanh qua NHANH_PRODUCT_MAP
_GIFT_SKU = [
    (r"trà sâm 1700.*20 gói|trà sâm 20 gói", "tra1700-20"),
    (r"trà sâm 1700.*10 gói|trà sâm 10 gói", "tra1700-10"),
    (r"trà sâm lai châu nguyên lá", "tra-nguyenla-100"),
    (r"nước hồng sâm mật ong|chai nước hồng sâm", "hsmo-chai"),
    (r"hồng sâm mật ong dạng túi", "hsmo-tui"),
    (r"long sâm linh đan \(6 viên\)", "longsam-6"),
    (r"tam sâm đan", "tamsamdan-30"),
    (r"đông trùng hạ thảo", "dongtrung-30"),
    (r"hồng sâm việt nam thái minh", "hsvn-lat-14"),
]


def _gift_items(gift_text: str, pmap: dict):
    """'1 hộp Hồng sâm ... + 1 hộp Trà sâm 1700 (20 gói)' → ([{id, quantity, price:0}], [phần không map được])."""
    found, rest = [], []
    for part in re.split(r"\s\+\s", gift_text or ""):
        p = part.strip()
        if not p:
            continue
        m = re.match(r"^(\d+)\s*(hộp|chai|lọ|túi)?\s*(.*)$", p, re.I)
        qty = int(m.group(1)) if m else 1
        low = p.lower()
        sku = next((s for pat, s in _GIFT_SKU if re.search(pat, low)), None)
        if sku and pmap.get(sku):
            found.append({"id": pmap[sku], "quantity": qty, "price": 0})
        else:
            rest.append(p)
    return found, rest


def build_payload(conv_id: str, order: dict, note: str = "", test: bool = False) -> dict:
    pmap = product_map()
    cust = order.get("customer") or {}
    products, missing, gift_notes = [], [], []
    gifts_by_sku = {}
    for pr in order.get("promo_applied") or []:
        gifts_by_sku.setdefault(pr["sku"], []).append(pr.get("gift") or "")
    for it in order.get("items") or []:
        pid = pmap.get(it["sku"])
        if not pid:
            missing.append(it["sku"])
            continue
        row = {"id": pid, "price": int(it["subtotal"] / max(1, it["qty"])), "quantity": it["qty"]}
        gl = []
        for g in gifts_by_sku.get(it["sku"], []):
            items, rest = _gift_items(g, pmap)
            gl += items
            gift_notes += rest
        if gl:
            row["gifts"] = gl
        products.append(row)
    sig = hashlib.md5(json.dumps([order.get("items"), cust.get("phone")], sort_keys=True,
                                 ensure_ascii=False).encode()).hexdigest()[:8]
    desc = []
    if test:
        desc.append("ĐƠN TEST - KHÔNG GIAO")
    desc.append("Đơn chatbot Facebook — chuyên viên gọi xác nhận trước khi gửi")
    all_gifts = [pr.get("gift") for pr in order.get("promo_applied") or [] if pr.get("gift")]
    if all_gifts:
        desc.append("Quà: " + "; ".join(all_gifts))
    if gift_notes:
        desc.append("Quà chưa gắn mã Nhanh (nhập tay): " + "; ".join(gift_notes))
    if note:
        desc.append("Ghi chú bot: " + note)
    if order.get("total") is not None:
        desc.append(f"Tổng bot báo khách: {order['total']:,}đ".replace(",", "."))
    info = {"description": " | ".join(desc)[:1000],
            "privateDescription": f"Hội thoại Pancake: {conv_id}"}
    if DEPOT_ID:
        info["depotId"] = DEPOT_ID
    if SALE_ID:
        info["saleId"] = SALE_ID
    payload = {
        "info": info,
        "channel": {"appOrderId": f"stm-{conv_id}-{sig}"[:64], "sourceName": SOURCE_NAME},
        "shippingAddress": {"name": cust.get("name") or "Khách Facebook",
                            "mobile": re.sub(r"\D", "", cust.get("phone") or ""),
                            "address": cust.get("address") or ""},
        "products": products,
    }
    if order.get("ship_fee") is not None:
        payload["carrier"] = {"customerShipFee": int(order["ship_fee"])}
    return {"payload": payload, "missing_skus": missing}


def push_order(conv_id: str, note: str = "", test: bool = False) -> dict:
    """Tạo đơn trên Nhanh từ đơn đã nhớ của hội thoại. Trả {ok, nhanh_id} hoặc {ok: False, reason}."""
    if not enabled():
        return {"ok": False, "reason": "Nhanh đang tắt (NHANH_ENABLED)"}
    if test and not allow_test():
        return {"ok": False, "reason": "hội thoại thử (#tm) — không đẩy đơn (NHANH_ALLOW_TEST=0)"}
    if not (APP_ID and _business_id() and _token()):
        return {"ok": False, "reason": "thiếu NHANH_APP_ID / businessId / accessToken"}
    done = db.get_setting("nhanh_done:" + conv_id)
    raw = db.get_setting("nhanh_last_order:" + conv_id)
    if not raw:
        return {"ok": False, "reason": "chưa có đơn đủ thông tin trong hội thoại"}
    order = json.loads(raw)
    b = build_payload(conv_id, order, note, test)
    if b["missing_skus"]:
        reason = "sản phẩm chưa khai ID Nhanh: " + ", ".join(b["missing_skus"])
        db.log_webhook("nhanh_fail", f"{conv_id}: {reason}")
        return {"ok": False, "reason": reason}
    app_oid = b["payload"]["channel"]["appOrderId"]
    if done and json.loads(done).get("appOrderId") == app_oid:
        return {"ok": True, "nhanh_id": json.loads(done).get("id"), "dup": True}
    r = _post("/order/add", b["payload"])
    if r.get("code") == 1:
        nid = (r.get("data") or {}).get("id")
        db.set_setting("nhanh_done:" + conv_id, json.dumps({"id": nid, "appOrderId": app_oid, "ts": time.time()}))
        db.log_webhook("nhanh_order", f"{conv_id}: đã tạo đơn Nhanh #{nid} ({app_oid})")
        return {"ok": True, "nhanh_id": nid}
    reason = f"{r.get('errorCode')}: {r.get('messages')}"
    db.log_webhook("nhanh_fail", f"{conv_id}: tạo đơn lỗi — {reason}"[:400])
    return {"ok": False, "reason": reason}
