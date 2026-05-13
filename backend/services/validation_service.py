from typing import Any

from backend.validation.evidence_validator import assess_evidence


class ValidationService:
    async def assess(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        return assess_evidence(chunks)
