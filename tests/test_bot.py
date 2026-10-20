import json
import unittest
from datetime import date, datetime
from pathlib import Path

from osym_bot.events import ExamFilter, build_events, select_rows, upcoming
from osym_bot.scraper import ScrapeError, parse_calendar, parse_moments

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "sinav_takvimi_2026.html"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
FILTERS = [ExamFilter.from_dict(raw) for raw in CONFIG["exams"]]


def selected():
    return select_rows(parse_calendar(FIXTURE.read_text(encoding="utf-8")), FILTERS)


class ScraperTests(unittest.TestCase):
    def test_parses_all_rows(self):
        rows = parse_calendar(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 93)

    def test_parses_dates_and_times(self):
        moments = parse_moments("07.10.2026 16:00 | 15.10.2026 23:59")
        self.assertEqual(moments[0].as_datetime(), datetime(2026, 10, 7, 16, 0))
        self.assertEqual(moments[1].day, date(2026, 10, 15))
        self.assertEqual(parse_moments("-"), [])

    def test_empty_page_raises(self):
        with self.assertRaises(ScrapeError):
            parse_calendar("<html></html>")


class FilterTests(unittest.TestCase):
    def test_only_requested_exams(self):
        names = sorted(row.session_name for row in selected())
        self.assertEqual(
            names,
            sorted([
                "2026-ALES/1", "2026-ALES/2", "2026-ALES/3",
                "2026-YDS/1", "2026-YDS/2",
                "2026-YÖKDİL/1", "2026-YÖKDİL/2",
                "2026-KPSS Lisans (Genel Yetenek-Genel Kültür)",
                "2026-KPSS Lisans (Alan Bilgisi) 1. gün",
                "2026-KPSS Lisans (Alan Bilgisi) 2. gün",
            ]),
        )

    def test_excludes_electronic_and_other_kpss(self):
        codes = {row.code for row in selected()}
        self.assertNotIn("e-YDS", codes)
        self.assertNotIn("e-YÖKDİL", codes)
        names = " ".join(row.session_name for row in selected())
        for excluded in ("Ön Lisans", "Ortaöğretim", "DHBT"):
            self.assertNotIn(excluded, names)


class EventTests(unittest.TestCase):
    def setUp(self):
        self.events = build_events(selected(), CONFIG["labels"], 180)
        self.by_key = {event.key: event for event in self.events}

    def test_kpss_application_is_grouped(self):
        kpss = [e for e in self.events if e.key.startswith("apply:") and "KPSS" in e.key]
        self.assertEqual(len(kpss), 1)
        self.assertEqual(kpss[0].title, "2026-KPSS Lisans · Başvuru")
        self.assertEqual(kpss[0].start, datetime(2026, 7, 1))
        self.assertEqual(kpss[0].end, datetime(2026, 7, 14))

    def test_application_span_alarms(self):
        event = self.by_key["apply:2026-ALES/3"]
        self.assertTrue(event.all_day)
        self.assertEqual(event.start, datetime(2026, 10, 7))
        self.assertEqual(event.end, datetime(2026, 10, 16))
        self.assertEqual(event.alarms, (540, 8 * 1440 + 540))

    def test_timed_exam(self):
        event = self.by_key["exam:2026-ALES/3"]
        self.assertFalse(event.all_day)
        self.assertEqual(event.start, datetime(2026, 11, 29, 10, 15))
        self.assertEqual(event.end, datetime(2026, 11, 29, 13, 15))

    def test_all_day_exam(self):
        event = self.by_key["exam:2026-YDS/1"]
        self.assertTrue(event.all_day)
        self.assertEqual(event.start, datetime(2026, 4, 5))

    def test_upcoming_drops_past_events(self):
        keys = {event.key for event in upcoming(self.events, date(2026, 10, 20))}
        self.assertEqual(keys, {"late:2026-ALES/3", "exam:2026-YDS/2", "exam:2026-ALES/3"})

    def test_marker_changes_when_dates_change(self):
        event = self.by_key["exam:2026-ALES/3"]
        moved = event.__class__(**{**event.__dict__, "start": datetime(2026, 11, 30, 10, 15)})
        self.assertEqual(event.key, moved.key)
        self.assertNotEqual(event.marker, moved.marker)


if __name__ == "__main__":
    unittest.main()
