"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { Product } from "@/lib/api";

const CART_STORAGE_KEY = "ai-grocery-commerce-cart";

export type CartItem = Product & {
  quantity: number;
};

type CartContextValue = {
  cart: CartItem[];
  cartTotal: number;
  cartItemCount: number;
  addToCart: (product: Product, quantity?: number) => void;
  decreaseQuantity: (productId: string) => void;
  increaseQuantity: (productId: string) => void;
  changeQuantityBy: (productId: string, delta: number) => void;
  removeFromCart: (productId: string) => void;
  clearCart: () => void;
  getCartQuantity: (productId: string) => number;
};

const CartContext = createContext<CartContextValue | null>(null);

function isCartItem(value: unknown): value is CartItem {
  if (!value || typeof value !== "object") {
    return false;
  }

  const item = value as Partial<CartItem>;
  return (
    typeof item.id === "string" &&
    typeof item.name === "string" &&
    typeof item.price === "number" &&
    typeof item.quantity === "number" &&
    item.quantity > 0
  );
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let restoredCart: CartItem[] = [];

    try {
      const savedCart = window.localStorage.getItem(CART_STORAGE_KEY);
      if (savedCart) {
        const parsedCart: unknown = JSON.parse(savedCart);
        if (Array.isArray(parsedCart)) {
          restoredCart = parsedCart.filter(isCartItem);
        }
      }
    } catch {
      window.localStorage.removeItem(CART_STORAGE_KEY);
    }

    const frame = window.requestAnimationFrame(() => {
      setCart(restoredCart);
      setIsReady(true);
    });

    return () => window.cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    if (isReady) {
      window.localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
    }
  }, [cart, isReady]);

  const value = useMemo<CartContextValue>(() => {
    const cartTotal = cart.reduce(
      (total, item) => total + item.price * item.quantity,
      0
    );
    const cartItemCount = cart.reduce((total, item) => total + item.quantity, 0);

    function changeQuantityBy(productId: string, delta: number) {
      setCart((currentCart) =>
        currentCart
          .map((item) =>
            item.id === productId
              ? { ...item, quantity: item.quantity + delta }
              : item
          )
          .filter((item) => item.quantity > 0)
      );
    }

    return {
      cart,
      cartTotal,
      cartItemCount,
      addToCart(product, quantity = 1) {
        const safeQuantity = Math.max(1, Math.floor(quantity));
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
      },
      decreaseQuantity(productId) {
        changeQuantityBy(productId, -1);
      },
      increaseQuantity(productId) {
        changeQuantityBy(productId, 1);
      },
      changeQuantityBy,
      removeFromCart(productId) {
        setCart((currentCart) =>
          currentCart.filter((item) => item.id !== productId)
        );
      },
      clearCart() {
        setCart([]);
      },
      getCartQuantity(productId) {
        return cart.find((item) => item.id === productId)?.quantity ?? 0;
      },
    };
  }, [cart]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const context = useContext(CartContext);

  if (!context) {
    throw new Error("useCart must be used inside CartProvider");
  }

  return context;
}
