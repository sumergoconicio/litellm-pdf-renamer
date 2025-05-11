"""
Title: Modular PDF Renamer (LLM-agnostic)
Description: Renames PDFs in a directory using user-selected LLM (Anthropic, OpenAI, etc.) and prompt file. Extensible for CLI or web UI. Updates filenames and PDF metadata.
Author: ChAI-Engine (chaiji)
Last Updated: 2025-05-11
Dependencies: PyPDF2, anthropic, openai, python-dotenv, pathlib, typing
Design Rationale: Provider abstraction and prompt decoupling enable flexible, testable, and future-proof document workflows.
"""

import os
import re
import json
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv
from PyPDF2 import PdfReader, PdfWriter
import argparse

from llm_provider import get_llm_provider

# --- Prompt Loader ---
def load_prompt(prompt_path: Path) -> str:
    """
    Purpose: Load the LLM prompt from a file.
    Inputs: prompt_path (Path)
    Outputs: prompt string
    Role: Decouples prompt editing from code.
    """
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

# --- PDF Extraction ---
def extract_first_n_pages_text(pdf_path: Path, n: int = 5) -> Optional[str]:
    """
    Purpose: Extract text from the first n pages of a PDF.
    Inputs: pdf_path (Path), n (int)
    Outputs: Extracted text or None
    Role: Supplies raw text for LLM analysis.
    """
    try:
        reader = PdfReader(str(pdf_path))
        if not reader.pages:
            return None
        num_pages = min(len(reader.pages), n)
        texts = []
        for i in range(num_pages):
            page_text = reader.pages[i].extract_text()
            if page_text:
                texts.append(page_text.strip())
        return "\n\n".join(texts) if texts else None
    except Exception as e:
        print(f"[ERROR] Failed to extract from {pdf_path.name}: {e}")
        return None
    """
    Purpose: Extract text from the first n pages of a PDF.
    Inputs: pdf_path (Path), n (int)
    Outputs: Extracted text or None
    Role: Supplies raw text for LLM analysis.
    """
    try:
        reader = PdfReader(str(pdf_path))
        if not reader.pages:
            return None
        num_pages = min(len(reader.pages), n)
        texts = []
        for i in range(num_pages):
            page_text = reader.pages[i].extract_text()
            if page_text:
                texts.append(page_text.strip())
        return "\n\n".join(texts) if texts else None
    except Exception as e:
        print(f"Failed to extract from {pdf_path.name}: {e}")
        return None

# --- Filename Sanitization ---
def sanitize_filename(raw: str, limit: int = 200) -> str:
    """
    Purpose: Remove forbidden/special chars, normalize whitespace, and ensure candidate filename is safe & not too long.
    Inputs: raw (str), limit (int)
    Outputs: cleaned, truncated string
    Role: Prevents OS errors, improves human readability in filenames.
    """
    cleaned = re.sub(r"[^\w\s\(\)\-\&]", "", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:limit]

# --- Destination Path Generation ---
def make_destination_path(base_dir: Path, proposed: str) -> Path:
    """
    Purpose: Given a directory and candidate filename, return a unique, absolute Path that doesn't overwrite existing files.
    Inputs: base_dir (Path), proposed (str)
    Outputs: Path object
    Role: File system collision avoidance, multi-run safety.
    """
    base_name = proposed
    if not base_name.lower().endswith(".pdf"):
        base_name += ".pdf"
    candidate = base_dir / base_name
    counter = 1
    while candidate.exists():
        stem, ext = os.path.splitext(base_name)
        candidate = base_dir / f"{stem}_{counter}{ext}"
        counter += 1
    return candidate

# --- PDF Metadata Update ---
def update_and_save_pdf_metadata(src_pdf: Path, dest_pdf: Path, author: str, title: str, date_str: str) -> bool:
    """
    Purpose: Copy PDF, update XMP/document metadata, save as dest_pdf.
    Inputs: src_pdf (Path), dest_pdf (Path), author/title/date_str (str)
    Outputs: True if successful, False on failure
    Role: Ensures both correct filename and internal PDF metadata for archival integrity.
    """
    try:
        reader = PdfReader(str(src_pdf))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        year_candidate = str(date_str)
        metadata = {
            "/Author": author,
            "/Title": title,
            "/CreationDate": f"D:{year_candidate}0101000000Z"
        }
        writer.add_metadata(metadata)
        temp_path = dest_pdf.parent / (dest_pdf.name + ".tmp")
        with open(temp_path, "wb") as out_f:
            writer.write(out_f)
        temp_path.replace(dest_pdf)
        return True
    except Exception as e:
        print(f"Error updating/writing PDF ({src_pdf.name}): {e}")
        return False

# --- Single PDF Processing ---
def process_single_pdf(pdf_path: Path, llm, prompt: str, n_pages: int = 5) -> Optional[Path]:
    """
    Purpose: For a single PDF, extract, AI-infer metadata, attempt rename and metadata write.
    Inputs: pdf_path (Path), llm (LLMProvider), prompt (str), n_pages (int)
    Outputs: Path to new PDF file on success (or original path if unchanged/fail)
    Role: Unit of work for workflow; enables granular testing and extension.
    """
    extracted = extract_first_n_pages_text(pdf_path, n=n_pages)
    if not extracted:
        print(f"[SKIP] {pdf_path.name}: no text found.")
        return pdf_path
    guessed = llm.extract_metadata(prompt, extracted)
    if not guessed:
        print(f"[SKIP] {pdf_path.name}: LLM metadata guess failed or unreliable.")
        return pdf_path
    candidate_name = f"{guessed['author']} - {guessed['title']} ({guessed['pubdate']})"
    clean_file = sanitize_filename(candidate_name)
    new_path = make_destination_path(pdf_path.parent, clean_file)
    # First, copy and update metadata as part of the rename process
    if update_and_save_pdf_metadata(pdf_path, new_path, sanitize_filename(guessed['author']), sanitize_filename(guessed['title']), guessed['pubdate']):
        pdf_path.unlink(missing_ok=True)
        # After renaming, ensure the metadata on the new file is refreshed (in case of further renames or edits)
        update_and_save_pdf_metadata(new_path, new_path, sanitize_filename(guessed['author']), sanitize_filename(guessed['title']), guessed['pubdate'])
        print(f"[RENAME] '{pdf_path.name}' -> '{new_path.name}' (metadata updated)")
        return new_path
    else:
        print(f"[FAIL] '{pdf_path.name}': metadata/write error.")
        return pdf_path
    """
    Purpose: For a single PDF, extract, AI-infer metadata, attempt rename and metadata write.
    Inputs: pdf_path (Path), llm (LLMProvider), prompt (str)
    Outputs: Path to new PDF file on success (or original path if unchanged/fail)
    Role: Unit of work for workflow; enables granular testing and extension.
    """
    extracted = extract_first_n_pages_text(pdf_path, n=10)
    if not extracted:
        print(f"Skipping {pdf_path.name}: no text found.")
        return pdf_path
    guessed = llm.extract_metadata(prompt, extracted)
    if not guessed:
        print(f"Skipping {pdf_path.name}: LLM metadata guess failed or unreliable.")
        return pdf_path
    candidate_name = f"{guessed['author']} - {guessed['title']} ({guessed['pubdate']})"
    clean_file = sanitize_filename(candidate_name)
    new_path = make_destination_path(pdf_path.parent, clean_file)
    if update_and_save_pdf_metadata(pdf_path, new_path, sanitize_filename(guessed['author']), sanitize_filename(guessed['title']), guessed['pubdate']):
        pdf_path.unlink(missing_ok=True)
        print(f"Renamed '{pdf_path.name}' → '{new_path.name}'")
        return new_path
    else:
        print(f"Failed to process '{pdf_path.name}': metadata/write error.")
        return pdf_path

# --- Directory Batch Processing ---
def process_pdf_directory(directory: Path, llm, prompt: str, n_pages: int = 5):
    """
    Purpose: For all PDFs in directory, apply process_single_pdf() in sorted, recent-first order.
    Inputs: directory (Path), llm (LLMProvider), prompt (str), n_pages (int)
    Outputs: None (prints progress)
    Role: Batch driver for workflow; entrypoint for CLI, scripting, or extension.
    """
    pdfs = sorted((f for f in directory.iterdir() if f.suffix.lower() == ".pdf" and f.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)
    for pdf_path in pdfs:
        process_single_pdf(pdf_path, llm, prompt, n_pages=n_pages)
    print("[DONE] Finished processing all PDFs!")
    """
    Purpose: For all PDFs in directory, apply process_single_pdf() in sorted, recent-first order.
    Inputs: directory (Path), llm (LLMProvider), prompt (str)
    Outputs: None (prints progress)
    Role: Batch driver for workflow; entrypoint for CLI, scripting, or extension.
    """
    pdfs = sorted((f for f in directory.iterdir() if f.suffix.lower() == ".pdf" and f.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)
    for pdf_path in pdfs:
        process_single_pdf(pdf_path, llm, prompt)
    print("Finished processing all PDFs!")

# --- Main Entrypoint ---
def main():
    """
    Purpose: CLI entrypoint; loads config, provider, prompt, and processes directory.
    Inputs: CLI args or env vars
    Outputs: None
    Role: End-to-end orchestration; ready for CLI or web UI.
    """
    DEFAULT_PROVIDER = "anthropic"
    DEFAULT_MODEL = None
    DEFAULT_PROMPT = "prompt.txt"
    DEFAULT_N_PAGES = 5

    parser = argparse.ArgumentParser(description="Modular PDF Renamer (LLM-agnostic)")
    parser.add_argument("directory", nargs="?", help="Directory with PDFs to process")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, help="LLM provider: anthropic or openai")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name (if applicable)")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Prompt file path")
    parser.add_argument("--pages", type=int, default=DEFAULT_N_PAGES, help="Number of pages to extract per PDF (default: 5)")
    args = parser.parse_args()

    load_dotenv()
    directory = Path(args.directory) if args.directory else Path(input("Enter directory with PDFs: ")).expanduser().resolve()
    if not directory.is_dir():
        print(f"[ERROR] Invalid directory: {directory}")
        return
    prompt_path = Path(args.prompt)
    if not prompt_path.is_file():
        print(f"[ERROR] Prompt file not found: {prompt_path}")
        return
    prompt = load_prompt(prompt_path)
    llm = get_llm_provider(model=args.model)
    process_pdf_directory(directory, llm, prompt, n_pages=args.pages)
    """
    Purpose: CLI entrypoint; loads config, provider, prompt, and processes directory.
    Inputs: CLI args or env vars
    Outputs: None
    Role: End-to-end orchestration; ready for CLI or web UI.
    """
    parser = argparse.ArgumentParser(description="Modular PDF Renamer (LLM-agnostic)")
    parser.add_argument("directory", nargs="?", help="Directory with PDFs to process")
    parser.add_argument("--provider", default="anthropic", help="LLM provider: anthropic or openai")
    parser.add_argument("--model", default=None, help="Model name (if applicable)")
    parser.add_argument("--prompt", default="prompt.txt", help="Prompt file path")
    args = parser.parse_args()

    load_dotenv()
    directory = Path(args.directory) if args.directory else Path(input("Enter directory with PDFs: ")).expanduser().resolve()
    if not directory.is_dir():
        print(f"Invalid directory: {directory}")
        return
    prompt_path = Path(args.prompt)
    if not prompt_path.is_file():
        print(f"Prompt file not found: {prompt_path}")
        return
    prompt = load_prompt(prompt_path)
    # Provider/model selection and API key logic are fully encapsulated in llm_provider.py
    # Only pass CLI args (model, etc.) to get_llm_provider; main script is now provider-agnostic
    llm = get_llm_provider(model=args.model)
    process_pdf_directory(directory, llm, prompt)

if __name__ == "__main__":
    main()
