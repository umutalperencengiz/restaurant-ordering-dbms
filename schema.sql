-- Database schema for the restaurant ordering DBMS project
-- Run this once on a fresh MySQL instance:
--   mysql -u root -p < schema.sql

DROP DATABASE IF EXISTS assignment3database;
CREATE DATABASE assignment3database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE assignment3database;

-- ----------------------------------------------------------------
-- Sales clerks (staff who manage orders / ingredients)
-- ----------------------------------------------------------------
CREATE TABLE SalesClerk (
    clerk_id    INT AUTO_INCREMENT PRIMARY KEY,
    clerkName   VARCHAR(100) NOT NULL,
    email       VARCHAR(150) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,   -- bcrypt hash
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------
-- Customers
-- ----------------------------------------------------------------
CREATE TABLE Customer (
    customer_id   INT AUTO_INCREMENT PRIMARY KEY,
    customerName  VARCHAR(100) NOT NULL,
    telephoneNum  VARCHAR(30)  NOT NULL,
    email         VARCHAR(150) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------
-- Menu items
-- ----------------------------------------------------------------
CREATE TABLE Item (
    item_id   INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100) NOT NULL UNIQUE,
    price     DECIMAL(10,2) NOT NULL DEFAULT 0.00
);

-- ----------------------------------------------------------------
-- Ingredient usage per item (grams / units)
-- item_id = 7 holds the running TOTALS of all ingredients in stock.
-- ----------------------------------------------------------------
CREATE TABLE ingredients (
    item_id   INT PRIMARY KEY,
    spice     INT NOT NULL DEFAULT 0,
    vegetable INT NOT NULL DEFAULT 0,
    meat      INT NOT NULL DEFAULT 0,
    FOREIGN KEY (item_id) REFERENCES Item(item_id)
);

-- ----------------------------------------------------------------
-- Orders placed by customers
-- ----------------------------------------------------------------
CREATE TABLE orders (
    order_id    INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    name        VARCHAR(100) NOT NULL,      -- item name ordered
    quantity    INT NOT NULL DEFAULT 1,
    date        DATE NOT NULL,
    totalPrice  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);

-- ----------------------------------------------------------------
-- Daily ingredient orders / restocking log
-- ----------------------------------------------------------------
CREATE TABLE order_ingredients (
    order_date        DATE PRIMARY KEY,
    price_spice       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    price_vegetables  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    price_meat        DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_spice       INT NOT NULL DEFAULT 0,
    total_vegetables  INT NOT NULL DEFAULT 0,
    total_meat        INT NOT NULL DEFAULT 0
);

-- ----------------------------------------------------------------
-- Seed data (example)
-- ----------------------------------------------------------------
INSERT INTO Item (name, price) VALUES
    ('Lahmacun', 45.00),
    ('Pide', 55.00),
    ('Kebab', 85.00),
    ('Durum', 60.00),
    ('Beverage', 15.00);

INSERT INTO ingredients (item_id, spice, vegetable, meat) VALUES
    (1, 10, 20, 5),
    (2, 5,  30, 10),
    (3, 15, 10, 40),
    (4, 10, 20, 25),
    (5, 0,  0,  0),
    (7, 500, 500, 500);   -- running stock totals

INSERT INTO SalesClerk (clerkName, email, password) VALUES
    ('Ahmet Demir', 'ahmet@restaurant.local',
     '$2b$12$K.v1xJQ9yGJ7j2Y7j2Y7eO9yGJ7j2Y7eO9yGJ7j2Y7eO9yGJ7j2');  -- password: clerk123
