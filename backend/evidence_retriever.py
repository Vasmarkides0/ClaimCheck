import requests


def _read_key(name: str) -> str:
    for line in open("/Users/vassilismarkides/Desktop/claimcheck/.env/keys"):
        if line.startswith(name + "="):
            return line.strip().split("=", 1)[1]
    return None


SERPER_API_KEY = _read_key("SERPER_API_KEY")

# How reliable is each source? Tier 1 = most reliable, Tier 4 = least
SOURCE_TIERS = {
    # Tier 1: Academic and independent benchmarks
    "arxiv.org": 1,
    "paperswithcode.com": 1,
    "huggingface.co": 1,
    "mlperf.org": 1,
    "nature.com": 1,
    "ieee.org": 1,
    "openreview.net": 1,
    # Tier 2: Reputable tech press and company research blogs
    "techcrunch.com": 2,
    "reuters.com": 2,
    "theverge.com": 2,
    "semianalysis.com": 2,
    "venturebeat.com": 2,
    "wired.com": 2,
    "arstechnica.com": 2,
    "openai.com": 2,
    "anthropic.com": 2,
    "research.google": 2,
    # Tier 3: Blogs, company pages, unknown
    "medium.com": 3,
    "substack.com": 3,
    "towardsdatascience.com": 3,
    # Tier 4: Social media, forums
    "reddit.com": 4,
    "twitter.com": 4,
    "x.com": 4,
    "quora.com": 4,
}


def classify_source(url: str) -> int:
    """What tier is this source? Returns 1-4. Default 3 (unknown)."""
    for domain, tier in SOURCE_TIERS.items():
        if domain in url.lower():
            return tier
    return 3


def search_web(query: str, num_results: int = 3) -> list:
    """Run one Google search via Serper.dev. Returns list of results."""
    response = requests.post(
        "https://google.serper.dev/search",
        json={"q": query, "num": num_results},
        headers={"X-API-KEY": SERPER_API_KEY},
    )
    if response.status_code != 200:
        print(f"Search failed for: {query}")
        return []
    results = response.json().get("organic", [])
    return [
        {
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "url": r.get("link", ""),
            "source_tier": classify_source(r.get("link", "")),
            "source_domain": r.get("link", "").split("/")[2] if len(r.get("link", "").split("/")) > 2 else "unknown",
        }
        for r in results
    ]


def retrieve_evidence(claim: dict) -> list:
    """For one claim, run all its search queries and combine results. Remove duplicates."""
    all_evidence = []
    seen_urls = set()
    for query in claim.get("search_queries", []):
        results = search_web(query)
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_evidence.append(r)
    # Sort: most reliable sources first
    all_evidence.sort(key=lambda x: x["source_tier"])
    return all_evidence


if __name__ == "__main__":
    test_claim = {
        "search_queries": [
        "attention is all you need arxiv transformer",
        "BERT paper arxiv natural language processing",
        "Vision Transformer ViT arxiv paper",
        ]
    }
    results = retrieve_evidence(test_claim)
    for r in results:
        print(f"[Tier {r['source_tier']}] {r['source_domain']}: {r['title']}") 