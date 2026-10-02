# Sample SQL Statements for Project Sprint 4

## Create Tables

```sql
# Products
CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price NUMERIC(10,2) NOT NULL
);

# Couriers
CREATE TABLE couriers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL
);

# Orders
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL,
    customer_address TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    courier_id INTEGER REFERENCES couriers(id),
    status TEXT NOT NULL,
    items TEXT NOT NULL 
);
```

- `serial PRIMARY KEY`: Auto-incrementing integer for IDs
- `REFERENCES couriers(id)`: creates a foreign key
- `items`: currently includes multiple values (not normalised - fix later)

### Python Sample Code

```py
...

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
   
def create_tables():
    conn = get_connection() # Call the get_connection() function
    cur = conn.cursor() # Call the cursor method against the 'conn' object

# Create a table using the cursor's execute method
    cur.execute("""
        CREATE TABLE IF NOT EXISTS more_products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price NUMERIC(10,2) NOT NULL
        );
    """)
    
    conn.commit() # Commit changes to DB
    cur.close() # Close cursor
    conn.close() # Close connection
    print("Table created successfully!")
    
create_tables()
```

## Adding Test Data

```sql
-- Products
INSERT INTO products (name, price) VALUES
('Espresso', 2.50),
('Cappuccino', 3.20),
('Latte', 3.50),
('Tea', 2.00),
('Chocolate Muffin', 2.75);

-- Couriers
INSERT INTO couriers (name, phone) VALUES
('Alice Johnson', '07123456789'),
('Bob Smith', '07234567890'),
('Charlie Brown', '07345678901');

-- Orders
-- items column is stored as TEXT (e.g. comma-separated product names or IDs)
INSERT INTO orders (
    customer_name,
    customer_address,
    customer_phone,
    courier_id,
    status,
    items
) VALUES
(
    'John Doe',
    '12 Market Street, Glossop',
    '07700111222',
    1,
    'Preparing',
    'Espresso, Chocolate Muffin'
),
(
    'Sarah Green',
    '45 High Road, Manchester',
    '07700333444',
    2,
    'Out for delivery',
    'Latte, Cappuccino'
),
(
    'Mark White',
    '89 Station View, Sheffield',
    '07700555666',
    3,
    'Delivered',
    'Tea'
),
(
    'Emma Black',
    '3 Riverside Walk, Stockport',
    '07700777888',
    1,
    'Cancelled',
    'Cappuccino, Muffin'
);
```
