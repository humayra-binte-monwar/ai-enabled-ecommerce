import Image from "next/image";

import { getProducts } from "@/lib/api";

export default async function Home() {
  const products = await getProducts();

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-8">
      <section className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium text-emerald-700">
            AI Grocery Commerce
          </p>
          <h1 className="mt-2 text-3xl font-bold text-slate-950">
            Shwapno-style Grocery Catalog
          </h1>
          <p className="mt-3 max-w-2xl text-slate-600">
            Browse products collected from a grocery catalog pipeline and served
            through a FastAPI backend.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {products.map((product) => (
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
      </section>
    </main>
  );
}