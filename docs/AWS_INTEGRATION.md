# AWS S3 & Redshift Integration

This document describes the AWS cloud integration for the Echo Analytics Platform, enabling scalable data lake storage with S3 and enterprise data warehousing with Redshift.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AWS CLOUD                                      │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                        S3 DATA LAKE                               │  │
│   │                                                                   │  │
│   │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐            │  │
│   │  │    /raw/    │   │  /staging/  │   │  /archive/  │            │  │
│   │  │             │   │             │   │             │            │  │
│   │  │ • CSV       │   │ • Validated │   │ • Processed │            │  │
│   │  │ • Excel     │──▶│ • Parquet   │──▶│ • Parquet   │            │  │
│   │  │ • JSON      │   │ • Ready     │   │ • Backup    │            │  │
│   │  └─────────────┘   └─────────────┘   └─────────────┘            │  │
│   │                                                                   │  │
│   └───────────────────────────────┬──────────────────────────────────┘  │
│                                   │                                      │
│                                   ▼ COPY                                 │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │                       REDSHIFT WAREHOUSE                          │  │
│   │                                                                   │  │
│   │   staging.*        dimensions.*        facts.*        marts.*    │  │
│   │  ┌──────────┐     ┌──────────────┐   ┌──────────┐   ┌─────────┐ │  │
│   │  │stg_      │     │dim_customer  │   │fct_trans │   │mrr_     │ │  │
│   │  │revenue   │────▶│dim_product   │──▶│fct_events│──▶│monthly  │ │  │
│   │  │customers │ dbt │dim_date      │dbt│fct_mrr   │dbt│revenue_ │ │  │
│   │  │products  │     │(SCD Type 2)  │   │          │   │summary  │ │  │
│   │  └──────────┘     └──────────────┘   └──────────┘   └─────────┘ │  │
│   │                                                                   │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │         FastAPI / dbt         │
                    │    Analytics & Dashboards     │
                    └───────────────────────────────┘
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# S3 Data Lake
S3_BUCKET_NAME=your-echo-data-lake-bucket
S3_RAW_PREFIX=raw/
S3_STAGING_PREFIX=staging/
S3_ARCHIVE_PREFIX=archive/

# Redshift
REDSHIFT_HOST=your-cluster.region.redshift.amazonaws.com
REDSHIFT_PORT=5439
REDSHIFT_USER=admin
REDSHIFT_PASSWORD=your_password
REDSHIFT_DATABASE=echo_analytics
REDSHIFT_SCHEMA=public
USE_REDSHIFT=true
```

### IAM Permissions Required

The AWS credentials need these permissions:

**S3 Permissions:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

**Redshift Permissions:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "redshift:GetClusterCredentials",
                "redshift:DescribeClusters"
            ],
            "Resource": "*"
        }
    ]
}
```

## S3 Data Lake

### Bucket Structure

```
s3://your-bucket/
├── raw/                    # Landing zone for incoming data
│   ├── revenue/
│   │   └── YYYY/MM/DD/     # Date-partitioned raw files
│   ├── customers/
│   ├── products/
│   └── marketing/
├── staging/                # Validated, transformed data
│   ├── revenue/
│   ├── customers/
│   └── ...
└── archive/                # Processed files for retention
    ├── revenue/
    └── ...
```

### Upload Methods

#### 1. API Upload

```bash
# Upload CSV to S3
curl -X POST "http://localhost:8000/api/v1/ingestion/upload/s3" \
  -H "X-API-Key: your-api-key" \
  -F "file=@data.csv" \
  -F "data_type=revenue" \
  -F "file_format=parquet"
```

#### 2. Presigned URL (Large Files)

```bash
# Get presigned URL
curl "http://localhost:8000/api/v1/ingestion/s3/presigned-url?data_type=revenue&filename=large_file.csv"

# Use the returned URL to upload directly to S3
curl -X PUT -T large_file.csv "https://presigned-url..."
```

#### 3. Programmatic Upload

```python
from app.core.s3 import S3Client
import pandas as pd

s3 = S3Client()
df = pd.read_csv("data.csv")

# Upload as Parquet
uri = s3.upload_dataframe(df, "raw/revenue/2024/01/data.parquet", "parquet")
print(f"Uploaded to: {uri}")
```

### S3 Client API

```python
from app.core.s3 import S3Client

s3 = S3Client()

# Upload file
s3.upload_file(file_bytes, "path/to/file.parquet")

# Upload DataFrame
s3.upload_dataframe(df, "path/to/data.parquet", "parquet")

# Download file
data = s3.download_file("path/to/file.parquet")

# Download as DataFrame
df = s3.download_dataframe("path/to/data.parquet")

# List files
files = s3.list_files("raw/revenue/")

# Delete file
s3.delete_file("path/to/file.parquet")

# Move file (archive)
s3.move_file("raw/revenue/file.parquet", "archive/revenue/file.parquet")
```

## Redshift Integration

### Connection

```python
from app.core.redshift import (
    get_redshift_engine,
    redshift_session,
    copy_from_s3,
    test_connection
)

# Test connection
result = test_connection()
print(result)  # {'success': True, 'user': 'admin', 'database': 'echo'}

# Execute queries
with redshift_session() as session:
    result = session.execute(text("SELECT COUNT(*) FROM staging.stg_revenue"))
```

### Loading Data

#### COPY from S3 (Recommended for Large Data)

```python
from app.core.redshift import copy_from_s3

# Load Parquet from S3
result = copy_from_s3(
    s3_path="s3://bucket/staging/revenue/data.parquet",
    table_name="stg_revenue",
    schema="staging",
    file_format="PARQUET"
)

# With IAM role (preferred in production)
result = copy_from_s3(
    s3_path="s3://bucket/staging/revenue/",
    table_name="stg_revenue",
    schema="staging",
    iam_role="arn:aws:iam::123456789:role/RedshiftLoadRole"
)
```

#### Direct DataFrame Load (Small Data)

```python
from app.core.redshift import load_dataframe

result = load_dataframe(
    df=my_dataframe,
    table_name="stg_customers",
    schema="staging",
    if_exists="append"
)
```

### UNLOAD to S3

```python
from app.core.redshift import unload_to_s3

# Export query results to S3
result = unload_to_s3(
    query="SELECT * FROM marts.mrr_monthly WHERE month >= '2024-01-01'",
    s3_path="s3://bucket/exports/mrr/",
    file_format="PARQUET"
)
```

## dbt with Redshift

### Profile Configuration

The Redshift targets are configured in `dbt/profiles.yml`:

```yaml
echo:
  target: dev  # Default to PostgreSQL
  outputs:
    dev:
      type: postgres
      # ... PostgreSQL config

    redshift:
      type: redshift
      host: "{{ env_var('REDSHIFT_HOST') }}"
      port: 5439
      user: "{{ env_var('REDSHIFT_USER') }}"
      password: "{{ env_var('REDSHIFT_PASSWORD') }}"
      dbname: "{{ env_var('REDSHIFT_DATABASE') }}"
      schema: public
      threads: 4
```

### Running dbt on Redshift

```bash
# Run all models on Redshift
dbt run --target redshift

# Run specific models
dbt run --target redshift --select staging.stg_revenue+

# Full refresh (rebuild all tables)
dbt run --target redshift --full-refresh

# Run tests
dbt test --target redshift
```

### Redshift-Specific Optimizations

```sql
-- Distribution keys for large fact tables
{{
    config(
        materialized='incremental',
        unique_key='transaction_id',
        dist='customer_id',
        sort=['transaction_date']
    )
}}
```

## Pipeline Flows

### S3 to Redshift Pipeline

```python
from orchestration.flows.s3_redshift_pipeline import s3_to_redshift_pipeline

# Run pipeline
result = s3_to_redshift_pipeline(
    s3_prefix="raw/revenue/",
    data_type="revenue",
    target_table="stg_revenue",
    target_schema="staging",
    file_format="PARQUET",
    run_dbt_models=True,
    archive_after_load=True,
    validate_data=True
)
```

### API Trigger

```bash
curl -X POST "http://localhost:8000/api/v1/ingestion/trigger/s3-pipeline" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_prefix": "raw/revenue/",
    "data_type": "revenue",
    "target_table": "stg_revenue",
    "run_dbt": true
  }'
```

### Prefect Tasks

```python
from orchestration.tasks.s3 import upload_to_s3, download_from_s3
from orchestration.tasks.load import copy_s3_to_redshift

# In a Prefect flow
@flow
def my_pipeline():
    # Upload to S3
    upload_result = upload_to_s3(df, "revenue", file_format="parquet")

    # Copy to Redshift
    copy_result = copy_s3_to_redshift(
        s3_path=upload_result["s3_uri"],
        table_name="stg_revenue",
        schema="staging"
    )
```

## Hybrid Architecture

The platform supports both PostgreSQL and Redshift backends:

| Feature | PostgreSQL | Redshift |
|---------|------------|----------|
| Use Case | Development, small scale | Production, enterprise |
| Configuration | `USE_REDSHIFT=false` | `USE_REDSHIFT=true` |
| dbt Target | `dev` | `redshift` |
| Best For | < 10M rows | 10M+ rows |

### Toggle Between Backends

```python
from app.config import get_settings

settings = get_settings()

if settings.USE_REDSHIFT:
    from app.core.redshift import get_redshift_engine as get_engine
else:
    from app.core.database import engine as get_engine
```

## Best Practices

### S3

1. **Use Parquet format** for analytics workloads (columnar, compressed)
2. **Partition by date** in folder structure for efficient queries
3. **Archive after processing** to maintain data lineage
4. **Use presigned URLs** for large file uploads

### Redshift

1. **Use COPY command** for bulk loads (not INSERT)
2. **Choose distribution keys** for large tables (e.g., `customer_id`)
3. **Define sort keys** for frequently filtered columns
4. **Run VACUUM and ANALYZE** after large loads
5. **Use Spectrum** for querying S3 directly (optional)

### Security

1. **Use IAM roles** instead of access keys in production
2. **Enable S3 encryption** (SSE-S3 or SSE-KMS)
3. **Enable Redshift encryption** at rest
4. **Use VPC endpoints** for private connectivity
5. **Rotate credentials** regularly

## Troubleshooting

### S3 Connection Issues

```python
from app.core.s3 import S3Client

s3 = S3Client()
# Check if bucket is accessible
files = s3.list_files("")
print(f"Connected. Found {len(files)} files.")
```

### Redshift Connection Issues

```python
from app.core.redshift import test_connection

result = test_connection()
if result["success"]:
    print(f"Connected as {result['user']}")
else:
    print(f"Error: {result['error']}")
```

### COPY Command Errors

Check the `stl_load_errors` table:

```sql
SELECT query, filename, line_number, colname, err_reason
FROM stl_load_errors
ORDER BY starttime DESC
LIMIT 10;
```

## Cost Optimization

1. **Use Redshift Serverless** for variable workloads
2. **Reserved instances** for predictable usage
3. **S3 Intelligent-Tiering** for infrequently accessed archives
4. **Compress data** before loading (Parquet + ZSTD)
5. **Use spot instances** for Redshift cluster nodes (if supported)
