from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import dependencies as deps
from src.api.routes import settings
from src.infrastructure.config.env_manager import env_manager


_SETTINGS_ENV_KEYS = [
    "ACCOUNT_ROTATION_ENABLED",
    "ACCOUNT_ROTATION_MODE",
    "ACCOUNT_ROTATION_RETRY_LIMIT",
    "ACCOUNT_BLACKLIST_TTL",
    "ACCOUNT_STATE_DIR",
    "PROXY_ROTATION_ENABLED",
    "PROXY_ROTATION_MODE",
    "PROXY_POOL",
    "PROXY_ROTATION_RETRY_LIMIT",
    "PROXY_BLACKLIST_TTL",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL_NAME",
    "SKIP_AI_ANALYSIS",
    "PROXY_URL",
    "NTFY_TOPIC_URL",
    "GOTIFY_URL",
    "GOTIFY_TOKEN",
    "BARK_URL",
    "WX_BOT_URL",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "TELEGRAM_API_BASE_URL",
    "WEBHOOK_URL",
    "WEBHOOK_METHOD",
    "WEBHOOK_HEADERS",
    "WEBHOOK_CONTENT_TYPE",
    "WEBHOOK_QUERY_PARAMETERS",
    "WEBHOOK_BODY",
    "PCURL_TO_MOBILE",
]


class _IdleProcessService:
    def __init__(self) -> None:
        self.processes = {}


def _build_settings_client() -> TestClient:
    app = FastAPI()
    app.include_router(settings.router)
    app.dependency_overrides[deps.get_process_service] = _IdleProcessService
    return TestClient(app)


def _clear_settings_env(monkeypatch) -> None:
    for key in _SETTINGS_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_rotation_settings_include_account_rotation_fields(tmp_path, monkeypatch):
    _clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "ACCOUNT_ROTATION_ENABLED=false",
                "ACCOUNT_ROTATION_MODE=per_task",
                "ACCOUNT_ROTATION_RETRY_LIMIT=2",
                "ACCOUNT_BLACKLIST_TTL=300",
                "ACCOUNT_STATE_DIR=state",
                "PROXY_ROTATION_ENABLED=false",
                "PROXY_ROTATION_MODE=per_task",
                "PROXY_ROTATION_RETRY_LIMIT=2",
                "PROXY_BLACKLIST_TTL=300",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(env_manager, "env_file", env_file)

    client = _build_settings_client()

    response = client.get("/api/settings/rotation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ACCOUNT_ROTATION_ENABLED"] is False
    assert payload["ACCOUNT_ROTATION_MODE"] == "per_task"
    assert payload["ACCOUNT_STATE_DIR"] == "state"

    update_response = client.put(
        "/api/settings/rotation",
        json={
            "ACCOUNT_ROTATION_ENABLED": True,
            "ACCOUNT_ROTATION_MODE": "on_failure",
            "ACCOUNT_ROTATION_RETRY_LIMIT": 4,
            "ACCOUNT_BLACKLIST_TTL": 900,
            "ACCOUNT_STATE_DIR": "accounts",
        },
    )
    assert update_response.status_code == 200

    latest = env_file.read_text(encoding="utf-8")
    assert "ACCOUNT_ROTATION_ENABLED=true" in latest
    assert "ACCOUNT_ROTATION_MODE=on_failure" in latest
    assert "ACCOUNT_ROTATION_RETRY_LIMIT=4" in latest
    assert "ACCOUNT_BLACKLIST_TTL=900" in latest
    assert "ACCOUNT_STATE_DIR=accounts" in latest


def test_notification_settings_redact_sensitive_values_and_expose_flags(tmp_path, monkeypatch):
    _clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "NTFY_TOPIC_URL=https://ntfy.sh/demo-topic",
                "GOTIFY_URL=https://gotify.example.com",
                "GOTIFY_TOKEN=secret-token",
                "BARK_URL=https://api.day.app/private-key/",
                "WX_BOT_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=secret",
                "TELEGRAM_BOT_TOKEN=telegram-secret",
                "TELEGRAM_CHAT_ID=123456",
                "TELEGRAM_API_BASE_URL=https://tg.example.com/proxy",
                "WEBHOOK_URL=https://hooks.example.com/notify?token=secret",
                'WEBHOOK_HEADERS={"Authorization":"Bearer secret"}',
                'WEBHOOK_BODY={"message":"{{content}}"}',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(env_manager, "env_file", env_file)
    client = _build_settings_client()

    response = client.get("/api/settings/notifications")

    assert response.status_code == 200
    payload = response.json()
    assert payload["NTFY_TOPIC_URL"] == "https://ntfy.sh/demo-topic"
    assert payload["GOTIFY_URL"] == "https://gotify.example.com"
    assert payload["TELEGRAM_CHAT_ID"] == "123456"
    assert payload["TELEGRAM_API_BASE_URL"] == "https://tg.example.com/proxy"
    assert payload["BARK_URL"] == ""
    assert payload["WX_BOT_URL"] == ""
    assert payload["GOTIFY_TOKEN"] == ""
    assert payload["TELEGRAM_BOT_TOKEN"] == ""
    assert payload["WEBHOOK_URL"] == ""
    assert payload["WEBHOOK_HEADERS"] == ""
    assert payload["BARK_URL_SET"] is True
    assert payload["WX_BOT_URL_SET"] is True
    assert payload["GOTIFY_TOKEN_SET"] is True
    assert payload["TELEGRAM_BOT_TOKEN_SET"] is True
    assert payload["WEBHOOK_URL_SET"] is True
    assert payload["WEBHOOK_HEADERS_SET"] is True
    assert payload["WEBHOOK_BODY"] == '{"message":"{{content}}"}'


def test_update_notification_settings_rejects_invalid_channel_config(tmp_path, monkeypatch):
    _clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setattr(env_manager, "env_file", env_file)
    client = _build_settings_client()

    gotify_response = client.put(
        "/api/settings/notifications",
        json={"GOTIFY_URL": "https://gotify.example.com"},
    )
    assert gotify_response.status_code == 422
    assert "GOTIFY_TOKEN" in gotify_response.text

    telegram_proxy_response = client.put(
        "/api/settings/notifications",
        json={"TELEGRAM_API_BASE_URL": "not-a-url"},
    )
    assert telegram_proxy_response.status_code == 422
    assert "TELEGRAM_API_BASE_URL" in telegram_proxy_response.text

    webhook_response = client.put(
        "/api/settings/notifications",
        json={
            "WEBHOOK_URL": "https://hooks.example.com/notify",
            "WEBHOOK_METHOD": "POST",
            "WEBHOOK_CONTENT_TYPE": "JSON",
            "WEBHOOK_HEADERS": '{"Authorization": "Bearer secret"',
        },
    )
    assert webhook_response.status_code == 422
    assert "WEBHOOK_HEADERS" in webhook_response.text


def test_system_status_includes_notification_channel_flags(tmp_path, monkeypatch):
    _clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "NTFY_TOPIC_URL=https://ntfy.sh/demo-topic",
                "GOTIFY_URL=https://gotify.example.com",
                "GOTIFY_TOKEN=secret-token",
                "BARK_URL=https://api.day.app/private-key/",
                "WX_BOT_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=secret",
                "TELEGRAM_BOT_TOKEN=telegram-secret",
                "TELEGRAM_CHAT_ID=123456",
                "WEBHOOK_URL=https://hooks.example.com/notify",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(env_manager, "env_file", env_file)
    client = _build_settings_client()

    response = client.get("/api/settings/status")

    assert response.status_code == 200
    env_payload = response.json()["env_file"]
    assert env_payload["ntfy_topic_url_set"] is True
    assert env_payload["gotify_url_set"] is True
    assert env_payload["gotify_token_set"] is True
    assert env_payload["bark_url_set"] is True
    assert env_payload["wx_bot_url_set"] is True
    assert env_payload["telegram_bot_token_set"] is True
    assert env_payload["telegram_chat_id_set"] is True
    assert env_payload["webhook_url_set"] is True


def test_notification_test_endpoint_merges_stored_secret_values(tmp_path, monkeypatch):
    _clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TELEGRAM_BOT_TOKEN=stored-token",
                "TELEGRAM_CHAT_ID=10001",
                "TELEGRAM_API_BASE_URL=https://tg-proxy.example.com/base",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(env_manager, "env_file", env_file)
    client = _build_settings_client()

    captured = {}

    class _FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    def _fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse()

    monkeypatch.setattr("requests.post", _fake_post)

    response = client.post(
        "/api/settings/notifications/test",
        json={
            "channel": "telegram",
            "settings": {
                "TELEGRAM_CHAT_ID": "20002",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"]["telegram"]["success"] is True
    assert captured["url"] == "https://tg-proxy.example.com/base/botstored-token/sendMessage"
    assert captured["json"]["chat_id"] == "20002"


def test_notification_test_endpoint_ignores_other_channel_dirty_fields(tmp_path, monkeypatch):
    _clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "NTFY_TOPIC_URL=https://ntfy.sh/demo-topic\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(env_manager, "env_file", env_file)
    client = _build_settings_client()

    captured = []

    class _FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

    def _fake_post(url, data=None, headers=None, timeout=None, **kwargs):
        captured.append({
            "url": url,
            "data": data,
            "headers": headers,
        })
        return _FakeResponse()

    monkeypatch.setattr("requests.post", _fake_post)

    response = client.post(
        "/api/settings/notifications/test",
        json={
            "channel": "ntfy",
            "settings": {
                "GOTIFY_URL": "not-a-url",
                "WEBHOOK_BODY": '{"message":"{{content}}"}',
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert list(payload["results"]) == ["ntfy"]
    assert payload["results"]["ntfy"]["success"] is True
    assert len(captured) == 1
    assert captured[0]["url"] == "https://ntfy.sh/demo-topic"


def test_ai_settings_fall_back_to_runtime_environment_when_env_file_missing(tmp_path, monkeypatch):
    _clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    monkeypatch.setattr(env_manager, "env_file", env_file)
    monkeypatch.setenv("OPENAI_API_KEY", "runtime-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://runtime.example.com/v1")
    monkeypatch.setenv("OPENAI_MODEL_NAME", "runtime-model")
    monkeypatch.setenv("PROXY_URL", "http://127.0.0.1:7890")
    client = _build_settings_client()

    ai_response = client.get("/api/settings/ai")
    assert ai_response.status_code == 200
    assert ai_response.json() == {
        "OPENAI_BASE_URL": "https://runtime.example.com/v1",
        "OPENAI_MODEL_NAME": "runtime-model",
        "SKIP_AI_ANALYSIS": False,
        "PROXY_URL": "http://127.0.0.1:7890",
    }

    status_response = client.get("/api/settings/status")
    assert status_response.status_code == 200
    env_payload = status_response.json()["env_file"]
    assert env_payload["exists"] is False
    assert env_payload["openai_api_key_set"] is True
    assert env_payload["openai_base_url_set"] is True
    assert env_payload["openai_model_name_set"] is True


def test_notification_settings_fall_back_to_runtime_environment_when_env_file_missing(
    tmp_path, monkeypatch
):
    _clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    monkeypatch.setattr(env_manager, "env_file", env_file)
    monkeypatch.setenv("NTFY_TOPIC_URL", "https://ntfy.sh/runtime-topic")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "runtime-telegram-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "20001")
    monkeypatch.setenv("TELEGRAM_API_BASE_URL", "https://runtime-tg-proxy.example.com")
    monkeypatch.setenv("BARK_URL", "https://api.day.app/runtime-secret/")
    client = _build_settings_client()

    response = client.get("/api/settings/notifications")

    assert response.status_code == 200
    payload = response.json()
    assert payload["NTFY_TOPIC_URL"] == "https://ntfy.sh/runtime-topic"
    assert payload["TELEGRAM_CHAT_ID"] == "20001"
    assert payload["TELEGRAM_API_BASE_URL"] == "https://runtime-tg-proxy.example.com"
    assert payload["BARK_URL"] == ""
    assert payload["BARK_URL_SET"] is True
    assert payload["TELEGRAM_BOT_TOKEN_SET"] is True
    assert sorted(payload["CONFIGURED_CHANNELS"]) == ["bark", "ntfy", "telegram"]


class _FakeHTTPResponse:
    """模拟 httpx.Response。"""

    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"Error code: {self.status_code}")

    def json(self):
        return self._payload


def _patch_httpx_client(monkeypatch, request_history, response):
    """把 /ai/test 端点使用的 httpx.AsyncClient 换成可断言的假实现。"""
    import httpx

    class _FakeAsyncClient:
        def __init__(self, **kwargs):
            request_history.append(("init", kwargs))

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_exc):
            return False

        async def post(self, url, json=None, headers=None):
            request_history.append(("post", {"url": url, "json": json, "headers": headers}))
            if isinstance(response, Exception):
                raise response
            return response

    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)


def _post_ai_test(client):
    return client.post(
        "/api/settings/ai/test",
        json={
            "OPENAI_API_KEY": "demo",
            "OPENAI_BASE_URL": "https://example.com/v1/",
            "OPENAI_MODEL_NAME": "demo-model",
        },
    )


def _build_ai_test_client(tmp_path, monkeypatch):
    _clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setattr(env_manager, "env_file", env_file)
    return _build_settings_client()


def test_ai_test_endpoint_returns_content_from_chat_completions(tmp_path, monkeypatch):
    client = _build_ai_test_client(tmp_path, monkeypatch)
    request_history = []
    _patch_httpx_client(
        monkeypatch,
        request_history,
        _FakeHTTPResponse({"choices": [{"message": {"content": " OK "}}]}),
    )

    response = _post_ai_test(client)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["response"] == "OK"

    post_call = next(item for item in request_history if item[0] == "post")[1]
    assert post_call["url"].endswith("/chat/completions")
    assert post_call["json"]["model"] == "demo-model"
    assert post_call["json"]["messages"][0]["content"] == settings.AI_TEST_PROMPT
    assert post_call["headers"]["Authorization"] == "Bearer demo"


def test_ai_test_endpoint_reports_failure_when_upstream_returns_error(
    tmp_path, monkeypatch
):
    client = _build_ai_test_client(tmp_path, monkeypatch)
    _patch_httpx_client(
        monkeypatch, [], _FakeHTTPResponse({}, status_code=404)
    )

    response = _post_ai_test(client)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert "404" in payload["message"]


def test_ai_test_endpoint_reports_failure_when_response_has_no_choices(
    tmp_path, monkeypatch
):
    client = _build_ai_test_client(tmp_path, monkeypatch)
    _patch_httpx_client(monkeypatch, [], _FakeHTTPResponse({"choices": []}))

    response = _post_ai_test(client)

    payload = response.json()
    assert payload["success"] is False
    assert "空响应" in payload["message"]
