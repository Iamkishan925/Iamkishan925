"""News headlines + sentiment from Alpha Vantage NEWS_SENTIMENT."""

from __future__ import annotations

import httpx2 as httpx

AV_URL = "https://www.alphavantage.co/query"


def latest(api_key: str | None, tickers: list[str] | None = None, limit: int = 10) -> list[dict]:
    """Return a compact list of recent articles. Empty list if no key configured.

    Alpha Vantage ticker formats: "AAPL", "FOREX:EUR", "CRYPTO:BTC".
    """
    if not api_key:
        return []
    params = {"function": "NEWS_SENTIMENT", "apikey": api_key, "limit": str(limit), "sort": "LATEST"}
    if tickers:
        params["tickers"] = ",".join(tickers)
    r = httpx.get(AV_URL, params=params, timeout=15)
    r.raise_for_status()
    feed = r.json().get("feed", [])[:limit]
    return [
        {
            "title": a.get("title"),
            "source": a.get("source"),
            "published": a.get("time_published"),
            "sentiment": a.get("overall_sentiment_label"),
            "score": a.get("overall_sentiment_score"),
            "summary": (a.get("summary") or "")[:400],
            "url": a.get("url"),
        }
        for a in feed
    ]
