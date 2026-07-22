"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useSearchParams } from "next/navigation";

import { useCart } from "@/components/CartProvider";

export function CheckoutResult() {
  const { clearCart } = useCart();
  const searchParams = useSearchParams();
  const status = searchParams.get("status");
  const orderId = searchParams.get("order_id");
  const isPaid = status === "paid";

  useEffect(() => {
    if (isPaid) {
      clearCart();
    }
  }, [clearCart, isPaid]);

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-12">
      <section className="mx-auto max-w-lg rounded-lg border border-slate-200 bg-white p-6 text-center shadow-sm">
        <p
          className={
            isPaid
              ? "text-sm font-semibold text-emerald-700"
              : "text-sm font-semibold text-red-700"
          }
        >
          {isPaid ? "Payment verified" : "Payment not completed"}
        </p>
        <h1 className="mt-2 text-2xl font-bold text-slate-950">
          {isPaid ? "Your order is confirmed" : "Your order still needs payment"}
        </h1>
        <p className="mt-3 text-sm text-slate-600">
          {isPaid
            ? "SSLCommerz confirmed this sandbox payment."
            : "No payment was confirmed. You can return to your cart and try again."}
        </p>
        {orderId ? (
          <p className="mt-3 text-xs text-slate-500">Order: {orderId}</p>
        ) : null}
        <Link
          href="/"
          className="mt-6 inline-flex h-10 items-center rounded-md bg-slate-950 px-4 text-sm font-semibold text-white"
        >
          Back to shop
        </Link>
      </section>
    </main>
  );
}
