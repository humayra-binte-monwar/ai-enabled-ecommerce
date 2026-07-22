import { Suspense } from "react";

import { CheckoutResult } from "@/components/CheckoutResult";

export default function PaymentResultPage() {
  return (
    <Suspense fallback={<main className="min-h-screen bg-slate-50" />}>
      <CheckoutResult />
    </Suspense>
  );
}
