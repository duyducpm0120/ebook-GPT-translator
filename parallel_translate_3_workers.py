#!/usr/bin/env python3
"""
Parallel translation: split 35 chapters across 3 workers.

Chapter index mapping: EPUB index 1..35 are the actual chapters.
Worker 1: index 1-12  (12 chapters)
Worker 2: index 13-24 (12 chapters)
Worker 3: index 25-35 (11 chapters)
"""
import subprocess
import sys
import os
import time

EPUB = "input/Atlas Shrugged by Ayn Rand.epub"
VENV_PYTHON = os.path.join(os.path.dirname(__file__), "venv", "bin", "python3")
PROJECT_DIR = os.path.dirname(__file__)

SPLITS = [
    (1, 12, "output_worker_1"),
    (13, 24, "output_worker_2"),
    (25, 35, "output_worker_3"),
]

processes = []

for start, end, output_dir in SPLITS:
    cmd = [
        VENV_PYTHON, "-m", "ebook_gpt_translator", "translate",
        EPUB,
        "--start-chapter", str(start),
        "--end-chapter", str(end),
        "--overwrite",
        "--output-dir", output_dir,
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["PYTHONUNBUFFERED"] = "1"

    print(f"[{output_dir}] Chapters {start}-{end}: {' '.join(cmd)}")
    p = subprocess.Popen(cmd, cwd=PROJECT_DIR, env=env)
    processes.append((output_dir, start, end, p))
    time.sleep(0.5)  # stagger slightly to avoid IO contention

print(f"\nLaunched {len(processes)} workers. PIDs: {[p.pid for _, _, _, p in processes]}")
print("Waiting for all to complete...")

exit_codes = []
for output_dir, start, end, p in processes:
    p.wait()
    exit_codes.append((output_dir, start, end, p.returncode))
    print(f"[{output_dir}] Chapters {start}-{end} exited with code {p.returncode}")

all_ok = all(rc == 0 for _, _, _, rc in exit_codes)
if all_ok:
    print("\nAll workers completed successfully!")
else:
    print("\nSome workers failed:")
    for name, s, e, rc in exit_codes:
        status = "OK" if rc == 0 else f"FAILED (code {rc})"
        print(f"  {name} (ch {s}-{e}): {status}")
    sys.exit(1)
