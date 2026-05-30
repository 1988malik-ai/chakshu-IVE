"""
File and frame hash verification — multiple algorithms.

Author: Mohit M
"""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Any

import numpy as np

from aive.imaging import bgr_to_jpeg_base64

ALGORITHMS = ("md5", "sha1", "sha256", "sha512")


def _hasher(algorithm: str):
    alg = algorithm.lower()
    if alg == "md5":
        return hashlib.md5()
    if alg == "sha1":
        return hashlib.sha1()
    if alg == "sha512":
        return hashlib.sha512()
    return hashlib.sha256()


def hash_file(path: Path, algorithm: str = "sha256") -> str:
    h = _hasher(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_bytes(data: bytes, algorithm: str = "sha256") -> str:
    h = _hasher(algorithm)
    h.update(data)
    return h.hexdigest()


def hash_all_algorithms(path: Path) -> dict[str, str]:
    data = path.read_bytes()
    return {alg: hash_bytes(data, alg) for alg in ALGORITHMS}


def hash_frame(frame: np.ndarray, algorithm: str = "sha256") -> str:
    raw = base64.b64decode(bgr_to_jpeg_base64(frame, quality=95))
    return hash_bytes(raw, algorithm)


def verify_file(path: Path, expected: dict[str, str]) -> dict[str, Any]:
    actual = hash_all_algorithms(path)
    match = {alg: actual.get(alg) == expected.get(alg) for alg in ALGORITHMS if alg in expected}
    return {
        "path": str(path),
        "actual": actual,
        "expected": expected,
        "match": match,
        "valid": all(match.values()) if match else False,
    }
