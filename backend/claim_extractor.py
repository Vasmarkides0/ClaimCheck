import anthropic
import json
import os

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def _read_key(name: str) -> str:
    for line in open("/Users/vassilismarkides/Desktop/claimcheck/.env/keys"):
        if line.startswith(name + "="):
            return line.strip().split("=", 1)[1]
    return None


ANTHROPIC_API_KEY = _read_key("ANTHROPIC_API_KEY") or "YOUR_ANTHROPIC_API_KEY_HERE"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

with open(os.path.join(_PROMPTS_DIR, "extraction.txt")) as f:
    EXTRACTION_PROMPT = f.read()


def extract_claims(text: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        temperature=0,
        messages=[{
            "role": "user",
            "content": f"{EXTRACTION_PROMPT}\n\n--- PITCH DECK TEXT ---\n{text}",
        }],
    )

    response_text = response.content[0].text
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    return json.loads(response_text.strip())


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/Users/vassilismarkides/Desktop/claimcheck/backend")
    from pdf_extractor import extract_text_from_pdf

    text = extract_text_from_pdf("/Users/vassilismarkides/Desktop/claimcheck/FINAL_build_roadmap.md.pdf")
    result = extract_claims(text)

    claims = result.get("claims", [])
    print(f"Found {len(claims)} verifiable claim(s):\n")
    for claim in claims:
        print(f"  [{claim['id']}] {claim['original_text']}")
