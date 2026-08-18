\set ON_ERROR_STOP on
\pset pager off
-- CompileDB mapping-aware relational workload
-- Conceptual workload: example2_schema_driven_selectivity_100_w10
-- Mapping ID: 3bba9ee6fbdf4e9bb7b96731f96ac463327fab03fd982ca89d52b96e1755c43c
-- Query shapes: 100
-- Executed statements: 100
BEGIN TRANSACTION READ ONLY;

-- Q001 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.fit_type_men, e.dimensions, e.quantity FROM MenClothing e WHERE e.product_id <= 15563858;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."fit_type_men" AS "fit_type_men",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."menclothing_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."fit_type_men" AS "fit_type_men",
    "b0"."dimensions" AS "dimensions",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."product_id" <= 15563858);

-- Q002 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.product_id, e.cpu, e.warranty_months, e.quantity FROM Desktop e WHERE e.ram_gb > 8;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."ram_gb" AS "ram_gb",
        "source"."warranty_months" AS "warranty_months",
        "source"."desktop_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_6" AS "source"
)
SELECT DISTINCT 
    "b0"."product_id" AS "product_id",
    "b0"."cpu" AS "cpu",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."ram_gb" > 8);

-- Q003 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.is_active, e.warranty_months FROM Phone e WHERE e.product_name <= 'Self-enabling 6thgeneration artificial intelligence';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_11" AS "source"
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."is_active" AS "is_active",
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."product_name" <= 'Self-enabling 6thgeneration artificial intelligence');

-- Q004 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.is_active, e.base_price FROM KitchenAppliance e WHERE e.warranty_years <= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_years" AS "warranty_years",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active"
    FROM "relation_14" AS "source"
)
SELECT DISTINCT 
    "b0"."is_active" AS "is_active",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."warranty_years" <= 2);

-- Q005 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.product_id, e.warranty_months FROM Laptop e WHERE e.base_price >= 59;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."laptop_id" AS "product_id"
    FROM "relation_7" AS "source"
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."product_id" AS "product_id",
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."base_price" >= 59);

-- Q006 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Accessory e WHERE e.dimensions <= 'medium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."dimensions" <= 'medium');

-- Q007 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.employee_no, e.password_hash FROM Employee e WHERE e.employee_no < 'EMP-49995178';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."employee_no" AS "employee_no",
        "source"."password_hash" AS "password_hash"
    FROM "relation_26" AS "source"
)
SELECT 
    "b0"."employee_no" AS "employee_no",
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."employee_no" < 'EMP-49995178');

-- Q008 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.email, e.user_id FROM Employee e WHERE e.password_hash <= 'fdf1aa44550352d5c2eb1369a2b93da819d08a6bbe86854d812d213213b44528';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash",
        "source"."employee_id" AS "user_id"
    FROM "relation_26" AS "source"
)
SELECT 
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."password_hash" <= 'fdf1aa44550352d5c2eb1369a2b93da819d08a6bbe86854d812d213213b44528');

-- Q009 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.dimensions FROM Footwear e WHERE e.sku >= 'SKU-Zigv-53703687';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_19" AS "source"
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-Zigv-53703687');

-- Q010 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.is_active FROM Camera e WHERE e.product_name >= 'Distributed national model';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_10" AS "source"
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_name" >= 'Distributed national model');

-- Q011 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Smartwatch e WHERE e.product_id < 11679217;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."smartwatch_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_9" AS "source"
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_id" < 11679217);

-- Q012 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.base_price, e.is_active, e.product_id FROM Smartwatch e WHERE e.product_id > 11447969;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."smartwatch_id" AS "product_id"
    FROM "relation_9" AS "source"
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."base_price" AS "base_price",
    "b0"."is_active" AS "is_active",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."product_id" > 11447969);

-- Q013 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system, e.dimensions, e.product_id, e.product_name FROM Clothing e WHERE e.base_price <= 120;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."clothing_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_16" AS "source"
    UNION ALL
    SELECT
        "source"."size_system" AS "size_system",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."menclothing_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_17" AS "source"
    UNION ALL
    SELECT
        "source"."size_system" AS "size_system",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."womenclothing_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_18" AS "source"
)
SELECT 
    "b0"."size_system" AS "size_system",
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."base_price" <= 120);

-- Q014 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.base_price, e.product_id FROM Accessory e WHERE e.quantity >= 13;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."accessory_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."base_price" AS "base_price",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."quantity" >= 13);

-- Q015 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.battery_wh, e.quantity, e.product_name, e.cpu FROM Laptop e WHERE e.cpu <= 'Ryzen 5';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."battery_wh" AS "battery_wh",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_7" AS "source"
)
SELECT DISTINCT 
    "b0"."battery_wh" AS "battery_wh",
    "b0"."quantity" AS "quantity",
    "b0"."product_name" AS "product_name",
    "b0"."cpu" AS "cpu"
FROM "b0"
WHERE ("b0"."cpu" <= 'Ryzen 5');

-- Q016 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.ram_gb, e.quantity, e.sku FROM Laptop e WHERE e.product_name > 'Diverse directional strategy';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ram_gb" AS "ram_gb",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_7" AS "source"
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."ram_gb" AS "ram_gb",
    "b0"."quantity" AS "quantity",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."product_name" > 'Diverse directional strategy');

-- Q017 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.product_id, e.base_price, e.product_name FROM Media e WHERE e.product_id <= 16364312;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."media_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_20" AS "source"
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."product_id" AS "product_id",
    "b0"."base_price" AS "base_price",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_id" <= 16364312);

-- Q018 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.quantity, e.delivery_type FROM Software e WHERE e.delivery_type < 'stream';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity"
    FROM "relation_21" AS "source"
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."quantity" AS "quantity",
    "b0"."delivery_type" AS "delivery_type"
FROM "b0"
WHERE ("b0"."delivery_type" < 'stream');

-- Q019 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id FROM WomenClothing e WHERE e.base_price <= 144;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."womenclothing_id" AS "product_id"
    FROM "relation_18" AS "source"
)
SELECT 
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."base_price" <= 144);

-- Q020 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.product_name, e.warranty_months, e.carrier_lock FROM Phone e WHERE e.base_price <= 883;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."carrier_lock" AS "carrier_lock",
        "source"."base_price" AS "base_price",
        "source"."phone_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_11" AS "source"
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."product_name" AS "product_name",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."carrier_lock" AS "carrier_lock"
FROM "b0"
WHERE ("b0"."base_price" <= 883);

-- Q021 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash, e.email, e.user_id FROM Employee e WHERE e.user_id > 1360680;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash",
        "source"."employee_id" AS "user_id"
    FROM "relation_26" AS "source"
)
SELECT 
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."user_id" > 1360680);

-- Q022 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.fit_type_women FROM WomenClothing e WHERE e.quantity >= 4;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."fit_type_women" AS "fit_type_women"
    FROM "relation_18" AS "source"
)
SELECT 
    "b0"."fit_type_women" AS "fit_type_women"
FROM "b0"
WHERE ("b0"."quantity" >= 4);

-- Q023 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.renewal_date, e.email FROM PrimeCustomer e WHERE e.renewal_date > '2026-04-04';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."renewal_date" AS "renewal_date",
        "source"."email" AS "email"
    FROM "relation_24" AS "source"
)
SELECT 
    "b0"."renewal_date" AS "renewal_date",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."renewal_date" > '2026-04-04');

-- Q024 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.product_id, e.product_name, e.quantity FROM Smartwatch e WHERE e.sku >= 'SKU-AaFi-92012341';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."smartwatch_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_9" AS "source"
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."product_id" AS "product_id",
    "b0"."product_name" AS "product_name",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-AaFi-92012341');

-- Q025 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.sku, e.base_price FROM Apparel e WHERE e.product_name >= 'Compatible systemic middleware';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_15" AS "source"
    UNION ALL
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_16" AS "source"
    UNION ALL
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_17" AS "source"
    UNION ALL
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_18" AS "source"
    UNION ALL
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_19" AS "source"
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."sku" AS "sku",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."product_name" >= 'Compatible systemic middleware');

-- Q026 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash, e.email, e.company_name, e.loyalty_tier FROM BusinessCustomer e WHERE e.email <= 'kimberlyduffy@example.net';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."company_name" AS "company_name",
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash"
    FROM "relation_25" AS "source"
)
SELECT 
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email",
    "b0"."company_name" AS "company_name",
    "b0"."loyalty_tier" AS "loyalty_tier"
FROM "b0"
WHERE ("b0"."email" <= 'kimberlyduffy@example.net');

-- Q027 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.employee_no, e.email, e.user_id, e.password_hash FROM Employee e WHERE e.email < 'klinevictoria@example.net';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."employee_no" AS "employee_no",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash",
        "source"."employee_id" AS "user_id"
    FROM "relation_26" AS "source"
)
SELECT 
    "b0"."employee_no" AS "employee_no",
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id",
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."email" < 'klinevictoria@example.net');

-- Q028 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions FROM MenClothing e WHERE e.material >= 'cotton';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."material" AS "material",
        "source"."dimensions" AS "dimensions"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."material" >= 'cotton');

-- Q029 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.screen_size_in, e.base_price, e.warranty_months, e.dimensions FROM Tablet e WHERE e.product_id > 11384081;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."tablet_id" AS "product_id",
        "source"."screen_size_in" AS "screen_size_in"
    FROM "relation_8" AS "source"
)
SELECT 
    "b0"."screen_size_in" AS "screen_size_in",
    "b0"."base_price" AS "base_price",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."product_id" > 11384081);

-- Q030 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.renewal_date FROM PrimeCustomer e WHERE e.email > 'jeffreyhill@example.net';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."renewal_date" AS "renewal_date",
        "source"."email" AS "email"
    FROM "relation_24" AS "source"
)
SELECT 
    "b0"."renewal_date" AS "renewal_date"
FROM "b0"
WHERE ("b0"."email" > 'jeffreyhill@example.net');

-- Q031 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system, e.material FROM WomenClothing e WHERE e.sku <= 'SKU-ZsSo-15977333';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."material" AS "material",
        "source"."sku" AS "sku"
    FROM "relation_18" AS "source"
)
SELECT 
    "b0"."size_system" AS "size_system",
    "b0"."material" AS "material"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-ZsSo-15977333');

-- Q032 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.cpu, e.sku, e.product_name FROM Desktop e WHERE e.product_id < 10638105;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."desktop_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_6" AS "source"
)
SELECT 
    "b0"."cpu" AS "cpu",
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_id" < 10638105);

-- Q033 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.is_active, e.quantity, e.base_price FROM Laptop e WHERE e.ram_gb > 8;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ram_gb" AS "ram_gb",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_7" AS "source"
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active",
    "b0"."quantity" AS "quantity",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."ram_gb" > 8);

-- Q034 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash, e.email, e.loyalty_tier FROM PrimeCustomer e WHERE e.email <= 'ujohnson@example.com';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash"
    FROM "relation_24" AS "source"
)
SELECT 
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email",
    "b0"."loyalty_tier" AS "loyalty_tier"
FROM "b0"
WHERE ("b0"."email" <= 'ujohnson@example.com');

-- Q035 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.warranty_months FROM Desktop e WHERE e.product_id >= 9901239;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."desktop_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_6" AS "source"
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."product_id" >= 9901239);

-- Q036 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id FROM Employee e WHERE e.user_id < 1472293;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."employee_id" AS "user_id"
    FROM "relation_26" AS "source"
)
SELECT 
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."user_id" < 1472293);

-- Q037 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity FROM MenClothing e WHERE e.size_system > 'UK';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."quantity" AS "quantity"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."size_system" > 'UK');

-- Q038 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash FROM Employee e WHERE e.password_hash < 'fdf23350bebe7b46ba6ed722980f14fdb83dc70b02a223f8693e700ca08caab9';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."password_hash" AS "password_hash"
    FROM "relation_26" AS "source"
)
SELECT 
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."password_hash" < 'fdf23350bebe7b46ba6ed722980f14fdb83dc70b02a223f8693e700ca08caab9');

-- Q039 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.dimensions FROM Phone e WHERE e.is_active > 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active"
    FROM "relation_11" AS "source"
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."is_active" > 0);

-- Q040 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.loyalty_tier, e.email FROM PrimeCustomer e WHERE e.email < 'kimberlyscott@example.com';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email"
    FROM "relation_24" AS "source"
)
SELECT 
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."email" < 'kimberlyscott@example.com');

-- Q041 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.product_id FROM Accessory e WHERE e.sku > 'SKU-UYkC-98748374';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_12" AS "source"
)
SELECT DISTINCT 
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."sku" > 'SKU-UYkC-98748374');

-- Q042 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku FROM MenClothing e WHERE e.is_active >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."is_active" >= 1);

-- Q043 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.fit_type_women, e.size_system, e.product_name FROM WomenClothing e WHERE e.material >= 'cotton';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."material" AS "material",
        "source"."product_name" AS "product_name",
        "source"."fit_type_women" AS "fit_type_women"
    FROM "relation_18" AS "source"
)
SELECT 
    "b0"."fit_type_women" AS "fit_type_women",
    "b0"."size_system" AS "size_system",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."material" >= 'cotton');

-- Q044 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.is_active, e.warranty_months, e.dimensions, e.product_id FROM Laptop e WHERE e.warranty_months < 36;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."laptop_id" AS "product_id"
    FROM "relation_7" AS "source"
)
SELECT DISTINCT 
    "b0"."is_active" AS "is_active",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."warranty_months" < 36);

-- Q045 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.form_factor FROM Desktop e WHERE e.sku > 'SKU-KZwS-86397790';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."form_factor" AS "form_factor",
        "source"."sku" AS "sku"
    FROM "relation_6" AS "source"
)
SELECT 
    "b0"."form_factor" AS "form_factor"
FROM "b0"
WHERE ("b0"."sku" > 'SKU-KZwS-86397790');

-- Q046 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.renewal_date, e.user_id FROM PrimeCustomer e WHERE e.email <= 'schneidersophia@example.com';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."renewal_date" AS "renewal_date",
        "source"."email" AS "email",
        "source"."primecustomer_id" AS "user_id"
    FROM "relation_24" AS "source"
)
SELECT 
    "b0"."renewal_date" AS "renewal_date",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."email" <= 'schneidersophia@example.com');

-- Q047 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.is_active FROM Electronics e WHERE e.sku >= 'SKU-AXln-03395574';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_4" AS "source"
    UNION ALL
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_5" AS "source"
    UNION ALL
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_6" AS "source"
    UNION ALL
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_7" AS "source"
    UNION ALL
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_8" AS "source"
    UNION ALL
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_9" AS "source"
    UNION ALL
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_10" AS "source"
    UNION ALL
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_11" AS "source"
    UNION ALL
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-AXln-03395574');

-- Q048 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.cpu, e.battery_wh, e.sku, e.ram_gb FROM Laptop e WHERE e.battery_wh <= 65;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."ram_gb" AS "ram_gb",
        "source"."battery_wh" AS "battery_wh",
        "source"."sku" AS "sku"
    FROM "relation_7" AS "source"
)
SELECT 
    "b0"."cpu" AS "cpu",
    "b0"."battery_wh" AS "battery_wh",
    "b0"."sku" AS "sku",
    "b0"."ram_gb" AS "ram_gb"
FROM "b0"
WHERE ("b0"."battery_wh" <= 65);

-- Q049 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.product_name, e.quantity, e.product_id FROM Desktop e WHERE e.sku >= 'SKU-PqiO-90741416';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."desktop_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_6" AS "source"
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."product_name" AS "product_name",
    "b0"."quantity" AS "quantity",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-PqiO-90741416');

-- Q050 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sensor_mp, e.sku, e.product_name FROM Camera e WHERE e.quantity >= 23;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sensor_mp" AS "sensor_mp",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_10" AS "source"
)
SELECT 
    "b0"."sensor_mp" AS "sensor_mp",
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."quantity" >= 23);

-- Q051 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.renewal_date, e.password_hash FROM PrimeCustomer e WHERE e.loyalty_tier < 'silver';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."renewal_date" AS "renewal_date",
        "source"."password_hash" AS "password_hash"
    FROM "relation_24" AS "source"
)
SELECT 
    "b0"."renewal_date" AS "renewal_date",
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."loyalty_tier" < 'silver');

-- Q052 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.base_price, e.dimensions, e.quantity FROM Smartwatch e WHERE e.quantity < 23;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity"
    FROM "relation_9" AS "source"
)
SELECT DISTINCT 
    "b0"."base_price" AS "base_price",
    "b0"."dimensions" AS "dimensions",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."quantity" < 23);

-- Q053 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.is_active, e.dimensions, e.product_name, e.energy_rating FROM KitchenAppliance e WHERE e.dimensions >= 'medium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."energy_rating" AS "energy_rating",
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_14" AS "source"
)
SELECT DISTINCT 
    "b0"."is_active" AS "is_active",
    "b0"."dimensions" AS "dimensions",
    "b0"."product_name" AS "product_name",
    "b0"."energy_rating" AS "energy_rating"
FROM "b0"
WHERE ("b0"."dimensions" >= 'medium');

-- Q054 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.is_active FROM Footwear e WHERE e.is_active >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_19" AS "source"
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."is_active" >= 1);

-- Q055 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.is_active, e.sku FROM Tablet e WHERE e.quantity >= 17;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."tablet_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_8" AS "source"
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."is_active" AS "is_active",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."quantity" >= 17);

-- Q056 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.dimensions, e.screen_size_in FROM Tablet e WHERE e.product_name < 'Triple-buffered 6thgeneration website';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."screen_size_in" AS "screen_size_in"
    FROM "relation_8" AS "source"
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."dimensions" AS "dimensions",
    "b0"."screen_size_in" AS "screen_size_in"
FROM "b0"
WHERE ("b0"."product_name" < 'Triple-buffered 6thgeneration website');

-- Q057 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.carrier_lock FROM Phone e WHERE e.carrier_lock > 'locked';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."carrier_lock" AS "carrier_lock"
    FROM "relation_11" AS "source"
)
SELECT DISTINCT 
    "b0"."carrier_lock" AS "carrier_lock"
FROM "b0"
WHERE ("b0"."carrier_lock" > 'locked');

-- Q058 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.quantity, e.accessory_type, e.dimensions FROM Accessory e WHERE e.base_price > 77;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."quantity" AS "quantity",
    "b0"."accessory_type" AS "accessory_type",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."base_price" > 77);

-- Q059 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.product_id FROM Tablet e WHERE e.product_id <= 11433232;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."tablet_id" AS "product_id"
    FROM "relation_8" AS "source"
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."product_id" <= 11433232);

-- Q060 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash, e.email FROM PrimeCustomer e WHERE e.email <= 'perezrodney@example.com';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash"
    FROM "relation_24" AS "source"
)
SELECT 
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."email" <= 'perezrodney@example.com');

-- Q061 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id, e.employee_no FROM Employee e WHERE e.password_hash < '97e1c0109b06eef14bad86e4c22d04498b32a4e2223c50cf53f8f814130bad76';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."employee_no" AS "employee_no",
        "source"."password_hash" AS "password_hash",
        "source"."employee_id" AS "user_id"
    FROM "relation_26" AS "source"
)
SELECT 
    "b0"."user_id" AS "user_id",
    "b0"."employee_no" AS "employee_no"
FROM "b0"
WHERE ("b0"."password_hash" < '97e1c0109b06eef14bad86e4c22d04498b32a4e2223c50cf53f8f814130bad76');

-- Q062 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.renewal_date, e.email FROM PrimeCustomer e WHERE e.loyalty_tier > 'bronze';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."renewal_date" AS "renewal_date",
        "source"."email" AS "email"
    FROM "relation_24" AS "source"
)
SELECT 
    "b0"."renewal_date" AS "renewal_date",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."loyalty_tier" > 'bronze');

-- Q063 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.product_name FROM Accessory e WHERE e.sku <= 'SKU-pcuo-72050177';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-pcuo-72050177');

-- Q064 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.quantity, e.form_factor, e.is_active FROM Desktop e WHERE e.base_price < 355;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."form_factor" AS "form_factor",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."desktop_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_6" AS "source"
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."quantity" AS "quantity",
    "b0"."form_factor" AS "form_factor",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."base_price" < 355);

-- Q065 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.dimensions, e.base_price FROM Accessory e WHERE e.base_price >= 121;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."dimensions" AS "dimensions",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."base_price" >= 121);

-- Q066 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash FROM Employee e WHERE e.employee_no >= 'EMP-39733584';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."employee_no" AS "employee_no",
        "source"."password_hash" AS "password_hash"
    FROM "relation_26" AS "source"
)
SELECT 
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."employee_no" >= 'EMP-39733584');

-- Q067 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active FROM MenClothing e WHERE e.is_active > 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."is_active" > 0);

-- Q068 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM MenClothing e WHERE e.product_name >= 'Compatible solution-oriented conglomeration';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_name" >= 'Compatible solution-oriented conglomeration');

-- Q069 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.license_type, e.sku, e.is_active, e.product_name FROM Software e WHERE e.is_active > 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku",
        "source"."license_type" AS "license_type"
    FROM "relation_21" AS "source"
)
SELECT 
    "b0"."license_type" AS "license_type",
    "b0"."sku" AS "sku",
    "b0"."is_active" AS "is_active",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."is_active" > 0);

-- Q070 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.size_system FROM MenClothing e WHERE e.base_price >= 79;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."base_price" AS "base_price"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."base_price" >= 79);

-- Q071 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.accessory_type, e.product_name, e.is_active, e.base_price FROM Accessory e WHERE e.sku <= 'SKU-fJiA-52653806';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."accessory_type" AS "accessory_type",
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-fJiA-52653806');

-- Q072 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.band_size, e.sku FROM Smartwatch e WHERE e.band_size < 'XL';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."sku" AS "sku",
        "source"."band_size" AS "band_size"
    FROM "relation_9" AS "source"
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."band_size" AS "band_size",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."band_size" < 'XL');

-- Q073 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.product_id, e.screen_size_in FROM Tablet e WHERE e.product_name < 'Phased systematic Graphic Interface';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."tablet_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."screen_size_in" AS "screen_size_in"
    FROM "relation_8" AS "source"
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id",
    "b0"."screen_size_in" AS "screen_size_in"
FROM "b0"
WHERE ("b0"."product_name" < 'Phased systematic Graphic Interface');

-- Q074 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.warranty_years FROM KitchenAppliance e WHERE e.is_active >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_years" AS "warranty_years",
        "source"."is_active" AS "is_active"
    FROM "relation_14" AS "source"
)
SELECT DISTINCT 
    "b0"."warranty_years" AS "warranty_years"
FROM "b0"
WHERE ("b0"."is_active" >= 1);

-- Q075 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active FROM Software e WHERE e.base_price > 40;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active"
    FROM "relation_21" AS "source"
)
SELECT 
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."base_price" > 40);

-- Q076 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.dimensions, e.base_price FROM Electronics e WHERE e.sku < 'SKU-uqeC-89650482';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_4" AS "source"
    UNION ALL
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_5" AS "source"
    UNION ALL
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_6" AS "source"
    UNION ALL
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_7" AS "source"
    UNION ALL
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_8" AS "source"
    UNION ALL
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_9" AS "source"
    UNION ALL
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_10" AS "source"
    UNION ALL
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_11" AS "source"
    UNION ALL
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."dimensions" AS "dimensions",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."sku" < 'SKU-uqeC-89650482');

-- Q077 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.product_name, e.dimensions, e.quantity FROM Clothing e WHERE e.product_name > 'Integrated empowering solution';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_16" AS "source"
    UNION ALL
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_17" AS "source"
    UNION ALL
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_18" AS "source"
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name",
    "b0"."dimensions" AS "dimensions",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."product_name" > 'Integrated empowering solution');

-- Q078 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active FROM Accessory e WHERE e.product_name >= 'Advanced 3rdgeneration task-force';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_name" >= 'Advanced 3rdgeneration task-force');

-- Q079 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.format, e.delivery_type, e.product_name FROM Media e WHERE e.base_price > 40;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."format" AS "format",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name"
    FROM "relation_20" AS "source"
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."format" AS "format",
    "b0"."delivery_type" AS "delivery_type",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."base_price" > 40);

-- Q080 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.is_active FROM Smartwatch e WHERE e.band_size > 'L';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."is_active" AS "is_active",
        "source"."band_size" AS "band_size"
    FROM "relation_9" AS "source"
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."band_size" > 'L');

-- Q081 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id FROM KitchenAppliance e WHERE e.dimensions <= 'medium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."kitchenappliance_id" AS "product_id"
    FROM "relation_14" AS "source"
)
SELECT 
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."dimensions" <= 'medium');

-- Q082 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.product_id FROM KitchenAppliance e WHERE e.product_id <= 13224232;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."kitchenappliance_id" AS "product_id"
    FROM "relation_14" AS "source"
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."product_id" <= 13224232);

-- Q083 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.quantity, e.is_active, e.base_price FROM Media e WHERE e.sku < 'SKU-vDVA-32710668';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_20" AS "source"
)
SELECT DISTINCT 
    "b0"."quantity" AS "quantity",
    "b0"."is_active" AS "is_active",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."sku" < 'SKU-vDVA-32710668');

-- Q084 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.format FROM Media e WHERE e.format <= 'music';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."format" AS "format",
        "source"."sku" AS "sku"
    FROM "relation_20" AS "source"
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."format" AS "format"
FROM "b0"
WHERE ("b0"."format" <= 'music');

-- Q085 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.is_active, e.sku FROM Software e WHERE e.product_id >= 16784796;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."software_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_21" AS "source"
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."is_active" AS "is_active",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."product_id" >= 16784796);

-- Q086 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions FROM Desktop e WHERE e.product_id > 9345322;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."desktop_id" AS "product_id"
    FROM "relation_6" AS "source"
)
SELECT 
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."product_id" > 9345322);

-- Q087 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.size_system FROM MenClothing e WHERE e.fit_type_men >= 'regular';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."fit_type_men" AS "fit_type_men",
        "source"."sku" AS "sku"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."fit_type_men" >= 'regular');

-- Q088 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.sku, e.product_id FROM MenClothing e WHERE e.base_price > 17;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."menclothing_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."sku" AS "sku",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."base_price" > 17);

-- Q089 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.company_name, e.email FROM BusinessCustomer e WHERE e.user_id >= 867793;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."company_name" AS "company_name",
        "source"."email" AS "email",
        "source"."businesscustomer_id" AS "user_id"
    FROM "relation_25" AS "source"
)
SELECT 
    "b0"."company_name" AS "company_name",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."user_id" >= 867793);

-- Q090 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id, e.loyalty_tier FROM PrimeCustomer e WHERE e.loyalty_tier < 'silver';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."primecustomer_id" AS "user_id"
    FROM "relation_24" AS "source"
)
SELECT 
    "b0"."user_id" AS "user_id",
    "b0"."loyalty_tier" AS "loyalty_tier"
FROM "b0"
WHERE ("b0"."loyalty_tier" < 'silver');

-- Q091 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.base_price FROM Desktop e WHERE e.ram_gb < 128;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ram_gb" AS "ram_gb",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active"
    FROM "relation_6" AS "source"
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."ram_gb" < 128);

-- Q092 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.sku, e.product_id FROM MenClothing e WHERE e.product_id < 15416832;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."menclothing_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."sku" AS "sku",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."product_id" < 15416832);

-- Q093 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.product_id, e.fit_type_men FROM MenClothing e WHERE e.product_name > 'Focused optimizing complexity';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."fit_type_men" AS "fit_type_men",
        "source"."is_active" AS "is_active",
        "source"."menclothing_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."product_id" AS "product_id",
    "b0"."fit_type_men" AS "fit_type_men"
FROM "b0"
WHERE ("b0"."product_name" > 'Focused optimizing complexity');

-- Q094 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM KitchenAppliance e WHERE e.is_active > 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_14" AS "source"
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."is_active" > 0);

-- Q095 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.warranty_months, e.product_name, e.accessory_type FROM Accessory e WHERE e.sku >= 'SKU-AYRN-67057161';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."warranty_months" AS "warranty_months",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_12" AS "source"
)
SELECT DISTINCT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."product_name" AS "product_name",
    "b0"."accessory_type" AS "accessory_type"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-AYRN-67057161');

-- Q096 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.band_size, e.sku FROM Smartwatch e WHERE e.product_name <= 'Re-contextualized clear-thinking utilization';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku",
        "source"."band_size" AS "band_size"
    FROM "relation_9" AS "source"
)
SELECT 
    "b0"."band_size" AS "band_size",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."product_name" <= 'Re-contextualized clear-thinking utilization');

-- Q097 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.loyalty_tier FROM BusinessCustomer e WHERE e.user_id >= 594890;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."businesscustomer_id" AS "user_id"
    FROM "relation_25" AS "source"
)
SELECT 
    "b0"."loyalty_tier" AS "loyalty_tier"
FROM "b0"
WHERE ("b0"."user_id" >= 594890);

-- Q098 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active FROM Tablet e WHERE e.screen_size_in > 8;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."screen_size_in" AS "screen_size_in"
    FROM "relation_8" AS "source"
)
SELECT 
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."screen_size_in" > 8);

-- Q099 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id FROM Apparel e WHERE e.product_name > 'Integrated transitional time-frame';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."apparel_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_15" AS "source"
    UNION ALL
    SELECT
        "source"."clothing_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_16" AS "source"
    UNION ALL
    SELECT
        "source"."menclothing_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_17" AS "source"
    UNION ALL
    SELECT
        "source"."womenclothing_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_18" AS "source"
    UNION ALL
    SELECT
        "source"."footwear_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_19" AS "source"
)
SELECT 
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."product_name" > 'Integrated transitional time-frame');

-- Q100 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.accessory_type, e.quantity, e.base_price, e.sku FROM Accessory e WHERE e.sku >= 'SKU-Zmjn-31499847';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."accessory_type" AS "accessory_type",
    "b0"."quantity" AS "quantity",
    "b0"."base_price" AS "base_price",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-Zmjn-31499847');

ROLLBACK;
