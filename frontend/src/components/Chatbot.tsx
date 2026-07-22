"use client";

import {
  getAiProviderStatus,
  type AiProviderStatus,
  type ChatCartAction,
  sendChatMessage,
  type ChatProductCard,
  type Product,
} from "@/lib/api";
import { useEffect, useMemo, useState } from "react";

type CartItem = Product & {
  quantity: number;
};

type ChatbotProps = {
  cart: CartItem[];
  onAddToCart: (product: ChatProductCard, quantity?: number) => void;
  onApplyCartAction: (action: ChatCartAction) => void;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  products?: ChatProductCard[];
  cartActions?: ChatCartAction[];
  toolsUsed?: string[];
  fallback?: boolean;
};

function createSessionId() {
  return `demo-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function Chatbot({ cart, onAddToCart, onApplyCartAction }: ChatbotProps) {
  const [sessionId] = useState(createSessionId);
  const [message, setMessage] = useState("");
  const [providerStatus, setProviderStatus] =
    useState<AiProviderStatus | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi, I am Grocery Copilot. Ask me about products, prices, bundles, health-conscious choices, or cart changes.",
    },
  ]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");

  const promptChips = useMemo(
    () => [
      "Find breakfast items under Tk 300",
      "Add the cheapest milk to my cart",
      "Make a 3-day grocery bundle for 2 people under Tk 1500",
      "Review my cart for healthier choices",
    ],
    []
  );

  const providerLabel = providerStatus?.client_ready
    ? `${providerStatus.provider.toUpperCase()} ${providerStatus.model}`
    : "Fallback mode";

  const providerStatusClass = providerStatus?.client_ready
    ? "bg-emerald-50 text-emerald-700"
    : "bg-amber-50 text-amber-700";

  useEffect(() => {
    let isMounted = true;

    getAiProviderStatus()
      .then((status) => {
        if (isMounted) {
          setProviderStatus(status);
        }
      })
      .catch(() => {
        if (isMounted) {
          setProviderStatus(null);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  async function submitChat(nextMessage = message) {
    const trimmedMessage = nextMessage.trim();

    if (!trimmedMessage) {
      return;
    }

    setIsSending(true);
    setError("");
    setMessage("");
    setMessages((currentMessages) => [
      ...currentMessages,
      { role: "user", content: trimmedMessage },
    ]);

    try {
      const response = await sendChatMessage({
        session_id: sessionId,
        message: trimmedMessage,
        cart_items: cart.map((item) => ({
          product_id: item.id,
          name: item.name,
          category: item.category,
          price: item.price,
          quantity: item.quantity,
        })),
      });

      response.cart_actions
        .filter((action) => !action.requires_confirmation)
        .forEach((action) => onApplyCartAction(action));

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          role: "assistant",
          content: response.message,
          products: response.products,
          cartActions: response.cart_actions,
          toolsUsed: response.tools_used,
          fallback: response.fallback,
        },
      ]);
    } catch {
      setError("The chat endpoint did not respond. Make sure the backend is running.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-950">Grocery Copilot</h2>
          <p className="mt-1 text-sm text-slate-600">
            Groq writes the answer after grounded catalog tools choose products and cart actions.
          </p>
        </div>
        <span
          className={`rounded px-2 py-1 text-xs font-medium ${providerStatusClass}`}
        >
          {providerLabel}
        </span>
      </div>

      {providerStatus && !providerStatus.client_ready ? (
        <div className="mb-4 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
          Groq is not active yet. Check `AI_AGENT_ENABLED`, `GROQ_API_KEY`, and
          backend dependencies.
          {providerStatus.langchain_import_error ? (
            <span> Import issue: {providerStatus.langchain_import_error}</span>
          ) : null}
        </div>
      ) : null}

      <div className="mb-4 max-h-96 space-y-3 overflow-y-auto rounded-md bg-slate-50 p-3">
        {messages.map((item, index) => (
          <div
            key={`${item.role}-${index}`}
            className={
              item.role === "user"
                ? "ml-auto max-w-[85%] rounded-md bg-red-600 px-3 py-2 text-sm text-white"
                : "max-w-[92%] rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800"
            }
          >
            <p>{item.content}</p>

            {item.toolsUsed?.length ? (
              <p className="mt-2 text-xs font-medium text-slate-500">
                Tools used: {item.toolsUsed.join(", ")}
                {typeof item.fallback === "boolean"
                  ? ` | ${item.fallback ? "fallback mode" : "Groq response"}`
                  : ""}
              </p>
            ) : null}

            {item.cartActions?.length ? (
              <div className="mt-3 space-y-2">
                {item.cartActions.map((action, actionIndex) => (
                  <div
                    key={`${action.type}-${action.product_id}-${actionIndex}`}
                    className="rounded-md border border-red-100 bg-red-50 p-2"
                  >
                    <p className="text-xs font-semibold text-red-900">
                      Action preview
                    </p>
                    <p className="mt-1 text-xs text-red-800">{action.message}</p>
                    {action.product ? (
                      action.requires_confirmation ? (
                        <button
                          type="button"
                          onClick={() =>
                            onAddToCart(action.product!, action.quantity ?? 1)
                          }
                          className="mt-2 h-8 w-full rounded-md bg-red-600 text-xs font-semibold text-white"
                        >
                          Confirm Add
                        </button>
                      ) : (
                        <p className="mt-2 text-xs font-semibold text-red-900">
                          Applied to cart
                        </p>
                      )
                    ) : null}
                    {!action.product && !action.requires_confirmation ? (
                      <p className="mt-2 text-xs font-semibold text-red-900">
                        Applied to cart
                      </p>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : null}

            {item.products?.length ? (
              <div className="mt-3 space-y-2">
                {item.products.slice(0, 8).map((product) => (
                  <div
                    key={product.id}
                    className="rounded-md border border-slate-200 bg-slate-50 p-2"
                  >
                    <p className="font-semibold text-slate-900">{product.name}</p>
                    <div className="mt-1 flex items-center justify-between gap-3">
                      <span className="text-xs text-slate-600">
                        {product.category}
                      </span>
                      <span className="text-sm font-bold text-red-700">
                        Tk {product.price}
                      </span>
                    </div>
                    {product.reason ? (
                      <p className="mt-1 text-xs text-slate-500">{product.reason}</p>
                    ) : null}
                    <button
                      type="button"
                      onClick={() => onAddToCart(product)}
                      className="mt-2 h-8 w-full rounded-md bg-slate-950 text-xs font-semibold text-white"
                    >
                      Add to Cart
                    </button>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        {promptChips.map((chip) => (
          <button
            key={chip}
            type="button"
            onClick={() => submitChat(chip)}
            disabled={isSending}
            className="rounded-md border border-slate-200 px-2 py-1 text-xs font-medium text-slate-700 hover:border-red-300 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {chip}
          </button>
        ))}
      </div>

      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          submitChat();
        }}
      >
        <input
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask about prices, products, bundles, or cart changes..."
          className="h-10 min-w-0 flex-1 rounded-md border border-slate-300 px-3 text-sm text-slate-900 outline-none placeholder:text-slate-500 focus:border-red-600"
        />
        <button
          type="submit"
          disabled={isSending}
          className="h-10 rounded-md bg-red-600 px-4 text-sm font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isSending ? "Thinking" : "Send"}
        </button>
      </form>

      {error ? <p className="mt-2 text-sm font-medium text-red-700">{error}</p> : null}
    </section>
  );
}
