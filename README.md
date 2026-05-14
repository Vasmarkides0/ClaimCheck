# ClaimCheck

AI-powered pitch deck due diligence. Upload a pitch deck and ClaimCheck extracts every verifiable technical claim, searches the web for evidence, and scores each one from 0 to 100.

## What it does

VCs review hundreds of pitch decks a month. Most include technical claims that take hours to verify manually. ClaimCheck automates that.

Upload a PDF. A Claude agent extracts verifiable claims, searches for evidence, and returns a credibility report with green/amber/red verdicts, source links, red flags, and follow-up questions for the founder.

## How it works

A Claude agent runs a four-stage pipeline using the Anthropic SDK with tool use:

1. Extract text from the PDF via PyMuPDF
2. Identify verifiable technical claims
3. Search for evidence in parallel via Serper API, ranked by source reliability
4. Score each claim starting from a baseline of 50, adjusted by source quality and contradictions

Verdicts: Green (70+), Amber (40-69), Red (below 40).

## Tech stack

- Anthropic SDK (Claude with tool use) — agentic pipeline
- FastAPI + Python — backend
- PyMuPDF — PDF extraction
- Serper API — evidence retrieval
- React (Lovable) — frontend
- Deployed on Railway

## Project structure

**backend/** — main.py (FastAPI server + Claude agentic loop), pdf_extractor.py (PDF text extraction), claim_extractor.py (claim identification), evidence_retriever.py (web search via Serper API), scorer.py (hybrid scoring logic), demo/ (cached demo results), prompts/ (extraction.txt, scoring.txt)

**frontend/** — React frontend

## Getting started

**1. Clone the repo**

`git clone https://github.com/Vasmarkides0/ClaimCheck`

`cd ClaimCheck/backend`

`pip install fastapi uvicorn anthropic pymupdf requests python-dotenv`

**2. Add API keys to backend/.env/keys**

`ANTHROPIC_API_KEY=your_key_here`

`SERPER_API_KEY=your_key_here`

**3. Run the backend**

`cd backend`

`uvicorn main:app --reload --port 8000`

Open the frontend preview URL in a separate browser tab.

## API

`POST /analyze` — upload PDF or raw text, returns scored claims

`GET /demo/{id}` — returns cached demo result

`GET /report?demo_id={id}` — returns styled HTML report

## Built at

UCL AI Festival Hackathon 2026. 24 hours. Vasilis Markides and Miguel Landa.
