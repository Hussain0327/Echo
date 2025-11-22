# Echo - AI Data Scientist for Small Businesses

> Building an AI-powered analytics tool that turns messy business data into clear insights. Because small businesses deserve good data tools too.

**Status**: In Development - Phase 1 Complete
**Powered by**: DeepSeek 3.2, FastAPI, PostgreSQL, Redis
**Goal**: Transform 2-hour manual reports into 15-minute automated insights

---

## What I'm Building

Most small businesses drown in spreadsheets but can't afford a full-time data analyst. Echo is my solution to that problem.

**The core idea**:
- Upload your business data (Stripe exports, HubSpot CSVs, whatever you've got)
- Get accurate metrics calculated automatically (no LLM hallucinations on the math)
- Receive plain-English explanations powered by AI
- Ask follow-up questions in natural language

**Why "deterministic metrics + LLM narrative"?**
I don't trust LLMs to do calculations. They're great at explaining things, terrible at math. So I'm building it the right way:
- Calculate metrics using SQL/Python (accurate, testable)
- Use LLM (DeepSeek) only for explanations and insights
- No made-up numbers, just facts with context

---

## Current Status

### Phase 1 Complete (Data Ingestion)
What's working right now:
- CSV and Excel file upload via API
- Automatic schema detection (date, currency, email, URL, boolean, etc.)
- Data validation with helpful error messages
- All uploads stored in PostgreSQL with metadata
- 39 tests passing, 88% code coverage

Try it:
```bash
# Start the services
docker-compose up -d

# Upload a CSV file
curl -X POST "http://localhost:8000/api/v1/ingestion/upload/csv" \
  -F "file=@data/samples/revenue_sample.csv"

# Response includes detected schema and validation results
```

Example response:
```json
{
  "status": "valid",
  "schema_info": {
    "columns": {
      "date": {"data_type": "date"},
      "amount": {"data_type": "currency"},
      "customer_id": {"data_type": "string"}
    },
    "total_rows": 101
  }
}
```

### Next Up: Phase 2 (Analytics Engine)
What I'm building next:
- Revenue metrics (MRR, ARR, growth rate)
- Financial metrics (CAC, LTV, burn rate)
- Marketing metrics (conversion rates, funnel analysis)
- Metrics registry with testable calculations

---

## API Endpoints

### Health
```
GET  /                        Service info
GET  /api/v1/health           Basic health check
GET  /api/v1/health/db        Database health
GET  /api/v1/health/redis     Redis health
```

### Ingestion (Phase 1)
```
POST /api/v1/ingestion/upload/csv     Upload CSV file
POST /api/v1/ingestion/upload/excel   Upload Excel file
GET  /api/v1/ingestion/sources        List all uploaded sources
GET  /api/v1/ingestion/sources/{id}   Get source by ID
```

### API Documentation
```
GET  /api/v1/docs             Swagger UI
GET  /api/v1/redoc            ReDoc
```

---

## The Plan (5-6 Weeks)

I'm building this in 6 phases:

**Phase 0** - Foundation (Complete)
Docker environment, FastAPI + PostgreSQL + Redis, health checks

**Phase 1** - Data Ingestion (Complete)
File upload, schema detection, data validation, storage

**Phase 2** - Analytics Engine (Next)
MRR, CAC, LTV, conversion rates - the real numbers SMBs care about

**Phase 3** - Intelligence
LLM-powered insights, natural language Q&A

**Phase 4** - Evaluation
Time tracking, accuracy metrics, user feedback

**Phase 5** - Production Ready
Tests, CI/CD, monitoring, error handling

**Phase 6** - Polish
Documentation, demos, portfolio presentation

Full roadmap: See `/planning/` folder

---

## Tech Stack

**Why I chose these tools:**

- **FastAPI** - Fast, modern, auto-generates docs
- **PostgreSQL** - Reliable, handles complex queries
- **Redis** - Cache repeated calculations
- **DeepSeek** - Affordable, powerful LLM (OpenAI-compatible API)
- **Docker** - Consistent dev environment
- **Pandas** - Data processing workhorse

**Full stack:**
```
Backend:     FastAPI, Python 3.11
Database:    PostgreSQL 15 (async)
Cache:       Redis 7
AI/LLM:      DeepSeek 3.2
Testing:     pytest, pytest-cov (88% coverage)
Monitoring:  structlog, Prometheus
DevOps:      Docker, GitHub Actions
```

---

## How to Run This

### Prerequisites
- Docker & Docker Compose
- DeepSeek API key (or OpenAI key)



### Development Commands
```bash
# View logs
docker-compose logs app -f

# Run tests
docker-compose exec app pytest

# Run tests with coverage
docker-compose exec app pytest --cov=app

# Restart after code changes
docker-compose restart app

# Stop everything
docker-compose down
```

---

## Project Structure

```
Echo/
├── app/                    # Main application
│   ├── api/v1/            # API endpoints
│   │   ├── health.py      # Health checks
│   │   └── ingestion.py   # File upload endpoints
│   ├── core/              # Database, cache, config
│   ├── models/            # SQLAlchemy & Pydantic models
│   │   ├── data_source.py # Upload tracking model
│   │   └── schemas.py     # API schemas
│   └── services/          # Business logic
│       ├── schema_detector.py   # Auto-detect column types
│       ├── data_validator.py    # Validation engine
│       ├── ingestion.py         # Upload orchestration
│       └── llm/                 # DeepSeek integration (Phase 3)
├── tests/                 # Test suite (39 tests)
│   ├── api/              # API tests
│   └── services/         # Service tests
├── planning/              # Detailed phase docs
├── data/samples/          # Sample datasets
│   ├── revenue_sample.csv
│   ├── marketing_sample.csv
│   └── bad_data_sample.csv
├── docker-compose.yml     # Services orchestration
└── requirements.txt       # Python dependencies
```

---

## What Makes This Different

**Not another analytics dashboard**
This isn't trying to be Tableau. It's focused on answering specific questions SMB owners actually ask:
- "How much did we make this month?"
- "Which marketing channel is working?"
- "Are we spending too much to acquire customers?"

**Deterministic + AI hybrid**
Most "AI analytics" tools just throw everything at an LLM and hope. I'm being deliberate:
- Hard calculations in code (testable, accurate)
- LLM for explanation (context, recommendations)
- Best of both worlds

**Built for real businesses**
Every feature is designed around actual SMB needs:
- Works with messy data (helpful error messages)
- Connects to tools they already use (Stripe, HubSpot)
- Plain English, no jargon

---

## Metrics I'm Tracking

To prove this actually works, I'm measuring:

**Time saved**
Target: 2 hours manual -> 15 minutes automated (8x faster)

**User satisfaction**
Target: >4.0/5 rating on generated insights

**Accuracy**
Target: >90% match with expert analysis (using golden datasets)

**Code Quality**
Current: 88% test coverage, 39 passing tests

---

## Current Roadmap

### Phase 0: Foundation (Complete)
- [x] Docker environment
- [x] FastAPI + PostgreSQL + Redis
- [x] Health checks working
- [x] DeepSeek configured

### Phase 1: Ingestion (Complete)
- [x] CSV/Excel upload
- [x] Schema detection (date, currency, email, URL, boolean)
- [x] Data validation with helpful messages
- [x] Store uploads in PostgreSQL
- [x] 39 tests, 88% coverage

### Phase 2: Analytics (Next)
- [ ] Revenue metrics (MRR, ARR)
- [ ] Financial metrics (CAC, LTV)
- [ ] Marketing metrics (conversion rates)
- [ ] Metrics registry

### Phase 3: Intelligence (Upcoming)
- [ ] Report templates
- [ ] DeepSeek narrative generation
- [ ] Natural language Q&A

See `/planning/` for detailed plans.

---

## Development Log

**2025-11-22** - Phase 1 Complete
Built the entire data ingestion layer:
- Schema detector that auto-identifies column types (date, currency, email, URL, boolean)
- Validation engine with helpful error messages
- CSV and Excel upload endpoints
- All metadata stored in PostgreSQL
- 39 tests passing with 88% coverage

Files created: 12 new files, 7 modified
Ready for Phase 2: Analytics Engine

**2025-11-19** - Phase 0 Complete
Got the entire foundation working. FastAPI running, Docker containers healthy, all health checks passing. DeepSeek API key configured.

---

## Why I'm Building This

Small businesses are the backbone of the economy, but they're stuck with either:
1. Manual spreadsheet hell (hours of work, error-prone)
2. Enterprise tools they can't afford ($500+/month, too complex)

There's a gap for something simple, affordable, and actually useful. That's what Echo is.

Plus, this is a great way to showcase:
- Data engineering (pipelines, validation, ETL)
- Backend development (APIs, databases, caching)
- AI/ML application (practical LLM use, not just prompting)
- Product thinking (real user needs, measurable value)

---

## Want to Follow Along?

- Check `/planning/` for detailed phase documentation
- See `PHASE_1_COMPLETE.md` for what's done
- Read `WHATS_NEXT.md` for immediate next steps

---

## License

MIT - Build whatever you want with this

---

## Contact

Building in public. Questions? Feedback? Open an issue.

---

*Last updated: 2025-11-22*
*Current phase: Phase 2 - Analytics Engine*
*LLM: DeepSeek 3.2*
