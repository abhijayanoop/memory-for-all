import pytest

from memoryforall.cli import main


@pytest.fixture(autouse=True)
def cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORYFORALL_CONFIG_DIR", str(tmp_path / "cfg"))
    return tmp_path


def test_set_kb_then_commands_use_it_and_create_folder(cfg, capsys):
    kb = cfg / "my kb"
    assert main(["set-kb", str(kb)]) == 0
    assert kb.is_dir()
    assert main(["status"]) == 0
    assert capsys.readouterr().out.split()[:4] == ["chatgpt:", "0", "claude:", "0"]


def test_flag_overrides_saved_path(cfg, capsys):
    main(["set-kb", str(cfg / "saved")])
    other = cfg / "other kb"
    assert main(["status", "--kb", str(other)]) == 0
    assert other.is_dir()


def test_no_path_suggests_documents(cfg, capsys):
    assert main(["status"]) == 2
    err = capsys.readouterr().err
    assert "set-kb" in err and "Documents" in err
