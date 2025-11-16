"""Estimate token usage of Gaode POI responses.

Usage:
    python tools/estimate_poi_tokens.py --query "火锅" --location "116.397128,39.916527" \
        --city 北京 --pages 1 --offset 20

The script calls Gaode's place/around API, aggregates POI fields, and reports
approximate token counts per POI and for the full batch. If tiktoken is
installed it will be used for accurate counts; otherwise it falls back to a
character/4 heuristic.
"""

import argparse
import json
import os
from typing import List, Dict, Any

import requests

try:
    import tiktoken  # type: ignore
except ImportError:  # pragma: no cover
    tiktoken = None


def encode_text(text: str) -> int:
    if tiktoken is None:
        return max(1, len(text) // 4)
    encoder = tiktoken.get_encoding("cl100k_base")
    return len(encoder.encode(text))


def build_poi_snippet(poi: Dict[str, Any]) -> str:
    fields = {
        "name": poi.get("name"),
        "address": poi.get("address"),
        "type": poi.get("type"),
        "rating": poi.get("biz_ext", {}).get("rating"),
        "cost": poi.get("biz_ext", {}).get("cost"),
        "location": poi.get("location"),
        "tel": poi.get("tel"),
    }
    return json.dumps(fields, ensure_ascii=False)


def fetch_pois(api_key: str, query: str, location: str, city: str, pages: int, offset: int,
               poi_type: str) -> List[Dict[str, Any]]:
    base_url = "https://restapi.amap.com/v3/place/around"
    pois: List[Dict[str, Any]] = []
    for page in range(1, pages + 1):
        params = {
            "key": api_key,
            "keywords": query,
            "location": location,
            "types": poi_type,
            "city": city,
            "citylimit": "true",
            "offset": str(offset),
            "page": str(page),
            "extensions": "all",
        }
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "1":
            raise RuntimeError(f"Gaode API error: {payload.get('info')}")
        page_pois = payload.get("pois", [])
        if not page_pois:
            break
        pois.extend(page_pois)
        if len(page_pois) < offset:
            break
    return pois


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate tokens for Gaode POI results")
    parser.add_argument("--query", default="美食", help="Keyword, e.g. 火锅")
    parser.add_argument(
        "--location",
        default="116.397128,39.916527",
        help="Gaode lng,lat string",
    )
    parser.add_argument("--city", default="北京", help="City name")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to fetch")
    parser.add_argument("--offset", type=int, default=20, help="POIs per page (<=25)")
    parser.add_argument("--types", default="050000", help="Gaode type filter")
    args = parser.parse_args()

    api_key = os.getenv("GAODE_API_KEY")
    if not api_key:
        raise EnvironmentError("GAODE_API_KEY is not set")

    pois = fetch_pois(
        api_key=api_key,
        query=args.query,
        location=args.location,
        city=args.city,
        pages=args.pages,
        offset=args.offset,
        poi_type=args.types,
    )

    snippets = [build_poi_snippet(p) for p in pois]
    token_counts = [encode_text(snippet) for snippet in snippets]
    total_tokens = sum(token_counts)
    avg_tokens = total_tokens / len(token_counts) if token_counts else 0

    print(f"Fetched {len(pois)} POIs")
    print(f"Total tokens ≈ {total_tokens:.0f}")
    print(f"Average tokens per POI ≈ {avg_tokens:.1f}")
    print("Max tokens for single POI ≈", max(token_counts, default=0))

    preview = "\n".join(snippets[:5])
    print("\nSample snippets (first 5):\n", preview)


if __name__ == "__main__":
    main()
