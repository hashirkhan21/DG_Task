from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from ..models import CandidateEvidence


_NAME_TITLE_PATTERN = re.compile(
    r"(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[-|–]\s*(?P<title>[^-|–]+?)\s*[-|–]\s*(?P<company>[^-|–]{2,})",
    re.IGNORECASE,
)


@dataclass
class RawSearchResult:
    title: str
    href: str
    body: str
    source_label: str
    query_label: str


def classify_source_label(url: str) -> str:
    host = url.lower()
    if "linkedin.com" in host:
        return "LinkedIn"
    if "wikipedia.org" in host:
        return "Wikipedia"
    if "crunchbase.com" in host:
        return "Crunchbase"
    if "about." in host or "/about" in host or "/team" in host or "/leadership" in host:
        return "Company website"
    if any(news_domain in host for news_domain in ["reuters.com", "bloomberg.com", "nytimes.com", "forbes.com"]):
        return "News outlet"
    return "Web result"


def _split_name(full_name: str) -> Optional[tuple[str, str]]:
    parts = full_name.strip().split()
    if len(parts) < 2:
        return None
    first = parts[0]
    last = parts[-1]
    return first, last


def extract_from_text_block(
    text: str, company: str, fallback_title: str, url: str, query_label: str
) -> Optional[CandidateEvidence]:
    match = _NAME_TITLE_PATTERN.search(text)
    if not match:
        return None

    full_name = match.group("name").strip()
    title = match.group("title").strip()
    company_guess = match.group("company").strip()

    name_parts = _split_name(full_name)
    if not name_parts:
        return None
    first_name, last_name = name_parts

    source_label = classify_source_label(url)

    credibility = 0.5
    if source_label in {"LinkedIn", "Company website"}:
        credibility = 0.9
    elif source_label in {"Wikipedia", "News outlet"}:
        credibility = 0.8

    if company.lower() in company_guess.lower():
        credibility += 0.05

    return CandidateEvidence(
        first_name=first_name,
        last_name=last_name,
        title=title or fallback_title,
        company_guess=company_guess,
        source_url=url,
        source_label=source_label,
        query_variant=query_label,
        credibility_score=min(credibility, 1.0),
    )


def normalize_ddg_result_item(item: Dict[str, Any], query_label: str) -> Optional[RawSearchResult]:
    href = item.get("href") or item.get("url")
    title = item.get("title") or ""
    body = item.get("body") or item.get("snippet") or ""
    if not href or not (title or body):
        return None
    return RawSearchResult(
        title=str(title),
        href=str(href),
        body=str(body),
        source_label=classify_source_label(str(href)),
        query_label=query_label,
    )


def extract_candidates_from_ddg_results(
    ddg_results_by_query: Dict[str, List[Dict[str, Any]]], company: str, designation: str
) -> List[CandidateEvidence]:
    candidates: List[CandidateEvidence] = []
    for query_label, items in ddg_results_by_query.items():
        for item in items:
            if "error" in item:
                continue
            raw = normalize_ddg_result_item(item, query_label)
            if not raw:
                continue
            combined_text = f"{raw.title} - {raw.body}"
            candidate = extract_from_text_block(
                combined_text,
                company=company,
                fallback_title=designation,
                url=raw.href,
                query_label=query_label,
            )
            if candidate:
                candidates.append(candidate)
                continue

            # Fallback: fetch page HTML for top few results to try extraction again
            if len(candidates) < 5:
                try:
                    resp = requests.get(raw.href, timeout=10)
                    if resp.ok and "text" in (resp.headers.get("Content-Type") or ""):
                        soup = BeautifulSoup(resp.text, "html.parser")
                        text_pieces: List[str] = []
                        if soup.title and soup.title.string:
                            text_pieces.append(soup.title.string)
                        for tag_name in ("h1", "h2", "h3"):
                            for tag in soup.find_all(tag_name):
                                if tag.get_text(strip=True):
                                    text_pieces.append(tag.get_text(strip=True))
                        page_text = " - ".join(text_pieces)
                        html_candidate = extract_from_text_block(
                            page_text,
                            company=company,
                            fallback_title=designation,
                            url=raw.href,
                            query_label=query_label,
                        )
                        if html_candidate:
                            candidates.append(html_candidate)
                except Exception:
                    # Network or parsing issues are non-fatal; we just skip HTML refinement for this result.
                    continue
    return candidates

