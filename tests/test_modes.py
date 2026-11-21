import json

import pytest

from memoryforall.cli import main


@pytest.fixture(autouse=True)
def cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORYFORALL_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return tmp_path


def settings(cfg):
    return json.loads((cfg / "cfg" / "settings.json").read_text(encoding="utf-8"))


def test_mode_defaults_to_local(capsys):
    assert main(["mode"]) == 0
    assert capsys.readouterr().out == "search: local\npack: local\n"


def test_mode_search_hosted_refused_without_openai_key(cfg, capsys, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret")
    assert main(["mode", "search", "hosted"]) == 2
    assert "OPENAI_API_KEY" in capsys.readouterr().err
    assert main(["mode"]) == 0
    assert "search: local" in capsys.readouterr().out


def test_mode_search_hosted_warns_and_saves_keeping_kb(cfg, capsys, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-value")
    main(["set-kb", str(cfg / "kb")])
    assert main(["mode", "search", "hosted"]) == 0
    out = capsys.readouterr().out
    assert "sent to OpenAI" in out and "sk-secret-value" not in out
    s = settings(cfg)
    assert s["search_mode"] == "hosted" and s["kb"] == str((cfg / "kb").resolve())
    assert "sk-secret-value" not in json.dumps(s)
    main(["set-kb", str(cfg / "kb2")])
    assert settings(cfg)["search_mode"] == "hosted"


@pytest.mark.parametrize("api,key", [("claude", "ANTHROPIC_API_KEY"), ("openai", "OPENAI_API_KEY")])
def test_mode_pack_hosted_checks_api_key(cfg, capsys, monkeypatch, api, key):
    assert main(["mode", "pack", "hosted", "--api", api]) == 2
    assert key in capsys.readouterr().err
    monkeypatch.setenv(key, "secret-123")
    assert main(["mode", "pack", "hosted", "--api", api]) == 0
    assert f"pack: hosted ({api})" in capsys.readouterr().out
    assert settings(cfg)["pack_mode"] == "hosted"
    assert main(["mode", "pack", "local"]) == 0
    assert settings(cfg)["pack_mode"] == "local"


def test_unknown_mode_value_names_file_and_value(cfg, capsys):
    f = cfg / "cfg" / "settings.json"
    f.parent.mkdir()
    f.write_text(json.dumps({"search_mode": "cloud"}), encoding="utf-8")
    assert main(["mode"]) == 2
    err = capsys.readouterr().err
    assert str(f) in err and "cloud" in err


def test_status_shows_modes_and_key_presence_never_values(cfg, capsys, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-value")
    main(["set-kb", str(cfg / "kb")])
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "search: local\npack: local" in out
    assert "OPENAI_API_KEY: present" in out and "ANTHROPIC_API_KEY: missing" in out
    assert "sk-secret-value" not in out
