import { AuthPanel } from "@/components/AuthPanel";
import { CartPanel } from "@/components/CartPanel";
import { OrderHistory } from "@/components/OrderHistory";
import { ProductCatalogLoader } from "@/components/ProductCatalogLoader";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-red-100 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-4 py-5 sm:px-6">
          <div>
            <p className="text-sm font-semibold text-red-700">AI Grocery Commerce</p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">Shwapno-style Grocery Catalog</h1>
          </div>
          <a href="#cart-panel" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-700 hover:bg-red-100 lg:hidden">View cart</a>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:py-8">
        <p className="mb-6 max-w-3xl text-slate-600">
          Browse grocery products, use the AI tools to plan your shop, and keep your basket and checkout ready beside you.
        </p>

        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="min-w-0 space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <AuthPanel />
              <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="text-lg font-bold text-slate-950">Your orders</h2>
                <div className="mt-4"><OrderHistory /></div>
              </section>
            </div>

            <ProductCatalogLoader />
          </div>

          <div className="lg:sticky lg:top-6">
            <CartPanel />
          </div>
        </div>
      </section>
    </main>
  );
}
