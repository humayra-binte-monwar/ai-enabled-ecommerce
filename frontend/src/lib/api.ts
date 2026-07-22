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
  payment_method?: string;
  payment_status?: string;
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
const REQUEST_TIMEOUT_MS = 8000;

async function fetchWithTimeout(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function getProducts(): Promise<Product[]> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/products`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch products");
  }

  return response.json();
}

export async function getProduct(productId: string): Promise<Product> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/products/${productId}`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch product");
  }

  return response.json();
}

export type ProductFinderProduct = {
  id: string;
  name: string;
  category: string;
  price: number;
  unit: string | null;
  image_url: string | null;
  product_url: string | null;
  reason: string;
};

export type ProductFinderResponse = {
  summary: string;
  products: ProductFinderProduct[];
};

export async function findProductsByIntent(
  query: string
): Promise<ProductFinderResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/ai/product-finder`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
    }
  );

  if (!response.ok) {
    throw new Error("Failed to find products");
  }

  return response.json();
}

export type BundlePlannerItem = {
  id: string;
  name: string;
  category: string;
  price: number;
  unit: string | null;
  image_url: string | null;
  product_url: string | null;
  recommended_quantity: number;
  suggested_quantity: number;
  reason: string;
};

export type BundlePlannerInput = {
  budget: number;
  people: number;
  duration_days: number;
  meal_type: string;
  preference?: string;
};

export type BundlePlannerResponse = {
  summary: string;
  estimated_total: number;
  remaining_budget: number;
  items: BundlePlannerItem[];
};

export async function planGroceryBundle(
  input: BundlePlannerInput
): Promise<BundlePlannerResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ai/bundle-planner`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });

  if (!response.ok) {
    throw new Error("Failed to plan grocery bundle");
  }

  return response.json();
}
