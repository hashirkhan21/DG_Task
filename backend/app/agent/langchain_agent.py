from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Union

from langchain_core.runnables import RunnableLambda, RunnableSequence

from ..config import get_settings
from ..models import (
    CandidateEvidence,
    ErrorResponse,
    PersonFindRequest,
    PersonFindResponse,
)
from ..search.aggregator import aggregate_candidates, compute_overall_confidence
from ..search.duckduckgo_client import DuckDuckGoSearchClient
from ..search.extractor import extract_candidates_from_ddg_results
from ..search.query_builder import build_search_queries
from ..search.service import run_person_search


def _needs_refinement(result: Union[PersonFindResponse, ErrorResponse]) -> bool:
    if isinstance(result, ErrorResponse):
        return True
    return result.confidence < 0.8


def _build_refined_queries(
    request: PersonFindRequest, base_result: PersonFindResponse
) -> Dict[str, str]:
    """
    Build additional, more targeted queries using the top candidate name.
    """
    name = f"{base_result.first_name} {base_result.last_name}"
    company = request.company
    designation = request.designation

    refined = {
        "name_company_role": f'{name} {company} {designation}',
        "name_linkedin": f'{name} {company} site:linkedin.com',
        "name_company_site": f'{name} site:{company.replace(" ", "").lower()}.com',
    }
    return refined


def _refine_with_additional_search(
    data: Dict[str, Union[PersonFindRequest, PersonFindResponse, ErrorResponse]]
) -> Union[PersonFindResponse, ErrorResponse]:
    request = data["request"]
    base_result = data["base_result"]

    assert isinstance(request, PersonFindRequest)

    if isinstance(base_result, ErrorResponse):
        # Nothing to refine; just pass through with a note.
        base_result.agent_notes = (
            "Agent attempted refinement but base search returned no candidates."
        )
        return base_result

    if not _needs_refinement(base_result):
        base_result.agent_notes = (
            base_result.agent_notes
            or "Agent accepted base result without refinement (high confidence)."
        )
        return base_result

    ddg = DuckDuckGoSearchClient()
    extra_queries = _build_refined_queries(request, base_result)
    labeled_queries = list(extra_queries.items())
    extra_results = ddg.multi_query_text_search(labeled_queries)

    extra_candidates: List[CandidateEvidence] = extract_candidates_from_ddg_results(
        extra_results,
        company=request.company,
        designation=request.designation,
    )

    if not extra_candidates:
        base_result.agent_notes = (
            base_result.agent_notes
            or "Agent attempted refinement but did not find stronger evidence."
        )
        return base_result

    merged_candidates = aggregate_candidates(
        list(base_result.raw_candidates) + extra_candidates
    )
    new_confidence = compute_overall_confidence(merged_candidates)
    top = merged_candidates[0]

    # If the refined result is actually weaker, keep the original.
    if new_confidence <= base_result.confidence:
        base_result.agent_notes = (
            base_result.agent_notes
            or "Agent refinement did not improve confidence; kept base result."
        )
        return base_result

    refined = PersonFindResponse(
        first_name=top.first_name,
        last_name=top.last_name,
        title=top.title,
        company=request.company,
        source_url=top.source_url,
        source_label=top.source_label,
        confidence=new_confidence,
        raw_candidates=merged_candidates,
        agent_notes=(
            "Agent refined query using top candidate name and cross-validated with "
            "additional DuckDuckGo searches."
        ),
    )
    return refined


def run_with_agent(
    request: PersonFindRequest,
) -> Union[PersonFindResponse, ErrorResponse]:
    """
    Run the base pipeline and, if needed, refine it using an agentic LangChain graph.

    This uses LangChain's Runnable graph to orchestrate multiple search/refinement
    steps without requiring an external LLM API key.
    """
    settings = get_settings()
    if not settings.enable_langchain_agent:
        return run_person_search(request)

    base_step = RunnableLambda(
        lambda req: {
            "request": req,
            "base_result": run_person_search(req),
        }
    )
    refine_step = RunnableLambda(_refine_with_additional_search)

    chain: RunnableSequence = base_step | refine_step
    return chain.invoke(request)

