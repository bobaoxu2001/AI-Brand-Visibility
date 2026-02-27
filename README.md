# AI Brand Visibility Tracker (GEO / Share of Model)

Production-style end-to-end project for measuring how major LLMs recommend EV brands (Tesla, Rivian, Lucid), and turning raw generations into executive-facing analytics.

---

## Why this project matters

Traditional marketing teams optimize for SEO.  
Modern teams also need **GEO (Generative Engine Optimization)**: how often and in what tone LLMs recommend your brand.

This repository implements a full stack:
- **Data generation** from real LLM APIs
- **Structured extraction** via LLM-as-a-judge
- **SQL analytics views**
- **Interactive enterprise dashboard** (Next.js + Tremor)

---

## Tech stack

### Backend / Data
- Python 3.11+
- `asyncio`
- OpenAI async SDK
- Anthropic async SDK
- `python-dotenv`
- `sqlite3`
- `pydantic`

### Frontend
- Next.js 14 (App Router)
- React
- Tailwind CSS
- Tremor
- better-sqlite3

---

## Repository structure

```text
.
├── pipeline/
│   ├── 1_generate_prompts.py
│   ├── 2_fetch_llm_responses.py
│   ├── 3_evaluate_responses.py
│   ├── 4_create_views.py
│   ├── config.py
│   └── db.py
├── dashboard/
│   ├── app/
│   │   ├── api/analytics/route.ts
│   │   └── page.tsx
│   └── lib/db.ts
├── docs/
│   └── STRATEGIC_INSIGHTS.md
├── sql/
│   └── query_templates.sql
├── scripts/
│   └── run_pipeline_end_to_end.sh
├── .env.example
├── requirements.txt
└── visibility_data.db
```

---

## Data model

Core tables:
- `prompts(id, category, prompt_text)`
- `raw_responses(id, prompt_id, model_name, raw_text, timestamp, status, error_message)`
- `parsed_metrics(id, response_id, top_brand, sentiment, key_features)`

Analytics views:
- `view_share_of_model`: brand win-rate (%) by source model
- `view_brand_sentiment`: avg sentiment by source model and brand

---

## Quickstart

### 1) Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

Optional tuning:
- `MAX_CONCURRENCY`
- `REQUEST_DELAY_SECONDS`

### 2) Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 3) One-click pipeline run

```bash
bash scripts/run_pipeline_end_to_end.sh
```

This executes:
1. prompt generation (`--reset`)
2. raw response ingestion (OpenAI + Anthropic)
3. judge extraction (`--force`)
4. SQL view creation

---

## Manual run commands (step-by-step)

```bash
python3 pipeline/1_generate_prompts.py --reset
python3 pipeline/2_fetch_llm_responses.py
python3 pipeline/3_evaluate_responses.py --force
python3 pipeline/4_create_views.py
```

---

## Launch dashboard

```bash
cd dashboard
npm install
npm run dev
```

Open: `http://localhost:3000`

### Dashboard walkthrough checklist
1. In header, use **Model Selector** to choose `gpt-4o-mini` or `claude-3-haiku-20240307`.
2. Verify KPI cards:
   - **Total Analyzed**
   - **Top Recommended Brand**
3. Inspect **Share of Voice %** bar chart for brand win-rate distribution.
4. Inspect **Brand Sentiment** donut chart + sentiment list.
5. Switch model again and confirm charts/KPIs update accordingly.

---

## SQL query templates

See `sql/query_templates.sql` for copy-ready analysis queries.

Useful quick checks:
```sql
SELECT COUNT(*) FROM prompts;
SELECT model_name, COUNT(*) FROM raw_responses WHERE status='success' GROUP BY model_name;
SELECT top_brand, COUNT(*) FROM parsed_metrics GROUP BY top_brand ORDER BY COUNT(*) DESC;
SELECT * FROM view_share_of_model ORDER BY model_name, win_rate_pct DESC;
```

---

## Interview narrative (talk track)

Use this project to show both engineering depth and strategic thinking:

1. **Business framing**
   - “I built a GEO observability pipeline to measure AI recommendation share by brand.”

2. **Pipeline architecture**
   - “I designed async multi-model ingestion, then normalized free text into structured metrics via judge-model parsing.”

3. **Data quality & reliability**
   - “The system has retry/backoff, concurrency controls, idempotent upserts, and view-level aggregation for BI consumption.”

4. **Decision impact**
   - “The final dashboard surfaces model-specific recommendation bias and sentiment, enabling messaging and content strategy decisions.”

### Resume-ready bullet
> Engineered an end-to-end LLM visibility tracking pipeline (Python, SQLite, Next.js, Tremor) to analyze recommendation share and sentiment across 200+ real AI responses, enabling GEO strategy decisions for EV brands.

---

## Notes on security

- Never commit `.env` to git.
- Rotate API keys if they were ever shared in plaintext.
- Consider adding budget/rate controls for production usage.
