#!/bin/bash

# Test Production Deployment Script
# Usage: ./test_production.sh https://your-app.up.railway.app

if [ -z "$1" ]; then
    echo "Usage: ./test_production.sh <YOUR_RAILWAY_URL>"
    echo "Example: ./test_production.sh https://echo-production.up.railway.app"
    exit 1
fi

API_URL="$1"
echo "Testing Echo API at: $API_URL"
echo "================================"
echo ""

# Test 1: Basic Health
echo "1. Testing basic health..."
HEALTH=$(curl -s "$API_URL/api/v1/health" | python3 -m json.tool 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Basic health check passed"
    echo "$HEALTH"
else
    echo "❌ Basic health check failed"
fi
echo ""

# Test 2: Database Connection
echo "2. Testing database connection..."
DB_HEALTH=$(curl -s "$API_URL/api/v1/health/db" | python3 -m json.tool 2>/dev/null)
if echo "$DB_HEALTH" | grep -q '"database": "connected"'; then
    echo "✅ Database connection working"
else
    echo "❌ Database connection failed"
    echo "$DB_HEALTH"
fi
echo ""

# Test 3: Redis Connection
echo "3. Testing Redis connection..."
REDIS_HEALTH=$(curl -s "$API_URL/api/v1/health/redis" | python3 -m json.tool 2>/dev/null)
if echo "$REDIS_HEALTH" | grep -q '"redis": "connected"'; then
    echo "✅ Redis connection working"
else
    echo "❌ Redis connection failed"
    echo "$REDIS_HEALTH"
fi
echo ""

# Test 4: Analytics Session
echo "4. Testing analytics session..."
SESSION=$(curl -s -X POST "$API_URL/api/v1/analytics/session/start" \
    -H "Content-Type: application/json" \
    -d '{"task_type": "report_generation"}')
if echo "$SESSION" | grep -q '"id"'; then
    echo "✅ Session tracking working"
else
    echo "❌ Session tracking failed"
    echo "$SESSION"
fi
echo ""

# Test 5: Portfolio Stats
echo "5. Testing portfolio stats..."
PORTFOLIO=$(curl -s "$API_URL/api/v1/analytics/portfolio" | python3 -m json.tool 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Portfolio stats endpoint working"
    echo "$PORTFOLIO"
else
    echo "❌ Portfolio stats failed"
fi
echo ""

# Test 6: API Docs
echo "6. Testing API documentation..."
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/v1/docs")
if [ "$DOCS_STATUS" = "200" ]; then
    echo "✅ API docs available at: $API_URL/api/v1/docs"
else
    echo "❌ API docs failed (status: $DOCS_STATUS)"
fi
echo ""

echo "================================"
echo "Production deployment test complete!"
echo ""
echo "If all tests passed, your API is live and working."
echo "Next steps:"
echo "  1. Visit $API_URL/api/v1/docs to see Swagger UI"
echo "  2. Update CORS_ORIGINS if you need frontend access"
echo "  3. Set up monitoring (Sentry, LogDNA, etc.)"
