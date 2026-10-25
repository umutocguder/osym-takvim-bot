<!-- Created by 11Hopem -->
# 🗓️ OSYM Calendar Sync Bot

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://apple.com)
[![Zero Dependency](https://img.shields.io/badge/dependencies-zero%20external-brightgreen.svg)](#architecture)
[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](https://11hopem.com)
[![Created by 11Hopem](https://img.shields.io/badge/created%20by-11Hopem-orange.svg)](https://11hopem.com)

An autonomous, zero-dependency background automation bot for macOS that scrapes the official Turkish Student Selection and Placement Center (ÖSYM) examination schedule and automatically synchronizes exam dates, application windows, and late submission deadlines directly into Apple Calendar and synced Google Calendars.

---

## 🌟 Key Features

- **Zero Third-Party Dependencies**: Built entirely using Python's standard library (`urllib`, `html.parser`, `sqlite3`, `json`) and macOS native automation (`osascript` / Apple Events).
- **Automated Scraping & Parsing**: Scrapes and parses official tables from `osym.gov.tr`, extracting Exam Names, Application Windows, Late Application Dates, Exam Days, and Result Announcement dates.
- **Bi-Directional Calendar Sync**: Creates native macOS Calendar events with alarms, reminders, and automatic cloud propagation to connected Google or iCloud accounts.
- **Idempotent Updates**: Maintains a local state ledger to avoid duplicate calendar events and updates changed dates seamlessly.
- **macOS `launchd` Daemon**: Includes a pre-configured `launchd` plist to run periodically (e.g. every Monday at 10:00 AM) without user intervention.

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│     osym.gov.tr Portal          │
│   Official HTML Exam Tables     │
└────────────────┬────────────────┘
                 │ HTTP GET (Standard Library)
                 ▼
┌─────────────────────────────────┐
│     OSYM Parser & Scraper       │
│  Extract dates, deadlines, keys │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     Sync & Diff Engine          │
│  State Ledger / SHA-256 Ledger  │
└────────────────┬────────────────┘
                 │ AppleScript (osascript)
                 ▼
┌─────────────────────────────────┐
│     macOS Calendar (Events)     │
│   Synced to Google / iCloud     │
└─────────────────────────────────┘
```

---

## 🚀 Quickstart & Usage

### Prerequisites

- macOS 12+ (Monterey, Ventura, Sonoma, Sequoia)
- Python 3.9 or higher

### 1. Clone Repository

```bash
git clone https://github.com/umutocguder/osym-takvim-bot.git
cd osym-takvim-bot
```

### 2. Run Manually

To fetch the latest schedule and preview matching exams:

```bash
python3 -m osym_bot.main --dry-run
```

To execute a live sync to your default Calendar:

```bash
python3 -m osym_bot.main
```

### 3. Automated Scheduling (`launchd`)

Install the macOS background agent to run weekly:

```bash
bash scripts/install_daemon.sh
```

To stop or uninstall:

```bash
launchctl unload ~/Library/LaunchAgents/com.11hopem.osym-bot.plist
```

---

## 🧪 Testing

Run the automated test suite:

```bash
python3 -m unittest discover -s tests
```

---

## 🛡️ License & Attribution

Created by [11Hopem](https://11hopem.com).  
Copyright © 2026 11Hopem. All rights reserved.  
Official website: [https://11hopem.com](https://11hopem.com)
