# Echo Frontend

React/Next.js frontend for Echo - AI Data Scientist

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **API**: REST (FastAPI backend)

## Getting Started

### Prerequisites

Make sure your backend is running first:

```bash
# In the root directory
docker-compose up -d

# Verify backend is running
curl http://localhost:8000/api/v1/health
```

### Install Dependencies

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Features

### Home Page
- Upload CSV or Excel files
- See instant metrics (Revenue, AOV, Conversion Rate)
- Clean, card-based layout

### Chat Page
- Upload data and chat with Echo
- Natural language questions about your data
- Real-time responses with context

### Reports Page
- Generate structured business reports
- Choose from 3 templates:
  - Revenue Health
  - Marketing Funnel
  - Financial Overview
- AI-generated narratives + deterministic metrics

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Home (file upload + metrics)
│   ├── chat/
│   │   └── page.tsx       # Chat with Echo
│   └── reports/
│       └── page.tsx       # Report generation
├── components/            # Reusable React components
│   ├── FileUpload.tsx    # Drag & drop file upload
│   ├── MetricsCard.tsx   # Metric display card
│   └── ChatInterface.tsx # Chat UI
├── lib/
│   └── api.ts            # API service layer
├── types/
│   └── index.ts          # TypeScript type definitions
└── .env.local            # Environment variables
```

## Configuration

Edit `.env.local` to change the API URL:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Available Scripts

```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run start      # Start production server
npm run lint       # Run ESLint
```

## Testing the Frontend

1. Start the backend:
   ```bash
   docker-compose up -d
   ```

2. Start the frontend:
   ```bash
   cd frontend && npm run dev
   ```

3. Try it out:
   - Go to http://localhost:3000
   - Upload a file from `../data/samples/revenue_sample.csv`
   - See metrics calculated
   - Click "Chat" to ask questions
   - Click "Reports" to generate a full report

## Common Issues

### Backend not connecting
**Error**: "Failed to calculate metrics. Make sure the backend is running."

**Fix**:
```bash
# Check if backend is running
docker-compose ps

# Restart if needed
docker-compose restart app

# Check logs
docker-compose logs app -f
```

### CORS errors
If you see CORS errors in the browser console, update the backend CORS settings:

In `app/config.py`, make sure `CORS_ORIGINS` includes:
```python
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### TypeScript errors
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
```

## Building for Production

```bash
npm run build
npm run start
```

The optimized production build will be in `.next/`

## Deployment

Can deploy to:
- **Vercel** (easiest - made by Next.js creators)
- **Netlify**
- **Railway** (alongside the backend)

Just connect your GitHub repo and it auto-deploys.

---

*Last updated: 2025-11-25*
