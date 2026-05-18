#!/bin/bash
# translate.sh - Dịch ebook Anh → Việt với 1 lệnh duy nhất
# Usage: ./translate.sh <file.epub>
# Ví dụ: ./translate.sh "Atlas Shrugged by Ayn Rand.epub"

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <input.epub>"
    echo "Example: $0 'Atlas Shrugged by Ayn Rand.epub'"
    exit 1
fi

INPUT_FILE="$1"
INPUT_PATH="input/$INPUT_FILE"
LOG_FILE="translate_$(date +%Y%m%d_%H%M%S).log"

if [ ! -f "$INPUT_PATH" ]; then
    # fallback: maybe user passed full path or relative
    if [ -f "$INPUT_FILE" ]; then
        INPUT_PATH="$INPUT_FILE"
    else
        echo "Error: File not found: $INPUT_PATH"
        echo "Place your .epub file in the input/ directory."
        exit 1
    fi
fi

echo "=== Translation Started ===" | tee "$LOG_FILE"
echo "Input:  $INPUT_PATH" | tee -a "$LOG_FILE"
echo "Output: output/" | tee -a "$LOG_FILE"
echo "Log:    $LOG_FILE" | tee -a "$LOG_FILE"
echo "Start:  $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

source venv/bin/activate
export PYTHONPATH=src

nohup python3 -m ebook_gpt_translator translate "$INPUT_PATH" --overwrite \
    >> "$LOG_FILE" 2>&1 &

PID=$!
echo "PID: $PID" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "=== Translation running in background (PID=$PID) ==="
echo "Check progress: tail -f $LOG_FILE"
echo "Wait for completion: wait $PID"
echo "" | tee -a "$LOG_FILE"

# Save PID for progress.sh
echo "$PID" > .translate.pid
echo "$LOG_FILE" > .translate.log
