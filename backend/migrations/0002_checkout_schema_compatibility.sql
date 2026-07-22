-- Upgrade prototype checkout tables without deleting existing data.
-- Run this after 0001_initial_schema.sql in the Supabase SQL Editor.

alter table public.order_items
    add column if not exists product_name text;

alter table public.order_items
    add column if not exists unit_price numeric(12, 2);

alter table public.order_items
    add column if not exists quantity integer not null default 1;

update public.order_items as order_item
set product_name = products.name
from public.products as products
where order_item.product_id = products.id
  and order_item.product_name is null;

update public.order_items as order_item
set unit_price = products.price
from public.products as products
where order_item.product_id = products.id
  and order_item.unit_price is null;

alter table public.order_items
    alter column product_name set not null;

alter table public.order_items
    alter column unit_price set not null;

alter table public.payments
    add column if not exists currency text not null default 'BDT';
