-- SQLite schema for Restaurant Ordering DBMS
-- No external database server needed — everything lives in restaurant.db

DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS order_ingredients;
DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS Item;
DROP TABLE IF EXISTS Customer;
DROP TABLE IF EXISTS SalesClerk;

CREATE TABLE SalesClerk (
    clerk_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    clerkName   TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    password    TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Customer (
    customer_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    customerName  TEXT NOT NULL,
    telephoneNum  TEXT NOT NULL,
    email         TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Item (
    item_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE,
    price     REAL NOT NULL DEFAULT 0.00
);

CREATE TABLE ingredients (
    item_id   INTEGER PRIMARY KEY,
    spice     INTEGER NOT NULL DEFAULT 0,
    vegetable INTEGER NOT NULL DEFAULT 0,
    meat      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    name        TEXT NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 1,
    date        TEXT NOT NULL,
    totalPrice  REAL NOT NULL DEFAULT 0.00
);

CREATE TABLE order_ingredients (
    order_date        TEXT PRIMARY KEY,
    price_spice       REAL NOT NULL DEFAULT 0.00,
    price_vegetables  REAL NOT NULL DEFAULT 0.00,
    price_meat        REAL NOT NULL DEFAULT 0.00,
    total_spice       INTEGER NOT NULL DEFAULT 0,
    total_vegetables  INTEGER NOT NULL DEFAULT 0,
    total_meat        INTEGER NOT NULL DEFAULT 0
);

-- Seed menu items
INSERT INTO Item (name, price) VALUES
    ('Lahmacun', 45.00),
    ('Pide', 55.00),
    ('Kebab', 85.00),
    ('Durum', 60.00),
    ('Beverage', 15.00);

-- Seed ingredient usage per item (item_id = 7 holds running stock totals)
INSERT INTO ingredients (item_id, spice, vegetable, meat) VALUES
    (1, 10, 20, 5),
    (2, 5,  30, 10),
    (3, 15, 10, 40),
    (4, 10, 20, 25),
    (5, 0,  0,  0),
    (7, 500, 500, 500);
