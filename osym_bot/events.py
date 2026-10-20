# Created by 11Hopem
# Copyright (c) 2026 11Hopem. All rights reserved.
# Licensed under 11Hopem Proprietary License.

import hashlib
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Sequence, Tuple

from .scraper import ExamRow, Moment

MARKER = "osym-bot"
MINUTES_PER_DAY = 24 * 60
ALL_DAY_ALARM_MINUTE = 9 * 60


@dataclass(frozen=True)
class ExamFilter:
    code: str
    name_includes: Tuple[str, ...] = ()
    name_excludes: Tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, raw: dict) -> "ExamFilter":
        return cls(
            code=raw["code"],
            name_includes=tuple(raw.get("name_includes", ())),
            name_excludes=tuple(raw.get("name_excludes", ())),
        )

    def matches(self, row: ExamRow) -> bool:
        if row.list_type != "sinav" or row.code.strip() != self.code:
            return False
        name = row.session_name
        if any(term not in name for term in self.name_includes):
            return False
        return not any(term in name for term in self.name_excludes)


@dataclass(frozen=True)
class CalendarEvent:
    key: str
    title: str
    start: datetime
    end: datetime
    all_day: bool
    url: str
    alarms: Tuple[int, ...]

    @property
    def fingerprint(self) -> str:
        raw = "|".join([self.title, self.start.isoformat(), self.end.isoformat(), str(self.all_day), self.url])
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

    @property
    def marker(self) -> str:
        return "%s:%s#%s" % (MARKER, self.key, self.fingerprint)

    @property
    def last_day(self) -> date:
        return (self.end - timedelta(days=1)).date() if self.all_day else self.end.date()


def select_rows(rows: Iterable[ExamRow], filters: Sequence[ExamFilter]) -> List[ExamRow]:
    return [row for row in rows if any(f.matches(row) for f in filters)]


def _all_day_span(moments: Sequence[Moment]) -> Tuple[datetime, datetime]:
    first = min(m.day for m in moments)
    last = max(m.day for m in moments)
    start = datetime(first.year, first.month, first.day)
    end = datetime(last.year, last.month, last.day) + timedelta(days=1)
    return start, end


def _span_alarms(start: datetime, end: datetime) -> Tuple[int, ...]:
    days = (end - start).days
    alarms = [ALL_DAY_ALARM_MINUTE]
    if days > 1:
        alarms.append((days - 1) * MINUTES_PER_DAY + ALL_DAY_ALARM_MINUTE)
    return tuple(alarms)


def _group_title(names: Sequence[str]) -> str:
    unique = sorted(set(names))
    if len(unique) == 1:
        return unique[0]
    return os.path.commonprefix(unique).rstrip(" (-–").strip() or unique[0]


def _span_events(rows: Sequence[ExamRow], attr: str, kind: str, label: str) -> List[CalendarEvent]:
    groups: Dict[Tuple[str, Tuple[Moment, ...]], List[ExamRow]] = {}
    for row in rows:
        moments = tuple(getattr(row, attr))
        if moments:
            groups.setdefault((row.code.strip(), moments), []).append(row)
    events = []
    for (_, moments), members in groups.items():
        name = _group_title([m.session_name for m in members])
        start, end = _all_day_span(moments)
        events.append(
            CalendarEvent(
                key="%s:%s" % (kind, name),
                title="%s · %s" % (name, label),
                start=start,
                end=end,
                all_day=True,
                url=members[0].url,
                alarms=_span_alarms(start, end),
            )
        )
    return events


def _exam_event(row: ExamRow, label: str, duration_minutes: int) -> CalendarEvent:
    moments = row.exam
    title = "%s · %s" % (row.session_name, label)
    key = "exam:%s" % row.session_name
    if len(moments) == 1 and moments[0].time is not None:
        start = moments[0].as_datetime()
        return CalendarEvent(
            key=key,
            title=title,
            start=start,
            end=start + timedelta(minutes=duration_minutes),
            all_day=False,
            url=row.url,
            alarms=(-7 * MINUTES_PER_DAY, -MINUTES_PER_DAY, -120),
        )
    start, end = _all_day_span(moments)
    day_before_morning = -MINUTES_PER_DAY + ALL_DAY_ALARM_MINUTE
    return CalendarEvent(
        key=key,
        title=title,
        start=start,
        end=end,
        all_day=True,
        url=row.url,
        alarms=(-7 * MINUTES_PER_DAY + ALL_DAY_ALARM_MINUTE, day_before_morning),
    )


def build_events(rows: Sequence[ExamRow], labels: Dict[str, str], exam_duration_minutes: int) -> List[CalendarEvent]:
    events: List[CalendarEvent] = []
    events += _span_events(rows, "application", "apply", labels["application"])
    events += _span_events(rows, "late_application", "late", labels["late_application"])
    events += [_exam_event(row, labels["exam"], exam_duration_minutes) for row in rows if row.exam]
    return sorted(events, key=lambda e: (e.start, e.key))


def upcoming(events: Iterable[CalendarEvent], today: date) -> List[CalendarEvent]:
    return [event for event in events if event.last_day >= today]
