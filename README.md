# Job Market Intelligence Platform

End-to-end data pipeline that scrapes 10,000+ job descriptions, extracts skills via NLP,
clusters roles using unsupervised learning, forecasts skill demand trends, and analyzes
resume skill gaps — surfaced in a React web app with a FastAPI backend.

## What it demonstrates

| Area | Implementation |
|---|---|
| Data collection | Adzuna REST API + USAJobs.gov API + synthetic data fallback |
| Web scraping | Rate-limited, retry-backed HTTP with `tenacity` |
| NLP | spaCy `PhraseMatcher` against ESCO/custom skills taxonomy |
| Feature engineering | Weekly skill frequency time-series from raw postings |
| Unsupervised learning | `sentence-transformers` → UMAP → HDBSCAN role clustering |
| Time-series forecasting | Holt-Winters exponential smoothing (statsmodels) — 26-week projections per skill |
| Resume analysis | Skill extraction + demand-weighted readiness score + market percentile |
| Frontend | React + Vite + TypeScript + Framer Motion + Plotly |
| Backend API | FastAPI serving parquet data as JSON |

---

## Quick start (mock data, no API keys needed)

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 2. Install Python dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Install Node dependencies
npm install
npm --prefix web install

# 4. Run the full pipeline with 500 synthetic jobs
python pipeline.py --all --mock --max-jobs 500

# 5. Start the app (API + frontend together)
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

---

## Quick start (real data)

```bash
# 1. Copy and fill in your credentials
cp .env.example .env
# Edit .env with your Adzuna keys (free at https://developer.adzuna.com/)

# 2. Scrape up to 10,000 jobs
python pipeline.py --scrape --max-jobs 10000

# 3. Run remaining pipeline steps
python pipeline.py --clean
python pipeline.py --extract
python pipeline.py --cluster
python pipeline.py --forecast

# 4. Start the app
npm run dev
```

---

## Running the servers separately

```bash
npm run dev:api   # FastAPI on http://localhost:8000
npm run dev:web   # React on  http://localhost:5173
```

---

## Pipeline steps

```
python pipeline.py --scrape   # fetch raw job postings → data/raw/*.jsonl
python pipeline.py --clean    # HTML strip + dedupe   → data/processed/jobs_clean.parquet
python pipeline.py --extract  # skill extraction      → data/processed/jobs_with_skills.parquet
python pipeline.py --cluster  # UMAP + HDBSCAN        → data/processed/jobs_clustered.parquet
python pipeline.py --forecast # Holt-Winters forecasts → data/processed/forecasts.parquet
python pipeline.py --all      # run all steps in order
```

---

## Pages

- **Overview** — KPI cards, top 30 skills bar chart, weekly posting volume
- **Skill Heatmap** — cluster × skill frequency heatmap with cluster filter
- **Role Clusters** — interactive 2D UMAP scatter plot coloured by cluster
- **Skill Trends** — historical weekly counts + 26-week forecast with confidence band + rising/falling badges
- **Resume Analyzer** — upload a PDF or DOCX resume, select a target role, and get:
  - Demand-weighted readiness score (0–100) and gauge
  - Market percentile vs. analysed job postings
  - Skills present / missing with demand classification (High / Medium / Low)
  - Top 10 recommended skills table with trend indicators
  - "Ahead of the curve" section for skills you already have that are trending up

---

## Project structure

```
├── api/
│   ├── main.py               # FastAPI app + CORS
│   ├── data.py               # cached parquet loaders + NLP singleton
│   └── routers/              # overview, heatmap, clusters, trends, resume
├── web/
│   └── src/
│       ├── components/       # Nav, MetricCard, Badge, SkillTable, EmptyState
│       ├── pages/            # Overview, SkillHeatmap, RoleClusters, SkillTrends, ResumeAnalyzer
│       └── lib/api.ts        # typed fetch wrappers
├── data/
│   ├── raw/                  # scraped JSONL batches (git-ignored)
│   ├── processed/            # parquet files (git-ignored)
│   └── skills/               # ESCO taxonomy CSV (optional)
├── src/
│   ├── scraper/              # adzuna.py, usajobs.py, mock.py
│   ├── nlp/                  # cleaner.py, extractor.py
│   ├── clustering/           # roles.py
│   ├── forecasting/          # demand.py
│   ├── analyzer/             # resume.py, gap.py
│   └── logger.py
├── tests/                    # 58 pytest unit tests
├── pipeline.py               # CLI orchestrator
├── requirements.txt          # Python deps
└── package.json              # npm dev scripts (concurrently)
```

---

## Environment variables

Copy `.env.example` to `.env` and fill in values as needed:

```
ADZUNA_APP_ID=your_app_id
ADZUNA_API_KEY=your_api_key
USAJOBS_API_KEY=your_usajobs_key   # optional — public jobs work without it
LOG_LEVEL=INFO                     # DEBUG for verbose output
```

---

## Running tests

```bash
pytest tests/ -v
# 58 tests across cleaner, extractor, forecasting, gap analyzer, resume parser
```

---

## Notes

- **ESCO taxonomy**: for higher-quality skill extraction, download the Level 3 skills CSV from [esco.ec.europa.eu](https://esco.ec.europa.eu/en/use-esco/download) and place it at `data/skills/esco_skills.csv` with a `preferredLabel` column. The bundled fallback covers ~60 common tech/data skills.
- **Adzuna free tier**: 250 calls/day × 50 results/page, capped at 50 pages per query — enough to collect thousands of jobs in a single run.
- **Embedding cache**: sentence-transformer embeddings are cached to `data/processed/embeddings.npy` (invalidated automatically when data changes) so re-clustering skips the expensive encoding step.
- **Forecasting**: uses Holt-Winters additive-trend exponential smoothing (`statsmodels`). No Stan/C++ compiler required.
- **Resume analyzer**: works with text-based PDFs and DOCX files. Scanned/image PDFs require conversion to DOCX first.
- **Bundle size**: plotly.js is large (~1.5 MB gzipped). Consider lazy-loading chart pages if initial load time matters.
