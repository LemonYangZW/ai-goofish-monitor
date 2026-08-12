"""AI 流式响应测试桩。

src/services/ai_request_compat.py 的 create_ai_response_async 以 `async for` 消费流式响应，
因此测试中的 client.create 必须返回异步可迭代对象，而非普通响应对象。
"""
from types import SimpleNamespace


class FakeStream:
    """模拟 OpenAI 异步流式响应对象。"""

    def __init__(self, chunks):
        self._chunks = chunks

    async def __aiter__(self):
        for chunk in self._chunks:
            yield chunk


def fake_stream(text, *, split=1):
    """构造流式响应，分片同时兼容 Chat Completions 与 Responses 两种模式。

    split 用于把 text 切成多个分片，验证增量聚合逻辑。
    """
    if not text:
        return FakeStream([])
    size = max(1, -(-len(text) // split))
    pieces = [text[i:i + size] for i in range(0, len(text), size)]
    return FakeStream([
        SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=piece))],
            type="response.output_text.delta",
            delta=piece,
        )
        for piece in pieces
    ])
