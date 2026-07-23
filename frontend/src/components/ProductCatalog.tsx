"use client";

import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";

import { BundlePlanner } from "@/components/BundlePlanner";
import { useCart } from "@/components/CartProvider";
import { Chatbot } from "@/components/Chatbot";
import { NaturalLanguageFinder } from "@/components/NaturalLanguageFinder";
import { type ChatCartAction, type Product } from "@/lib/api";

type ProductCatalogProps = {
  products: Product[];
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

export function ProductCatalog({ products }: ProductCatalogProps) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const {
    addToCart,
    cart,
    changeQuantityBy,
    clearCart,
    decreaseQuantity,
    getCartQuantity,
    increaseQuantity,
    removeFromCart,
  } = useCart();

  const categories = useMemo(() => {
    return [
      "All",
      ...Array.from(
        new Set(
          products.map(
            (product) => product.normalized_category ?? product.category
          )
        )
      ).sort(),
    ];
  }, [products]);

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      const matchesSearch =
        product.name.toLowerCase().includes(search.toLowerCase()) ||
        product.category.toLowerCase().includes(search.toLowerCase()) ||
        product.brand?.toLowerCase().includes(search.toLowerCase());

      const matchesCategory =
        category === "All" ||
        (product.normalized_category ?? product.category) === category;

      return matchesSearch && matchesCategory;
    });
  }, [products, search, category]);

  function addSuggestedProductToCart(product: SuggestedProduct, quantity = 1) {
    addToCart({
      id: product.id,
      name: product.name,
      category: product.category,
      brand: null,
      price: product.price,
      unit: product.unit,
      image_url: product.image_url,
      product_url: product.product_url,
      stock_status: "in_stock",
    }, quantity);
  }

  function applyChatCartAction(action: ChatCartAction) {
    if (action.type === "clear_cart") {
      clearCart();
      return;
    }

    if (action.type === "add_item" && action.product) {
      addSuggestedProductToCart(action.product, action.quantity ?? 1);
      return;
    }

    if (!action.product_id) {
      return;
    }

    if (action.type === "remove_item") {
      removeFromCart(action.product_id);
      return;
    }

    if (action.type === "increase_quantity") {
      changeQuantityBy(action.product_id, action.quantity ?? 1);
      return;
    }

    if (action.type === "decrease_quantity") {
      changeQuantityBy(action.product_id, -(action.quantity ?? 1));
    }
  }

  return (
    <section>
          <div className="mb-8">
            <Chatbot
              cart={cart}
              onAddToCart={addSuggestedProductToCart}
              onApplyCartAction={applyChatCartAction}
            />
          </div>

          <div className="mb-8">
            <NaturalLanguageFinder
              products={products}
              getQuantity={getCartQuantity}
              onAddToCart={addSuggestedProductToCart}
              onDecreaseQuantity={decreaseQuantity}
              onIncreaseQuantity={increaseQuantity}
            />
          </div>

          <div className="mb-8">
            <BundlePlanner
              getQuantity={getCartQuantity}
              onAddToCart={addSuggestedProductToCart}
              onDecreaseQuantity={decreaseQuantity}
              onIncreaseQuantity={increaseQuantity}
            />
          </div>

          <div className="mb-6 flex flex-col gap-3 sm:flex-row">
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search groceries..."
              className="h-11 flex-1 rounded-md border border-slate-300 bg-white px-4 text-sm text-slate-900 outline-none placeholder:text-slate-600 focus:border-red-600"
            />

            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="h-11 rounded-md border border-slate-300 bg-white px-4 text-sm text-slate-900 outline-none focus:border-red-600"
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
                <Link href={`/products/${product.id}`}>
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
                </Link>

                <p className="text-xs text-slate-500">
                  {product.normalized_category ?? product.category}
                </p>
                <Link href={`/products/${product.id}`}>
                  <h2 className="mt-1 line-clamp-2 min-h-12 text-sm font-semibold text-slate-900 hover:text-red-700">
                    {product.name}
                  </h2>
                </Link>

                {product.tags?.length ? (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {product.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600"
                      >
                        {tag.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                ) : null}

                <div className="mt-3 flex items-center justify-between">
                  <span className="text-lg font-bold text-red-700">
                    Tk {product.price}
                  </span>
                  <span className="text-xs text-slate-500">{product.unit}</span>
                </div>

                <button
                  type="button"
                  onClick={() => addToCart(product)}
                  className="mt-4 h-10 w-full rounded-md bg-red-600 text-sm font-semibold text-white hover:bg-red-700"
                >
                  Add to Cart
                </button>
              </article>
            ))}
          </div>
    </section>
  );
}
