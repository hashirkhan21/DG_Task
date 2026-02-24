from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Tuple

from duckduckgo_search import DDGS

from ..config import get_settings


class DuckDuckGoSearchClient:
    """
    Thin wrapper around duckduckgo-search with simple rate limiting and error handling.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._last_call_ts: float = 0.0

    def _respect_rate_limit(self) -> None:
        # Very simple per-request delay based on rate_limit_per_minute
        min_interval = 60.0 / float(self._settings.rate_limit_per_minute)
        now = time.time()
        elapsed = now - self._last_call_ts
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_call_ts = time.time()

    def text_search(self, query: str, max_results: int | None = None) -> List[Dict[str, Any]]:
        """
        Perform a generic web text search.
        """
        self._respect_rate_limit()
        limit = max_results or self._settings.ddg_max_results

        try:
            with DDGS() as ddgs:
                results: Iterable[Dict[str, Any]] = ddgs.text(
                    query,
                    max_results=limit,
                    safesearch="moderate",
                )
                return list(results)
        except Exception as exc:  # noqa: BLE001
            # In a real system we might log this; here we just surface a structured error.
            return [
                {
                    "error": str(exc),
                    "query": query,
                    "kind": "ddg_error",
                }
            ]

    def multi_query_text_search(
        self, queries: List[Tuple[str, str]], max_results: int | None = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run multiple labeled queries and return a mapping label -> result list.

        `queries` is a list of (label, query_string).
        """
        all_results: Dict[str, List[Dict[str, Any]]] = {}
        for label, q in queries:
            all_results[label] = self.text_search(q, max_results=max_results)
        return all_results

