# AGENTS.md — ÖSYM Takvim Bot

## 1. Project Overview & Architecture
**ÖSYM Takvim Bot** is an autonomous macOS background bot developed by **11Hopem**. It scrapes the official ÖSYM exam calendar schedule ([osym.gov.tr/Sayfa/SinavTakvimi](https://www.osym.gov.tr/Sayfa/SinavTakvimi)) on a weekly schedule (every Monday 10:00), parses application deadlines, late application windows, and exam dates for configured exams (ALES, KPSS Lisans, YÖKDİL, YDS), and synchronizes them directly into macOS Calendar and Google Calendar via native AppleScript/JXA integration.

### Core Architecture
- **Language / Runtime:** Python 3.9+ (Zero external pip dependencies, standard library only).
- **Automation / Scheduler:** macOS `launchd` LaunchAgent (`com.umut.osym-takvim-bot`).
- **Data Flow:**
  1. `scraper.py`: Fetches official HTML via `/usr/bin/curl`, parses table rows and moments.
  2. `events.py`: Filters exams based on user criteria (`config.json`), groups joint application periods, and builds calendar events with smart reminder alarms.
  3. `apple_calendar.py`: Interfaces with macOS Calendar (`Calendar.app`) through `osascript` with unique marker hashes (`osym-bot:<key>#<hash>`) to guarantee idempotency and atomic updates.
  4. `telemetry/logger.py`: Enterprise dual-tier telemetry streaming with automated PII scrubbing (TCKN, credit cards, phones, bearer tokens) and non-blocking Cloud Firestore REST ingestion.
  5. `scripts/backup.py`: Autonomous SHA-256 verified snapshot backup engine.

---

## 2. Technology Stack & Commands
- **Language:** Python 3.12+
- **Test Framework:** Python standard library `unittest`
- **Automation:** macOS `launchd`
- **Cloud Infrastructure:** Firebase Ecosystem (`hopem-software-cloud` / Firestore REST)
- **Attribution:** [11Hopem](https://11hopem.com)

### Common Commands
- **Dry-Run Inspection:** `python3 -m osym_bot --dry-run`
- **Manual Sync:** `python3 -m osym_bot`
- **Run Automated Tests:** `python3 -m unittest discover tests`
- **Autonomous Backup:** `python3 scripts/backup.py`
- **Install Service:** `./scripts/install.sh`
- **Uninstall Service:** `./scripts/uninstall.sh`
- **View System Logs:** `tail -f ~/Library/Logs/osym-takvim-bot.log`

---

## 3. Strict Development & Confidentiality Rules
1. **Confidentiality & Isolation (Rule 1):** Strictly isolated personal project under `~/mycodespaces/osym-takvim-bot`. Never transfer company code or place company resources here.
2. **Commit Standard (Rule 2):** Commits must use `Umut Öçgüder <umutocgdr@gmail.com>`.
3. **100% English Code Standard (Rule 3):** All code, variables, functions, comments, logs, and tests must be in English. Turkish strings are permitted only in user-facing calendar event labels defined in `config.json`.
4. **Mandatory Automated Tests (Rule 8):** Zero untested code. All changes must pass tests with 100% success rate.
5. **Brand Identity (Rule 9 & 13):** Attribution strictly `11Hopem` with link `https://11hopem.com`. Dedicated SVG logo and favicon maintained in `assets/`.
6. **Telemetry & Zero-Crash (Rule 7 & 18):** Logging must stream sanitized structured events to Firestore REST API with zero-crash guarantee and local data custody.
