"""Input sanitization and prompt-injection mitigation helpers."""

import html
import re
from typing import Final

_MAX_QUERY_LEN: Final[int] = 8000
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_user_query(text: str, max_len: int = _MAX_QUERY_LEN) -> str:
    """Strip control chars, bound length, normalize whitespace."""
    if not isinstance(text, str):
        return ""
    t = _CONTROL_RE.sub("", text).strip()
    if len(t) > max_len:
        t = t[:max_len]
    t = re.sub(r"\s+", " ", t)
    return t


def sanitize_for_log(text: str, max_len: int = 500) -> str:
    """One-line safe snippet for logs."""
    t = sanitize_user_query(text, max_len=max_len)
    return t.replace("\n", " ").replace("\r", " ")


def escape_citation_html(text: str) -> str:
    """Escape user- or model-derived strings embedded in HTML UIs."""
    return html.escape(text or "", quote=True)
