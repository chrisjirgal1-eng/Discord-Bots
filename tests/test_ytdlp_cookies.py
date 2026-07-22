import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

import ytdlp_cookies


def _clear_env(monkeypatch):
    monkeypatch.delenv("YTDLP_COOKIES", raising=False)
    monkeypatch.delenv("COOKIES", raising=False)


def test_none_when_nothing_set(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.setattr(ytdlp_cookies, "ROOT", str(tmp_path))  # no secrets/cookies.txt here
    assert ytdlp_cookies.cookies_file() is None


def test_env_path_must_exist(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.setattr(ytdlp_cookies, "ROOT", str(tmp_path))
    monkeypatch.setenv("YTDLP_COOKIES", str(tmp_path / "missing.txt"))
    assert ytdlp_cookies.cookies_file() is None  # points at a nonexistent file -> ignored


def test_ytdlp_cookies_takes_priority(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.setattr(ytdlp_cookies, "ROOT", str(tmp_path))
    primary = tmp_path / "primary.txt"; primary.write_text("c")
    legacy = tmp_path / "legacy.txt"; legacy.write_text("c")
    monkeypatch.setenv("YTDLP_COOKIES", str(primary))
    monkeypatch.setenv("COOKIES", str(legacy))
    assert ytdlp_cookies.cookies_file() == str(primary)


def test_cookies_env_fallback(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.setattr(ytdlp_cookies, "ROOT", str(tmp_path))
    legacy = tmp_path / "legacy.txt"; legacy.write_text("c")
    monkeypatch.setenv("COOKIES", str(legacy))
    assert ytdlp_cookies.cookies_file() == str(legacy)


def test_secrets_fallback(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.setattr(ytdlp_cookies, "ROOT", str(tmp_path))
    secrets = tmp_path / "secrets"; secrets.mkdir()
    f = secrets / "cookies.txt"; f.write_text("c")
    assert ytdlp_cookies.cookies_file() == str(f)
