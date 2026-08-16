"""
NovaMS — i18n (Internationalization) Layer
────────────────────────────────────────────────────────────────────────────
Purely local, dictionary-based translation for fixed dashboard UI text
(nav labels, KPI titles, buttons, etc). NEVER calls an LLM. Loading a
language file is cheap and cached via st.cache_data, so switching
languages costs no API tokens at all.

Additive module — does not import or modify anything in app.py.
Add support for a new language by dropping languages/<code>.json next to
this file and adding one line to _SUPPORTED below.
"""

import json
import os
import streamlit as st

_LANG_DIR = os.path.join(os.path.dirname(__file__), "languages")

# Add new languages here — the whole system (dashboard + AI Analyst) picks
# them up automatically once languages/<code>.json exists.
_SUPPORTED = {
    "en": "English",
    "hi": "हिन्दी",
    "mr": "मराठी",
}
_FALLBACK_LANG = "en"
_SESSION_KEY = "_nova_lang"


@st.cache_data
def _load_lang_file(lang_code: str) -> dict:
    """Cached so repeat lookups within/between reruns cost ~0ms and 0 tokens."""
    path = os.path.join(_LANG_DIR, f"{lang_code}.json")
    if not os.path.exists(path):
        path = os.path.join(_LANG_DIR, f"{_FALLBACK_LANG}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def available_languages() -> dict:
    """{code: display_name} — used to populate the sidebar selector."""
    return dict(_SUPPORTED)


def get_language() -> str:
    """Current session language code. Defaults to English, persists for the
    session (Streamlit's session_state already survives reruns)."""
    return st.session_state.get(_SESSION_KEY, _FALLBACK_LANG)


def set_language(lang_code: str) -> None:
    """Sets the session language. Unsupported codes silently fall back to
    English per the 'unsupported language -> fallback to English' rule."""
    st.session_state[_SESSION_KEY] = lang_code if lang_code in _SUPPORTED else _FALLBACK_LANG


def t(key: str, **kwargs) -> str:
    """
    Translate one UI string key for the current session language.
    Falls back to the English string, then to the raw key, so a missing
    translation never crashes the page — it just shows English/the key.
    Supports simple {placeholder} formatting, e.g. t("data_trust_explain_prefix", score=87).
    """
    lang = get_language()
    strings = _load_lang_file(lang)
    fallback = _load_lang_file(_FALLBACK_LANG)
    text = strings.get(key, fallback.get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


def language_selector_sidebar(key: str = "_nova_lang_selector") -> str:
    """
    Drop-in sidebar widget. Renders a selectbox of supported languages and
    persists the choice to session_state for the rest of the session.
    Call this once near the top of the sidebar block in app.py — see
    MULTILINGUAL_INTEGRATION_GUIDE.md for the exact insertion point.
    Returns the selected language code.
    """
    codes = list(_SUPPORTED.keys())
    labels = list(_SUPPORTED.values())
    current = get_language()
    idx = codes.index(current) if current in codes else 0
    choice_label = st.selectbox(t("language_label"), labels, index=idx, key=key)
    chosen_code = codes[labels.index(choice_label)]
    set_language(chosen_code)
    return chosen_code
