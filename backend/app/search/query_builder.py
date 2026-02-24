from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


_DESIGNATION_ALIASES: Dict[str, List[str]] = {
    "ceo": ["CEO", "Chief Executive Officer"],
    "cto": ["CTO", "Chief Technology Officer"],
    "cfo": ["CFO", "Chief Financial Officer"],
    "coo": ["COO", "Chief Operating Officer"],
    "cmo": ["CMO", "Chief Marketing Officer"],
    "founder": ["Founder", "Co-founder"],
    "chairman": ["Chairman", "Chairwoman", "Chairperson"],
}


@dataclass(frozen=True)
class QueryVariant:
    label: str
    query: str


def _normalize_designation(designation: str) -> str:
    return designation.strip().lower()


def get_aliases_for_designation(designation: str) -> List[str]:
    key = _normalize_designation(designation)
    # If we know this designation, return its aliases; otherwise, just return the original
    if key in _DESIGNATION_ALIASES:
        return _DESIGNATION_ALIASES[key]
    # Also try to look up raw (for exact phrases like 'chief executive officer')
    for canon, aliases in _DESIGNATION_ALIASES.items():
        if key in (a.lower() for a in aliases):
            return aliases
    return [designation.strip()]


def build_search_queries(company: str, designation: str) -> List[QueryVariant]:
    """
    Build multiple search query variants combining company, designation aliases, and
    bias terms like LinkedIn or press releases.
    """
    company = company.strip()
    aliases = get_aliases_for_designation(designation)

    queries: List[QueryVariant] = []

    # Variant 1: LinkedIn-focused search
    queries.append(
        QueryVariant(
            label="linkedin_focus",
            query=f'{company} {aliases[0]} site:linkedin.com "profile"',
        )
    )

    # Variant 2: Company site / about page
    queries.append(
        QueryVariant(
            label="company_site",
            query=f'{company} {aliases[0]} site:{company.replace(" ", "").lower()}.com "leadership"',
        )
    )

    # Variant 3: News / press release
    queries.append(
        QueryVariant(
            label="news_press",
            query=f'{company} {aliases[0]} "press release" OR "announces" OR "appointed"',
        )
    )

    # Variant 4: Generic alias-based search across aliases
    alias_terms = " OR ".join(f'"{a}"' for a in aliases)
    queries.append(
        QueryVariant(
            label="generic_role",
            query=f'{company} ({alias_terms})',
        )
    )

    return queries

