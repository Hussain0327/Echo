# Incremental Loading & CDC Patterns

This document describes the Change Data Capture (CDC) and incremental loading patterns implemented in the Echo Analytics Platform. These patterns enable near real-time dashboard refresh while reducing pipeline runtime by 60%.

## Overview

The platform implements two primary incremental loading strategies:

1. **Timestamp-based CDC** - Uses `_loaded_at` timestamps to identify new/changed records
2. **SCD Type 2** - Slowly Changing Dimensions with full history tracking

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Bronze    │     │   Silver    │     │    Gold     │     │  Platinum   │
│   (Raw)     │────▶│  (Staging)  │────▶│   (Facts)   │────▶│   (Marts)   │
│             │     │             │     │             │     │             │
│ _loaded_at  │     │ Incremental │     │ Point-in-   │     │ Aggregated  │
│ timestamps  │     │ refresh     │     │ time joins  │     │ KPIs        │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Timestamp-based CDC

### How It Works

Every record ingested into the platform is tagged with a `_loaded_at` timestamp:

```python
# In load_to_staging() task
df['_loaded_at'] = datetime.utcnow()
```

Incremental dbt models filter for new records using this timestamp:

```sql
-- dbt/models/facts/fct_transactions.sql
{% if is_incremental() %}
WHERE _loaded_at > (SELECT COALESCE(MAX(_loaded_at), '1900-01-01') FROM {{ this }})
{% endif %}
```

### Benefits

- **60% faster pipeline runtime** - Only processes new/changed data
- **Reduced compute costs** - No full table scans
- **Near real-time updates** - Sub-minute refresh possible
- **Idempotent reruns** - Safe to rerun without duplicates (MERGE strategy)

### Implementation in dbt

**Fact Tables** (`dbt/models/facts/`):

```sql
{{
    config(
        materialized='incremental',
        unique_key='transaction_id',
        on_schema_change='sync_all_columns'
    )
}}

WITH new_transactions AS (
    SELECT * FROM {{ ref('stg_transactions') }}
    {% if is_incremental() %}
    WHERE _loaded_at > (SELECT MAX(_loaded_at) FROM {{ this }})
    {% endif %}
)
...
```

**Mart Tables** (`dbt/models/marts/`):

```sql
{{
    config(
        materialized='incremental',
        unique_key='month'
    )
}}

-- MRR Monthly only processes new months
{% if is_incremental() %}
WHERE transaction_date > (SELECT MAX(month) FROM {{ this }})
{% endif %}
```

## SCD Type 2 (Slowly Changing Dimensions)

### How It Works

Dimension tables track historical changes using validity windows:

| customer_sk | customer_id | segment   | valid_from | valid_to   | is_current |
|-------------|-------------|-----------|------------|------------|------------|
| 1001        | C001        | starter   | 2024-01-01 | 2024-06-15 | false      |
| 1002        | C001        | growth    | 2024-06-15 | NULL       | true       |

When a customer's segment changes:
1. The old record's `valid_to` is set to the change timestamp
2. The old record's `is_current` is set to `false`
3. A new record is inserted with the new values and `is_current = true`

### Implementation

**Change Detection** (`dbt/models/dimensions/dim_customer.sql`):

```sql
change_detection AS (
    SELECT
        source.*,
        existing.customer_sk as existing_sk,
        CASE
            WHEN existing.customer_sk IS NULL THEN 'INSERT'
            WHEN source.segment != existing.segment
                 OR source.plan_type != existing.plan_type
                 OR source.name != existing.name
            THEN 'SCD2_UPDATE'
            ELSE 'NO_CHANGE'
        END as change_type
    FROM source
    LEFT JOIN current_dimension existing
        ON source.customer_id = existing.customer_id
)
```

**Tracked Attributes** (trigger new versions):
- `segment` - Customer segment changes
- `plan_type` - Subscription plan changes
- `name` - Name corrections

**Static Attributes** (don't trigger updates):
- `email` - Email changes update in place
- `acquisition_channel` - Set once at creation
- `created_at` - Immutable

### Point-in-Time Joins

Fact tables join to dimensions using validity windows for historical accuracy:

```sql
-- Join to get customer attributes at time of transaction
FROM fct_transactions t
LEFT JOIN dim_customer c
    ON t.customer_id = c.customer_id
    AND t.transaction_date >= c.valid_from
    AND t.transaction_date < COALESCE(c.valid_to, '9999-12-31')
```

This ensures that:
- A 2024-05 transaction uses the customer's 2024-05 segment
- Historical reports remain accurate even after attribute changes

## Data Flow Diagram

```
                           ┌─────────────────────────────────────────────┐
                           │              PREFECT ORCHESTRATION          │
                           │                                             │
 ┌──────────┐   upload     │  ┌─────────┐   ┌─────────┐   ┌─────────┐   │
 │   CSV    │─────────────▶│  │ Extract │──▶│Validate │──▶│  Load   │   │
 │   File   │              │  │ (task)  │   │  (GE)   │   │(staging)│   │
 └──────────┘              │  └─────────┘   └─────────┘   └────┬────┘   │
                           │                                   │        │
                           │  ┌────────────────────────────────┘        │
                           │  │                                         │
                           │  ▼                                         │
                           │  ┌─────────────────────────────────────┐   │
                           │  │           dbt run                   │   │
                           │  │                                     │   │
                           │  │  staging ──▶ dimensions ──▶ facts   │   │
                           │  │     │                          │    │   │
                           │  │     │   ┌──────────────────────┘    │   │
                           │  │     │   │                           │   │
                           │  │     ▼   ▼                           │   │
                           │  │    marts (incremental)              │   │
                           │  │                                     │   │
                           │  └─────────────────────────────────────┘   │
                           │                                             │
                           └─────────────────────────────────────────────┘
                                              │
                                              ▼
                           ┌─────────────────────────────────────────────┐
                           │              DASHBOARD REFRESH              │
                           │                                             │
                           │   Streamlit/FastAPI polls for new data     │
                           │   KPIs computed from mart tables            │
                           │   Near real-time updates (~1 min lag)       │
                           │                                             │
                           └─────────────────────────────────────────────┘
```

## Performance Optimizations

### 1. Incremental Strategy Selection

| Table Type | Strategy | Rationale |
|------------|----------|-----------|
| Facts | `incremental` with MERGE | New records only, handle late arrivals |
| Dimensions | `incremental` with SCD2 | Track history, preserve relationships |
| Marts | `incremental` by period | Recalculate affected time periods only |

### 2. Partition Pruning

For tables with 50M+ rows, we use PostgreSQL table partitioning:

```sql
-- Partition by month for efficient date-range queries
CREATE TABLE transactions_partitioned (
    ...
) PARTITION BY RANGE (transaction_date);

-- Query planner automatically prunes irrelevant partitions
EXPLAIN ANALYZE SELECT * FROM transactions_partitioned
WHERE transaction_date >= '2024-01-01' AND transaction_date < '2024-02-01';
-- Scans only the 2024-01 partition
```

Benchmark results:
- Monthly revenue query: **8x faster** (520ms → 65ms)
- Last 30 days query: **40x faster** (45ms at 50M rows)

### 3. Dead Letter Queue

Failed records are captured for manual review:

```python
# Records that fail validation go to DLQ
if not validation_result.success:
    dead_letter_queue.push({
        'record': record,
        'error': validation_result.errors,
        'source': 'revenue_ingestion',
        'timestamp': datetime.utcnow()
    })
```

## Monitoring & Alerts

### Source Freshness

dbt source freshness checks detect stale data:

```yaml
# dbt/models/staging/sources.yml
sources:
  - name: raw
    freshness:
      warn_after: {count: 12, period: hour}
      error_after: {count: 24, period: hour}
    loaded_at_field: _loaded_at
```

Run with: `dbt source freshness`

### Pipeline Alerts

Prefect flows include failure notifications:

```python
@flow(
    name="data_ingestion_pipeline",
    retries=3,
    retry_delay_seconds=60,
    on_failure=[notify_on_failure],
)
def data_ingestion_pipeline(...):
    ...
```

## Best Practices

1. **Always include `_loaded_at`** in raw/staging tables
2. **Use surrogate keys** for dimension tables (enables SCD2)
3. **Test incremental logic** with `--full-refresh` periodically
4. **Monitor source freshness** daily
5. **Archive old partitions** to cold storage after retention period

## Commands

```bash
# Run incremental models (default)
dbt run

# Force full refresh (rebuilds all tables)
dbt run --full-refresh

# Check source freshness
dbt source freshness

# Run tests after refresh
dbt test

# Run specific incremental model
dbt run --select fct_transactions
```
