"""
data_engine.file_detector
─────────────────────────────
Detects a file's type from its extension and classifies it into a broad
category — structured, semi-structured, document, presentation, image, or
unknown — BEFORE anything tries to parse it as a table. Only structured and
semi-structured files are turned into a dataset right now; document,
presentation, and image formats are recognized and reported honestly
rather than forced into a broken table (Phase 2 — not yet implemented).
"""

_STRUCTURED_EXTENSIONS = {"csv", "tsv", "xlsx", "xls", "xlsm", "parquet", "ods"}
_SEMI_STRUCTURED_EXTENSIONS = {"json", "jsonl", "xml"}
_DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx", "txt", "rtf"}
_PRESENTATION_EXTENSIONS = {"ppt", "pptx"}
_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

ALL_SUPPORTED_NOW = sorted(_STRUCTURED_EXTENSIONS | _SEMI_STRUCTURED_EXTENSIONS)
ALL_RECOGNIZED = sorted(
    _STRUCTURED_EXTENSIONS | _SEMI_STRUCTURED_EXTENSIONS
    | _DOCUMENT_EXTENSIONS | _PRESENTATION_EXTENSIONS | _IMAGE_EXTENSIONS
)


def classify_file(filename: str) -> dict:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext in _STRUCTURED_EXTENSIONS:
        category = "structured"
    elif ext in _SEMI_STRUCTURED_EXTENSIONS:
        category = "semi_structured"
    elif ext in _DOCUMENT_EXTENSIONS:
        category = "document"
    elif ext in _PRESENTATION_EXTENSIONS:
        category = "presentation"
    elif ext in _IMAGE_EXTENSIONS:
        category = "image"
    else:
        category = "unknown"
    return dict(
        extension=ext,
        category=category,
        supported_now=category in ("structured", "semi_structured"),
    )
