import concurrent.futures
import json
import os
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from pdf_extractor import extract_text_from_pdf
from claim_extractor import extract_claims
from evidence_retriever import retrieve_evidence
from scorer import score_claim

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_BACKEND_DIR = os.path.dirname(__file__)
DEMO_DIR = os.path.join(_BACKEND_DIR, "demo")


@app.post("/analyze")
async def analyze(file: UploadFile = File(None), text: str = Form(None)):
    # Station 1: extract text
    if file is not None:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        try:
            deck_text = extract_text_from_pdf(tmp_path)
        finally:
            os.unlink(tmp_path)
    elif text:
        deck_text = text
    else:
        raise HTTPException(status_code=400, detail="Provide either a PDF file or raw text.")

    # Station 2: extract verifiable claims
    extraction = extract_claims(deck_text)
    claims = extraction.get("claims", [])

    # Stations 3 + 4: retrieve evidence then score each claim
    def process_claim(claim):
        evidence = retrieve_evidence(claim)
        return score_claim(claim, evidence)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        scored_claims = list(executor.map(process_claim, claims))

    # Build summary
    verdicts = [c["verdict"] for c in scored_claims]
    scores = [c["score"] for c in scored_claims]
    summary = {
        "total_claims": len(scored_claims),
        "verified": verdicts.count("green"),
        "uncertain": verdicts.count("amber"),
        "unverified": verdicts.count("red"),
        "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
    }

    return {"summary": summary, "claims": scored_claims}


@app.get("/demo/{demo_id}")
async def get_demo(demo_id: str):
    path = os.path.join(DEMO_DIR, f"cached_result_{demo_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Demo '{demo_id}' not found.")
    with open(path) as f:
        return json.load(f)


def generate_report_html(results: dict) -> str:
    summary = results.get("summary", {})
    claims = results.get("claims", [])

    VERDICT_COLOR = {"green": "#22c55e", "amber": "#f59e0b", "red": "#ef4444"}
    VERDICT_LABEL = {"green": "Verified", "amber": "Uncertain", "red": "Unverified"}

    def bullet_list(items: list, link_key: str = None) -> str:
        if not items:
            return ""
        lis = ""
        for item in items:
            if link_key and isinstance(item, dict):
                url = item.get("source_url", "#")
                txt = item.get("text", "")
                lis += f'<li><a href="{url}" target="_blank">{txt}</a></li>'
            else:
                lis += f"<li>{item}</li>"
        return f"<ul>{lis}</ul>"

    claims_html = ""
    for claim in claims:
        verdict = claim.get("verdict", "amber")
        color = VERDICT_COLOR.get(verdict, "#f59e0b")
        label = VERDICT_LABEL.get(verdict, "Uncertain")
        score = claim.get("score", 0)

        ev_for = bullet_list(claim.get("evidence_for", []), link_key="source_url")
        ev_against = bullet_list(claim.get("evidence_against", []), link_key="source_url")
        red_flags = bullet_list(claim.get("red_flags", []))
        follow_ups = bullet_list(claim.get("follow_up_questions", []))

        sections = ""
        if ev_for:
            sections += f'<div class="section"><strong>Evidence For</strong>{ev_for}</div>'
        if ev_against:
            sections += f'<div class="section"><strong>Evidence Against</strong>{ev_against}</div>'
        if red_flags:
            sections += f'<div class="section"><strong>Red Flags</strong>{red_flags}</div>'
        if follow_ups:
            sections += f'<div class="section"><strong>Follow-up Questions</strong>{follow_ups}</div>'

        claims_html += f"""
        <div class="claim" style="border-left:4px solid {color};">
          <div class="claim-header">
            <span class="claim-text">&ldquo;{claim.get('original_text', '')}&rdquo;</span>
            <span class="badge" style="background:{color};">{label} &mdash; {score}/100</span>
          </div>
          <p class="claim-type">{claim.get('claim_type', '').replace('_', ' ')}</p>
          <p class="summary">{claim.get('summary', '')}</p>
          {sections}
        </div>"""

    avg = summary.get("average_score", 0)
    total = summary.get("total_claims", 0)
    verified = summary.get("verified", 0)
    uncertain = summary.get("uncertain", 0)
    unverified = summary.get("unverified", 0)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ClaimCheck Report</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           background: #0f172a; color: #e2e8f0; padding: 32px 24px; line-height: 1.6; }}
    h1 {{ font-size: 1.75rem; font-weight: 700; margin-bottom: 4px; }}
    .subtitle {{ color: #94a3b8; margin-bottom: 32px; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
                     gap: 16px; margin-bottom: 36px; }}
    .stat {{ background: #1e293b; border-radius: 12px; padding: 20px; text-align: center; }}
    .stat-value {{ font-size: 2rem; font-weight: 700; }}
    .stat-label {{ color: #94a3b8; font-size: 0.8rem; margin-top: 4px; text-transform: uppercase;
                   letter-spacing: 0.05em; }}
    .claim {{ background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 16px; }}
    .claim-header {{ display: flex; justify-content: space-between; align-items: flex-start;
                     gap: 16px; margin-bottom: 8px; }}
    .claim-text {{ font-style: italic; color: #cbd5e1; flex: 1; }}
    .badge {{ border-radius: 6px; padding: 4px 10px; font-size: 0.78rem; font-weight: 600;
              color: #fff; white-space: nowrap; }}
    .claim-type {{ color: #64748b; font-size: 0.75rem; text-transform: uppercase;
                   letter-spacing: 0.06em; margin-bottom: 10px; }}
    .summary {{ color: #cbd5e1; margin-bottom: 4px; }}
    .section {{ margin-top: 12px; }}
    .section strong {{ display: block; font-size: 0.82rem; text-transform: uppercase;
                       letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 4px; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 4px; }}
    a {{ color: #60a5fa; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <h1>ClaimCheck Report</h1>
  <p class="subtitle">Technical due diligence analysis of pitch deck claims</p>
  <div class="summary-grid">
    <div class="stat">
      <div class="stat-value">{total}</div>
      <div class="stat-label">Total Claims</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#22c55e;">{verified}</div>
      <div class="stat-label">Verified</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#f59e0b;">{uncertain}</div>
      <div class="stat-label">Uncertain</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#ef4444;">{unverified}</div>
      <div class="stat-label">Unverified</div>
    </div>
    <div class="stat">
      <div class="stat-value">{avg}</div>
      <div class="stat-label">Avg Score</div>
    </div>
  </div>
  {claims_html}
</body>
</html>"""


@app.get("/report")
async def get_report(demo_id: str = None):
    """
    Returns an HTML report. Pass ?demo_id=<id> to render a cached result
    from demo/cached_result_<id>.json. To render a live result, call
    generate_report_html() directly or add a POST /report variant.
    """
    if demo_id is None:
        raise HTTPException(status_code=400, detail="Provide ?demo_id=<id> as a query parameter.")
    path = os.path.join(DEMO_DIR, f"cached_result_{demo_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Demo '{demo_id}' not found.")
    with open(path) as f:
        results = json.load(f)
    return HTMLResponse(content=generate_report_html(results))


# Run with: uvicorn main:app --reload --port 8000
