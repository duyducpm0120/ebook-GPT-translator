#!/bin/bash
# progress.sh - Xem tiến độ dịch đang chạy
# Usage: ./progress.sh

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

PID_FILE=".translate.pid"
LOG_FILE=".translate.log"

if [ ! -f "$PID_FILE" ]; then
    echo "No translation process found."
    echo "Start one with: ./translate.sh <file.epub>"
    exit 1
fi

PID=$(cat "$PID_FILE" 2>/dev/null)
LOG=$(cat "$LOG_FILE" 2>/dev/null)

if [ -z "$PID" ] || ! kill -0 "$PID" 2>/dev/null; then
    echo "Translation process (PID=$PID) is NOT running."
    echo "Final log:"
    echo "---"
    tail -20 "$LOG" 2>/dev/null || echo "(no log)"
    rm -f "$PID_FILE" "$LOG_FILE"
    exit 1
fi

echo "=== Translation Status ==="
echo "PID:     $PID (RUNNING)"
echo "Log:     $LOG"
echo ""
echo "Latest output:"
echo "---"
tail -10 "$LOG" 2>/dev/null || echo "(empty - process starting...)"
echo ""
echo "---"
echo "Refresh: ./progress.sh"
echo "Watch:   tail -f $LOG"
echo "Stop:    kill $PID"
