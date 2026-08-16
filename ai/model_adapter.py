"""
NovaMS — Model Adapter
────────────────────────────────────────────────────────────────────────────
Provider-agnostic wrapper around whichever LLM is powering the AI Analyst.
The dashboard and analytics engine never call an API directly — they call
ModelAdapter.complete(), so switching provider/model later means editing
this file only, nothing in app.py.

    Nova AI Analyst
          |
     ModelAdapter
      ├── claude       (Anthropic Messages API)
      ├── huggingface   (Hugging Face Inference API)
      └── local         (Ollama — fully offline)

Credentials are read from environment variables / st.secrets by the caller
and passed in; this module never hard-codes or logs a key.
"""

import os
import requests


class ModelAdapter:
    def __init__(self, provider: str = None, api_key: str = None, model: str = None):
        self.provider = (provider or os.environ.get("NOVA_MODEL_PROVIDER", "claude")).lower()
        self.api_key = api_key
        self.model = model

    def complete(self, system: str, messages: list, max_tokens: int = 1024) -> str:
        """messages: [{"role": "user"|"assistant", "content": str}, ...]"""
        try:
            if self.provider == "claude":
                return self._complete_claude(system, messages, max_tokens)
            if self.provider == "huggingface":
                return self._complete_huggingface(system, messages, max_tokens)
            if self.provider == "local":
                return self._complete_local(system, messages, max_tokens)
            return f"⚠️ Unknown model provider: '{self.provider}'."
        except Exception as e:
            # Never leak stack traces / credentials to the UI.
            return f"⚠️ AI Analyst is temporarily unavailable ({self.provider}). Please try again."

    # ── Claude (default / primary) ──────────────────────────────────────
    def _complete_claude(self, system, messages, max_tokens):
        if not self.api_key:
            return "⚠️ No Claude API key configured. Add one in the sidebar → BlinkBot AI Mode."
        headers = {
            "x-api-key": self.api_key.strip(),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model or "claude-sonnet-5",
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=45)
        if not r.ok:
            return f"⚠️ Claude API error ({r.status_code})."
        data = r.json()
        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")

    # ── Hugging Face (secondary / open-source models) ───────────────────
    def _complete_huggingface(self, system, messages, max_tokens):
        token = self.api_key or os.environ.get("HF_TOKEN", "")
        model = self.model or os.environ.get("HF_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
        if not token:
            return "⚠️ No Hugging Face token configured."
        prompt = system + "\n\n" + "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        r = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {token}"},
            json={"inputs": prompt, "parameters": {"max_new_tokens": max_tokens, "return_full_text": False}},
            timeout=60,
        )
        if not r.ok:
            return f"⚠️ Hugging Face API error ({r.status_code})."
        out = r.json()
        if isinstance(out, list) and out and "generated_text" in out[0]:
            return out[0]["generated_text"].strip()
        return str(out)

    # ── Local / Ollama (fully offline, zero token cost) ─────────────────
    def _complete_local(self, system, messages, max_tokens):
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        model = self.model or os.environ.get("OLLAMA_MODEL", "llama3")
        prompt = system + "\n\n" + "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        r = requests.post(
            f"{host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        if not r.ok:
            return f"⚠️ Local model error ({r.status_code}). Is Ollama running at {host}?"
        return r.json().get("response", "").strip()
