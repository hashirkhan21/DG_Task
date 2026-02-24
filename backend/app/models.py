from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class PersonFindRequest(BaseModel):
    company: str = Field(..., description="Company name, e.g., 'Meta' or 'Facebook'")
    designation: str = Field(..., description="Role, e.g., 'CEO', 'Chief Executive Officer'")


class CandidateEvidence(BaseModel):
    first_name: str
    last_name: str
    title: str
    company_guess: Optional[str] = None
    source_url: str
    source_label: str
    query_variant: Optional[str] = None
    credibility_score: float


class PersonFindResponse(BaseModel):
    first_name: str
    last_name: str
    title: str
    company: str
    source_url: str
    source_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    raw_candidates: List[CandidateEvidence] = []
    agent_notes: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    confidence: float = 0.0
    tried_sources: List[str] = []
    warning: Optional[str] = None
    kind: Optional[Literal["no_result", "upstream_error", "bad_request"]] = None

