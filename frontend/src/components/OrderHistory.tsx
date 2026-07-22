"use client";

import { useEffect, useState } from "react";

import { ApiError, getMyOrders, type Order } from "@/lib/api";
import {
  createClient,
  getFreshAccessToken,
  refreshAccessToken,
} from "@/lib/supabase/client";

const STATUS_LABELS: Record<string, string> = {
  cancelled: "Cancelled",
  confirmed: "Confirmed",
  paid: "Paid",
  payment_failed: "Payment failed",
  pending_payment: "Awaiting payment",
  refunded: "Refunded",
};

export function OrderHistory() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadOrders() {
      const supabase = createClient();
      let accessToken = await getFreshAccessToken();

      if (!accessToken) {
        setIsLoading(false);
        return;
      }

      try {
        setOrders(await getMyOrders(accessToken));
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          accessToken = await refreshAccessToken();
          if (accessToken) {
            try {
              setOrders(await getMyOrders(accessToken));
              return;
            } catch (retryError) {
              if (retryError instanceof ApiError && retryError.status === 401) {
                await supabase.auth.signOut();
                setError("Your session expired. Please log in again.");
                return;
              }

              setError(
                retryError instanceof Error
                  ? retryError.message
                  : "Could not load your order history right now."
              );
              return;
            }
          }
        }

        setError(
          error instanceof Error
            ? error.message
            : "Could not load your order history right now."
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadOrders();
  }, []);

  if (isLoading) {
    return <p className="text-sm text-slate-500">Loading your orders...</p>;
  }

  if (error) {
    return <p className="text-sm font-medium text-red-700">{error}</p>;
  }

  if (orders.length === 0) {
    return <p className="text-sm text-slate-500">No orders yet.</p>;
  }

  return (
    <div className="space-y-3">
      {orders.map((order) => (
        <article key={order.id} className="rounded-md border border-slate-200 p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-950">
                Tk {order.total}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {new Date(order.created_at).toLocaleDateString("en-BD", {
                  day: "numeric",
                  month: "short",
                  year: "numeric",
                })}
              </p>
            </div>
            <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
              {STATUS_LABELS[order.status] ?? order.status}
            </span>
          </div>
          <p className="mt-3 text-xs text-slate-600">
            {order.items.map((item) => `${item.product_name} × ${item.quantity}`).join(", ")}
          </p>
        </article>
      ))}
    </div>
  );
}
