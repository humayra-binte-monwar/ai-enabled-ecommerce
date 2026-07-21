import json
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def clean_price(text: str) -> float:
    numbers = re.findall(r"\d[\d,]*", text)
    if not numbers:
        return 0

    return float(numbers[0].replace(",", ""))


def scrape_shwapno_products():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    scraped_at = datetime.now(timezone.utc).isoformat()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        page.goto("https://www.shwapno.com/?lang=en", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)

        raw_html = page.content()
        (RAW_DIR / "shwapno_home.html").write_text(raw_html, encoding="utf-8")

        if "403 Forbidden" in raw_html:
            browser.close()
            raise RuntimeError("Shwapno blocked the scraper with 403 Forbidden.")

        products = page.evaluate(
            """
            () => {
                const getFirstSrcFromSet = (srcset) => {
                    if (!srcset) {
                        return "";
                    }

                    return srcset.split(",")[0]?.trim()?.split(" ")[0] || "";
                };

                return Array.from(document.querySelectorAll(".product-box"))
                    .slice(0, 80)
                    .map((card) => {
                        const productLink = card.querySelector(".product-box-title a");
                        const image = card.querySelector(".product-box-gallery img");
                        const source = card.querySelector(".product-box-gallery source");
                        const price = card.querySelector(".active-price");
                        const unit = Array.from(card.querySelectorAll(".product-price span"))
                            .map((span) => span.innerText.trim())
                            .find((text) => text.toLowerCase().includes("per")) || "Per Piece";
                        const imageSrcSet =
                            image?.getAttribute("srcset") ||
                            source?.getAttribute("srcset") ||
                            "";

                        return {
                            name: productLink?.innerText?.trim() || "",
                            price_text: price?.innerText || "",
                            unit,
                            image_url:
                                image?.getAttribute("src") ||
                                image?.currentSrc ||
                                getFirstSrcFromSet(imageSrcSet),
                            product_url: productLink?.href || "",
                        };
                    })
                    .filter((product) => product.name && product.price_text);
            }
            """
        )

        browser.close()

    unique_products = []
    seen_ids = set()

    for item in products:
        name = item["name"]
        price = clean_price(item["price_text"])

        if not name or price <= 0:
            continue

        product_id = slugify(name)

        if product_id in seen_ids:
            continue

        seen_ids.add(product_id)
        unique_products.append(
            {
                "id": product_id,
                "name": name,
                "category": "General",
                "brand": None,
                "price": price,
                "unit": item["unit"],
                "image_url": item["image_url"],
                "product_url": item["product_url"],
                "stock_status": "in_stock",
                "scraped_at": scraped_at,
            }
        )

    if not unique_products:
        raise RuntimeError("No products found. The page loaded, but selectors need adjustment.")

    output_file = PROCESSED_DIR / "products.json"
    output_file.write_text(
        json.dumps(unique_products, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with_images = sum(1 for product in unique_products if product["image_url"])
    print(f"Saved {len(unique_products)} products to {output_file}")
    print(f"Products with images: {with_images}")


if __name__ == "__main__":
    scrape_shwapno_products()
