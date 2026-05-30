#!/usr/bin/env python3
"""Vendor utility — generate a machine-bound license key."""

import argparse
import os
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))

from aive.license.protection import generate_license_key, machine_fingerprint


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--machine-id", default=None)
    p.add_argument("--name", default="Licensed User")
    p.add_argument("--days", type=int, default=None)
    p.add_argument("--secret", default=os.environ.get("AIVE_LICENSE_SECRET", "AI-IVE-DEV-SECRET-CHANGE-ME"))
    args = p.parse_args()
    mid = args.machine_id or machine_fingerprint()
    key = generate_license_key(mid, args.name, args.secret, args.days)
    print(f"Machine ID: {mid}")
    print(f"License key:\n{key}")


if __name__ == "__main__":
    main()
