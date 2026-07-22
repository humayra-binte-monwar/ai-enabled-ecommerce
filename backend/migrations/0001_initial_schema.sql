create extension if not exists pgcrypto;
create extension if not exists vector;

create table if not exists public.products (
    id text primary key,
    source_id text unique,
    slug text unique,
    name text not null,
    category text not null,
    normalized_category text,
    product_type text,
    brand text,
    price numeric(12, 2) not null check (price >= 0),
    old_price numeric(12, 2) check (old_price is null or old_price >= price),
    unit text,
    image_url text,
    product_url text not null unique,
    stock_status text not null default 'unknown' check (stock_status in ('in_stock', 'out_of_stock', 'unknown')),
    tags text[] not null default '{}',
    scraped_at timestamptz not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists products_category_idx on public.products (normalized_category);
create index if not exists products_price_idx on public.products (price);
create index if not exists products_name_idx on public.products using gin (to_tsvector('simple', name));

create table if not exists public.product_embeddings (
    product_id text primary key references public.products(id) on delete cascade,
    content_hash text not null,
    model text not null,
    embedding vector(1536) not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text,
    full_name text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.carts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    status text not null default 'active' check (status in ('active', 'converted', 'abandoned')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, status)
);

create table if not exists public.cart_items (
    id uuid primary key default gen_random_uuid(),
    cart_id uuid not null references public.carts(id) on delete cascade,
    product_id text not null references public.products(id),
    quantity integer not null check (quantity > 0 and quantity <= 99),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (cart_id, product_id)
);

create table if not exists public.orders (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete restrict,
    customer_name text not null,
    customer_phone text not null,
    customer_address text not null,
    subtotal numeric(12, 2) not null check (subtotal >= 0),
    delivery_fee numeric(12, 2) not null default 0 check (delivery_fee >= 0),
    total numeric(12, 2) not null check (total >= 0),
    currency text not null default 'BDT',
    status text not null default 'pending_payment' check (status in ('pending_payment', 'paid', 'confirmed', 'cancelled', 'refunded', 'payment_failed')),
    idempotency_key uuid not null unique,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists orders_user_created_idx on public.orders (user_id, created_at desc);

create table if not exists public.order_items (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references public.orders(id) on delete cascade,
    product_id text not null references public.products(id),
    product_name text not null,
    unit_price numeric(12, 2) not null check (unit_price >= 0),
    quantity integer not null check (quantity > 0 and quantity <= 99),
    created_at timestamptz not null default now()
);

create index if not exists order_items_order_idx on public.order_items (order_id);

create table if not exists public.payments (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references public.orders(id) on delete restrict,
    provider text not null,
    provider_payment_id text unique,
    status text not null check (status in ('created', 'requires_payment', 'succeeded', 'failed', 'cancelled', 'refunded')),
    amount numeric(12, 2) not null check (amount >= 0),
    currency text not null default 'BDT',
    provider_event_id text unique,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists payments_order_idx on public.payments (order_id);

create table if not exists public.ai_interactions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete set null,
    feature text not null,
    request_metadata jsonb not null default '{}',
    response_metadata jsonb not null default '{}',
    model text,
    latency_ms integer check (latency_ms is null or latency_ms >= 0),
    created_at timestamptz not null default now()
);

create index if not exists ai_interactions_user_created_idx on public.ai_interactions (user_id, created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists products_set_updated_at on public.products;
create trigger products_set_updated_at before update on public.products
for each row execute function public.set_updated_at();

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at before update on public.profiles
for each row execute function public.set_updated_at();

drop trigger if exists carts_set_updated_at on public.carts;
create trigger carts_set_updated_at before update on public.carts
for each row execute function public.set_updated_at();

drop trigger if exists cart_items_set_updated_at on public.cart_items;
create trigger cart_items_set_updated_at before update on public.cart_items
for each row execute function public.set_updated_at();

drop trigger if exists orders_set_updated_at on public.orders;
create trigger orders_set_updated_at before update on public.orders
for each row execute function public.set_updated_at();

drop trigger if exists payments_set_updated_at on public.payments;
create trigger payments_set_updated_at before update on public.payments
for each row execute function public.set_updated_at();

alter table public.products enable row level security;
alter table public.product_embeddings enable row level security;
alter table public.profiles enable row level security;
alter table public.carts enable row level security;
alter table public.cart_items enable row level security;
alter table public.orders enable row level security;
alter table public.order_items enable row level security;
alter table public.payments enable row level security;
alter table public.ai_interactions enable row level security;

drop policy if exists "public can read products" on public.products;
create policy "public can read products" on public.products
for select using (true);

drop policy if exists "users can read own profile" on public.profiles;
create policy "users can read own profile" on public.profiles
for select using (auth.uid() = id);

drop policy if exists "users can update own profile" on public.profiles;
create policy "users can update own profile" on public.profiles
for update using (auth.uid() = id) with check (auth.uid() = id);

drop policy if exists "users can read own carts" on public.carts;
create policy "users can read own carts" on public.carts
for select using (auth.uid() = user_id);

drop policy if exists "users can manage own carts" on public.carts;
create policy "users can manage own carts" on public.carts
for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "users can manage own cart items" on public.cart_items;
create policy "users can manage own cart items" on public.cart_items
for all using (
    exists (select 1 from public.carts where carts.id = cart_items.cart_id and carts.user_id = auth.uid())
)
with check (
    exists (select 1 from public.carts where carts.id = cart_items.cart_id and carts.user_id = auth.uid())
);

drop policy if exists "users can read own orders" on public.orders;
create policy "users can read own orders" on public.orders
for select using (auth.uid() = user_id);

drop policy if exists "users can read own order items" on public.order_items;
create policy "users can read own order items" on public.order_items
for select using (
    exists (select 1 from public.orders where orders.id = order_items.order_id and orders.user_id = auth.uid())
);

drop policy if exists "users can read own payments" on public.payments;
create policy "users can read own payments" on public.payments
for select using (
    exists (select 1 from public.orders where orders.id = payments.order_id and orders.user_id = auth.uid())
);

drop policy if exists "users can read own ai interactions" on public.ai_interactions;
create policy "users can read own ai interactions" on public.ai_interactions
for select using (auth.uid() = user_id);
