# Scraping and Data Preparation

## Purpose

This document describes the scraping and data preparation workflow implemented in this repository.

It focuses on:

- where the raw data comes from
- how the scraper works
- what fields are extracted
- how processed records are written
- what quality checks are currently generated
- current limitations visible in the code and data

This document is based on:

- [backend/app/scrapers/shawpno_scraper.py](/D:/humayra/ai-enabled-ecommerce/backend/app/scrapers/shawpno_scraper.py)
- [data/raw/shwapno_home.html](/D:/humayra/ai-enabled-ecommerce/data/raw/shwapno_home.html)
- [data/raw/shwapno_home_20260722T180512Z.html](/D:/humayra/ai-enabled-ecommerce/data/raw/shwapno_home_20260722T180512Z.html)
- [data/processed/products.json](/D:/humayra/ai-enabled-ecommerce/data/processed/products.json)
- [data/processed/data_quality_report.json](/D:/humayra/ai-enabled-ecommerce/data/processed/data_quality_report.json)

## 1. Data Source

The scraper targets the public Shwapno website:

- base URL: `https://www.shwapno.com`
- default start URL: `https://www.shwapno.com/?lang=en`

The implementation uses the public HTML rendered by the site and extracts category navigation and product card data from the page content.

The repository currently includes raw homepage HTML snapshots under `data/raw/` and a normalized product export under `data/processed/`.

## 2. Scraper Location

The scraper is implemented in:

- [backend/app/scrapers/shawpno_scraper.py](/D:/humayra/ai-enabled-ecommerce/backend/app/scrapers/shawpno_scraper.py)

The script uses:

- Playwright for browser automation
- HTML parsing through regular expression matching for category discovery
- client-side DOM evaluation for product extraction

## 3. Scraping Workflow

The implemented workflow is:

1. open the Shwapno homepage
2. save the fetched homepage HTML into `data/raw/`
3. extract category pages from homepage navigation metadata
4. visit the selected category pages
5. extract product cards from each page
6. normalize the product fields
7. deduplicate by product URL
8. write the final dataset to `data/processed/products.json`
9. generate a quality report in `data/processed/data_quality_report.json`

## 4. Start URLs and Category Discovery

The script defines:

- `BASE_URL = "https://www.shwapno.com"`
- `DEFAULT_START_URL = "https://www.shwapno.com/?lang=en"`

If no custom URLs are passed, the scraper starts from the default homepage and then expands to a limited set of category pages discovered from the homepage HTML.

Category discovery is handled by `extract_category_pages(raw_html)`.

Current behavior:

- it reads the homepage HTML as text
- it replaces escaped quotes
- it searches for repeated `"title":"...","url":"..."` patterns
- it ignores a small set of non-catalog slugs such as:
  - `/`
  - `about-us`
  - `contact-us`
  - `our-outlets`
- it removes duplicates
- it keeps only slugs that match a conservative text pattern

The scraper limits category coverage through:

- `MAX_CATEGORY_PAGES = 10`

If more than ten category candidates are found, the script samples them at fixed intervals instead of crawling all available categories.

## 5. Request and Browser Behavior

The script uses Playwright Chromium in either:

- headless mode by default
- headed mode when `--headed` is provided

The browser context is created with:

- viewport `1366 x 768`
- a custom user agent string:
  `AI Grocery Commerce demo scraper; respectful rate-limited catalog collection`

Page fetches are handled by `fetch_page(page, url)`.

Current request behavior:

- up to 3 attempts per page
- `wait_until="networkidle"`
- 60 second navigation timeout
- 1.5 second post-load wait
- exponential backoff based on the configured request delay

Configured delay:

- `REQUEST_DELAY_SECONDS = 1.5`

If a page contains `403 Forbidden`, the script raises an error and treats the page as blocked.

## 6. Product Extraction

Product extraction is implemented in `extract_products(page, category, scraped_at)`.

The function runs JavaScript in the page and reads elements matching:

- `.product-box`

For each product card, it extracts:

- product link from `.product-box-title a`
- image from `.product-box-gallery img`
- image source fallback from `.product-box-gallery source`
- active price from `.active-price`
- all visible price-related spans from `.product-price span`

The script limits the number of product cards processed per page through:

- `MAX_PRODUCTS_PER_PAGE = 80`

## 7. Normalized Output Fields

The normalized product record currently contains:

| Field | Source in scraper | Notes |
| --- | --- | --- |
| `id` | slugified product name | generated locally |
| `source_id` | slugified last segment of product URL | generated locally |
| `slug` | slugified last segment of product URL | generated locally |
| `name` | product title text | required for keeping record |
| `category` | category label from crawl target | assigned by scraper |
| `brand` | currently set to `null` | not parsed |
| `price` | parsed from `price_text` | must be positive |
| `old_price` | parsed from secondary price text | optional |
| `unit` | derived from a visible price span containing `per` | optional |
| `image_url` | image source from card | optional in schema, but present in current dataset |
| `product_url` | href from product link | required for keeping record |
| `stock_status` | currently hardcoded to `in_stock` | not dynamically parsed |
| `scraped_at` | current UTC timestamp | applied to all records in one run |

The current processed file in [data/processed/products.json](/D:/humayra/ai-enabled-ecommerce/data/processed/products.json) shows these fields directly.

## 8. Cleaning and Validation Rules

The scraper applies several cleaning rules before writing a record.

### 8.1 Slug generation

`slugify(text)`:

- lowercases text
- replaces non-alphanumeric characters with `-`
- trims leading and trailing `-`

This is used for:

- `id`
- `source_id`
- `slug`

### 8.2 Price parsing

`clean_price(text)`:

- extracts the first numeric value from a string
- removes comma separators
- returns `float`

If a valid positive price cannot be parsed, the record is skipped.

### 8.3 Domain filtering

The scraper only keeps product URLs whose host matches the configured site domain.

This prevents the dataset from including off-site links.

### 8.4 Duplicate removal

Deduplication is based on `product_url`.

If the same URL appears more than once across pages:

- the first copy is kept
- later copies are counted as rejected duplicates

## 9. Output Files

The scraper writes two main outputs.

### 9.1 Raw HTML

The homepage HTML is saved to `data/raw/` using a timestamped filename:

- example: `shwapno_home_20260722T180512Z.html`

This preserves a raw page snapshot that can be inspected later if the site structure changes.

The repository also contains:

- [data/raw/shwapno_home.html](/D:/humayra/ai-enabled-ecommerce/data/raw/shwapno_home.html)

### 9.2 Processed product dataset

The normalized catalog is written to:

- [data/processed/products.json](/D:/humayra/ai-enabled-ecommerce/data/processed/products.json)

This file is the main catalog source used by:

- the product seed script
- the backend fallback product loader
- embedding generation

### 9.3 Data quality report

The scraper generates:

- [data/processed/data_quality_report.json](/D:/humayra/ai-enabled-ecommerce/data/processed/data_quality_report.json)

This report summarizes the current scrape output.

## 10. Current Data Quality Report

The latest committed quality report contains:

- `generated_at`: `2026-07-22T18:06:06.839028+00:00`
- `record_count`: `421`
- `rejected_or_duplicate_count`: `19`
- `missing_image_count`: `0`
- `missing_source_url_count`: `0`
- `min_price`: `5.0`
- `max_price`: `2100.0`

Current category counts:

- `Atta Maida & Suji`: `30`
- `Condensed Milk & Cream`: `6`
- `Deodorant`: `45`
- `Floor Glass & Wood Cleaners`: `45`
- `Food`: `49`
- `Frozen`: `27`
- `General`: `68`
- `Pasta`: `21`
- `Sauces & Pickles`: `50`
- `Spices`: `48`
- `Storage & Containers`: `32`

## 11. How Categories Are Assigned

Category values come from the crawl target, not from a separate product-detail page or category taxonomy API.

This leads to two types of categories in the current dataset:

- `General` for products collected directly from the homepage start URL
- named categories for products collected from discovered category pages

This behavior is visible in the scraper code:

- the homepage target is always added as `("General", url)`
- additional targets come from `extract_category_pages(...)`

As a result, products scraped from the homepage remain in the `General` bucket even if they belong to a more specific retail category.

## 12. Command Usage

The scraper can be run directly as a Python module script.

Current supported arguments:

- `--url` to provide one or more explicit catalog URLs
- `--headed` to show the browser window

Example command:

```bash
cd backend
python app/scrapers/shawpno_scraper.py
```

Example with a visible browser:

```bash
cd backend
python app/scrapers/shawpno_scraper.py --headed
```

Example with explicit URLs:

```bash
cd backend
python app/scrapers/shawpno_scraper.py --url "https://www.shwapno.com/?lang=en"
```

## 13. Downstream Use of Scraped Data

The processed product dataset is reused in multiple later stages of the project.

### Product seeding

[backend/scripts/seed_products.py](/D:/humayra/ai-enabled-ecommerce/backend/scripts/seed_products.py) reads `data/processed/products.json` and upserts the records into the `products` table.

### Backend fallback reads

[backend/app/services/product_service.py](/D:/humayra/ai-enabled-ecommerce/backend/app/services/product_service.py) can load the same processed file directly if the Supabase read fails.

### Embedding generation

[backend/scripts/generate_product_embeddings.py](/D:/humayra/ai-enabled-ecommerce/backend/scripts/generate_product_embeddings.py) reads the processed products and converts them into embedding documents for semantic search.

## 14. Current Limitations

The following limitations are visible from the current scraper implementation and data artifacts.

### 14.1 Limited category coverage

The scraper limits discovered category pages to at most 10 targets.

This means the current dataset is bounded rather than exhaustive.

### 14.2 Homepage-driven `General` category

Products collected from the homepage are labeled `General`.

This is one reason the final dataset still contains a large `General` bucket.

### 14.3 No product detail crawl

The scraper does not currently visit each product detail page.

Because of that:

- `brand` is set to `null`
- `stock_status` is hardcoded to `in_stock`
- richer product metadata is not collected

### 14.4 Selector dependence

The extraction logic depends on current page selectors such as:

- `.product-box`
- `.product-box-title a`
- `.product-box-gallery img`
- `.active-price`

If the site markup changes, the scraper may stop collecting valid records.

### 14.5 Partial price and unit parsing

The current parser:

- reads the first numeric value from the visible price text
- treats a text snippet containing `per` as the unit

This works for the current dataset shape, but it is still a heuristic.

### 14.6 No dedicated raw JSON export

The current raw artifact is the saved homepage HTML snapshot. The scraper does not also write a separate intermediate raw JSON file for every crawl target.

### 14.7 No committed scheduler or recurring ingestion flow

The repository contains a runnable scraper script, but it does not include a committed job scheduler or recurring ingestion pipeline.

## 15. Notes on Compliance and Scope

The repository contains the scraper code and raw page snapshots, but it does not contain a separate committed policy review document for:

- `robots.txt`
- terms of service
- crawl approval notes

For that reason, this document only describes the implemented technical workflow. It does not make any claim about a separate documented compliance review beyond what is present in the repository.

## 16. Summary

The current data collection flow is a lightweight Playwright-based scraper built around public homepage and category pages from Shwapno.

Its main outputs are:

- raw homepage HTML snapshots
- a normalized `products.json` dataset
- a quality report with record counts, category counts, duplicate counts, and price range

The current approach is sufficient for generating a usable demo catalog, but it remains intentionally simple. The main limitations are bounded category coverage, incomplete metadata extraction, and dependence on homepage/category page structure rather than deeper product-detail crawling.

