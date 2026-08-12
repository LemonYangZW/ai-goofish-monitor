from src.services.account_state_service import (
    default_account_state_path,
    list_account_state_files,
    resolve_preferred_task_state_file,
)


def test_account_state_files_are_listed_with_forward_slashes(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("ACCOUNT_STATE_DIR=state\n", encoding="utf-8")
    monkeypatch.setattr("src.infrastructure.config.env_manager.env_manager.env_file", env_file)
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "1.json").write_text("{}", encoding="utf-8")

    assert list_account_state_files() == ["state/1.json"]


def test_auto_strategy_prefers_account_management_files_over_legacy_state(
    tmp_path,
    monkeypatch,
):
    env_file = tmp_path / ".env"
    env_file.write_text("ACCOUNT_STATE_DIR=state\n", encoding="utf-8")
    monkeypatch.setattr("src.infrastructure.config.env_manager.env_manager.env_file", env_file)
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "1.json").write_text("{}", encoding="utf-8")
    (tmp_path / "xianyu_state.json").write_text("{}", encoding="utf-8")

    assert resolve_preferred_task_state_file({"account_strategy": "auto"}) == "state/1.json"


def test_default_login_state_path_belongs_to_account_management(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setattr("src.infrastructure.config.env_manager.env_manager.env_file", env_file)

    assert default_account_state_path() == "state/default.json"
