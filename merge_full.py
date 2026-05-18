#!/usr/bin/env python3
"""
Merge 3 worker EPUB outputs into one complete file.
Simple approach: extract all split_*.htm files from each worker in spine order.
"""
import zipfile
import os
import re
import shutil

BASE_DIR = "/root/ebook-GPT-translator"
OUTPUT_FILE = "Atlas Shrugged (Vietnamese).epub"
OUTPUT_PATH = os.path.join(BASE_DIR, OUTPUT_FILE)
TMP_DIR = os.path.join(BASE_DIR, "output_merged_tmp")

if os.path.exists(TMP_DIR):
    shutil.rmtree(TMP_DIR)

os.makedirs(os.path.join(TMP_DIR, "META-INF"), exist_ok=True)
os.makedirs(os.path.join(TMP_DIR, "EPUB"), exist_ok=True)

WORKERS = ["output_worker_1", "output_worker_2", "output_worker_3"]

# Step 1: Collect all .htm files from each worker in spine order
all_chapters = []  # (worker_index, internal_href, content)

for widx, wdir in enumerate(WORKERS):
    epub_path = os.path.join(BASE_DIR, wdir, "Atlas Shrugged by Ayn Rand.translated.epub")
    z = zipfile.ZipFile(epub_path, 'r')
    opf = z.read("EPUB/content.opf").decode('utf-8')
    
    # Get spine order (skip nav)
    spine_refs = re.findall(r'<itemref idref="([^"]+)"', opf)
    
    for ref in spine_refs:
        if ref in ('nav', 'ncx'):
            continue
        # Find href for this id
        m = re.search(rf'<item\s+href="([^"]+)"\s+id="{ref}"', opf)
        if not m:
            m = re.search(rf'id="{ref}"[^>]*href="([^"]+)"', opf)
        if m:
            href = m.group(1)
            if href.endswith('.htm'):
                content = z.read(f"EPUB/{href}").decode('utf-8')
                all_chapters.append((widx, href, content))
                print(f"  [{wdir}] {ref} -> {href} ({len(content)} bytes)")
    
    # Copy cover and style from first worker
    if widx == 0:
        for fname in z.namelist():
            if fname in ("mimetype",):
                continue
            bn = os.path.basename(fname)
            if bn in ("cover.jpeg", "style.css"):
                target_dir = os.path.dirname(fname)
                if target_dir == "EPUB/style":
                    os.makedirs(os.path.join(TMP_DIR, "EPUB", "style"), exist_ok=True)
                elif target_dir == "EPUB/style":
                    os.makedirs(os.path.join(TMP_DIR, "EPUB", "style"), exist_ok=True)
                dst = os.path.join(TMP_DIR, fname)
                with open(dst, 'wb') as f:
                    f.write(z.read(fname))
                print(f"  Copied: {fname}")
    
    z.close()

print(f"\n  Total chapters: {len(all_chapters)}")

if not all_chapters:
    print("  ERROR: No chapters collected!")
    exit(1)

# Step 2: Write all chapter files
for widx, href, content in all_chapters:
    outpath = os.path.join(TMP_DIR, "EPUB", href)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(content)

# Step 3: Write mimetype
with open(os.path.join(TMP_DIR, "mimetype"), 'wb') as f:
    f.write(b"application/epub+zip")

# Step 4: Write container.xml
container = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
with open(os.path.join(TMP_DIR, "META-INF", "container.xml"), 'w', encoding='utf-8') as f:
    f.write(container)

# Step 5: Extract titles for TOC from actual content
toc_entries = []
for widx, href, content in all_chapters:
    # Extract first h1/h2 text
    titles = re.findall(r'<h[12][^>]*>(.*?)</h[12]>', content, re.DOTALL)
    clean = []
    for t in titles:
        t2 = re.sub(r'<[^>]+>', '', t).strip()
        if t2:
            clean.append(t2)
    display = clean[0] if clean else href.replace('_split_', ' ').replace('.htm', '')
    
    # Clean up: skip empty or raw-English PART lines
    if 'PART' in display and 'PHẦN' not in display:
        # Use the content body to find the actual Vietnamese part title
        body = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
        if body:
            body_text = re.sub(r'<[^>]+>', '\n', body.group(1))
            for line in body_text.split('\n'):
                line = line.strip()
                if line and ('PHẦN' in line.upper() or 'CHƯƠNG' in line.upper()):
                    display = line
                    break
    
    toc_entries.append((href, display))
    print(f"  TOC: {href[:50]:50s} -> {display}")

# Step 6: Write nav.xhtml
nav_items = []
for href, title in toc_entries:
    nav_items.append(f'    <li><a href="{href}">{title}</a></li>')

nav = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>Mục Lục</title>
</head>
<body>
  <nav epub:type="toc">
    <h1>Mục Lục</h1>
    <ol>
{chr(10).join(nav_items)}
    </ol>
  </nav>
</body>
</html>'''

with open(os.path.join(TMP_DIR, "EPUB", "nav.xhtml"), 'w', encoding='utf-8') as f:
    f.write(nav)

# Step 7: Write toc.ncx
ncx_items = []
for i, (href, title) in enumerate(toc_entries, 1):
    ncx_items.append(f'''    <navPoint id="navpoint-{i}" playOrder="{i}">
      <navLabel>
        <text>{title}</text>
      </navLabel>
      <content src="{href}"/>
    </navPoint>''')

ncx_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="atlas-shrugged-vi"/>
    <meta name="dtb:depth" content="2"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>Atlas Shrugged</text>
  </docTitle>
  <navMap>
{chr(10).join(ncx_items)}
  </navMap>
</ncx>'''

with open(os.path.join(TMP_DIR, "EPUB", "toc.ncx"), 'w', encoding='utf-8') as f:
    f.write(ncx_xml)

# Step 8: Write content.opf
manifest_lines = []
spine_lines = []

# Cover
manifest_lines.append('    <item id="cover" href="cover.jpeg" media-type="image/jpeg"/>')

# Style
style_css_path = os.path.join(TMP_DIR, "EPUB", "style.css")
style_css_path2 = os.path.join(TMP_DIR, "EPUB", "style", "style.css")
if os.path.exists(style_css_path2):
    manifest_lines.append('    <item id="style" href="style/style.css" media-type="text/css"/>')
elif os.path.exists(style_css_path):
    manifest_lines.append('    <item id="style" href="style.css" media-type="text/css"/>')

# Content items
for href, title in toc_entries:
    item_id = href.replace(' ', '_').replace(',', '').replace('.htm', '')
    manifest_lines.append(f'    <item id="{item_id}" href="{href}" media-type="application/xhtml+xml"/>')
    spine_lines.append(f'    <itemref idref="{item_id}"/>')

# Nav
manifest_lines.append('    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
# NCX
manifest_lines.append('    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')

opf_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:identifier id="BookId">urn:uuid:atlas-shrugged-vi</dc:identifier>
    <dc:title>Atlas Shrugged</dc:title>
    <dc:creator>Ayn Rand</dc:creator>
    <dc:language>vi</dc:language>
    <dc:publisher>Hermes Agent Translation</dc:publisher>
    <meta property="dcterms:modified">2026-05-18T00:00:00Z</meta>
    <meta name="cover" content="cover"/>
  </metadata>
  <manifest>
{chr(10).join(manifest_lines)}
  </manifest>
  <spine toc="ncx">
{chr(10).join(spine_lines)}
  </spine>
  <guide>
    <reference href="cover.jpeg" type="cover" title="Cover"/>
    <reference href="nav.xhtml" type="toc" title="Mục Lục"/>
  </guide>
</package>'''

with open(os.path.join(TMP_DIR, "EPUB", "content.opf"), 'w', encoding='utf-8') as f:
    f.write(opf_xml)

# Step 9: Create final EPUB
if os.path.exists(OUTPUT_PATH):
    os.remove(OUTPUT_PATH)

with zipfile.ZipFile(OUTPUT_PATH, 'w', zipfile.ZIP_DEFLATED) as zout:
    for root, dirs, files in os.walk(TMP_DIR):
        for file in sorted(files):
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, TMP_DIR)
            if file == "mimetype":
                zout.write(file_path, arcname, compress_type=zipfile.ZIP_STORED)
            else:
                zout.write(file_path, arcname)

size = os.path.getsize(OUTPUT_PATH)
print(f"\n✅ Done! Created: {OUTPUT_FILE}")
print(f"  Size: {size:,} bytes")
print(f"  Chapters: {len(toc_entries)}")
print(f"  TOC entries: {len(nav_items)}")

# Verify structure
with zipfile.ZipFile(OUTPUT_PATH, 'r') as z:
    print(f"  Files in EPUB: {len(z.namelist())}")
    for n in sorted(z.namelist()):
        info = z.getinfo(n)
        print(f"    {n:50s} {info.file_size:>8,} bytes")

# Cleanup
shutil.rmtree(TMP_DIR)
print("  Temp dir cleaned")
