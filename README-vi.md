# ebook-GPT-translator — Bản Dịch Tiếng Việt 🇻🇳

Công cụ dịch ebook (EPUB, PDF, TXT, DOCX) từ tiếng Anh sang tiếng Việt với chất lượng văn học, sử dụng AI (OpenAI / OpenRouter / Claude Code / Gemini).

**Fork từ** [jesselau76/ebook-GPT-translator](https://github.com/jesselau76/ebook-GPT-translator) và được tùy chỉnh cho nhu cầu dịch tiểu thuyết Anh → Việt.

## Tính năng nổi bật

- Dịch EPUB, PDF, DOCX, TXT → output TXT + EPUB giữ nguyên định dạng
- Prompt dịch thuật văn học: giữ giọng văn, xử lý hội thoại, thành ngữ, ẩn dụ
- Tên riêng (nhân vật, địa danh) được giữ nguyên bản
- **Resume cache**: nếu bị gián đoạn, chạy lại sẽ tiếp tục từ chỗ dừng
- **Term memory**: thuật ngữ nhất quán xuyên suốt cuốn sách
- **Chapter memory**: ngữ cảnh giữa các chương không bị mất
- Hỗ trợ glossary (danh sách thuật ngữ cố định)
- Hỗ trợ nhiều provider: OpenAI, OpenRouter, Claude Code, Gemini, Codex

## Cài đặt nhanh

```bash
git clone https://github.com/duyducpm0120/ebook-GPT-translator.git
cd ebook-GPT-translator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Sử dụng

### 1. Tạo file cấu hình

```bash
cp settings.toml.example settings.toml
# Sau đó sửa settings.toml — điền API key của bạn
```

### 2. Dịch thử (test mode — chỉ dịch 3 block đầu)

```bash
PYTHONPATH=src python3 -m ebook_gpt_translator translate sach.epub \
  --test --test-limit 3
```

### 3. Dịch thật

```bash
PYTHONPATH=src python3 -m ebook_gpt_translator translate sach.epub
```

Kết quả nằm trong thư mục `output/`:
- `sach.translated.txt` — bản dịch dạng text
- `sach.translated.epub` — bản dịch dạng epub
- `.cache/jobs/sach.memory.json` — bộ nhớ dịch (để resume sau)

### 4. Dùng custom prompt cho văn phong tiểu thuyết

```bash
PYTHONPATH=src python3 -m ebook_gpt_translator translate sach.epub \
  --custom-prompt "$(cat novel_style_prompt.txt)"
```

### 5. Dùng OpenRouter (nhiều model)

```bash
PYTHONPATH=src python3 -m ebook_gpt_translator translate sach.epub \
  --provider compatible \
  --model "deepseek/deepseek-v4-chat" \
  --api-key "sk-or-v1-..." \
  --api-base-url "https://openrouter.ai/api/v1"
```

## Yêu cầu

- Python 3.10+
- API key (OpenAI / OpenRouter / Anthropic) hoặc CLI tool (Codex / Claude Code / Gemini)

## Cấu trúc project

```
ebook-GPT-translator/
├── src/ebook_gpt_translator/
│   ├── pipeline.py      # Core translation pipeline + system prompt
│   ├── providers.py     # Các provider (OpenAI, Codex, Claude, Gemini)
│   ├── config.py        # Cấu hình (default: Vietnamese)
│   ├── cli.py           # CLI interface
│   ├── documents.py     # Đọc/ghi EPUB, PDF, DOCX, TXT
│   ├── cache.py         # SQLite cache
│   ├── chunking.py      # Chia nhỏ văn bản
│   ├── glossary.py      # Xử lý glossary
│   ├── models.py        # Data models
│   └── gui.py           # Desktop GUI (optional)
├── settings.toml.example
├── novel_style_prompt.txt
└── output/
```

## So sánh với bản gốc

| Tính năng | Bản gốc | Bản này |
|-----------|---------|---------|
| Ngôn ngữ đích mặc định | Simplified Chinese | **Vietnamese** |
| System prompt | Dịch thuật chung | **Văn phong văn học Việt Nam** |
| Custom prompt mẫu | Không có | **novel_style_prompt.txt** |
| Settings mẫu | Chinese target | **EN→VI với OpenRouter** |
| Xử lý thành ngữ | Không đặc thù | **Tìm tương đương tiếng Việt** |
| Tên riêng | Có thể bị dịch | **Giữ nguyên bản** |
