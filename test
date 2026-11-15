
SELECT
    c.table_name,
    c.ordinal_position AS column_order,
    c.column_name,
    pg_catalog.format_type(
        a.atttypid, a.atttypmod
    ) AS data_type,
    c.is_nullable,
    c.column_default,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM pg_catalog.pg_index i
            WHERE i.indrelid = t.oid
              AND i.indisprimary
              AND a.attnum = ANY(i.indkey)
        )
        THEN 'YES'
        ELSE 'NO'
    END AS primary_key
FROM information_schema.columns c
JOIN pg_catalog.pg_namespace n
    ON n.nspname = c.table_schema
JOIN pg_catalog.pg_class t
    ON t.relnamespace = n.oid
    AND t.relname = c.table_name
    AND t.relkind IN ('r', 'p')
JOIN pg_catalog.pg_attribute a
    ON a.attrelid = t.oid
    AND a.attname = c.column_name
WHERE c.table_schema = 'public'
ORDER BY c.table_name, c.ordinal_position;
