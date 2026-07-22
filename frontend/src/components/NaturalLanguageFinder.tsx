"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

import type { Product, ProductFinderProduct } from "@/lib/api";
import {
  getSemanticSearchModelName,
  semanticProductSearch,
} from "@/lib/semanticProductSearch";

type NaturalLanguageFinderProps = {
  products: Product[];
  getQuantity: (productId: string) => number;
  onAddToCart: (product: ProductFinderProduct) => void;
  onDecreaseQuantity: (productId: string) => void;
  onIncreaseQuantity: (productId: string) => void;
};

export function NaturalLanguageFinder({
  products: catalogProducts,
  getQuantity,
  onAddToCart,
  onDecreaseQuantity,
  onIncreaseQuantity,
}: NaturalLanguageFinderProps) {
  const [query, setQuery] = useState("");
  const [summary, setSummary] = useState("");
  const [products, setProducts] = useState<ProductFinderProduct[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function searchIntent() {
    if (!query.trim()) {
      setError("Tell me what you are looking for.");
      return;
    }

    setIsLoading(true);
    setError("");
    setSummary("Loading the free browser AI model and matching your catalog...");
    setProducts([]);

    try {
      const matches = await semanticProductSearch(catalogProducts, query);
      setSummary(
        `Matched "${query.trim()}" against ${catalogProducts.length} scraped products using ${getSemanticSearchModelName()}.`
      );
      setProducts(matches);
    } catch {
      setError(
        "Could not load the browser AI model. Check your internet connection and try again."
      );
      setSummary("");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="rounded-lg border border-red-100 bg-white p-4 shadow-sm">
      <div>
        <p className="text-sm font-medium text-red-700">AI Feature 1</p>
        <h2 className="mt-1 text-lg font-bold text-slate-950">
          Free Semantic Product Finder
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Try phrases like breakfast under 300, snacks for kids, or biryani
          essentials.
        </p>
      </div>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="What are you shopping for?"
          className="h-10 flex-1 rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none placeholder:text-slate-600 focus:border-red-600"
        />

        <button
          type="button"
          onClick={searchIntent}
          disabled={isLoading}
          className="h-10 rounded-md bg-red-600 px-4 text-sm font-semibold text-white hover:bg-red-700 disabled:bg-slate-400"
        >
          {isLoading ? "Matching..." : "Find Products"}
        </button>
      </div>

      {error ? (
        <p className="mt-3 text-sm font-medium text-red-700">{error}</p>
      ) : null}

      {summary ? (
        <p className="mt-4 text-sm font-medium text-slate-800">{summary}</p>
      ) : null}

      {products.length > 0 ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {products.map((product) => {
            const quantity = getQuantity(product.id);

            return (
              <article
                key={product.id}
                className="rounded-md border border-slate-200 bg-slate-50 p-3 hover:border-red-200"
              >
                <Link href={`/products/${product.id}`}>
                  <div className="relative mb-3 aspect-square overflow-hidden rounded bg-white">
                    {product.image_url ? (
                      <Image
                        src={product.image_url}
                        alt={product.name}
                        fill
                        className="object-contain p-2"
                        sizes="(min-width: 1024px) 20vw, 50vw"
                      />
                    ) : null}
                  </div>
                </Link>

                <Link href={`/products/${product.id}`}>
                  <p className="line-clamp-2 text-sm font-semibold text-slate-950 hover:text-red-700">
                    {product.name}
                  </p>
                </Link>
                <p className="mt-1 text-sm font-bold text-red-700">
                  Tk {product.price}
                </p>
                <p className="mt-1 text-xs text-slate-600">{product.reason}</p>

                {quantity > 0 ? (
                  <div className="mt-3 flex h-9 items-center justify-between rounded-md border border-red-200 bg-white px-2">
                    <button
                      type="button"
                      onClick={() => onDecreaseQuantity(product.id)}
                      className="h-7 w-7 rounded text-sm font-bold text-red-700 hover:bg-red-50"
                    >
                      -
                    </button>
                    <span className="text-sm font-semibold text-slate-900">
                      {quantity}
                    </span>
                    <button
                      type="button"
                      onClick={() => onIncreaseQuantity(product.id)}
                      className="h-7 w-7 rounded text-sm font-bold text-red-700 hover:bg-red-50"
                    >
                      +
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => onAddToCart(product)}
                    className="mt-3 h-9 w-full rounded-md bg-red-600 text-sm font-semibold text-white hover:bg-red-700"
                  >
                    Add to Cart
                  </button>
                )}
              </article>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
