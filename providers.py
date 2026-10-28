"""Lớp đa nhà cung cấp model — cho phép bản TEST NỘI BỘ cắm thêm ChatGPT / DeepSeek
(chuẩn OpenAI-compatible) bên cạnh Anthropic, dùng CHUNG một bộ tool.

Điểm khó: Anthropic và OpenAI khác nhau về định dạng tool-use. File này định nghĩa
một "transcript chuẩn hoá" và để mỗi provider tự dịch sang định dạng riêng.

Transcript chuẩn hoá (list các turn):
  {"role": "user", "text": "..."}
  {"role": "assistant", "text": "...", "tool_calls": [{"id","name","input"}]}
  {"role": "tool", "tool_call_id": "...", "name": "...", "output": {...}}

provider.call(system_text, transcript, tools) -> chuẩn hoá:
  {"text": str, "tool_calls": [{"id","name","input"}], "stop_reason": str, "usage": {...}}
hoặc {"error": "..."}

v0.1.15 (13/10/2026): PROMPT CACHING dùng chung giữa các khách. engine.py chèn CACHE_SPLIT giữa phần hướng dẫn
CỐ ĐỊNH (persona/playbook/faq/luật — giống nhau mọi hội thoại) và phần RIÊNG từng hội thoại (sản phẩm trọng tâm,
hồ sơ khách). Anthropic: phần cố định là 1 block có cache_control (dùng lại cho MỌI khách), phần riêng là block sau
không cache. Trước đây cả hai nằm chung 1 block nên cache chỉ trúng trong cùng một hội thoại.
Thêm 1 điểm cache ở tin cuối để các vòng gọi tool trong cùng 1 lượt không tính lại toàn bộ lịch sử.
"""
import base64
import json
import os
import urllib.error
import urllib.request

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
# Dấu tách phần cố định / phần riêng của system prompt (engine.py dùng đúng chuỗi này).
CACHE_SPLIT = "\n\n=== THÔNG TIN RIÊNG CỦA HỘI THOẠI NÀY ==="


def _http_json(url, headers, payload, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        try:
            body = json.loads(ex.read().decode("utf-8"))
            msg = body.get("error", {})
            msg = msg.get("message", str(msg)) if isinstance(msg, dict) else str(msg)
        except Exception:  # noqa: BLE001
            msg = f"HTTP {ex.code}"
        return {"_error": f"{ex.code}: {msg}"}
    except Exception as ex:  # noqa: BLE001
        return {"_error": f"network: {ex}"}



# ------------------------------------------------------------------ Ảnh cho model
# v0.5.42 (03/09): sự cố 01/09 — sticker khách nằm ở fbcdn.net, trước đây bot đưa Anthropic
# ĐƯỜNG LINK ảnh để Anthropic tự tải; Anthropic tôn trọng robots.txt của fbcdn (chặn bot)
# nên trả 400, CẢ LƯỢT trả lời hỏng → bot IM. Cách chắc chắn: SERVER TỰ TẢI ảnh về rồi gửi
# base64 (không nhờ Anthropic tải hộ). Tải lỗi/quá to → trả None, bỏ qua ảnh đó (đường lùi).
_MAX_IMG_BYTES = int(os.environ.get("VISION_MAX_IMG_BYTES", str(3 * 1024 * 1024)))
_IMG_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
_EXT_CTYPE = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
              "gif": "image/gif", "webp": "image/webp"}


def _fetch_image_block(url, timeout=8):
    """Tải 1 ảnh về server, trả block Anthropic dạng base64; None nếu tải lỗi/không phải ảnh/quá to."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": _IMG_UA, "Accept": "image/avif,image/webp,image/*,*/*"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            raw = resp.read(_MAX_IMG_BYTES + 1)
    except Exception:  # noqa: BLE001
        return None
    if not raw or len(raw) > _MAX_IMG_BYTES:
        return None
    if ctype not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
        low = url.lower().split("?")[0]
        ctype = next((v for k, v in _EXT_CTYPE.items() if low.endswith("." + k)), "")
        if not ctype:
            return None
    return {"type": "image", "source": {"type": "base64", "media_type": ctype,
                                        "data": base64.b64encode(raw).decode("ascii")}}


def _system_blocks(system_text):
    """v0.1.15: tách system prompt tại CACHE_SPLIT → [phần cố định (cache), phần riêng hội thoại (không cache)]."""
    static, sep, dynamic = (system_text or "").partition(CACHE_SPLIT)
    blocks = [{"type": "text", "text": static, "cache_control": {"type": "ephemeral"}}]
    if sep and dynamic.strip():
        blocks.append({"type": "text", "text": (sep + dynamic).strip()})
    return blocks


# ------------------------------------------------------------------ Anthropic
class AnthropicProvider:
    external = False        # Anthropic = nội bộ, không cần tách PII

    def __init__(self, model, api_key=None, max_tokens=2048):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.max_tokens = max_tokens

    def ready(self):
        return bool(self.api_key)

    def _tools(self, tools):
        # tools đầu vào ở dạng Anthropic gốc (name, description, input_schema)
        out = [dict(t) for t in tools]
        if out:
            out[-1] = {**out[-1], "cache_control": {"type": "ephemeral"}}
        return out

    def _messages(self, transcript):
        msgs = []
        for t in transcript:
            if t["role"] == "user":
                imgs = [str(u) for u in (t.get("images") or []) if str(u).startswith("http")][:3]
                blocks = []
                for u in imgs:
                    # v0.5.42: SERVER tự tải rồi gửi base64 (không để Anthropic tải fbcdn — bị
                    # robots.txt chặn → 400 → bot im, sự cố 01/09). Tải lỗi 1 ảnh: bỏ qua ảnh đó.
                    b = _fetch_image_block(u)
                    if b:
                        blocks.append(b)
                if blocks:
                    blocks.append({"type": "text",
                                   "text": (t.get("text") or "").strip() or "(khách gửi hình đính kèm)"})
                    msgs.append({"role": "user", "content": blocks})
                elif (t.get("text") or "").strip():
                    # không tải được ảnh nào → vẫn gửi phần chữ (marker sticker/ảnh) để bot còn trả lời
                    msgs.append({"role": "user", "content": t["text"]})
            elif t["role"] == "assistant":
                content = []
                if t.get("text"):
                    content.append({"type": "text", "text": t["text"]})
                for tc in t.get("tool_calls", []):
                    content.append({"type": "tool_use", "id": tc["id"],
                                    "name": tc["name"], "input": tc["input"]})
                msgs.append({"role": "assistant", "content": content or [{"type": "text", "text": "..."}]})
            elif t["role"] == "tool":
                msgs.append({"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": t["tool_call_id"],
                    "content": json.dumps(t["output"], ensure_ascii=False)}]})
        # v0.1.15: điểm cache ở tin cuối — vòng tool kế tiếp trong cùng lượt đọc lại lịch sử từ cache
        if msgs:
            last = msgs[-1]
            c = last["content"]
            if isinstance(c, str):
                last["content"] = [{"type": "text", "text": c, "cache_control": {"type": "ephemeral"}}]
            elif isinstance(c, list) and c:
                c[-1] = {**c[-1], "cache_control": {"type": "ephemeral"}}
        return msgs

    def call(self, system_text, transcript, tools, no_tools=False):
        payload = {
            "model": self.model, "max_tokens": self.max_tokens,
            "system": _system_blocks(system_text),
            "messages": self._messages(transcript),
            "tools": self._tools(tools),
        }
        if no_tools:
            payload["tool_choice"] = {"type": "none"}
        data = _http_json(ANTHROPIC_URL,
                          {"content-type": "application/json", "x-api-key": self.api_key,
                           "anthropic-version": "2023-06-01"}, payload)
        if data.get("_error"):
            return {"error": data["_error"]}
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        tool_calls = [{"id": b["id"], "name": b["name"], "input": b.get("input", {})}
                      for b in data.get("content", []) if b.get("type") == "tool_use"]
        return {"text": text, "tool_calls": tool_calls,
                "stop_reason": data.get("stop_reason"), "usage": data.get("usage", {})}


# -------------------------------------------------- OpenAI-compatible (GPT/DeepSeek)
class OpenAICompatProvider:
    """Dùng cho ChatGPT (api.openai.com) và DeepSeek (api.deepseek.com) — cùng chuẩn
    OpenAI chat/completions + function calling. external=True → BẬT tách PII.
    (Các hãng này tự cache theo đoạn đầu giống nhau — phần cố định đứng trước nên cũng được lợi.)"""
    external = True

    def __init__(self, model, api_key, base_url, max_tokens=2048, label=""):
        self.model = model
        self.api_key = api_key
        self.base_url = (base_url or "").rstrip("/")
        self.max_tokens = max_tokens
        self.label = label or model

    def ready(self):
        return bool(self.api_key and self.base_url and self.model)

    def _tools(self, tools):
        # Anthropic {name, description, input_schema} -> OpenAI {type:function, function:{...}}
        return [{"type": "function", "function": {
            "name": t["name"], "description": t.get("description", ""),
            "parameters": t["input_schema"]}} for t in tools]

    def _messages(self, system_text, transcript):
        msgs = [{"role": "system", "content": system_text}]
        for t in transcript:
            if t["role"] == "user":
                if (t.get("text") or "").strip():
                    msgs.append({"role": "user", "content": t["text"]})
            elif t["role"] == "assistant":
                m = {"role": "assistant", "content": t.get("text") or None}
                if t.get("tool_calls"):
                    m["tool_calls"] = [{"id": tc["id"], "type": "function",
                                        "function": {"name": tc["name"],
                                                     "arguments": json.dumps(tc["input"], ensure_ascii=False)}}
                                       for tc in t["tool_calls"]]
                msgs.append(m)
            elif t["role"] == "tool":
                msgs.append({"role": "tool", "tool_call_id": t["tool_call_id"],
                             "content": json.dumps(t["output"], ensure_ascii=False)})
        return msgs

    def call(self, system_text, transcript, tools, no_tools=False):
        payload = {
            "model": self.model, "max_tokens": self.max_tokens,
            "messages": self._messages(system_text, transcript),
        }
        if not no_tools:
            payload["tools"] = self._tools(tools)
            payload["tool_choice"] = "auto"
        data = _http_json(f"{self.base_url}/chat/completions",
                          {"content-type": "application/json",
                           "authorization": f"Bearer {self.api_key}"}, payload)
        if data.get("_error"):
            return {"error": data["_error"]}
        try:
            choice = data["choices"][0]["message"]
        except Exception:  # noqa: BLE001
            return {"error": "openai: no choices"}
        text = choice.get("content") or ""
        tool_calls = []
        for tc in choice.get("tool_calls", []) or []:
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except Exception:  # noqa: BLE001
                args = {}
            tool_calls.append({"id": tc.get("id", ""), "name": fn.get("name", ""), "input": args})
        return {"text": text, "tool_calls": tool_calls,
                "stop_reason": data["choices"][0].get("finish_reason"),
                "usage": data.get("usage", {})}


# ------------------------------------------------------------ Google Gemini
class GeminiProvider(OpenAICompatProvider):
    """v0.1.10 (24/09/2026): Google Gemini qua cổng tương thích OpenAI của Google
    (https://generativelanguage.googleapis.com/v1beta/openai/). external=True → BẬT tách PII.

    Khác OpenAICompatProvider ở 3 điểm:
    1. THOUGHT SIGNATURE (Gemini 3): mỗi tool_call trả về có thể kèm `extra_content`
       (chữ ký suy nghĩ). Vòng tool sau PHẢI gửi trả nguyên văn, thiếu là Google trả 400.
       → lưu vào tc["extra"] (và extra_content cấp message vào t["msg_extra"]) rồi gửi lại y hệt.
    2. Ảnh khách gửi: server tự tải rồi gửi base64 dạng data URL (giống Anthropic, không để Google tự tải fbcdn).
    3. reasoning_effort (GEMINI_REASONING, mặc định low) để tiết kiệm token suy nghĩ; max_tokens riêng
       (GEMINI_MAX_TOKENS, mặc định 4096) vì token suy nghĩ tính chung vào giới hạn đầu ra.
    """
    external = True

    def __init__(self, model, api_key, base_url=None, max_tokens=4096, label="Gemini", reasoning="low"):
        super().__init__(model, api_key,
                         base_url or "https://generativelanguage.googleapis.com/v1beta/openai",
                         max_tokens, label=label)
        self.reasoning = (reasoning or "").strip().lower()

    def _messages(self, system_text, transcript):
        msgs = [{"role": "system", "content": system_text}]
        for t in transcript:
            if t["role"] == "user":
                text = (t.get("text") or "").strip()
                imgs = [str(u) for u in (t.get("images") or []) if str(u).startswith("http")][:3]
                parts = []
                for u in imgs:
                    b = _fetch_image_block(u)
                    if b:
                        src = b["source"]
                        parts.append({"type": "image_url", "image_url": {
                            "url": f"data:{src['media_type']};base64,{src['data']}"}})
                if parts:
                    parts.append({"type": "text", "text": text or "(khách gửi hình đính kèm)"})
                    msgs.append({"role": "user", "content": parts})
                elif text:
                    msgs.append({"role": "user", "content": text})
            elif t["role"] == "assistant":
                m = {"role": "assistant", "content": t.get("text") or None}
                if t.get("tool_calls"):
                    calls = []
                    for tc in t["tool_calls"]:
                        c = {"id": tc["id"], "type": "function",
                             "function": {"name": tc["name"],
                                          "arguments": json.dumps(tc["input"], ensure_ascii=False)}}
                        if tc.get("extra"):
                            c["extra_content"] = tc["extra"]      # chữ ký suy nghĩ — trả lại nguyên văn
                        calls.append(c)
                    m["tool_calls"] = calls
                if t.get("msg_extra"):
                    m["extra_content"] = t["msg_extra"]
                if m["content"] is None and not m.get("tool_calls"):
                    m["content"] = "..."
                msgs.append(m)
            elif t["role"] == "tool":
                msgs.append({"role": "tool", "tool_call_id": t["tool_call_id"],
                             "content": json.dumps(t["output"], ensure_ascii=False)})
        return msgs

    def call(self, system_text, transcript, tools, no_tools=False):
        payload = {
            "model": self.model, "max_tokens": self.max_tokens,
            "messages": self._messages(system_text, transcript),
        }
        if self.reasoning in ("low", "medium", "high", "minimal", "none"):
            payload["reasoning_effort"] = self.reasoning
        if not no_tools:
            payload["tools"] = self._tools(tools)
            payload["tool_choice"] = "auto"
        data = _http_json(f"{self.base_url}/chat/completions",
                          {"content-type": "application/json",
                           "authorization": f"Bearer {self.api_key}"}, payload)
        if isinstance(data, list):          # Google đôi khi bọc lỗi trong mảng
            data = data[0] if data else {}
        if data.get("_error"):
            return {"error": "gemini " + data["_error"]}
        try:
            choice = data["choices"][0]["message"]
        except Exception:  # noqa: BLE001
            return {"error": "gemini: no choices"}
        text = choice.get("content") or ""
        if isinstance(text, list):          # phòng khi trả dạng mảng part
            text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
        tool_calls = []
        for i, tc in enumerate(choice.get("tool_calls", []) or []):
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except Exception:  # noqa: BLE001
                args = {}
            item = {"id": tc.get("id") or f"call_{i}", "name": fn.get("name", ""), "input": args}
            if tc.get("extra_content"):
                item["extra"] = tc["extra_content"]
            tool_calls.append(item)
        out = {"text": text, "tool_calls": tool_calls,
               "stop_reason": data["choices"][0].get("finish_reason"),
               "usage": data.get("usage", {})}
        if choice.get("extra_content"):
            out["msg_extra"] = choice["extra_content"]
        return out


# ------------------------------------------------------------------ registry
def build_registry(max_tokens=2048):
    """Trả về dict model_key -> provider instance. Chỉ gồm provider có đủ cấu hình (ready)."""
    reg = {}
    ak = os.environ.get("ANTHROPIC_API_KEY", "")
    reg["sonnet"] = AnthropicProvider(os.environ.get("MODEL_SONNET", "claude-sonnet-4-5"), ak, max_tokens)
    reg["haiku"] = AnthropicProvider(os.environ.get("MODEL_HAIKU", "claude-haiku-4-5"), ak, max_tokens)
    # ChatGPT
    reg["gpt"] = OpenAICompatProvider(
        os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        os.environ.get("OPENAI_API_KEY", ""),
        os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        max_tokens, label="ChatGPT")
    # DeepSeek
    reg["deepseek"] = OpenAICompatProvider(
        os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        os.environ.get("DEEPSEEK_API_KEY", ""),
        os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        max_tokens, label="DeepSeek")
    # Google Gemini (v0.1.10) — cần GEMINI_API_KEY (AI Studio, BẬT thanh toán: bản miễn phí Google được dùng dữ liệu)
    gk = os.environ.get("GEMINI_API_KEY", "")
    gbase = os.environ.get("GEMINI_BASE_URL", "")
    gmax = int(os.environ.get("GEMINI_MAX_TOKENS", "4096"))
    greason = os.environ.get("GEMINI_REASONING", "low")
    reg["gemini"] = GeminiProvider(os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"), gk, gbase,
                                   gmax, label="Gemini Flash", reasoning=greason)
    reg["gemini_lite"] = GeminiProvider(os.environ.get("GEMINI_MODEL_LITE", "gemini-3.5-flash-lite"), gk, gbase,
                                        gmax, label="Gemini Flash-Lite", reasoning=greason)
    return reg


def available(reg):
    """Danh sách model_key đã cấu hình đủ (để UI hiện đúng lựa chọn)."""
    return {k: getattr(p, "label", k) for k, p in reg.items() if p.ready()}
