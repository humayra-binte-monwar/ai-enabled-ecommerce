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
  tags?: string[];
  normalized_category?: string | null;
  product_type?: string | null;
};

export type CheckoutItemInput = {
  product_id: string;
  quantity: number;
};

export type CheckoutInput = {
  customer_name: string;
  customer_phone: string;
  customer_address: string;
  items: CheckoutItemInput[];
  idempotency_key: string;
};

export type CheckoutSession = {
  order_id: string;
  payment_url: string;
};

export type OrderItem = {
  product_id: string;
  product_name: string;
  unit_price: number;
  quantity: number;
};

export type Order = {
  id: string;
  customer_name: string;
  customer_phone: string;
  customer_address: string;
  subtotal: number;
  delivery_fee: number;
  total: number;
  currency: string;
  status: string;
  created_at: string;
  items: OrderItem[];
};

async function getErrorMessage(response: Response, fallback: string) {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    return fallback;
  }

  return fallback;
}

export async function createCheckout(
  checkout: CheckoutInput,
  accessToken: string
): Promise<CheckoutSession> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/orders/checkout`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(checkout),
    },
    30000
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Failed to start checkout"));
  }

  return response.json();
}

export async function getMyOrders(accessToken: string): Promise<Order[]> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/orders/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Failed to load orders"));
  }

  return response.json();
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001";
const REQUEST_TIMEOUT_MS = 8000;
const CHAT_TIMEOUT_MS = 30000;

async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs = REQUEST_TIMEOUT_MS
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

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
  tags?: string[];
  normalized_category?: string | null;
  product_type?: string | null;
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
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/ai/bundle-planner`, {
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

export type CartOptimizerItemInput = {
  product_id: string;
  name: string;
  category: string;
  price: number;
  quantity: number;
};

export type CartOptimizerSuggestion = {
  type: string;
  message: string;
  product_id: string | null;
  product_name: string | null;
  category: string | null;
  price: number | null;
  unit: string | null;
  image_url: string | null;
  product_url: string | null;
};

export type CartOptimizerResponse = {
  summary: string;
  cart_total: number;
  suggestions: CartOptimizerSuggestion[];
};

export async function optimizeCart(
  items: CartOptimizerItemInput[],
  goal?: string
): Promise<CartOptimizerResponse> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/ai/cart-optimizer`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ items, goal }),
  });

  if (!response.ok) {
    throw new Error("Failed to optimize cart");
  }

  return response.json();
}

export type ChatCartItemInput = {
  product_id: string;
  name: string;
  category: string;
  price: number;
  quantity: number;
};

export type ChatProductCard = {
  id: string;
  name: string;
  category: string;
  price: number;
  unit: string | null;
  image_url: string | null;
  product_url: string | null;
  tags?: string[];
  normalized_category?: string | null;
  product_type?: string | null;
  reason: string | null;
};

export type ChatCartAction = {
  type: string;
  product_id: string | null;
  product_name: string | null;
  quantity: number | null;
  requires_confirmation: boolean;
  message: string;
  product: ChatProductCard | null;
};

export type ChatResponse = {
  message: string;
  intent: string;
  products: ChatProductCard[];
  cart_actions: ChatCartAction[];
  follow_up_suggestions: string[];
  tools_used: string[];
  fallback: boolean;
};

export type AiProviderStatus = {
  provider: string;
  agent_enabled: boolean;
  model: string;
  langchain_available: boolean;
  langchain_import_error: string;
  has_provider_key: boolean;
  client_ready: boolean;
};

export async function getAiProviderStatus(): Promise<AiProviderStatus> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/ai/provider-status`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch AI provider status");
  }

  return response.json();
}

export async function sendChatMessage(input: {
  session_id: string;
  message: string;
  cart_items: ChatCartItemInput[];
}): Promise<ChatResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/ai/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    },
    CHAT_TIMEOUT_MS
  );

  if (!response.ok) {
    throw new Error("Failed to send chat message");
  }

  return response.json();
}
