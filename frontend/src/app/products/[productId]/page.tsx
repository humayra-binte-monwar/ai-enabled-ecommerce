import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getProduct } from "@/lib/api";

type ProductPageProps = {
  params: Promise<{
    productId: string;
  }>;
};

export default async function ProductPage({ params }: ProductPageProps) {
  const { productId } = await params;

  let product;

  try {
    product = await getProduct(productId);
  } catch {
    notFound();
  }

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-8">
      <section className="mx-auto grid max-w-5xl gap-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm md:grid-cols-2">
        <div className="relative aspect-square overflow-hidden rounded-md bg-slate-100">
          {product.image_url ? (
            <Image
              src={product.image_url}
              alt={product.name}
              fill
              className="object-contain p-6"
              sizes="(min-width: 768px) 50vw, 100vw"
              priority
            />
          ) : null}
        </div>

        <div>
          <Link
            href="/"
            className="text-sm font-medium text-red-700 hover:text-red-800"
          >
            Back to catalog
          </Link>

          <p className="mt-6 text-sm text-slate-500">{product.category}</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-950">
            {product.name}
          </h1>

          <div className="mt-6">
            <p className="text-3xl font-bold text-red-700">
              Tk {product.price}
            </p>
            <p className="mt-1 text-sm text-slate-500">{product.unit}</p>
          </div>

          <div className="mt-6 rounded-md bg-slate-50 p-4">
            <p className="text-sm text-slate-600">
              Stock status:{" "}
              <span className="font-semibold text-slate-900">
                {product.stock_status}
              </span>
            </p>
            {product.product_url ? (
              <a
                href={product.product_url}
                target="_blank"
                rel="noreferrer"
                className="mt-3 block text-sm font-medium text-red-700 hover:text-red-800"
              >
                View source product
              </a>
            ) : null}
          </div>
        </div>
      </section>
    </main>
  );
}
