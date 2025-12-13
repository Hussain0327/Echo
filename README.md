# Echo Analytics Platform

An analytics platform I built to turn messy business data into something useful. Upload a CSV, get metrics, see trends, ask questions in plain English.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![Tests](https://img.shields.io/badge/tests-238%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-78%25-blue)

**[Live Dashboard Demo](https://echo-analytics.streamlit.app)**

---

## The Problem

Small businesses have data everywhere - spreadsheets, exports, random CSVs. They need answers but don't have time to wrestle with formulas or learn BI tools. I wanted to build something that handles the messy parts automatically.

## What I Built

**Data Pipeline**: Ingest raw files, detect schemas, clean the mess (currency symbols, date formats, inconsistent booleans), validate quality, then calculate metrics.

**Analytics Layer**: 20+ business metrics computed deterministically. Revenue trends, cohort retention, customer segmentation, funnel analysis. All tested, all reproducible.

**Two Interfaces**:
- **Streamlit Dashboard** - KPIs, charts, drill-downs for BI-style analysis
- **Next.js Web App** - Chat interface where you ask questions in plain English, powered by an LLM that explains the numbers (but never calculates them - that's handled by tested Python code)

---

## Screenshots

### Streamlit Dashboard

| Overview | Revenue Analysis | Customer Segmentation |
|:--------:|:----------------:|:---------------------:|
| ![Dashboard](docs/screenshots/dashboard-overview.png) | ![Revenue](docs/screenshots/dashboard-revenue.png) | ![Customers](docs/screenshots/dashboard-customers.png) |

### Next.js Web App

| Metrics View | Chat Interface | Reports |
|:------------:|:--------------:|:-------:|
| ![Metrics](docs/screenshots/02-metrics-view.png) | ![Chat](docs/screenshots/03-chat-interface.png) | ![Reports](docs/screenshots/04-reports-page.png) |

---

## Technical Highlights

### Data Analytics and BI

**SQL Portfolio** - 10+ queries in `sql/analytics/` covering:
- CTEs and window functions (LAG, LEAD, NTILE, ROW_NUMBER)
- Cohort retention matrices
- RFM customer segmentation
- Funnel conversion analysis
- Time series with moving averages and anomaly detection

```sql
-- Month-over-month revenue growth
WITH monthly AS (
    SELECT DATE_TRUNC('month', transaction_date) AS month,
           SUM(amount) AS revenue
    FROM transactions
    GROUP BY 1
)
SELECT month, revenue,
       LAG(revenue) OVER (ORDER BY month) AS prev_month,
       ROUND((revenue - LAG(revenue) OVER (ORDER BY month)) /
             NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100, 2) AS growth_pct
FROM monthly;
```

**Jupyter Notebooks** - Four analysis notebooks in `notebooks/`:
- Cohort retention with heatmaps and survival curves
- Revenue forecasting with time series decomposition
- Customer segmentation using RFM and K-means
- A/B test analysis with z-tests and confidence intervals

**Streamlit Dashboard** - Multi-page app with KPI cards, revenue trends with 7-day moving averages, customer segment breakdowns, and interactive filters.

### Data Engineering

**ETL with Prefect** - Orchestrated flows for daily metric computation, incremental loads, and error handling.

**dbt Models** - Transformations organized into staging, intermediate, and mart layers. Incremental MRR calculations, customer lifetime aggregations.

**Data Quality with Great Expectations** - 26 validation rules catching nulls, duplicates, referential integrity issues, and schema drift before bad data hits the warehouse.

**Data Cleaning** - The `DataAutoFixer` service normalizes column names, parses mixed date formats, strips currency symbols, standardizes booleans, and flags outliers.

### Software Engineering

**FastAPI Backend** - REST API with structured routers for ingestion, metrics, chat, reports, experiments, and analytics. Request validation with Pydantic, async where it matters.

**Next.js Frontend** - TypeScript, Tailwind CSS, drag-and-drop file upload, real-time metric display, and a chat interface for conversational analytics.

**PostgreSQL + Redis** - Postgres for persistence, Redis for caching expensive metric calculations.

**238 Tests, 78% Coverage** - Unit tests for metrics calculations, integration tests for API endpoints, fixture-based test data.

**Docker Compose** - One command to spin up the full stack locally.

---

## Architecture

```
echo/
├── app/                      # FastAPI backend
│   ├── api/v1/               # REST endpoints
│   ├── services/             # Business logic
│   │   ├── metrics/          # Metric calculations
│   │   ├── experiments/      # A/B testing
│   │   └── data_profiler.py  # Data profiling
│   └── models/               # SQLAlchemy models
├── frontend/                 # Next.js web app (chat, uploads, reports)
├── dashboard/                # Streamlit BI dashboard
├── sql/                      # SQL query portfolio
├── notebooks/                # Analysis notebooks
├── orchestration/            # Prefect ETL flows
├── dbt/                      # dbt transformations
├── data_quality/             # Great Expectations
└── tests/                    # Test suite
```

| Layer | Tech |
|-------|------|
| API | FastAPI, Python 3.11 |
| Database | PostgreSQL 15, Redis 7 |
| Web App | Next.js 15, TypeScript, Tailwind |
| Dashboard | Streamlit, Plotly |
| ETL | Prefect 2.14 |
| Transformations | dbt 1.7 |
| Data Quality | Great Expectations 0.18 |

---

## Running It

### Dashboard (Streamlit)

Live at **[echo-analytics.streamlit.app](https://echo-analytics.streamlit.app)**

Or run locally:
```bash
pipx install streamlit --include-deps
pipx inject streamlit plotly
streamlit run dashboard/app.py
```

### Full Stack (Docker)

```bash
git clone https://github.com/Hussain0327/Echo_Data_Scientist.git
cd Echo_Data_Scientist
cp .env.example .env
# Add your DEEPSEEK_API_KEY or OPENAI_API_KEY

docker-compose up -d

# Frontend
cd frontend && npm install && npm run dev

# Open http://localhost:3000
```

### Notebooks

```bash
jupyter notebook notebooks/
```

---

## What I Learned

**Data cleaning is most of the work.** The `DataAutoFixer` went through five rewrites. Real data is messy in ways you don't expect until you see it.

**LLMs are bad at math.** I learned this the hard way. Now Python handles all calculations, and the LLM just explains results it's given. Much more reliable.

**Testing saves time.** 238 tests sounds like a lot, but they caught regressions constantly. Especially when refactoring the metrics engine.

---

## License

MIT
