\set ON_ERROR_STOP on
\pset pager off
-- CompileDB mapping-aware relational workload
-- Conceptual workload: example2_schema_driven_selectivity_100_w01
-- Mapping ID: fa68ce77642be474c0e91514ccfa5d29b037566d0f2e42ffd246fae48a9fc668
-- Query shapes: 100
-- Executed statements: 100
BEGIN TRANSACTION READ ONLY;

-- Q001 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.dimensions FROM Laptop e WHERE e.product_name >= 'Intuitive client-server service-desk';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT DISTINCT 
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."product_name" >= 'Intuitive client-server service-desk');

-- Q002 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.size_system, e.is_active FROM Footwear e WHERE e.base_price >= 41;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT DISTINCT 
    "b0"."size_system" AS "size_system",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."base_price" >= 41);

-- Q003 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price FROM WomenClothing e WHERE e.dimensions < 'small';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."dimensions" < 'small');

-- Q004 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.company_name FROM BusinessCustomer e WHERE e.password_hash < 'b48c2613361ebf036b633a98d1a425fe0973362b038e19b9fb3c62a3be45a7c4';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."company_name" AS "company_name",
        "source"."password_hash" AS "password_hash"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT DISTINCT 
    "b0"."company_name" AS "company_name"
FROM "b0"
WHERE ("b0"."password_hash" < 'b48c2613361ebf036b633a98d1a425fe0973362b038e19b9fb3c62a3be45a7c4');

-- Q005 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.loyalty_tier, e.email, e.user_id, e.company_name FROM BusinessCustomer e WHERE e.email >= 'davidhuff@example.com';
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
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id",
    "b0"."company_name" AS "company_name"
FROM "b0"
WHERE ("b0"."email" >= 'davidhuff@example.com');

-- Q006 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.loyalty_tier FROM PrimeCustomer e WHERE e.user_id < 375517;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT 
    "b0"."loyalty_tier" AS "loyalty_tier"
FROM "b0"
WHERE ("b0"."user_id" < 375517);

-- Q007 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.product_id, e.is_active, e.product_name FROM Media e WHERE e.quantity >= 22;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."product_id" AS "product_id",
    "b0"."is_active" AS "is_active",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."quantity" >= 22);

-- Q008 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price FROM WomenClothing e WHERE e.product_name >= 'Focused content-based focus group';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."product_name" >= 'Focused content-based focus group');

-- Q009 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.product_name, e.sole_material FROM Footwear e WHERE e.quantity < 85;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sole_material" AS "sole_material",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."product_name" AS "product_name",
    "b0"."sole_material" AS "sole_material"
FROM "b0"
WHERE ("b0"."quantity" < 85);

-- Q010 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.sku, e.quantity, e.license_type FROM Software e WHERE e.product_name >= 'Object-based 24/7 artificial intelligence';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku",
        "source"."license_type" AS "license_type"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."sku" AS "sku",
    "b0"."quantity" AS "quantity",
    "b0"."license_type" AS "license_type"
FROM "b0"
WHERE ("b0"."product_name" >= 'Object-based 24/7 artificial intelligence');

-- Q011 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.product_id FROM Footwear e WHERE e.product_id <= 15716945;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."product_id" <= 15716945);

-- Q012 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.is_active, e.dimensions FROM Accessory e WHERE e.accessory_type >= 'case';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."accessory_type" >= 'case');

-- Q013 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.quantity FROM Software e WHERE e.quantity > 16;
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
    "b0"."sku" AS "sku",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."quantity" > 16);

-- Q014 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.product_name FROM MenClothing e WHERE e.sku >= 'SKU-FSCK-64850736';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-FSCK-64850736');

-- Q015 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.renewal_date, e.password_hash, e.email FROM PrimeCustomer e WHERE e.email < 'ujones@example.com';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."renewal_date" AS "renewal_date",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT 
    "b0"."renewal_date" AS "renewal_date",
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."email" < 'ujones@example.com');

-- Q016 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.product_id, e.format FROM Media e WHERE e.product_id > 16045006;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."format" AS "format",
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."product_id" AS "product_id",
    "b0"."format" AS "format"
FROM "b0"
WHERE ("b0"."product_id" > 16045006);

-- Q017 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.sku FROM Camera e WHERE e.dimensions > 'large';
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
    "b0"."dimensions" AS "dimensions",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."dimensions" > 'large');

-- Q018 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.product_name, e.product_id FROM Footwear e WHERE e.sole_material > 'TPU';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sole_material" AS "sole_material",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."product_name" AS "product_name",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."sole_material" > 'TPU');

-- Q019 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.sku, e.accessory_type, e.dimensions FROM Accessory e WHERE e.quantity <= 22;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."sku" AS "sku",
    "b0"."accessory_type" AS "accessory_type",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."quantity" <= 22);

-- Q020 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.employee_no, e.password_hash, e.email, e.user_id FROM Employee e WHERE e.user_id >= 1427893;
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
SELECT DISTINCT 
    "b0"."employee_no" AS "employee_no",
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."user_id" >= 1427893);

-- Q021 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.sole_material, e.product_name FROM Footwear e WHERE e.product_id < 15725246;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sole_material" AS "sole_material",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."sole_material" AS "sole_material",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_id" < 15725246);

-- Q022 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku FROM Camera e WHERE e.sku <= 'SKU-pcfH-16550496';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-pcfH-16550496');

-- Q023 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.accessory_type, e.sku FROM Accessory e WHERE e.accessory_type <= 'case';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."dimensions" AS "dimensions",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."accessory_type" AS "accessory_type",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."accessory_type" <= 'case');

-- Q024 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id, e.email, e.employee_no, e.password_hash FROM Employee e WHERE e.employee_no <= 'EMP-99018214';
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
    "b0"."email" AS "email",
    "b0"."employee_no" AS "employee_no",
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."employee_no" <= 'EMP-99018214');

-- Q025 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.dimensions, e.base_price, e.fit_type_men FROM MenClothing e WHERE e.product_name > 'Focused optimizing complexity';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."fit_type_men" AS "fit_type_men",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."dimensions" AS "dimensions",
    "b0"."base_price" AS "base_price",
    "b0"."fit_type_men" AS "fit_type_men"
FROM "b0"
WHERE ("b0"."product_name" > 'Focused optimizing complexity');

-- Q026 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM KitchenAppliance e WHERE e.base_price > 95;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."base_price" > 95);

-- Q027 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.is_active FROM Electronics e WHERE e.product_id > 3971079;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_id" > 3971079);

-- Q028 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.delivery_type, e.base_price FROM Software e WHERE e.product_id <= 16796632;
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
SELECT DISTINCT 
    "b0"."delivery_type" AS "delivery_type",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."product_id" <= 16796632);

-- Q029 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.product_name FROM Tablet e WHERE e.sku > 'SKU-aLIL-48201596';
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
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."sku" > 'SKU-aLIL-48201596');

-- Q030 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sku FROM MenClothing e WHERE e.material >= 'cotton';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."material" AS "material",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT DISTINCT 
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."material" >= 'cotton');

-- Q031 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.loyalty_tier, e.user_id FROM PrimeCustomer e WHERE e.password_hash >= '80121adceba1683a4e0c327f08ae179a45f26e01f05e851d4580fa4a0c309a8e';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT DISTINCT 
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."password_hash" >= '80121adceba1683a4e0c327f08ae179a45f26e01f05e851d4580fa4a0c309a8e');

-- Q032 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.cpu FROM Desktop e WHERE e.product_id > 9517334;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."cpu" AS "cpu"
FROM "b0"
WHERE ("b0"."product_id" > 9517334);

-- Q033 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price FROM MenClothing e WHERE e.material < 'polyester';
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
WHERE ("b0"."material" < 'polyester');

-- Q034 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash FROM PrimeCustomer e WHERE e.renewal_date >= '2026-09-07';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."renewal_date" AS "renewal_date",
        "source"."password_hash" AS "password_hash"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT 
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."renewal_date" >= '2026-09-07');

-- Q035 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.product_id, e.warranty_months, e.product_name FROM Tablet e WHERE e.base_price >= 17;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."base_price" >= 17);

-- Q036 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.base_price, e.sku FROM Software e WHERE e.sku > 'SKU-KINm-31688537';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."base_price" AS "base_price",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."sku" > 'SKU-KINm-31688537');

-- Q037 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions FROM Desktop e WHERE e.product_id >= 10269945;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."product_id" >= 10269945);

-- Q038 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.quantity, e.dimensions, e.sku FROM Accessory e WHERE e.warranty_months > 6;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."quantity" AS "quantity",
    "b0"."dimensions" AS "dimensions",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."warranty_months" > 6);

-- Q039 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.sku, e.warranty_months, e.is_active FROM Smartwatch e WHERE e.product_id <= 11725791;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."sku" AS "sku",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_id" <= 11725791);

-- Q040 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.is_active, e.carrier_lock FROM Phone e WHERE e.product_name <= 'Object-based bandwidth-monitored contingency';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."carrier_lock" AS "carrier_lock",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."is_active" AS "is_active",
    "b0"."carrier_lock" AS "carrier_lock"
FROM "b0"
WHERE ("b0"."product_name" <= 'Object-based bandwidth-monitored contingency');

-- Q041 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.accessory_type, e.product_name, e.warranty_months FROM Accessory e WHERE e.sku <= 'SKU-Zmip-90105888';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."warranty_months" AS "warranty_months",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."accessory_type" AS "accessory_type",
    "b0"."product_name" AS "product_name",
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-Zmip-90105888');

-- Q042 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id FROM Phone e WHERE e.product_id >= 12284908;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."product_id" >= 12284908);

-- Q043 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.cpu FROM Desktop e WHERE e.form_factor > 'all-in-one';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."form_factor" AS "form_factor"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT DISTINCT 
    "b0"."cpu" AS "cpu"
FROM "b0"
WHERE ("b0"."form_factor" > 'all-in-one');

-- Q044 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.quantity, e.sku, e.delivery_type FROM Media e WHERE e.base_price < 242;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT DISTINCT 
    "b0"."quantity" AS "quantity",
    "b0"."sku" AS "sku",
    "b0"."delivery_type" AS "delivery_type"
FROM "b0"
WHERE ("b0"."base_price" < 242);

-- Q045 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.product_id, e.is_active FROM Apparel e WHERE e.product_id > 13255741;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear'))
)
SELECT DISTINCT 
    "b0"."product_id" AS "product_id",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_id" > 13255741);

-- Q046 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.product_id, e.warranty_months FROM Camera e WHERE e.sensor_mp > 16;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sensor_mp" AS "sensor_mp",
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id",
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."sensor_mp" > 16);

-- Q047 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id, e.password_hash FROM Customer e WHERE e.user_id < 1213873;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."user_id" AS "user_id",
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."user_id" < 1213873);

-- Q048 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.product_name, e.is_active FROM Media e WHERE e.quantity >= 4;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT DISTINCT 
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."quantity" >= 4);

-- Q049 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.base_price, e.fit_type_men, e.dimensions FROM MenClothing e WHERE e.size_system > 'EU';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."fit_type_men" AS "fit_type_men",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."base_price" AS "base_price",
    "b0"."fit_type_men" AS "fit_type_men",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."size_system" > 'EU');

-- Q050 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_years, e.quantity, e.product_name, e.dimensions FROM KitchenAppliance e WHERE e.dimensions <= 'oversize';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_years" AS "warranty_years",
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."warranty_years" AS "warranty_years",
    "b0"."quantity" AS "quantity",
    "b0"."product_name" AS "product_name",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."dimensions" <= 'oversize');

-- Q051 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.quantity, e.warranty_months FROM Smartwatch e WHERE e.product_id >= 11490727;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."quantity" AS "quantity",
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."product_id" >= 11490727);

-- Q052 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.product_id, e.product_name, e.quantity FROM Smartwatch e WHERE e.sku <= 'SKU-eqJB-90041693';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."product_id" AS "product_id",
    "b0"."product_name" AS "product_name",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."sku" <= 'SKU-eqJB-90041693');

-- Q053 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price FROM Desktop e WHERE e.product_id <= 10462920;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."product_id" <= 10462920);

-- Q054 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.product_id FROM Apparel e WHERE e.base_price <= 148;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."base_price" <= 148);

-- Q055 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.screen_size_in, e.quantity, e.product_name FROM Tablet e WHERE e.product_name >= 'Object-based transitional portal';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."screen_size_in" AS "screen_size_in"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."screen_size_in" AS "screen_size_in",
    "b0"."quantity" AS "quantity",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_name" >= 'Object-based transitional portal');

-- Q056 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.material FROM Clothing e WHERE e.size_system > 'EU';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."material" AS "material",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('clothing', 'menclothing', 'womenclothing'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."material" AS "material"
FROM "b0"
WHERE ("b0"."size_system" > 'EU');

-- Q057 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.material, e.size_system, e.quantity FROM WomenClothing e WHERE e.dimensions >= 'medium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."material" AS "material",
        "source"."dimensions" AS "dimensions",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."material" AS "material",
    "b0"."size_system" AS "size_system",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."dimensions" >= 'medium');

-- Q058 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.email, e.loyalty_tier, e.password_hash, e.user_id FROM BusinessCustomer e WHERE e.email <= 'saramcdonald@example.org';
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
SELECT DISTINCT 
    "b0"."email" AS "email",
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."password_hash" AS "password_hash",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."email" <= 'saramcdonald@example.org');

-- Q059 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.cpu, e.dimensions, e.is_active, e.warranty_months FROM Laptop e WHERE e.base_price < 371;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT 
    "b0"."cpu" AS "cpu",
    "b0"."dimensions" AS "dimensions",
    "b0"."is_active" AS "is_active",
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."base_price" < 371);

-- Q060 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.employee_no, e.password_hash, e.email, e.user_id FROM Employee e WHERE e.email <= 'scontreras@example.net';
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
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."email" <= 'scontreras@example.net');

-- Q061 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.quantity, e.base_price FROM MenClothing e WHERE e.size_system > 'UK';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."quantity" AS "quantity",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."size_system" > 'UK');

-- Q062 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id FROM KitchenAppliance e WHERE e.base_price <= 243;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."base_price" <= 243);

-- Q063 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sensor_mp FROM Camera e WHERE e.sensor_mp > 20;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sensor_mp" AS "sensor_mp"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT DISTINCT 
    "b0"."sensor_mp" AS "sensor_mp"
FROM "b0"
WHERE ("b0"."sensor_mp" > 20);

-- Q064 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.employee_no, e.email FROM Employee e WHERE e.email >= 'klinevictoria@example.net';
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
    "b0"."employee_no" AS "employee_no",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."email" >= 'klinevictoria@example.net');

-- Q065 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.quantity, e.product_name, e.warranty_years FROM KitchenAppliance e WHERE e.is_active > 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_years" AS "warranty_years",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT DISTINCT 
    "b0"."quantity" AS "quantity",
    "b0"."product_name" AS "product_name",
    "b0"."warranty_years" AS "warranty_years"
FROM "b0"
WHERE ("b0"."is_active" > 0);

-- Q066 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.is_active, e.sensor_mp, e.quantity FROM Camera e WHERE e.base_price <= 153;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sensor_mp" AS "sensor_mp",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active",
    "b0"."sensor_mp" AS "sensor_mp",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."base_price" <= 153);

-- Q067 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.is_active, e.dimensions FROM MenClothing e WHERE e.base_price >= 122;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."is_active" AS "is_active",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."base_price" >= 122);

-- Q068 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.loyalty_tier, e.email, e.user_id FROM BusinessCustomer e WHERE e.loyalty_tier > 'bronze';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."loyalty_tier" > 'bronze');

-- Q069 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.product_name, e.is_active, e.size_system FROM MenClothing e WHERE e.quantity < 30;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."quantity" < 30);

-- Q070 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash, e.user_id, e.company_name, e.loyalty_tier FROM BusinessCustomer e WHERE e.email <= 'kimberlyduffy@example.net';
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
    "b0"."password_hash" AS "password_hash",
    "b0"."user_id" AS "user_id",
    "b0"."company_name" AS "company_name",
    "b0"."loyalty_tier" AS "loyalty_tier"
FROM "b0"
WHERE ("b0"."email" <= 'kimberlyduffy@example.net');

-- Q071 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku FROM KitchenAppliance e WHERE e.base_price < 244;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."base_price" < 244);

-- Q072 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.product_id, e.dimensions FROM WomenClothing e WHERE e.dimensions > 'large';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."product_id" AS "product_id",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."dimensions" > 'large');

-- Q073 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.product_id, e.is_active FROM Tablet e WHERE e.dimensions >= 'medium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."product_id" AS "product_id",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."dimensions" >= 'medium');

-- Q074 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.base_price, e.product_id, e.sku, e.delivery_type FROM Software e WHERE e.sku > 'SKU-AZVi-78639304';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT DISTINCT 
    "b0"."base_price" AS "base_price",
    "b0"."product_id" AS "product_id",
    "b0"."sku" AS "sku",
    "b0"."delivery_type" AS "delivery_type"
FROM "b0"
WHERE ("b0"."sku" > 'SKU-AZVi-78639304');

-- Q075 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.product_id FROM Desktop e WHERE e.cpu <= 'Ryzen 5';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."cpu" <= 'Ryzen 5');

-- Q076 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months FROM Desktop e WHERE e.product_name >= 'Integrated tertiary system engine';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE ("b0"."product_name" >= 'Integrated tertiary system engine');

-- Q077 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.dimensions, e.carrier_lock FROM Phone e WHERE e.product_id >= 12088872;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."carrier_lock" AS "carrier_lock",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."dimensions" AS "dimensions",
    "b0"."carrier_lock" AS "carrier_lock"
FROM "b0"
WHERE ("b0"."product_id" >= 12088872);

-- Q078 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.product_name, e.is_active, e.sku FROM Smartwatch e WHERE e.product_id < 11908200;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT DISTINCT 
    "b0"."product_name" AS "product_name",
    "b0"."is_active" AS "is_active",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."product_id" < 11908200);

-- Q079 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Desktop e WHERE e.sku > 'SKU-PprG-17406221';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."sku" > 'SKU-PprG-17406221');

-- Q080 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.loyalty_tier, e.password_hash, e.company_name, e.user_id FROM BusinessCustomer e WHERE e.password_hash < 'cd3532bab6fa3c35fb43b3dc77f7136fb6fbceb7e8876d7305ac0baab77a8468';
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
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."password_hash" AS "password_hash",
    "b0"."company_name" AS "company_name",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."password_hash" < 'cd3532bab6fa3c35fb43b3dc77f7136fb6fbceb7e8876d7305ac0baab77a8468');

-- Q081 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system, e.material, e.base_price FROM MenClothing e WHERE e.product_id < 14898778;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."material" AS "material",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."size_system" AS "size_system",
    "b0"."material" AS "material",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."product_id" < 14898778);

-- Q082 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.delivery_type, e.quantity, e.license_type, e.sku FROM Software e WHERE e.product_name <= 'Networked zero-defect core';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku",
        "source"."license_type" AS "license_type"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b0"."delivery_type" AS "delivery_type",
    "b0"."quantity" AS "quantity",
    "b0"."license_type" AS "license_type",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."product_name" <= 'Networked zero-defect core');

-- Q083 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.sku, e.dimensions, e.quantity FROM Footwear e WHERE e.product_id < 15725246;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."sku" AS "sku",
    "b0"."dimensions" AS "dimensions",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."product_id" < 15725246);

-- Q084 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash, e.loyalty_tier, e.user_id, e.email FROM BusinessCustomer e WHERE e.company_name > 'Davis PLC';
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
    "b0"."password_hash" AS "password_hash",
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."user_id" AS "user_id",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."company_name" > 'Davis PLC');

-- Q085 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sku, e.form_factor FROM Desktop e WHERE e.cpu >= 'Core i7';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."form_factor" AS "form_factor",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT DISTINCT 
    "b0"."sku" AS "sku",
    "b0"."form_factor" AS "form_factor"
FROM "b0"
WHERE ("b0"."cpu" >= 'Core i7');

-- Q086 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.product_name FROM KitchenAppliance e WHERE e.quantity < 246;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT DISTINCT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."quantity" < 246);

-- Q087 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.quantity FROM Appliance e WHERE e.quantity < 56;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('appliance', 'kitchenappliance'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."quantity" < 56);

-- Q088 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.delivery_type, e.product_id, e.is_active FROM Media e WHERE e.format >= 'ebook';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."format" AS "format",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT DISTINCT 
    "b0"."delivery_type" AS "delivery_type",
    "b0"."product_id" AS "product_id",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."format" >= 'ebook');

-- Q089 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.ram_gb, e.dimensions FROM Desktop e WHERE e.cpu > 'Apple M3';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."ram_gb" AS "ram_gb",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."ram_gb" AS "ram_gb",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."cpu" > 'Apple M3');

-- Q090 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.quantity FROM Laptop e WHERE e.product_id >= 11246252;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."product_id" >= 11246252);

-- Q091 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.employee_no, e.password_hash, e.user_id, e.email FROM Employee e WHERE e.email <= 'klindsey@example.org';
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
WHERE ("b0"."email" <= 'klindsey@example.org');

-- Q092 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.product_name, e.screen_size_in, e.product_id FROM Tablet e WHERE e.warranty_months < 36;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."screen_size_in" AS "screen_size_in"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."product_name" AS "product_name",
    "b0"."screen_size_in" AS "screen_size_in",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."warranty_months" < 36);

-- Q093 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.sku, e.dimensions FROM Camera e WHERE e.product_name < 'Visionary asynchronous hardware';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."sku" AS "sku",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."product_name" < 'Visionary asynchronous hardware');

-- Q094 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.quantity FROM MenClothing e WHERE e.quantity < 269;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."quantity" < 269);

-- Q095 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.quantity, e.dimensions FROM KitchenAppliance e WHERE e.base_price < 187;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."quantity" AS "quantity",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."base_price" < 187);

-- Q096 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.loyalty_tier FROM BusinessCustomer e WHERE e.email > 'brian79@example.net';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT DISTINCT 
    "b0"."loyalty_tier" AS "loyalty_tier"
FROM "b0"
WHERE ("b0"."email" > 'brian79@example.net');

-- Q097 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.is_active, e.quantity FROM Software e WHERE e.product_name >= 'Front-line foreground Local Area Network';
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
    "b0"."base_price" AS "base_price",
    "b0"."is_active" AS "is_active",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."product_name" >= 'Front-line foreground Local Area Network');

-- Q098 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.is_active, e.quantity, e.size_system FROM WomenClothing e WHERE e.product_id <= 15695838;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT DISTINCT 
    "b0"."is_active" AS "is_active",
    "b0"."quantity" AS "quantity",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."product_id" <= 15695838);

-- Q099 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system FROM MenClothing e WHERE e.quantity < 85;
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
WHERE ("b0"."quantity" < 85);

-- Q100 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.delivery_type, e.quantity, e.product_id FROM Software e WHERE e.delivery_type < 'stream';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT DISTINCT 
    "b0"."delivery_type" AS "delivery_type",
    "b0"."quantity" AS "quantity",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."delivery_type" < 'stream');

ROLLBACK;
