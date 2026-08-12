import pytest

from src.services.ai_response_parser import (
    extract_ai_response_content,
    parse_ai_response_json,
    EmptyAIResponseError,
)


def test_parse_ai_response_json_uses_first_object_when_multiple_json_objects_are_concatenated():
    content = """```json
{"is_recommended": true, "reason": "first"}
{"is_recommended": false, "reason": "second"}
```"""

    result = parse_ai_response_json(content)

    assert result["is_recommended"] is True
    assert result["reason"] == "first"


def test_parse_ai_response_json_extracts_json_from_wrapped_text():
    content = """分析结果如下：

```json
{"is_recommended": true, "reason": "wrapped"}
```

请按第一份结果处理。"""

    result = parse_ai_response_json(content)

    assert result["is_recommended"] is True
    assert result["reason"] == "wrapped"


def test_parse_ai_response_json_raises_when_no_json_exists():
    with pytest.raises(ValueError):
        parse_ai_response_json("没有任何 JSON 内容")


# -- _normalize_ai_result 归一化行为 --


def test_parse_ai_response_json_fills_missing_prompt_version_and_risk_tags():
    result = parse_ai_response_json('{"is_recommended": true, "reason": "ok"}')

    assert result["prompt_version"] == "EagleEye-V6.4"
    assert result["risk_tags"] == []


def test_parse_ai_response_json_coerces_string_is_recommended():
    """部分模型会把布尔值输出成字符串，需归一化以免触发无效重试。"""
    assert parse_ai_response_json('{"is_recommended": "true"}')["is_recommended"] is True
    assert parse_ai_response_json('{"is_recommended": "False"}')["is_recommended"] is False


def test_parse_ai_response_json_wraps_string_risk_tags_into_list():
    assert parse_ai_response_json('{"risk_tags": "价格异常"}')["risk_tags"] == ["价格异常"]
    assert parse_ai_response_json('{"risk_tags": "  "}')["risk_tags"] == []


def test_parse_ai_response_json_keeps_existing_prompt_version():
    result = parse_ai_response_json('{"prompt_version": "custom-v1"}')

    assert result["prompt_version"] == "custom-v1"


# -- extract_ai_response_content 的 reasoning_content 回退 --


def test_extract_ai_response_content_with_none_content_but_valid_reasoning_content():
    """当 content 为 None 但 reasoning_content 有值时，应该成功提取 reasoning_content 的内容"""
    # 创建 mock 对象模拟 OpenAI 风格的响应
    message = type('Message', (), {
        'content': None,
        'reasoning_content': '这是推理内容'
    })()
    choice = type('Choice', (), {'message': message})()
    response = type('Response', (), {'choices': [choice]})()

    result = extract_ai_response_content(response)

    assert result == '这是推理内容'


def test_extract_ai_response_content_raises_when_content_and_reasoning_content_are_empty():
    """当 content 和 reasoning_content 都为空时，应该抛出 EmptyAIResponseError"""
    # 创建 mock 对象
    message = type('Message', (), {
        'content': None,
        'reasoning_content': None
    })()
    choice = type('Choice', (), {'message': message})()
    response = type('Response', (), {'choices': [choice]})()

    with pytest.raises(EmptyAIResponseError):
        extract_ai_response_content(response)
