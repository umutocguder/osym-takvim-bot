# Created by 11Hopem
# Copyright (c) 2026 11Hopem. All rights reserved.
# Licensed under 11Hopem Proprietary License.

import unittest
import tempfile
import os
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from osym_bot.telemetry.firebase_config import FIREBASE_ECOSYSTEM_CONFIG
from osym_bot.telemetry.logger import TelemetryLogger, scrub_sensitive_data, to_firestore_fields

class TestTelemetryLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.logger = TelemetryLogger(
            app_name="osym-takvim-bot-test",
            app_version="1.0.0",
            log_dir=self.temp_dir.name
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_firebase_config(self):
        self.assertEqual(FIREBASE_ECOSYSTEM_CONFIG["account"], "umutocgdr@gmail.com")
        self.assertEqual(FIREBASE_ECOSYSTEM_CONFIG["project_id"], "hopem-software-cloud")
        self.assertTrue("hopem-software-cloud" in FIREBASE_ECOSYSTEM_CONFIG["firestore_base_url"])

    def test_log_writing_and_local_custody(self):
        entry = self.logger.info("Calendar sync started", {"exam": "ALES"})
        self.assertEqual(entry["level"], "INFO")
        self.assertEqual(entry["app_name"], "osym-takvim-bot-test")
        self.assertEqual(entry["context"]["exam"], "ALES")
        self.assertEqual(entry["target_collection"], "app_logs")

        error_entry = self.logger.error("Network timeout during scrape", {"retry": 1})
        self.assertEqual(error_entry["level"], "ERROR")

        # Verify JSONL file exists and is populated
        self.assertTrue(os.path.exists(self.logger.log_file))
        with open(self.logger.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)
            parsed = json.loads(lines[0])
            self.assertEqual(parsed["message"], "Calendar sync started")

    def test_scrub_sensitive_data(self):
        dirty = {
            "password": "SecretPassword123",
            "api_key": "AIzaSySecretToken",
            "token": "Bearer bot-auth-token",
            "candidate": {
                "tckn": "12345678901",
                "phone": "05321112233",
                "credit_card": "4543 1234 5678 9012"
            },
            "msg": "Candidate TCKN 12345678901 and card 4543 1234 5678 9012 used Bearer eyJhb"
        }
        clean = scrub_sensitive_data(dirty)
        self.assertEqual(clean["password"], "***REDACTED***")
        self.assertEqual(clean["api_key"], "***REDACTED***")
        self.assertEqual(clean["token"], "***REDACTED***")
        self.assertEqual(clean["candidate"]["tckn"], "***REDACTED***")
        self.assertEqual(clean["candidate"]["credit_card"], "***REDACTED***")
        self.assertNotIn("12345678901", clean["msg"])
        self.assertNotIn("4543 1234 5678 9012", clean["msg"])
        self.assertNotIn("eyJhb", clean["msg"])

    def test_to_firestore_fields(self):
        fields = to_firestore_fields({
            "appName": "osym-takvim-bot",
            "eventsCount": 15,
            "duration": 2.5,
            "success": True,
            "error": None,
            "stats": {"created": 3, "updated": 1}
        })
        self.assertEqual(fields["appName"], {"stringValue": "osym-takvim-bot"})
        self.assertEqual(fields["eventsCount"], {"integerValue": "15"})
        self.assertEqual(fields["duration"], {"doubleValue": 2.5})
        self.assertEqual(fields["success"], {"booleanValue": True})
        self.assertEqual(fields["error"], {"nullValue": None})
        self.assertIn("created", fields["stats"]["stringValue"])

    def test_multi_collection_routing(self):
        sec = self.logger.security("Unauthorized calendar access attempt", {"app": "unknown"})
        self.assertEqual(sec["target_collection"], "security_audit_logs")

        tel = self.logger.telemetry("Sync completed", {"created": 5, "updated": 2})
        self.assertEqual(tel["target_collection"], "telemetry_logs")

        vis = self.logger.visitor("Dry run executed", {"mode": "cli"})
        self.assertEqual(vis["target_collection"], "visitor_logs")

        cr = self.logger.crash("Calendar process crashed", {"code": 1})
        self.assertEqual(cr["target_collection"], "crash_logs")

        perf = self.logger.performance("scrape_latency", 185)
        self.assertEqual(perf["target_collection"], "telemetry_logs")

    def test_zero_crash_guarantee(self):
        res1 = self.logger.log(None, None)
        self.assertIsNotNone(res1)
        res2 = self.logger.error(Exception("Test exception"))
        self.assertIsNotNone(res2)

if __name__ == "__main__":
    unittest.main()
