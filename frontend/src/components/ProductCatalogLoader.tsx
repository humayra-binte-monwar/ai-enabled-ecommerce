"use client";

import { useEffect, useRef, useState } from "react";

import { ProductCatalog } from "@/components/ProductCatalog";
import { getProducts, type Product } from "@/lib/api";

const MAX_ATTEMPTS = 7;

export function ProductCatalogLoader() {
  const [products, setProducts] = useState<Product[] | null>(null);
  const [attempt, setAttempt] = useState(1);
  const [isRetrying, setIsRetrying] = useState(false);
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadProducts() {
      setIsRetrying(attempt > 1);

      try {
        const loadedProducts = await getProducts();
        if (!cancelled) {
          setProducts(loadedProducts);
        }
      } catch {
        if (cancelled || attempt >= MAX_ATTEMPTS) {
          if (!cancelled) {
            setIsRetrying(false);
          }
          return;
        }

        setIsRetrying(true);
        retryTimer.current = setTimeout(() => {
          if (!cancelled) {
            setAttempt((currentAttempt) => currentAttempt + 1);
          }
        }, 3000);
      }
    }

    void loadProducts();

    return () => {
      cancelled = true;
      if (retryTimer.current) {
        clearTimeout(retryTimer.current);
      }
    };
  }, [attempt]);

  if (products) {
    return <ProductCatalog products={products} />;
  }

  const canRetry = attempt >= MAX_ATTEMPTS && !isRetrying;

  return (
    <section
      className="flex min-h-80 flex-col items-center justify-center rounded-xl border border-red-100 bg-white px-6 py-12 text-center shadow-sm"
      aria-live="polite"
    >
      <span className="mb-4 h-9 w-9 animate-spin rounded-full border-4 border-red-100 border-t-red-600" aria-hidden="true" />
      <h2 className="text-lg font-bold text-slate-950">Fetching fresh groceries</h2>
      {canRetry ? (
        <>
          <p className="mt-2 max-w-md text-sm leading-6 text-slate-600">
            The grocery service is taking a little longer to wake up. Please try again.
          </p>
          <button
            type="button"
            className="mt-5 rounded-md bg-red-700 px-4 py-2 text-sm font-semibold text-white hover:bg-red-800"
            onClick={() => {
              setAttempt(1);
            }}
          >
            Try again
          </button>
        </>
      ) : (
        <p className="mt-2 max-w-md text-sm leading-6 text-slate-600">
          {isRetrying
            ? `The service is waking up. Retrying automatically (${attempt} of ${MAX_ATTEMPTS})…`
            : "Connecting to the grocery service…"}
        </p>
      )}
    </section>
  );
}
