"""License protection — hardware-bound standalone activation."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


LICENSE_DIR = Path.home() / ".ai-ive"
LICENSE_FILE = LICENSE_DIR / "license.dat"
TRIAL_FILE = LICENSE_DIR / "trial.json"


@dataclass
class LicenseStatus:
    valid: bool
    message: str
    licensed_to: str = ""
    expires: str | None = None
    is_trial: bool = False
    days_remaining: int | None = None


def machine_fingerprint() -> str:
    parts = [
        platform.node(),
        platform.machine(),
        platform.processor(),
        str(uuid.getnode()),
    ]
    if platform.system() == "Windows":
        try:
            import winreg  # type: ignore

            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            parts.append(str(guid))
        except Exception:
            pass
    raw = "|".join(parts).encode()
    return hashlib.sha256(raw).hexdigest()[:32].upper()


def _derive_key(secret: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=120_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret.encode()))


def generate_license_key(
    machine_id: str,
    licensed_to: str,
    secret: str,
    days_valid: int | None = None,
) -> str:
    """Vendor-side key generation (use secure secret in production)."""
    payload = {
        "machine_id": machine_id,
        "licensed_to": licensed_to,
        "issued": datetime.utcnow().isoformat(),
        "expires": (
            (datetime.utcnow() + timedelta(days=days_valid)).isoformat()
            if days_valid
            else None
        ),
    }
    salt = hashlib.sha256(machine_id.encode()).digest()[:16]
    f = Fernet(_derive_key(secret, salt))
    token = f.encrypt(json.dumps(payload).encode())
    return base64.urlsafe_b64encode(salt + token).decode()


def activate_license(license_key: str, secret: str | None = None) -> LicenseStatus:
    secret = secret or os.environ.get("AIVE_LICENSE_SECRET", "AI-IVE-DEV-SECRET-CHANGE-ME")
    try:
        raw = base64.urlsafe_b64decode(license_key.encode())
        salt, token = raw[:16], raw[16:]
        f = Fernet(_derive_key(secret, salt))
        payload = json.loads(f.decrypt(token).decode())
    except (InvalidToken, Exception) as e:
        return LicenseStatus(False, f"Invalid license key: {e}")

    if payload.get("machine_id") != machine_fingerprint():
        return LicenseStatus(False, "License not valid for this machine")

    expires = payload.get("expires")
    if expires and datetime.fromisoformat(expires) < datetime.utcnow():
        return LicenseStatus(False, "License expired", payload.get("licensed_to", ""), expires)

    LICENSE_DIR.mkdir(parents=True, exist_ok=True)
    LICENSE_FILE.write_text(license_key)
    return LicenseStatus(
        True,
        "License activated",
        payload.get("licensed_to", ""),
        expires,
    )


def check_license(trial_days: int = 14) -> LicenseStatus:
    mid = machine_fingerprint()
    secret = os.environ.get("AIVE_LICENSE_SECRET", "AI-IVE-DEV-SECRET-CHANGE-ME")

    if LICENSE_FILE.exists():
        status = activate_license(LICENSE_FILE.read_text().strip(), secret)
        if status.valid:
            return status
        LICENSE_FILE.unlink(missing_ok=True)

    LICENSE_DIR.mkdir(parents=True, exist_ok=True)
    if not TRIAL_FILE.exists():
        TRIAL_FILE.write_text(
            json.dumps({"started": datetime.utcnow().isoformat(), "machine_id": mid})
        )

    trial = json.loads(TRIAL_FILE.read_text())
    started = datetime.fromisoformat(trial["started"])
    elapsed = (datetime.utcnow() - started).days
    remaining = max(0, trial_days - elapsed)
    if remaining <= 0:
        return LicenseStatus(False, "Trial expired. Please activate a license.", is_trial=True)
    return LicenseStatus(
        True,
        f"Trial mode — {remaining} day(s) remaining",
        is_trial=True,
        days_remaining=remaining,
    )
