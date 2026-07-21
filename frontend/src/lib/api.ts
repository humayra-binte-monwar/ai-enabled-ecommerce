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

export type OrderItemInput = {
  product_id: string;
  name: string;
  price: number;
  quantity: number;
};

export type OrderInput = {
  customer_name: string;
  customer_phone: string;
  customer_address: string;
  items: OrderItemInput[];
  total: number;
  user_id?: string;
  user_email?: string;
};

export async function createOrder(order: OrderInput) {
  const response = await fetch(`${API_BASE_URL}/api/orders`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(order),
  });

  if (!response.ok) {
    throw new Error("Failed to create order");
  }

  return response.json();
}

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

export async function getProduct(productId: string): Promise<Product> {
  const response = await fetch(`${API_BASE_URL}/api/products/${productId}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch product");
  }

  return response.json();
}