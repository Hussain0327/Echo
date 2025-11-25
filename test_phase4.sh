#!/bin/bash

BASE_URL="http://localhost:8000/api/v1"

echo "================================"
echo "Phase 4 Manual Testing Script"
echo "================================"
echo ""

echo "1. Starting a session..."
SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/analytics/session/start" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "report_generation",
    "baseline_time_seconds": 7200
  }')

SESSION_ID=$(echo $SESSION_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "   Session ID: $SESSION_ID"
echo ""

echo "2. Simulating work (calculating metrics)..."
sleep 2
curl -s -X POST "$BASE_URL/metrics/calculate/csv" \
  -F "file=@data/samples/revenue_sample.csv" \
  -F "metrics=TotalRevenue" \
  -F "metrics=AverageOrderValue" > /dev/null
echo "   Metrics calculated!"
echo ""

echo "3. Ending session..."
sleep 1
END_RESPONSE=$(curl -s -X POST "$BASE_URL/analytics/session/end" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\"}")

DURATION=$(echo $END_RESPONSE | grep -o '"duration_seconds":[0-9.]*' | cut -d':' -f2)
TIME_SAVED=$(echo $END_RESPONSE | grep -o '"time_saved_seconds":[0-9.]*' | cut -d':' -f2)
echo "   Duration: ${DURATION}s"
echo "   Time saved: ${TIME_SAVED}s (~$(echo "scale=1; $TIME_SAVED/3600" | bc)h)"
echo ""

echo "4. Submitting feedback..."
FEEDBACK_RESPONSE=$(curl -s -X POST "$BASE_URL/feedback" \
  -H "Content-Type: application/json" \
  -d "{
    \"interaction_type\": \"report\",
    \"session_id\": \"$SESSION_ID\",
    \"rating\": 5,
    \"feedback_text\": \"Amazing! So much faster than doing this manually.\",
    \"accuracy_rating\": \"correct\"
  }")

FEEDBACK_ID=$(echo $FEEDBACK_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "   Feedback ID: $FEEDBACK_ID"
echo ""

echo "5. Viewing analytics..."
echo ""
echo "   Time Savings:"
curl -s "$BASE_URL/analytics/time-savings" | python3 -m json.tool
echo ""

echo "   Satisfaction:"
curl -s "$BASE_URL/analytics/satisfaction" | python3 -m json.tool
echo ""

echo "   Accuracy:"
curl -s "$BASE_URL/analytics/accuracy" | python3 -m json.tool
echo ""

echo "6. Portfolio Stats (The Money Shot):"
curl -s "$BASE_URL/analytics/portfolio" | python3 -m json.tool
echo ""

echo "================================"
echo "Test Complete!"
echo "================================"
