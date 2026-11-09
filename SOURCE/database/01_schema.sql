USE lab_config;
CREATE TABLE orders (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    customer_alias VARCHAR(40) NOT NULL,
    product_name VARCHAR(80) NOT NULL,
    quantity INT NOT NULL,
    unit_price_vnd BIGINT NOT NULL,
    created_at_utc DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT valid_quantity CHECK (quantity BETWEEN 1 AND 100),
    CONSTRAINT valid_price CHECK (unit_price_vnd BETWEEN 1 AND 100000000),
    CONSTRAINT valid_product CHECK (product_name IN ('Notebook', 'Pen', 'Folder'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
