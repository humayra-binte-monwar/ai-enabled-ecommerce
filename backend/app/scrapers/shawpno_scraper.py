import argparse
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
BASE_URL = "https://www.shwapno.com"
DEFAULT_START_URL = f"{BASE_URL}/?lang=en"
MAX_CATEGORY_PAGES = 10
MAX_PRODUCTS_PER_PAGE = 80
REQUEST_DELAY_SECONDS = 1.5


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def clean_price(text: str) -> float | None:
    numbers = re.findall(r"\d[\d,]*(?:\.\d+)?", text)
    if not numbers:
        return None
    return float(numbers[0].replace(",", ""))


def extract_category_pages(raw_html: str) -> list[tuple[str, str]]:
    """Read public navigation metadata rendered on the homepage.

    The site renders category titles/slugs in its Next.js response. Keeping this
    parser separate makes the crawler easy to review when the site changes.
    """

    navigation_html = raw_html.replace(r'\"', '"')
    pattern = re.compile(r'"title":"(?P<title>[^"]+)","url":"(?P<slug>[^"]+)"')
    ignored_slugs = {"", "/", "about-us", "contact-us", "our-outlets"}
    seen_slugs = set()
    categories = []

    for match in pattern.finditer(navigation_html):
        title = match.group("title").strip().replace("\\u0026", "&")
        slug = match.group("slug").strip().lstrip("/")
        if not title or not slug or slug in ignored_slugs or slug in seen_slugs:
            continue
        if not re.fullmatch(r"[A-Za-z0-9&\- ]+", slug):
            continue

        seen_slugs.add(slug)
        categories.append((title, urljoin(f"{BASE_URL}/", slug)))

    if len(categories) <= MAX_CATEGORY_PAGES:
        return categories

    step = len(categories) / MAX_CATEGORY_PAGES
    return [categories[int(index * step)] for index in range(MAX_CATEGORY_PAGES)]


def fetch_page(page: Page, url: str) -> str:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(1500)
            html = page.content()
            if "403 Forbidden" in html:
                raise RuntimeError("Shwapno blocked the scraper with 403 Forbidden.")
            return html
        except (PlaywrightError, RuntimeError) as error:
            last_error = error
            if attempt == 2:
                break
            time.sleep((attempt + 1) * REQUEST_DELAY_SECONDS)

    raise RuntimeError(f"Could not load {url}: {last_error}")


def extract_products(page: Page, category: str, scraped_at: str) -> list[dict]:
    raw_products = page.evaluate(
        """
        (maxProducts) => {
            const firstSrcFromSet = (srcset) => {
                if (!srcset) return "";
                return srcset.split(",")[0]?.trim()?.split(" ")[0] || "";
            };

            return Array.from(document.querySelectorAll(".product-box"))
                .slice(0, maxProducts)
                .map((card) => {
                    const productLink = card.querySelector(".product-box-title a");
                    const image = card.querySelector(".product-box-gallery img");
                    const source = card.querySelector(".product-box-gallery source");
                    const activePrice = card.querySelector(".active-price");
                    const prices = Array.from(card.querySelectorAll(".product-price span"))
                        .map((span) => span.innerText.trim());
                    const unit = prices.find((text) => text.toLowerCase().includes("per")) || null;
                    const imageSrcSet = image?.getAttribute("srcset") || source?.getAttribute("srcset") || "";

                    return {
                        name: productLink?.innerText?.trim() || "",
                        price_text: activePrice?.innerText || "",
                        old_price_text: prices.find((text) => /৳|tk|taka/i.test(text) && text !== activePrice?.innerText) || "",
                        unit,
                        image_url: image?.getAttribute("src") || image?.currentSrc || firstSrcFromSet(imageSrcSet),
                        product_url: productLink?.href || "",
                    };
                })
                .filter((product) => product.name && product.price_text && product.product_url);
        }
        """,
        MAX_PRODUCTS_PER_PAGE,
    )

    products = []
    for item in raw_products:
        price = clean_price(item["price_text"])
        if price is None or price <= 0:
            continue

        product_url = item["product_url"]
        if urlparse(product_url).netloc != urlparse(BASE_URL).netloc:
            continue

        products.append(
            {
                "id": slugify(item["name"]),
                "source_id": slugify(product_url.rstrip("/").split("/")[-1]),
                "slug": slugify(product_url.rstrip("/").split("/")[-1]),
                "name": item["name"],
                "category": category,
                "brand": None,
                "price": price,
                "old_price": clean_price(item["old_price_text"]),
                "unit": item["unit"],
                "image_url": item["image_url"],
                "product_url": product_url,
                "stock_status": "in_stock",
                "scraped_at": scraped_at,
            }
        )

    return products


def build_quality_report(products: list[dict], rejected_count: int) -> dict:
    category_counts = Counter(product["category"] for product in products)
    prices = [product["price"] for product in products]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(products),
        "category_counts": dict(sorted(category_counts.items())),
        "missing_image_count": sum(not product["image_url"] for product in products),
        "missing_source_url_count": sum(not product["product_url"] for product in products),
        "rejected_or_duplicate_count": rejected_count,
        "min_price": min(prices) if prices else None,
        "max_price": max(prices) if prices else None,
    }


def scrape_shwapno_products(start_urls: list[str] | None = None, headless: bool = True) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    scraped_at = datetime.now(timezone.utc).isoformat()
    start_urls = start_urls or [DEFAULT_START_URL]
    all_products: list[dict] = []
    seen_product_urls: set[str] = set()
    rejected_count = 0

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="AI Grocery Commerce demo scraper; respectful rate-limited catalog collection",
        )
        page = context.new_page()

        homepage_html = fetch_page(page, start_urls[0])
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        (RAW_DIR / f"shwapno_home_{timestamp}.html").write_text(homepage_html, encoding="utf-8")

        targets: list[tuple[str, str]] = [("General", url) for url in start_urls]
        if start_urls == [DEFAULT_START_URL]:
            targets.extend(extract_category_pages(homepage_html))

        for category, url in targets:
            try:
                if url != start_urls[0]:
                    fetch_page(page, url)
                    time.sleep(REQUEST_DELAY_SECONDS)
                page_products = extract_products(page, category, scraped_at)
            except RuntimeError as error:
                print(f"Skipped {url}: {error}")
                continue

            for product in page_products:
                if product["product_url"] in seen_product_urls:
                    rejected_count += 1
                    continue
                seen_product_urls.add(product["product_url"])
                all_products.append(product)

        browser.close()

    if not all_products:
        raise RuntimeError("No products found. Check current site selectors before replacing the dataset.")

    (PROCESSED_DIR / "products.json").write_text(
        json.dumps(all_products, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    report = build_quality_report(all_products, rejected_count)
    (PROCESSED_DIR / "data_quality_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect public Shwapno catalog pages.")
    parser.add_argument("--url", action="append", dest="urls", help="Catalog URL to scrape; repeat for multiple pages.")
    parser.add_argument("--headed", action="store_true", help="Show the browser while scraping.")
    args = parser.parse_args()
    scrape_shwapno_products(start_urls=args.urls, headless=not args.headed)
