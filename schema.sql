-- SQLite schema for Restaurant Ordering DBMS
-- No external database server needed — everything lives in restaurant.db
--
-- This file is executed automatically on startup and is idempotent:
-- re-running it never drops tables or duplicates seed rows.

CREATE TABLE IF NOT EXISTS SalesClerk (
    clerk_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    clerkName   TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    password    TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Customer (
    customer_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    customerName  TEXT NOT NULL,
    telephoneNum  TEXT NOT NULL,
    email         TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Item (
    item_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE,
    price     REAL NOT NULL DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS ingredients (
    item_id   INTEGER PRIMARY KEY,
    spice     INTEGER NOT NULL DEFAULT 0,
    vegetable INTEGER NOT NULL DEFAULT 0,
    meat      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    order_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    name        TEXT NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 1,
    date        TEXT NOT NULL,
    totalPrice  REAL NOT NULL DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS order_ingredients (
    order_date        TEXT PRIMARY KEY,
    price_spice       REAL NOT NULL DEFAULT 0.00,
    price_vegetables  REAL NOT NULL DEFAULT 0.00,
    price_meat        REAL NOT NULL DEFAULT 0.00,
    total_spice       INTEGER NOT NULL DEFAULT 0,
    total_vegetables  INTEGER NOT NULL DEFAULT 0,
    total_meat        INTEGER NOT NULL DEFAULT 0
);

-- Seed menu items (safe to re-run thanks to the UNIQUE name constraint)
INSERT OR IGNORE INTO Item (name, price) VALUES
    ('Lahmacun', 45.00),
    ('Pide', 55.00),
    ('Kebab', 85.00),
    ('Durum', 60.00),
    ('Beverage', 15.00);

-- Ingredient usage per dish (grams per portion)
INSERT OR IGNORE INTO ingredients (item_id, spice, vegetable, meat)
    SELECT item_id, 10, 20, 5 FROM Item WHERE name = 'Lahmacun';
INSERT OR IGNORE INTO ingredients (item_id, spice, vegetable, meat)
    SELECT item_id, 5, 30, 10 FROM Item WHERE name = 'Pide';
INSERT OR IGNORE INTO ingredients (item_id, spice, vegetable, meat)
    SELECT item_id, 15, 10, 40 FROM Item WHERE name = 'Kebab';
INSERT OR IGNORE INTO ingredients (item_id, spice, vegetable, meat)
    SELECT item_id, 10, 20, 25 FROM Item WHERE name = 'Durum';
INSERT OR IGNORE INTO ingredients (item_id, spice, vegetable, meat)
    SELECT item_id, 0, 0, 0 FROM Item WHERE name = 'Beverage';

-- item_id = 7 is the running stock row (not a dish)
INSERT OR IGNORE INTO ingredients (item_id, spice, vegetable, meat) VALUES
    (7, 500, 500, 500);
