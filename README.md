# ClaimCheck

> AI-powered technical due diligence for venture capitalists.

---

## The Problem

VCs review hundreds of pitch decks every month. Many include technical claims — benchmark scores, performance comparisons, accuracy metrics — that are impossible to verify without domain expertise and hours of manual research. In practice, investors either spend hours cross-checking sources or rely on founder representations.

When a startup claims it outperforms GPT-4 on MMLU, few investors have the time to check whether the cited baseline is current, comparable, or even accurate.

---

## The Solution

Upload a pitch deck. ClaimCheck does the rest.

A Claude agent autonomously extracts every verifiable technical claim, searches the web for evidence, and scores each claim from 0 to 100 — returning a structured credibility report in minutes.

Each claim gets:
- A **green, amber, or red verdict**
- Supporting and contradicting evidence with **clickable source links**
- Automatically detected **red flags**
- **Follow-up questions** to ask the founder in the next meeting

---

## How It Works

ClaimCheck uses the Anthropic SDK to run a Claude agent that autonomously orchestrates a four-stage verification pipeline. Rather than a hardcoded sequence, Claude reasons over evidence between tool calls and adapts its investigation strategy per claim.
```
PDF Upload
    │
    ▼
[1] extract_text_from_pdf   →   Raw text extracted via PyMuPDF
    │
    ▼
[2] extract_claims          →   Claude identifies verifiable technical claims
    │
    ▼
[3] retrieve_evidence       →   Parallel web searches via Serper API
    │                           Sources ranked by reliability tier
    ▼
[4] score_claim             →   Hybrid scoring: Claude reasoning + deterministic formula
    │
    ▼
Structured Report
```

### Scoring Formula

Each claim starts at a baseline of 50 and is adjusted deterministically:

| Signal | Adjustment |
|--------|-----------|
| Tier 1 source support (arxiv, official docs) | +15 |
| Tier 2 source support (established tech media) | +10 |
| Tier 1 source contradiction | -20 |
| Red flag detected | -5 each |

Verdicts: **Green** (70+) · **Amber** (40–69) · **Red** (below 40)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Agent | Anthropic SDK — Claude with tool use |
| Backend | FastAPI + Python |
| PDF Extraction | PyMuPDF |
| Evidence Retrieval | Serper API (Google Search) |
| Parallelisation | Python ThreadPoolExecutor |
| Frontend | React via Lovable |
| Server | Uvicorn |

---

## Project Structure
```
claimcheck/
├── backend/
│   ├── main.py                 # FastAPI server + Claude agentic loop
│   ├── pdf_extractor.py        # PDF text extraction
│   ├── claim_extractor.py      # Claim identification via Claude
│   ├── evidence_retriever.py   # Parallelised web search via Serper API
│   ├── scorer.py               # Hybrid scoring logic
│   ├── demo/                   # Cached demo results
│   └── prompts/
│       ├── extraction.txt      # Claim extraction prompt
│       └── scoring.txt         # Scoring prompt
└── frontend/                   # React frontend built with Lovable
```

---

## Setup

### Prerequisites

- Python 3.9+
- Anthropic API key
- Serper API key

### Install Dependencies
```bash
git clone https://github.com/Vasmarkides0/ClaimCheck
cd ClaimCheck/backend
pip install fastapi uvicorn anthropic pymupdf requests python-dotenv
```

### API Keys

Create a file at `backend/.env/keys`:
```
ANTHROPIC_API_KEY=your_key_here
SERPER_API_KEY=your_key_here
```

### Run the Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

Open the frontend preview URL in a separate browser tab. Localhost API calls will not work inside the Lovable iframe.

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Upload a PDF or raw text, returns scored claims |
| `/demo/{id}` | GET | Returns a cached demo result as JSON |
| `/report?demo_id={id}` | GET | Returns a styled HTML report |

---

## Built At

**UCL AI Festival Hackathon 2026**

Built in 24 hours by Vasilis Markides and Miguel Landaa.
