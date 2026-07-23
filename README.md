# AI-Enabled Grocery E-Commerce

An end-to-end grocery commerce demo for AI-assisted shopping, product discovery, and checkout workflows.

This project demonstrates how an AI-assisted shopping experience can be layered on top of a grocery storefront inspired by publicly visible Shawpno-style catalog data. 

This repository implements a vertical slice of an AI-enabled grocery commerce system with:

- a Next.js storefront
- a FastAPI backend
- Supabase for data and auth
- semantic product search with embeddings
- three AI shopping assistants
- a sandbox payment flow for checkout

## Live Links

- Frontend: [https://ai-enabled-ecommerce.vercel.app](https://ai-enabled-ecommerce.vercel.app)
- Backend health: [https://ai-grocery-commerce-api.onrender.com/api/health](https://ai-grocery-commerce-api.onrender.com/api/health)
- Project Demo: [https://youtu.be/QXPYDL4ChhE](https://youtu.be/QXPYDL4ChhE)

## What The App Does

The demo supports the core flow of a small grocery commerce product:

- browse a product catalog
- search and inspect products
- add products to cart
- sign in with Supabase-backed auth
- create a checkout session
- redirect to SSLCOMMERZ sandbox payment
- review order history

On top of that, it includes AI-assisted shopping features:

- Natural Language Product Finder: 
  Interprets queries like "breakfast under Tk 300" and returns grounded catalog matches.

- Smart Grocery Bundle Planner: 
  Suggests a grocery bundle based on budget, household size, duration, and meal preference.

- Cart Health + Savings Optimizer: 
  Reviews the current basket and suggests substitutions or complementary items.

- Hybrid Semantic Search: 
  Uses embeddings plus structured filters for better retrieval than plain keyword matching.

- AI Chat Support: 
  The backend includes an AI chat endpoint and a provider status endpoint.

## Current Project Status

This repository represents an MVP/prototype implementation rather than a production launch.

What is already implemented:

- frontend app in `frontend/`
- backend API in `backend/`
- SQL migrations for core schema
- product seed data in `data/processed/products.json`
- data quality report
- embedding generation script
- semantic retrieval evaluation script and report
- deployment config for Render backend

## Architecture

```text
Raw catalog HTML / scrape inputs
        |
        v
data/raw/ + normalization pipeline
        |
        v
data/processed/products.json
        |
        +--> backend/scripts/seed_products.py
        |         |
        |         v
        |     Supabase products table
        |
        +--> backend/scripts/generate_product_embeddings.py
                  |
                  v
            product_embeddings table

Frontend (Next.js 16, React 19)
        |
        v
FastAPI backend
        |
        +--> Products / Search / AI / Orders / Payments APIs
        +--> Supabase auth + database
        +--> Embedding + hybrid retrieval
        +--> SSLCOMMERZ sandbox payment callbacks
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | FastAPI, Pydantic, Uvicorn |
| Database/Auth | Supabase |
| Search/Retrieval | Embeddings + pgvector-style hybrid retrieval via Supabase RPC |
| AI Providers | Groq, OpenAI, xAI configurable via env |
| Data Collection | HTML inputs and scraper utilities in Python/Playwright/BeautifulSoup |
| Payments | SSLCOMMERZ sandbox integration |
| Deployment | Render backend config committed; frontend structured for Vercel-style deployment |

## Repository Structure

```text
.
+-- frontend/                    # Next.js storefront
+-- backend/                     # FastAPI API, services, scripts, migrations
+-- data/
|   +-- raw/                     # raw HTML inputs / scrape artifacts
|   +-- processed/               # normalized products, orders, quality report
|   \-- evaluation/              # retrieval evaluation inputs and report
+-- render.yaml                  # Render deployment config for backend
+-- .env.example                 # environment variable template
\-- shawpno_ai_ecommerce_roadmap.md
```

## Key Features

### 1. Product Catalog

- product listing endpoint and storefront rendering
- product detail pages
- image, category, unit, price, and source metadata
- tag/category enrichment support

### 2. Authenticated Checkout Flow

- Supabase-based sign-in flow
- authenticated order history under `/api/orders/me`
- checkout session creation via backend
- payment callback handling for success, failure, and cancellation

### 3. AI Shopping Features

- intent-based product finder
- bundle planning based on user constraints
- cart review and savings recommendations
- provider status endpoint for debugging AI readiness
- semantic search route separate from classic browsing flow

### 4. Data + Retrieval Pipeline

- processed product dataset committed in repo
- seed script to populate `products`
- embedding generation script for `product_embeddings`
- evaluation script with recall and ranking metrics

## Dataset Snapshot

The committed processed dataset currently contains:

- `421` product records
- `19` rejected or duplicate records in the latest quality report
- `11` category buckets
- price range from `5.0` to `2100.0`
- `0` missing image URLs in the current processed file
- `0` missing source URLs in the current processed file

Category distribution from `data/processed/data_quality_report.json` includes:

- Food
- Frozen
- Spices
- Sauces & Pickles
- Pasta
- Deodorant
- Floor Glass & Wood Cleaners
- Storage & Containers
- Atta Maida & Suji
- Condensed Milk & Cream
- General

## Semantic Retrieval Evaluation

The repository includes an evaluation set at `data/evaluation/grocery_retrieval_eval.json` and a generated report at `data/evaluation/retrieval_report.json`.

Current reported metrics:

- queries: `15`
- recall@5: `1.0`
- mrr@5: `0.9333`
- embedding model: `sentence-transformers/all-MiniLM-L6-v2`

Example evaluated query types:

- premium chinigura rice
- fortified jeerashail rice
- moshur lentils
- full cream milk powder
- instant masala noodles
- washing powder detergent

## API Overview

The FastAPI app is exposed under `backend/app/main.py`.

### Health

- `GET /api/health`

### Products

- `GET /api/products`
- `GET /api/products/{product_id}`
- `GET /api/products/tags`

### Orders

- `GET /api/orders/me`
- `GET /api/orders/{order_id}`
- `POST /api/orders/checkout`

### Payments

- `GET|POST /api/payments/sslcommerz/success`
- `GET|POST /api/payments/sslcommerz/fail`
- `GET|POST /api/payments/sslcommerz/cancel`

### AI

- `POST /api/ai/product-finder`
- `POST /api/ai/bundle-planner`
- `POST /api/ai/cart-optimizer`
- `POST /api/ai/chat`
- `GET /api/ai/provider-status`

### Search

- `POST /api/search/hybrid`

When running locally, Swagger/OpenAPI is available from FastAPI’s default docs endpoint, typically:

- [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

## Local Setup

### Prerequisites

- Node.js 20+
- npm
- Python 3.11+
- a Supabase project
- optional AI provider key
- optional SSLCOMMERZ sandbox credentials

### 1. Clone and enter the repository

```bash
git clone <your-repo-url>
cd ai-enabled-ecommerce
```

### 2. Configure environment variables

Copy `.env.example` into the places your frontend and backend expect.

Recommended approach:

- create `backend/.env` for backend variables
- create `frontend/.env.local` for frontend public variables

Use the root `.env.example` as the master reference.

Important variables:

| Variable | Purpose |
| --- | --- |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | backend service credential |
| `SUPABASE_ANON_KEY` | anon/public auth key reference |
| `NEXT_PUBLIC_SUPABASE_URL` | frontend Supabase URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | frontend public auth key |
| `NEXT_PUBLIC_API_BASE_URL` | frontend -> backend API base URL |
| `AI_PROVIDER` | `groq`, `openai`, or another configured provider |
| `GROQ_API_KEY` | Groq provider key |
| `OPENAI_API_KEY` | OpenAI provider key |
| `OPENAI_EMBEDDING_MODEL` | embedding model for semantic indexing |
| `FRONTEND_URL` | canonical frontend URL |
| `BACKEND_URL` | canonical backend URL |
| `CORS_ALLOWED_ORIGINS` | comma-separated allowed origins |
| `SSLCOMMERZ_STORE_ID` | payment sandbox store ID |
| `SSLCOMMERZ_STORE_PASSWORD` | payment sandbox password |
| `SSLCOMMERZ_SANDBOX` | `true` for sandbox mode |

### 3. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Backend health check:

```bash
http://127.0.0.1:8001/api/health
```

### 4. Start the frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL:

```bash
http://localhost:3000
```

### Database Setup

The repository already includes SQL migrations under `backend/migrations/`:

- `0001_initial_schema.sql`
- `0002_checkout_schema_compatibility.sql`
- `0003_semantic_retrieval.sql`

Apply these to your Supabase/Postgres instance before seeding data.

After the schema is ready, seed products:

```bash
cd backend
python scripts/seed_products.py
```

### Build The Embedding Index

To populate semantic search data:

```bash
cd backend
python scripts/generate_product_embeddings.py
```

This script:

- loads processed products
- creates a canonical document per product
- generates embeddings
- upserts vectors into `product_embeddings`

### Run Retrieval Evaluation

```bash
cd backend
python scripts/evaluate_retrieval.py
```

This regenerates `data/evaluation/retrieval_report.json`.

### Frontend Commands

```bash
cd frontend
npm run dev
npm run build
npm run start
npm run lint
```

### Backend Commands

```bash
cd backend
uvicorn app.main:app --reload --port 8001
python scripts/seed_products.py
python scripts/generate_product_embeddings.py
python scripts/evaluate_retrieval.py
pytest
```

## Payment Flow

This project currently integrates with SSLCOMMERZ sandbox mode through backend-managed payment session creation and callback handling.

The checkout flow is:

1. frontend sends checkout payload to `POST /api/orders/checkout`
2. backend creates a pending order
3. backend requests a payment session from SSLCOMMERZ
4. user is redirected to payment URL
5. gateway redirects back to success/fail/cancel callback routes
6. backend verifies and updates payment/order state
7. frontend reads result on the checkout result page

This follows a standard backend-managed payment flow, though additional webhook hardening, idempotency review, and broader production testing would still be required for production use.

## AI Design Notes

The AI workflows are designed to stay grounded in actual catalog data rather than generating unsupported products or prices.

The intended pattern is:

- structured product data first
- retrieval over real catalog items
- LLM for interpretation/explanation where helpful
- deterministic price and catalog references in the final response

The hybrid search service currently:

- embeds the query
- optionally infers a budget cap from phrases like `under 500 taka`
- calls a database retrieval function
- returns structured matches with semantic scores

This is important for commerce use cases, where hallucinated products or prices would reduce reliability.

## Deployment

The repository includes `render.yaml` for the backend service.

Current committed deployment assumptions:

- backend deployed on Render
- frontend deployable on Vercel or similar
- Supabase used as managed backend data/auth layer

Render service highlights:

- Python web service
- root directory `backend`
- build command `pip install -r requirements.txt`
- start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- health check path `/api/health`
