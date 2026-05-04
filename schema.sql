CREATE TABLE IF NOT EXISTS customers (
    id    SERIAL PRIMARY KEY,
    nom   VARCHAR(100) NOT NULL,
    pays  VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS products (
    id    SERIAL PRIMARY KEY,
    nom   VARCHAR(200) NOT NULL,
    prix  NUMERIC(10, 2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    id             SERIAL PRIMARY KEY,
    customer_id    INT REFERENCES customers(id),
    statut         VARCHAR(20) NOT NULL DEFAULT 'pending',
    montant_total  NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    id            SERIAL PRIMARY KEY,
    order_id      INT REFERENCES orders(id),
    product_id    INT REFERENCES products(id),
    quantite      INT NOT NULL DEFAULT 1,
    prix_unitaire NUMERIC(10, 2) NOT NULL DEFAULT 0
);
