"""Anthropic /v1/messages API 兼容层。"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

ANTHROPIC_MESSAGES_API_MODE = "anthropic_messages"
ANTHROPIC_VERSION = "2023-06-01"
_DATA_URL_RE = re.compile(r"^data:(image/[^;]+);base64,(.+)$", re.DOTALL)
_ANTHROPIC_INDICATORS = ("anthropic.com", "anthropic.ai")


def detect_api_format(settings: Any) -> str:
    """根据配置决定使用哪种 API 格式。返回 'openai' 或 'anthropic'。"""
    fmt = getattr(settings, "ai_api_format", "auto") or "auto"
    fmt = fmt.strip().lower()
    if fmt == "anthropic":
        return "anthropic"
    if fmt == "openai":
        return "openai"

    base_url = (getattr(settings, "base_url", "") or "").lower()
    model_name = (getattr(settings, "model_name", "") or "").lower()

    if any(indicator in base_url for indicator in _ANTHROPIC_INDICATORS):
        return "anthropic"
    if model_name.startswith("claude-"):
        return "anthropic"
    return "openai"


def convert_messages_to_anthropic(
    messages: List[Dict[str, Any]],
) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """将 OpenAI 格式消息转换为 Anthropic 格式。

    Returns:
        (system_prompt, anthropic_messages)
    """
    system_parts: List[str] = []
    anthropic_messages: List[Dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content")

        if role == "system":
            if isinstance(content, str):
                system_parts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        system_parts.append(item["text"])
                    elif isinstance(item, str):
                        system_parts.append(item)
            continue

        anthropic_messages.append({
            "role": role,
            "content": _convert_content(content),
        })

    system_prompt = "\n".join(system_parts) if system_parts else None
    return system_prompt, anthropic_messages


def build_anthropic_request_params(
    *,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: Optional[float] = None,
    max_output_tokens: int = 4096,
    enable_json_output: bool = False,
) -> Dict[str, Any]:
    """构建 Anthropic /v1/messages 请求参数。"""
    system_prompt, converted = convert_messages_to_anthropic(messages)

    params: Dict[str, Any] = {
        "model": model,
        "max_tokens": max_output_tokens,
        "messages": converted,
    }

    if system_prompt:
        final_system = system_prompt
    else:
        final_system = None

    if enable_json_output:
        json_instruction = "You must respond with valid JSON only. No markdown fences, no extra text."
        if final_system:
            final_system = f"{final_system}\n\n{json_instruction}"
        else:
            final_system = json_instruction

    if final_system:
        params["system"] = final_system

    if temperature is not None:
        params["temperature"] = temperature

    return params


def _build_url(base_url: str) -> str:
    """构建 Anthropic messages 端点 URL。"""
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/messages"
    return f"{base}/v1/messages"


def _build_headers(api_key: str) -> Dict[str, str]:
    return {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": ANTHROPIC_VERSION,
    }


async def create_anthropic_response_async(
    settings: Any,
    request_params: Dict[str, Any],
) -> str:
    """通过 httpx 异步流式调用 Anthropic API，聚合后返回完整文本。"""
    url = _build_url(settings.base_url)
    proxy = getattr(settings, "proxy_url", None)
    headers = {**_build_headers(settings.api_key or ""), "Accept": "text/event-stream"}
    params = {**request_params, "stream": True}

    parts: List[str] = []
    async with httpx.AsyncClient(proxy=proxy, timeout=120.0) as client:
        async with client.stream("POST", url, json=params, headers=headers) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if not data_str or data_str == "[DONE]":
                    continue
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                if data.get("type") == "content_block_delta":
                    delta = data.get("delta", {})
                    if delta.get("type") == "text_delta":
                        parts.append(delta.get("text", ""))
    return "".join(parts)


def create_anthropic_response_sync(
    settings: Any,
    request_params: Dict[str, Any],
) -> Dict[str, Any]:
    """通过 httpx 同步调用 Anthropic API。"""
    url = _build_url(settings.base_url)
    headers = _build_headers(settings.api_key or "")
    proxy = getattr(settings, "proxy_url", None)

    with httpx.Client(proxy=proxy, timeout=30.0) as client:
        resp = client.post(url, json=request_params, headers=headers)
        resp.raise_for_status()
        return resp.json()


def _convert_content(content: Any) -> List[Dict[str, Any]]:
    """将 OpenAI 消息 content 转换为 Anthropic content blocks。"""
    if isinstance(content, str):
        return [{"type": "text", "text": content}]

    if not isinstance(content, list):
        return [{"type": "text", "text": str(content)}]

    blocks: List[Dict[str, Any]] = []
    for item in content:
        if isinstance(item, str):
            blocks.append({"type": "text", "text": item})
            continue
        if not isinstance(item, dict):
            continue

        item_type = item.get("type", "")
        if item_type == "text":
            blocks.append({"type": "text", "text": item.get("text", "")})
        elif item_type == "image_url":
            block = _convert_image_url_item(item)
            if block:
                blocks.append(block)

    return blocks


def _convert_image_url_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """将 OpenAI image_url 格式转换为 Anthropic image 格式。"""
    image_url_obj = item.get("image_url")
    if isinstance(image_url_obj, dict):
        url = image_url_obj.get("url", "")
    elif isinstance(image_url_obj, str):
        url = image_url_obj
    else:
        return None

    match = _DATA_URL_RE.match(url)
    if not match:
        return {"type": "text", "text": f"[image: {url[:100]}]"}

    media_type = match.group(1)
    data = match.group(2)
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": data,
        },
    }
