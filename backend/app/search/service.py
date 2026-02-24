from __future__ import annotations

from typing import Tuple, Union

from ..models import (
    CandidateEvidence,
    ErrorResponse,
    PersonFindRequest,
    PersonFindResponse,
)
from .aggregator import aggregate_candidates, compute_overall_confidence
from .duckduckgo_client import DuckDuckGoSearchClient
from .extractor import extract_candidates_from_ddg_results
from .query_builder import build_search_queries


def run_person_search(request: PersonFindRequest) -> Union[PersonFindResponse, ErrorResponse]:
    company = request.company.strip()
    designation = request.designation.strip()
    if not company or not designation:
        return ErrorResponse(
            error="Both company and designation are required.",
            confidence=0.0,
            tried_sources=[],
            kind="bad_request",
        )

    queries = build_search_queries(company, designation)
    client = DuckDuckGoSearchClient()

    label_query_pairs = [(q.label, q.query) for q in queries]
    raw_results_by_label = client.multi_query_text_search(label_query_pairs)

    candidates: list[CandidateEvidence] = extract_candidates_from_ddg_results(
        raw_results_by_label,
        company=company,
        designation=designation,
    )

    if not candidates:
        tried = list(raw_results_by_label.keys())
        return ErrorResponse(
            error="No matching person found in public search results.",
            confidence=0.0,
            tried_sources=tried,
            kind="no_result",
        )

    merged = aggregate_candidates(candidates)
    confidence = compute_overall_confidence(merged)

    top = merged[0]

    response = PersonFindResponse(
        first_name=top.first_name,
        last_name=top.last_name,
        title=top.title,
        company=company,
        source_url=top.source_url,
        source_label=top.source_label,
        confidence=confidence,
        raw_candidates=merged,
        agent_notes=None,
    )
    return response

