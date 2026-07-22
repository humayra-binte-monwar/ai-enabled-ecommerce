"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

import { planGroceryBundle, type BundlePlannerItem } from "@/lib/api";

type BundlePlannerProps = {
  getQuantity: (productId: string) => number;
  onAddToCart: (product: BundlePlannerItem) => void;
  onDecreaseQuantity: (productId: string) => void;
  onIncreaseQuantity: (productId: string) => void;
};

export function BundlePlanner({
  getQuantity,
  onAddToCart,
  onDecreaseQuantity,
  onIncreaseQuantity,
}: BundlePlannerProps) {
  const [budget, setBudget] = useState(1500);
  const [people, setPeople] = useState(2);
  const [durationDays, setDurationDays] = useState(3);
  const [mealType, setMealType] = useState("breakfast and dinner");
  const [preference, setPreference] = useState("family essentials");
  const [summary, setSummary] = useState("");
  const [estimatedTotal, setEstimatedTotal] = useState(0);
  const [remainingBudget, setRemainingBudget] = useState(0);
  const [items, setItems] = useState<BundlePlannerItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function generateBundle() {
    setIsLoading(true);
    setError("");
    setSummary("");
    setItems([]);

    try {
      const response = await planGroceryBundle({
        budget,
        people,
        duration_days: durationDays,
        meal_type: mealType,
        preference,
      });

      setSummary(response.summary);
      setEstimatedTotal(response.estimated_total);
      setRemainingBudget(response.remaining_budget);
      setItems(response.items);
    } catch {
      setError("Could not generate a bundle. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="rounded-lg border border-red-100 bg-white p-4 shadow-sm">
      <div>
        <p className="text-sm font-medium text-red-700">AI Feature 2</p>
        <h2 className="mt-1 text-lg font-bold text-slate-950">
          Smart Grocery Bundle Planner
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Build a practical grocery basket using your budget, household size,
          and meal needs.
        </p>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="text-sm font-medium text-slate-700">
          Budget
          <input
            type="number"
            value={budget}
            onChange={(event) => setBudget(Number(event.target.value))}
            className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none focus:border-red-600"
          />
        </label>

        <label className="text-sm font-medium text-slate-700">
          People
          <input
            type="number"
            value={people}
            onChange={(event) => setPeople(Number(event.target.value))}
            className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none focus:border-red-600"
          />
        </label>

        <label className="text-sm font-medium text-slate-700">
          Days
          <input
            type="number"
            value={durationDays}
            onChange={(event) => setDurationDays(Number(event.target.value))}
            className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none focus:border-red-600"
          />
        </label>

        <label className="text-sm font-medium text-slate-700">
          Meal Need
          <input
            value={mealType}
            onChange={(event) => setMealType(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none focus:border-red-600"
          />
        </label>
      </div>

      <label className="mt-3 block text-sm font-medium text-slate-700">
        Preference
        <input
          value={preference}
          onChange={(event) => setPreference(event.target.value)}
          placeholder="family essentials, healthy, kids..."
          className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none placeholder:text-slate-600 focus:border-red-600"
        />
      </label>

      <button
        type="button"
        onClick={generateBundle}
        disabled={isLoading}
        className="mt-4 h-10 rounded-md bg-red-600 px-4 text-sm font-semibold text-white hover:bg-red-700 disabled:bg-slate-400"
      >
        {isLoading ? "Building..." : "Build Bundle"}
      </button>

      {error ? (
        <p className="mt-3 text-sm font-medium text-red-700">{error}</p>
      ) : null}

      {summary ? (
        <div className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-700">
          <p className="font-semibold text-slate-900">{summary}</p>
          <p className="mt-1">
            Estimated total: Tk {estimatedTotal} | Remaining: Tk{" "}
            {remainingBudget}
          </p>
        </div>
      ) : null}

      {items.length > 0 ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {items.map((item) => {
            const quantity = getQuantity(item.id);

            return (
              <article
                key={item.id}
                className="rounded-md border border-slate-200 bg-slate-50 p-3 hover:border-red-200"
              >
                <Link href={`/products/${item.id}`}>
                  <div className="relative mb-3 aspect-square overflow-hidden rounded bg-white">
                    {item.image_url ? (
                      <Image
                        src={item.image_url}
                        alt={item.name}
                        fill
                        className="object-contain p-2"
                        sizes="(min-width: 1024px) 20vw, 50vw"
                      />
                    ) : null}
                  </div>
                </Link>

                <Link href={`/products/${item.id}`}>
                  <p className="line-clamp-2 text-sm font-semibold text-slate-950 hover:text-red-700">
                    {item.name}
                  </p>
                </Link>
                <p className="mt-1 text-sm font-bold text-red-700">
                  Tk {item.price}
                </p>
                <p className="mt-1 text-xs font-semibold text-slate-900">
                  Suggested: {item.suggested_quantity} item
                  {item.suggested_quantity === 1 ? "" : "s"}
                </p>
                <p className="mt-1 text-xs text-slate-600">{item.reason}</p>

                {quantity > 0 ? (
                  <div className="mt-3 flex h-9 items-center justify-between rounded-md border border-red-200 bg-white px-2">
                    <button
                      type="button"
                      onClick={() => onDecreaseQuantity(item.id)}
                      className="h-7 w-7 rounded text-sm font-bold text-red-700 hover:bg-red-50"
                    >
                      -
                    </button>
                    <span className="text-sm font-semibold text-slate-900">
                      {quantity}
                    </span>
                    <button
                      type="button"
                      onClick={() => onIncreaseQuantity(item.id)}
                      className="h-7 w-7 rounded text-sm font-bold text-red-700 hover:bg-red-50"
                    >
                      +
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => onAddToCart(item)}
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
