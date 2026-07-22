"use client";

import { useState } from "react";

import {
  optimizeCart,
  type CartOptimizerSuggestion,
  type Product,
} from "@/lib/api";

type CartItem = Product & {
  quantity: number;
};

type SuggestedProduct = {
  id: string;
  name: string;
  category: string;
  price: number;
  unit: string | null;
  image_url: string | null;
  product_url: string | null;
};

type CartOptimizerProps = {
  cart: CartItem[];
  onAddToCart: (product: SuggestedProduct) => void;
};

export function CartOptimizer({ cart, onAddToCart }: CartOptimizerProps) {
  const [goal, setGoal] = useState("save money and keep meals balanced");
  const [summary, setSummary] = useState("");
  const [suggestions, setSuggestions] = useState<CartOptimizerSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function reviewCart() {
    setIsLoading(true);
    setError("");
    setSummary("");
    setSuggestions([]);

    try {
      const response = await optimizeCart(
        cart.map((item) => ({
          product_id: item.id,
          name: item.name,
          category: item.category,
          price: item.price,
          quantity: item.quantity,
        })),
        goal
      );

      setSummary(response.summary);
      setSuggestions(response.suggestions);
    } catch {
      setError("Could not optimize this cart. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  function addSuggestion(suggestion: CartOptimizerSuggestion) {
    if (!suggestion.product_id || !suggestion.product_name || !suggestion.price) {
      return;
    }

    onAddToCart({
      id: suggestion.product_id,
      name: suggestion.product_name,
      category: suggestion.category ?? "General",
      price: suggestion.price,
      unit: suggestion.unit,
      image_url: suggestion.image_url,
      product_url: suggestion.product_url,
    });
  }

  return (
    <div className="rounded-md border border-red-100 bg-red-50 p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-red-700">
        AI Feature 3
      </p>
      <h3 className="mt-1 text-sm font-bold text-slate-950">
        Cart Health + Savings Optimizer
      </h3>

      <label className="mt-3 block text-xs font-medium text-slate-700">
        Goal
        <input
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
          placeholder="save money, healthy, family meals..."
          className="mt-1 h-9 w-full rounded-md border border-red-200 bg-white px-3 text-xs text-slate-900 outline-none placeholder:text-slate-600 focus:border-red-600"
        />
      </label>

      <button
        type="button"
        onClick={reviewCart}
        disabled={isLoading || cart.length === 0}
        className="mt-3 h-9 w-full rounded-md bg-red-600 text-xs font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-slate-400"
      >
        {isLoading ? "Reviewing..." : "Review Cart"}
      </button>

      {error ? <p className="mt-2 text-xs font-medium text-red-700">{error}</p> : null}

      {summary ? (
        <p className="mt-3 text-xs font-semibold text-slate-900">{summary}</p>
      ) : null}

      {suggestions.length > 0 ? (
        <div className="mt-3 space-y-2">
          {suggestions.map((suggestion, index) => (
            <div
              key={`${suggestion.type}-${suggestion.product_id ?? index}`}
              className="rounded-md border border-red-100 bg-white p-2"
            >
              <p className="text-xs text-slate-700">{suggestion.message}</p>

              {suggestion.product_name ? (
                <p className="mt-1 text-xs font-semibold text-slate-950">
                  {suggestion.product_name}
                  {suggestion.price ? ` - Tk ${suggestion.price}` : ""}
                </p>
              ) : null}

              {suggestion.product_id &&
              suggestion.product_name &&
              suggestion.price ? (
                <button
                  type="button"
                  onClick={() => addSuggestion(suggestion)}
                  className="mt-2 h-8 rounded-md bg-slate-950 px-3 text-xs font-semibold text-white hover:bg-slate-800"
                >
                  Add Suggestion
                </button>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
