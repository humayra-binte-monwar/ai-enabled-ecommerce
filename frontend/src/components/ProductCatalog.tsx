"use client";

import Image from "next/image";
import { useMemo, useState } from "react";

import type { Product } from "@/lib/api";

type ProductCatalogProps = {
  products: Product[];
};

export function ProductCatalog({ products }: ProductCatalogProps) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");

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

  return (
    <>
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

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
          </article>
        ))}
      </div>
    </>
  );
}