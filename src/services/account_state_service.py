"""
账号登录态文件解析服务。

主渠道是前端账号管理维护的 state/*.json，根目录 xianyu_state.json 仅作为旧版兼容兜底。
"""
from __future__ import annotations

import os

from src.infrastructure.config.env_manager import env_manager
from src.services.account_strategy_service import (
    clean_account_state_file,
    normalize_account_strategy,
)


DEFAULT_ACCOUNT_NAME = "default"
DEFAULT_ACCOUNT_STATE_DIR = "state"
LEGACY_STATE_FILE = "xianyu_state.json"


def normalize_state_path(path: str | None) -> str:
    text = str(path or "").strip()
    if not text:
        return ""
    return text.replace("\\", "/").rstrip("/")


def to_filesystem_path(path: str) -> str:
    return normalize_state_path(path).replace("/", os.sep)


def account_state_dir() -> str:
    raw = env_manager.get_value("ACCOUNT_STATE_DIR", DEFAULT_ACCOUNT_STATE_DIR)
    return normalize_state_path(str(raw or DEFAULT_ACCOUNT_STATE_DIR).strip("\"'"))


def legacy_state_file() -> str:
    raw = env_manager.get_value("STATE_FILE", LEGACY_STATE_FILE)
    return normalize_state_path(str(raw or LEGACY_STATE_FILE).strip("\"'"))


def account_state_path(name: str) -> str:
    return normalize_state_path(f"{account_state_dir()}/{name}.json")


def default_account_state_path() -> str:
    return account_state_path(DEFAULT_ACCOUNT_NAME)


def ensure_account_state_dir() -> None:
    os.makedirs(to_filesystem_path(account_state_dir()), exist_ok=True)


def account_state_file_exists(path: str) -> bool:
    return bool(path) and os.path.exists(to_filesystem_path(path))


def list_account_state_files() -> list[str]:
    state_dir = account_state_dir()
    fs_dir = to_filesystem_path(state_dir)
    if not os.path.isdir(fs_dir):
        return []
    files = []
    for filename in os.listdir(fs_dir):
        if filename.endswith(".json"):
            files.append(normalize_state_path(f"{state_dir}/{filename}"))
    return sorted(files)


def resolve_task_state_candidates(task_config: dict) -> list[str]:
    account_files = list_account_state_files()
    legacy_file = legacy_state_file()
    legacy_files = [legacy_file] if account_state_file_exists(legacy_file) else []
    account_state_file = clean_account_state_file(task_config.get("account_state_file"))
    strategy = normalize_account_strategy(
        task_config.get("account_strategy"),
        account_state_file,
    )

    if strategy == "fixed":
        return [account_state_file] if account_state_file else []
    if strategy == "rotate":
        return account_files
    return account_files or legacy_files


def resolve_preferred_task_state_file(task_config: dict) -> str | None:
    candidates = resolve_task_state_candidates(task_config)
    return candidates[0] if candidates else None
