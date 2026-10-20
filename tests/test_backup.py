# Created by 11Hopem
# Copyright (c) 2026 11Hopem. All rights reserved.
# Licensed under 11Hopem Proprietary License.

import unittest
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.backup import create_backup, verify_backup, LATEST_BACKUP, CHECKSUMS_FILE

class TestAutonomousBackup(unittest.TestCase):
    def test_backup_creation_and_integrity(self):
        res = create_backup()
        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(os.path.exists(LATEST_BACKUP))
        self.assertTrue(os.path.exists(CHECKSUMS_FILE))

        # Verify integrity
        self.assertTrue(verify_backup())

        # Verify payload structure
        with open(LATEST_BACKUP, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["appName"], "osym-takvim-bot")
            self.assertEqual(data["author"], "11Hopem")
            self.assertIn("config", data)

if __name__ == "__main__":
    unittest.main()
