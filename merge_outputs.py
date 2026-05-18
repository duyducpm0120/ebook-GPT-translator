#!/usr/bin/env python3
"""
merge_outputs.py - Ghép output từ 3 workers thành file hoàn chỉnh
"""

import json
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
NUM_WORKERS = 3

# 1. Merge JSON memory states
print("=== Merging worker outputs ===")

input_epub = PROJECT_DIR / "input/Atlas Shrugged by Ayn Rand.epub"

# 2. Read all chapters from original epub
import sys
sys.path.insert(0, str(PROJECT_DIR / "src"))
os.chdir(PROJECT_DIR)

from ebook_gpt_translator.documents import load_document
from ebook_gpt_translator.config import AppConfig

config = AppConfig()
doc = load_document(input_epub, config)

# 3. Load each worker's output and map translated blocks
print("Loading worker outputs...")
for i in range(NUM_WORKERS):
    out_dir = PROJECT_DIR / f"output_worker_{i+1}"
    memory_file = PROJECT_DIR / f".cache/jobs/Atlas_Shrugged_by_Ayn_Rand.memory.json"
    
    if not out_dir.exists():
        print(f"  Worker {i+1}: no output directory")
        continue
    
    # Try to load memory state to get block translations
    if memory_file.exists():
        memory = json.loads(memory_file.read_text(encoding='utf-8'))
        block_translations = memory.get('block_translations', {})
        print(f"  Worker {i+1}: {len(block_translations)} translated blocks from memory")
        
        # Map to document
        count = 0
        for ch in doc.chapters:
            for block in ch.blocks:
                if block.block_id in block_translations:
                    block.translated_text = block_translations[block.block_id]
                    count += 1
        print(f"    Mapped {count} blocks")

# 4. Write merged output
output_dir = PROJECT_DIR / "output"
output_dir.mkdir(exist_ok=True)

from ebook_gpt_translator.documents import write_outputs

txt_path, epub_path = write_outputs(doc, config)
print(f"\nMerged output:")
print(f"  TXT:  {txt_path}")
print(f"  EPUB: {epub_path}")

# Stats
total = sum(1 for ch in doc.chapters for b in ch.blocks if b.is_text and b.text.strip())
translated = sum(1 for ch in doc.chapters for b in ch.blocks if b.translated_text)
print(f"  Blocks: {translated}/{total} translated")
