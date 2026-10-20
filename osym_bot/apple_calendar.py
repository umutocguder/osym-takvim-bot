import subprocess
from datetime import datetime
from typing import Dict, List, Sequence

from .events import MARKER, CalendarEvent

COMMON = r'''
on makeDate(stamp)
    set dt to current date
    set day of dt to 1
    set year of dt to (text 1 thru 4 of stamp) as integer
    set month of dt to (text 6 thru 7 of stamp) as integer
    set day of dt to (text 9 thru 10 of stamp) as integer
    set hours of dt to (text 12 thru 13 of stamp) as integer
    set minutes of dt to (text 15 thru 16 of stamp) as integer
    set seconds of dt to 0
    return dt
end makeDate

on findCalendar(calName)
    tell application "Calendar"
        set matches to every calendar whose name is calName
        if (count of matches) is 0 then error "Calendar not found: " & calName number 1001
        if (count of matches) > 1 then error "Calendar name is not unique: " & calName number 1002
        return item 1 of matches
    end tell
end findCalendar
'''

LIST_SCRIPT = COMMON + r'''
on run argv
    set calName to item 1 of argv
    set markerPrefix to item 2 of argv
    set cal to my findCalendar(calName)
    set out to ""
    tell application "Calendar"
        repeat with ev in (every event of cal whose description contains markerPrefix)
            set out to out & (uid of ev) & tab & (paragraph 1 of (description of ev as text)) & linefeed
        end repeat
    end tell
    return out
end run
'''

CREATE_SCRIPT = COMMON + r'''
on run argv
    set calName to item 1 of argv
    set evTitle to item 2 of argv
    set startStamp to item 3 of argv
    set endStamp to item 4 of argv
    set isAllDay to (item 5 of argv) is "1"
    set evDescription to item 6 of argv
    set evUrl to item 7 of argv
    set alarmList to {}
    if (count of argv) > 7 then set alarmList to items 8 thru -1 of argv
    set cal to my findCalendar(calName)
    tell application "Calendar"
        set ev to make new event at end of events of cal with properties {summary:evTitle, start date:my makeDate(startStamp), end date:my makeDate(endStamp), allday event:isAllDay, description:evDescription, url:evUrl}
        repeat with offsetMinutes in alarmList
            tell ev to make new display alarm at end of display alarms with properties {trigger interval:(offsetMinutes as integer)}
        end repeat
        return uid of ev
    end tell
end run
'''

DELETE_SCRIPT = COMMON + r'''
on run argv
    set calName to item 1 of argv
    set evUid to item 2 of argv
    set cal to my findCalendar(calName)
    tell application "Calendar"
        delete (every event of cal whose uid is evUid)
    end tell
end run
'''


class CalendarError(RuntimeError):
    pass


def _stamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M")


def _run(script: str, args: Sequence[str]) -> str:
    result = subprocess.run(
        ["osascript", "-", *args],
        input=script,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        raise CalendarError(result.stderr.strip() or "osascript failed")
    return result.stdout


class AppleCalendar:
    def __init__(self, calendar_name: str):
        self.calendar_name = calendar_name

    def existing_markers(self) -> Dict[str, List[str]]:
        output = _run(LIST_SCRIPT, [self.calendar_name, MARKER + ":"])
        found: Dict[str, List[str]] = {}
        for line in output.splitlines():
            uid, _, marker = line.partition("\t")
            if uid and marker.startswith(MARKER + ":"):
                found.setdefault(marker.strip(), []).append(uid)
        return found

    def create(self, event: CalendarEvent, description: str) -> str:
        args = [
            self.calendar_name,
            event.title,
            _stamp(event.start),
            _stamp(event.end),
            "1" if event.all_day else "0",
            event.marker + "\n" + description,
            event.url,
            *[str(a) for a in event.alarms],
        ]
        return _run(CREATE_SCRIPT, args).strip()

    def delete(self, uid: str) -> None:
        _run(DELETE_SCRIPT, [self.calendar_name, uid])
