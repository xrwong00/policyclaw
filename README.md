# PolicyClaw

**Claw back control from policy confusion.**

PolicyClaw is an AI decision-intelligence product that turns dense insurance PDFs into clear, evidence-backed recommendations. In minutes, users can see what they are paying for, where policies overlap, what rights they can act on, and whether to keep, switch, downgrade, or dump.

## Problem

Insurance policyholders face a decision paralysis problem:

- Policy documents are long, technical, and hard to compare.
- Benefits and exclusions are easy to miss.
- Policy overlap creates hidden waste.
- Most users do not know their rights under BNM guidance.

The result is poor decisions made under uncertainty: overpaying, underprotected coverage, and delayed action.

## Solution

PolicyClaw combines document understanding and AI reasoning into one decision flow:

1. Ingest policy PDF(s) and extract structured policy details.
2. Retrieve relevant evidence chunks from source documents.
3. Run AI analysis for coverage quality, overlap risk, and rights detection.
4. Return a final verdict with confidence and citations.

This is decision support, not blind automation: users can review and edit extracted fields before analysis.

## Key Features

### Policy X-Ray
Transforms complex policy text into a clear summary of plan type, premium, coverage limit, dates, and riders.

### Overlap Detection
Identifies duplicate or unnecessary coverage across policy documents to surface avoidable spend.

### BNM Rights Scanner
Flags relevant Bank Negara Malaysia consumer-rights signals found in policy wording.

### Verdict Engine
Outputs a direct action recommendation: **Keep**, **Switch**, **Downgrade**, or **Dump** with reasons, confidence score, and supporting citations.

## How It Works

1. **Upload PDF(s):** User uploads one or more insurance policies.
2. **Auto-Extraction:** Backend extracts candidate policy profiles and auto-fills fields.
3. **Human Review:** User confirms or edits values (including required monthly income).
4. **AI Analysis:** System runs retrieval + LLM analysis against the uploaded content.
5. **Decision Output:** UI presents verdict, projected savings, overlap/rights signals, and citations.

## Tech Stack

- **Frontend:** Next.js, React, TypeScript
- **Backend:** FastAPI, Pydantic
- **AI + Retrieval:** GLM integration (Ilmu/BigModel-compatible), PDF parsing, chunking, retrieval pipeline
- **Document Processing:** pypdf
- **Transport:** HTTP multipart uploads + JSON APIs

## Project Structure

- [PRD.md](PRD.md) - Product requirements and scope
- [backend](backend) - FastAPI services and AI/document pipeline
- [frontend](frontend) - Next.js product interface

## Setup

### Prerequisites

- Python 3.10+
- Node.js 20+

### 1) Install backend dependencies

```powershell
c:/Users/USER/Documents/policyclaw/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
```

### 2) Configure backend environment

Use [backend/.env.example](backend/.env.example) as reference. Key variables:

- `GLM_API_KEY=`
- `GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4`
- `GLM_MODEL=glm-5.1`
- `DEBUG=false`

### 3) Run backend

```powershell
c:/Users/USER/Documents/policyclaw/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Backend:

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

### 4) Install and run frontend

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Frontend:

- App: http://127.0.0.1:3000

## API Surface

### Current production flow

- `POST /api/extract-policy-profile` - Extract structured policy profile(s) from uploaded PDF(s)
- `POST /api/analyze` - Execute full analysis and return verdict, reasons, confidence, and citations

### FutureClaw simulator (F6, Wow Factor 2)

- `POST /v1/simulate/affordability` - 1000-run Monte Carlo premium projection; returns 3 scenario bands (optimistic / realistic / pessimistic) over 10 years
- `POST /v1/simulate/life-event` - 4 life-event scenarios (cancer / heart attack / disability / death) with covered / co-pay / out-of-pocket breakdown and GLM-generated narratives (EN + BM)

### Legacy compatibility endpoints

- `GET /health`
- `POST /v1/policies/upload`
- `POST /v1/simulate/premium`
- `POST /v1/verdict`

## Why This Matters

PolicyClaw converts insurance from a trust-heavy black box into a transparent decision system. The product goal is simple: faster, clearer, and more defensible policy decisions for everyday policyholders.

## Disclaimer

PolicyClaw provides decision support only and is not licensed financial advice.
