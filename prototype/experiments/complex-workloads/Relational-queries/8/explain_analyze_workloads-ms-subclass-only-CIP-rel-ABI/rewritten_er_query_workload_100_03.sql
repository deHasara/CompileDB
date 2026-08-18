\set ON_ERROR_STOP on
\pset pager off
-- CompileDB mapping-aware relational workload
-- Conceptual workload: example2_schema_driven_selectivity_100_w03
-- Mapping ID: f015fd00db116d7c19ae94a5f40a6e34250534220293ca53b7b6086b1499e981
-- Query shapes: 100
-- Executed statements: 100
BEGIN TRANSACTION READ ONLY;

-- Q001 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.is_active FROM Smartwatch e WHERE e.warranty_months < 24;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."warranty_months" < 24);

-- Q002 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id, e.loyalty_tier, e.company_name, e.email FROM BusinessCustomer e WHERE e.password_hash >= '678b6ccb82b391db70fd23ea09d1c0fd13d13a3265f86d186340fd69ad19be01';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."company_name" AS "company_name",
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."user_id" AS "user_id",
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."company_name" AS "company_name",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."password_hash" >= '678b6ccb82b391db70fd23ea09d1c0fd13d13a3265f86d186340fd69ad19be01');

-- Q003 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id FROM Media e WHERE e.format > 'ebook';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."format" AS "format",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."format" > 'ebook');

-- Q004 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.product_name, e.base_price FROM Software e WHERE e.is_active >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."product_name" AS "product_name",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."is_active" >= 1);

-- Q005 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.dimensions, e.product_name, e.accessory_type, e.base_price FROM Accessory e WHERE e.product_id > 12758995;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT DISTINCT 
    "b0"."dimensions" AS "dimensions",
    "b0"."product_name" AS "product_name",
    "b0"."accessory_type" AS "accessory_type",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."product_id" > 12758995);

-- Q006 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.email, e.user_id, e.password_hash, e.employee_no FROM Employee e WHERE e.password_hash <= 'e66f74c8a6880b886f1ee9249b0047e1be0d45e0a1ab418d97bf2ba7ebe4a717';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."employee_no" AS "employee_no",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('employee'))
)
SELECT 
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id",
    "b0"."password_hash" AS "password_hash",
    "b0"."employee_no" AS "employee_no"
FROM "b0"
WHERE ("b0"."password_hash" <= 'e66f74c8a6880b886f1ee9249b0047e1be0d45e0a1ab418d97bf2ba7ebe4a717');

-- Q007 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id FROM BusinessCustomer e WHERE e.loyalty_tier > 'bronze';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."loyalty_tier" > 'bronze');

-- Q008 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id FROM Employee e WHERE e.email > 'brianna57@example.com';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."email" AS "email",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('employee'))
)
SELECT 
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."email" > 'brianna57@example.com');

-- Q009 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.product_name, e.cpu, e.product_id FROM Laptop e WHERE e.sku <= 'SKU-epMc-83578933';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."product_name" AS "product_name",
    "b0"."cpu" AS "cpu",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-epMc-83578933');

-- Q010 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.quantity, e.delivery_type FROM Media e WHERE e.product_name < 'Phased 5thgeneration Internet solution';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."quantity" AS "quantity",
    "b0"."delivery_type" AS "delivery_type"
FROM "b0"
WHERE ("b0"."product_name" < 'Phased 5thgeneration Internet solution');

-- Q011 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months FROM Desktop e WHERE e.dimensions > 'large';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."dimensions" > 'large');

-- Q012 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.warranty_months, e.sku, e.base_price FROM Phone e WHERE e.product_id > 12088780;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."sku" AS "sku",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."product_id" > 12088780);

-- Q013 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.sku, e.is_active FROM Accessory e WHERE e.base_price > 77;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."sku" AS "sku",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."base_price" > 77);

-- Q014 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.base_price FROM Electronics e WHERE e.quantity > 22;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."quantity" > 22);

-- Q015 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.is_active, e.sole_material FROM Footwear e WHERE e.sole_material > 'EVA';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sole_material" AS "sole_material",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."is_active" AS "is_active",
    "b0"."sole_material" AS "sole_material"
FROM "b0"
WHERE ("b0"."sole_material" > 'EVA');

-- Q016 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.product_name, e.warranty_months, e.dimensions FROM Smartwatch e WHERE e.product_name > 'Integrated stable knowledge user';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."product_name" > 'Integrated stable knowledge user');

-- Q017 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.sensor_mp, e.sku, e.product_name FROM Camera e WHERE e.sku <= 'SKU-pcfH-16550496';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sensor_mp" AS "sensor_mp",
        "source"."warranty_months" AS "warranty_months",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."sensor_mp" AS "sensor_mp",
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-pcfH-16550496');

-- Q018 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.product_name, e.size_system FROM Footwear e WHERE e.size_system < 'alpha';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."product_name" AS "product_name",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."size_system" < 'alpha');

-- Q019 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.dimensions, e.base_price, e.size_system FROM WomenClothing e WHERE e.dimensions >= 'medium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT DISTINCT 
    "b0"."dimensions" AS "dimensions",
    "b0"."base_price" AS "base_price",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."dimensions" >= 'medium');

-- Q020 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sensor_mp FROM Camera e WHERE e.product_id > 11996864;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sensor_mp" AS "sensor_mp",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."sensor_mp" AS "sensor_mp"
FROM "b0"
WHERE ("b0"."product_id" > 11996864);

-- Q021 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.product_id FROM Software e WHERE e.delivery_type > 'account_activation';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."delivery_type" > 'account_activation');

-- Q022 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.is_active, e.quantity, e.dimensions FROM WomenClothing e WHERE e.product_name > 'Distributed homogeneous strategy';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."is_active" AS "is_active",
    "b0"."quantity" AS "quantity",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."product_name" > 'Distributed homogeneous strategy');

-- Q023 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.accessory_type, e.base_price, e.warranty_months, e.is_active FROM Accessory e WHERE e.quantity >= 13;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT DISTINCT 
    "b0"."accessory_type" AS "accessory_type",
    "b0"."base_price" AS "base_price",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."quantity" >= 13);

-- Q024 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.fit_type_men, e.base_price FROM MenClothing e WHERE e.is_active > 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."fit_type_men" AS "fit_type_men",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."fit_type_men" AS "fit_type_men",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."is_active" > 0);

-- Q025 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.material, e.product_id FROM MenClothing e WHERE e.dimensions < 'oversize';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."material" AS "material",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT DISTINCT 
    "b0"."material" AS "material",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."dimensions" < 'oversize');

-- Q026 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sku, e.is_active FROM Desktop e WHERE e.product_name < 'Persistent background budgetary management';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT DISTINCT 
    "b0"."sku" AS "sku",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_name" < 'Persistent background budgetary management');

-- Q027 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.screen_size_in, e.sku FROM Tablet e WHERE e.screen_size_in < 13;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku",
        "source"."screen_size_in" AS "screen_size_in"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."screen_size_in" AS "screen_size_in",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."screen_size_in" < 13);

-- Q028 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.is_active, e.base_price FROM Phone e WHERE e.product_name <= 'Object-based bandwidth-monitored contingency';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."is_active" AS "is_active",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."product_name" <= 'Object-based bandwidth-monitored contingency');

-- Q029 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions FROM Tablet e WHERE e.sku <= 'SKU-zYNL-95065719';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-zYNL-95065719');

-- Q030 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash FROM Customer e WHERE e.password_hash < '7f4a1dbc472fb43a642380ef05ffa5bbeb761b16939b13ef9d5abfba248e46b3';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."password_hash" AS "password_hash"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."password_hash" < '7f4a1dbc472fb43a642380ef05ffa5bbeb761b16939b13ef9d5abfba248e46b3');

-- Q031 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_years FROM KitchenAppliance e WHERE e.warranty_years < 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_years" AS "warranty_years"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."warranty_years" AS "warranty_years"
FROM "b0"
WHERE ("b0"."warranty_years" < 3);

-- Q032 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.form_factor, e.cpu, e.base_price, e.product_name FROM Desktop e WHERE e.product_id < 11019532;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."form_factor" AS "form_factor",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."form_factor" AS "form_factor",
    "b0"."cpu" AS "cpu",
    "b0"."base_price" AS "base_price",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_id" < 11019532);

-- Q033 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.product_name, e.dimensions, e.warranty_months FROM Phone e WHERE e.base_price < 885;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name",
    "b0"."dimensions" AS "dimensions",
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."base_price" < 885);

-- Q034 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.base_price, e.sku, e.form_factor FROM Desktop e WHERE e.sku < 'SKU-uqSb-43331552';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."form_factor" AS "form_factor",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."base_price" AS "base_price",
    "b0"."sku" AS "sku",
    "b0"."form_factor" AS "form_factor"
FROM "b0"
WHERE ("b0"."sku" < 'SKU-uqSb-43331552');

-- Q035 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.base_price, e.quantity, e.product_id FROM Phone e WHERE e.product_id <= 12691279;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."base_price" AS "base_price",
    "b0"."quantity" AS "quantity",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."product_id" <= 12691279);

-- Q036 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM MenClothing e WHERE e.size_system < 'alpha';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."size_system" < 'alpha');

-- Q037 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash, e.user_id, e.company_name FROM BusinessCustomer e WHERE e.company_name >= 'Alexander-Everett';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."company_name" AS "company_name",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."password_hash" AS "password_hash",
    "b0"."user_id" AS "user_id",
    "b0"."company_name" AS "company_name"
FROM "b0"
WHERE ("b0"."company_name" >= 'Alexander-Everett');

-- Q038 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.size_system, e.base_price FROM Footwear e WHERE e.sole_material >= 'rubber';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."sole_material" AS "sole_material",
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."size_system" AS "size_system",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."sole_material" >= 'rubber');

-- Q039 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.battery_wh, e.base_price, e.cpu, e.is_active FROM Laptop e WHERE e.sku <= 'SKU-ugrP-78202470';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."battery_wh" AS "battery_wh",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT 
    "b0"."battery_wh" AS "battery_wh",
    "b0"."base_price" AS "base_price",
    "b0"."cpu" AS "cpu",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-ugrP-78202470');

-- Q040 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.loyalty_tier, e.password_hash, e.email FROM Customer e WHERE e.email > 'davidanderson@example.org';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."email" > 'davidanderson@example.org');

-- Q041 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sku FROM Software e WHERE e.delivery_type < 'stream';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT DISTINCT 
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."delivery_type" < 'stream');

-- Q042 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.sku, e.product_name, e.size_system FROM WomenClothing e WHERE e.material >= 'cotton';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."material" AS "material",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."material" >= 'cotton');

-- Q043 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.base_price, e.product_name, e.sku FROM KitchenAppliance e WHERE e.quantity >= 12;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."base_price" AS "base_price",
    "b0"."product_name" AS "product_name",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."quantity" >= 12);

-- Q044 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system, e.product_id FROM WomenClothing e WHERE e.size_system > 'EU';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."size_system" AS "size_system",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."size_system" > 'EU');

-- Q045 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.email, e.user_id, e.company_name FROM BusinessCustomer e WHERE e.user_id >= 686882;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."company_name" AS "company_name",
        "source"."email" AS "email",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id",
    "b0"."company_name" AS "company_name"
FROM "b0"
WHERE ("b0"."user_id" >= 686882);

-- Q046 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.base_price FROM Software e WHERE e.sku >= 'SKU-AZla-96163993';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-AZla-96163993');

-- Q047 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price FROM MenClothing e WHERE e.material >= 'cotton';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."material" AS "material",
        "source"."base_price" AS "base_price"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."material" >= 'cotton');

-- Q048 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity FROM Software e WHERE e.sku < 'SKU-ZPWD-28766382';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."sku" < 'SKU-ZPWD-28766382');

-- Q049 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.user_id, e.employee_no, e.password_hash FROM Employee e WHERE e.employee_no > 'EMP-00997221';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."employee_no" AS "employee_no",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('employee'))
)
SELECT DISTINCT 
    "b0"."user_id" AS "user_id",
    "b0"."employee_no" AS "employee_no",
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."employee_no" > 'EMP-00997221');

-- Q050 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Tablet e WHERE e.warranty_months < 36;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."warranty_months" < 36);

-- Q051 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.battery_wh, e.product_id FROM Laptop e WHERE e.quantity > 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."battery_wh" AS "battery_wh",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."battery_wh" AS "battery_wh",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."quantity" > 3);

-- Q052 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.product_name, e.is_active FROM PhysicalProduct e WHERE e.product_id >= 7911105;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_id" >= 7911105);

-- Q053 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.sku, e.accessory_type FROM Accessory e WHERE e.warranty_months >= 12;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."warranty_months" AS "warranty_months",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."sku" AS "sku",
    "b0"."accessory_type" AS "accessory_type"
FROM "b0"
WHERE ("b0"."warranty_months" >= 12);

-- Q054 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system, e.product_name, e.is_active FROM Footwear e WHERE e.quantity < 245;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."size_system" AS "size_system",
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."quantity" < 245);

-- Q055 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sole_material, e.sku, e.product_name FROM Footwear e WHERE e.dimensions <= 'medium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sole_material" AS "sole_material",
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."sole_material" AS "sole_material",
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."dimensions" <= 'medium');

-- Q056 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.quantity, e.sku, e.is_active FROM Tablet e WHERE e.base_price > 40;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."quantity" AS "quantity",
    "b0"."sku" AS "sku",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."base_price" > 40);

-- Q057 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.sku, e.base_price, e.size_system FROM Footwear e WHERE e.size_system <= 'US';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."sku" AS "sku",
    "b0"."base_price" AS "base_price",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."size_system" <= 'US');

-- Q058 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.format, e.product_id, e.quantity FROM Media e WHERE e.product_id < 16573608;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."format" AS "format",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."format" AS "format",
    "b0"."product_id" AS "product_id",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."product_id" < 16573608);

-- Q059 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions FROM Phone e WHERE e.warranty_months < 36;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."warranty_months" < 36);

-- Q060 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system FROM MenClothing e WHERE e.quantity >= 17;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."quantity" >= 17);

-- Q061 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.quantity, e.base_price, e.product_id FROM Footwear e WHERE e.quantity <= 29;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."quantity" AS "quantity",
    "b0"."base_price" AS "base_price",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."quantity" <= 29);

-- Q062 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id, e.password_hash, e.email, e.loyalty_tier FROM BusinessCustomer e WHERE e.user_id >= 867793;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."user_id" AS "user_id",
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email",
    "b0"."loyalty_tier" AS "loyalty_tier"
FROM "b0"
WHERE ("b0"."user_id" >= 867793);

-- Q063 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.quantity, e.form_factor FROM Desktop e WHERE e.quantity <= 256;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."form_factor" AS "form_factor",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT DISTINCT 
    "b0"."quantity" AS "quantity",
    "b0"."form_factor" AS "form_factor"
FROM "b0"
WHERE ("b0"."quantity" <= 256);

-- Q064 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.quantity, e.base_price, e.sku FROM KitchenAppliance e WHERE e.quantity >= 4;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."quantity" AS "quantity",
    "b0"."base_price" AS "base_price",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."quantity" >= 4);

-- Q065 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.ram_gb, e.is_active FROM Laptop e WHERE e.cpu < 'Ryzen 7';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."ram_gb" AS "ram_gb",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."ram_gb" AS "ram_gb",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."cpu" < 'Ryzen 7');

-- Q066 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.ram_gb FROM Computer e WHERE e.cpu > 'Core i5';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."ram_gb" AS "ram_gb",
        "source"."is_active" AS "is_active"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('computer', 'desktop', 'laptop'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."ram_gb" AS "ram_gb"
FROM "b0"
WHERE ("b0"."cpu" > 'Core i5');

-- Q067 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.warranty_months, e.base_price FROM Camera e WHERE e.sensor_mp < 48;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sensor_mp" AS "sensor_mp",
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."sensor_mp" < 48);

-- Q068 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.format, e.delivery_type FROM Media e WHERE e.sku >= 'SKU-VGKr-25365355';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."format" AS "format",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."format" AS "format",
    "b0"."delivery_type" AS "delivery_type"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-VGKr-25365355');

-- Q069 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.base_price FROM Camera e WHERE e.product_id <= 11996864;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT DISTINCT 
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."product_id" <= 11996864);

-- Q070 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.dimensions, e.product_id, e.warranty_years FROM KitchenAppliance e WHERE e.product_name > 'Networked systemic installation';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_years" AS "warranty_years",
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id",
    "b0"."warranty_years" AS "warranty_years"
FROM "b0"
WHERE ("b0"."product_name" > 'Networked systemic installation');

-- Q071 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.dimensions, e.energy_rating FROM Appliance e WHERE e.product_name > 'Integrated intermediate paradigm';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."energy_rating" AS "energy_rating",
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('appliance', 'kitchenappliance'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."dimensions" AS "dimensions",
    "b0"."energy_rating" AS "energy_rating"
FROM "b0"
WHERE ("b0"."product_name" > 'Integrated intermediate paradigm');

-- Q072 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.base_price, e.warranty_months, e.ram_gb, e.is_active FROM Laptop e WHERE e.is_active >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ram_gb" AS "ram_gb",
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT DISTINCT 
    "b0"."base_price" AS "base_price",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."ram_gb" AS "ram_gb",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."is_active" >= 1);

-- Q073 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.dimensions FROM KitchenAppliance e WHERE e.dimensions >= 'medium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT DISTINCT 
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."dimensions" >= 'medium');

-- Q074 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_years FROM KitchenAppliance e WHERE e.product_name >= 'Focused static adapter';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_years" AS "warranty_years",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."warranty_years" AS "warranty_years"
FROM "b0"
WHERE ("b0"."product_name" >= 'Focused static adapter');

-- Q075 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months FROM Desktop e WHERE e.sku >= 'SKU-aPmG-61191428';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-aPmG-61191428');

-- Q076 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Phone e WHERE e.carrier_lock > 'locked';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."carrier_lock" AS "carrier_lock",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."carrier_lock" > 'locked');

-- Q077 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.is_active, e.warranty_months, e.quantity FROM Camera e WHERE e.product_name > 'Networked tertiary moratorium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."is_active" AS "is_active",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."product_name" > 'Networked tertiary moratorium');

-- Q078 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price FROM Camera e WHERE e.sensor_mp < 32;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sensor_mp" AS "sensor_mp",
        "source"."base_price" AS "base_price"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."sensor_mp" < 32);

-- Q079 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.form_factor FROM Desktop e WHERE e.form_factor >= 'mini';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."form_factor" AS "form_factor"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."form_factor" AS "form_factor"
FROM "b0"
WHERE ("b0"."form_factor" >= 'mini');

-- Q080 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.product_name, e.product_id FROM Desktop e WHERE e.product_id < 10832198;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."product_name" AS "product_name",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."product_id" < 10832198);

-- Q081 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.warranty_months, e.sku, e.quantity, e.product_id FROM Phone e WHERE e.base_price > 39;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT DISTINCT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."sku" AS "sku",
    "b0"."quantity" AS "quantity",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."base_price" > 39);

-- Q082 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system, e.product_name, e.sku, e.material FROM MenClothing e WHERE e.product_name >= 'Focused optimizing time-frame';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."material" AS "material",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."size_system" AS "size_system",
    "b0"."product_name" AS "product_name",
    "b0"."sku" AS "sku",
    "b0"."material" AS "material"
FROM "b0"
WHERE ("b0"."product_name" >= 'Focused optimizing time-frame');

-- Q083 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.sku, e.base_price, e.warranty_months FROM Smartwatch e WHERE e.base_price >= 60;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."sku" AS "sku",
    "b0"."base_price" AS "base_price",
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."base_price" >= 60);

-- Q084 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.form_factor, e.product_name FROM Desktop e WHERE e.quantity < 40;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."form_factor" AS "form_factor",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT DISTINCT 
    "b0"."form_factor" AS "form_factor",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."quantity" < 40);

-- Q085 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sensor_mp FROM Camera e WHERE e.product_name > 'Integrated bottom-line utilization';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sensor_mp" AS "sensor_mp",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."sensor_mp" AS "sensor_mp"
FROM "b0"
WHERE ("b0"."product_name" > 'Integrated bottom-line utilization');

-- Q086 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.dimensions FROM PhysicalProduct e WHERE e.sku < 'SKU-kqLx-85719614';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."sku" < 'SKU-kqLx-85719614');

-- Q087 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.warranty_years FROM KitchenAppliance e WHERE e.dimensions < 'small';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_years" AS "warranty_years",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."warranty_years" AS "warranty_years"
FROM "b0"
WHERE ("b0"."dimensions" < 'small');

-- Q088 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.quantity, e.base_price FROM Laptop e WHERE e.base_price > 96;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."quantity" AS "quantity",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."base_price" > 96);

-- Q089 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.delivery_type FROM Software e WHERE e.license_type < 'subscription';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."quantity" AS "quantity",
        "source"."license_type" AS "license_type"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."delivery_type" AS "delivery_type"
FROM "b0"
WHERE ("b0"."license_type" < 'subscription');

-- Q090 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions FROM WomenClothing e WHERE e.product_id < 15695844;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."product_id" < 15695844);

-- Q091 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.is_active, e.cpu, e.product_name FROM Laptop e WHERE e.product_id >= 11232191;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."warranty_months" AS "warranty_months",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."is_active" AS "is_active",
    "b0"."cpu" AS "cpu",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_id" >= 11232191);

-- Q092 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.material, e.product_id, e.base_price, e.product_name FROM WomenClothing e WHERE e.material < 'polyester';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."material" AS "material",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."material" AS "material",
    "b0"."product_id" AS "product_id",
    "b0"."base_price" AS "base_price",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."material" < 'polyester');

-- Q093 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.email, e.company_name, e.user_id FROM BusinessCustomer e WHERE e.loyalty_tier > 'bronze';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."company_name" AS "company_name",
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."email" AS "email",
    "b0"."company_name" AS "company_name",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."loyalty_tier" > 'bronze');

-- Q094 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id FROM PrimeCustomer e WHERE e.email < 'schoi@example.net';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."email" AS "email",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT 
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."email" < 'schoi@example.net');

-- Q095 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.product_id, e.product_name FROM Smartwatch e WHERE e.is_active >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."is_active" >= 1);

-- Q096 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.is_active FROM Phone e WHERE e.base_price >= 40;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."base_price" >= 40);

-- Q097 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.email FROM Employee e WHERE e.employee_no <= 'EMP-99018214';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."employee_no" AS "employee_no",
        "source"."email" AS "email"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('employee'))
)
SELECT 
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."employee_no" <= 'EMP-99018214');

-- Q098 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.loyalty_tier FROM BusinessCustomer e WHERE e.password_hash < 'e65d9048613e155e369a59d7b8fdacab5e397b1127e8bdab47d3aaf8ef132502';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."password_hash" AS "password_hash"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."loyalty_tier" AS "loyalty_tier"
FROM "b0"
WHERE ("b0"."password_hash" < 'e65d9048613e155e369a59d7b8fdacab5e397b1127e8bdab47d3aaf8ef132502');

-- Q099 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions FROM WomenClothing e WHERE e.product_id >= 15614838;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."product_id" >= 15614838);

-- Q100 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.product_id, e.product_name FROM Accessory e WHERE e.dimensions < 'small';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."product_id" AS "product_id",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."dimensions" < 'small');

ROLLBACK;
