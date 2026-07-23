# AI Use Cases

## Purpose

This document describes the AI-related features implemented in this repository.

It focuses on:

- the user-facing AI features
- the backend routes that support them
- how each feature works internally
- where retrieval, heuristics, and provider-assisted generation are used
- guardrails and grounding behavior
- current limitations visible in the code

This document is based on:

- [backend/app/api/ai.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/ai.py)
- [backend/app/api/search.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/search.py)
- [backend/app/services/product_finder_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/product_finder_service.py)
- [backend/app/services/bundle_planner_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/bundle_planner_service.py)
- [backend/app/services/cart_optimizer_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/cart_optimizer_service.py)
- [backend/app/services/hybrid_search_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/hybrid_search_service.py)
- [backend/app/services/embedding_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/embedding_service.py)
- [backend/app/ai/agent.py](/D:/humayra/ai-enabled-ecommerce/backend/app/ai/agent.py)
- [backend/app/ai/tools.py](/D:/humayra/ai-enabled-ecommerce/backend/app/ai/tools.py)
- [backend/app/ai/prompts.py](/D:/humayra/ai-enabled-ecommerce/backend/app/ai/prompts.py)
- [backend/app/ai/guardrails.py](/D:/humayra/ai-enabled-ecommerce/backend/app/ai/guardrails.py)
- [frontend/src/components/NaturalLanguageFinder.tsx](/D:/humayra/ai-enabled-ecommerce/frontend/src/components/NaturalLanguageFinder.tsx)
- [frontend/src/components/BundlePlanner.tsx](/D:/humayra/ai-enabled-ecommerce/frontend/src/components/BundlePlanner.tsx)
- [frontend/src/components/CartOptimizer.tsx](/D:/humayra/ai-enabled-ecommerce/frontend/src/components/CartOptimizer.tsx)
- [frontend/src/components/Chatbot.tsx](/D:/humayra/ai-enabled-ecommerce/frontend/src/components/Chatbot.tsx)

## 1. Overview

The project contains four AI-related user-facing capabilities:

1. semantic product finder
2. grocery bundle planner
3. cart health and savings optimizer
4. conversational grocery copilot

These capabilities do not all use the same implementation pattern.

The current codebase uses a mix of:

- semantic retrieval with embeddings
- rule-based intent detection
- heuristic ranking and filtering
- optional provider-assisted response synthesis

The current backend supports both:

- task-specific AI endpoints
- a general chat endpoint

## 2. Design Principles Visible in the Code

Several design choices appear consistently across the implementation.

### 2.1 Ground recommendations in the catalog

The project is designed to recommend products that already exist in the catalog.

This is visible in the code because:

- semantic search returns product rows
- task-specific services read from `load_products()`
- chat responses include structured product cards
- chat citations include `product_id` and `source_url`
- prompts instruct the model not to invent products or prices

### 2.2 Keep price and product identity deterministic

The system does not rely on a model to invent:

- product names
- product prices
- stock information
- source links

The prompt file [backend/app/ai/prompts.py](/D:/humayra/ai-enabled-ecommerce/backend/app/ai/prompts.py) explicitly instructs the assistant to recommend only products returned by catalog tools.

### 2.3 Use provider-assisted output only when available

The chat system can use a configured provider, but it also has a deterministic fallback path.

This behavior is implemented in:

- `get_llm_client()`
- `synthesize_with_llm(...)`

If provider configuration or dependencies are not available, the system still returns a grounded response using the deterministic tool outputs.

## 3. AI Feature Map

The following table summarizes the implemented features.

| Feature | Frontend entry point | Backend route | Main implementation pattern |
| --- | --- | --- | --- |
| Semantic Product Finder | `NaturalLanguageFinder` | `POST /api/search/hybrid` | embedding retrieval with fallback |
| Product Finder API | not the primary UI path | `POST /api/ai/product-finder` | heuristic keyword and intent matching |
| Smart Grocery Bundle Planner | `BundlePlanner` | `POST /api/ai/bundle-planner` | heuristic planning over real catalog items |
| Cart Health + Savings Optimizer | `CartOptimizer` | `POST /api/ai/cart-optimizer` | rule-based cart analysis over real catalog items |
| Grocery Copilot Chat | `Chatbot` | `POST /api/ai/chat` | grounded tools plus optional LLM synthesis |

## 4. Use Case 1: Semantic Product Finder

## 4.1 User goal

Allow the user to search the product catalog using natural language such as:

- `breakfast under 300`
- `snacks for kids`
- `biryani essentials`

## 4.2 Frontend entry point

The user-facing component is:

- [frontend/src/components/NaturalLanguageFinder.tsx](/D:/humayra/ai-enabled-ecommerce/frontend/src/components/NaturalLanguageFinder.tsx)

The UI:

- accepts a free-text query
- first calls the server-side semantic search endpoint
- falls back to a browser-side semantic method if the server index is not ready

The component labels this feature in the UI as:

- `AI Feature 1`
- `Free Semantic Product Finder`

## 4.3 Backend route

The primary backend route used by the UI is:

- `POST /api/search/hybrid`

This route is implemented in:

- [backend/app/api/search.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/search.py)

## 4.4 Core implementation

The semantic retrieval flow is implemented through:

- [backend/app/services/hybrid_search_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/hybrid_search_service.py)
- [backend/app/services/embedding_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/embedding_service.py)
- the SQL function `match_products_hybrid(...)` defined in migration `0003`

The current flow is:

1. receive a query
2. optionally infer a budget from text such as `under 500 taka`
3. generate a 384-dimensional embedding for the query
4. call the Supabase RPC function `match_products_hybrid(...)`
5. return ranked product matches with a semantic score

## 4.5 Inputs

Supported request fields are:

- `query`
- optional `category`
- optional `min_price`
- optional `max_price`
- optional `limit`

## 4.6 Outputs

The response returns:

- the original query
- applied filters
- ranked products
- a semantic similarity score per product

Each returned product includes:

- product identity
- category
- price
- image
- source URL
- tags
- normalized category
- product type
- reason text

## 4.7 Fallback behavior

If the server-side embedding index is not available, the frontend attempts a browser fallback.

This behavior is visible in:

- [frontend/src/components/NaturalLanguageFinder.tsx](/D:/humayra/ai-enabled-ecommerce/frontend/src/components/NaturalLanguageFinder.tsx)

The summary text shown by the frontend makes the distinction explicit:

- server-side embedding index path
- browser fallback path

## 4.8 Grounding

This use case is grounded because the result set comes from the product catalog rather than from free-form text generation.

## 4.9 Current limitations

- The frontend’s main natural-language finder uses the semantic search route, not the `product-finder` route.
- The fallback browser implementation is separate from the backend retrieval path.
- The retrieved `reason` string is generic in the SQL function.
- No reranking stage using a separate model appears in the current code.

## 5. Use Case 1B: Product Finder API

## 5.1 Purpose

The repository also contains a second product-finder path:

- `POST /api/ai/product-finder`

This is implemented in:

- [backend/app/services/product_finder_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/product_finder_service.py)

## 5.2 Implementation pattern

This route does not use the embedding index.

Instead, it uses:

- intent keyword dictionaries
- synonym mapping
- stop-word removal
- simple budget extraction
- heuristic term scoring against product text

## 5.3 How it works

The service:

1. extracts a budget from the query when possible
2. expands the query into intent terms
3. classifies whether the query is food-focused
4. filters out clearly non-food products for food-oriented queries
5. scores products by matched terms and budget fit
6. sorts results by score and price
7. returns up to eight matches

## 5.4 Examples of supported intents

The implementation contains explicit intent coverage for terms such as:

- `breakfast`
- `cleaning`
- `biryani`
- `healthy`
- `kids`
- `iftar`
- `picnic`
- `tea`

## 5.5 Current role in the system

This route exists and is functional, but the main visible frontend finder component currently uses semantic search first rather than this endpoint.

## 5.6 Current limitations

- matching is heuristic rather than embedding-based
- intent coverage depends on hardcoded dictionaries
- brand extraction is limited by the underlying dataset
- the route may be less semantically flexible than the hybrid search path

## 6. Use Case 2: Smart Grocery Bundle Planner

## 6.1 User goal

Build a practical grocery basket based on:

- budget
- household size
- number of days
- meal need
- optional preference

## 6.2 Frontend entry point

The user-facing component is:

- [frontend/src/components/BundlePlanner.tsx](/D:/humayra/ai-enabled-ecommerce/frontend/src/components/BundlePlanner.tsx)

The UI labels this feature as:

- `AI Feature 2`
- `Smart Grocery Bundle Planner`

## 6.3 Backend route

The route is:

- `POST /api/ai/bundle-planner`

Implemented in:

- [backend/app/api/ai.py](/D:/humayra/ai-enabled-ecommerce/backend/app/api/ai.py)

## 6.4 Core implementation

The main logic is in:

- [backend/app/services/bundle_planner_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/bundle_planner_service.py)

This feature is currently heuristic and catalog-grounded.

The implementation does not call an LLM for bundle generation.

## 6.5 How it works

The planner:

1. builds a query from `meal_type` and optional `preference`
2. derives intent terms using `get_intent_terms(...)`
3. expands the term set using the `MEAL_NEEDS` dictionary
4. decides whether the request is food-only
5. removes non-food-only intent labels when necessary
6. loops through candidate terms
7. finds matching catalog products
8. sorts candidates by price
9. estimates recommended quantity based on people and duration
10. reduces quantity when needed to stay within budget
11. returns selected items and budget summary

## 6.6 Quantity estimation

Quantity estimation is implemented with:

- `QUANTITY_RULES`
- package-size parsing from product names
- scaling logic based on people and duration

Examples in code include rules for:

- rice
- dal
- flour
- oil
- egg
- milk
- bread
- sugar
- salt
- tea

Each selected bundle item returns:

- `recommended_quantity`
- `suggested_quantity`
- a reason string

This allows the response to distinguish between:

- the ideal estimated amount
- the reduced amount used to fit the budget

## 6.7 Outputs

The route returns:

- a summary
- estimated total
- remaining budget
- a list of item recommendations

Each recommendation maps to a real catalog product.

## 6.8 Grounding

The planner is grounded because it selects only from actual catalog products loaded through `load_products()`.

## 6.9 Current limitations

- The planner uses heuristic matching rather than semantic retrieval.
- It does not model nutrition, recipe completeness, or store inventory beyond current product availability in the dataset.
- It does not call a language model to reason over meal plans.
- Quantity logic is rule-based and approximate.

## 7. Use Case 3: Cart Health + Savings Optimizer

## 7.1 User goal

Review the current cart and suggest:

- cheaper alternatives
- missing essential items
- more balanced choices for a stated goal

## 7.2 Frontend entry point

The user-facing component is:

- [frontend/src/components/CartOptimizer.tsx](/D:/humayra/ai-enabled-ecommerce/frontend/src/components/CartOptimizer.tsx)

The UI labels this feature as:

- `AI Feature 3`
- `Cart Health + Savings Optimizer`

## 7.3 Backend route

The route is:

- `POST /api/ai/cart-optimizer`

## 7.4 Core implementation

The main logic is in:

- [backend/app/services/cart_optimizer_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/cart_optimizer_service.py)

This feature is also heuristic and grounded.

## 7.5 How it works

The optimizer:

1. reads the current cart items supplied by the frontend
2. computes the cart total
3. checks the goal text for budget-related terms
4. searches for cheaper same-group alternatives when budget help is requested
5. checks whether essential staples are missing
6. suggests low-price essentials that are not already in the cart
7. checks whether the goal asks for healthier or more balanced choices
8. adds a healthier staple if no healthy item appears to be present
9. flags mismatches between a meal-focused goal and a cart that contains non-food cleaning or personal-care items

## 7.6 Product grouping and alternatives

The optimizer uses a `STAPLE_GROUPS` dictionary to group products by type.

Examples include:

- rice
- dal
- milk
- egg
- oil
- noodles
- onion
- potato
- sugar
- salt

This grouping is used for:

- alternative search
- missing staple detection

## 7.7 Outputs

The response returns:

- a short summary
- the computed cart total
- up to five suggestions

Each suggestion includes:

- suggestion type
- message
- optional product information

This means the UI can either:

- show an informational message
- or provide an add-to-cart action when a real product is attached

## 7.8 Grounding

The optimizer only suggests products that exist in the current catalog.

## 7.9 Current limitations

- health-related reasoning is basic and keyword-driven
- there is no nutritional database or ingredient-level analysis
- product grouping is manual and finite
- the optimizer does not consider checkout history or user preferences beyond the current goal string

## 8. Use Case 4: Conversational Grocery Copilot

## 8.1 User goal

Provide a single conversational interface for:

- catalog search
- bundle requests
- price comparison
- cart review
- cart modifications

## 8.2 Frontend entry point

The user-facing component is:

- [frontend/src/components/Chatbot.tsx](/D:/humayra/ai-enabled-ecommerce/frontend/src/components/Chatbot.tsx)

The component displays:

- conversation history
- product cards
- structured cart actions
- provider readiness status

## 8.3 Backend route

The route is:

- `POST /api/ai/chat`

## 8.4 Core implementation pattern

The chat assistant is implemented as a hybrid system in:

- [backend/app/ai/agent.py](/D:/humayra/ai-enabled-ecommerce/backend/app/ai/agent.py)
- [backend/app/ai/tools.py](/D:/humayra/ai-enabled-ecommerce/backend/app/ai/tools.py)

The current pattern is:

1. detect likely intent using rule-based functions
2. call a tool that works on catalog or cart data
3. optionally send the structured result to an LLM for final wording
4. return structured actions and product results

## 8.5 Implemented intent types

The current chat logic explicitly handles:

- greetings
- cart status
- clear cart
- remove from cart
- increase quantity
- decrease quantity
- cart review
- bundle requests
- price comparison
- product search
- add to cart
- health-related shopping questions

## 8.6 Tool layer

The chat tool layer includes:

- `search_products_tool`
- `compare_prices_tool`
- `plan_bundle_tool`
- `optimize_cart_tool`
- structured cart action builders

The tool layer is grounded because it works from:

- catalog products
- current cart items
- deterministic service outputs

## 8.7 Provider-assisted synthesis

The assistant can optionally use a language model through `ChatOpenAI` when:

- `AI_AGENT_ENABLED` is true
- provider credentials are configured
- the LangChain dependency is available

Supported providers in code:

- Groq
- OpenAI
- xAI

If no provider is available, the assistant returns the deterministic message.

## 8.8 Chat-specific behavior

The frontend and backend support structured cart operations such as:

- add item
- remove item
- increase quantity
- decrease quantity
- clear cart

The response indicates whether an action:

- requires confirmation
- or has already been applied by the app

The frontend applies non-confirmation actions automatically.

## 8.9 Current limitations

- intent detection is rule-based
- the chat path still depends on the quality of underlying heuristic services
- memory is session-scoped through the request flow rather than backed by a dedicated conversation store
- the route is not authenticated in the reviewed backend code

## 9. Guardrails and Safety Behavior

## 9.1 Prompt-level guardrails

The prompt file [backend/app/ai/prompts.py](/D:/humayra/ai-enabled-ecommerce/backend/app/ai/prompts.py) includes rules such as:

- recommend only products returned by tools
- never invent product names, prices, stock, discounts, or source URLs
- use `Tk` for pricing
- avoid recommending non-food products for meal-related requests
- treat health and nutrition content as general information only

## 9.2 Health guardrails

The guardrail file [backend/app/ai/guardrails.py](/D:/humayra/ai-enabled-ecommerce/backend/app/ai/guardrails.py) defines:

- general health terms
- more sensitive health-related terms

When health-related questions are detected, the chat flow can prepend a disclaimer.

Sensitive cases include terms such as:

- allergy
- diabetic
- pregnancy
- baby formula
- medicine
- supplement

In those cases, the disclaimer explicitly says the system is not providing medical advice.

## 9.3 Food versus non-food protection

Both the product finder and bundle planner contain logic to avoid returning non-food items for food-focused requests.

This is implemented through term lists such as:

- `NON_FOOD_TERMS`
- `FOOD_INTENTS`
- food-only filtering checks

## 10. Retrieval and Evaluation Support

The AI features sit on top of the broader retrieval pipeline documented elsewhere in the repository.

Key supporting pieces include:

- `products.json` as the normalized catalog
- `product_embeddings` as vector storage
- `match_products_hybrid(...)` as the retrieval function
- `data/evaluation/grocery_retrieval_eval.json` as retrieval test input
- `data/evaluation/retrieval_report.json` as the current evaluation report

Current reported retrieval metrics in the committed report are:

- `queries`: `15`
- `recall_at_5`: `1.0`
- `mrr_at_5`: `0.9333`

These metrics apply to the retrieval layer rather than to every higher-level AI workflow.

## 11. Current Implementation Boundaries

The current AI subsystem is broader than a simple chat widget, but it is not a single end-to-end agentic planning system.

The main boundaries visible in the code are:

- semantic retrieval is used explicitly in the search route, not uniformly in every AI route
- some features are retrieval-based, while others are mostly heuristic
- the chat assistant is a grounded orchestration layer over deterministic tools
- provider-assisted generation is optional and limited to synthesis rather than authoritative product generation

## 12. Summary

The repository currently implements four practical AI-related shopping features:

- a semantic product finder
- a bundle planner
- a cart optimizer
- a conversational grocery copilot

The system emphasizes grounded outputs and practical product actions rather than unconstrained text generation.

The strongest grounding path in the current code is the semantic search route backed by embeddings and database retrieval. The bundle planner and cart optimizer are currently rule-based but still grounded in real catalog products. The chat assistant combines these grounded tools with optional provider-assisted wording and explicit guardrails around hallucination and health-related content.

