from typing import List, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.config import get_settings
from backend.llm.provider import get_llm_provider

STRICT_SYSTEM_PROMPT = """You are a strictly constrained medical evidence synthesizer.

RULES:
1. Answer ONLY using the supplied medical evidence chunks below.
2. If the answer cannot be directly inferred from the evidence, respond EXACTLY with: "I don't know based on the available evidence."
3. Do not use prior knowledge.
4. Do not infer unsupported conclusions.
5. Every medical claim must map to the retrieved citations.

EVIDENCE CHUNKS:
{evidence}
"""


class ResponseSynthesizer:
    def __init__(self, provider_type: str = "openrouter", model_name: str | None = None):
        settings = get_settings()
        self.provider = get_llm_provider(
            provider_type, model_name or settings.llm_model_generation
        )

    @staticmethod
    def _extractive_summary(query: str, chunks: List[Dict]) -> str:
        """Deterministic grounding when no LLM is configured."""
        lines = [
            "The following passages were retrieved from the evidence index "
            "(no generative model is configured; excerpts only, not a clinical recommendation):",
            "",
        ]
        for i, chunk in enumerate(chunks[:8], start=1):
            meta = chunk.get("metadata") or {}
            pmid = meta.get("pmid", "unknown")
            title = (meta.get("title") or "").strip()
            text = (chunk.get("text") or chunk.get("page_content") or "").strip()
            snippet = text[:650] + ("…" if len(text) > 650 else "")
            head = f"[{i}] PMID {pmid}"
            if title:
                head += f" — {title}"
            lines.append(head)
            lines.append(snippet)
            lines.append("")
        lines.append(f"User question (for context only): {query}")
        return "\n".join(lines).strip()

    async def synthesize(self, query: str, chunks: List[Dict]) -> str:
        settings = get_settings()
        if not chunks:
            from backend.core.constants import FALLBACK_NO_EVIDENCE

            return FALLBACK_NO_EVIDENCE

        if not (settings.openrouter_api_key or "").strip():
            return self._extractive_summary(query, chunks)

        evidence_text = ""
        for chunk in chunks:
            pmid = (chunk.get("metadata") or {}).get("pmid", "Unknown")
            text = chunk.get("text") or chunk.get("page_content", "")
            evidence_text += f"\n[PMID: {pmid}]:\n{text}\n"

        system_prompt = STRICT_SYSTEM_PROMPT.format(evidence=evidence_text)
        try:
            model = self.provider.get_model(temperature=0.0)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query),
            ]
            response = await model.ainvoke(messages)
            return str(response.content)
        except Exception as e:
            print(f"LLM Generation Exception: {e}")
            return self._extractive_summary(query, chunks)
