"""
NovaMS — Multilingual AI Analyst Layer
────────────────────────────────────────────────────────────────────────────
Sits between app.py's existing AI Analyst page and the LLM. Adds language
awareness WITHOUT touching Nova's Data Engine, calculations, or the rule-
based BlinkBot handlers — those keep computing real numbers exactly as
before; this module only affects (a) which language the LLM is asked to
answer in, and (b) which fixed suggested-question chips are shown.

    User Question
         |
    Selected Language (i18n.get_language)
         |
    Nova AI Analyst  ─── analytics results already computed by app.py ───┐
         |                                                               |
    build_multilingual_system_prompt()  (adds ONE instruction paragraph) |
         |                                                               |
    ModelAdapter.complete()  ── cached per (question, language) ─────────┘
         |
    Response in selected language
         |
    Dashboard

No raw dataset rows are ever sent here — only the compact KPI/context
string app.py's _build_llm_system_prompt() already builds.
"""

import hashlib
import streamlit as st

from i18n import get_language, t

# Only the language *instruction* changes per request — everything else in
# the system prompt (KPIs, top products, etc.) is built once by app.py's
# existing _build_llm_system_prompt() and passed in unchanged, so no extra
# tokens are spent per language.
_LANG_INSTRUCTION = {
    "en": "Respond in clear, professional English.",
    "hi": (
        "उत्तर हिंदी में दें। संख्याएँ और ज़रूरी तकनीकी शब्द (जैसे Revenue, Profit, "
        "Margin, Data Trust, KPI) अंग्रेज़ी में ही रख सकते हैं जहाँ स्वाभाविक लगे। "
        "अगर सवाल स्पष्ट न हो तो अंदाज़ा न लगाएँ — विनम्रता से दोबारा पूछने को कहें।"
    ),
    "mr": (
        "उत्तर मराठीत द्या. संख्या आणि आवश्यक तांत्रिक शब्द (उदा. Revenue, Profit, "
        "Margin, Data Trust, KPI) योग्य वाटल्यास इंग्रजीत ठेवू शकता. "
        "प्रश्न अस्पष्ट असल्यास अंदाज लावू नका — नम्रपणे प्रश्न पुन्हा विचारायला सांगा."
    ),
}

# Same three questions as the English defaults already in app.py's
# render_ai_analyst(), translated — swap the QUICK_BASE list there for
# get_suggested_questions() to make the chips language-aware.
_SUGGESTED_QUESTIONS = {
    "en": [
        ("📉 Why revenue dropped", "Why did revenue decrease?"),
        ("🏙️ Top cities", "Show the top-performing cities."),
        ("🔮 Forecast", "Forecast next month."),
    ],
    "hi": [
        ("📉 राजस्व क्यों घटा", "राजस्व क्यों कम हुआ?"),
        ("🏙️ सर्वश्रेष्ठ शहर", "सबसे अच्छा प्रदर्शन करने वाले शहर दिखाएं।"),
        ("🔮 पूर्वानुमान", "अगले महीने का पूर्वानुमान बताएं।"),
    ],
    "mr": [
        ("📉 महसूल का घटला", "महसूल का कमी झाला?"),
        ("🏙️ सर्वोत्तम शहरे", "सर्वाधिक कामगिरी करणारी शहरे दाखवा."),
        ("🔮 अंदाज", "पुढील महिन्याचा अंदाज सांगा."),
    ],
}


def build_multilingual_system_prompt(base_system_prompt: str) -> str:
    """
    Wraps app.py's existing _build_llm_system_prompt() output with one
    language instruction paragraph. Call this right before _call_claude_stream
    (or ModelAdapter.complete) — nothing else about the prompt changes.
    """
    lang = get_language()
    instruction = _LANG_INSTRUCTION.get(lang, _LANG_INSTRUCTION["en"])
    return (
        base_system_prompt
        + "\n\n## RESPONSE LANGUAGE\n"
        + instruction
        + "\nNEVER invent numbers to sound fluent in this language — every figure must still come "
          "from the LIVE DATA SNAPSHOT above."
    )


def get_suggested_questions() -> list[tuple[str, str]]:
    """[(button_label, question_text), ...] for the current language."""
    return _SUGGESTED_QUESTIONS.get(get_language(), _SUGGESTED_QUESTIONS["en"])


def data_trust_explanation(score: int, status: str, main_issue: str) -> str:
    """
    Builds the Data Trust sentence in the selected language using ONLY the
    local dictionary (no LLM call) — the score/status/issue text itself
    still comes from Nova's real compute_trust_score(), never from an LLM.
    Mirrors the spec's example:
      EN: "Data Trust Score is 87/100. Missing values are the main issue."
      HI: "डेटा ट्रस्ट स्कोर 87/100 है। Missing values मुख्य समस्या हैं।"
    """
    prefix = t("data_trust_explain_prefix", score=score)
    issue_label = t("data_trust_main_issue_label")
    return f"{prefix} {issue_label}: {main_issue}"


def _cache_key(question: str, lang: str, dataset_signature: str) -> str:
    raw = f"{lang}:{dataset_signature}:{question.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def cached_llm_answer(question: str, base_system_prompt: str, messages: list,
                       adapter, dataset_signature: str = "", max_tokens: int = 1024) -> str:
    """
    Token-efficient entry point for a natural-language analytical question:
      1. Checks an in-session cache keyed on (question, language, dataset).
      2. On a miss, builds the language-aware prompt and calls the model
         ONCE via the configured ModelAdapter (Claude / HF / local).
      3. Caches successful answers so identical follow-ups don't re-call
         the model — directly implements the spec's "repeated responses"
         and "conversation context" efficiency requirements.
    `dataset_signature` should be something cheap like f"{len(df)}:{filters}"
    so the cache naturally invalidates when filters or the dataset change.
    """
    lang = get_language()
    key = _cache_key(question, lang, dataset_signature)
    cache = st.session_state.setdefault("_nova_llm_cache", {})
    if key in cache:
        return cache[key]

    full_system = build_multilingual_system_prompt(base_system_prompt)
    answer = adapter.complete(full_system, messages, max_tokens=max_tokens)

    if answer.startswith("⚠️"):
        # Don't cache errors — let the next attempt retry cleanly.
        return answer

    cache[key] = answer
    # Keep the cache from growing unbounded across a long session.
    if len(cache) > 200:
        for old_key in list(cache.keys())[:50]:
            cache.pop(old_key, None)
    return answer
