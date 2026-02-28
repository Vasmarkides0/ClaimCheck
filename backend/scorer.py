import anthropic
import json


def _read_key(name: str) -> str:
    for line in open("/Users/vassilismarkides/Desktop/claimcheck/.env/keys"):
        if line.startswith(name + "="):
            return line.strip().split("=", 1)[1]
    return None


ANTHROPIC_API_KEY = _read_key("ANTHROPIC_API_KEY") or "YOUR_ANTHROPIC_API_KEY_HERE"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SCORING_PROMPT = """You are a technical due diligence analyst at a VC firm.

CLAIM FROM STARTUP PITCH DECK:
{claim_text}

EVIDENCE FOUND FROM WEB SEARCH:
{evidence_text}

Assess this claim's credibility based on the evidence. Return ONLY valid JSON, no markdown, no explanation:
{{
    "summary": "2-3 sentence assessment. Be specific — cite numbers from the evidence.",
    "evidence_for": [
        {{"text": "what supports the claim, citing specific data", "source_url": "URL"}}
    ],
    "evidence_against": [
        {{"text": "what contradicts the claim, citing specific data", "source_url": "URL"}}
    ],
    "red_flags": ["specific red flags like: no peer review, deprecated benchmark, cherry-picked metric, no public repo, superlative claim"],
    "follow_up_questions": ["2-3 specific questions a VC should ask the founder"]
}}

RULES:
- Only cite evidence that actually appears in the search results above
- Do NOT make up or hallucinate any sources
- Be specific with numbers — don't say "the claim seems exaggerated", say "evidence shows X while they claim Y"
- If there's insufficient evidence, say so clearly
- Return a MAXIMUM of 3 red flags. Only list a red flag if you can point to a specific gap in the evidence provided. Do not invent red flags that are not supported by what you see above."""


def score_claim_with_claude(claim: dict, evidence: list) -> dict:
    """Get Claude's qualitative assessment of a claim."""
    evidence_text = ""
    for i, e in enumerate(evidence[:10]):  # Limit to top 10 results
        evidence_text += f"\n[Source {i+1}] {e['source_domain']} (Reliability: Tier {e['source_tier']})\n"
        evidence_text += f"Title: {e['title']}\n"
        evidence_text += f"Snippet: {e['snippet']}\n"
        evidence_text += f"URL: {e['url']}\n"

    if not evidence_text.strip():
        evidence_text = "NO EVIDENCE FOUND — no relevant search results returned."

    prompt = SCORING_PROMPT.format(
        claim_text=claim.get("original_text", ""),
        evidence_text=evidence_text,
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = response.content[0].text
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    return json.loads(response_text.strip())


def calculate_score(assessment: dict, evidence: list) -> int:
    """Deterministic formula. Same input = same score. Always."""
    score = 50  # Start neutral

    # Count supporting evidence by tier
    for e in assessment.get("evidence_for", []):
        url = e.get("source_url", "")
        tier = 3  # default
        for ev in evidence:
            if ev["url"] == url:
                tier = ev["source_tier"]
                break
        if tier == 1:
            score += 15   # Academic/benchmark = strong support
        elif tier == 2:
            score += 10   # Reputable press = moderate support
        elif tier == 3:
            score += 3    # Company blog = weak support
        elif tier == 4:
            score += 1    # Social media = barely counts

    # Count contradicting evidence by tier
    for e in assessment.get("evidence_against", []):
        url = e.get("source_url", "")
        tier = 3
        for ev in evidence:
            if ev["url"] == url:
                tier = ev["source_tier"]
                break
        if tier == 1:
            score -= 20   # Academic contradiction = strong hit
        elif tier == 2:
            score -= 12   # Press contradiction = moderate hit
        elif tier == 3:
            score -= 5    # Blog contradiction = minor hit
        elif tier == 4:
            score -= 2    # Social media = barely counts

    # Red flags penalty
    score -= len(assessment.get("red_flags", [])) * 5

    # No evidence found at all = suspicious
    if not assessment.get("evidence_for") and not assessment.get("evidence_against"):
        score -= 15

    return max(0, min(100, score))


def get_verdict(score: int) -> str:
    if score >= 70:
        return "green"
    elif score >= 40:
        return "amber"
    else:
        return "red"


def score_claim(claim: dict, evidence: list) -> dict:
    """Full scoring pipeline: Claude assessment + deterministic formula."""
    assessment = score_claim_with_claude(claim, evidence)
    numerical_score = calculate_score(assessment, evidence)
    verdict = get_verdict(numerical_score)
    return {
        "id": claim.get("id"),
        "original_text": claim.get("original_text", ""),
        "claim_type": claim.get("claim_type", ""),
        "score": numerical_score,
        "verdict": verdict,
        "summary": assessment.get("summary", ""),
        "evidence_for": assessment.get("evidence_for", []),
        "evidence_against": assessment.get("evidence_against", []),
        "red_flags": assessment.get("red_flags", []),
        "follow_up_questions": assessment.get("follow_up_questions", []),
    }


if __name__ == "__main__":
    test_claim = {"id": 1, "original_text": "Our model is 10x faster than H100"}
    test_evidence = [
        {
            "title": "Groq benchmark",
            "snippet": "Groq achieves 300 tok/s...",
            "url": "https://semianalysis.com/test",
            "source_tier": 2,
            "source_domain": "semianalysis.com",
        }
    ]
    result = score_claim(test_claim, test_evidence)
    print(f"Score: {result['score']}, Verdict: {result['verdict']}")
