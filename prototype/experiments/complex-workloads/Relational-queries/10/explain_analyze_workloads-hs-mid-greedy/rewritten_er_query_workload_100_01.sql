\set ON_ERROR_STOP on
\pset pager off
-- CompileDB mapping-aware relational workload
-- Conceptual workload: example2_selectivity_aligned_100_w01
-- Mapping ID: 831b5e142cc90cb46c7ae5dc04870c05c92ea3e93a22453984d317af7f0e01aa
-- Query shapes: 100
-- Executed statements: 100
BEGIN TRANSACTION READ ONLY;

-- Q001 [selection_projection] occurrence 1/1
-- Original E/R: SELECT p.product_name, p.base_price FROM Product p WHERE p.base_price > 89 AND p.is_active = 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE (("b0"."base_price" > 89) AND ("b0"."is_active" = 1));

-- Q002 [selection_projection] occurrence 1/1
-- Original E/R: SELECT p.sku, p.product_name, p.quantity, p.mv_attributes FROM Product p WHERE p.quantity < 13;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."mv_attributes" AS "mv_attributes",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name",
    "b0"."quantity" AS "quantity",
    "b0"."mv_attributes" AS "mv_attributes"
FROM "b0"
WHERE ("b0"."quantity" < 13);

-- Q003 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT p.product_name FROM Product p WHERE p.base_price IN (42, 57, 58);
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
)
SELECT DISTINCT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."base_price" IN (42, 57, 58));

-- Q004 [selection_projection] occurrence 1/1
-- Original E/R: SELECT pp.product_name, pp.dimensions FROM PhysicalProduct pp WHERE pp.base_price >= 243;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."base_price" >= 243);

-- Q005 [selection_projection] occurrence 1/1
-- Original E/R: SELECT dp.product_name, dp.delivery_type FROM DigitalProduct dp WHERE dp.is_active = 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('digitalproduct', 'media', 'software'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."delivery_type" AS "delivery_type"
FROM "b0"
WHERE ("b0"."is_active" = 0);

-- Q006 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.warranty_months FROM Electronics e WHERE e.warranty_months >= 24 AND e.base_price > 182;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."warranty_months" AS "warranty_months"
FROM "b0"
WHERE (("b0"."warranty_months" >= 24) AND ("b0"."base_price" > 182));

-- Q007 [selection_projection] occurrence 1/1
-- Original E/R: SELECT c.product_name, c.cpu, c.ram_gb FROM Computer c WHERE c.ram_gb >= 32;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."ram_gb" AS "ram_gb",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('computer', 'desktop', 'laptop'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."cpu" AS "cpu",
    "b0"."ram_gb" AS "ram_gb"
FROM "b0"
WHERE ("b0"."ram_gb" >= 32);

-- Q008 [selection_projection] occurrence 1/1
-- Original E/R: SELECT d.product_name, d.cpu, d.form_factor FROM Desktop d WHERE d.base_price > 119;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."form_factor" AS "form_factor",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."cpu" AS "cpu",
    "b0"."form_factor" AS "form_factor"
FROM "b0"
WHERE ("b0"."base_price" > 119);

-- Q009 [selection_projection] occurrence 1/1
-- Original E/R: SELECT l.product_name, l.ram_gb, l.battery_wh FROM Laptop l WHERE l.battery_wh >= 85;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "ancestor_0"."ram_gb" AS "ram_gb",
        "source"."battery_wh" AS "battery_wh",
        "ancestor_0"."product_name" AS "product_name"
    FROM "relation_2" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."laptop_id" = "ancestor_0"."product_id")
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."ram_gb" AS "ram_gb",
    "b0"."battery_wh" AS "battery_wh"
FROM "b0"
WHERE ("b0"."battery_wh" >= 85);

-- Q010 [selection_projection] occurrence 1/1
-- Original E/R: SELECT t.product_name, t.screen_size_in FROM Tablet t WHERE t.screen_size_in IN (10, 13, 8);
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "ancestor_0"."product_name" AS "product_name",
        "source"."screen_size_in" AS "screen_size_in"
    FROM "relation_3" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."tablet_id" = "ancestor_0"."product_id")
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."screen_size_in" AS "screen_size_in"
FROM "b0"
WHERE ("b0"."screen_size_in" IN (10, 13, 8));

-- Q011 [selection_projection] occurrence 1/1
-- Original E/R: SELECT s.product_name, s.band_size FROM Smartwatch s WHERE s.is_active = 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "ancestor_0"."is_active" AS "is_active",
        "ancestor_0"."product_name" AS "product_name",
        "source"."band_size" AS "band_size"
    FROM "relation_4" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."smartwatch_id" = "ancestor_0"."product_id")
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."band_size" AS "band_size"
FROM "b0"
WHERE ("b0"."is_active" = 1);

-- Q012 [selection_projection] occurrence 1/1
-- Original E/R: SELECT c.product_name, c.sensor_mp FROM Camera c WHERE c.sensor_mp >= 48;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sensor_mp" AS "sensor_mp",
        "ancestor_0"."product_name" AS "product_name"
    FROM "relation_5" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."camera_id" = "ancestor_0"."product_id")
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."sensor_mp" AS "sensor_mp"
FROM "b0"
WHERE ("b0"."sensor_mp" >= 48);

-- Q013 [selection_projection] occurrence 1/1
-- Original E/R: SELECT p.product_name, p.carrier_lock FROM Phone p WHERE p.carrier_lock = 'locked';
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
    "b0"."product_name" AS "product_name",
    "b0"."carrier_lock" AS "carrier_lock"
FROM "b0"
WHERE ("b0"."carrier_lock" = 'locked');

-- Q014 [selection_projection] occurrence 1/1
-- Original E/R: SELECT a.product_name, a.accessory_type FROM Accessory a WHERE a.base_price > 361;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "ancestor_0"."base_price" AS "base_price",
        "ancestor_0"."product_name" AS "product_name"
    FROM "relation_6" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."accessory_id" = "ancestor_0"."product_id")
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."accessory_type" AS "accessory_type"
FROM "b0"
WHERE ("b0"."base_price" > 361);

-- Q015 [selection_projection] occurrence 1/1
-- Original E/R: SELECT a.product_name, a.energy_rating FROM Appliance a WHERE a.energy_rating IN ('C', 'A++');
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."energy_rating" AS "energy_rating",
        "ancestor_0"."product_name" AS "product_name"
    FROM "relation_7" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."appliance_id" = "ancestor_0"."product_id")
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."energy_rating" AS "energy_rating"
FROM "b0"
WHERE ("b0"."energy_rating" IN ('C', 'A++'));

-- Q016 [selection_projection] occurrence 1/1
-- Original E/R: SELECT k.product_name, k.energy_rating, k.warranty_years FROM KitchenAppliance k WHERE k.warranty_years >= 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."energy_rating" AS "energy_rating",
        "source"."warranty_years" AS "warranty_years",
        "ancestor_0"."product_name" AS "product_name"
    FROM "relation_7" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."appliance_id" = "ancestor_0"."product_id")
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."energy_rating" AS "energy_rating",
    "b0"."warranty_years" AS "warranty_years"
FROM "b0"
WHERE ("b0"."warranty_years" >= 5);

-- Q017 [selection_projection] occurrence 1/1
-- Original E/R: SELECT a.product_name, a.size_system FROM Apparel a WHERE a.quantity > 54;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."quantity" > 54);

-- Q018 [selection_projection] occurrence 1/1
-- Original E/R: SELECT c.product_name, c.size_system, c.material FROM Clothing c WHERE c.material = 'polyester';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."material" AS "material",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('clothing', 'menclothing', 'womenclothing'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."size_system" AS "size_system",
    "b0"."material" AS "material"
FROM "b0"
WHERE ("b0"."material" = 'polyester');

-- Q019 [selection_projection] occurrence 1/1
-- Original E/R: SELECT m.product_name, m.material, m.fit_type_men FROM MenClothing m WHERE m.base_price < 41;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."material" AS "material",
        "source"."fit_type_men" AS "fit_type_men",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."material" AS "material",
    "b0"."fit_type_men" AS "fit_type_men"
FROM "b0"
WHERE ("b0"."base_price" < 41);

-- Q020 [selection_projection] occurrence 1/1
-- Original E/R: SELECT w.product_name, w.material, w.fit_type_women FROM WomenClothing w WHERE w.is_active = 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "ancestor_0"."material" AS "material",
        "ancestor_0"."is_active" AS "is_active",
        "ancestor_0"."product_name" AS "product_name",
        "source"."fit_type_women" AS "fit_type_women"
    FROM "relation_8" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."womenclothing_id" = "ancestor_0"."product_id")
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."material" AS "material",
    "b0"."fit_type_women" AS "fit_type_women"
FROM "b0"
WHERE ("b0"."is_active" = 0);

-- Q021 [selection_projection] occurrence 1/1
-- Original E/R: SELECT f.product_name, f.size_system, f.sole_material FROM Footwear f WHERE f.quantity >= 23;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "ancestor_0"."size_system" AS "size_system",
        "source"."sole_material" AS "sole_material",
        "ancestor_0"."product_name" AS "product_name",
        "ancestor_0"."quantity" AS "quantity"
    FROM "relation_9" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."footwear_id" = "ancestor_0"."product_id")
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."size_system" AS "size_system",
    "b0"."sole_material" AS "sole_material"
FROM "b0"
WHERE ("b0"."quantity" >= 23);

-- Q022 [selection_projection] occurrence 1/1
-- Original E/R: SELECT m.product_name, m.delivery_type, m.format FROM Media m WHERE m.format IN ('music', 'printable');
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."format" AS "format",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."delivery_type" AS "delivery_type",
    "b0"."format" AS "format"
FROM "b0"
WHERE ("b0"."format" IN ('music', 'printable'));

-- Q023 [selection_projection] occurrence 1/1
-- Original E/R: SELECT s.product_name, s.delivery_type, s.license_type FROM Software s WHERE s.base_price <= 58;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "ancestor_0"."delivery_type" AS "delivery_type",
        "ancestor_0"."base_price" AS "base_price",
        "ancestor_0"."product_name" AS "product_name",
        "source"."license_type" AS "license_type"
    FROM "relation_10" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."software_id" = "ancestor_0"."product_id")
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."delivery_type" AS "delivery_type",
    "b0"."license_type" AS "license_type"
FROM "b0"
WHERE ("b0"."base_price" <= 58);

-- Q024 [selection_projection] occurrence 1/1
-- Original E/R: SELECT u.email, u.mv_user FROM User u WHERE u.password_hash IS NOT NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."email" AS "email",
        "source"."mv_user" AS "mv_user",
        "source"."password_hash" AS "password_hash"
    FROM "relation_11" AS "source"
    UNION ALL
    SELECT
        "source"."email" AS "email",
        "source"."mv_user" AS "mv_user",
        "source"."password_hash" AS "password_hash"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."email" AS "email",
    "b0"."mv_user" AS "mv_user"
FROM "b0"
WHERE ("b0"."password_hash" IS NOT NULL);

-- Q025 [selection_projection] occurrence 1/1
-- Original E/R: SELECT c.email, c.loyalty_tier, c.contact_no FROM Customer c WHERE c.loyalty_tier <> 'bronze';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."contact_no" AS "contact_no",
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."email" AS "email",
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."contact_no" AS "contact_no"
FROM "b0"
WHERE ("b0"."loyalty_tier" <> 'bronze');

-- Q026 [selection_projection] occurrence 1/1
-- Original E/R: SELECT p.email, p.loyalty_tier, p.renewal_date, p.subscription_addons FROM PrimeCustomer p WHERE p.renewal_date IS NOT NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."renewal_date" AS "renewal_date",
        "source"."subscription_addons" AS "subscription_addons",
        "source"."email" AS "email"
    FROM "relation_12" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT 
    "b0"."email" AS "email",
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."renewal_date" AS "renewal_date",
    "b0"."subscription_addons" AS "subscription_addons"
FROM "b0"
WHERE ("b0"."renewal_date" IS NOT NULL);

-- Q027 [selection_projection] occurrence 1/1
-- Original E/R: SELECT b.email, b.company_name FROM BusinessCustomer b WHERE b.company_name IS NOT NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."company_name" AS "company_name",
        "source"."email" AS "email"
    FROM "relation_12" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."email" AS "email",
    "b0"."company_name" AS "company_name"
FROM "b0"
WHERE ("b0"."company_name" IS NOT NULL);

-- Q028 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.email, e.employee_no FROM Employee e WHERE e.employee_no IS NOT NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."employee_no" AS "employee_no",
        "source"."email" AS "email"
    FROM "relation_11" AS "source"
    WHERE ("source"."role" IN ('employee'))
)
SELECT 
    "b0"."email" AS "email",
    "b0"."employee_no" AS "employee_no"
FROM "b0"
WHERE ("b0"."employee_no" IS NOT NULL);

-- Q029 [selection_projection] occurrence 1/1
-- Original E/R: SELECT c.category_name, c.parent FROM Category c WHERE c.parent IS NOT NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."category_name" AS "category_name",
        "source"."parent" AS "parent"
    FROM "relation_0" AS "source"
)
SELECT 
    "b0"."category_name" AS "category_name",
    "b0"."parent" AS "parent"
FROM "b0"
WHERE ("b0"."parent" IS NOT NULL);

-- Q030 [selection_projection] occurrence 1/1
-- Original E/R: SELECT o.placed_at, o.status FROM CustOrder o WHERE o.status IN ('delivered', 'pending');
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."status" AS "status"
    FROM "relation_23" AS "source"
)
SELECT 
    "b0"."placed_at" AS "placed_at",
    "b0"."status" AS "status"
FROM "b0"
WHERE ("b0"."status" IN ('delivered', 'pending'));

-- Q031 [weak_owner] occurrence 1/1
-- Original E/R: SELECT pi.url, pi.alt_text, pi.sort_order FROM ProductImage pi WHERE pi.sort_order <= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."alt_text" AS "alt_text",
        "source"."sort_order" AS "sort_order",
        "source"."url" AS "url"
    FROM "relation_13" AS "source"
)
SELECT 
    "b0"."url" AS "url",
    "b0"."alt_text" AS "alt_text",
    "b0"."sort_order" AS "sort_order"
FROM "b0"
WHERE ("b0"."sort_order" <= 1);

-- Q032 [weak_owner] occurrence 1/1
-- Original E/R: SELECT p.product_name, pi.url FROM ProductImage pi JOIN Product p ON OWNER(pi) = REF(p) WHERE p.is_active = 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."url" AS "url",
        "source"."product_id" AS "__owner_0"
    FROM "relation_13" AS "source"
),
"b1" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    "b0"."url" AS "url"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."is_active" = 0);

-- Q033 [weak_owner] occurrence 1/1
-- Original E/R: SELECT pv.barcode, pv.price_override, pv.is_active_variant FROM ProductVariant pv WHERE pv.price_override IS NOT NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."barcode" AS "barcode",
        "source"."is_active_variant" AS "is_active_variant",
        "source"."price_override" AS "price_override"
    FROM "relation_14" AS "source"
)
SELECT 
    "b0"."barcode" AS "barcode",
    "b0"."price_override" AS "price_override",
    "b0"."is_active_variant" AS "is_active_variant"
FROM "b0"
WHERE ("b0"."price_override" IS NOT NULL);

-- Q034 [weak_owner] occurrence 1/1
-- Original E/R: SELECT p.product_name, pv.barcode, pv.price_override FROM ProductVariant pv JOIN Product p ON OWNER(pv) = REF(p) WHERE pv.is_active_variant = 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."barcode" AS "barcode",
        "source"."is_active_variant" AS "is_active_variant",
        "source"."price_override" AS "price_override",
        "source"."product_id" AS "__owner_0"
    FROM "relation_14" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    "b0"."barcode" AS "barcode",
    "b0"."price_override" AS "price_override"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."is_active_variant" = 0);

-- Q035 [weak_owner] occurrence 1/1
-- Original E/R: SELECT ph.starts_at, ph.ends_at, ph.price FROM PriceHistory ph WHERE ph.price > 328;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ends_at" AS "ends_at",
        "source"."price" AS "price",
        "source"."starts_at" AS "starts_at"
    FROM "relation_15" AS "source"
)
SELECT 
    "b0"."starts_at" AS "starts_at",
    "b0"."ends_at" AS "ends_at",
    "b0"."price" AS "price"
FROM "b0"
WHERE ("b0"."price" > 328);

-- Q036 [weak_owner] occurrence 1/1
-- Original E/R: SELECT p.product_name, ph.starts_at, ph.price FROM PriceHistory ph JOIN Product p ON OWNER(ph) = REF(p) WHERE ph.price < p.base_price;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."price" AS "price",
        "source"."starts_at" AS "starts_at",
        "source"."product_id" AS "__owner_0"
    FROM "relation_15" AS "source"
),
"b1" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    "b0"."starts_at" AS "starts_at",
    "b0"."price" AS "price"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."price" < "b1"."base_price");

-- Q037 [weak_owner] occurrence 1/1
-- Original E/R: SELECT a.kind, a.city, a.state, a.country FROM Address a WHERE a.country = 'GB';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."city" AS "city",
        "source"."country" AS "country",
        "source"."kind" AS "kind",
        "source"."state" AS "state"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."kind" AS "kind",
    "b0"."city" AS "city",
    "b0"."state" AS "state",
    "b0"."country" AS "country"
FROM "b0"
WHERE ("b0"."country" = 'GB');

-- Q038 [weak_owner] occurrence 1/1
-- Original E/R: SELECT c.email, a.kind, a.city, a.postal_code FROM Address a JOIN Customer c ON OWNER(a) = REF(c) WHERE a.state = 'VA';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."city" AS "city",
        "source"."kind" AS "kind",
        "source"."postal_code" AS "postal_code",
        "source"."state" AS "state",
        "source"."customer_id" AS "__owner_0"
    FROM "relation_17" AS "source"
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
)
SELECT 
    "b1"."email" AS "email",
    "b0"."kind" AS "kind",
    "b0"."city" AS "city",
    "b0"."postal_code" AS "postal_code"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."state" = 'VA');

-- Q039 [weak_owner] occurrence 1/1
-- Original E/R: SELECT pm.brand, pm.last4, pm.exp_month, pm.exp_year FROM PaymentMethod pm WHERE pm.is_default = 'false';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."brand" AS "brand",
        "source"."exp_month" AS "exp_month",
        "source"."exp_year" AS "exp_year",
        "source"."is_default" AS "is_default",
        "source"."last4" AS "last4"
    FROM "relation_18" AS "source"
)
SELECT 
    "b0"."brand" AS "brand",
    "b0"."last4" AS "last4",
    "b0"."exp_month" AS "exp_month",
    "b0"."exp_year" AS "exp_year"
FROM "b0"
WHERE ("b0"."is_default" = 'false');

-- Q040 [weak_owner] occurrence 1/1
-- Original E/R: SELECT c.email, pm.brand, pm.last4 FROM PaymentMethod pm JOIN Customer c ON OWNER(pm) = REF(c) WHERE pm.exp_year >= 2031;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."brand" AS "brand",
        "source"."exp_year" AS "exp_year",
        "source"."last4" AS "last4",
        "source"."customer_id" AS "__owner_0"
    FROM "relation_18" AS "source"
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
)
SELECT 
    "b1"."email" AS "email",
    "b0"."brand" AS "brand",
    "b0"."last4" AS "last4"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."exp_year" >= 2031);

-- Q041 [weak_owner] occurrence 1/1
-- Original E/R: SELECT c.updated_at, OWNER(c) AS customer_ref FROM Cart c WHERE c.updated_at IS NOT NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."updated_at" AS "updated_at",
        "source"."customer_id" AS "__owner_0"
    FROM "relation_19" AS "source"
)
SELECT 
    "b0"."updated_at" AS "updated_at",
    "b0"."__owner_0" AS "customer_ref"
FROM "b0"
WHERE ("b0"."updated_at" IS NOT NULL);

-- Q042 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.wishlist_name, OWNER(w) AS customer_ref FROM Wishlist w WHERE w.wishlist_name IS NOT NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."wishlist_name" AS "wishlist_name",
        "source"."customer_id" AS "__owner_0"
    FROM "relation_20" AS "source"
)
SELECT 
    "b0"."wishlist_name" AS "wishlist_name",
    "b0"."__owner_0" AS "customer_ref"
FROM "b0"
WHERE ("b0"."wishlist_name" IS NOT NULL);

-- Q043 [weak_owner] occurrence 1/1
-- Original E/R: SELECT r.rating, r.title, r.created_at FROM Review r WHERE r.rating >= 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."rating" AS "rating",
        "source"."title" AS "title"
    FROM "relation_21" AS "source"
)
SELECT 
    "b0"."rating" AS "rating",
    "b0"."title" AS "title",
    "b0"."created_at" AS "created_at"
FROM "b0"
WHERE ("b0"."rating" >= 5);

-- Q044 [weak_owner] occurrence 1/1
-- Original E/R: SELECT c.email, r.rating, r.title FROM Review r JOIN Customer c ON OWNER(r) = REF(c) WHERE r.rating <= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."rating" AS "rating",
        "source"."title" AS "title",
        "source"."customer_id" AS "__owner_0"
    FROM "relation_21" AS "source"
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
)
SELECT 
    "b1"."email" AS "email",
    "b0"."rating" AS "rating",
    "b0"."title" AS "title"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."rating" <= 2);

-- Q045 [weak_owner] occurrence 1/1
-- Original E/R: SELECT s.started_at, s.device, OWNER(s) AS user_ref FROM BrowsingSession s WHERE s.device IN ('desktop', 'other');
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."device" AS "device",
        "source"."started_at" AS "started_at",
        "source"."user_id" AS "__owner_0"
    FROM "relation_22" AS "source"
)
SELECT 
    "b0"."started_at" AS "started_at",
    "b0"."device" AS "device",
    "b0"."__owner_0" AS "user_ref"
FROM "b0"
WHERE ("b0"."device" IN ('desktop', 'other'));

-- Q046 [weak_owner] occurrence 1/1
-- Original E/R: SELECT s.carrier, s.tracking_no, s.shipped_at, s.delivered_at FROM Shipment s WHERE s.delivered_at IS NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."carrier" AS "carrier",
        "source"."delivered_at" AS "delivered_at",
        "source"."shipped_at" AS "shipped_at",
        "source"."tracking_no" AS "tracking_no"
    FROM "relation_24" AS "source"
)
SELECT 
    "b0"."carrier" AS "carrier",
    "b0"."tracking_no" AS "tracking_no",
    "b0"."shipped_at" AS "shipped_at",
    "b0"."delivered_at" AS "delivered_at"
FROM "b0"
WHERE ("b0"."delivered_at" IS NULL);

-- Q047 [weak_owner] occurrence 1/1
-- Original E/R: SELECT o.status, s.carrier, s.tracking_no FROM Shipment s JOIN CustOrder o ON OWNER(s) = REF(o) WHERE s.shipped_at IS NOT NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."carrier" AS "carrier",
        "source"."shipped_at" AS "shipped_at",
        "source"."tracking_no" AS "tracking_no",
        "source"."custorder_id" AS "__owner_0"
    FROM "relation_24" AS "source"
),
"b1" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
)
SELECT 
    "b1"."status" AS "status",
    "b0"."carrier" AS "carrier",
    "b0"."tracking_no" AS "tracking_no"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."shipped_at" IS NOT NULL);

-- Q048 [weak_owner] occurrence 1/1
-- Original E/R: SELECT p.promo_name, c.max_uses, c.per_user_limit FROM Coupon c JOIN Promotion p ON OWNER(c) = REF(p) WHERE c.max_uses > 879;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."max_uses" AS "max_uses",
        "source"."per_user_limit" AS "per_user_limit",
        "source"."promotion_id" AS "__owner_0"
    FROM "relation_26" AS "source"
),
"b1" AS (
    SELECT
        "source"."promo_name" AS "promo_name",
        "source"."promotion_id" AS "__reference_0"
    FROM "relation_25" AS "source"
)
SELECT 
    "b1"."promo_name" AS "promo_name",
    "b0"."max_uses" AS "max_uses",
    "b0"."per_user_limit" AS "per_user_limit"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."max_uses" > 879);

-- Q049 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.warehouse_name, b.code FROM WarehouseBin b JOIN Warehouse w ON OWNER(b) = REF(w) WHERE w.region = 'Midwest';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."code" AS "code",
        "source"."warehouse_id" AS "__owner_0"
    FROM "relation_28" AS "source"
),
"b1" AS (
    SELECT
        "source"."region" AS "region",
        "source"."warehouse_name" AS "warehouse_name",
        "source"."warehouse_id" AS "__reference_0"
    FROM "relation_27" AS "source"
)
SELECT 
    "b1"."warehouse_name" AS "warehouse_name",
    "b0"."code" AS "code"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."region" = 'Midwest');

-- Q050 [weak_owner] occurrence 1/1
-- Original E/R: SELECT s.supplier_name, sc.email, sc.phone FROM SupplierContact sc JOIN Supplier s ON OWNER(sc) = REF(s) WHERE sc.email IS NOT NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."email" AS "email",
        "source"."phone" AS "phone",
        "source"."supplier_id" AS "__owner_0"
    FROM "relation_30" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_29" AS "source"
)
SELECT 
    "b1"."supplier_name" AS "supplier_name",
    "b0"."email" AS "email",
    "b0"."phone" AS "phone"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."email" IS NOT NULL);

-- Q051 [relationship_join] occurrence 1/1
-- Original E/R: SELECT c.category_name, p.product_name FROM category_products cp JOIN Category c ON ENDPOINT(cp, Category) = REF(c) JOIN Product p ON ENDPOINT(cp, Product) = REF(p) WHERE p.is_active = 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."category_products_category_id" AS "__endpoint_category_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b1" AS (
    SELECT
        "source"."category_name" AS "category_name",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."category_name" AS "category_name",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."is_active" = 0);

-- Q052 [relationship_join] occurrence 1/1
-- Original E/R: SELECT p.product_name, t.tag_name FROM product_tags pt JOIN Product p ON ENDPOINT(pt, Product) = REF(p) JOIN Tag t ON ENDPOINT(pt, Tag) = REF(t) WHERE p.base_price > 244;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."tag_id" AS "__endpoint_tag_0"
    FROM "relation_34" AS "source"
),
"b1" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."tag_name" AS "tag_name",
        "source"."tag_id" AS "__reference_0"
    FROM "relation_16" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    "b2"."tag_name" AS "tag_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_tag_0" = "b2"."__reference_0"))
WHERE ("b1"."base_price" > 244);

-- Q053 [relationship_join] occurrence 1/1
-- Original E/R: SELECT p.product_name AS bundle, c.product_name AS component FROM bundle_components bc JOIN Product p ON ENDPOINT(bc, product_id) = REF(p) JOIN Product c ON ENDPOINT(bc, bundle_product_id) = REF(c);
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_product_product_id" AS "__endpoint_bundle_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_35" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."product_name" AS "bundle",
    "b2"."product_name" AS "component"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bundle_product_id_0" = "b2"."__reference_0"));

-- Q054 [relationship_join] occurrence 1/1
-- Original E/R: SELECT p1.product_name AS product, p2.product_name AS related_product FROM bought_together bt JOIN Product p1 ON ENDPOINT(bt, product_id) = REF(p1) JOIN Product p2 ON ENDPOINT(bt, bought_together_product_id) = REF(p2) WHERE p1.is_active = 0 AND p2.is_active = 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_36" AS "source"
),
"b1" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."product_name" AS "product",
    "b2"."product_name" AS "related_product"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bought_together_product_id_0" = "b2"."__reference_0"))
WHERE (("b1"."is_active" = 0) AND ("b2"."is_active" = 0));

-- Q055 [relationship_join] occurrence 1/1
-- Original E/R: SELECT OWNER(c) AS customer_ref, p.product_name FROM cart_contains cc JOIN Cart c ON ENDPOINT(cc, Cart) = REF(c) JOIN Product p ON ENDPOINT(cc, Product) = REF(p) WHERE p.quantity > 29;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_cart_0",
        "source"."cart_id" AS "__endpoint_cart_1",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_37" AS "source"
),
"b1" AS (
    SELECT
        "source"."customer_id" AS "__owner_0",
        "source"."customer_id" AS "__reference_0",
        "source"."cart_id" AS "__reference_1"
    FROM "relation_19" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."__owner_0" AS "customer_ref",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_cart_0" = "b1"."__reference_0" AND "b0"."__endpoint_cart_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."quantity" > 29);

-- Q056 [relationship_join] occurrence 1/1
-- Original E/R: SELECT w.wishlist_name, p.product_name FROM wishlist_contains wc JOIN Wishlist w ON ENDPOINT(wc, Wishlist) = REF(w) JOIN Product p ON ENDPOINT(wc, Product) = REF(p) WHERE p.base_price < 97;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_wishlist_0",
        "source"."wishlist_id" AS "__endpoint_wishlist_1"
    FROM "relation_38" AS "source"
),
"b1" AS (
    SELECT
        "source"."wishlist_name" AS "wishlist_name",
        "source"."customer_id" AS "__reference_0",
        "source"."wishlist_id" AS "__reference_1"
    FROM "relation_20" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."wishlist_name" AS "wishlist_name",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_wishlist_0" = "b1"."__reference_0" AND "b0"."__endpoint_wishlist_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."base_price" < 97);

-- Q057 [relationship_join] occurrence 1/1
-- Original E/R: SELECT p.product_name, r.rating, r.title FROM reviews rv JOIN Product p ON ENDPOINT(rv, Product) = REF(p) JOIN Review r ON ENDPOINT(rv, Review) = REF(r) WHERE r.rating >= 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."reviews_product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_review_0",
        "source"."review_id" AS "__endpoint_review_1"
    FROM "relation_39" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."rating" AS "rating",
        "source"."title" AS "title",
        "source"."customer_id" AS "__reference_0",
        "source"."review_id" AS "__reference_1"
    FROM "relation_21" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    "b2"."rating" AS "rating",
    "b2"."title" AS "title"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_review_0" = "b2"."__reference_0" AND "b0"."__endpoint_review_1" = "b2"."__reference_1"))
WHERE ("b2"."rating" >= 5);

-- Q058 [relationship_join] occurrence 1/1
-- Original E/R: SELECT c.email, o.placed_at, o.status FROM customer_orders co JOIN Customer c ON ENDPOINT(co, Customer) = REF(c) JOIN CustOrder o ON ENDPOINT(co, CustOrder) = REF(o) WHERE o.status = 'delivered';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_23" AS "source"
    WHERE ("source"."customer_orders_customer_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
),
"b2" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
)
SELECT 
    "b1"."email" AS "email",
    "b2"."placed_at" AS "placed_at",
    "b2"."status" AS "status"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b2"."status" = 'delivered');

-- Q059 [relationship_join] occurrence 1/1
-- Original E/R: SELECT o.status, p.product_name, p.base_price FROM order_items oi JOIN CustOrder o ON ENDPOINT(oi, CustOrder) = REF(o) JOIN Product p ON ENDPOINT(oi, Product) = REF(p) WHERE p.quantity > 29;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_40" AS "source"
),
"b1" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."status" AS "status",
    "b2"."product_name" AS "product_name",
    "b2"."base_price" AS "base_price"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."quantity" > 29);

-- Q060 [relationship_join] occurrence 1/1
-- Original E/R: SELECT pm.brand, pm.last4, o.status FROM payment_order po JOIN PaymentMethod pm ON ENDPOINT(po, PaymentMethod) = REF(pm) JOIN CustOrder o ON ENDPOINT(po, CustOrder) = REF(o) WHERE pm.is_default = 'true';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."payment_order_customer_id" AS "__endpoint_paymentmethod_0",
        "source"."payment_order_payment_method_id" AS "__endpoint_paymentmethod_1"
    FROM "relation_23" AS "source"
    WHERE ("source"."payment_order_customer_id" IS NOT NULL) AND ("source"."payment_order_payment_method_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."brand" AS "brand",
        "source"."is_default" AS "is_default",
        "source"."last4" AS "last4",
        "source"."customer_id" AS "__reference_0",
        "source"."payment_method_id" AS "__reference_1"
    FROM "relation_18" AS "source"
),
"b2" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
)
SELECT 
    "b1"."brand" AS "brand",
    "b1"."last4" AS "last4",
    "b2"."status" AS "status"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_paymentmethod_0" = "b1"."__reference_0" AND "b0"."__endpoint_paymentmethod_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."is_default" = 'true');

-- Q061 [relationship_join] occurrence 1/1
-- Original E/R: SELECT o.placed_at, p.product_name FROM order_returns r JOIN CustOrder o ON ENDPOINT(r, CustOrder) = REF(o) JOIN Product p ON ENDPOINT(r, Product) = REF(p) WHERE o.status = 'shipped';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_41" AS "source"
),
"b1" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."placed_at" AS "placed_at",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."status" = 'shipped');

-- Q062 [relationship_join] occurrence 1/1
-- Original E/R: SELECT o.status, c.max_uses, c.per_user_limit FROM order_coupons oc JOIN CustOrder o ON ENDPOINT(oc, CustOrder) = REF(o) JOIN Coupon c ON ENDPOINT(oc, Coupon) = REF(c) WHERE c.per_user_limit > 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."promotion_id" AS "__endpoint_coupon_0",
        "source"."coupon_code" AS "__endpoint_coupon_1",
        "source"."order_coupons_custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_42" AS "source"
),
"b1" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
),
"b2" AS (
    SELECT
        "source"."max_uses" AS "max_uses",
        "source"."per_user_limit" AS "per_user_limit",
        "source"."promotion_id" AS "__reference_0",
        "source"."coupon_code" AS "__reference_1"
    FROM "relation_26" AS "source"
)
SELECT 
    "b1"."status" AS "status",
    "b2"."max_uses" AS "max_uses",
    "b2"."per_user_limit" AS "per_user_limit"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_coupon_0" = "b2"."__reference_0" AND "b0"."__endpoint_coupon_1" = "b2"."__reference_1"))
WHERE ("b2"."per_user_limit" > 1);

-- Q063 [relationship_join] occurrence 1/1
-- Original E/R: SELECT p.product_name, b.code FROM stock st JOIN Product p ON ENDPOINT(st, Product) = REF(p) JOIN WarehouseBin b ON ENDPOINT(st, WarehouseBin) = REF(b) WHERE p.quantity < 4;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."warehouse_id" AS "__endpoint_warehousebin_0",
        "source"."bin_id" AS "__endpoint_warehousebin_1"
    FROM "relation_43" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."code" AS "code",
        "source"."warehouse_id" AS "__reference_0",
        "source"."bin_id" AS "__reference_1"
    FROM "relation_28" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    "b2"."code" AS "code"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_warehousebin_0" = "b2"."__reference_0" AND "b0"."__endpoint_warehousebin_1" = "b2"."__reference_1"))
WHERE ("b1"."quantity" < 4);

-- Q064 [relationship_join] occurrence 1/1
-- Original E/R: SELECT s.supplier_name, p.product_name FROM supplier_products sp JOIN Supplier s ON ENDPOINT(sp, Supplier) = REF(s) JOIN Product p ON ENDPOINT(sp, Product) = REF(p) WHERE p.is_active = 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_44" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_29" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."supplier_name" AS "supplier_name",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."is_active" = 0);

-- Q065 [relationship_join] occurrence 1/1
-- Original E/R: SELECT s.supplier_name, po.created_at, po.status FROM supplier_pos r JOIN Supplier s ON ENDPOINT(r, Supplier) = REF(s) JOIN PurchaseOrder po ON ENDPOINT(r, PurchaseOrder) = REF(po) WHERE po.status <> 'received';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0",
        "source"."supplier_pos_supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_31" AS "source"
    WHERE ("source"."supplier_pos_supplier_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_29" AS "source"
),
"b2" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."status" AS "status",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_31" AS "source"
)
SELECT 
    "b1"."supplier_name" AS "supplier_name",
    "b2"."created_at" AS "created_at",
    "b2"."status" AS "status"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_purchaseorder_0" = "b2"."__reference_0"))
WHERE ("b2"."status" <> 'received');

-- Q066 [relationship_join] occurrence 1/1
-- Original E/R: SELECT po.status, p.product_name FROM po_items pi JOIN PurchaseOrder po ON ENDPOINT(pi, PurchaseOrder) = REF(po) JOIN Product p ON ENDPOINT(pi, Product) = REF(p) WHERE p.base_price >= 149;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0"
    FROM "relation_45" AS "source"
),
"b1" AS (
    SELECT
        "source"."status" AS "status",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_31" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."status" AS "status",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_purchaseorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."base_price" >= 149);

-- Q067 [relationship_join] occurrence 1/1
-- Original E/R: SELECT cp.carrier_code, s.tracking_no, s.delivered_at FROM courier_shipments cs JOIN CourierPartner cp ON ENDPOINT(cs, CourierPartner) = REF(cp) JOIN Shipment s ON ENDPOINT(cs, Shipment) = REF(s) WHERE s.shipped_at IS NOT NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."courier_shipments_courierpartner_id" AS "__endpoint_courierpartner_0",
        "source"."custorder_id" AS "__endpoint_shipment_0",
        "source"."shipment_id" AS "__endpoint_shipment_1"
    FROM "relation_24" AS "source"
    WHERE ("source"."courier_shipments_courierpartner_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."carrier_code" AS "carrier_code",
        "source"."courierpartner_id" AS "__reference_0"
    FROM "relation_32" AS "source"
),
"b2" AS (
    SELECT
        "source"."delivered_at" AS "delivered_at",
        "source"."shipped_at" AS "shipped_at",
        "source"."tracking_no" AS "tracking_no",
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_24" AS "source"
)
SELECT 
    "b1"."carrier_code" AS "carrier_code",
    "b2"."tracking_no" AS "tracking_no",
    "b2"."delivered_at" AS "delivered_at"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
WHERE ("b2"."shipped_at" IS NOT NULL);

-- Q068 [relationship_join] occurrence 1/1
-- Original E/R: SELECT p1.product_name AS phone, p2.product_name AS bundled_phone FROM bundle_phones bp JOIN Phone p1 ON ENDPOINT(bp, phone_id) = REF(p1) JOIN Phone p2 ON ENDPOINT(bp, bundle_phone_id) = REF(p2) WHERE p1.carrier_lock = 'locked';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_phone_phone_id" AS "__endpoint_bundle_phone_id_0",
        "source"."phone_id" AS "__endpoint_phone_id_0"
    FROM "relation_46" AS "source"
),
"b1" AS (
    SELECT
        "source"."carrier_lock" AS "carrier_lock",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b1"."product_name" AS "phone",
    "b2"."product_name" AS "bundled_phone"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bundle_phone_id_0" = "b2"."__reference_0"))
WHERE ("b1"."carrier_lock" = 'locked');

-- Q069 [relationship_join] occurrence 1/1
-- Original E/R: SELECT p.product_name AS phone, a.product_name AS accessory FROM bundled_phone_accessory bpa JOIN Phone p ON ENDPOINT(bpa, Phone) = REF(p) JOIN Accessory a ON ENDPOINT(bpa, Accessory) = REF(a) WHERE a.base_price < 78;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_id" AS "__endpoint_accessory_0",
        "source"."phone_id" AS "__endpoint_phone_0"
    FROM "relation_47" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "ancestor_0"."base_price" AS "base_price",
        "ancestor_0"."product_name" AS "product_name",
        "source"."accessory_id" AS "__reference_0"
    FROM "relation_6" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."accessory_id" = "ancestor_0"."product_id")
)
SELECT 
    "b1"."product_name" AS "phone",
    "b2"."product_name" AS "accessory"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_accessory_0" = "b2"."__reference_0"))
WHERE ("b2"."base_price" < 78);

-- Q070 [relationship_join] occurrence 1/1
-- Original E/R: SELECT s.product_name, c.email FROM software_downloads sd JOIN Software s ON ENDPOINT(sd, Software) = REF(s) JOIN Customer c ON ENDPOINT(sd, Customer) = REF(c) WHERE s.is_active = 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_customer_0",
        "source"."software_id" AS "__endpoint_software_0"
    FROM "relation_48" AS "source"
),
"b1" AS (
    SELECT
        "ancestor_0"."is_active" AS "is_active",
        "ancestor_0"."product_name" AS "product_name",
        "source"."software_id" AS "__reference_0"
    FROM "relation_10" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."software_id" = "ancestor_0"."product_id")
),
"b2" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    "b2"."email" AS "email"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_software_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_customer_0" = "b2"."__reference_0"))
WHERE ("b1"."is_active" = 0);

-- Q071 [aggregation] occurrence 1/1
-- Original E/R: SELECT c.category_name, COUNT(DISTINCT REF(p)) AS product_count FROM category_products cp JOIN Category c ON ENDPOINT(cp, Category) = REF(c) JOIN Product p ON ENDPOINT(cp, Product) = REF(p) GROUP BY REF(c), c.category_name HAVING COUNT(DISTINCT REF(p)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."category_products_category_id" AS "__endpoint_category_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b1" AS (
    SELECT
        "source"."category_name" AS "category_name",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."category_name" AS "category_name",
    COUNT(DISTINCT "b2"."__reference_0") AS "product_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
GROUP BY
    "b1"."__reference_0",
    "b1"."category_name"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 2);

-- Q072 [aggregation] occurrence 1/1
-- Original E/R: SELECT t.tag_name, COUNT(DISTINCT REF(p)) AS product_count FROM product_tags pt JOIN Product p ON ENDPOINT(pt, Product) = REF(p) JOIN Tag t ON ENDPOINT(pt, Tag) = REF(t) GROUP BY REF(t), t.tag_name HAVING COUNT(DISTINCT REF(p)) > 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."tag_id" AS "__endpoint_tag_0"
    FROM "relation_34" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."tag_name" AS "tag_name",
        "source"."tag_id" AS "__reference_0"
    FROM "relation_16" AS "source"
)
SELECT 
    "b2"."tag_name" AS "tag_name",
    COUNT(DISTINCT "b1"."__reference_0") AS "product_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_tag_0" = "b2"."__reference_0"))
GROUP BY
    "b2"."__reference_0",
    "b2"."tag_name"
HAVING (COUNT(DISTINCT "b1"."__reference_0") > 5);

-- Q073 [aggregation] occurrence 1/1
-- Original E/R: SELECT c.category_name, AVG(p.base_price) AS average_price, MAX(p.base_price) AS maximum_price FROM category_products cp JOIN Category c ON ENDPOINT(cp, Category) = REF(c) JOIN Product p ON ENDPOINT(cp, Product) = REF(p) WHERE p.is_active = 0 GROUP BY REF(c), c.category_name HAVING AVG(p.base_price) > 50;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."category_products_category_id" AS "__endpoint_category_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b1" AS (
    SELECT
        "source"."category_name" AS "category_name",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."category_name" AS "category_name",
    AVG("b2"."base_price") AS "average_price",
    MAX("b2"."base_price") AS "maximum_price"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."is_active" = 0)
GROUP BY
    "b1"."__reference_0",
    "b1"."category_name"
HAVING (AVG("b2"."base_price") > 50);

-- Q074 [aggregation] occurrence 1/1
-- Original E/R: SELECT s.supplier_name, COUNT(DISTINCT REF(p)) AS supplied_products FROM supplier_products sp JOIN Supplier s ON ENDPOINT(sp, Supplier) = REF(s) JOIN Product p ON ENDPOINT(sp, Product) = REF(p) GROUP BY REF(s), s.supplier_name HAVING COUNT(DISTINCT REF(p)) >= 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_44" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_29" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."supplier_name" AS "supplier_name",
    COUNT(DISTINCT "b2"."__reference_0") AS "supplied_products"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
GROUP BY
    "b1"."__reference_0",
    "b1"."supplier_name"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 3);

-- Q075 [aggregation] occurrence 1/1
-- Original E/R: SELECT w.warehouse_name, COUNT(DISTINCT REF(p)) AS stocked_products FROM stock st JOIN Product p ON ENDPOINT(st, Product) = REF(p) JOIN WarehouseBin b ON ENDPOINT(st, WarehouseBin) = REF(b) JOIN Warehouse w ON OWNER(b) = REF(w) GROUP BY REF(w), w.warehouse_name HAVING COUNT(DISTINCT REF(p)) > 10;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."warehouse_id" AS "__endpoint_warehousebin_0",
        "source"."bin_id" AS "__endpoint_warehousebin_1"
    FROM "relation_43" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."warehouse_id" AS "__owner_0",
        "source"."warehouse_id" AS "__reference_0",
        "source"."bin_id" AS "__reference_1"
    FROM "relation_28" AS "source"
),
"b3" AS (
    SELECT
        "source"."warehouse_name" AS "warehouse_name",
        "source"."warehouse_id" AS "__reference_0"
    FROM "relation_27" AS "source"
)
SELECT 
    "b3"."warehouse_name" AS "warehouse_name",
    COUNT(DISTINCT "b1"."__reference_0") AS "stocked_products"
FROM ((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_warehousebin_0" = "b2"."__reference_0" AND "b0"."__endpoint_warehousebin_1" = "b2"."__reference_1")) INNER JOIN "b3" ON ("b2"."__owner_0" = "b3"."__reference_0"))
GROUP BY
    "b3"."__reference_0",
    "b3"."warehouse_name"
HAVING (COUNT(DISTINCT "b1"."__reference_0") > 10);

-- Q076 [aggregation] occurrence 1/1
-- Original E/R: SELECT c.email, COUNT(DISTINCT REF(o)) AS order_count FROM customer_orders co JOIN Customer c ON ENDPOINT(co, Customer) = REF(c) JOIN CustOrder o ON ENDPOINT(co, CustOrder) = REF(o) GROUP BY REF(c), c.email HAVING COUNT(DISTINCT REF(o)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_23" AS "source"
    WHERE ("source"."customer_orders_customer_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
),
"b2" AS (
    SELECT
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
)
SELECT 
    "b1"."email" AS "email",
    COUNT(DISTINCT "b2"."__reference_0") AS "order_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
GROUP BY
    "b1"."__reference_0",
    "b1"."email"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 2);

-- Q077 [aggregation] occurrence 1/1
-- Original E/R: SELECT o.status, COUNT(DISTINCT REF(p)) AS item_count, SUM(p.base_price) AS item_value FROM order_items oi JOIN CustOrder o ON ENDPOINT(oi, CustOrder) = REF(o) JOIN Product p ON ENDPOINT(oi, Product) = REF(p) GROUP BY REF(o), o.status HAVING SUM(p.base_price) > 200;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_40" AS "source"
),
"b1" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."status" AS "status",
    COUNT(DISTINCT "b2"."__reference_0") AS "item_count",
    SUM("b2"."base_price") AS "item_value"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
GROUP BY
    "b1"."__reference_0",
    "b1"."status"
HAVING (SUM("b2"."base_price") > 200);

-- Q078 [aggregation] occurrence 1/1
-- Original E/R: SELECT p.product_name, COUNT(DISTINCT REF(r)) AS review_count, AVG(r.rating) AS average_rating FROM reviews rv JOIN Product p ON ENDPOINT(rv, Product) = REF(p) JOIN Review r ON ENDPOINT(rv, Review) = REF(r) GROUP BY REF(p), p.product_name HAVING AVG(r.rating) >= 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."reviews_product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_review_0",
        "source"."review_id" AS "__endpoint_review_1"
    FROM "relation_39" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."rating" AS "rating",
        "source"."customer_id" AS "__reference_0",
        "source"."review_id" AS "__reference_1"
    FROM "relation_21" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) AS "review_count",
    AVG("b2"."rating") AS "average_rating"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_review_0" = "b2"."__reference_0" AND "b0"."__endpoint_review_1" = "b2"."__reference_1"))
GROUP BY
    "b1"."__reference_0",
    "b1"."product_name"
HAVING (AVG("b2"."rating") >= 3);

-- Q079 [aggregation] occurrence 1/1
-- Original E/R: SELECT OWNER(c) AS customer_ref, COUNT(DISTINCT REF(p)) AS cart_products FROM cart_contains cc JOIN Cart c ON ENDPOINT(cc, Cart) = REF(c) JOIN Product p ON ENDPOINT(cc, Product) = REF(p) GROUP BY REF(c), OWNER(c) HAVING COUNT(DISTINCT REF(p)) >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_cart_0",
        "source"."cart_id" AS "__endpoint_cart_1",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_37" AS "source"
),
"b1" AS (
    SELECT
        "source"."customer_id" AS "__owner_0",
        "source"."customer_id" AS "__reference_0",
        "source"."cart_id" AS "__reference_1"
    FROM "relation_19" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."__owner_0" AS "customer_ref",
    COUNT(DISTINCT "b2"."__reference_0") AS "cart_products"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_cart_0" = "b1"."__reference_0" AND "b0"."__endpoint_cart_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
GROUP BY
    "b1"."__reference_0",
    "b1"."__reference_1",
    "b1"."__owner_0"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 1);

-- Q080 [aggregation] occurrence 1/1
-- Original E/R: SELECT w.wishlist_name, COUNT(DISTINCT REF(p)) AS wishlist_products FROM wishlist_contains wc JOIN Wishlist w ON ENDPOINT(wc, Wishlist) = REF(w) JOIN Product p ON ENDPOINT(wc, Product) = REF(p) GROUP BY REF(w), w.wishlist_name HAVING COUNT(DISTINCT REF(p)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_wishlist_0",
        "source"."wishlist_id" AS "__endpoint_wishlist_1"
    FROM "relation_38" AS "source"
),
"b1" AS (
    SELECT
        "source"."wishlist_name" AS "wishlist_name",
        "source"."customer_id" AS "__reference_0",
        "source"."wishlist_id" AS "__reference_1"
    FROM "relation_20" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."wishlist_name" AS "wishlist_name",
    COUNT(DISTINCT "b2"."__reference_0") AS "wishlist_products"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_wishlist_0" = "b1"."__reference_0" AND "b0"."__endpoint_wishlist_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
GROUP BY
    "b1"."__reference_0",
    "b1"."__reference_1",
    "b1"."wishlist_name"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 2);

-- Q081 [aggregation] occurrence 1/1
-- Original E/R: SELECT s.product_name, COUNT(DISTINCT REF(c)) AS download_customers FROM software_downloads sd JOIN Software s ON ENDPOINT(sd, Software) = REF(s) JOIN Customer c ON ENDPOINT(sd, Customer) = REF(c) GROUP BY REF(s), s.product_name HAVING COUNT(DISTINCT REF(c)) > 10;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_customer_0",
        "source"."software_id" AS "__endpoint_software_0"
    FROM "relation_48" AS "source"
),
"b1" AS (
    SELECT
        "ancestor_0"."product_name" AS "product_name",
        "source"."software_id" AS "__reference_0"
    FROM "relation_10" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."software_id" = "ancestor_0"."product_id")
),
"b2" AS (
    SELECT
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    COUNT(DISTINCT "b2"."__reference_0") AS "download_customers"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_software_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_customer_0" = "b2"."__reference_0"))
GROUP BY
    "b1"."__reference_0",
    "b1"."product_name"
HAVING (COUNT(DISTINCT "b2"."__reference_0") > 10);

-- Q082 [aggregation] occurrence 1/1
-- Original E/R: SELECT p.product_name, MIN(ph.price) AS minimum_price, MAX(ph.price) AS maximum_price, AVG(ph.price) AS average_price FROM PriceHistory ph JOIN Product p ON OWNER(ph) = REF(p) GROUP BY REF(p), p.product_name HAVING MIN(ph.price) < MAX(ph.price);
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."price" AS "price",
        "source"."product_id" AS "__owner_0"
    FROM "relation_15" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    MIN("b0"."price") AS "minimum_price",
    MAX("b0"."price") AS "maximum_price",
    AVG("b0"."price") AS "average_price"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
GROUP BY
    "b1"."__reference_0",
    "b1"."product_name"
HAVING (MIN("b0"."price") < MAX("b0"."price"));

-- Q083 [aggregation] occurrence 1/1
-- Original E/R: SELECT c.email, COUNT(DISTINCT REF(r)) AS review_count, AVG(r.rating) AS average_rating FROM Review r JOIN Customer c ON OWNER(r) = REF(c) GROUP BY REF(c), c.email HAVING COUNT(DISTINCT REF(r)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."rating" AS "rating",
        "source"."customer_id" AS "__owner_0",
        "source"."customer_id" AS "__reference_0",
        "source"."review_id" AS "__reference_1"
    FROM "relation_21" AS "source"
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
)
SELECT 
    "b1"."email" AS "email",
    COUNT(DISTINCT ROW("b0"."__reference_0", "b0"."__reference_1")) AS "review_count",
    AVG("b0"."rating") AS "average_rating"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
GROUP BY
    "b1"."__reference_0",
    "b1"."email"
HAVING (COUNT(DISTINCT ROW("b0"."__reference_0", "b0"."__reference_1")) >= 2);

-- Q084 [aggregation] occurrence 1/1
-- Original E/R: SELECT p.promo_name, COUNT(DISTINCT REF(c)) AS coupon_count, MAX(c.max_uses) AS largest_limit FROM Coupon c JOIN Promotion p ON OWNER(c) = REF(p) GROUP BY REF(p), p.promo_name HAVING COUNT(DISTINCT REF(c)) > 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."max_uses" AS "max_uses",
        "source"."promotion_id" AS "__owner_0",
        "source"."promotion_id" AS "__reference_0",
        "source"."coupon_code" AS "__reference_1"
    FROM "relation_26" AS "source"
),
"b1" AS (
    SELECT
        "source"."promo_name" AS "promo_name",
        "source"."promotion_id" AS "__reference_0"
    FROM "relation_25" AS "source"
)
SELECT 
    "b1"."promo_name" AS "promo_name",
    COUNT(DISTINCT ROW("b0"."__reference_0", "b0"."__reference_1")) AS "coupon_count",
    MAX("b0"."max_uses") AS "largest_limit"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
GROUP BY
    "b1"."__reference_0",
    "b1"."promo_name"
HAVING (COUNT(DISTINCT ROW("b0"."__reference_0", "b0"."__reference_1")) > 1);

-- Q085 [aggregation] occurrence 1/1
-- Original E/R: SELECT cp.carrier_code, COUNT(DISTINCT REF(s)) AS shipment_count FROM courier_shipments cs JOIN CourierPartner cp ON ENDPOINT(cs, CourierPartner) = REF(cp) JOIN Shipment s ON ENDPOINT(cs, Shipment) = REF(s) GROUP BY REF(cp), cp.carrier_code HAVING COUNT(DISTINCT REF(s)) >= 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."courier_shipments_courierpartner_id" AS "__endpoint_courierpartner_0",
        "source"."custorder_id" AS "__endpoint_shipment_0",
        "source"."shipment_id" AS "__endpoint_shipment_1"
    FROM "relation_24" AS "source"
    WHERE ("source"."courier_shipments_courierpartner_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."carrier_code" AS "carrier_code",
        "source"."courierpartner_id" AS "__reference_0"
    FROM "relation_32" AS "source"
),
"b2" AS (
    SELECT
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_24" AS "source"
)
SELECT 
    "b1"."carrier_code" AS "carrier_code",
    COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) AS "shipment_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
GROUP BY
    "b1"."__reference_0",
    "b1"."carrier_code"
HAVING (COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) >= 5);

-- Q086 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT c.category_name, p.product_name, t.tag_name FROM category_products cp JOIN Category c ON ENDPOINT(cp, Category) = REF(c) JOIN Product p ON ENDPOINT(cp, Product) = REF(p) JOIN product_tags pt ON ENDPOINT(pt, Product) = REF(p) JOIN Tag t ON ENDPOINT(pt, Tag) = REF(t) WHERE p.is_active = 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."category_products_category_id" AS "__endpoint_category_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b1" AS (
    SELECT
        "source"."category_name" AS "category_name",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."tag_id" AS "__endpoint_tag_0"
    FROM "relation_34" AS "source"
),
"b4" AS (
    SELECT
        "source"."tag_name" AS "tag_name",
        "source"."tag_id" AS "__reference_0"
    FROM "relation_16" AS "source"
)
SELECT 
    "b1"."category_name" AS "category_name",
    "b2"."product_name" AS "product_name",
    "b4"."tag_name" AS "tag_name"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_tag_0" = "b4"."__reference_0"))
WHERE ("b2"."is_active" = 0);

-- Q087 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT s.supplier_name, p.product_name, c.category_name FROM supplier_products sp JOIN Supplier s ON ENDPOINT(sp, Supplier) = REF(s) JOIN Product p ON ENDPOINT(sp, Product) = REF(p) JOIN category_products cp ON ENDPOINT(cp, Product) = REF(p) JOIN Category c ON ENDPOINT(cp, Category) = REF(c) WHERE p.base_price > 187;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_44" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_29" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."category_products_category_id" AS "__endpoint_category_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b4" AS (
    SELECT
        "source"."category_name" AS "category_name",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
)
SELECT 
    "b1"."supplier_name" AS "supplier_name",
    "b2"."product_name" AS "product_name",
    "b4"."category_name" AS "category_name"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_category_0" = "b4"."__reference_0"))
WHERE ("b2"."base_price" > 187);

-- Q088 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT p.product_name, r.rating, r.title, c.email FROM reviews rv JOIN Product p ON ENDPOINT(rv, Product) = REF(p) JOIN Review r ON ENDPOINT(rv, Review) = REF(r) JOIN Customer c ON OWNER(r) = REF(c) WHERE r.rating >= 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."reviews_product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_review_0",
        "source"."review_id" AS "__endpoint_review_1"
    FROM "relation_39" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."rating" AS "rating",
        "source"."title" AS "title",
        "source"."customer_id" AS "__owner_0",
        "source"."customer_id" AS "__reference_0",
        "source"."review_id" AS "__reference_1"
    FROM "relation_21" AS "source"
),
"b3" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    "b2"."rating" AS "rating",
    "b2"."title" AS "title",
    "b3"."email" AS "email"
FROM ((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_review_0" = "b2"."__reference_0" AND "b0"."__endpoint_review_1" = "b2"."__reference_1")) INNER JOIN "b3" ON ("b2"."__owner_0" = "b3"."__reference_0"))
WHERE ("b2"."rating" >= 5);

-- Q089 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT c.email, o.status, p.product_name FROM customer_orders co JOIN Customer c ON ENDPOINT(co, Customer) = REF(c) JOIN CustOrder o ON ENDPOINT(co, CustOrder) = REF(o) JOIN order_items oi ON ENDPOINT(oi, CustOrder) = REF(o) JOIN Product p ON ENDPOINT(oi, Product) = REF(p) WHERE o.status = 'shipped';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_23" AS "source"
    WHERE ("source"."customer_orders_customer_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
),
"b2" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
),
"b3" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_40" AS "source"
),
"b4" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."email" AS "email",
    "b2"."status" AS "status",
    "b4"."product_name" AS "product_name"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_0" = "b4"."__reference_0"))
WHERE ("b2"."status" = 'shipped');

-- Q090 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT c.email, o.status, pm.brand, pm.last4 FROM customer_orders co JOIN Customer c ON ENDPOINT(co, Customer) = REF(c) JOIN CustOrder o ON ENDPOINT(co, CustOrder) = REF(o) JOIN payment_order po ON ENDPOINT(po, CustOrder) = REF(o) JOIN PaymentMethod pm ON ENDPOINT(po, PaymentMethod) = REF(pm) WHERE pm.is_default = 'true';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_23" AS "source"
    WHERE ("source"."customer_orders_customer_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
),
"b2" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
),
"b3" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."payment_order_customer_id" AS "__endpoint_paymentmethod_0",
        "source"."payment_order_payment_method_id" AS "__endpoint_paymentmethod_1"
    FROM "relation_23" AS "source"
    WHERE ("source"."payment_order_customer_id" IS NOT NULL) AND ("source"."payment_order_payment_method_id" IS NOT NULL)
),
"b4" AS (
    SELECT
        "source"."brand" AS "brand",
        "source"."is_default" AS "is_default",
        "source"."last4" AS "last4",
        "source"."customer_id" AS "__reference_0",
        "source"."payment_method_id" AS "__reference_1"
    FROM "relation_18" AS "source"
)
SELECT 
    "b1"."email" AS "email",
    "b2"."status" AS "status",
    "b4"."brand" AS "brand",
    "b4"."last4" AS "last4"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_paymentmethod_0" = "b4"."__reference_0" AND "b3"."__endpoint_paymentmethod_1" = "b4"."__reference_1"))
WHERE ("b4"."is_default" = 'true');

-- Q091 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT o.status, p.promo_name, c.max_uses FROM order_coupons oc JOIN CustOrder o ON ENDPOINT(oc, CustOrder) = REF(o) JOIN Coupon c ON ENDPOINT(oc, Coupon) = REF(c) JOIN Promotion p ON OWNER(c) = REF(p) WHERE p.discount_value IS NOT NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."promotion_id" AS "__endpoint_coupon_0",
        "source"."coupon_code" AS "__endpoint_coupon_1",
        "source"."order_coupons_custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_42" AS "source"
),
"b1" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
),
"b2" AS (
    SELECT
        "source"."max_uses" AS "max_uses",
        "source"."promotion_id" AS "__owner_0",
        "source"."promotion_id" AS "__reference_0",
        "source"."coupon_code" AS "__reference_1"
    FROM "relation_26" AS "source"
),
"b3" AS (
    SELECT
        "source"."discount_value" AS "discount_value",
        "source"."promo_name" AS "promo_name",
        "source"."promotion_id" AS "__reference_0"
    FROM "relation_25" AS "source"
)
SELECT 
    "b1"."status" AS "status",
    "b3"."promo_name" AS "promo_name",
    "b2"."max_uses" AS "max_uses"
FROM ((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_coupon_0" = "b2"."__reference_0" AND "b0"."__endpoint_coupon_1" = "b2"."__reference_1")) INNER JOIN "b3" ON ("b2"."__owner_0" = "b3"."__reference_0"))
WHERE ("b3"."discount_value" IS NOT NULL);

-- Q092 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT w.warehouse_name, b.code, p.product_name, c.category_name FROM stock st JOIN Product p ON ENDPOINT(st, Product) = REF(p) JOIN WarehouseBin b ON ENDPOINT(st, WarehouseBin) = REF(b) JOIN Warehouse w ON OWNER(b) = REF(w) JOIN category_products cp ON ENDPOINT(cp, Product) = REF(p) JOIN Category c ON ENDPOINT(cp, Category) = REF(c) WHERE w.region = 'Southwest';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."warehouse_id" AS "__endpoint_warehousebin_0",
        "source"."bin_id" AS "__endpoint_warehousebin_1"
    FROM "relation_43" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."code" AS "code",
        "source"."warehouse_id" AS "__owner_0",
        "source"."warehouse_id" AS "__reference_0",
        "source"."bin_id" AS "__reference_1"
    FROM "relation_28" AS "source"
),
"b3" AS (
    SELECT
        "source"."region" AS "region",
        "source"."warehouse_name" AS "warehouse_name",
        "source"."warehouse_id" AS "__reference_0"
    FROM "relation_27" AS "source"
),
"b4" AS (
    SELECT
        "source"."category_products_category_id" AS "__endpoint_category_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b5" AS (
    SELECT
        "source"."category_name" AS "category_name",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
)
SELECT 
    "b3"."warehouse_name" AS "warehouse_name",
    "b2"."code" AS "code",
    "b1"."product_name" AS "product_name",
    "b5"."category_name" AS "category_name"
FROM ((((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_warehousebin_0" = "b2"."__reference_0" AND "b0"."__endpoint_warehousebin_1" = "b2"."__reference_1")) INNER JOIN "b3" ON ("b2"."__owner_0" = "b3"."__reference_0")) INNER JOIN "b4" ON ("b4"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b5" ON ("b4"."__endpoint_category_0" = "b5"."__reference_0"))
WHERE ("b3"."region" = 'Southwest');

-- Q093 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT s.supplier_name, po.status, p.product_name FROM supplier_pos sp JOIN Supplier s ON ENDPOINT(sp, Supplier) = REF(s) JOIN PurchaseOrder po ON ENDPOINT(sp, PurchaseOrder) = REF(po) JOIN po_items pi ON ENDPOINT(pi, PurchaseOrder) = REF(po) JOIN Product p ON ENDPOINT(pi, Product) = REF(p) WHERE po.status = 'approved';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0",
        "source"."supplier_pos_supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_31" AS "source"
    WHERE ("source"."supplier_pos_supplier_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_29" AS "source"
),
"b2" AS (
    SELECT
        "source"."status" AS "status",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_31" AS "source"
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0"
    FROM "relation_45" AS "source"
),
"b4" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."supplier_name" AS "supplier_name",
    "b2"."status" AS "status",
    "b4"."product_name" AS "product_name"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_purchaseorder_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_purchaseorder_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_0" = "b4"."__reference_0"))
WHERE ("b2"."status" = 'approved');

-- Q094 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT cp.carrier_code, s.tracking_no, o.status FROM courier_shipments cs JOIN CourierPartner cp ON ENDPOINT(cs, CourierPartner) = REF(cp) JOIN Shipment s ON ENDPOINT(cs, Shipment) = REF(s) JOIN CustOrder o ON OWNER(s) = REF(o) WHERE s.delivered_at IS NULL;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."courier_shipments_courierpartner_id" AS "__endpoint_courierpartner_0",
        "source"."custorder_id" AS "__endpoint_shipment_0",
        "source"."shipment_id" AS "__endpoint_shipment_1"
    FROM "relation_24" AS "source"
    WHERE ("source"."courier_shipments_courierpartner_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."carrier_code" AS "carrier_code",
        "source"."courierpartner_id" AS "__reference_0"
    FROM "relation_32" AS "source"
),
"b2" AS (
    SELECT
        "source"."delivered_at" AS "delivered_at",
        "source"."tracking_no" AS "tracking_no",
        "source"."custorder_id" AS "__owner_0",
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_24" AS "source"
),
"b3" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
)
SELECT 
    "b1"."carrier_code" AS "carrier_code",
    "b2"."tracking_no" AS "tracking_no",
    "b3"."status" AS "status"
FROM ((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1")) INNER JOIN "b3" ON ("b2"."__owner_0" = "b3"."__reference_0"))
WHERE ("b2"."delivered_at" IS NULL);

-- Q095 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT p.product_name AS phone, a.product_name AS accessory, ph.price FROM bundled_phone_accessory bpa JOIN Phone p ON ENDPOINT(bpa, Phone) = REF(p) JOIN Accessory a ON ENDPOINT(bpa, Accessory) = REF(a) JOIN PriceHistory ph ON OWNER(ph) = REF(a) WHERE ph.price < a.base_price;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_id" AS "__endpoint_accessory_0",
        "source"."phone_id" AS "__endpoint_phone_0"
    FROM "relation_47" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "ancestor_0"."base_price" AS "base_price",
        "ancestor_0"."product_name" AS "product_name",
        "source"."accessory_id" AS "__reference_0"
    FROM "relation_6" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."accessory_id" = "ancestor_0"."product_id")
),
"b3" AS (
    SELECT
        "source"."price" AS "price",
        "source"."product_id" AS "__owner_0"
    FROM "relation_15" AS "source"
)
SELECT 
    "b1"."product_name" AS "phone",
    "b2"."product_name" AS "accessory",
    "b3"."price" AS "price"
FROM ((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_accessory_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__owner_0" = "b2"."__reference_0"))
WHERE ("b3"."price" < "b2"."base_price");

-- Q096 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT c.email, s.product_name, o.status FROM software_downloads sd JOIN Software s ON ENDPOINT(sd, Software) = REF(s) JOIN Customer c ON ENDPOINT(sd, Customer) = REF(c) LEFT JOIN customer_orders co ON ENDPOINT(co, Customer) = REF(c) LEFT JOIN CustOrder o ON ENDPOINT(co, CustOrder) = REF(o) WHERE s.is_active = 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_customer_0",
        "source"."software_id" AS "__endpoint_software_0"
    FROM "relation_48" AS "source"
),
"b1" AS (
    SELECT
        "ancestor_0"."is_active" AS "is_active",
        "ancestor_0"."product_name" AS "product_name",
        "source"."software_id" AS "__reference_0"
    FROM "relation_10" AS "source"
    INNER JOIN "relation_1" AS "ancestor_0" ON ("source"."software_id" = "ancestor_0"."product_id")
),
"b2" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
),
"b3" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_23" AS "source"
    WHERE ("source"."customer_orders_customer_id" IS NOT NULL)
),
"b4" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
)
SELECT 
    "b2"."email" AS "email",
    "b1"."product_name" AS "product_name",
    "b4"."status" AS "status"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_software_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_customer_0" = "b2"."__reference_0")) LEFT JOIN "b3" ON ("b3"."__endpoint_customer_0" = "b2"."__reference_0")) LEFT JOIN "b4" ON ("b3"."__endpoint_custorder_0" = "b4"."__reference_0"))
WHERE ("b1"."is_active" = 0);

-- Q097 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT p.product_name AS bundle, c.product_name AS component, t.tag_name FROM bundle_components bc JOIN Product p ON ENDPOINT(bc, product_id) = REF(p) JOIN Product c ON ENDPOINT(bc, bundle_product_id) = REF(c) JOIN product_tags pt ON ENDPOINT(pt, Product) = REF(c) JOIN Tag t ON ENDPOINT(pt, Tag) = REF(t) WHERE c.is_active = 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_product_product_id" AS "__endpoint_bundle_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_35" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."tag_id" AS "__endpoint_tag_0"
    FROM "relation_34" AS "source"
),
"b4" AS (
    SELECT
        "source"."tag_name" AS "tag_name",
        "source"."tag_id" AS "__reference_0"
    FROM "relation_16" AS "source"
)
SELECT 
    "b1"."product_name" AS "bundle",
    "b2"."product_name" AS "component",
    "b4"."tag_name" AS "tag_name"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bundle_product_id_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_tag_0" = "b4"."__reference_0"))
WHERE ("b2"."is_active" = 0);

-- Q098 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT p1.product_name, c1.category_name, p2.product_name, c2.category_name FROM bought_together bt JOIN Product p1 ON ENDPOINT(bt, product_id) = REF(p1) JOIN Product p2 ON ENDPOINT(bt, bought_together_product_id) = REF(p2) JOIN category_products cp1 ON ENDPOINT(cp1, Product) = REF(p1) JOIN Category c1 ON ENDPOINT(cp1, Category) = REF(c1) JOIN category_products cp2 ON ENDPOINT(cp2, Product) = REF(p2) JOIN Category c2 ON ENDPOINT(cp2, Category) = REF(c2);
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_36" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."category_products_category_id" AS "__endpoint_category_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b4" AS (
    SELECT
        "source"."category_name" AS "category_name",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
),
"b5" AS (
    SELECT
        "source"."category_products_category_id" AS "__endpoint_category_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b6" AS (
    SELECT
        "source"."category_name" AS "category_name",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    "b4"."category_name" AS "category_name",
    "b2"."product_name" AS "product_name",
    "b6"."category_name" AS "category_name"
FROM (((((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bought_together_product_id_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_category_0" = "b4"."__reference_0")) INNER JOIN "b5" ON ("b5"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b6" ON ("b5"."__endpoint_category_0" = "b6"."__reference_0"));

-- Q099 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT c.email, cart.updated_at, p.product_name, pv.barcode FROM Cart cart JOIN Customer c ON OWNER(cart) = REF(c) JOIN cart_contains cc ON ENDPOINT(cc, Cart) = REF(cart) JOIN Product p ON ENDPOINT(cc, Product) = REF(p) LEFT JOIN ProductVariant pv ON OWNER(pv) = REF(p) WHERE p.quantity > 38;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."updated_at" AS "updated_at",
        "source"."customer_id" AS "__owner_0",
        "source"."customer_id" AS "__reference_0",
        "source"."cart_id" AS "__reference_1"
    FROM "relation_19" AS "source"
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
),
"b2" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_cart_0",
        "source"."cart_id" AS "__endpoint_cart_1",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_37" AS "source"
),
"b3" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b4" AS (
    SELECT
        "source"."barcode" AS "barcode",
        "source"."product_id" AS "__owner_0"
    FROM "relation_14" AS "source"
)
SELECT 
    "b1"."email" AS "email",
    "b0"."updated_at" AS "updated_at",
    "b3"."product_name" AS "product_name",
    "b4"."barcode" AS "barcode"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b2"."__endpoint_cart_0" = "b0"."__reference_0" AND "b2"."__endpoint_cart_1" = "b0"."__reference_1")) INNER JOIN "b3" ON ("b2"."__endpoint_product_0" = "b3"."__reference_0")) LEFT JOIN "b4" ON ("b4"."__owner_0" = "b3"."__reference_0"))
WHERE ("b3"."quantity" > 38);

-- Q100 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT c.email, COUNT(DISTINCT REF(o)) AS order_count, COUNT(DISTINCT REF(p)) AS product_count, AVG(p.base_price) AS average_product_price FROM customer_orders co JOIN Customer c ON ENDPOINT(co, Customer) = REF(c) JOIN CustOrder o ON ENDPOINT(co, CustOrder) = REF(o) JOIN order_items oi ON ENDPOINT(oi, CustOrder) = REF(o) JOIN Product p ON ENDPOINT(oi, Product) = REF(p) WHERE o.status <> 'delivered' GROUP BY REF(c), c.email HAVING COUNT(DISTINCT REF(o)) >= 2 AND AVG(p.base_price) > 50;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_23" AS "source"
    WHERE ("source"."customer_orders_customer_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."customer_id" AS "__reference_0"
    FROM "relation_12" AS "source"
),
"b2" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_23" AS "source"
),
"b3" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_40" AS "source"
),
"b4" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."email" AS "email",
    COUNT(DISTINCT "b2"."__reference_0") AS "order_count",
    COUNT(DISTINCT "b4"."__reference_0") AS "product_count",
    AVG("b4"."base_price") AS "average_product_price"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_0" = "b4"."__reference_0"))
WHERE ("b2"."status" <> 'delivered')
GROUP BY
    "b1"."__reference_0",
    "b1"."email"
HAVING ((COUNT(DISTINCT "b2"."__reference_0") >= 2) AND (AVG("b4"."base_price") > 50));

ROLLBACK;
