#!/usr/bin/env python3
# Created by 11Hopem
# Copyright (c) 2026 11Hopem. All rights reserved.
# Licensed under 11Hopem Proprietary License.

import os
import json
import hashlib
import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = PROJECT_ROOT / "data" / "backups"
CONFIG_FILE = PROJECT_ROOT / "config.json"
LATEST_BACKUP = BACKUP_DIR / "osym_latest_backup.json"
CHECKSUMS_FILE = BACKUP_DIR / "osym_checksums.json"

def calculate_sha256(data_bytes: bytes) -> str:
    return hashlib.sha256(data_bytes).hexdigest()

def create_backup() -> dict:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    config = {}
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open(encoding="utf-8") as f:
            config = json.load(f)

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    snapshot = {
        "appName": "osym-takvim-bot",
        "timestamp": timestamp,
        "author": "11Hopem",
        "config": config,
        "version": "1.0.0"
    }

    serialized = json.dumps(snapshot, indent=2, ensure_ascii=False)
    serialized_bytes = serialized.encode("utf-8")
    checksum = calculate_sha256(serialized_bytes)

    with LATEST_BACKUP.open("w", encoding="utf-8") as f:
        f.write(serialized)

    checksum_entry = {
        "timestamp": timestamp,
        "sha256": checksum,
        "size_bytes": len(serialized_bytes),
        "file": LATEST_BACKUP.name
    }

    history = []
    if CHECKSUMS_FILE.exists():
        try:
            with CHECKSUMS_FILE.open(encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(checksum_entry)
    if len(history) > 30:
        history = history[-30:]

    with CHECKSUMS_FILE.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    return {"status": "SUCCESS", "sha256": checksum, "file": str(LATEST_BACKUP)}

def verify_backup() -> bool:
    if not LATEST_BACKUP.exists() or not CHECKSUMS_FILE.exists():
        return False

    with LATEST_BACKUP.open("rb") as f:
        actual_hash = calculate_sha256(f.read())

    with CHECKSUMS_FILE.open(encoding="utf-8") as f:
        history = json.load(f)

    if not history:
        return False

    latest_recorded = history[-1]["sha256"]
    return actual_hash == latest_recorded

if __name__ == "__main__":
    res = create_backup()
    print(f"Backup created: {res['sha256']}")
