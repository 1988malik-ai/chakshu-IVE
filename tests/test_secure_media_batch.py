"""R-145 secure media batch tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from aive.forensics.secure_media_batch import batch_secure_export, register_secure_media, scan_secure_media


def test_scan_secure_media_folder(tmp_path: Path):
    media = tmp_path / "nested" / "clip.mp4"
    media.parent.mkdir(parents=True)
    media.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64)

    result = scan_secure_media(tmp_path)
    assert result["success"] is True
    assert result["count"] == 1
    assert result["files"][0]["relative_path"] == "nested/clip.mp4"


def test_batch_secure_export_copy(tmp_path: Path):
    src_root = tmp_path / "secure"
    out = tmp_path / "export"
    file_a = src_root / "a.jpg"
    src_root.mkdir()
    file_a.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 32)

    result = batch_secure_export(src_root, out, mode="copy")
    assert result["total"] == 1
    assert result["done"] == 1
    assert result["failed"] == 0
    assert (out / "a.jpg").is_file()
    assert Path(result["report_path"]).is_file()


def test_register_secure_media(tmp_path: Path):
    root = tmp_path / "case"
    root.mkdir()
    (root / "evidence.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x01" * 40)

    result = register_secure_media(root, actor="tester")
    assert result["success"] is True
    assert result["registered"] == 1
