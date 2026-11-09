-- Synthetic fixture timestamps, NOT incident or recovery measurements.
-- MySQL entrypoint runs this only when the data directory is empty.
USE lab_config;
INSERT INTO orders (id, customer_alias, product_name, quantity, unit_price_vnd, created_at_utc)
SELECT n + 1,
       CONCAT('LAB-', LPAD(n + 1, 4, '0')),
       ELT(MOD(n, 3) + 1, 'Notebook', 'Pen', 'Folder'),
       MOD(n, 5) + 1,
       10000 + n * 1000,
       TIMESTAMPADD(SECOND, n, '2026-01-01 00:00:00')
FROM (
    SELECT tens.d * 10 + ones.d AS n
    FROM (SELECT 0 d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
          UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) tens
    CROSS JOIN
         (SELECT 0 d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
          UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
) numbers
ORDER BY n;
