"use client";

import { useCart } from "@/components/CartProvider";
import type { Product } from "@/lib/api";

export function AddToCartButton({ product }: { product: Product }) {
  const { addToCart, getCartQuantity } = useCart();
  const quantity = getCartQuantity(product.id);

  return (
    <button
      type="button"
      onClick={() => addToCart(product)}
      className="mt-6 h-11 w-full rounded-md bg-red-600 text-sm font-semibold text-white hover:bg-red-700"
    >
      {quantity > 0 ? `Add another (in cart: ${quantity})` : "Add to Cart"}
    </button>
  );
}
