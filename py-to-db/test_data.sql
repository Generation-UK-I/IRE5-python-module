-- Adminer 5.4.2 PostgreSQL 18.3 dump
-- Copy the below into Adminer's SQL command field to quickly rebuild the DB

connect "postgres";

DROP TABLE IF EXISTS "couriers";
DROP SEQUENCE IF EXISTS "public".couriers_id_seq;
CREATE SEQUENCE "public".couriers_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1;

CREATE TABLE "public"."couriers" (
    "id" integer DEFAULT nextval('couriers_id_seq') NOT NULL,
    "name" text NOT NULL,
    "phone" text NOT NULL,
    CONSTRAINT "couriers_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

INSERT INTO "couriers" ("id", "name", "phone") VALUES
(1,	'Alice Johnson',	'07123456789'),
(2,	'Bob Smith',	'07234567890'),
(3,	'Charlie Brown',	'07345678901');

DROP TABLE IF EXISTS "orders";
DROP SEQUENCE IF EXISTS "public".orders_id_seq;
CREATE SEQUENCE "public".orders_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1;

CREATE TABLE "public"."orders" (
    "id" integer DEFAULT nextval('orders_id_seq') NOT NULL,
    "customer_name" text NOT NULL,
    "customer_address" text NOT NULL,
    "customer_phone" text NOT NULL,
    "courier_id" integer,
    "status" text NOT NULL,
    "items" text NOT NULL,
    CONSTRAINT "orders_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

INSERT INTO "orders" ("id", "customer_name", "customer_address", "customer_phone", "courier_id", "status", "items") VALUES
(1,	'John Doe',	'12 Market Street, Glossop',	'07700111222',	1,	'Preparing',	'Espresso, Chocolate Muffin'),
(2,	'Sarah Green',	'45 High Road, Manchester',	'07700333444',	2,	'Out for delivery',	'Latte, Cappuccino'),
(3,	'Mark White',	'89 Station View, Sheffield',	'07700555666',	3,	'Delivered',	'Tea'),
(4,	'Emma Black',	'3 Riverside Walk, Stockport',	'07700777888',	1,	'Cancelled',	'Cappuccino, Muffin');

DROP TABLE IF EXISTS "products";
DROP SEQUENCE IF EXISTS "public".products_id_seq;
CREATE SEQUENCE "public".products_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1;

CREATE TABLE "public"."products" (
    "id" integer DEFAULT nextval('products_id_seq') NOT NULL,
    "name" text NOT NULL,
    "price" numeric(10,2) NOT NULL,
    CONSTRAINT "products_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

INSERT INTO "products" ("id", "name", "price") VALUES
(1,	'Espresso',	2.50),
(2,	'Cappuccino',	3.20),
(3,	'Latte',	3.50),
(4,	'Tea',	2.00),
(5,	'Chocolate Muffin',	2.75);

ALTER TABLE ONLY "public"."orders" ADD CONSTRAINT "orders_courier_id_fkey" FOREIGN KEY (courier_id) REFERENCES couriers(id);

-- 2026-04-24 22:03:19 UTC