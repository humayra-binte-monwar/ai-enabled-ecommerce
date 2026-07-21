export type Product = {
  id: string;
  name: string;
  category: string;
  brand: string | null;
  price: number;
  unit: string | null;
  image_url: string | null;
  product_url: string | null;
  stock_status: string;
  scraped_at?: string;
};

const API_BASE_URL = "http://127.0.0.1:8000";

export async function getProducts(): Promise<Product[]> {
  const response = await fetch(`${API_BASE_URL}/api/products`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch products");
  }

  return response.json();
}