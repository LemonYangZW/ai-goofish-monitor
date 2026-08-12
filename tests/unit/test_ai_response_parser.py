import pytest

from src.services.ai_response_parser import parse_ai_response_json


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
