from typing import Any


class CitationService:
    @staticmethod
    def dedupe_citations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for c in items:
            key = str(c.get("pmid") or c.get("url") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(c)
        return out
