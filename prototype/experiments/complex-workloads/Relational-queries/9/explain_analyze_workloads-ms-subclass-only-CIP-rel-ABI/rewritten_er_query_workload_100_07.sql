\set ON_ERROR_STOP on
\pset pager off
-- CompileDB mapping-aware relational workload
-- Conceptual workload: example2_schema_driven_selectivity_100_w07
-- Mapping ID: f015fd00db116d7c19ae94a5f40a6e34250534220293ca53b7b6086b1499e981
-- Query shapes: 100
-- Executed statements: 100
BEGIN TRANSACTION READ ONLY;

-- Q001 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.base_price, e.carrier_lock FROM Phone e WHERE e.quantity < 247;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."carrier_lock" AS "carrier_lock",
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT DISTINCT 
    "b0"."base_price" AS "base_price",
    "b0"."carrier_lock" AS "carrier_lock"
FROM "b0"
WHERE ("b0"."quantity" < 247);

-- Q002 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity FROM Phone e WHERE e.warranty_months >= 12;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."warranty_months" >= 12);

-- Q003 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.warranty_months, e.base_price FROM Accessory e WHERE e.warranty_months <= 12;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT DISTINCT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."warranty_months" <= 12);

-- Q004 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity FROM WomenClothing e WHERE e.fit_type_women <= 'regular';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."fit_type_women" AS "fit_type_women"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."fit_type_women" <= 'regular');

-- Q005 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.dimensions, e.sku FROM Desktop e WHERE e.cpu > 'Apple M3';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."dimensions" AS "dimensions",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT DISTINCT 
    "b0"."dimensions" AS "dimensions",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."cpu" > 'Apple M3');

-- Q006 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.is_active FROM MenClothing e WHERE e.sku >= 'SKU-Pndh-97504895';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-Pndh-97504895');

-- Q007 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.product_id, e.dimensions, e.product_name FROM WomenClothing e WHERE e.dimensions < 'small';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."product_id" AS "product_id",
    "b0"."dimensions" AS "dimensions",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."dimensions" < 'small');

-- Q008 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.dimensions, e.is_active, e.product_id FROM Tablet e WHERE e.warranty_months > 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT DISTINCT 
    "b0"."dimensions" AS "dimensions",
    "b0"."is_active" AS "is_active",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."warranty_months" > 0);

-- Q009 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.quantity, e.carrier_lock FROM Phone e WHERE e.sku >= 'SKU-ZoyC-08250395';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."carrier_lock" AS "carrier_lock",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."quantity" AS "quantity",
    "b0"."carrier_lock" AS "carrier_lock"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-ZoyC-08250395');

-- Q010 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sole_material FROM Footwear e WHERE e.sku >= 'SKU-PXxJ-02988886';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sole_material" AS "sole_material",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."sole_material" AS "sole_material"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-PXxJ-02988886');

-- Q011 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.sensor_mp, e.product_id, e.dimensions FROM Camera e WHERE e.warranty_months >= 12;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sensor_mp" AS "sensor_mp",
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."sensor_mp" AS "sensor_mp",
    "b0"."product_id" AS "product_id",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."warranty_months" >= 12);

-- Q012 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.ram_gb, e.warranty_months, e.sku FROM Desktop e WHERE e.product_name < 'Secured impactful policy';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ram_gb" AS "ram_gb",
        "source"."warranty_months" AS "warranty_months",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."ram_gb" AS "ram_gb",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."product_name" < 'Secured impactful policy');

-- Q013 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.sku, e.warranty_months, e.product_id FROM Tablet e WHERE e.sku >= 'SKU-KUIu-03771611';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."sku" AS "sku",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-KUIu-03771611');

-- Q014 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id, e.employee_no, e.email, e.password_hash FROM Employee e WHERE e.user_id < 1427893;
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
    "b0"."user_id" AS "user_id",
    "b0"."employee_no" AS "employee_no",
    "b0"."email" AS "email",
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."user_id" < 1427893);

-- Q015 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sku, e.quantity FROM KitchenAppliance e WHERE e.base_price > 39;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT DISTINCT 
    "b0"."sku" AS "sku",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."base_price" > 39);

-- Q016 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system, e.is_active, e.fit_type_women FROM WomenClothing e WHERE e.is_active >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."is_active" AS "is_active",
        "source"."fit_type_women" AS "fit_type_women"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."size_system" AS "size_system",
    "b0"."is_active" AS "is_active",
    "b0"."fit_type_women" AS "fit_type_women"
FROM "b0"
WHERE ("b0"."is_active" >= 1);

-- Q017 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.warranty_months, e.is_active, e.product_name, e.product_id FROM Accessory e WHERE e.warranty_months <= 12;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT DISTINCT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."is_active" AS "is_active",
    "b0"."product_name" AS "product_name",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."warranty_months" <= 12);

-- Q018 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Accessory e WHERE e.warranty_months < 24;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."warranty_months" < 24);

-- Q019 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.sku FROM WomenClothing e WHERE e.base_price < 117;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."base_price" < 117);

-- Q020 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.product_name, e.quantity, e.is_active, e.dimensions FROM Laptop e WHERE e.cpu > 'Core i5';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT DISTINCT 
    "b0"."product_name" AS "product_name",
    "b0"."quantity" AS "quantity",
    "b0"."is_active" AS "is_active",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."cpu" > 'Core i5');

-- Q021 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.product_name, e.format, e.delivery_type FROM Media e WHERE e.base_price <= 146;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."format" AS "format",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."product_name" AS "product_name",
    "b0"."format" AS "format",
    "b0"."delivery_type" AS "delivery_type"
FROM "b0"
WHERE ("b0"."base_price" <= 146);

-- Q022 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity FROM Footwear e WHERE e.size_system > 'UK';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."size_system" > 'UK');

-- Q023 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.product_id FROM Clothing e WHERE e.quantity > 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('clothing', 'menclothing', 'womenclothing'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."quantity" > 3);

-- Q024 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.material, e.quantity, e.base_price FROM Clothing e WHERE e.sku <= 'SKU-vDvq-61048724';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."material" AS "material",
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('clothing', 'menclothing', 'womenclothing'))
)
SELECT 
    "b0"."material" AS "material",
    "b0"."quantity" AS "quantity",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-vDvq-61048724');

-- Q025 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id, e.company_name, e.password_hash, e.loyalty_tier FROM BusinessCustomer e WHERE e.company_name <= 'Wright-Solis';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."company_name" AS "company_name",
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."user_id" AS "user_id",
    "b0"."company_name" AS "company_name",
    "b0"."password_hash" AS "password_hash",
    "b0"."loyalty_tier" AS "loyalty_tier"
FROM "b0"
WHERE ("b0"."company_name" <= 'Wright-Solis');

-- Q026 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sku, e.size_system, e.is_active, e.fit_type_women FROM WomenClothing e WHERE e.material <= 'denim';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."material" AS "material",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku",
        "source"."fit_type_women" AS "fit_type_women"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT DISTINCT 
    "b0"."sku" AS "sku",
    "b0"."size_system" AS "size_system",
    "b0"."is_active" AS "is_active",
    "b0"."fit_type_women" AS "fit_type_women"
FROM "b0"
WHERE ("b0"."material" <= 'denim');

-- Q027 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.accessory_type FROM Accessory e WHERE e.sku <= 'SKU-Zmip-90105888';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."accessory_type" AS "accessory_type"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-Zmip-90105888');

-- Q028 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.quantity, e.sku FROM Software e WHERE e.license_type > 'open_source';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku",
        "source"."license_type" AS "license_type"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."quantity" AS "quantity",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."license_type" > 'open_source');

-- Q029 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id FROM Software e WHERE e.quantity < 23;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."quantity" < 23);

-- Q030 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.band_size, e.warranty_months, e.sku FROM Smartwatch e WHERE e.band_size < 'S';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."sku" AS "sku",
        "source"."band_size" AS "band_size"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."band_size" AS "band_size",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."band_size" < 'S');

-- Q031 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.sku FROM Appliance e WHERE e.quantity <= 29;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('appliance', 'kitchenappliance'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."quantity" <= 29);

-- Q032 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sku, e.is_active, e.quantity FROM Media e WHERE e.delivery_type >= 'license_key';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT DISTINCT 
    "b0"."sku" AS "sku",
    "b0"."is_active" AS "is_active",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."delivery_type" >= 'license_key');

-- Q033 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku FROM Appliance e WHERE e.sku > 'SKU-ZwTg-41836845';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('appliance', 'kitchenappliance'))
)
SELECT 
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."sku" > 'SKU-ZwTg-41836845');

-- Q034 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.delivery_type FROM Software e WHERE e.product_id >= 16787791;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."delivery_type" AS "delivery_type"
FROM "b0"
WHERE ("b0"."product_id" >= 16787791);

-- Q035 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.base_price, e.dimensions, e.product_id FROM Tablet e WHERE e.product_name < 'Triple-buffered 6thgeneration website';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."base_price" AS "base_price",
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."product_name" < 'Triple-buffered 6thgeneration website');

-- Q036 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price FROM Media e WHERE e.quantity < 30;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."quantity" < 30);

-- Q037 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.warranty_months, e.accessory_type FROM Accessory e WHERE e.product_id < 12844466;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."warranty_months" AS "warranty_months",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."accessory_type" AS "accessory_type"
FROM "b0"
WHERE ("b0"."product_id" < 12844466);

-- Q038 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.form_factor, e.ram_gb, e.dimensions FROM Desktop e WHERE e.sku > 'SKU-aPlU-59647828';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ram_gb" AS "ram_gb",
        "source"."form_factor" AS "form_factor",
        "source"."dimensions" AS "dimensions",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."form_factor" AS "form_factor",
    "b0"."ram_gb" AS "ram_gb",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."sku" > 'SKU-aPlU-59647828');

-- Q039 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.employee_no, e.password_hash, e.email FROM Employee e WHERE e.email <= 'klindsey@example.org';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."employee_no" AS "employee_no",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('employee'))
)
SELECT 
    "b0"."employee_no" AS "employee_no",
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."email" <= 'klindsey@example.org');

-- Q040 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.product_name FROM Camera e WHERE e.sku < 'SKU-uihl-64441565';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."sku" < 'SKU-uihl-64441565');

-- Q041 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.sku, e.product_name, e.size_system FROM Footwear e WHERE e.product_name <= 'Vision-oriented zero tolerance contingency';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."product_name" <= 'Vision-oriented zero tolerance contingency');

-- Q042 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.email, e.user_id FROM PrimeCustomer e WHERE e.loyalty_tier < 'silver';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT 
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."loyalty_tier" < 'silver');

-- Q043 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sku, e.ram_gb, e.form_factor FROM Desktop e WHERE e.sku > 'SKU-AbPG-06927745';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ram_gb" AS "ram_gb",
        "source"."form_factor" AS "form_factor",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT DISTINCT 
    "b0"."sku" AS "sku",
    "b0"."ram_gb" AS "ram_gb",
    "b0"."form_factor" AS "form_factor"
FROM "b0"
WHERE ("b0"."sku" > 'SKU-AbPG-06927745');

-- Q044 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.fit_type_women, e.base_price, e.size_system FROM WomenClothing e WHERE e.base_price < 182;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."base_price" AS "base_price",
        "source"."fit_type_women" AS "fit_type_women"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."fit_type_women" AS "fit_type_women",
    "b0"."base_price" AS "base_price",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."base_price" < 182);

-- Q045 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.quantity, e.product_name, e.warranty_months FROM Smartwatch e WHERE e.sku <= 'SKU-eqJB-90041693';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT DISTINCT 
    "b0"."quantity" AS "quantity",
    "b0"."product_name" AS "product_name",
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-eqJB-90041693');

-- Q046 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Phone e WHERE e.is_active > 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."is_active" > 0);

-- Q047 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.product_id, e.warranty_years FROM KitchenAppliance e WHERE e.energy_rating <= 'A++';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."energy_rating" AS "energy_rating",
        "source"."warranty_years" AS "warranty_years",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT DISTINCT 
    "b0"."product_id" AS "product_id",
    "b0"."warranty_years" AS "warranty_years"
FROM "b0"
WHERE ("b0"."energy_rating" <= 'A++');

-- Q048 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.base_price FROM Accessory e WHERE e.sku <= 'SKU-kSyY-73027379';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT DISTINCT 
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-kSyY-73027379');

-- Q049 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.is_active FROM Desktop e WHERE e.product_id >= 9901239;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_id" >= 9901239);

-- Q050 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.screen_size_in, e.base_price FROM Tablet e WHERE e.quantity <= 29;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity",
        "source"."screen_size_in" AS "screen_size_in"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."screen_size_in" AS "screen_size_in",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."quantity" <= 29);

-- Q051 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash FROM BusinessCustomer e WHERE e.loyalty_tier < 'silver';
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
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."loyalty_tier" < 'silver');

-- Q052 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.product_id FROM Desktop e WHERE e.sku >= 'SKU-KZxx-36843123';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-KZxx-36843123');

-- Q053 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active FROM MenClothing e WHERE e.base_price > 97;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."base_price" > 97);

-- Q054 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active FROM PhysicalProduct e WHERE e.base_price < 359;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."base_price" < 359);

-- Q055 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active FROM Footwear e WHERE e.size_system > 'EU';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."is_active" AS "is_active"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."size_system" > 'EU');

-- Q056 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_years, e.product_id, e.quantity FROM KitchenAppliance e WHERE e.product_name > 'Networked systemic installation';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_years" AS "warranty_years",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."warranty_years" AS "warranty_years",
    "b0"."product_id" AS "product_id",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."product_name" > 'Networked systemic installation');

-- Q057 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.dimensions, e.sole_material, e.product_id FROM Footwear e WHERE e.sku < 'SKU-pHKc-51129828';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sole_material" AS "sole_material",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT DISTINCT 
    "b0"."dimensions" AS "dimensions",
    "b0"."sole_material" AS "sole_material",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."sku" < 'SKU-pHKc-51129828');

-- Q058 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.quantity, e.product_id, e.base_price FROM Footwear e WHERE e.size_system <= 'US';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."quantity" AS "quantity",
    "b0"."product_id" AS "product_id",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."size_system" <= 'US');

-- Q059 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.delivery_type, e.product_name FROM Media e WHERE e.product_name < 'Visionary asymmetric capacity';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."delivery_type" AS "delivery_type",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_name" < 'Visionary asymmetric capacity');

-- Q060 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.sku FROM Media e WHERE e.product_id < 16573608;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."product_id" < 16573608);

-- Q061 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash, e.user_id, e.employee_no, e.email FROM Employee e WHERE e.email < 'michael45@example.com';
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
    "b0"."password_hash" AS "password_hash",
    "b0"."user_id" AS "user_id",
    "b0"."employee_no" AS "employee_no",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."email" < 'michael45@example.com');

-- Q062 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Accessory e WHERE e.sku < 'SKU-Zmjn-31499847';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."sku" < 'SKU-Zmjn-31499847');

-- Q063 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku FROM Camera e WHERE e.dimensions <= 'medium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."dimensions" <= 'medium');

-- Q064 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.email, e.employee_no, e.user_id, e.password_hash FROM Employee e WHERE e.password_hash <= 'cd40300b17a335c922ab953f264cddbf9905e451e22d054954aa833fda238aa3';
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
    "b0"."employee_no" AS "employee_no",
    "b0"."user_id" AS "user_id",
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."password_hash" <= 'cd40300b17a335c922ab953f264cddbf9905e451e22d054954aa833fda238aa3');

-- Q065 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active FROM Media e WHERE e.product_id > 15835368;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_id" > 15835368);

-- Q066 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.is_active FROM KitchenAppliance e WHERE e.sku > 'SKU-FBrb-04215167';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."sku" > 'SKU-FBrb-04215167');

-- Q067 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.product_id, e.dimensions FROM Smartwatch e WHERE e.base_price < 148;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."product_id" AS "product_id",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."base_price" < 148);

-- Q068 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.base_price, e.energy_rating FROM KitchenAppliance e WHERE e.product_id < 13124279;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."energy_rating" AS "energy_rating",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."base_price" AS "base_price",
    "b0"."energy_rating" AS "energy_rating"
FROM "b0"
WHERE ("b0"."product_id" < 13124279);

-- Q069 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Tablet e WHERE e.sku <= 'SKU-phiT-43841200';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-phiT-43841200');

-- Q070 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.email, e.password_hash, e.user_id, e.company_name FROM BusinessCustomer e WHERE e.user_id < 1225492;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."company_name" AS "company_name",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."email" AS "email",
    "b0"."password_hash" AS "password_hash",
    "b0"."user_id" AS "user_id",
    "b0"."company_name" AS "company_name"
FROM "b0"
WHERE ("b0"."user_id" < 1225492);

-- Q071 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.product_id, e.warranty_years FROM KitchenAppliance e WHERE e.product_id >= 13016288;
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
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id",
    "b0"."warranty_years" AS "warranty_years"
FROM "b0"
WHERE ("b0"."product_id" >= 13016288);

-- Q072 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.base_price, e.sku, e.quantity, e.accessory_type FROM Accessory e WHERE e.base_price >= 121;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT DISTINCT 
    "b0"."base_price" AS "base_price",
    "b0"."sku" AS "sku",
    "b0"."quantity" AS "quantity",
    "b0"."accessory_type" AS "accessory_type"
FROM "b0"
WHERE ("b0"."base_price" >= 121);

-- Q073 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.employee_no, e.password_hash, e.user_id, e.email FROM Employee e WHERE e.user_id < 1517085;
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
    "b0"."employee_no" AS "employee_no",
    "b0"."password_hash" AS "password_hash",
    "b0"."user_id" AS "user_id",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."user_id" < 1517085);

-- Q074 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.fit_type_men FROM MenClothing e WHERE e.dimensions < 'small';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."fit_type_men" AS "fit_type_men",
        "source"."dimensions" AS "dimensions"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."fit_type_men" AS "fit_type_men"
FROM "b0"
WHERE ("b0"."dimensions" < 'small');

-- Q075 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.sku, e.is_active FROM Footwear e WHERE e.size_system < 'alpha';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."sku" AS "sku",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."size_system" < 'alpha');

-- Q076 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.sku, e.is_active FROM DigitalProduct e WHERE e.product_id >= 16007192;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('digitalproduct', 'media', 'software'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."sku" AS "sku",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_id" >= 16007192);

-- Q077 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.fit_type_men, e.product_name FROM MenClothing e WHERE e.product_id < 15243672;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."fit_type_men" AS "fit_type_men",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."fit_type_men" AS "fit_type_men",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_id" < 15243672);

-- Q078 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.warranty_months, e.product_id, e.dimensions FROM Electronics e WHERE e.base_price <= 247;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."product_id" AS "product_id",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."base_price" <= 247);

-- Q079 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.product_name, e.is_active FROM KitchenAppliance e WHERE e.warranty_years > 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_years" AS "warranty_years",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."warranty_years" > 1);

-- Q080 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku FROM Media e WHERE e.sku > 'SKU-FNjV-77166401';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."sku" > 'SKU-FNjV-77166401');

-- Q081 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.quantity FROM Software e WHERE e.product_name < 'Vision-oriented upward-trending leverage';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."product_name" < 'Vision-oriented upward-trending leverage');

-- Q082 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id, e.employee_no, e.password_hash, e.email FROM Employee e WHERE e.employee_no <= 'EMP-89941966';
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
    "b0"."user_id" AS "user_id",
    "b0"."employee_no" AS "employee_no",
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."employee_no" <= 'EMP-89941966');

-- Q083 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.loyalty_tier FROM BusinessCustomer e WHERE e.password_hash <= 'b483213abcc462b0c9474c890d3a5624fd05cda523343df4fd390dc1d4d7933a';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."password_hash" AS "password_hash"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT DISTINCT 
    "b0"."loyalty_tier" AS "loyalty_tier"
FROM "b0"
WHERE ("b0"."password_hash" <= 'b483213abcc462b0c9474c890d3a5624fd05cda523343df4fd390dc1d4d7933a');

-- Q084 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions FROM Accessory e WHERE e.product_name < 'Vision-oriented well-modulated alliance';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."product_name" < 'Vision-oriented well-modulated alliance');

-- Q085 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.email, e.employee_no FROM Employee e WHERE e.password_hash < 'fdf23350bebe7b46ba6ed722980f14fdb83dc70b02a223f8693e700ca08caab9';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."employee_no" AS "employee_no",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('employee'))
)
SELECT 
    "b0"."email" AS "email",
    "b0"."employee_no" AS "employee_no"
FROM "b0"
WHERE ("b0"."password_hash" < 'fdf23350bebe7b46ba6ed722980f14fdb83dc70b02a223f8693e700ca08caab9');

-- Q086 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.product_name, e.quantity, e.product_id, e.warranty_months FROM Camera e WHERE e.warranty_months > 6;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT DISTINCT 
    "b0"."product_name" AS "product_name",
    "b0"."quantity" AS "quantity",
    "b0"."product_id" AS "product_id",
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."warranty_months" > 6);

-- Q087 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.cpu, e.base_price, e.warranty_months, e.sku FROM Desktop e WHERE e.dimensions >= 'medium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."cpu" AS "cpu",
    "b0"."base_price" AS "base_price",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."dimensions" >= 'medium');

-- Q088 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.product_id, e.base_price, e.product_name FROM Desktop e WHERE e.product_id >= 10269945;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."product_id" AS "product_id",
    "b0"."base_price" AS "base_price",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_id" >= 10269945);

-- Q089 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.warranty_months, e.sku, e.form_factor, e.is_active FROM Desktop e WHERE e.cpu < 'Ryzen 7';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."form_factor" AS "form_factor",
        "source"."warranty_months" AS "warranty_months",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT DISTINCT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."sku" AS "sku",
    "b0"."form_factor" AS "form_factor",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."cpu" < 'Ryzen 7');

-- Q090 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Smartwatch e WHERE e.product_name < 'Self-enabling homogeneous functionalities';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_name" < 'Self-enabling homogeneous functionalities');

-- Q091 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.quantity, e.band_size FROM Smartwatch e WHERE e.warranty_months < 36;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku",
        "source"."band_size" AS "band_size"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."quantity" AS "quantity",
    "b0"."band_size" AS "band_size"
FROM "b0"
WHERE ("b0"."warranty_months" < 36);

-- Q092 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.email FROM PrimeCustomer e WHERE e.email >= 'brian39@example.com';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."email" AS "email"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT 
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."email" >= 'brian39@example.com');

-- Q093 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.quantity, e.delivery_type, e.sku, e.is_active FROM Software e WHERE e.product_name <= 'Re-contextualized asymmetric framework';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT DISTINCT 
    "b0"."quantity" AS "quantity",
    "b0"."delivery_type" AS "delivery_type",
    "b0"."sku" AS "sku",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_name" <= 'Re-contextualized asymmetric framework');

-- Q094 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.base_price, e.quantity FROM WomenClothing e WHERE e.quantity < 23;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."base_price" AS "base_price",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."quantity" < 23);

-- Q095 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.dimensions, e.sku, e.size_system FROM Apparel e WHERE e.quantity > 17;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."dimensions" AS "dimensions",
    "b0"."sku" AS "sku",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."quantity" > 17);

-- Q096 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.product_id, e.energy_rating, e.is_active FROM KitchenAppliance e WHERE e.product_id < 13097966;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."energy_rating" AS "energy_rating",
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id",
    "b0"."energy_rating" AS "energy_rating",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_id" < 13097966);

-- Q097 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.product_id, e.quantity FROM Software e WHERE e.product_name > 'Advanced bi-directional orchestration';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."product_id" AS "product_id",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."product_name" > 'Advanced bi-directional orchestration');

-- Q098 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.product_id FROM Tablet e WHERE e.sku <= 'SKU-phiT-43841200';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-phiT-43841200');

-- Q099 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.product_id, e.quantity, e.base_price FROM Phone e WHERE e.warranty_months >= 12;
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
    "b0"."sku" AS "sku",
    "b0"."product_id" AS "product_id",
    "b0"."quantity" AS "quantity",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."warranty_months" >= 12);

-- Q100 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.employee_no FROM Employee e WHERE e.user_id >= 1427893;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."employee_no" AS "employee_no",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('employee'))
)
SELECT 
    "b0"."employee_no" AS "employee_no"
FROM "b0"
WHERE ("b0"."user_id" >= 1427893);

ROLLBACK;
