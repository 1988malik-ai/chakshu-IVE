#!/usr/bin/env python3
"""Verify Phase 4 — all catalog filters are implemented and apply without error."""

from __future__ import annotations

import sys

import numpy as np

from aive.filters.catalog import FILTER_CATALOG, filter_count
from aive.filters.engine import apply_filter, is_implemented


def main() -> int:
    n = sum(1 for f in FILTER_CATALOG if is_implemented(f.id))
    total = filter_count()
    print(f"implemented: {n} / {total}")
    if n != total:
        missing = [f.id for f in FILTER_CATALOG if not is_implemented(f.id)]
        print("missing:", missing[:10])
        return 1

    rng = np.random.default_rng(42)
    frame = rng.integers(0, 256, (48, 64, 3), dtype=np.uint8)
    failed: list[str] = []
    for spec in FILTER_CATALOG:
        try:
            out = apply_filter(frame, spec.id)
            if out is None or out.size == 0:
                failed.append(spec.id)
        except Exception as exc:
            failed.append(f"{spec.id}: {exc}")

    if failed:
        print("failures:", failed[:15])
        return 1

    print("ALL PASS — Phase 4 filter catalog live")
    return 0


if __name__ == "__main__":
    sys.exit(main())
