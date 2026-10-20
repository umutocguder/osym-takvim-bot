#!/bin/bash
set -euo pipefail

LABEL="com.umut.osym-takvim-bot"
PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$(command -v python3)"
LOG="$HOME/Library/Logs/osym-takvim-bot.log"
TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"

sed -e "s|__PYTHON__|$PYTHON|g" -e "s|__PROJECT__|$PROJECT|g" -e "s|__LOG__|$LOG|g" \
    "$PROJECT/launchd/$LABEL.plist.template" > "$TARGET"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$TARGET"
echo "Installed $TARGET (runs on day 1 of every month at 10:00, log: $LOG)"

if [[ "${1:-}" == "--run-now" ]]; then
    launchctl kickstart -k "gui/$(id -u)/$LABEL"
    echo "Started one run now"
fi
