#!/usr/bin/env python3
"""
parallel_translate.py - Dịch song song nhiều chapter cùng lúc
Chia sách thành N phần bằng nhau, mỗi phần 1 process riêng.
Output: output_worker_1/, output_worker_2/, output_worker_3/
Sau đó cần merge: python3 merge_outputs.py
"""

import json, os, subprocess, sys, time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
INPUT_FILE = PROJECT_DIR / "input/Atlas Shrugged by Ayn Rand.epub"
VENV_PYTHON = str(PROJECT_DIR / "venv/bin/python3")
NUM_WORKERS = 3
os.chdir(PROJECT_DIR)
env = {**os.environ, "PYTHONPATH": str(PROJECT_DIR / "src")}

# 1. Analyze
result = subprocess.run(
    [VENV_PYTHON, "-c", f"""
import json, sys
sys.path.insert(0, '{PROJECT_DIR / "src"}')
from pathlib import Path
from ebook_gpt_translator.documents import load_document
from ebook_gpt_translator.config import AppConfig
config = AppConfig()
doc = load_document(Path('{INPUT_FILE}'), config)
chapters = []
for i, ch in enumerate(doc.chapters):
    text_blocks = sum(1 for b in ch.blocks if b.is_text and b.text.strip())
    chars = sum(len(b.text) for b in ch.blocks if b.is_text)
    if text_blocks >= 10:
        chapters.append({{'index': i, 'blocks': text_blocks, 'chars': chars, 'title': ch.title.strip()[:40]}})
print(json.dumps(chapters, ensure_ascii=False))
"""], capture_output=True, text=True, timeout=30, env=env
)
chapters = json.loads(result.stdout.strip())
print(f"=== Atlas Shrugged — Parallel Translation ===")
print(f"Total: {len(chapters)} chapters, {sum(c['chars'] for c in chapters):,} chars")

# 2. Load balance
chapters.sort(key=lambda c: c['chars'], reverse=True)
workers = [[] for _ in range(NUM_WORKERS)]
w_chars = [0] * NUM_WORKERS
for ch in chapters:
    idx = min(range(NUM_WORKERS), key=lambda i: w_chars[i])
    workers[idx].append(ch['index'])
    w_chars[idx] += ch['chars']

for i in range(NUM_WORKERS):
    idxs = sorted(workers[i])
    chs = [c for c in chapters if c['index'] in idxs]
    print(f"  Worker {i+1}: {len(idxs)} ch, {sum(c['chars'] for c in chs):,} chars, {sum(c['blocks'] for c in chs)} blocks")
    # Show first/last chapter title
    first = [c['title'] for c in chs if c['index'] == idxs[0]][0] if chs else '?'
    last = [c['title'] for c in chs if c['index'] == idxs[-1]][0] if chs else '?'
    print(f"    Range: [{idxs[0]}:{idxs[-1]+1}] \"{first}\" → \"{last}\"")

print()

# 3. Start workers
processes = []
for i in range(NUM_WORKERS):
    idxs = sorted(workers[i])
    start, end = idxs[0], idxs[-1] + 1
    log_file = PROJECT_DIR / f"worker_{i+1}.log"
    cmd = [VENV_PYTHON, "-m", "ebook_gpt_translator", "translate",
            str(INPUT_FILE), "--start-chapter", str(start), "--end-chapter", str(end),
            "--overwrite", "--output-dir", f"output_worker_{i+1}"]
    with open(log_file, "w") as lf:
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=PROJECT_DIR)
    processes.append((i+1, proc, log_file, start, end))
    print(f"  Worker {i+1} started (PID={proc.pid}, log=worker_{i+1}.log)")
    time.sleep(1.5)

print()
print("All workers started. Waiting for completion...")
print()

# 4. Wait + monitor with timeout per worker
start_time = time.time()
MAX_WAIT = 6 * 3600  # 6 hours max

for wid, proc, log_file, start_ch, end_ch in processes:
    while proc.poll() is None:
        elapsed = time.time() - start_time
        if elapsed > MAX_WAIT:
            print(f"  Worker {wid}: TIMEOUT after {elapsed/3600:.1f}h, killing...")
            proc.kill()
            break
        time.sleep(30)
        # Quick progress check
        lines = log_file.read_text().split('\n') if log_file.exists() else []
        last = [l for l in lines[-3:] if l.strip() and '━' not in l and '╭' not in l and '╰' not in l]
        print(f"  Worker {wid} ({elapsed/60:.0f}m): still running, last: {last[0][:100] if last else 'starting...'}")
    
    rc = proc.returncode if proc.poll() is not None else -1
    lines = log_file.read_text().split('\n') if log_file.exists() else []
    summary = [l for l in lines if 'Blocks:' in l or 'complete' in l or 'TXT:' in l or 'EPUB:' in l]
    print(f"  Worker {wid}: DONE (rc={rc})")
    for s in summary:
        print(f"    {s}")

print()
print("=" * 60)
print("ALL WORKERS COMPLETED!")
print(f"Total time: {(time.time() - start_time)/60:.1f} minutes")
print()
print("Output directories:")
for i in range(NUM_WORKERS):
    out_dir = PROJECT_DIR / f"output_worker_{i+1}"
    if out_dir.exists():
        for f in out_dir.iterdir():
            print(f"  {f} ({f.stat().st_size/1024/1024:.1f} MB)")
    else:
        print(f"  {out_dir}: NOT FOUND")
print()
print("Run: python3 merge_outputs.py")
