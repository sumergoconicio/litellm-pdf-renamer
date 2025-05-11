# litellm-pdf-renamer

> Modular, LLM-powered PDF renamer: batch-renames PDFs and updates their internal metadata (author, title, pubdate) using AI-inferred bibliographic details. Ensures filenames and metadata are always in sync for robust archival search and retrieval.

---

## Table of Contents

1. [About](#about)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [License](#license)

---

## About

litellm-pdf-renamer uses large language models (LLMs) to:
- Extract bibliographic metadata (author, title, pubdate) from the first pages of each PDF
- Rename files and update their internal metadata accordingly
- Guarantee that filenames and PDF metadata are always synchronized, even after repeated or batch renames

Designed for CLI batch processing, prompt customization, and easy extension to new LLMs/providers.

---

## Features

- ✅ **AI-powered renaming**: Uses LLMs to infer author, title, and publication date for each PDF
- ✅ **Metadata synchronization**: After renaming, PDF metadata is always updated to match the filename (author/title/pubdate)
- ✅ **Batch processing**: Rename and tag all PDFs in a directory in one command
- ✅ **Prompt-editable**: Change extraction logic by editing `prompt.txt`
- ✅ **Provider-agnostic**: Works with Anthropic, OpenAI, Gemini, Perplexity, Llama, and any litellm-supported model
- ✅ **Extensible**: Modular CLI, ready for web UI or new LLMs

---

## Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/yourusername/litellm-pdf-renamer.git
   cd litellm-pdf-renamer
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

- **Prompt:** Edit `prompt.txt` to tune LLM extraction instructions
- **Model/Provider:** Any model supported by litellm; set API keys in `.env` (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)

---

## Usage

Basic usage:
```bash
python pdf_renamer.py <directory> --model <model-name> [--prompt prompt.txt]
```

Examples:
- OpenAI GPT-4 Turbo:
  ```bash
  python pdf_renamer.py ./sandbox --model gpt-4-turbo --prompt prompt.txt
  ```
- Anthropic Claude:
  ```bash
  python pdf_renamer.py ./sandbox --model claude-3-haiku-20240307 --prompt prompt.txt
  ```

After running, all PDFs in the target directory will be renamed and their internal metadata updated to match the inferred author, title, and publication date.

---

## License

Distributed under the MIT License. See LICENSE for more information.