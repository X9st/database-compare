"""加密密钥路径解析测试"""
from __future__ import annotations

from pathlib import Path

from app.utils import crypto


def test_resolve_key_file_defaults_to_project_data_dir(monkeypatch):
    monkeypatch.delenv("ENCRYPTION_KEY_FILE", raising=False)
    path = crypto._resolve_key_file()
    assert path == crypto.PROJECT_ROOT / "data/encryption.key"


def test_resolve_key_file_supports_relative_path(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY_FILE", "./custom/key.file")
    path = crypto._resolve_key_file()
    assert path == crypto.PROJECT_ROOT / "custom/key.file"


def test_resolve_key_file_keeps_absolute_path(monkeypatch, tmp_path):
    absolute = tmp_path / "fixed.key"
    monkeypatch.setenv("ENCRYPTION_KEY_FILE", str(absolute))
    path = crypto._resolve_key_file()
    assert path == Path(str(absolute))
