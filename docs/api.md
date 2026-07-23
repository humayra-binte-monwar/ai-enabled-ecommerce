# API Documentation

## Purpose

This document describes the HTTP API implemented in the FastAPI backend in this repository.

It covers:

- base URLs
- authentication
- available endpoints
- request and response formats
- current error behavior visible in the code

This document is based on the current backend implementation in:

- [backend/app/main.py](/D:/humayra/ai-enabled-ecommerce/backend/app/main.py)
- [backend/app/api/products.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/products.py)
- [backend/app/api/orders.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/orders.py)
- [backend/app/api/payments.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/payments.py)
- [backend/app/api/ai.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/ai.py)
- [backend/app/api/search.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/search.py)

## Base URLs

### Local development

- Backend API: `http://127.0.0.1:8001`
- OpenAPI / Swagger UI: `http://127.0.0.1:8001/docs`

### Deployed service

- Health check: [https://ai-grocery-commerce-api.onrender.com/api/health](https://ai-grocery-commerce-api.onrender.com/api/health)

## API Conventions

- All application routes are prefixed with `/api`.
- JSON is used for request and response bodies except payment callbacks, which may receive query parameters or form data from the payment gateway.
- Protected order routes use bearer token authentication.
- Product, search, and AI routes are currently public in the reviewed backend code.

## Authentication

Authentication for protected routes is implemented in [backend/app/api/dependencies.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/dependencies.py).

The backend expects:

- `Authorization: Bearer <supabase_access_token>`

If the token is missing, invalid, or expired, the backend returns HTTP `401`.

Current authentication error messages include:

- `Sign in is required.`
- `Your session is invalid or has expired.`

## Common Response Patterns

### Success responses

Successful JSON endpoints generally return:

- HTTP `200` for reads and AI operations
- HTTP `201` for checkout session creation

### Error responses

FastAPI error responses use a `detail` field. Typical shape:

```json
{
  "detail": "Product not found"
}
```

Validation errors from Pydantic and FastAPI will use the standard FastAPI validation error format.

## 1. Health Endpoint

### `GET /api/health`

Returns a basic backend health response.

#### Authentication

- not required

#### Response

```json
{
  "status": "healthy"
}
```

## 2. Product Endpoints

Product routes are implemented in [backend/app/api/products.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/products.py).

## 2.1 List products

### `GET /api/products`

Returns a list of products.

#### Authentication

- not required

#### Query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `search` | string | no | Case-insensitive text match against product name, category, or brand |
| `category` | string | no | Exact category match against `product.category` |

#### Example request

```http
GET /api/products?search=rice&category=Food
```

#### Response shape

Returns an array of product objects with the schema defined in [backend/app/schemas/product.py](/D:/humayra/ai-enabled-ecommerce/backend/app/schemas/product.py).

Example:

```json
[
  {
    "id": "aci-pure-salt-1kg",
    "name": "ACI Pure Salt 1kg",
    "category": "Food",
    "brand": "ACI",
    "price": 55.0,
    "unit": "1kg",
    "image_url": "https://example.com/image.jpg",
    "product_url": "https://example.com/product",
    "stock_status": "in_stock",
    "tags": ["salt", "iodized"],
    "normalized_category": "Food",
    "product_type": "salt"
  }
]
```

#### Current implementation notes

- The backend loads products from Supabase when available.
- If the product query fails, `product_service` falls back to `data/processed/products.json`.
- The current route does not implement pagination.

## 2.2 Get product by ID

### `GET /api/products/{product_id}`

Returns one product by ID.

#### Authentication

- not required

#### Path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `product_id` | string | yes | Product identifier used in the dataset and database |

#### Example request

```http
GET /api/products/aci-pure-salt-1kg
```

#### Success response

```json
{
  "id": "aci-pure-salt-1kg",
  "name": "ACI Pure Salt 1kg",
  "category": "Food",
  "brand": "ACI",
  "price": 55.0,
  "unit": "1kg",
  "image_url": "https://example.com/image.jpg",
  "product_url": "https://example.com/product",
  "stock_status": "in_stock",
  "tags": ["salt", "iodized"],
  "normalized_category": "Food",
  "product_type": "salt"
}
```

#### Error responses

- `404` if the product is not found

Example:

```json
{
  "detail": "Product not found"
}
```

## 2.3 Get product tags and derived categories

### `GET /api/products/tags`

Returns derived metadata from the current product catalog.

#### Authentication

- not required

#### Response

```json
{
  "tags": ["iodized", "salt"],
  "normalized_categories": ["Food", "Frozen"],
  "product_types": ["salt", "milk_powder"]
}
```

#### Current implementation notes

- `tags` are derived from `product.tags`
- `normalized_categories` are derived from non-null `product.normalized_category`
- `product_types` are derived from non-null `product.product_type`

## 3. Order Endpoints

Order routes are implemented in [backend/app/api/orders.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/orders.py).

These routes require a valid Supabase bearer token.

## 3.1 List current user orders

### `GET /api/orders/me`

Returns orders for the authenticated user.

#### Authentication

- required

#### Headers

```http
Authorization: Bearer <supabase_access_token>
```

#### Response shape

Returns an array of `Order` objects defined in [backend/app/schemas/order.py](/D:/humayra/ai-enabled-ecommerce/backend/app/schemas/order.py).

Example:

```json
[
  {
    "id": "f8cb77da-9f1e-4fc4-bc8d-f12f8d20a1aa",
    "customer_name": "Test User",
    "customer_phone": "01700000000",
    "customer_address": "Dhaka",
    "subtotal": 550.0,
    "delivery_fee": 0.0,
    "total": 550.0,
    "currency": "BDT",
    "status": "paid",
    "created_at": "2026-07-23T10:20:30.000000+00:00",
    "items": [
      {
        "product_id": "aci-pure-salt-1kg",
        "product_name": "ACI Pure Salt 1kg",
        "unit_price": 55.0,
        "quantity": 2
      }
    ]
  }
]
```

#### Error responses

- `401` if the bearer token is missing or invalid

## 3.2 Get one order for the current user

### `GET /api/orders/{order_id}`

Returns one order if it belongs to the authenticated user.

#### Authentication

- required

#### Path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `order_id` | string | yes | Order UUID |

#### Success response

Returns the same `Order` schema shown above.

#### Error responses

- `401` if the token is missing or invalid
- `404` if the order does not exist or does not belong to the authenticated user

Example:

```json
{
  "detail": "Order not found."
}
```

## 3.3 Create checkout session

### `POST /api/orders/checkout`

Creates a pending order and returns a payment session URL.

#### Authentication

- required

#### Request body

Schema defined by `CheckoutCreate` in [backend/app/schemas/order.py](/D:/humayra/ai-enabled-ecommerce/backend/app/schemas/order.py).

```json
{
  "customer_name": "Test User",
  "customer_phone": "01700000000",
  "customer_address": "Dhaka, Bangladesh",
  "items": [
    {
      "product_id": "aci-pure-salt-1kg",
      "quantity": 2
    }
  ],
  "idempotency_key": "8e721e2d-6b9d-4a55-a6f5-a92348b4b569"
}
```

#### Behavior

The backend currently:

1. validates the bearer token
2. checks whether the same user already used the same `idempotency_key`
3. fetches product prices from the database
4. rejects missing or out-of-stock items
5. calculates `subtotal` and `total` on the server
6. inserts `orders`, `order_items`, and an initial `payments` row
7. requests a payment session from SSLCOMMERZ
8. returns the payment URL

#### Success response

HTTP `201`

```json
{
  "order_id": "f8cb77da-9f1e-4fc4-bc8d-f12f8d20a1aa",
  "payment_url": "https://sandbox.sslcommerz.com/..."
}
```

#### Error responses

- `401` if the token is missing or invalid
- `400` if one or more products are unavailable
- `400` if one or more requested products are out of stock
- `500` if order creation fails after validation
- `502` if the payment session cannot be started
- `503` if the payment gateway is not configured

Examples from current code:

```json
{
  "detail": "One or more products are no longer available."
}
```

```json
{
  "detail": "Out of stock: Product Name."
}
```

```json
{
  "detail": "Checkout could not be started. Please try again."
}
```

```json
{
  "detail": "Payment gateway is not configured."
}
```

## 4. Payment Callback Endpoints

Payment callback routes are implemented in [backend/app/api/payments.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/payments.py).

These routes are intended for SSLCOMMERZ callbacks rather than direct frontend use.

## 4.1 Success callback

### `GET|POST /api/payments/sslcommerz/success`

#### Authentication

- not required

#### Input

- query parameters or form fields from SSLCOMMERZ

#### Behavior

- reads callback data
- verifies the payment through `verify_sslcommerz_payment`
- determines whether the payment is valid
- redirects the browser to:
  - `/checkout/result?status=paid&order_id=...` on successful verification
  - `/checkout/result?status=verification_failed` if verification fails

#### Response

- HTTP `303` redirect

## 4.2 Failure callback

### `GET|POST /api/payments/sslcommerz/fail`

#### Behavior

- reads callback data
- marks the payment as `failed`
- redirects to `/checkout/result?status=failed&order_id=...` when an order ID is present

#### Response

- HTTP `303` redirect

## 4.3 Cancel callback

### `GET|POST /api/payments/sslcommerz/cancel`

#### Behavior

- reads callback data
- marks the payment as `cancelled`
- redirects to `/checkout/result?status=cancelled&order_id=...` when an order ID is present

#### Response

- HTTP `303` redirect

## 5. AI Endpoints

AI routes are implemented in [backend/app/api/ai.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/ai.py).

## 5.1 Product finder

### `POST /api/ai/product-finder`

Finds products from a natural-language shopping query.

#### Authentication

- not required

#### Request body

```json
{
  "query": "breakfast under 300 taka"
}
```

#### Response

Schema defined by `ProductFinderResponse`.

```json
{
  "summary": "Found several breakfast items within budget.",
  "products": [
    {
      "id": "fresh-premium-green-tea-37-5gm",
      "name": "Fresh Premium Green Tea 37.5gm",
      "category": "Food",
      "price": 120.0,
      "unit": "37.5gm",
      "image_url": "https://example.com/image.jpg",
      "product_url": "https://example.com/product",
      "tags": ["tea", "green_tea"],
      "normalized_category": "Food",
      "product_type": "tea",
      "reason": "Matched breakfast-related query terms."
    }
  ]
}
```

#### Current implementation notes

- the exact product selection logic is delegated to `find_products(request.query)`
- response content is grounded in product records rather than free-text suggestions only

## 5.2 Bundle planner

### `POST /api/ai/bundle-planner`

Builds a grocery bundle based on user constraints.

#### Authentication

- not required

#### Request body

```json
{
  "budget": 1500,
  "people": 2,
  "duration_days": 3,
  "meal_type": "breakfast",
  "preference": "budget"
}
```

#### Response

Schema defined by `BundlePlannerResponse`.

```json
{
  "summary": "Planned a breakfast bundle within budget.",
  "estimated_total": 1320.0,
  "remaining_budget": 180.0,
  "items": [
    {
      "id": "fresh-premium-green-tea-37-5gm",
      "name": "Fresh Premium Green Tea 37.5gm",
      "category": "Food",
      "price": 120.0,
      "unit": "37.5gm",
      "image_url": "https://example.com/image.jpg",
      "product_url": "https://example.com/product",
      "recommended_quantity": 1,
      "suggested_quantity": 1,
      "reason": "Selected for breakfast use."
    }
  ]
}
```

## 5.3 Cart optimizer

### `POST /api/ai/cart-optimizer`

Reviews the current cart and returns suggestions.

#### Authentication

- not required

#### Request body

```json
{
  "items": [
    {
      "product_id": "aci-pure-salt-1kg",
      "name": "ACI Pure Salt 1kg",
      "category": "Food",
      "price": 55.0,
      "quantity": 2
    }
  ],
  "goal": "reduce cost"
}
```

#### Response

Schema defined by `CartOptimizerResponse`.

```json
{
  "summary": "Reviewed the cart and found some saving opportunities.",
  "cart_total": 110.0,
  "suggestions": [
    {
      "type": "alternative",
      "message": "A lower-priced option is available.",
      "product_id": "some-other-product",
      "product_name": "Alternative Product",
      "category": "Food",
      "price": 50.0,
      "unit": "1kg",
      "image_url": "https://example.com/image.jpg",
      "product_url": "https://example.com/product"
    }
  ]
}
```

## 5.4 Chat endpoint

### `POST /api/ai/chat`

Accepts a free-form chat message and returns:

- a message
- detected intent
- optional product recommendations
- optional cart actions
- optional citations
- follow-up suggestions

#### Authentication

- not required

#### Request body

Schema defined by `ChatRequest`.

```json
{
  "session_id": "demo-1721721721-abcd1234",
  "message": "Add the cheapest milk to my cart",
  "cart_items": [
    {
      "product_id": "aci-pure-salt-1kg",
      "name": "ACI Pure Salt 1kg",
      "category": "Food",
      "price": 55.0,
      "quantity": 1
    }
  ],
  "confirm_actions": false
}
```

#### Response

Schema defined by `ChatResponse`.

```json
{
  "message": "I found a matching product and prepared the cart action.",
  "intent": "cart_add",
  "products": [
    {
      "id": "fresh-instant-full-cream-milk-powder-500gm",
      "name": "Fresh Instant Full Cream Milk Powder 500gm",
      "category": "Food",
      "price": 450.0,
      "unit": "500gm",
      "image_url": "https://example.com/image.jpg",
      "product_url": "https://example.com/product",
      "tags": ["milk", "powder_milk"],
      "normalized_category": "Food",
      "product_type": "milk_powder",
      "reason": "Sorted by lowest price"
    }
  ],
  "cart_actions": [
    {
      "type": "add_item",
      "product_id": "fresh-instant-full-cream-milk-powder-500gm",
      "product_name": "Fresh Instant Full Cream Milk Powder 500gm",
      "quantity": 1,
      "requires_confirmation": false,
      "message": "Added 1 x Fresh Instant Full Cream Milk Powder 500gm to cart.",
      "product": {
        "id": "fresh-instant-full-cream-milk-powder-500gm",
        "name": "Fresh Instant Full Cream Milk Powder 500gm",
        "category": "Food",
        "price": 450.0,
        "unit": "500gm",
        "image_url": "https://example.com/image.jpg",
        "product_url": "https://example.com/product",
        "tags": ["milk", "powder_milk"],
        "normalized_category": "Food",
        "product_type": "milk_powder",
        "reason": "Selected for cart action"
      }
    }
  ],
  "citations": [
    {
      "product_id": "fresh-instant-full-cream-milk-powder-500gm",
      "source_url": "https://example.com/product"
    }
  ],
  "follow_up_suggestions": [
    "Show cheaper options",
    "Make it healthier"
  ],
  "tools_used": ["compare_prices", "add_to_cart"],
  "fallback": false
}
```

#### Current implementation notes

The chat route uses a hybrid pattern implemented in [backend/app/ai/agent.py](/D:/humayra/ai-enabled-ecommerce/backend/app/ai/agent.py):

- rule-based intent detection
- grounded product and cart tools
- optional LLM synthesis when a provider is configured
- deterministic fallback when no provider is available

#### Common intent categories in current code

The current chat logic includes flows for:

- greeting
- cart status
- clear cart
- remove item from cart
- increase or decrease quantity
- cart review
- bundle planning
- price comparison
- product search
- add to cart
- health-related questions with disclaimer behavior

## 5.5 Provider status

### `GET /api/ai/provider-status`

Returns AI provider readiness information.

#### Authentication

- not required

#### Response

Current response fields from the route implementation:

```json
{
  "provider": "groq",
  "agent_enabled": true,
  "model": "llama-3.1-8b-instant",
  "langchain_available": true,
  "langchain_import_error": "",
  "has_provider_key": true,
  "client_ready": true
}
```

#### Current implementation notes

- `provider` comes from backend settings
- `model` currently returns the Groq model when provider is `groq`, otherwise it returns the OpenAI model branch used in the route
- `client_ready` indicates whether `get_llm_client()` returned a usable client

## 6. Semantic Search Endpoint

Search routes are implemented in [backend/app/api/search.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/search.py).

## 6.1 Hybrid semantic search

### `POST /api/search/hybrid`

Runs semantic retrieval over the indexed product catalog.

#### Authentication

- not required

#### Request body

Schema defined by `HybridSearchRequest`.

```json
{
  "query": "rice under 500 taka",
  "category": "Food",
  "min_price": 0,
  "max_price": 500,
  "limit": 5
}
```

#### Validation rules

| Field | Rule |
| --- | --- |
| `query` | minimum length 2, maximum length 300 |
| `category` | optional, maximum length 100 |
| `min_price` | optional, must be `>= 0` |
| `max_price` | optional, must be `>= 0` |
| `limit` | default `8`, minimum `1`, maximum `20` |

#### Response

Schema defined by `HybridSearchResponse`.

```json
{
  "query": "rice under 500 taka",
  "applied_filters": {
    "category": "Food",
    "min_price": 0,
    "max_price": 500
  },
  "products": [
    {
      "id": "rupchanda-chinigura-rice-1kg",
      "name": "Rupchanda Chinigura Rice 1kg",
      "category": "Food",
      "price": 190.0,
      "unit": "1kg",
      "image_url": "https://example.com/image.jpg",
      "product_url": "https://example.com/product",
      "tags": ["rice", "chinigura"],
      "normalized_category": "Food",
      "product_type": "rice",
      "reason": "Retrieved by semantic similarity from the product catalog",
      "semantic_score": 0.92
    }
  ]
}
```

#### Current implementation notes

- If `max_price` is not provided, the backend may infer it from phrases like `under 500 taka`.
- The backend embeds the query and calls the `match_products_hybrid` RPC function in Supabase.

#### Error responses

- `503` if semantic search is not ready or the embedding RPC fails

Example:

```json
{
  "detail": "Semantic search is not ready. Generate the product embedding index first."
}
```

## 7. Status Codes Summary

The current backend code uses the following status codes across the reviewed routes.

| Status | Meaning in current implementation |
| --- | --- |
| `200` | Successful read or AI/search response |
| `201` | Checkout session created |
| `303` | Payment callback redirect |
| `400` | Invalid checkout business condition such as unavailable or out-of-stock products |
| `401` | Missing or invalid bearer token |
| `404` | Product or order not found |
| `422` | Validation error from FastAPI or Pydantic |
| `500` | Server-side checkout creation failure |
| `502` | Payment gateway session creation failure |
| `503` | External dependency or search index unavailable |

## 8. Notes On Current API Scope

The current API surface is intentionally small and focused on the implemented demo flow.

Current scope includes:

- catalog access
- authenticated order access
- checkout session creation
- payment gateway callback handling
- semantic retrieval
- AI recommendation and chat routes

Current scope does not include dedicated routes for:

- cart persistence through `carts` and `cart_items`
- product pagination
- admin operations
- user profile management through the backend API

## 9. Recommended Reviewer Workflow

To inspect the API in practice:

1. open the backend docs at `/docs`
2. call `GET /api/health`
3. call `GET /api/products`
4. call `POST /api/search/hybrid`
5. call one or more AI routes such as `/api/ai/product-finder`
6. authenticate through the frontend and test `/api/orders/me` and `/api/orders/checkout`

