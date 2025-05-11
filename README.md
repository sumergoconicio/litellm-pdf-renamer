# PROJECT_NAME

> **Short one-liner**: A concise description of what this project does and why it matters.

---

## Table of Contents

1. [About](#about)  
2. [Features](#features)  
3. [Getting Started](#getting-started)  
   - [Prerequisites](#prerequisites)  
   - [Installation](#installation)  
   - [Configuration](#configuration)  
4. [Usage](#usage)  
5. [License](#license)  

---

## About

litellm-pdf-renamer is a modular tool that uses LLMs to auto-rename PDFs and update their internal metadata for discoverability and archival reliability. After every rename, the PDF's internal metadata (author, title, pubdate) is also updated to match the inferred values, guaranteeing that filenames and metadata always remain in sync.

---

## Features

- ✅ **Automatic PDF renaming** – Uses LLMs to infer and rename PDFs by author, title, and publication date  
- ✅ **Metadata synchronization** – After renaming, PDF metadata is always updated to match the new filename (author/title/pubdate), ensuring archival integrity  
- ✅ **Prompt-editable** – Easily customize extraction logic via `prompt.txt`  
- ✅ **Provider-agnostic** – Works with Anthropic, OpenAI, and any litellm-supported model  
- ✅ **Batch processing** – Rename and tag entire directories at once  
- 🚧 **Feature C** – in progress  
- ❌ **Feature D** – planned

---

## Getting Started

### Prerequisites

List what the user needs before installing:

```bash
# e.g. Node.js, Python, Docker, etc.
brew install node@18
```

---

---

## Usage
```bash
python pdf_renamer.py <directory> --model <model-name> [--prompt prompt.txt]
```
- Example: OpenAI GPT-4 Turbo
  ```bash
  python pdf_renamer.py ./pdfs --model gpt-4-turbo --prompt prompt.txt
  ```
- Example: Anthropic Claude
  ```bash
  python pdf_renamer.py ./pdfs --model claude-3-haiku-20240307 --prompt prompt.txt
  ```

---

## Configuration
- **Prompt:** Edit `prompt.txt` to change the LLM instructions.
- **Model/Provider:** Any model supported by litellm can be used. Set API keys in `.env`.

---

## Extending
- The codebase is fully modular. All LLM logic is routed through `litellm` (see `llm_provider.py`).
- Ready for CLI or web UI (Flask/Gradio) integration.
- To add new LLMs, just update your model name and API key—no code changes needed.
Typical workflow would look like this.
- Step 1: ...
- Step 2: ...

---

## License

Distributed under the MIT License. See LICENSE for more information.