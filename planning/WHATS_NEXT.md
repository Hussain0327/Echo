# What's Next

**Current Status**: Phase 1 Complete
**Next Phase**: Phase 2 - Deterministic Analytics Layer
**Previous**: See `PHASE_1_COMPLETE.md` for what was built

---

## Where We Left Off

Phase 1 is complete. The data ingestion layer is fully functional:
- CSV/Excel upload endpoints working
- Schema detection identifies column types (date, currency, email, etc.)
- Validation engine provides helpful error messages
- All uploads stored in PostgreSQL
- 39 tests passing, 88% coverage

You can now upload data files and get back structured schema information with validation feedback.

---

## What We Need to Do: Phase 2

Phase 2 builds the analytics engine - the deterministic calculations that form the foundation of Echo's value. No LLM involvement here. Just accurate, testable math.

### Core Principle

```
Raw Data -> Deterministic Metrics -> (Later: LLM Narrative)
             ^^^^^^^^^^^^^^^^^
             Phase 2 builds this
```

### Deliverables

1. **Metrics Engine Architecture**
   - Base metric class with standard interface
   - Metric result model (value, unit, period, metadata)
   - Metric registry for discovery

2. **Revenue Metrics**
   - Total Revenue
   - MRR (Monthly Recurring Revenue)
   - ARR (Annual Recurring Revenue)
   - Revenue Growth Rate (MoM, YoY)

3. **Financial Metrics**
   - CAC (Customer Acquisition Cost)
   - LTV (Lifetime Value)
   - LTV:CAC Ratio
   - Burn Rate

4. **Marketing Metrics**
   - Conversion Rate
   - Funnel Analysis (leads -> customers)
   - Channel Performance

5. **Time-Series Utilities**
   - Period aggregation (daily, weekly, monthly)
   - Period-over-period comparisons

---

## Quick Start for Phase 2

### Step 1: Read the Plan
Open: `/planning/03_PHASE_2_ANALYTICS_LAYER.md`

### Step 2: First Task - Base Metric Class

Create `app/services/metrics/base.py`:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd
from pydantic import BaseModel
from datetime import datetime


class MetricResult(BaseModel):
    metric_name: str
    value: float
    unit: str  # "$", "%", "count"
    period: str  # "2024-01", "Q1 2024"
    metadata: Dict[str, Any] = {}
    calculated_at: datetime = datetime.now()


class MetricDefinition(BaseModel):
    name: str
    display_name: str
    description: str
    category: str  # "revenue", "financial", "marketing"
    unit: str
    formula: str
    required_columns: List[str]


class BaseMetric(ABC):

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.validate_data()

    @abstractmethod
    def calculate(self) -> MetricResult:
        pass

    @abstractmethod
    def get_definition(self) -> MetricDefinition:
        pass

    def validate_data(self):
        definition = self.get_definition()
        missing = [col for col in definition.required_columns if col not in self.df.columns]
        if missing:
            raise ValueError(f"Missing columns for {definition.name}: {missing}")
```

### Step 3: First Metric - Total Revenue

Create `app/services/metrics/revenue.py`:

```python
import pandas as pd
from app.services.metrics.base import BaseMetric, MetricResult, MetricDefinition


class TotalRevenue(BaseMetric):

    def get_definition(self) -> MetricDefinition:
        return MetricDefinition(
            name="total_revenue",
            display_name="Total Revenue",
            description="Sum of all revenue in the period",
            category="revenue",
            unit="$",
            formula="SUM(amount)",
            required_columns=["amount"]
        )

    def calculate(self, period: str = None) -> MetricResult:
        total = self.df["amount"].sum()
        return MetricResult(
            metric_name="total_revenue",
            value=round(total, 2),
            unit="$",
            period=period or "all"
        )
```

### Step 4: Test It

```bash
docker-compose exec app python
>>> import pandas as pd
>>> from app.services.metrics.revenue import TotalRevenue
>>> df = pd.read_csv('data/samples/revenue_sample.csv')
>>> metric = TotalRevenue(df)
>>> result = metric.calculate()
>>> print(f"Total Revenue: ${result.value:,.2f}")
```

---

## Phase 2 Task Checklist

### Task 1: Metrics Architecture (Day 1)
- [ ] Create `app/services/metrics/` directory
- [ ] Create `base.py` with BaseMetric, MetricResult, MetricDefinition
- [ ] Create `registry.py` for metric discovery
- [ ] Write tests for base classes

### Task 2: Revenue Metrics (Day 1-2)
- [ ] TotalRevenue
- [ ] MRR (Monthly Recurring Revenue)
- [ ] ARR (Annual Recurring Revenue)
- [ ] RevenueGrowthRate
- [ ] Tests for each metric

### Task 3: Financial Metrics (Day 2-3)
- [ ] CAC (Customer Acquisition Cost)
- [ ] LTV (Lifetime Value)
- [ ] LTVCACRatio
- [ ] Tests for each metric

### Task 4: Marketing Metrics (Day 3-4)
- [ ] ConversionRate
- [ ] FunnelAnalysis
- [ ] ChannelPerformance
- [ ] Tests for each metric

### Task 5: Time-Series Utilities (Day 4-5)
- [ ] Create `app/services/metrics/timeseries.py`
- [ ] Period aggregation (daily, weekly, monthly)
- [ ] Period-over-period comparison
- [ ] Tests for time-series functions

### Task 6: API Endpoints (Day 5)
- [ ] Create `app/api/v1/metrics.py`
- [ ] GET /metrics - List available metrics
- [ ] POST /metrics/calculate - Calculate metrics for a data source
- [ ] Tests for API endpoints

---

## Success Criteria

Phase 2 is complete when:

1. All metrics pass unit tests with known datasets
2. Metrics match manual calculations (verified with sample data)
3. Metrics API endpoints return correct results
4. Code coverage remains >80%

---

## Key Files to Create

```
app/services/metrics/
├── __init__.py
├── base.py          # BaseMetric, MetricResult, MetricDefinition
├── registry.py      # Metric registry for discovery
├── revenue.py       # TotalRevenue, MRR, ARR, GrowthRate
├── financial.py     # CAC, LTV, LTVCACRatio
├── marketing.py     # ConversionRate, FunnelAnalysis
└── timeseries.py    # Period aggregation, comparisons

app/api/v1/metrics.py  # Metrics API endpoints

tests/services/metrics/
├── __init__.py
├── test_revenue.py
├── test_financial.py
├── test_marketing.py
└── test_timeseries.py
```

---

## Testing Approach

For each metric:
1. Create a known dataset with expected results
2. Calculate metric
3. Assert result matches expected value exactly

Example:
```python
def test_total_revenue():
    df = pd.DataFrame({
        'amount': [100, 200, 300]
    })
    metric = TotalRevenue(df)
    result = metric.calculate()
    assert result.value == 600.0
    assert result.unit == "$"
```

---

## Architecture Notes

**Single Agent Decision**: We decided against multi-agent architecture. Phase 3 will use a single LLM call to generate narratives from the calculated metrics. This keeps costs low and latency fast.

**Metrics Flow**:
```
Data Source (from Phase 1)
    |
    v
Load DataFrame
    |
    v
Calculate Metrics (Phase 2)
    |
    v
Return MetricResult objects
    |
    v
(Phase 3: Pass to LLM for narrative)
```

---

## Development Commands

```bash
# Run tests
docker-compose exec app pytest tests/services/metrics/ -v

# Run with coverage
docker-compose exec app pytest --cov=app/services/metrics

# Test a metric interactively
docker-compose exec app python
>>> from app.services.metrics.revenue import MRR
>>> import pandas as pd
>>> df = pd.read_csv('data/samples/revenue_sample.csv')
>>> mrr = MRR(df)
>>> result = mrr.calculate(period='2024-01')
>>> print(result)
```

---

## Resources

- Phase 2 detailed plan: `/planning/03_PHASE_2_ANALYTICS_LAYER.md`
- Sample revenue data: `data/samples/revenue_sample.csv`
- Sample marketing data: `data/samples/marketing_sample.csv`

---

## After Phase 2

Phase 3: LLM-Powered Insights
- Report templates
- DeepSeek narrative generation (single call, not multi-agent)
- Natural language Q&A

The metrics from Phase 2 feed directly into Phase 3's narrative generation.

---

*Last updated: 2025-11-22*
