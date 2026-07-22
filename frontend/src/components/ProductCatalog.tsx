"use client";

import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";

import { BundlePlanner } from "@/components/BundlePlanner";
import { CartOptimizer } from "@/components/CartOptimizer";
import { Chatbot } from "@/components/Chatbot";
import { NaturalLanguageFinder } from "@/components/NaturalLanguageFinder";
import { createOrder, type Product } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

type CartItem = Product & {
  quantity: number;
};

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
  const [cart, setCart] = useState<CartItem[]>([]);
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [orderPlaced, setOrderPlaced] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [customerAddress, setCustomerAddress] = useState("");
  const [isSubmittingOrder, setIsSubmittingOrder] = useState(false);
  const [orderError, setOrderError] = useState("");

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

  function addToCart(product: Product, quantity = 1) {
    const safeQuantity = Math.max(1, quantity);
    setOrderPlaced(false);
    setCart((currentCart) => {
      const existingItem = currentCart.find((item) => item.id === product.id);

      if (existingItem) {
        return currentCart.map((item) =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + safeQuantity }
            : item
        );
      }

      return [...currentCart, { ...product, quantity: safeQuantity }];
    });
  }

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

  function getCartQuantity(productId: string) {
    return cart.find((item) => item.id === productId)?.quantity ?? 0;
  }

  async function placeOrder() {
    if (
      !customerName ||
      !customerPhone ||
      !customerAddress ||
      cart.length === 0
    ) {
      setOrderError("Please fill in all checkout fields.");
      return;
    }

    setIsSubmittingOrder(true);
    setOrderError("");

    try {
      const supabase = createClient();
      const { data } = await supabase.auth.getUser();
      const user = data.user;

      await createOrder({
        customer_name: customerName,
        customer_phone: customerPhone,
        customer_address: customerAddress,
        items: cart.map((item) => ({
          product_id: item.id,
          name: item.name,
          price: item.price,
          quantity: item.quantity,
        })),
        total: cartTotal,
        user_id: user?.id,
        user_email: user?.email,
        payment_method: "mock_card",
        payment_status: "paid_demo",
      });

      setOrderPlaced(true);
      setIsCheckingOut(false);
      setCart([]);
      setCustomerName("");
      setCustomerPhone("");
      setCustomerAddress("");
    } catch {
      setOrderError("Could not place order. Please try again.");
    } finally {
      setIsSubmittingOrder(false);
    }
  }

  return (
    <>
      {orderPlaced ? (
        <div className="mb-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-800">
          Order placed successfully. This is a demo checkout using mock payment.
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <section>
          <div className="mb-8">
            <Chatbot cart={cart} onAddToCart={addSuggestedProductToCart} />
          </div>

          <div className="mb-8">
            <NaturalLanguageFinder
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

                <p className="text-xs text-slate-500">{product.category}</p>
                <Link href={`/products/${product.id}`}>
                  <h2 className="mt-1 line-clamp-2 min-h-12 text-sm font-semibold text-slate-900 hover:text-red-700">
                    {product.name}
                  </h2>
                </Link>

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
                      Tk {item.price} x {item.quantity}
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => decreaseQuantity(item.id)}
                        className="h-7 w-7 rounded border border-slate-300 text-slate-700"
                      >
                        -
                      </button>
                      <span className="w-5 text-center text-sm font-semibold text-slate-900">
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
                <span className="text-xl font-bold text-red-700">
                  Tk {cartTotal}
                </span>
              </div>

              <CartOptimizer
                cart={cart}
                onAddToCart={addSuggestedProductToCart}
              />

              <button
                type="button"
                onClick={() => setIsCheckingOut(true)}
                className="h-11 w-full rounded-md bg-slate-950 text-sm font-semibold text-white"
              >
                Checkout
              </button>

              {isCheckingOut ? (
                <div className="mt-4 space-y-3 border-t border-slate-100 pt-4">
                  <input
                    value={customerName}
                    onChange={(event) => setCustomerName(event.target.value)}
                    placeholder="Full name"
                    className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none placeholder:text-slate-600 focus:border-red-600"
                  />

                  <input
                    value={customerPhone}
                    onChange={(event) => setCustomerPhone(event.target.value)}
                    placeholder="Phone number"
                    className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none placeholder:text-slate-600 focus:border-red-600"
                  />

                  <textarea
                    value={customerAddress}
                    onChange={(event) => setCustomerAddress(event.target.value)}
                    placeholder="Delivery address"
                    className="min-h-20 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none placeholder:text-slate-600 focus:border-red-600"
                  />

                  {orderError ? (
                    <p className="text-sm font-medium text-red-700">
                      {orderError}
                    </p>
                  ) : null}

                  <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
                    <p className="text-sm font-semibold text-slate-900">
                      Payment
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      Mock card payment will be marked as paid for this demo.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={placeOrder}
                    disabled={isSubmittingOrder}
                    className="h-11 w-full rounded-md bg-red-600 text-sm font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                  >
                    {isSubmittingOrder
                      ? "Placing Order..."
                      : "Place Mock Order"}
                  </button>
                </div>
              ) : null}
            </div>
          )}
        </aside>
      </div>
    </>
  );
}
