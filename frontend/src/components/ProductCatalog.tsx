"use client";

import Image from "next/image";
import { useMemo, useState } from "react";

import type { Product } from "@/lib/api";

type CartItem = Product & {
  quantity: number;
};

type ProductCatalogProps = {
  products: Product[];
};

export function ProductCatalog({ products }: ProductCatalogProps) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [cart, setCart] = useState<CartItem[]>([]);

  const categories = useMemo(() => {
    return ["All", ...Array.from(new Set(products.map((p) => p.category)))];
  }, [products]);

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      const matchesSearch =
        product.name.toLowerCase().includes(search.toLowerCase()) ||
        product.category.toLowerCase().includes(search.toLowerCase()) ||
        product.brand?.toLowerCase().includes(search.toLowerCase());

      const matchesCategory =
        category === "All" || product.category === category;

      return matchesSearch && matchesCategory;
    });
  }, [products, search, category]);

  const cartTotal = useMemo(() => {
    return cart.reduce((total, item) => total + item.price * item.quantity, 0);
  }, [cart]);

  function addToCart(product: Product) {
    setCart((currentCart) => {
      const existingItem = currentCart.find((item) => item.id === product.id);

      if (existingItem) {
        return currentCart.map((item) =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }

      return [...currentCart, { ...product, quantity: 1 }];
    });
  }

  function decreaseQuantity(productId: string) {
    setCart((currentCart) =>
      currentCart
        .map((item) =>
          item.id === productId
            ? { ...item, quantity: item.quantity - 1 }
            : item
        )
        .filter((item) => item.quantity > 0)
    );
  }

  function increaseQuantity(productId: string) {
    setCart((currentCart) =>
      currentCart.map((item) =>
        item.id === productId ? { ...item, quantity: item.quantity + 1 } : item
      )
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
      <section>
        <div className="mb-6 flex flex-col gap-3 sm:flex-row">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search groceries..."
            className="h-11 flex-1 rounded-md border border-slate-300 bg-white px-4 text-sm text-slate-900 outline-none focus:border-emerald-600"
          />

          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            className="h-11 rounded-md border border-slate-300 bg-white px-4 text-sm text-slate-900 outline-none focus:border-emerald-600"
          >
            {categories.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>

        <p className="mb-4 text-sm text-slate-600">
          Showing {filteredProducts.length} of {products.length} products
        </p>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {filteredProducts.map((product) => (
            <article
              key={product.id}
              className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div className="relative mb-4 aspect-square overflow-hidden rounded-md bg-slate-100">
                {product.image_url ? (
                  <Image
                    src={product.image_url}
                    alt={product.name}
                    fill
                    className="object-contain p-3"
                    sizes="(min-width: 1024px) 25vw, 50vw"
                  />
                ) : null}
              </div>

              <p className="text-xs text-slate-500">{product.category}</p>
              <h2 className="mt-1 line-clamp-2 min-h-12 text-sm font-semibold text-slate-900">
                {product.name}
              </h2>

              <div className="mt-3 flex items-center justify-between">
                <span className="text-lg font-bold text-emerald-700">
                  ৳{product.price}
                </span>
                <span className="text-xs text-slate-500">{product.unit}</span>
              </div>

              <button
                type="button"
                onClick={() => addToCart(product)}
                className="mt-4 h-10 w-full rounded-md bg-emerald-600 text-sm font-semibold text-white hover:bg-emerald-700"
              >
                Add to Cart
              </button>
            </article>
          ))}
        </div>
      </section>

      <aside className="h-fit rounded-lg border border-slate-200 bg-white p-4 shadow-sm lg:sticky lg:top-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-950">Cart</h2>
          <span className="text-sm text-slate-500">{cart.length} items</span>
        </div>

        {cart.length === 0 ? (
          <p className="text-sm text-slate-500">Your cart is empty.</p>
        ) : (
          <div className="space-y-4">
            {cart.map((item) => (
              <div key={item.id} className="border-b border-slate-100 pb-3">
                <p className="text-sm font-medium text-slate-900">
                  {item.name}
                </p>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-sm text-slate-600">
                    ৳{item.price} × {item.quantity}
                  </span>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => decreaseQuantity(item.id)}
                      className="h-7 w-7 rounded border border-slate-300 text-slate-700"
                    >
                      -
                    </button>
                    <span className="w-5 text-center text-sm">
                      {item.quantity}
                    </span>
                    <button
                      type="button"
                      onClick={() => increaseQuantity(item.id)}
                      className="h-7 w-7 rounded border border-slate-300 text-slate-700"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            ))}

            <div className="flex items-center justify-between pt-2">
              <span className="font-semibold text-slate-900">Total</span>
              <span className="text-xl font-bold text-emerald-700">
                ৳{cartTotal}
              </span>
            </div>

            <button
              type="button"
              className="h-11 w-full rounded-md bg-slate-950 text-sm font-semibold text-white"
            >
              Checkout
            </button>
          </div>
        )}
      </aside>
    </div>
  );
}