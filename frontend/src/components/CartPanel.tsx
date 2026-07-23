"use client";

import { useState } from "react";

import { useCart } from "@/components/CartProvider";
import { CartOptimizer } from "@/components/CartOptimizer";
import { ApiError, createCheckout, type Product } from "@/lib/api";
import {
  createClient,
  getFreshAccessToken,
  refreshAccessToken,
} from "@/lib/supabase/client";

type SuggestedProduct = Pick<
  Product,
  "id" | "name" | "category" | "price" | "unit" | "image_url" | "product_url"
>;

export function CartPanel() {
  const {
    addToCart,
    cart,
    cartItemCount,
    cartTotal,
    decreaseQuantity,
    increaseQuantity,
    removeFromCart,
  } = useCart();
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [customerAddress, setCustomerAddress] = useState("");
  const [isSubmittingOrder, setIsSubmittingOrder] = useState(false);
  const [orderError, setOrderError] = useState("");

  function addSuggestedProductToCart(product: SuggestedProduct) {
    addToCart({ ...product, brand: null, stock_status: "in_stock" });
  }

  async function placeOrder() {
    if (!customerName || !customerPhone || !customerAddress || cart.length === 0) {
      setOrderError("Please fill in all checkout fields.");
      return;
    }

    setIsSubmittingOrder(true);
    setOrderError("");

    try {
      const supabase = createClient();
      let accessToken = await getFreshAccessToken();
      if (!accessToken) {
        setOrderError("Please sign in before starting checkout.");
        return;
      }

      const checkoutPayload = {
        customer_name: customerName,
        customer_phone: customerPhone,
        customer_address: customerAddress,
        items: cart.map((item) => ({ product_id: item.id, quantity: item.quantity })),
        idempotency_key: crypto.randomUUID(),
      };

      let checkout;
      try {
        checkout = await createCheckout(checkoutPayload, accessToken);
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 401) throw error;

        accessToken = await refreshAccessToken();
        if (!accessToken) {
          await supabase.auth.signOut();
          setOrderError("Please sign in again before starting checkout.");
          return;
        }
        checkout = await createCheckout(checkoutPayload, accessToken);
      }

      window.location.assign(checkout.payment_url);
    } catch (error) {
      setOrderError(error instanceof Error ? error.message : "Could not place order. Please try again.");
    } finally {
      setIsSubmittingOrder(false);
    }
  }

  return (
    <aside id="cart-panel" className="scroll-mt-24 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-red-700">Your basket</p>
          <h2 className="mt-1 text-lg font-bold text-slate-950">Cart</h2>
        </div>
        <span className="rounded-full bg-red-50 px-2.5 py-1 text-sm font-semibold text-red-700">
          {cartItemCount} item{cartItemCount === 1 ? "" : "s"}
        </span>
      </div>

      {cart.length === 0 ? (
        <p className="rounded-md bg-slate-50 p-3 text-sm text-slate-500">Add products from the catalogue or an AI recommendation to begin.</p>
      ) : (
        <div className="space-y-4">
          <div className="max-h-72 space-y-3 overflow-y-auto pr-1">
            {cart.map((item) => (
              <div key={item.id} className="border-b border-slate-100 pb-3">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-medium text-slate-900">{item.name}</p>
                  <button type="button" onClick={() => removeFromCart(item.id)} className="text-xs font-semibold text-slate-500 hover:text-red-700">Remove</button>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-sm text-slate-600">Tk {item.price} × {item.quantity}</span>
                  <div className="flex items-center gap-2">
                    <button type="button" onClick={() => decreaseQuantity(item.id)} aria-label={`Decrease ${item.name} quantity`} className="h-7 w-7 rounded border border-slate-300 text-slate-700 hover:border-red-300">−</button>
                    <span className="w-5 text-center text-sm font-semibold text-slate-900">{item.quantity}</span>
                    <button type="button" onClick={() => increaseQuantity(item.id)} aria-label={`Increase ${item.name} quantity`} className="h-7 w-7 rounded border border-slate-300 text-slate-700 hover:border-red-300">+</button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between border-t border-slate-100 pt-3">
            <span className="font-semibold text-slate-900">Total</span>
            <span className="text-xl font-bold text-red-700">Tk {cartTotal}</span>
          </div>

          <CartOptimizer cart={cart} onAddToCart={addSuggestedProductToCart} />

          <button type="button" onClick={() => setIsCheckingOut((open) => !open)} className="h-11 w-full rounded-md bg-slate-950 text-sm font-semibold text-white hover:bg-slate-800">
            {isCheckingOut ? "Hide checkout" : "Checkout"}
          </button>

          {isCheckingOut ? (
            <div className="space-y-3 border-t border-slate-100 pt-4">
              <p className="text-sm font-semibold text-slate-950">Delivery details</p>
              <input value={customerName} onChange={(event) => setCustomerName(event.target.value)} placeholder="Full name" className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none placeholder:text-slate-500 focus:border-red-600" />
              <input value={customerPhone} onChange={(event) => setCustomerPhone(event.target.value)} placeholder="Phone number" className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none placeholder:text-slate-500 focus:border-red-600" />
              <textarea value={customerAddress} onChange={(event) => setCustomerAddress(event.target.value)} placeholder="Delivery address" className="min-h-20 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none placeholder:text-slate-500 focus:border-red-600" />
              {orderError ? <p className="text-sm font-medium text-red-700">{orderError}</p> : null}
              <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">Secure SSLCommerz sandbox checkout. An order is marked paid only after gateway verification.</div>
              <button type="button" onClick={placeOrder} disabled={isSubmittingOrder} className="h-11 w-full rounded-md bg-red-600 text-sm font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-slate-400">
                {isSubmittingOrder ? "Starting payment..." : "Continue to Payment"}
              </button>
            </div>
          ) : null}
        </div>
      )}
    </aside>
  );
}
