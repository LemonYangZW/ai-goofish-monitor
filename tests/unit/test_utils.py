import asyncio

from src.services.result_storage_service import load_all_result_records
from src.utils import (
    format_registration_days,
    get_link_unique_key,
    safe_get,
    save_to_jsonl,
)


def test_safe_get_nested_and_default():
    data = {"a": {"b": [{"c": "value"}]}}
    assert asyncio.run(safe_get(data, "a", "b", 0, "c")) == "value"
    assert asyncio.run(safe_get(data, "a", "b", 1, "c", default="missing")) == "missing"


def test_format_registration_days():
    assert format_registration_days(400).startswith("\u6765\u95f2\u9c7c")
    assert format_registration_days(-1) == "\u672a\u77e5"


def test_get_link_unique_key():
    link = "https://www.goofish.com/item?id=123&foo=bar"
    assert get_link_unique_key(link) == "https://www.goofish.com/item?id=123"


def test_save_to_jsonl(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    record = {
        "爬取时间": "2026-01-01T10:00:00",
        "搜索关键字": "sony a7m4",
        "任务名称": "Sony A7M4",
        "商品信息": {
            "商品ID": "1",
            "商品标题": "Sony A7M4",
            "商品链接": "https://www.goofish.com/item?id=1",
            "当前售价": "¥10000",
        },
    }

    ok = asyncio.run(save_to_jsonl(record, keyword="sony a7m4"))
    assert ok is True

    records = asyncio.run(
        load_all_result_records(
            "sony_a7m4_full_data.jsonl",
            ai_recommended_only=False,
            keyword_recommended_only=False,
            sort_by="crawl_time",
            sort_order="asc",
        )
    )
    assert len(records) == 1
    stored = records[0]
    # 存储层会附加下划线前缀的元数据（商品状态、黑名单命中等），新入库记录应为可见的 active
    assert stored["_status"] == "active"
    assert stored["_effective_hidden"] is False
    # 业务字段需与写入内容完全一致，元数据字段不参与比较，避免存储层扩展字段时误报
    assert {k: v for k, v in stored.items() if not k.startswith("_")} == record
