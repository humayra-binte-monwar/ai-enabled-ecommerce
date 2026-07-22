-- all-MiniLM-L6-v2 emits normalized 384-dimensional embeddings.
-- Keep the original 1536-dimensional column nullable for backward compatibility.

alter table public.product_embeddings
    alter column embedding drop not null;

alter table public.product_embeddings
    add column if not exists embedding_384 vector(384);

create index if not exists product_embeddings_embedding_384_hnsw_idx
    on public.product_embeddings
    using hnsw (embedding_384 vector_cosine_ops)
    with (m = 16, ef_construction = 64);

create or replace function public.match_products_hybrid(
    query_embedding vector(384),
    match_count integer default 8,
    filter_category text default null,
    min_price numeric default null,
    max_price numeric default null
)
returns table (
    id text,
    name text,
    category text,
    brand text,
    price numeric,
    unit text,
    image_url text,
    product_url text,
    tags text[],
    normalized_category text,
    product_type text,
    reason text,
    semantic_score double precision
)
language sql
stable
as $$
    select
        products.id,
        products.name,
        products.category,
        products.brand,
        products.price,
        products.unit,
        products.image_url,
        products.product_url,
        products.tags,
        products.normalized_category,
        products.product_type,
        'Retrieved by semantic similarity from the product catalog'::text as reason,
        (1 - (product_embeddings.embedding_384 <=> query_embedding))::double precision as semantic_score
    from public.product_embeddings
    join public.products on products.id = product_embeddings.product_id
    where product_embeddings.embedding_384 is not null
      and (filter_category is null or lower(coalesce(products.normalized_category, products.category)) = lower(filter_category))
      and (min_price is null or products.price >= min_price)
      and (max_price is null or products.price <= max_price)
    order by product_embeddings.embedding_384 <=> query_embedding
    limit least(greatest(match_count, 1), 20);
$$;

grant execute on function public.match_products_hybrid(vector, integer, text, numeric, numeric)
    to anon, authenticated, service_role;
