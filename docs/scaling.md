# Scaling

## Purpose

This document describes how the current system can be operated and extended for moderate growth, with a concrete focus on a target of 2,000 registered users.

It separates:

- what is implemented in the current repository
- what assumptions are used for scaling discussion
- what changes would be the next practical scaling steps

This document is based on the current codebase and deployment setup, including:

- [docs/architecture.md](/D:/humayra/ai-enabled-ecommerce/docs/architecture.md)
- [docs/deployment.md](/D:/humayra/ai-enabled-ecommerce/docs/deployment.md)
- [backend/app/main.py](/D:/humayra/ai-enabled-ecommerce/backend/app/main.py)
- [backend/migrations/0001_initial_schema.sql](/D:/humayra/ai-enabled-ecommerce/backend/migrations/0001_initial_schema.sql)
- [backend/migrations/0003_semantic_retrieval.sql](/D:/humayra/ai-enabled-ecommerce/backend/migrations/0003_semantic_retrieval.sql)
- [backend/app/services/order_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/order_service.py)
- [backend/app/services/hybrid_search_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/hybrid_search_service.py)
- [frontend/src/components/CartProvider.tsx](/D:/humayra/ai-enabled-ecommerce/frontend/src/components/CartProvider.tsx)
- [render.yaml](/D:/humayra/ai-enabled-ecommerce/render.yaml)

## 1. Current State

The deployed system currently runs as:

- a Next.js frontend on Vercel
- a FastAPI backend on Render
- a Supabase database and auth layer
- an SSLCOMMERZ sandbox payment integration

The current architecture is appropriate for an MVP and a demo workload. It already includes several useful building blocks for moderate scaling:

- a stateless backend API
- a managed database and auth provider
- indexed relational data in PostgreSQL
- vector search support through `pgvector`
- product and embedding seed scripts
- public product reads separated from authenticated order routes

At the same time, some scaling-related pieces are not yet fully implemented in the current repo:

- no server-side persistent cart flow in active use
- no background job worker in the committed deployment
- no response caching layer
- no automated load test or benchmark report
- no observability stack or error-tracing configuration

## 2. Target and Assumptions

The target discussed in this document is:

- `2,000` registered users

For a project at this size, the most useful discussion is not total registered users alone, but expected activity patterns.

The following assumptions are used for planning:

- registered users: `2,000`
- daily active users: `150` to `400`
- peak concurrent frontend users: `20` to `60`
- catalog browsing is much more frequent than checkout
- product reads are much more frequent than product writes
- AI requests are lower-volume than catalog requests
- most users generate short sessions rather than long continuous sessions

These are planning assumptions only. They are not measurements from production telemetry.

## 3. Expected Load Pattern

The current product is read-heavy.

The expected workload distribution is approximately:

- highest volume: product browsing, product detail requests, semantic search
- medium volume: authentication, order history
- lower volume: checkout and payment session creation
- lower volume but higher cost per request: AI chat and AI recommendation routes

This matters because different parts of the system scale differently:

- catalog reads benefit from caching and efficient indexes
- checkout needs correctness and idempotency more than raw throughput
- AI features need latency and cost control

## 4. What Already Helps Scaling

## 4.1 Managed frontend hosting

The frontend is deployed on Vercel, which already provides:

- CDN-backed static asset delivery
- managed HTTPS
- efficient global distribution for the Next.js frontend

This reduces the amount of infrastructure work needed for the UI layer.

## 4.2 Stateless backend design

The FastAPI backend is mostly stateless between requests.

This is a good scaling property because:

- request handling can be moved across replicas
- no in-memory session state is required for core backend logic
- Supabase and payment providers hold the authoritative state

The current backend uses:

- bearer token validation for protected order access
- database-backed order and payment records
- request-driven semantic retrieval

## 4.3 Indexed relational schema

The database already contains several indexes that are useful as traffic grows.

Examples from the committed schema:

- `products_category_idx`
- `products_price_idx`
- `products_name_idx`
- `orders_user_created_idx`
- `order_items_order_idx`
- `payments_order_idx`
- HNSW index on `product_embeddings.embedding_384`

These indexes support:

- catalog filtering
- order history reads
- order-to-line-item access
- payment lookup
- semantic retrieval

## 4.4 Managed authentication and database service

Supabase provides:

- managed PostgreSQL
- managed auth
- row-level security support

This reduces the operational burden compared with self-hosting a database and auth service at this stage.

## 5. Current Scaling Constraints

The following limits are visible from the current codebase.

## 5.1 Product list route loads the full catalog

`GET /api/products` currently loads all products and filters them in application code.

This is acceptable for a small catalog, but it will become less efficient as:

- the number of products grows
- concurrent users grow
- more filters and sorts are added

The next scaling step here would be:

- move filtering, sorting, and pagination into the database query itself

## 5.2 Local-storage cart is simple but not shared

The active frontend cart uses local browser storage through `CartProvider`.

This is fine for a demo, but it does not support:

- multi-device cart continuity
- cross-session server-side recovery
- shared cart state across clients

This is more a product scaling issue than an infrastructure scaling issue, but it becomes important as real usage grows.

## 5.3 Checkout writes are sequential

Checkout currently performs multiple write operations in sequence:

- insert order
- insert order items
- insert payment row

This works at current scale, but a stronger production path would use:

- explicit database transactions
- or a server-side database function / RPC that encapsulates the write set

## 5.4 AI routes can become the highest-cost requests

AI routes are likely to be the most expensive and variable part of the system because they may involve:

- embeddings
- semantic retrieval
- optional external provider calls

As traffic increases, AI routes need stronger controls than plain catalog reads.

## 5.5 No committed background worker

The current repository does not include a committed background worker for:

- recurring scraping
- embedding refresh
- asynchronous AI logging
- post-checkout notifications

At higher volume, background tasks should be separated from request/response traffic.

## 6. Scaling Strategy for 2,000 Users

The most practical scaling plan for this project is to keep the current managed-service architecture and improve it incrementally.

## 6.1 Frontend scaling

Recommended approach:

- continue using Vercel for frontend delivery
- keep static assets and app shell on CDN
- minimize unnecessary client re-fetching
- avoid blocking the first page load on non-critical requests

For this project, frontend scaling is unlikely to be the first bottleneck.

## 6.2 Backend scaling

Recommended approach:

- keep the backend stateless
- run the FastAPI service behind managed HTTPS
- scale backend instances horizontally when request concurrency grows

Practical next steps:

- move from a single free-tier instance to a tier that supports steadier uptime and more predictable cold-start behavior
- set conservative request timeouts
- keep expensive AI operations isolated from simpler catalog requests where possible

## 6.3 Database scaling

Recommended approach:

- keep PostgreSQL as the source of truth
- make product reads more query-efficient
- keep order writes authoritative and explicit

Practical next steps:

- add paginated product queries
- push search and filter conditions into SQL rather than in-memory filtering
- measure slow queries
- keep payment and order lookup indexes in place

## 6.4 Semantic search scaling

Recommended approach:

- keep embeddings in `product_embeddings`
- continue using the HNSW vector index
- treat vector search as a catalog retrieval service rather than a generic unbounded search layer

Practical next steps:

- regenerate embeddings only when product content changes
- use the existing `content_hash` to avoid unnecessary re-embedding
- monitor retrieval latency separately from normal catalog latency

## 6.5 AI feature scaling

Recommended approach:

- separate expensive AI behavior from cheap catalog behavior
- treat AI provider calls as a limited resource
- preserve deterministic fallbacks

Practical next steps:

- rate-limit AI routes
- cache repeated semantic-search or bundle-planning queries where safe
- cap the number of products and tool outputs passed into synthesis
- keep deterministic fallback behavior for provider outages

## 7. Recommended Infrastructure Improvements

The following changes would provide the biggest scaling benefit with the smallest architectural disruption.

## 7.1 Add pagination to product APIs

Priority: high

Reason:

- the current product list endpoint reads more data than necessary
- pagination reduces payload size and database work

## 7.2 Add server-side cart persistence

Priority: medium

Reason:

- the schema already supports `carts` and `cart_items`
- moving the active cart to the database will improve continuity and state consistency

## 7.3 Add a cache for hot catalog reads

Priority: high

Reason:

- product lists, product detail reads, category metadata, and frequent search results are good cache candidates

Possible cache targets:

- product list responses
- product tag/category metadata
- frequent semantic search requests

The current repository does not include Redis or another cache service, so this would be an added component.

## 7.4 Move asynchronous work into a worker

Priority: medium

Reason:

- scraping and embedding refresh should not block user-facing API capacity
- a worker can also handle low-priority post-processing

Candidate tasks:

- scheduled scraping
- scheduled seed refresh
- embedding updates
- AI interaction logging aggregation

## 7.5 Add operational monitoring

Priority: high

Reason:

- scaling without measurement is unreliable

Minimum recommended signals:

- backend latency
- API error rates
- database query latency
- semantic search latency
- payment callback success/failure rates
- AI provider error rates

## 8. Data and Query Strategy

## 8.1 Product catalog reads

At 2,000 registered users, the catalog path should remain efficient if:

- product list reads are paginated
- filter logic is handled in SQL
- static frontend assets remain on CDN

The current catalog size is small enough that the system can function today, but the route implementation should still be improved before substantially increasing catalog size or traffic.

## 8.2 Order and payment writes

Order creation and payment verification should continue to prioritize correctness over throughput.

Recommended improvements:

- use a stronger transactional write boundary for checkout
- keep idempotency protection for order creation
- verify payment status only from the provider callback path

These steps help protect order correctness as request volume grows.

## 8.3 AI data path

AI features should continue to read from:

- catalog products
- embedding index
- cart state

They should not become the source of truth for prices, order state, or payment status.

## 9. Security and Abuse Considerations at Scale

Scaling is not only a performance issue. It also increases the importance of safety and abuse control.

Recommended next steps:

- rate-limit authenticated and anonymous routes separately
- rate-limit AI endpoints more aggressively than catalog endpoints
- keep service-role keys server-only
- restrict CORS to expected frontend origins
- continue using row-level security for user-owned data

For checkout and payment:

- preserve order idempotency
- validate server-side totals from the database
- rely on payment verification before marking an order as paid

## 10. Reliability Strategy

For a 2,000-user target, the most practical reliability approach is:

- managed hosting for frontend and backend
- managed database and auth
- bounded request timeouts
- deterministic AI fallback behavior
- health endpoint verification

Current reliability-related strengths already visible in the repo:

- `/api/health`
- product JSON fallback for product reads
- server-side price recalculation during checkout
- payment verification before marking an order as paid

Current missing reliability pieces:

- no committed readiness probe beyond basic health
- no circuit-breaker logic for AI providers
- no queue for delayed tasks
- no automated load report

## 11. Cost Control

At this scale, cost control is especially important for AI-enabled features.

The likely cost drivers are:

- AI provider calls
- vector search and embedding updates
- managed backend uptime beyond free tiers

Recommended cost controls:

- cache repeated AI-retrieval patterns when safe
- keep provider-assisted synthesis optional
- use deterministic fallback when provider use is not necessary
- avoid re-embedding unchanged products

## 12. Suggested Scaling Roadmap

The following phased plan matches the current project maturity.

### Phase 1: strengthen the current MVP

- add database-side pagination and filtering for products
- add better error and latency monitoring
- keep the current managed-service deployment model

### Phase 2: improve state and performance

- move active cart persistence to the database
- add response caching for hot catalog and search reads
- separate background tasks from request handling

### Phase 3: harden AI and operations

- add AI-specific rate limits
- add worker-based embedding refresh
- add formal load testing and operational alerts

## 13. What Would Be Measured Next

To validate the scaling plan, the next useful measurements would be:

- p50 and p95 latency for `/api/products`
- p50 and p95 latency for `/api/search/hybrid`
- p50 and p95 latency for `/api/ai/chat`
- checkout success rate
- payment callback verification success rate
- Supabase query latency under concurrent product browsing

The current repository does not include these measurements yet.

## 14. Summary

The current architecture can support a moderate demo-scale workload because it already uses managed hosting, a stateless backend, indexed relational data, and vector search support.

For a target of 2,000 registered users, the most important next steps are not a full platform rewrite. The practical priorities are:

- paginate and push catalog filtering into the database
- add caching for hot reads
- move asynchronous work into a background worker
- rate-limit and monitor AI routes
- improve transactional and operational hardening around checkout

This keeps the current architecture intact while addressing the most likely bottlenecks first.

