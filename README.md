# Echo - AI Data Scientist for Small Businesses

> Building an AI-powered analytics tool that turns messy business data into clear insights. Because small businesses deserve good data tools too.

**Status**: In Development - Phase 5 In Progress (Frontend + Production Ready)
**Powered by**: DeepSeek 3.2, FastAPI, PostgreSQL, Redis, Next.js
**Goal**: Transform 2-hour manual reports into 15-minute automated insights
**Test Coverage**: 82% (190 tests passing)

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

### Phase 5 In Progress (Frontend + Production Ready)

Just built a complete React/Next.js frontend for Echo. Users can now upload files and get instant metrics through a clean web interface instead of just API calls.

**What's working:**
- Next.js 15 frontend with TypeScript and Tailwind CSS
- 3 pages: Home (file upload + metrics), Chat (talk to Echo), Reports (generate business reports)
- 3 reusable components: FileUpload, MetricsCard, ChatInterface
- Full API integration layer with error handling
- Responsive design with drag-and-drop file upload

**Current issue:**
Working through Codespaces networking configuration. The frontend and backend are running but need proper port forwarding setup to communicate. The backend CORS is configured for Codespaces URLs, just need to make ports public in the Ports panel.

**What's left for Phase 5:**
- Fix Codespaces port visibility (ports 3000 and 8000 need to be public)
- Test all three pages end-to-end
- CI/CD pipeline (GitHub Actions)
- Better error handling and logging
- Rate limiting and security headers
- Deploy to production (Railway for backend, Vercel for frontend)

See `/frontend/` for the new React app and `/FRONTEND_COMPLETE.md` for details.

### Phase 4 Complete (Evaluation & Metrics)
Built the entire evaluation system to track real impact. Now I can prove Echo actually saves time and delivers accurate insights.

**What's working now:**
- Session tracking: automatically records how long each task takes
- Time savings calculation: compares actual duration vs baseline (manual work)
- Feedback collection: users can rate insights and flag accuracy issues
- Analytics aggregation: total time saved, satisfaction ratings, accuracy rates
- Portfolio stats endpoint: generates showcase-ready impact metrics
- Telemetry middleware: logs every API call with timing and status

**Test it yourself:**
```bash
# Run the demo script
./test_phase4.sh

# Or manually start a session
curl -X POST "http://localhost:8000/api/v1/analytics/session/start" \
  -H "Content-Type: application/json" \
  -d '{"task_type": "report_generation", "baseline_time_seconds": 7200}'

# End the session (calculates time saved)
curl -X POST "http://localhost:8000/api/v1/analytics/session/end" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID"}'

# Submit feedback
curl -X POST "http://localhost:8000/api/v1/feedback" \
  -H "Content-Type: application/json" \
  -d '{"interaction_type": "report", "rating": 5, "accuracy_rating": "correct"}'

# View your impact stats
curl "http://localhost:8000/api/v1/analytics/portfolio" | python3 -m json.tool
```

The portfolio endpoint returns headline metrics like:
- "Saved users an average of 1.85 hours per analysis"
- "4.3/5 average user satisfaction from 150 ratings"
- "94% accuracy on 200 insights"

Perfect for demonstrating real impact in a portfolio.

### Phase 3 Complete (Conversational AI + Reports)
Built "Echo" - a conversational data consultant that generates structured business reports. Upload a CSV, get professional analysis with metrics and narratives.

**What's working:**
- Conversational chat interface with DeepSeek
- Session management (maintains context across messages)
- Structured report generation (3 templates: Revenue, Marketing, Financial)
- Automatic metrics calculation + AI-generated narratives
- Report storage and retrieval in PostgreSQL
- McKinsey-style persona - direct, insightful, no jargon
- Guardrails to stay on topic and never make up numbers

Try the chat interface:
```bash
# Start the services
docker-compose up -d

# Chat with Echo
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi!"}'

# Chat with your data
curl -X POST "http://localhost:8000/api/v1/chat/with-data" \
  -F "message=How's my revenue looking?" \
  -F "file=@data/samples/revenue_sample.csv"
```

Try the report generation:
```bash
# Generate a revenue health report
curl -X POST "http://localhost:8000/api/v1/reports/generate?template_type=revenue_health" \
  -F "file=@data/samples/revenue_sample.csv"

# Generate a marketing funnel report
curl -X POST "http://localhost:8000/api/v1/reports/generate?template_type=marketing_funnel" \
  -F "file=@data/samples/marketing_sample.csv"

# List available templates
curl http://localhost:8000/api/v1/reports/templates

# List your reports
curl http://localhost:8000/api/v1/reports

# Get a specific report
curl http://localhost:8000/api/v1/reports/{report_id}
```

Each report includes:
- Executive summary (2-3 sentence overview)
- Key findings (3-5 data-driven insights)
- Detailed analysis (patterns, trends, anomalies)
- Recommendations (2-4 specific, actionable next steps)

The reports are stored in PostgreSQL, so you can retrieve them later or compare across time periods.

### Phase 2 Complete (Deterministic Analytics)
The metrics engine is done. 20 business metrics, all deterministic math, no AI hallucinations.

**What's working:**
- 7 revenue metrics (Total Revenue, MRR, ARR, Growth Rate, AOV, Revenue by Period/Product)
- 6 financial metrics (CAC, LTV, LTV:CAC Ratio, Gross Margin, Burn Rate, Runway)
- 7 marketing metrics (Conversion Rate, Channel/Campaign Performance, CPL, ROAS, Lead Velocity, Funnel)
- Time-series analysis (trends, growth, period comparisons)
- 184 tests passing, 83% coverage

```bash
# Calculate revenue metrics from a CSV
curl -X POST "http://localhost:8000/api/v1/metrics/calculate/revenue" \
  -F "file=@data/samples/revenue_sample.csv"
```

All numbers verified against manual calculations. Pure pandas math, no AI involved.

---

## API Endpoints

### Analytics (Phase 4) - Track Time & Impact
```
POST /api/v1/analytics/session/start      Start tracking a session
POST /api/v1/analytics/session/end        End session and calculate time saved
GET  /api/v1/analytics/session/{id}       Get specific session details
GET  /api/v1/analytics/sessions           List all user sessions
GET  /api/v1/analytics/time-savings       Time savings statistics
GET  /api/v1/analytics/satisfaction       User satisfaction statistics
GET  /api/v1/analytics/accuracy           Accuracy statistics
GET  /api/v1/analytics/usage              Usage patterns and metrics
GET  /api/v1/analytics/overview           Complete analytics overview
GET  /api/v1/analytics/portfolio          Portfolio-ready impact metrics
```

### Feedback (Phase 4) - Collect User Ratings
```
POST /api/v1/feedback                     Submit feedback and ratings
GET  /api/v1/feedback/{id}                Get specific feedback
GET  /api/v1/feedback                     List all user feedback
GET  /api/v1/feedback/report/{id}         Get feedback for a specific report
```

### Reports (Phase 3) - Structured Business Reports
```
GET  /api/v1/reports/templates            List available report templates
GET  /api/v1/reports/templates/{type}     Get template details
POST /api/v1/reports/generate             Generate report from CSV + template
GET  /api/v1/reports                      List user's reports
GET  /api/v1/reports/{id}                 Get specific report
DELETE /api/v1/reports/{id}               Delete report
```

### Chat (Phase 3) - Talk to Echo
```
POST /api/v1/chat                    Send a message to Echo
POST /api/v1/chat/with-data          Chat + upload data in one call
POST /api/v1/chat/load-data          Load data into existing session
GET  /api/v1/chat/history/{id}       Get conversation history
DELETE /api/v1/chat/session/{id}     Clear a session
GET  /api/v1/chat/sessions           List all active sessions
```

### Metrics (Phase 2) - Deterministic Calculations
```
GET  /api/v1/metrics/available           List all available metrics
POST /api/v1/metrics/calculate/csv       Calculate any metrics from CSV
POST /api/v1/metrics/calculate/revenue   Revenue metrics only
POST /api/v1/metrics/calculate/marketing Marketing metrics only
POST /api/v1/metrics/trend               Trend analysis on a column
POST /api/v1/metrics/growth              Growth analysis over time
```

### Ingestion (Phase 1) - Data Upload
```
POST /api/v1/ingestion/upload/csv     Upload CSV file
POST /api/v1/ingestion/upload/excel   Upload Excel file
GET  /api/v1/ingestion/sources        List all uploaded sources
GET  /api/v1/ingestion/sources/{id}   Get source by ID
```

### Health
```
GET  /                        Service info
GET  /api/v1/health           Basic health check
GET  /api/v1/health/db        Database health
GET  /api/v1/health/redis     Redis health
```

### API Documentation
```
GET  /docs                    Swagger UI
GET  /redoc                   ReDoc
```

---

## The Plan (5-6 Weeks)

I'm building this in 6 phases:

**Phase 0** - Foundation (Complete)
Docker environment, FastAPI + PostgreSQL + Redis, health checks

**Phase 1** - Data Ingestion (Complete)
File upload, schema detection, data validation, storage

**Phase 2** - Analytics Engine (Complete)
20 metrics: MRR, ARR, CAC, LTV, conversion rates, channel performance, funnel analysis

**Phase 3** - Intelligence (Complete)
LLM-powered insights, natural language Q&A, structured report generation

**Phase 4** - Evaluation (Complete)
Time tracking, accuracy metrics, user feedback, portfolio stats

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
Frontend:    Next.js 15, React, TypeScript, Tailwind CSS
Backend:     FastAPI, Python 3.11
Database:    PostgreSQL 15 (async)
Cache:       Redis 7
AI/LLM:      DeepSeek 3.2
Testing:     pytest, pytest-cov (82% coverage)
Monitoring:  structlog, Prometheus
DevOps:      Docker, GitHub Actions
```

---

## How to Run This

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- DeepSeek API key (or OpenAI key)

### Quick Start

**1. Start the backend:**
```bash
docker-compose up -d
```

**2. Start the frontend:**
```bash
cd frontend
npm install
npm run dev
```

**3. Open your browser:**
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/api/v1/docs

**Note for Codespaces users:**
If running in GitHub Codespaces, make sure ports 3000 and 8000 are set to **Public** visibility in the Ports panel. The frontend needs to access the backend via the public Codespaces URL.

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
├── frontend/               # React/Next.js frontend (Phase 5)
│   ├── app/               # Next.js App Router pages
│   │   ├── page.tsx       # Home (file upload + metrics)
│   │   ├── chat/page.tsx  # Chat with Echo
│   │   └── reports/page.tsx # Report generation
│   ├── components/        # Reusable components
│   │   ├── FileUpload.tsx # Drag & drop upload
│   │   ├── MetricsCard.tsx # Metric display
│   │   └── ChatInterface.tsx # Chat UI
│   ├── lib/api.ts         # API service layer
│   ├── types/index.ts     # TypeScript definitions
│   └── .env.local         # Frontend config
├── app/                    # Backend application
│   ├── api/v1/            # API endpoints
│   │   ├── health.py      # Health checks
│   │   ├── ingestion.py   # File upload endpoints
│   │   ├── metrics.py     # Metrics calculation endpoints
│   │   ├── chat.py        # Conversational AI endpoints (Phase 3)
│   │   ├── reports.py     # Report generation endpoints (Phase 3)
│   │   ├── analytics.py   # Time tracking & stats endpoints (Phase 4)
│   │   └── feedback.py    # User feedback endpoints (Phase 4)
│   ├── core/              # Database, cache, config
│   ├── middleware/        # Request/response processing
│   │   └── telemetry.py   # Logs all API calls with timing (Phase 4)
│   ├── models/            # SQLAlchemy & Pydantic models
│   │   ├── data_source.py # Upload tracking model
│   │   ├── report.py      # Report storage model
│   │   ├── usage_metric.py # Session tracking model (Phase 4)
│   │   ├── feedback.py    # User feedback model (Phase 4)
│   │   └── schemas.py     # API schemas
│   └── services/          # Business logic
│       ├── schema_detector.py   # Auto-detect column types
│       ├── data_validator.py    # Validation engine
│       ├── ingestion.py         # Upload orchestration
│       ├── metrics/             # Deterministic analytics (Phase 2)
│       │   ├── base.py          # BaseMetric, MetricResult
│       │   ├── engine.py        # MetricsEngine orchestrator
│       │   ├── registry.py      # Metric discovery
│       │   ├── revenue.py       # 7 revenue metrics
│       │   ├── financial.py     # 6 financial metrics
│       │   ├── marketing.py     # 7 marketing metrics
│       │   └── timeseries.py    # Time-series utilities
│       ├── llm/                 # Conversational AI (Phase 3)
│       │   ├── conversation.py  # Chat service, session management
│       │   ├── context_builder.py # Formats data/metrics for LLM
│       │   └── prompts/
│       │       └── consultant.py # Echo's persona and guardrails
│       ├── reports/             # Report generation (Phase 3)
│       │   ├── templates.py     # Report templates (Revenue, Marketing, Financial)
│       │   └── generator.py     # Report generation service
│       └── analytics/           # Evaluation & tracking (Phase 4)
│           ├── tracking.py      # Session time tracking
│           ├── feedback.py      # Feedback collection
│           └── aggregator.py    # Stats aggregation
├── tests/                 # Test suite (190 tests, 82% coverage)
│   ├── api/              # API tests
│   │   ├── test_analytics.py   # Analytics API tests (11 tests)
│   │   └── test_feedback.py    # Feedback API tests (8 tests)
│   └── services/         # Service tests
│       ├── metrics/      # Metrics tests (75 tests)
│       ├── llm/          # Conversation tests (31 tests)
│       └── reports/      # Report tests (16 tests)
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

Now that Phase 4 is done, I can actually track real impact metrics:

**Time saved**
Target: 2 hours manual -> 15 minutes automated (8x faster)
Currently tracking: session duration, baseline comparison, total time saved per user

**User satisfaction**
Target: >4.0/5 rating on generated insights
Currently tracking: ratings per interaction type, rating distribution, average satisfaction

**Accuracy**
Target: >90% match with expert analysis
Currently tracking: user validation (correct/incorrect/partially correct), accuracy rate

**Usage patterns**
Tracking: most-used metrics, sessions per day, reports generated, chat interactions

**Code Quality**
Current: 82% test coverage, 190 passing tests

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

### Phase 2: Analytics (Complete)
- [x] Revenue metrics (Total, MRR, ARR, Growth, AOV, by Period, by Product)
- [x] Financial metrics (CAC, LTV, LTV:CAC, Gross Margin, Burn Rate, Runway)
- [x] Marketing metrics (Conversion, Channel, Campaign, CPL, ROAS, Velocity, Funnel)
- [x] Time-series utilities (trends, growth, comparisons)
- [x] Metrics API endpoints

### Phase 3: Intelligence (Complete)
- [x] Conversational chat interface with DeepSeek
- [x] Echo persona (McKinsey-style data consultant)
- [x] Session management and conversation history
- [x] Data context injection (metrics auto-calculated)
- [x] Guardrails (stays on topic, never fabricates numbers)
- [x] Report templates (Revenue Health, Marketing Funnel, Financial Overview)
- [x] Structured report generation (metrics + AI narratives)
- [x] Report storage and retrieval in PostgreSQL
- [x] 16 new tests for reports, 87% coverage on generator

### Phase 4: Evaluation (Complete)
- [x] Session tracking with start/end time
- [x] Time savings calculation (baseline vs actual)
- [x] Feedback collection (ratings + accuracy validation)
- [x] Analytics aggregation (time, satisfaction, accuracy, usage)
- [x] Portfolio stats endpoint with headline metrics
- [x] Telemetry middleware (logs all requests with timing)
- [x] 19 new tests (11 analytics + 8 feedback)
- [x] Test script for manual testing

### Phase 5-6: What's Left
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Better error handling and logging
- [ ] Rate limiting and security headers
- [ ] Load testing and performance optimization
- [ ] Documentation polish
- [ ] Demo video and screenshots
- [ ] Deploy to production (Railway/Render)

See `/planning/` for detailed plans.

---

## Development Log

**2025-11-25** - Phase 5 Started: Frontend Development
Started building the React/Next.js frontend to give Echo a proper web interface. Users can now interact with Echo through a clean UI instead of just API calls.

What I built:
- Complete Next.js 15 app with TypeScript and Tailwind CSS
- 3 pages: Home (upload + metrics), Chat (conversational interface), Reports (generate business reports)
- 3 reusable components: FileUpload (drag & drop), MetricsCard (metric display), ChatInterface (chat UI)
- API service layer in lib/api.ts with full error handling
- TypeScript type definitions for all API responses
- Responsive design that works on mobile and desktop

Current challenge:
Working through Codespaces networking configuration. The frontend and backend are both running, but need proper port forwarding to communicate. Backend CORS is configured for Codespaces URLs, just need to make ports 3000 and 8000 public in the Ports panel.

Next steps:
- Fix Codespaces port visibility
- Test all three pages end-to-end with real data
- Polish the UI and add loading states
- Deploy frontend to Vercel, backend to Railway

Files created: 10 new frontend files (pages, components, lib, types)
Configuration added: .devcontainer/devcontainer.json for auto port forwarding

This brings Echo much closer to being a real product people can use. Phase 5 in progress.

**2025-11-25** - Phase 4 Complete: Evaluation & Metrics
Built the entire evaluation system to prove Echo actually delivers value. Now I can track real impact and generate portfolio-ready stats.

What I built:
- UsageMetric model: tracks session start/end, calculates duration and time saved
- Feedback model: collects ratings (1-5), accuracy validation, and text feedback
- TrackingService: manages session lifecycle and time calculations
- FeedbackService: handles feedback submission and retrieval
- AnalyticsAggregator: aggregates stats across time savings, satisfaction, accuracy, and usage
- TelemetryMiddleware: logs every API request with timing data
- 10 new analytics endpoints (session tracking, stats, portfolio)
- 4 new feedback endpoints (submit, retrieve, list)
- 19 new tests, all passing (11 for analytics, 8 for feedback)
- Test script for manual testing (test_phase4.sh)

The portfolio endpoint generates showcase-ready headlines like:
- "Saved users an average of 1.85 hours per analysis"
- "4.3/5 average user satisfaction from 150 ratings"
- "94% accuracy on 200 insights"

Now I can actually prove the impact metrics I've been targeting:
- Time savings: automatically calculated from session tracking
- Satisfaction: real user ratings aggregated by interaction type
- Accuracy: user validation on insights (correct/partially/incorrect)
- Usage patterns: most-used metrics, sessions per day, reports generated

Total test coverage now at 82% with 190 tests passing.

Next up: Phase 5 (production readiness - CI/CD, error handling, deployment).

**2025-11-25** - Phase 3 Complete: Report Generation
Finished the report generation system. You can now upload a CSV and get a professional business report with metrics and AI-generated narratives.

What I built:
- Report database model with versioning and status tracking
- 3 report templates: Revenue Health, Marketing Funnel, Financial Overview
- Report generator service that calculates metrics + generates narratives
- 5 new API endpoints for report templates, generation, listing, retrieval, deletion
- 16 new tests, all passing, 87% coverage on report generator

Each template defines required metrics, required columns, and sections (executive summary, key findings, detailed analysis, recommendations). The generator validates data, calculates all metrics deterministically, then uses DeepSeek to generate natural language narratives for each section. Reports are stored in PostgreSQL with full metadata.

Tested it live:
- Generated revenue report: correctly identified -64% MoM decline, concentration risk in Enterprise product
- Generated marketing report: calculated 10.21% conversion rate, identified Email as best cost-per-conversion at $1.74
- Both reports stored and retrievable via API

Files created: 1 model, 3 services, 1 API endpoint, 3 test files
Files modified: 3 (imports and router registration)

Phase 3 is done. Next up: Phase 4 (evaluation metrics, accuracy tracking).

**2025-11-24** - Phase 3 Started: Conversational AI
Built "Echo" - the conversational data consultant interface:
- Created the McKinsey-style persona with guardrails
- Built conversation service with DeepSeek integration
- Added session management (tracks conversation history per user)
- Built data context builder that formats metrics for the LLM
- Created 6 new chat API endpoints
- 31 new tests, conversation service at 99% coverage

The idea is simple: you already have accurate metrics from Phase 2, now Echo explains them in plain English. Upload your data, ask questions, get insights. Echo never makes up numbers - it only uses the deterministic metrics we already calculated.

Key design decisions:
- LLM never does math, only explains
- Sessions maintain context across messages
- Auto-calculates all available metrics when you load data
- Politely redirects off-topic questions back to business analytics

Files created: conversation.py, context_builder.py, consultant.py (persona), chat.py (API)

**2025-11-23** - Phase 2 Complete
Built the entire deterministic analytics layer:
- 20 business metrics across revenue, financial, and marketing categories
- Time-series analysis with trend detection and growth calculations
- 6 new API endpoints for metric calculation
- All metrics verified against manual calculations - pure pandas math, no AI
- 124 tests passing with 88% coverage

Key metrics working:
- Revenue: $190,100.50 total from sample data (verified)
- Marketing: 10.21% conversion rate across 17,254 leads (verified)
- Channel analysis: Email cheapest at $1.74/conversion, LinkedIn best rate at 17.45%

Files created: 8 new service files, 5 test files, 1 API endpoint file
Ready for Phase 3: LLM narrative generation

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
- See `PHASE_2_COMPLETE.md` for the latest completed work
- Read `WHATS_NEXT.md` for immediate next steps

---

## License

MIT - Build whatever you want with this

---

## Contact

Building in public. Questions? Feedback? Open an issue.

---

*Last updated: 2025-11-25*
*Current phase: Phase 5 In Progress (Frontend + Production Ready)*
*Test coverage: 82% (190 tests passing)*
*LLM: DeepSeek 3.2*
*Frontend: Next.js 15 + TypeScript + Tailwind*
