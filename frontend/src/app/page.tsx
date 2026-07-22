import { AuthPanel } from "@/components/AuthPanel";
import { ProductCatalog } from "@/components/ProductCatalog";
import { NaturalLanguageFinder } from "@/components/NaturalLanguageFinder";
import { getProducts, type Product } from "@/lib/api";

export default async function Home() {
  let products: Product[] = [];
  let productsError = "";

  try {
    products = await getProducts();
  } catch {
    productsError =
      "Products could not load. Make sure the FastAPI backend is running.";
  }

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-8">
      <section className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium text-red-700">
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

        <div className="mb-8 max-w-md">
          <AuthPanel />
        </div>

        <div className="mb-8">
          <NaturalLanguageFinder />
        </div>

        {productsError ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-800">
            {productsError}
          </div>
        ) : (
          <ProductCatalog products={products} />
        )}
      </section>
    </main>
  );
}
