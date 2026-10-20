import argparse
import json
import logging
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List

from .apple_calendar import AppleCalendar, CalendarError
from .events import MARKER, CalendarEvent, ExamFilter, build_events, select_rows, upcoming
from .scraper import CALENDAR_URL, ScrapeError, fetch_calendar_html, parse_calendar

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "config.json"

log = logging.getLogger("osym_bot")


def notify(message: str) -> None:
    script = 'on run argv\n display notification (item 1 of argv) with title "ÖSYM Takvim Bot"\nend run'
    subprocess.run(["osascript", "-e", script, message], capture_output=True)


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def plan_events(page: str, config: dict, today: date) -> List[CalendarEvent]:
    filters = [ExamFilter.from_dict(raw) for raw in config["exams"]]
    rows = select_rows(parse_calendar(page), filters)
    log.info("Matched %d exam rows", len(rows))
    events = build_events(rows, config["labels"], int(config.get("exam_duration_minutes", 180)))
    return upcoming(events, today)


def sync(calendar: AppleCalendar, events: List[CalendarEvent], source_label: str) -> Dict[str, int]:
    existing = calendar.existing_markers()
    stats = {"created": 0, "updated": 0, "unchanged": 0}
    for event in events:
        if event.marker in existing:
            stats["unchanged"] += 1
            continue
        key_prefix = "%s:%s#" % (MARKER, event.key)
        stale = [uid for marker, uids in existing.items() if marker.startswith(key_prefix) for uid in uids]
        for uid in stale:
            calendar.delete(uid)
        calendar.create(event, "%s: %s" % (source_label, event.url))
        stats["updated" if stale else "created"] += 1
        log.info("%s %s (%s -> %s)", "Updated" if stale else "Created", event.title, event.start, event.end)
    return stats


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="osym_bot", description="Sync selected OSYM exam dates into macOS Calendar")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--html", type=Path, help="Parse a saved HTML file instead of downloading the page")
    parser.add_argument("--dry-run", action="store_true", help="Print planned events without touching the calendar")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = load_config(args.config)

    try:
        page = args.html.read_text(encoding="utf-8") if args.html else fetch_calendar_html(CALENDAR_URL)
        events = plan_events(page, config, args.today)
    except (ScrapeError, OSError) as error:
        log.error("Could not read OSYM calendar: %s", error)
        notify("OSYM calendar could not be read: %s" % error)
        return 2

    if args.dry_run:
        for event in events:
            kind = "all-day" if event.all_day else "timed"
            print("%s  %s -> %s  [%s]  %s" % (event.title, event.start, event.end, kind, event.url))
        log.info("Dry run: %d upcoming events", len(events))
        return 0

    try:
        stats = sync(AppleCalendar(config["calendar_name"]), events, config["labels"]["source"])
    except CalendarError as error:
        log.error("Calendar sync failed: %s", error)
        notify("Calendar sync failed: %s" % error)
        return 3
    log.info("Done: %s", stats)
    changed = stats["created"] + stats["updated"]
    if changed:
        notify("%d exam events added or updated" % changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
