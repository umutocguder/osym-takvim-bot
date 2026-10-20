# Created by 11Hopem
# Copyright (c) 2026 11Hopem. All rights reserved.
# Licensed under 11Hopem Proprietary License.

import html
import re
import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional, Tuple

CALENDAR_URL = "https://www.osym.gov.tr/Sayfa/SinavTakvimi"
BASE_URL = "https://www.osym.gov.tr"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) osym-takvim-bot/1.0"

ROW_RE = re.compile(r'<tr class="st-takvim-list-row"(.*?)</tr>', re.S)
ATTR_RE = re.compile(r'data-([a-z-]+)="([^"]*)"')
CELL_RE = re.compile(r'<td data-label="([^"]*)"[^>]*>(.*?)</td>', re.S)
LINK_RE = re.compile(r'<a href="([^"]+)"')
DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})(?:\s+(\d{2}):(\d{2}))?")

LABEL_NAME = "Sınav Adı"
LABEL_APPLICATION = "Başvuru Tarihi"
LABEL_LATE_APPLICATION = "Geç Başvuru Tarihi"
LABEL_EXAM = "Sınav Tarihi"


class ScrapeError(RuntimeError):
    pass


@dataclass(frozen=True)
class Moment:
    day: date
    time: Optional[Tuple[int, int]] = None

    def as_datetime(self) -> datetime:
        hour, minute = self.time or (0, 0)
        return datetime(self.day.year, self.day.month, self.day.day, hour, minute)


@dataclass
class ExamRow:
    code: str
    year: int
    list_type: str
    long_name: str
    session_name: str
    url: str
    application: List[Moment] = field(default_factory=list)
    late_application: List[Moment] = field(default_factory=list)
    exam: List[Moment] = field(default_factory=list)


def fetch_calendar_html(url: str = CALENDAR_URL, timeout: int = 60) -> str:
    result = subprocess.run(
        ["/usr/bin/curl", "--silent", "--show-error", "--fail", "--location", "--max-time", str(timeout), "--user-agent", USER_AGENT, url],
        capture_output=True,
    )
    if result.returncode != 0:
        raise ScrapeError("Download failed: %s" % result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout.decode("utf-8", errors="replace")


def _strip_tags(fragment: str) -> str:
    text = re.sub(r"<br\s*/?>", " | ", fragment)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _div_text(fragment: str, css_class: str) -> str:
    match = re.search(r'<div class="%s">(.*?)</div>' % re.escape(css_class), fragment, re.S)
    return _strip_tags(match.group(1)) if match else ""


def parse_moments(text: str) -> List[Moment]:
    moments = []
    for d, m, y, hh, mm in DATE_RE.findall(text):
        time = (int(hh), int(mm)) if hh else None
        moments.append(Moment(date(int(y), int(m), int(d)), time))
    return moments


def parse_calendar(page: str) -> List[ExamRow]:
    rows = []
    for raw in ROW_RE.findall(page):
        head, _, body = raw.partition(">")
        attrs = {k: html.unescape(v).strip() for k, v in ATTR_RE.findall(head)}
        cells = {html.unescape(k): v for k, v in CELL_RE.findall(body)}
        name_cell = cells.get(LABEL_NAME, "")
        link = LINK_RE.search(name_cell)
        rows.append(
            ExamRow(
                code=attrs.get("sinavad", ""),
                year=int(attrs.get("yil", "0") or 0),
                list_type=attrs.get("liste-tur", ""),
                long_name=_div_text(name_cell, "st-takvim-list-uzun"),
                session_name=_div_text(name_cell, "st-takvim-list-sinav-adi"),
                url=BASE_URL + link.group(1) if link and link.group(1).startswith("/") else (link.group(1) if link else CALENDAR_URL),
                application=parse_moments(_strip_tags(cells.get(LABEL_APPLICATION, ""))),
                late_application=parse_moments(_strip_tags(cells.get(LABEL_LATE_APPLICATION, ""))),
                exam=parse_moments(_strip_tags(cells.get(LABEL_EXAM, ""))),
            )
        )
    if not rows:
        raise ScrapeError("No calendar rows found; the OSYM page layout may have changed")
    return rows
