"""
Title: Litellm Provider for PDF Renamer
Description: Provides a unified interface for all LLM providers/models via litellm, for extracting PDF metadata. Users select model/provider using litellm's standard API.
Author: ChAI-Engine (chaiji)
Last Updated: 2025-05-11
Dependencies: litellm, typing, re, json
Design Rationale: Centralizes all LLM calls through litellm; simplifies provider/model selection and future-proofs LLM integration.
"""

from typing import Dict, Optional
import re
import json

class LitellmProvider:
    """
    Purpose: Use litellm to call any supported LLM for PDF metadata extraction.
    Inputs: model (str), api_key (str), optional kwargs
    Outputs: Dict with keys 'author', 'title', 'pubdate' or None
    Role: Central LLM interface for the renamer pipeline.
    """
    def __init__(self, model: str, api_key: str, **kwargs):
        """
        Purpose: Initialize LitellmProvider with selected model and API key.
        Inputs: model (str), api_key (str), kwargs (dict)
        Outputs: None
        Role: Sets up LLM provider for subsequent metadata extraction.
        """
        import litellm
        self.litellm = litellm
        self.model = model
        self.api_key = api_key
        self.kwargs = kwargs

    def extract_metadata(self, prompt: str, extracted_text: str) -> Optional[Dict[str, str]]:
        """
        Purpose: Submit prompt and extracted text to LLM, parse and normalize output.
        Inputs: prompt (str), extracted_text (str)
        Outputs: Dict with keys 'author', 'title', 'pubdate' or None
        Role: Main LLM call for metadata extraction.
        """
        """
        Purpose: Submit prompt and extracted text to LLM, parse and normalize output.
        Inputs: prompt (str), extracted_text (str)
        Outputs: Dict with keys 'author', 'title', 'pubdate' or None
        Role: Main LLM call for metadata extraction.
        """
        try:
            response = self.litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": extracted_text},
                ],
                api_key=self.api_key,
                **self.kwargs
            )
            content = response['choices'][0]['message']['content']
            # Extract JSON from code block if present
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, flags=re.DOTALL)
            content = match.group(1) if match else content
            content = re.sub(r'^```(?:json)?', '', content.strip(), flags=re.IGNORECASE).strip()
            content = re.sub(r'```$', '', content.strip()).strip()
            content_match = re.search(r'\{.*\}', content, flags=re.DOTALL)
            if content_match:
                content = content_match.group(0)
            if '"' not in content:
                content = content.replace("'", '"')
            content = re.sub(r',\s*([}\]])', r'\1', content)
            guessed = json.loads(content)
            if (
                guessed.get("author", "").strip().lower() in {"unknown", "various"}
                or guessed.get("title", "").strip().lower() == "unknown"
                or not guessed.get("title", "").strip()
            ):
                return None
            return guessed
        except Exception as e:
            print(f"LitellmProvider error: {e}")
            return None

def get_llm_provider(model: str = None, **kwargs) -> 'LitellmProvider':
    """
    Purpose: Factory for LitellmProvider; encapsulates all provider/model/API key logic.
    Inputs: model (str, optional), kwargs (for future extensibility)
    Outputs: LitellmProvider instance
    Role: Centralizes all logic for LLM selection and secrets management. Main script is now fully agnostic.
    """
    """
    Purpose: Factory for LitellmProvider; encapsulates all provider/model/API key logic.
    Inputs: model (str, optional), kwargs (for future extensibility)
    Outputs: LitellmProvider instance
    Role: Centralizes all logic for LLM selection and secrets management. Main script is now fully agnostic.
    
    Model/provider mapping and API key selection:
      - If model is None, defaults to Anthropic Claude-3-Haiku (recommended for best results).
      - Supports: Anthropic (Claude), OpenAI (GPT-3/4), Gemini, Perplexity, Llama (local), etc.
      - Easily extensible: add new models/providers to the mappings below.
    """
    import os
    # Map models to providers
    MODEL_PROVIDER_MAP = {
        # Anthropic
        'claude-3-haiku-20240307': 'anthropic',
        'claude-3-sonnet-20240229': 'anthropic',
        'claude-3-opus-20240229': 'anthropic',
        # OpenAI
        'gpt-4-turbo': 'openai',
        'gpt-4': 'openai',
        'gpt-3.5-turbo': 'openai',
        # Gemini
        'gemini-pro': 'gemini',
        # Perplexity
        'pplx-70b-online': 'perplexity',
        # Llama (local)
        'llama-2-70b': 'llama',
    }
    # Map providers to envvar names
    PROVIDER_ENVVAR_MAP = {
        'anthropic': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'gemini': 'GEMINI_API_KEY',
        'perplexity': 'PERPLEXITY_API_KEY',
        'llama': 'LLAMA_API_KEY',  # for local models, can be a dummy
    }
    # Defaults
    DEFAULT_MODEL = 'claude-3-haiku-20240307'
    DEFAULT_PROVIDER = 'anthropic'
    # Select model
    selected_model = model or DEFAULT_MODEL
    provider = MODEL_PROVIDER_MAP.get(selected_model, DEFAULT_PROVIDER)
    envvar = PROVIDER_ENVVAR_MAP.get(provider)
    api_key = os.getenv(envvar)
    if not api_key:
        raise RuntimeError(f"API key for provider '{provider}' not found. Please set {envvar} in your environment or .env file.")
    return LitellmProvider(selected_model, api_key, **kwargs)
