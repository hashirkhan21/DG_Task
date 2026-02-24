from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from ..models import CandidateEvidence


def _key_for_candidate(c: CandidateEvidence) -> Tuple[str, str]:
    return (c.first_name.lower() + " " + c.last_name.lower(), c.title.lower())


def aggregate_candidates(candidates: List[CandidateEvidence]) -> List[CandidateEvidence]:
    """
    Group candidates by (normalized full name, title) and average their credibility scores.
    """
    grouped: Dict[Tuple[str, str], List[CandidateEvidence]] = defaultdict(list)
    for c in candidates:
        grouped[_key_for_candidate(c)].append(c)

    merged: List[CandidateEvidence] = []
    for _, group in grouped.items():
        base = group[0]
        avg_cred = sum(c.credibility_score for c in group) / float(len(group))
        best_source = max(group, key=lambda c: c.credibility_score)
        merged.append(
            CandidateEvidence(
                first_name=base.first_name,
                last_name=base.last_name,
                title=base.title,
                company_guess=best_source.company_guess,
                source_url=best_source.source_url,
                source_label=best_source.source_label,
                query_variant=best_source.query_variant,
                credibility_score=avg_cred,
            )
        )
    merged.sort(key=lambda c: c.credibility_score, reverse=True)
    return merged


def compute_overall_confidence(merged_candidates: List[CandidateEvidence]) -> float:
    if not merged_candidates:
        return 0.0

    top = merged_candidates[0]
    score = top.credibility_score

    if len(merged_candidates) >= 2:
        second = merged_candidates[1]
        if _key_for_candidate(top) == _key_for_candidate(second):
            score = min(1.0, score + 0.1)

    return max(0.0, min(score, 1.0))

