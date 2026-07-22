-- Upgrade prototype checkout tables without deleting existing data.
-- Run this after 0001_initial_schema.sql in the Supabase SQL Editor.

alter table public.order_items
    add column if not exists product_name text;

alter table public.order_items
    add column if not exists unit_price numeric(12, 2);

alter table public.order_items
    add column if not exists quantity integer not null default 1;

alter table public.order_items
    add column if not exists name text;

alter table public.order_items
    add column if not exists price numeric(12, 2);

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

-- The original prototype used name and price. Keep those legacy columns
-- nullable because the application now stores immutable product snapshots in
-- product_name and unit_price.
alter table public.order_items
    alter column name drop not null;

alter table public.order_items
    alter column price drop not null;

update public.order_items
set name = product_name
where name is null;

update public.order_items
set price = unit_price
where price is null;

alter table public.payments
    add column if not exists currency text not null default 'BDT';
