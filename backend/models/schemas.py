from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class CitationSpan(BaseModel):
    source_id: str = Field(description="The unique identifier for the source (e.g., PMID).")
    chunk_id: str = Field(description="The unique identifier for the specific chunk of text.")
    start_char: int = Field(description="Starting character offset in the source text.")
    end_char: int = Field(description="Ending character offset in the source text.")
    exact_text: str = Field(description="The exact text snippet from the source.")

class ValidatedClaim(BaseModel):
    claim: str = Field(description="The atomic claim made in the response.")
    is_supported: bool = Field(description="Whether the claim is fully supported by the retrieved evidence.")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0.")
    citations: List[CitationSpan] = Field(default_factory=list, description="List of citation spans supporting the claim.")

class QueryIntent(BaseModel):
    intent_type: Literal["medical_question", "general_chat", "clarification_needed"] = Field(
        description="The classified intent of the user query."
    )
    entities: List[str] = Field(description="Extracted medical entities (e.g., diseases, drugs, symptoms).")
    requires_clarification: bool = Field(description="True if the query is ambiguous and needs clarification.")
    clarification_prompt: Optional[str] = Field(
        description="If clarification is needed, the question to ask the user.", default=None
    )

class RetrievalPlan(BaseModel):
    search_queries: List[str] = Field(description="List of optimized search queries.")
    temporal_filter_years: Optional[int] = Field(description="Number of years to filter back, if applicable.", default=None)
    required_source_types: List[str] = Field(
        description="List of source types to prioritize (e.g., 'rct', 'systematic_review').",
        default_factory=list
    )

class EvidenceQuality(BaseModel):
    quality_level: Literal["high", "moderate", "low", "insufficient"] = Field(
        description="The overall quality of the retrieved evidence."
    )
    reasoning: str = Field(description="Explanation for the quality assessment.")
    trust_score: float = Field(description="Aggregated trust score based on source types.", default=0.0)

class DraftResponse(BaseModel):
    response_text: str = Field(description="The generated response text, grounded ONLY in the provided evidence.")
    claims: List[ValidatedClaim] = Field(description="The atomic claims extracted from the response text for validation.")
