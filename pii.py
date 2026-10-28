"""Lớp tách PII — che số điện thoại & địa chỉ khách TRƯỚC khi gửi sang model NGOÀI Anthropic
(ChatGPT/DeepSeek), để dữ liệu cá nhân khách không rời hệ thống mình khi thử model bên thứ ba.

Cơ chế: mask text trong transcript thành [SĐT_1], [ĐIACHI_1]... giữ map placeholder->giá trị thật.
Khi model gọi tool build_order với arg chứa placeholder → restore lại giá trị thật (server tự tính,
tự validate). Model chỉ thấy placeholder, không bao giờ thấy SĐT/địa chỉ thật.

Chỉ bật khi provider.external = True. Anthropic (nội bộ) không mask.
"""
import re

# SĐT VN: 09xxxxxxxx, 03/05/07/08x, có thể có +84, dấu cách/gạch
_RE_PHONE = re.compile(r"(?<!\d)(?:\+?84[\s.-]?|0)(?:\d[\s.-]?){8,10}\d(?!\d)")
# Địa chỉ: khó bắt tuyệt đối — bắt cụm có "số nhà", "ngõ", "đường", "phường", "xã", "quận", "huyện"
_RE_ADDR = re.compile(
    r"((?:số\s*nhà|ngõ|ngách|đường|phố|thôn|xóm|ấp|tổ)\s*[^\n,]{1,40}"
    r"(?:,[^\n,]{1,40}){0,4})", re.IGNORECASE)


class PiiMap:
    def __init__(self):
        self.to_real = {}       # placeholder -> real
        self._phone_n = 0
        self._addr_n = 0

    def _new_phone(self, real):
        # nếu đã có placeholder cho số này rồi thì tái sử dụng
        for ph, rv in self.to_real.items():
            if rv == real and ph.startswith("[SĐT_"):
                return ph
        self._phone_n += 1
        ph = f"[SĐT_{self._phone_n}]"
        self.to_real[ph] = real
        return ph

    def _new_addr(self, real):
        for ph, rv in self.to_real.items():
            if rv == real and ph.startswith("[ĐIACHI_"):
                return ph
        self._addr_n += 1
        ph = f"[ĐIACHI_{self._addr_n}]"
        self.to_real[ph] = real
        return ph

    def mask_text(self, text):
        if not text:
            return text
        text = _RE_PHONE.sub(lambda m: self._new_phone(m.group(0).strip()), text)
        text = _RE_ADDR.sub(lambda m: self._new_addr(m.group(1).strip()), text)
        return text

    def restore(self, value):
        """Đổi placeholder ngược lại giá trị thật (dùng khi tool nhận arg từ model)."""
        if not isinstance(value, str):
            return value
        for ph, real in self.to_real.items():
            if ph in value:
                value = value.replace(ph, real)
        return value

    def restore_deep(self, obj):
        if isinstance(obj, str):
            return self.restore(obj)
        if isinstance(obj, list):
            return [self.restore_deep(x) for x in obj]
        if isinstance(obj, dict):
            return {k: self.restore_deep(v) for k, v in obj.items()}
        return obj


def mask_transcript(transcript, pmap):
    """Trả về bản sao transcript đã che PII trong mọi text của user/assistant."""
    out = []
    for t in transcript:
        t2 = dict(t)
        if t.get("text"):
            t2["text"] = pmap.mask_text(t["text"])
        out.append(t2)
    return out
