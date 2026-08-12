from src.scraper import _build_extra_headers


# 浏览器扩展导出的真实快照 headers（采集自页面中的某个 XHR 请求）
SNAPSHOT_HEADERS = {
    "sec-ch-ua-platform": '"Windows"',
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/151.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="151", "Chromium";v="151"',
    "sec-ch-ua-mobile": "?0",
    "Accept": "*/*",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://www.goofish.com/",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def test_build_extra_headers_keeps_fingerprint_headers():
    headers = _build_extra_headers(SNAPSHOT_HEADERS)

    assert headers == {
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua": '"Google Chrome";v="151", "Chromium";v="151"',
        "sec-ch-ua-mobile": "?0",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }


def test_build_extra_headers_drops_sec_fetch_headers():
    """Sec-Fetch-* 由 Chromium 按请求类型自行计算，覆盖会导致 net::ERR_INVALID_ARGUMENT。"""
    headers = _build_extra_headers(SNAPSHOT_HEADERS)

    assert not any(key.lower().startswith("sec-fetch-") for key in headers)


def test_build_extra_headers_drops_request_scoped_headers():
    """Accept/Referer/Accept-Encoding 只对采集时的那个 XHR 成立，不能套用到导航与脚本请求。"""
    headers = _build_extra_headers(SNAPSHOT_HEADERS)

    for key in ("Accept", "Accept-Encoding", "Referer", "User-Agent"):
        assert key not in headers


def test_build_extra_headers_is_case_insensitive():
    headers = _build_extra_headers(
        {"SEC-FETCH-MODE": "cors", "COOKIE": "a=1", "Origin": "https://www.goofish.com"}
    )

    assert headers == {}


def test_build_extra_headers_skips_empty_and_none():
    assert _build_extra_headers(None) == {}
    assert _build_extra_headers({}) == {}
    assert _build_extra_headers({"X-Custom": None}) == {}


def test_build_extra_headers_keeps_unknown_custom_headers():
    """未列入黑名单的自定义头应保留，避免过滤规则限制扩展导出能力。"""
    headers = _build_extra_headers({"X-Custom-Trace": "abc123"})

    assert headers == {"X-Custom-Trace": "abc123"}
