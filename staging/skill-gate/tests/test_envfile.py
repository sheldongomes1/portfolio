"""The .env loader: nearest file wins, the shell wins over the file, blanks are skipped."""

import os

import pytest

from skillgate.envfile import find_env_file, load_env_file, parse


@pytest.fixture
def clean_env(monkeypatch):
    for name in ("SG_TEST_A", "SG_TEST_B", "SG_TEST_C", "SG_TEST_D"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_parse_forms():
    text = '# comment\n\nexport SG_TEST_A=one\nSG_TEST_B = "two # not a comment"\nSG_TEST_C=three # note\nnot a line\n'
    assert parse(text) == {"SG_TEST_A": "one", "SG_TEST_B": "two # not a comment", "SG_TEST_C": "three"}


def test_loads_from_parent_and_never_overrides(tmp_path, clean_env):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".env").write_text("SG_TEST_A=from-file\nSG_TEST_B=from-file\nSG_TEST_C=\n", encoding="utf-8")
    sub = tmp_path / "examples" / "demo"
    sub.mkdir(parents=True)
    clean_env.setenv("SG_TEST_B", "from-shell")
    assert load_env_file(sub) == tmp_path / ".env"
    assert os.environ["SG_TEST_A"] == "from-file"
    assert os.environ["SG_TEST_B"] == "from-shell"
    assert "SG_TEST_C" not in os.environ


def test_nearest_file_wins(tmp_path, clean_env):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".env").write_text("SG_TEST_D=outer\n", encoding="utf-8")
    inner = tmp_path / "inner"
    inner.mkdir()
    (inner / ".env").write_text("SG_TEST_D=inner\n", encoding="utf-8")
    load_env_file(inner)
    assert os.environ["SG_TEST_D"] == "inner"


def test_stops_at_repository_root(tmp_path):
    (tmp_path / ".env").write_text("SG_TEST_A=outside\n", encoding="utf-8")
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    assert find_env_file(repo) is None
