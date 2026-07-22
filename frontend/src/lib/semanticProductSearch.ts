import type { Product, ProductFinderProduct } from "@/lib/api";

const MODEL_ID = "onnx-community/all-MiniLM-L6-v2-ONNX";
const MAX_INDEXED_PRODUCTS = 500;

type FeatureExtractor = (
  input: string | string[],
  options: { pooling: "mean"; normalize: boolean }
) => Promise<{ data: Float32Array | number[]; dims?: number[] }>;

type IndexedProduct = {
  product: Product;
  embedding: number[];
};

let extractorPromise: Promise<FeatureExtractor> | null = null;
let indexedProducts: IndexedProduct[] = [];
let indexedSignature = "";

function getProductDocument(product: Product) {
  return [
    product.name,
    product.brand,
    product.normalized_category ?? product.category,
    product.product_type,
    product.unit,
    product.tags?.join(" "),
  ]
    .filter(Boolean)
    .join(". ");
}

function getCatalogSignature(products: Product[]) {
  return products.map((product) => `${product.id}:${product.name}`).join("|");
}

async function getExtractor() {
  if (!extractorPromise) {
    extractorPromise = import("@huggingface/transformers").then(
      async ({ env, pipeline }) => {
        env.allowLocalModels = false;
        return pipeline("feature-extraction", MODEL_ID, {
          dtype: "q8",
        }) as Promise<FeatureExtractor>;
      }
    );
  }

  return extractorPromise;
}

async function embedTexts(texts: string[]) {
  const extractor = await getExtractor();
  const output = await extractor(texts, {
    pooling: "mean",
    normalize: true,
  });
  const values = Array.from(output.data);
  const rowCount = output.dims?.[0] ?? texts.length;
  const columnCount = output.dims?.[1] ?? Math.floor(values.length / rowCount);

  return Array.from({ length: rowCount }, (_, rowIndex) =>
    values.slice(rowIndex * columnCount, (rowIndex + 1) * columnCount)
  );
}

async function ensureProductIndex(products: Product[]) {
  const indexableProducts = products.slice(0, MAX_INDEXED_PRODUCTS);
  const signature = getCatalogSignature(indexableProducts);

  if (signature === indexedSignature && indexedProducts.length > 0) {
    return indexedProducts;
  }

  const embeddings = await embedTexts(indexableProducts.map(getProductDocument));
  indexedProducts = indexableProducts.map((product, index) => ({
    product,
    embedding: embeddings[index],
  }));
  indexedSignature = signature;

  return indexedProducts;
}

function cosineSimilarity(first: number[], second: number[]) {
  let score = 0;
  const length = Math.min(first.length, second.length);

  for (let index = 0; index < length; index += 1) {
    score += first[index] * second[index];
  }

  return score;
}

function toFinderProduct(product: Product, score: number): ProductFinderProduct {
  const category = product.normalized_category ?? product.category;
  const confidence = Math.max(0, Math.min(99, Math.round(score * 100)));

  return {
    id: product.id,
    name: product.name,
    category: product.category,
    price: product.price,
    unit: product.unit,
    image_url: product.image_url,
    product_url: product.product_url,
    tags: product.tags,
    normalized_category: product.normalized_category,
    product_type: product.product_type,
    reason: `${confidence}% semantic match from ${category}`,
  };
}

export async function semanticProductSearch(products: Product[], query: string) {
  const [queryEmbedding] = await embedTexts([query]);
  const index = await ensureProductIndex(products);

  return index
    .map(({ product, embedding }) => ({
      product,
      score: cosineSimilarity(queryEmbedding, embedding),
    }))
    .sort((first, second) => second.score - first.score)
    .slice(0, 8)
    .map(({ product, score }) => toFinderProduct(product, score));
}

export function getSemanticSearchModelName() {
  return MODEL_ID;
}
