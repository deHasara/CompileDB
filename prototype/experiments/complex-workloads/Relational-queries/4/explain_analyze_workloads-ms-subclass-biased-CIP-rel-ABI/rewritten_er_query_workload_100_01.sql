\set ON_ERROR_STOP on
\pset pager off
-- CompileDB mapping-aware relational workload
-- Conceptual workload: example2_schema_driven_selectivity_100_w01
-- Mapping ID: f015fd00db116d7c19ae94a5f40a6e34250534220293ca53b7b6086b1499e981
-- Query shapes: 100
-- Executed statements: 100
BEGIN TRANSACTION READ ONLY;

-- Q001 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.base_price, e2.quantity, e3.code FROM bought_together r1 JOIN Product e1 ON ENDPOINT(r1, bought_together_product_id) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, product_id) = REF(e2) JOIN stock r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN WarehouseBin e3 ON ENDPOINT(r2, WarehouseBin) = REF(e3) WHERE e2.product_id >= 1668483;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_26" AS "source"
),
"b1" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."warehouse_id" AS "__endpoint_warehousebin_0",
        "source"."bin_id" AS "__endpoint_warehousebin_1"
    FROM "relation_35" AS "source"
),
"b4" AS (
    SELECT
        "source"."code" AS "code",
        "source"."warehouse_id" AS "__reference_0",
        "source"."bin_id" AS "__reference_1"
    FROM "relation_18" AS "source"
)
SELECT 
    "b1"."base_price" AS "base_price",
    "b2"."quantity" AS "quantity",
    "b4"."code" AS "code"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_bought_together_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_id_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_warehousebin_0" = "b4"."__reference_0" AND "b3"."__endpoint_warehousebin_1" = "b4"."__reference_1"))
WHERE ("b2"."product_id" >= 1668483);

-- Q002 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.sku, e2.status, e3.supplier_id FROM po_items r1 JOIN PhysicalProduct e1 ON ENDPOINT(r1, Product) = REF(e1) JOIN PurchaseOrder e2 ON ENDPOINT(r1, PurchaseOrder) = REF(e2) JOIN supplier_pos r2 ON ENDPOINT(r2, PurchaseOrder) = REF(e2) JOIN Supplier e3 ON ENDPOINT(r2, Supplier) = REF(e3) WHERE e2.created_at < '2025-03-20';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0"
    FROM "relation_38" AS "source"
),
"b1" AS (
    SELECT
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
),
"b2" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."status" AS "status",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
),
"b3" AS (
    SELECT
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0",
        "source"."supplier_pos_supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_37" AS "source"
),
"b4" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
)
SELECT 
    "b1"."sku" AS "sku",
    "b2"."status" AS "status",
    "b4"."supplier_id" AS "supplier_id"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_purchaseorder_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_purchaseorder_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_supplier_0" = "b4"."__reference_0"))
WHERE ("b2"."created_at" < '2025-03-20');

-- Q003 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.accessory_type, e2.supplier_name, e3.status FROM supplier_products r1 JOIN Accessory e1 ON ENDPOINT(r1, Product) = REF(e1) JOIN Supplier e2 ON ENDPOINT(r1, Supplier) = REF(e2) JOIN supplier_pos r2 ON ENDPOINT(r2, Supplier) = REF(e2) JOIN PurchaseOrder e3 ON ENDPOINT(r2, PurchaseOrder) = REF(e3) WHERE e1.accessory_type < 'headset';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_36" AS "source"
),
"b1" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
),
"b2" AS (
    SELECT
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b3" AS (
    SELECT
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0",
        "source"."supplier_pos_supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_37" AS "source"
),
"b4" AS (
    SELECT
        "source"."status" AS "status",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
)
SELECT 
    "b1"."accessory_type" AS "accessory_type",
    "b2"."supplier_name" AS "supplier_name",
    "b4"."status" AS "status"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_supplier_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_supplier_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_purchaseorder_0" = "b4"."__reference_0"))
WHERE ("b1"."accessory_type" < 'headset');

-- Q004 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.body, COUNT(DISTINCT REF(e1)) AS related_count FROM reviews r JOIN PhysicalProduct e1 ON ENDPOINT(r, Product) = REF(e1) JOIN Review e2 ON ENDPOINT(r, Review) = REF(e2) WHERE e2.rating > 1 GROUP BY REF(e2), e2.body HAVING COUNT(DISTINCT REF(e1)) >= 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."reviews_product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_review_0",
        "source"."review_id" AS "__endpoint_review_1"
    FROM "relation_29" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
),
"b2" AS (
    SELECT
        "source"."body" AS "body",
        "source"."rating" AS "rating",
        "source"."user_id" AS "__reference_0",
        "source"."review_id" AS "__reference_1"
    FROM "relation_11" AS "source"
)
SELECT 
    "b2"."body" AS "body",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_review_0" = "b2"."__reference_0" AND "b0"."__endpoint_review_1" = "b2"."__reference_1"))
WHERE ("b2"."rating" > 1)
GROUP BY
    "b2"."__reference_0",
    "b2"."__reference_1",
    "b2"."body"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 5);

-- Q005 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.dimensions FROM Laptop e WHERE e.sku < 'SKU-ugyy-86730684';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."sku" < 'SKU-ugyy-86730684');

-- Q006 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.ends_at, w.price_id, w.starts_at FROM PriceHistory w WHERE w.price <= 136;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ends_at" AS "ends_at",
        "source"."price" AS "price",
        "source"."price_id" AS "price_id",
        "source"."starts_at" AS "starts_at"
    FROM "relation_5" AS "source"
)
SELECT 
    "b0"."ends_at" AS "ends_at",
    "b0"."price_id" AS "price_id",
    "b0"."starts_at" AS "starts_at"
FROM "b0"
WHERE ("b0"."price" <= 136);

-- Q007 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.base_price, e.sku, e.band_size FROM Smartwatch e WHERE e.base_price >= 121;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku",
        "source"."band_size" AS "band_size"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."base_price" AS "base_price",
    "b0"."sku" AS "sku",
    "b0"."band_size" AS "band_size"
FROM "b0"
WHERE ("b0"."base_price" >= 121);

-- Q008 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.product_name, e.sole_material FROM Footwear e WHERE e.quantity < 23;
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
WHERE ("b0"."quantity" < 23);

-- Q009 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.created_at, e2.base_price, e3.status FROM po_items r1 JOIN PurchaseOrder e1 ON ENDPOINT(r1, PurchaseOrder) = REF(e1) JOIN KitchenAppliance e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN order_returns r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN CustOrder e3 ON ENDPOINT(r2, CustOrder) = REF(e3) WHERE e2.is_active < 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0"
    FROM "relation_38" AS "source"
),
"b1" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
),
"b3" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b4" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b1"."created_at" AS "created_at",
    "b2"."base_price" AS "base_price",
    "b4"."status" AS "status"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_purchaseorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_custorder_0" = "b4"."__reference_0"))
WHERE ("b2"."is_active" < 1);

-- Q010 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.base_price, COUNT(DISTINCT REF(e1)) AS related_count FROM wishlist_contains r JOIN Wishlist e1 ON ENDPOINT(r, Wishlist) = REF(e1) JOIN PhysicalProduct e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.wishlist_name > 'default' GROUP BY REF(e2), e2.base_price HAVING COUNT(DISTINCT REF(e1)) >= 4;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_wishlist_0",
        "source"."wishlist_id" AS "__endpoint_wishlist_1"
    FROM "relation_28" AS "source"
),
"b1" AS (
    SELECT
        "source"."wishlist_name" AS "wishlist_name",
        "source"."user_id" AS "__reference_0",
        "source"."wishlist_id" AS "__reference_1"
    FROM "relation_10" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b2"."base_price" AS "base_price",
    COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_wishlist_0" = "b1"."__reference_0" AND "b0"."__endpoint_wishlist_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."wishlist_name" > 'default')
GROUP BY
    "b2"."__reference_0",
    "b2"."base_price"
HAVING (COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) >= 4);

-- Q011 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.energy_rating, e.sku, e.base_price FROM Appliance e WHERE e.product_id <= 13130552;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."energy_rating" AS "energy_rating",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('appliance', 'kitchenappliance'))
)
SELECT 
    "b0"."energy_rating" AS "energy_rating",
    "b0"."sku" AS "sku",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."product_id" <= 13130552);

-- Q012 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.placed_at, e2.per_user_limit, e2.coupon_code FROM order_coupons r JOIN CustOrder e1 ON ENDPOINT(r, CustOrder) = REF(e1) JOIN Coupon e2 ON ENDPOINT(r, Coupon) = REF(e2) WHERE e2.max_uses > 369;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."promotion_id" AS "__endpoint_coupon_0",
        "source"."coupon_code" AS "__endpoint_coupon_1",
        "source"."order_coupons_custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_34" AS "source"
),
"b1" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
),
"b2" AS (
    SELECT
        "source"."coupon_code" AS "coupon_code",
        "source"."max_uses" AS "max_uses",
        "source"."per_user_limit" AS "per_user_limit",
        "source"."promotion_id" AS "__reference_0",
        "source"."coupon_code" AS "__reference_1"
    FROM "relation_16" AS "source"
)
SELECT 
    "b1"."placed_at" AS "placed_at",
    "b2"."per_user_limit" AS "per_user_limit",
    "b2"."coupon_code" AS "coupon_code"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_coupon_0" = "b2"."__reference_0" AND "b0"."__endpoint_coupon_1" = "b2"."__reference_1"))
WHERE ("b2"."max_uses" > 369);

-- Q013 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity FROM Accessory e WHERE e.product_name >= 'Object-based regional structure';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."product_name" >= 'Object-based regional structure');

-- Q014 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system, e.is_active FROM MenClothing e WHERE e.material > 'cotton';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."material" AS "material",
        "source"."is_active" AS "is_active"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."size_system" AS "size_system",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."material" > 'cotton');

-- Q015 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.category_id, COUNT(DISTINCT REF(e2)) AS related_count FROM category_products r JOIN Category e1 ON ENDPOINT(r, Category) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.product_name <= 'Total needs-based product' GROUP BY REF(e1), e1.category_id HAVING COUNT(DISTINCT REF(e2)) >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."category_products_category_id" AS "__endpoint_category_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_23" AS "source"
),
"b1" AS (
    SELECT
        "source"."category_id" AS "category_id",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."category_id" AS "category_id",
    COUNT(DISTINCT "b2"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."product_name" <= 'Total needs-based product')
GROUP BY
    "b1"."__reference_0",
    "b1"."category_id"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 1);

-- Q016 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.email, COUNT(DISTINCT REF(e2)) AS related_count FROM customer_orders r JOIN Customer e1 ON ENDPOINT(r, Customer) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.user_id > 695679 GROUP BY REF(e1), e1.email HAVING COUNT(DISTINCT REF(e2)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_30" AS "source"
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."user_id" AS "user_id",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
),
"b2" AS (
    SELECT
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b1"."email" AS "email",
    COUNT(DISTINCT "b2"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."user_id" > 695679)
GROUP BY
    "b1"."__reference_0",
    "b1"."email"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 2);

-- Q017 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.max_uses, e2.placed_at, e3.warranty_months FROM order_coupons r1 JOIN Coupon e1 ON ENDPOINT(r1, Coupon) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r1, CustOrder) = REF(e2) JOIN order_returns r2 ON ENDPOINT(r2, CustOrder) = REF(e2) JOIN Camera e3 ON ENDPOINT(r2, Product) = REF(e3) WHERE e3.sku >= 'SKU-aMkd-32417538';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."promotion_id" AS "__endpoint_coupon_0",
        "source"."coupon_code" AS "__endpoint_coupon_1",
        "source"."order_coupons_custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_34" AS "source"
),
"b1" AS (
    SELECT
        "source"."max_uses" AS "max_uses",
        "source"."promotion_id" AS "__reference_0",
        "source"."coupon_code" AS "__reference_1"
    FROM "relation_16" AS "source"
),
"b2" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
),
"b3" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b4" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b1"."max_uses" AS "max_uses",
    "b2"."placed_at" AS "placed_at",
    "b4"."warranty_months" AS "warranty_months"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_coupon_0" = "b1"."__reference_0" AND "b0"."__endpoint_coupon_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_0" = "b4"."__reference_0"))
WHERE ("b4"."sku" >= 'SKU-aMkd-32417538');

-- Q018 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.sort_order, w.url, o.is_active, o.dimensions FROM ProductImage w JOIN Computer o ON OWNER(w) = REF(o) WHERE w.sort_order < 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."sort_order" AS "sort_order",
        "source"."url" AS "url",
        "source"."product_id" AS "__owner_0"
    FROM "relation_3" AS "source"
),
"b1" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('computer', 'desktop', 'laptop'))
)
SELECT 
    "b0"."sort_order" AS "sort_order",
    "b0"."url" AS "url",
    "b1"."is_active" AS "is_active",
    "b1"."dimensions" AS "dimensions"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."sort_order" < 3);

-- Q019 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.city, o.password_hash FROM Address w JOIN Customer o ON OWNER(w) = REF(o) WHERE w.country >= 'FR';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."city" AS "city",
        "source"."country" AS "country",
        "source"."user_id" AS "__owner_0"
    FROM "relation_7" AS "source"
),
"b1" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."city" AS "city",
    "b1"."password_hash" AS "password_hash"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."country" >= 'FR');

-- Q020 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.supplier_id, e1.supplier_name, e2.quantity, e2.sku FROM supplier_products r JOIN Supplier e1 ON ENDPOINT(r, Supplier) = REF(e1) JOIN WomenClothing e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.fit_type_women > 'plus';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_36" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b2" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku",
        "source"."fit_type_women" AS "fit_type_women",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b1"."supplier_id" AS "supplier_id",
    "b1"."supplier_name" AS "supplier_name",
    "b2"."quantity" AS "quantity",
    "b2"."sku" AS "sku"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."fit_type_women" > 'plus');

-- Q021 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.cart_id, COUNT(DISTINCT REF(e2)) AS related_count FROM cart_contains r JOIN Cart e1 ON ENDPOINT(r, Cart) = REF(e1) JOIN DigitalProduct e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.is_active <= 0 GROUP BY REF(e1), e1.cart_id HAVING COUNT(DISTINCT REF(e2)) >= 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_cart_0",
        "source"."cart_id" AS "__endpoint_cart_1",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_27" AS "source"
),
"b1" AS (
    SELECT
        "source"."cart_id" AS "cart_id",
        "source"."user_id" AS "__reference_0",
        "source"."cart_id" AS "__reference_1"
    FROM "relation_9" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('digitalproduct', 'media', 'software'))
)
SELECT 
    "b1"."cart_id" AS "cart_id",
    COUNT(DISTINCT "b2"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_cart_0" = "b1"."__reference_0" AND "b0"."__endpoint_cart_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."is_active" <= 0)
GROUP BY
    "b1"."__reference_0",
    "b1"."__reference_1",
    "b1"."cart_id"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 3);

-- Q022 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.wishlist_id, w.wishlist_name, o.password_hash FROM Wishlist w JOIN Customer o ON OWNER(w) = REF(o) WHERE o.loyalty_tier >= 'gold';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."wishlist_id" AS "wishlist_id",
        "source"."wishlist_name" AS "wishlist_name",
        "source"."user_id" AS "__owner_0"
    FROM "relation_10" AS "source"
),
"b1" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."wishlist_id" AS "wishlist_id",
    "b0"."wishlist_name" AS "wishlist_name",
    "b1"."password_hash" AS "password_hash"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."loyalty_tier" >= 'gold');

-- Q023 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.address_id, w.kind, o.password_hash FROM Address w JOIN Customer o ON OWNER(w) = REF(o) WHERE o.password_hash > '7f492fe17bafb6e2cb231681b2221c5e2ef3d496053bb9b1ea13a7c897e71ef5';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."address_id" AS "address_id",
        "source"."kind" AS "kind",
        "source"."user_id" AS "__owner_0"
    FROM "relation_7" AS "source"
),
"b1" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."address_id" AS "address_id",
    "b0"."kind" AS "kind",
    "b1"."password_hash" AS "password_hash"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."password_hash" > '7f492fe17bafb6e2cb231681b2221c5e2ef3d496053bb9b1ea13a7c897e71ef5');

-- Q024 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.placed_at, COUNT(DISTINCT REF(e3)) AS related_count FROM order_coupons r1 JOIN Coupon e1 ON ENDPOINT(r1, Coupon) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r1, CustOrder) = REF(e2) JOIN order_items r2 ON ENDPOINT(r2, CustOrder) = REF(e2) JOIN Software e3 ON ENDPOINT(r2, Product) = REF(e3) WHERE e2.placed_at < '2025-08-26' GROUP BY REF(e2), e2.placed_at HAVING COUNT(DISTINCT REF(e3)) >= 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."promotion_id" AS "__endpoint_coupon_0",
        "source"."coupon_code" AS "__endpoint_coupon_1",
        "source"."order_coupons_custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_34" AS "source"
),
"b1" AS (
    SELECT
        "source"."promotion_id" AS "__reference_0",
        "source"."coupon_code" AS "__reference_1"
    FROM "relation_16" AS "source"
),
"b2" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
),
"b3" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_31" AS "source"
),
"b4" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT 
    "b2"."placed_at" AS "placed_at",
    COUNT(DISTINCT "b4"."__reference_0") AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_coupon_0" = "b1"."__reference_0" AND "b0"."__endpoint_coupon_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_0" = "b4"."__reference_0"))
WHERE ("b2"."placed_at" < '2025-08-26')
GROUP BY
    "b2"."__reference_0",
    "b2"."placed_at"
HAVING (COUNT(DISTINCT "b4"."__reference_0") >= 5);

-- Q025 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.email, o.supplier_id, o.supplier_name FROM SupplierContact w JOIN Supplier o ON OWNER(w) = REF(o) WHERE w.email >= 'cochranjared@example.com';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."email" AS "email",
        "source"."supplier_id" AS "__owner_0"
    FROM "relation_20" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
)
SELECT 
    "b0"."email" AS "email",
    "b1"."supplier_id" AS "supplier_id",
    "b1"."supplier_name" AS "supplier_name"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."email" >= 'cochranjared@example.com');

-- Q026 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.contact_id, w.phone, w.email, o.supplier_id FROM SupplierContact w JOIN Supplier o ON OWNER(w) = REF(o) WHERE w.contact_id > 3017052;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."contact_id" AS "contact_id",
        "source"."email" AS "email",
        "source"."phone" AS "phone",
        "source"."supplier_id" AS "__owner_0"
    FROM "relation_20" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
)
SELECT 
    "b0"."contact_id" AS "contact_id",
    "b0"."phone" AS "phone",
    "b0"."email" AS "email",
    "b1"."supplier_id" AS "supplier_id"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."contact_id" > 3017052);

-- Q027 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash, e.email, e.user_id FROM User e WHERE e.user_id > 304726;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
)
SELECT 
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."user_id" > 304726);

-- Q028 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.sku, e1.is_active, e2.title FROM reviews r JOIN Product e1 ON ENDPOINT(r, Product) = REF(e1) JOIN Review e2 ON ENDPOINT(r, Review) = REF(e2) WHERE e1.base_price < 149;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."reviews_product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_review_0",
        "source"."review_id" AS "__endpoint_review_1"
    FROM "relation_29" AS "source"
),
"b1" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."title" AS "title",
        "source"."user_id" AS "__reference_0",
        "source"."review_id" AS "__reference_1"
    FROM "relation_11" AS "source"
)
SELECT 
    "b1"."sku" AS "sku",
    "b1"."is_active" AS "is_active",
    "b2"."title" AS "title"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_review_0" = "b2"."__reference_0" AND "b0"."__endpoint_review_1" = "b2"."__reference_1"))
WHERE ("b1"."base_price" < 149);

-- Q029 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.brand, e2.custorder_id, e2.placed_at FROM payment_order r JOIN PaymentMethod e1 ON ENDPOINT(r, PaymentMethod) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.exp_year <= 2029;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."payment_order_customer_id" AS "__endpoint_paymentmethod_0",
        "source"."payment_order_payment_method_id" AS "__endpoint_paymentmethod_1"
    FROM "relation_32" AS "source"
),
"b1" AS (
    SELECT
        "source"."brand" AS "brand",
        "source"."exp_year" AS "exp_year",
        "source"."user_id" AS "__reference_0",
        "source"."payment_method_id" AS "__reference_1"
    FROM "relation_8" AS "source"
),
"b2" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."placed_at" AS "placed_at",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b1"."brand" AS "brand",
    "b2"."custorder_id" AS "custorder_id",
    "b2"."placed_at" AS "placed_at"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_paymentmethod_0" = "b1"."__reference_0" AND "b0"."__endpoint_paymentmethod_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."exp_year" <= 2029);

-- Q030 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.supplier_name, e1.supplier_id, e2.created_at FROM supplier_pos r JOIN Supplier e1 ON ENDPOINT(r, Supplier) = REF(e1) JOIN PurchaseOrder e2 ON ENDPOINT(r, PurchaseOrder) = REF(e2) WHERE e2.purchaseorder_id < 120363;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0",
        "source"."supplier_pos_supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_37" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b2" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."purchaseorder_id" AS "purchaseorder_id",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
)
SELECT 
    "b1"."supplier_name" AS "supplier_name",
    "b1"."supplier_id" AS "supplier_id",
    "b2"."created_at" AS "created_at"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_purchaseorder_0" = "b2"."__reference_0"))
WHERE ("b2"."purchaseorder_id" < 120363);

-- Q031 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.carrier_lock, e2.base_price FROM bundle_phones r JOIN Phone e1 ON ENDPOINT(r, phone_id) = REF(e1) JOIN Phone e2 ON ENDPOINT(r, bundle_phone_id) = REF(e2) WHERE e1.carrier_lock <= 'unlocked';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_phone_phone_id" AS "__endpoint_bundle_phone_id_0",
        "source"."phone_id" AS "__endpoint_phone_id_0"
    FROM "relation_40" AS "source"
),
"b1" AS (
    SELECT
        "source"."carrier_lock" AS "carrier_lock",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b1"."carrier_lock" AS "carrier_lock",
    "b2"."base_price" AS "base_price"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bundle_phone_id_0" = "b2"."__reference_0"))
WHERE ("b1"."carrier_lock" <= 'unlocked');

-- Q032 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.sku, e1.product_id, e2.rating, e2.created_at FROM reviews r JOIN Product e1 ON ENDPOINT(r, Product) = REF(e1) JOIN Review e2 ON ENDPOINT(r, Review) = REF(e2) WHERE e1.quantity < 86;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."reviews_product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_review_0",
        "source"."review_id" AS "__endpoint_review_1"
    FROM "relation_29" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."rating" AS "rating",
        "source"."user_id" AS "__reference_0",
        "source"."review_id" AS "__reference_1"
    FROM "relation_11" AS "source"
)
SELECT 
    "b1"."sku" AS "sku",
    "b1"."product_id" AS "product_id",
    "b2"."rating" AS "rating",
    "b2"."created_at" AS "created_at"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_review_0" = "b2"."__reference_0" AND "b0"."__endpoint_review_1" = "b2"."__reference_1"))
WHERE ("b1"."quantity" < 86);

-- Q033 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.status, e1.placed_at, e2.per_user_limit, e2.max_uses FROM order_coupons r JOIN CustOrder e1 ON ENDPOINT(r, CustOrder) = REF(e1) JOIN Coupon e2 ON ENDPOINT(r, Coupon) = REF(e2) WHERE e2.coupon_code <= 6962508;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."promotion_id" AS "__endpoint_coupon_0",
        "source"."coupon_code" AS "__endpoint_coupon_1",
        "source"."order_coupons_custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_34" AS "source"
),
"b1" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
),
"b2" AS (
    SELECT
        "source"."coupon_code" AS "coupon_code",
        "source"."max_uses" AS "max_uses",
        "source"."per_user_limit" AS "per_user_limit",
        "source"."promotion_id" AS "__reference_0",
        "source"."coupon_code" AS "__reference_1"
    FROM "relation_16" AS "source"
)
SELECT 
    "b1"."status" AS "status",
    "b1"."placed_at" AS "placed_at",
    "b2"."per_user_limit" AS "per_user_limit",
    "b2"."max_uses" AS "max_uses"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_coupon_0" = "b2"."__reference_0" AND "b0"."__endpoint_coupon_1" = "b2"."__reference_1"))
WHERE ("b2"."coupon_code" <= 6962508);

-- Q034 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.created_at, e2.supplier_id, e3.dimensions FROM supplier_pos r1 JOIN PurchaseOrder e1 ON ENDPOINT(r1, PurchaseOrder) = REF(e1) JOIN Supplier e2 ON ENDPOINT(r1, Supplier) = REF(e2) JOIN supplier_products r2 ON ENDPOINT(r2, Supplier) = REF(e2) JOIN PhysicalProduct e3 ON ENDPOINT(r2, Product) = REF(e3) WHERE e2.supplier_name >= 'Brown-Hernandez';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0",
        "source"."supplier_pos_supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_37" AS "source"
),
"b1" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
),
"b2" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_36" AS "source"
),
"b4" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b1"."created_at" AS "created_at",
    "b2"."supplier_id" AS "supplier_id",
    "b4"."dimensions" AS "dimensions"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_purchaseorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_supplier_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_supplier_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_0" = "b4"."__reference_0"))
WHERE ("b2"."supplier_name" >= 'Brown-Hernandez');

-- Q035 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.employee_no, e.user_id, e.password_hash, e.email FROM Employee e WHERE e.email <= 'scontreras@example.net';
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
    "b0"."user_id" AS "user_id",
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."email" <= 'scontreras@example.net');

-- Q036 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.supplier_id, e1.supplier_name, e2.is_active FROM supplier_products r JOIN Supplier e1 ON ENDPOINT(r, Supplier) = REF(e1) JOIN Smartwatch e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.supplier_name <= 'Levy, Burns and Davis';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_36" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b1"."supplier_id" AS "supplier_id",
    "b1"."supplier_name" AS "supplier_name",
    "b2"."is_active" AS "is_active"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."supplier_name" <= 'Levy, Burns and Davis');

-- Q037 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.accessory_type, e.product_name, e.warranty_months FROM Accessory e WHERE e.sku <= 'SKU-uhaA-69151410';
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
WHERE ("b0"."sku" <= 'SKU-uhaA-69151410');

-- Q038 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.status, COUNT(DISTINCT REF(e1)) AS related_count FROM payment_order r JOIN PaymentMethod e1 ON ENDPOINT(r, PaymentMethod) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.brand < 'Visa' GROUP BY REF(e2), e2.status HAVING COUNT(DISTINCT REF(e1)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."payment_order_customer_id" AS "__endpoint_paymentmethod_0",
        "source"."payment_order_payment_method_id" AS "__endpoint_paymentmethod_1"
    FROM "relation_32" AS "source"
),
"b1" AS (
    SELECT
        "source"."brand" AS "brand",
        "source"."user_id" AS "__reference_0",
        "source"."payment_method_id" AS "__reference_1"
    FROM "relation_8" AS "source"
),
"b2" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b2"."status" AS "status",
    COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_paymentmethod_0" = "b1"."__reference_0" AND "b0"."__endpoint_paymentmethod_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."brand" < 'Visa')
GROUP BY
    "b2"."__reference_0",
    "b2"."status"
HAVING (COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) >= 2);

-- Q039 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.email, o.supplier_id FROM SupplierContact w JOIN Supplier o ON OWNER(w) = REF(o) WHERE o.supplier_id > 20894;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."email" AS "email",
        "source"."supplier_id" AS "__owner_0"
    FROM "relation_20" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
)
SELECT 
    "b0"."email" AS "email",
    "b1"."supplier_id" AS "supplier_id"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."supplier_id" > 20894);

-- Q040 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.carrier_code, e1.webhook_url, e2.shipment_id FROM courier_shipments r JOIN CourierPartner e1 ON ENDPOINT(r, CourierPartner) = REF(e1) JOIN Shipment e2 ON ENDPOINT(r, Shipment) = REF(e2) WHERE e2.shipment_id <= 5047940;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."courier_shipments_courierpartner_id" AS "__endpoint_courierpartner_0",
        "source"."custorder_id" AS "__endpoint_shipment_0",
        "source"."shipment_id" AS "__endpoint_shipment_1"
    FROM "relation_39" AS "source"
),
"b1" AS (
    SELECT
        "source"."carrier_code" AS "carrier_code",
        "source"."webhook_url" AS "webhook_url",
        "source"."courierpartner_id" AS "__reference_0"
    FROM "relation_22" AS "source"
),
"b2" AS (
    SELECT
        "source"."shipment_id" AS "shipment_id",
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_14" AS "source"
)
SELECT 
    "b1"."carrier_code" AS "carrier_code",
    "b1"."webhook_url" AS "webhook_url",
    "b2"."shipment_id" AS "shipment_id"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
WHERE ("b2"."shipment_id" <= 5047940);

-- Q041 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.product_id, COUNT(DISTINCT REF(e1)) AS related_count FROM wishlist_contains r JOIN Wishlist e1 ON ENDPOINT(r, Wishlist) = REF(e1) JOIN Desktop e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.base_price > 119 GROUP BY REF(e2), e2.product_id HAVING COUNT(DISTINCT REF(e1)) >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_wishlist_0",
        "source"."wishlist_id" AS "__endpoint_wishlist_1"
    FROM "relation_28" AS "source"
),
"b1" AS (
    SELECT
        "source"."user_id" AS "__reference_0",
        "source"."wishlist_id" AS "__reference_1"
    FROM "relation_10" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b2"."product_id" AS "product_id",
    COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_wishlist_0" = "b1"."__reference_0" AND "b0"."__endpoint_wishlist_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."base_price" > 119)
GROUP BY
    "b2"."__reference_0",
    "b2"."product_id"
HAVING (COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) >= 1);

-- Q042 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.updated_at, e2.dimensions FROM cart_contains r JOIN Cart e1 ON ENDPOINT(r, Cart) = REF(e1) JOIN Footwear e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.base_price <= 148;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_cart_0",
        "source"."cart_id" AS "__endpoint_cart_1",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_27" AS "source"
),
"b1" AS (
    SELECT
        "source"."updated_at" AS "updated_at",
        "source"."user_id" AS "__reference_0",
        "source"."cart_id" AS "__reference_1"
    FROM "relation_9" AS "source"
),
"b2" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b1"."updated_at" AS "updated_at",
    "b2"."dimensions" AS "dimensions"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_cart_0" = "b1"."__reference_0" AND "b0"."__endpoint_cart_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."base_price" <= 148);

-- Q043 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.product_name, e2.tag_name FROM product_tags r JOIN Product e1 ON ENDPOINT(r, Product) = REF(e1) JOIN Tag e2 ON ENDPOINT(r, Tag) = REF(e2) WHERE e2.tag_name >= 'popular';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."tag_id" AS "__endpoint_tag_0"
    FROM "relation_24" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."tag_name" AS "tag_name",
        "source"."tag_id" AS "__reference_0"
    FROM "relation_6" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    "b2"."tag_name" AS "tag_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_tag_0" = "b2"."__reference_0"))
WHERE ("b2"."tag_name" >= 'popular');

-- Q044 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.session_id, w.started_at FROM BrowsingSession w WHERE w.session_id > 937408;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."session_id" AS "session_id",
        "source"."started_at" AS "started_at"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."session_id" AS "session_id",
    "b0"."started_at" AS "started_at"
FROM "b0"
WHERE ("b0"."session_id" > 937408);

-- Q045 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.placed_at, COUNT(DISTINCT REF(e3)) AS related_count FROM order_returns r1 JOIN Product e1 ON ENDPOINT(r1, Product) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r1, CustOrder) = REF(e2) JOIN order_coupons r2 ON ENDPOINT(r2, CustOrder) = REF(e2) JOIN Coupon e3 ON ENDPOINT(r2, Coupon) = REF(e3) WHERE e2.status < 'shipped' GROUP BY REF(e2), e2.placed_at HAVING COUNT(DISTINCT REF(e3)) >= 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
),
"b3" AS (
    SELECT
        "source"."promotion_id" AS "__endpoint_coupon_0",
        "source"."coupon_code" AS "__endpoint_coupon_1",
        "source"."order_coupons_custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_34" AS "source"
),
"b4" AS (
    SELECT
        "source"."promotion_id" AS "__reference_0",
        "source"."coupon_code" AS "__reference_1"
    FROM "relation_16" AS "source"
)
SELECT 
    "b2"."placed_at" AS "placed_at",
    COUNT(DISTINCT ROW("b4"."__reference_0", "b4"."__reference_1")) AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_coupon_0" = "b4"."__reference_0" AND "b3"."__endpoint_coupon_1" = "b4"."__reference_1"))
WHERE ("b2"."status" < 'shipped')
GROUP BY
    "b2"."__reference_0",
    "b2"."placed_at"
HAVING (COUNT(DISTINCT ROW("b4"."__reference_0", "b4"."__reference_1")) >= 5);

-- Q046 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.sku, COUNT(DISTINCT REF(e1)) AS related_count FROM cart_contains r JOIN Cart e1 ON ENDPOINT(r, Cart) = REF(e1) JOIN Camera e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.base_price <= 249 GROUP BY REF(e2), e2.sku HAVING COUNT(DISTINCT REF(e1)) >= 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_cart_0",
        "source"."cart_id" AS "__endpoint_cart_1",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_27" AS "source"
),
"b1" AS (
    SELECT
        "source"."user_id" AS "__reference_0",
        "source"."cart_id" AS "__reference_1"
    FROM "relation_9" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b2"."sku" AS "sku",
    COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_cart_0" = "b1"."__reference_0" AND "b0"."__endpoint_cart_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."base_price" <= 249)
GROUP BY
    "b2"."__reference_0",
    "b2"."sku"
HAVING (COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) >= 5);

-- Q047 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.is_active, e2.supplier_name, e3.status FROM supplier_products r1 JOIN PhysicalProduct e1 ON ENDPOINT(r1, Product) = REF(e1) JOIN Supplier e2 ON ENDPOINT(r1, Supplier) = REF(e2) JOIN supplier_pos r2 ON ENDPOINT(r2, Supplier) = REF(e2) JOIN PurchaseOrder e3 ON ENDPOINT(r2, PurchaseOrder) = REF(e3) WHERE e1.base_price > 96;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_36" AS "source"
),
"b1" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
),
"b2" AS (
    SELECT
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b3" AS (
    SELECT
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0",
        "source"."supplier_pos_supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_37" AS "source"
),
"b4" AS (
    SELECT
        "source"."status" AS "status",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
)
SELECT 
    "b1"."is_active" AS "is_active",
    "b2"."supplier_name" AS "supplier_name",
    "b4"."status" AS "status"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_supplier_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_supplier_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_purchaseorder_0" = "b4"."__reference_0"))
WHERE ("b1"."base_price" > 96);

-- Q048 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.coupon_code, w.per_user_limit, w.max_uses, o.starts_at, o.discount_type FROM Coupon w JOIN Promotion o ON OWNER(w) = REF(o) WHERE o.discount_value > '10';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."coupon_code" AS "coupon_code",
        "source"."max_uses" AS "max_uses",
        "source"."per_user_limit" AS "per_user_limit",
        "source"."promotion_id" AS "__owner_0"
    FROM "relation_16" AS "source"
),
"b1" AS (
    SELECT
        "source"."discount_type" AS "discount_type",
        "source"."discount_value" AS "discount_value",
        "source"."starts_at" AS "starts_at",
        "source"."promotion_id" AS "__reference_0"
    FROM "relation_15" AS "source"
)
SELECT 
    "b0"."coupon_code" AS "coupon_code",
    "b0"."per_user_limit" AS "per_user_limit",
    "b0"."max_uses" AS "max_uses",
    "b1"."starts_at" AS "starts_at",
    "b1"."discount_type" AS "discount_type"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."discount_value" > '10');

-- Q049 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.coupon_code FROM Coupon w WHERE w.per_user_limit > 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."coupon_code" AS "coupon_code",
        "source"."per_user_limit" AS "per_user_limit"
    FROM "relation_16" AS "source"
)
SELECT 
    "b0"."coupon_code" AS "coupon_code"
FROM "b0"
WHERE ("b0"."per_user_limit" > 1);

-- Q050 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.updated_at, e2.quantity, e2.product_name FROM cart_contains r JOIN Cart e1 ON ENDPOINT(r, Cart) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.sku >= 'SKU-KWpp-43251915';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_cart_0",
        "source"."cart_id" AS "__endpoint_cart_1",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_27" AS "source"
),
"b1" AS (
    SELECT
        "source"."updated_at" AS "updated_at",
        "source"."user_id" AS "__reference_0",
        "source"."cart_id" AS "__reference_1"
    FROM "relation_9" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."updated_at" AS "updated_at",
    "b2"."quantity" AS "quantity",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_cart_0" = "b1"."__reference_0" AND "b0"."__endpoint_cart_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."sku" >= 'SKU-KWpp-43251915');

-- Q051 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity FROM MenClothing e WHERE e.quantity >= 9;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."quantity" >= 9);

-- Q052 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.warranty_months, e.form_factor FROM Desktop e WHERE e.sku > 'SKU-PprG-17406221';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."form_factor" AS "form_factor",
        "source"."warranty_months" AS "warranty_months",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."form_factor" AS "form_factor"
FROM "b0"
WHERE ("b0"."sku" > 'SKU-PprG-17406221');

-- Q053 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.carrier_lock FROM Phone e WHERE e.warranty_months > 6;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."carrier_lock" AS "carrier_lock",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."carrier_lock" AS "carrier_lock"
FROM "b0"
WHERE ("b0"."warranty_months" > 6);

-- Q054 [selection_projection] occurrence 1/1
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

-- Q055 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.email, w.contact_id FROM SupplierContact w WHERE w.email <= 'stephaniewilliamson@example.com';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."contact_id" AS "contact_id",
        "source"."email" AS "email"
    FROM "relation_20" AS "source"
)
SELECT 
    "b0"."email" AS "email",
    "b0"."contact_id" AS "contact_id"
FROM "b0"
WHERE ("b0"."email" <= 'stephaniewilliamson@example.com');

-- Q056 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions, e.material, e.product_name, e.product_id FROM WomenClothing e WHERE e.material > 'blend';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."material" AS "material",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."dimensions" AS "dimensions",
    "b0"."material" AS "material",
    "b0"."product_name" AS "product_name",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."material" > 'blend');

-- Q057 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.password_hash, e2.status, e2.custorder_id FROM customer_orders r JOIN PrimeCustomer e1 ON ENDPOINT(r, Customer) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.password_hash <= 'b32d79402fb4d52277d400f9b244d43b6dceea4376e76762e024093007e66df7';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_30" AS "source"
),
"b1" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
),
"b2" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b1"."password_hash" AS "password_hash",
    "b2"."status" AS "status",
    "b2"."custorder_id" AS "custorder_id"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."password_hash" <= 'b32d79402fb4d52277d400f9b244d43b6dceea4376e76762e024093007e66df7');

-- Q058 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.loyalty_tier, e.user_id FROM PrimeCustomer e WHERE e.loyalty_tier > 'bronze';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT DISTINCT 
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."loyalty_tier" > 'bronze');

-- Q059 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.dimensions, e.sku FROM Smartwatch e WHERE e.base_price < 247;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."dimensions" AS "dimensions",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."base_price" < 247);

-- Q060 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.courierpartner_id, e1.carrier_code, e2.shipment_id FROM courier_shipments r JOIN CourierPartner e1 ON ENDPOINT(r, CourierPartner) = REF(e1) JOIN Shipment e2 ON ENDPOINT(r, Shipment) = REF(e2) WHERE e1.webhook_url < 'https://www.cummings.com/';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."courier_shipments_courierpartner_id" AS "__endpoint_courierpartner_0",
        "source"."custorder_id" AS "__endpoint_shipment_0",
        "source"."shipment_id" AS "__endpoint_shipment_1"
    FROM "relation_39" AS "source"
),
"b1" AS (
    SELECT
        "source"."carrier_code" AS "carrier_code",
        "source"."courierpartner_id" AS "courierpartner_id",
        "source"."webhook_url" AS "webhook_url",
        "source"."courierpartner_id" AS "__reference_0"
    FROM "relation_22" AS "source"
),
"b2" AS (
    SELECT
        "source"."shipment_id" AS "shipment_id",
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_14" AS "source"
)
SELECT 
    "b1"."courierpartner_id" AS "courierpartner_id",
    "b1"."carrier_code" AS "carrier_code",
    "b2"."shipment_id" AS "shipment_id"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
WHERE ("b1"."webhook_url" < 'https://www.cummings.com/');

-- Q061 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.code, e2.base_price, e3.is_active FROM stock r1 JOIN WarehouseBin e1 ON ENDPOINT(r1, WarehouseBin) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN bought_together r2 ON ENDPOINT(r2, bought_together_product_id) = REF(e2) JOIN Product e3 ON ENDPOINT(r2, product_id) = REF(e3) WHERE e3.sku < 'SKU-vFdW-79279946';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."warehouse_id" AS "__endpoint_warehousebin_0",
        "source"."bin_id" AS "__endpoint_warehousebin_1"
    FROM "relation_35" AS "source"
),
"b1" AS (
    SELECT
        "source"."code" AS "code",
        "source"."warehouse_id" AS "__reference_0",
        "source"."bin_id" AS "__reference_1"
    FROM "relation_18" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_26" AS "source"
),
"b4" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."code" AS "code",
    "b2"."base_price" AS "base_price",
    "b4"."is_active" AS "is_active"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_warehousebin_0" = "b1"."__reference_0" AND "b0"."__endpoint_warehousebin_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_bought_together_product_id_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_id_0" = "b4"."__reference_0"))
WHERE ("b4"."sku" < 'SKU-vFdW-79279946');

-- Q062 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.per_user_limit, w.max_uses, o.discount_type, o.ends_at FROM Coupon w JOIN Promotion o ON OWNER(w) = REF(o) WHERE o.discount_type > 'fixed';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."max_uses" AS "max_uses",
        "source"."per_user_limit" AS "per_user_limit",
        "source"."promotion_id" AS "__owner_0"
    FROM "relation_16" AS "source"
),
"b1" AS (
    SELECT
        "source"."discount_type" AS "discount_type",
        "source"."ends_at" AS "ends_at",
        "source"."promotion_id" AS "__reference_0"
    FROM "relation_15" AS "source"
)
SELECT 
    "b0"."per_user_limit" AS "per_user_limit",
    "b0"."max_uses" AS "max_uses",
    "b1"."discount_type" AS "discount_type",
    "b1"."ends_at" AS "ends_at"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."discount_type" > 'fixed');

-- Q063 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.status, e2.product_id, e3.supplier_name FROM po_items r1 JOIN PurchaseOrder e1 ON ENDPOINT(r1, PurchaseOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN supplier_products r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN Supplier e3 ON ENDPOINT(r2, Supplier) = REF(e3) WHERE e2.product_id >= 1668483;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0"
    FROM "relation_38" AS "source"
),
"b1" AS (
    SELECT
        "source"."status" AS "status",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_36" AS "source"
),
"b4" AS (
    SELECT
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
)
SELECT 
    "b1"."status" AS "status",
    "b2"."product_id" AS "product_id",
    "b4"."supplier_name" AS "supplier_name"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_purchaseorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_supplier_0" = "b4"."__reference_0"))
WHERE ("b2"."product_id" >= 1668483);

-- Q064 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.per_user_limit, w.coupon_code, w.max_uses, o.ends_at, o.starts_at FROM Coupon w JOIN Promotion o ON OWNER(w) = REF(o) WHERE o.discount_value <= '25';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."coupon_code" AS "coupon_code",
        "source"."max_uses" AS "max_uses",
        "source"."per_user_limit" AS "per_user_limit",
        "source"."promotion_id" AS "__owner_0"
    FROM "relation_16" AS "source"
),
"b1" AS (
    SELECT
        "source"."discount_value" AS "discount_value",
        "source"."ends_at" AS "ends_at",
        "source"."starts_at" AS "starts_at",
        "source"."promotion_id" AS "__reference_0"
    FROM "relation_15" AS "source"
)
SELECT 
    "b0"."per_user_limit" AS "per_user_limit",
    "b0"."coupon_code" AS "coupon_code",
    "b0"."max_uses" AS "max_uses",
    "b1"."ends_at" AS "ends_at",
    "b1"."starts_at" AS "starts_at"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."discount_value" <= '25');

-- Q065 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.exp_month, COUNT(DISTINCT REF(e2)) AS related_count FROM payment_order r JOIN PaymentMethod e1 ON ENDPOINT(r, PaymentMethod) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e2.placed_at < '2025-03-11' GROUP BY REF(e1), e1.exp_month HAVING COUNT(DISTINCT REF(e2)) >= 4;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."payment_order_customer_id" AS "__endpoint_paymentmethod_0",
        "source"."payment_order_payment_method_id" AS "__endpoint_paymentmethod_1"
    FROM "relation_32" AS "source"
),
"b1" AS (
    SELECT
        "source"."exp_month" AS "exp_month",
        "source"."user_id" AS "__reference_0",
        "source"."payment_method_id" AS "__reference_1"
    FROM "relation_8" AS "source"
),
"b2" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b1"."exp_month" AS "exp_month",
    COUNT(DISTINCT "b2"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_paymentmethod_0" = "b1"."__reference_0" AND "b0"."__endpoint_paymentmethod_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b2"."placed_at" < '2025-03-11')
GROUP BY
    "b1"."__reference_0",
    "b1"."__reference_1",
    "b1"."exp_month"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 4);

-- Q066 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.rating, w.title, w.body, o.password_hash FROM Review w JOIN Customer o ON OWNER(w) = REF(o) WHERE w.rating < 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."body" AS "body",
        "source"."rating" AS "rating",
        "source"."title" AS "title",
        "source"."user_id" AS "__owner_0"
    FROM "relation_11" AS "source"
),
"b1" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."rating" AS "rating",
    "b0"."title" AS "title",
    "b0"."body" AS "body",
    "b1"."password_hash" AS "password_hash"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."rating" < 5);

-- Q067 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id FROM PrimeCustomer e WHERE e.email > 'brian36@example.net';
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
WHERE ("b0"."email" > 'brian36@example.net');

-- Q068 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.warranty_months, e.quantity FROM Computer e WHERE e.product_id < 11127629;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('computer', 'desktop', 'laptop'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."warranty_months" AS "warranty_months",
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."product_id" < 11127629);

-- Q069 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.delivery_type, e.product_id, e.license_type, e.sku FROM Software e WHERE e.product_id < 16793771;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku",
        "source"."license_type" AS "license_type"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
)
SELECT DISTINCT 
    "b0"."delivery_type" AS "delivery_type",
    "b0"."product_id" AS "product_id",
    "b0"."license_type" AS "license_type",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."product_id" < 16793771);

-- Q070 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.sku, COUNT(DISTINCT REF(e1)) AS related_count FROM order_returns r JOIN CustOrder e1 ON ENDPOINT(r, CustOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.placed_at > '2023-10-22' GROUP BY REF(e2), e2.sku HAVING COUNT(DISTINCT REF(e1)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b1" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
),
"b2" AS (
    SELECT
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b2"."sku" AS "sku",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."placed_at" > '2023-10-22')
GROUP BY
    "b2"."__reference_0",
    "b2"."sku"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 2);

-- Q071 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.base_price, e.is_active FROM DigitalProduct e WHERE e.product_id > 16116999;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('digitalproduct', 'media', 'software'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."base_price" AS "base_price",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_id" > 16116999);

-- Q072 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.created_at, e1.purchaseorder_id, e2.is_active, e2.base_price FROM po_items r JOIN PurchaseOrder e1 ON ENDPOINT(r, PurchaseOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.created_at > '2023-11-02';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0"
    FROM "relation_38" AS "source"
),
"b1" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."purchaseorder_id" AS "purchaseorder_id",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."created_at" AS "created_at",
    "b1"."purchaseorder_id" AS "purchaseorder_id",
    "b2"."is_active" AS "is_active",
    "b2"."base_price" AS "base_price"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_purchaseorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."created_at" > '2023-11-02');

-- Q073 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.carrier, w.tracking_no FROM Shipment w WHERE w.carrier < 'USPS';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."carrier" AS "carrier",
        "source"."tracking_no" AS "tracking_no"
    FROM "relation_14" AS "source"
)
SELECT 
    "b0"."carrier" AS "carrier",
    "b0"."tracking_no" AS "tracking_no"
FROM "b0"
WHERE ("b0"."carrier" < 'USPS');

-- Q074 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.product_id, e2.sku, e3.product_id FROM bundle_phones r1 JOIN Phone e1 ON ENDPOINT(r1, bundle_phone_id) = REF(e1) JOIN Phone e2 ON ENDPOINT(r1, phone_id) = REF(e2) JOIN bundled_phone_accessory r2 ON ENDPOINT(r2, Phone) = REF(e2) JOIN Accessory e3 ON ENDPOINT(r2, Accessory) = REF(e3) WHERE e3.base_price > 120;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_phone_phone_id" AS "__endpoint_bundle_phone_id_0",
        "source"."phone_id" AS "__endpoint_phone_id_0"
    FROM "relation_40" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b3" AS (
    SELECT
        "source"."accessory_id" AS "__endpoint_accessory_0",
        "source"."phone_id" AS "__endpoint_phone_0"
    FROM "relation_41" AS "source"
),
"b4" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b1"."product_id" AS "product_id",
    "b2"."sku" AS "sku",
    "b4"."product_id" AS "product_id"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_bundle_phone_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_phone_id_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_phone_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_accessory_0" = "b4"."__reference_0"))
WHERE ("b4"."base_price" > 120);

-- Q075 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.is_active, e1.sku, e2.tag_name, e2.tag_id FROM product_tags r JOIN Product e1 ON ENDPOINT(r, Product) = REF(e1) JOIN Tag e2 ON ENDPOINT(r, Tag) = REF(e2) WHERE e1.sku >= 'SKU-UisD-54179086';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."tag_id" AS "__endpoint_tag_0"
    FROM "relation_24" AS "source"
),
"b1" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."tag_id" AS "tag_id",
        "source"."tag_name" AS "tag_name",
        "source"."tag_id" AS "__reference_0"
    FROM "relation_6" AS "source"
)
SELECT 
    "b1"."is_active" AS "is_active",
    "b1"."sku" AS "sku",
    "b2"."tag_name" AS "tag_name",
    "b2"."tag_id" AS "tag_id"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_tag_0" = "b2"."__reference_0"))
WHERE ("b1"."sku" >= 'SKU-UisD-54179086');

-- Q076 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.custorder_id, COUNT(DISTINCT REF(e1)) AS related_count FROM payment_order r JOIN PaymentMethod e1 ON ENDPOINT(r, PaymentMethod) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.is_default > 'false' GROUP BY REF(e2), e2.custorder_id HAVING COUNT(DISTINCT REF(e1)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."payment_order_customer_id" AS "__endpoint_paymentmethod_0",
        "source"."payment_order_payment_method_id" AS "__endpoint_paymentmethod_1"
    FROM "relation_32" AS "source"
),
"b1" AS (
    SELECT
        "source"."is_default" AS "is_default",
        "source"."user_id" AS "__reference_0",
        "source"."payment_method_id" AS "__reference_1"
    FROM "relation_8" AS "source"
),
"b2" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b2"."custorder_id" AS "custorder_id",
    COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_paymentmethod_0" = "b1"."__reference_0" AND "b0"."__endpoint_paymentmethod_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."is_default" > 'false')
GROUP BY
    "b2"."__reference_0",
    "b2"."custorder_id"
HAVING (COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) >= 2);

-- Q077 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.sku FROM DigitalProduct e WHERE e.delivery_type <= 'license_key';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('digitalproduct', 'media', 'software'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."delivery_type" <= 'license_key');

-- Q078 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.image_id FROM ProductImage w WHERE w.url < 'https://placekitten.com/713/549';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."image_id" AS "image_id",
        "source"."url" AS "url"
    FROM "relation_3" AS "source"
)
SELECT 
    "b0"."image_id" AS "image_id"
FROM "b0"
WHERE ("b0"."url" < 'https://placekitten.com/713/549');

-- Q079 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.product_name, COUNT(DISTINCT REF(e2)) AS related_count FROM stock r JOIN Software e1 ON ENDPOINT(r, Product) = REF(e1) JOIN WarehouseBin e2 ON ENDPOINT(r, WarehouseBin) = REF(e2) WHERE e1.product_id < 16790755 GROUP BY REF(e1), e1.product_name HAVING COUNT(DISTINCT REF(e2)) >= 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."warehouse_id" AS "__endpoint_warehousebin_0",
        "source"."bin_id" AS "__endpoint_warehousebin_1"
    FROM "relation_35" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
),
"b2" AS (
    SELECT
        "source"."warehouse_id" AS "__reference_0",
        "source"."bin_id" AS "__reference_1"
    FROM "relation_18" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_warehousebin_0" = "b2"."__reference_0" AND "b0"."__endpoint_warehousebin_1" = "b2"."__reference_1"))
WHERE ("b1"."product_id" < 16790755)
GROUP BY
    "b1"."__reference_0",
    "b1"."product_name"
HAVING (COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) >= 5);

-- Q080 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.dimensions, COUNT(DISTINCT REF(e2)) AS related_count FROM reviews r JOIN Clothing e1 ON ENDPOINT(r, Product) = REF(e1) JOIN Review e2 ON ENDPOINT(r, Review) = REF(e2) WHERE e1.sku >= 'SKU-aYOC-58263401' GROUP BY REF(e1), e1.dimensions HAVING COUNT(DISTINCT REF(e2)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."reviews_product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_review_0",
        "source"."review_id" AS "__endpoint_review_1"
    FROM "relation_29" AS "source"
),
"b1" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('clothing', 'menclothing', 'womenclothing'))
),
"b2" AS (
    SELECT
        "source"."user_id" AS "__reference_0",
        "source"."review_id" AS "__reference_1"
    FROM "relation_11" AS "source"
)
SELECT 
    "b1"."dimensions" AS "dimensions",
    COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_review_0" = "b2"."__reference_0" AND "b0"."__endpoint_review_1" = "b2"."__reference_1"))
WHERE ("b1"."sku" >= 'SKU-aYOC-58263401')
GROUP BY
    "b1"."__reference_0",
    "b1"."dimensions"
HAVING (COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) >= 2);

-- Q081 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.started_at, w.session_id, w.device, o.loyalty_tier FROM BrowsingSession w JOIN Customer o ON OWNER(w) = REF(o) WHERE o.loyalty_tier >= 'gold';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."device" AS "device",
        "source"."session_id" AS "session_id",
        "source"."started_at" AS "started_at",
        "source"."user_id" AS "__owner_0"
    FROM "relation_12" AS "source"
),
"b1" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."started_at" AS "started_at",
    "b0"."session_id" AS "session_id",
    "b0"."device" AS "device",
    "b1"."loyalty_tier" AS "loyalty_tier"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."loyalty_tier" >= 'gold');

-- Q082 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.updated_at, w.cart_id, o.loyalty_tier FROM Cart w JOIN Customer o ON OWNER(w) = REF(o) WHERE o.user_id < 1008612;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cart_id" AS "cart_id",
        "source"."updated_at" AS "updated_at",
        "source"."user_id" AS "__owner_0"
    FROM "relation_9" AS "source"
),
"b1" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."user_id" AS "user_id",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."updated_at" AS "updated_at",
    "b0"."cart_id" AS "cart_id",
    "b1"."loyalty_tier" AS "loyalty_tier"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."user_id" < 1008612);

-- Q083 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.supplier_id, e2.warranty_months, e3.sku FROM supplier_products r1 JOIN Supplier e1 ON ENDPOINT(r1, Supplier) = REF(e1) JOIN Electronics e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN bundle_components r2 ON ENDPOINT(r2, product_id) = REF(e2) JOIN Phone e3 ON ENDPOINT(r2, bundle_product_id) = REF(e3) WHERE e1.supplier_id < 52844;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_36" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b2" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
),
"b3" AS (
    SELECT
        "source"."bundle_product_product_id" AS "__endpoint_bundle_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
),
"b4" AS (
    SELECT
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b1"."supplier_id" AS "supplier_id",
    "b2"."warranty_months" AS "warranty_months",
    "b4"."sku" AS "sku"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_id_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_bundle_product_id_0" = "b4"."__reference_0"))
WHERE ("b1"."supplier_id" < 52844);

-- Q084 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.loyalty_tier, e.password_hash, e.email, e.user_id FROM Customer e WHERE e.email <= 'sedwards@example.net';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."password_hash" AS "password_hash",
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."email" <= 'sedwards@example.net');

-- Q085 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.max_uses, w.per_user_limit, o.starts_at, o.discount_value FROM Coupon w JOIN Promotion o ON OWNER(w) = REF(o) WHERE o.discount_value <= '20';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."max_uses" AS "max_uses",
        "source"."per_user_limit" AS "per_user_limit",
        "source"."promotion_id" AS "__owner_0"
    FROM "relation_16" AS "source"
),
"b1" AS (
    SELECT
        "source"."discount_value" AS "discount_value",
        "source"."starts_at" AS "starts_at",
        "source"."promotion_id" AS "__reference_0"
    FROM "relation_15" AS "source"
)
SELECT 
    "b0"."max_uses" AS "max_uses",
    "b0"."per_user_limit" AS "per_user_limit",
    "b1"."starts_at" AS "starts_at",
    "b1"."discount_value" AS "discount_value"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."discount_value" <= '20');

-- Q086 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.last4, e2.status, e2.custorder_id FROM payment_order r JOIN PaymentMethod e1 ON ENDPOINT(r, PaymentMethod) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e2.status < 'paid';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."payment_order_customer_id" AS "__endpoint_paymentmethod_0",
        "source"."payment_order_payment_method_id" AS "__endpoint_paymentmethod_1"
    FROM "relation_32" AS "source"
),
"b1" AS (
    SELECT
        "source"."last4" AS "last4",
        "source"."user_id" AS "__reference_0",
        "source"."payment_method_id" AS "__reference_1"
    FROM "relation_8" AS "source"
),
"b2" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b1"."last4" AS "last4",
    "b2"."status" AS "status",
    "b2"."custorder_id" AS "custorder_id"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_paymentmethod_0" = "b1"."__reference_0" AND "b0"."__endpoint_paymentmethod_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b2"."status" < 'paid');

-- Q087 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.shipment_id, COUNT(DISTINCT REF(e1)) AS related_count FROM courier_shipments r JOIN CourierPartner e1 ON ENDPOINT(r, CourierPartner) = REF(e1) JOIN Shipment e2 ON ENDPOINT(r, Shipment) = REF(e2) WHERE e2.shipment_id <= 5047940 GROUP BY REF(e2), e2.shipment_id HAVING COUNT(DISTINCT REF(e1)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."courier_shipments_courierpartner_id" AS "__endpoint_courierpartner_0",
        "source"."custorder_id" AS "__endpoint_shipment_0",
        "source"."shipment_id" AS "__endpoint_shipment_1"
    FROM "relation_39" AS "source"
),
"b1" AS (
    SELECT
        "source"."courierpartner_id" AS "__reference_0"
    FROM "relation_22" AS "source"
),
"b2" AS (
    SELECT
        "source"."shipment_id" AS "shipment_id",
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_14" AS "source"
)
SELECT 
    "b2"."shipment_id" AS "shipment_id",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
WHERE ("b2"."shipment_id" <= 5047940)
GROUP BY
    "b2"."__reference_0",
    "b2"."__reference_1",
    "b2"."shipment_id"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 2);

-- Q088 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.product_name FROM PhysicalProduct e WHERE e.dimensions < 'small';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."dimensions" < 'small');

-- Q089 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.base_price, e2.loyalty_tier FROM software_downloads r JOIN Software e1 ON ENDPOINT(r, Software) = REF(e1) JOIN BusinessCustomer e2 ON ENDPOINT(r, Customer) = REF(e2) WHERE e1.quantity <= 39;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_customer_0",
        "source"."software_id" AS "__endpoint_software_0"
    FROM "relation_42" AS "source"
),
"b1" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
),
"b2" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b1"."base_price" AS "base_price",
    "b2"."loyalty_tier" AS "loyalty_tier"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_software_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_customer_0" = "b2"."__reference_0"))
WHERE ("b1"."quantity" <= 39);

-- Q090 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.employee_no, e.email, e.user_id, e.password_hash FROM Employee e WHERE e.email < 'pearsonjames@example.org';
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
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id",
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."email" < 'pearsonjames@example.org');

-- Q091 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.band_size, e.sku, e.dimensions, e.product_name FROM Smartwatch e WHERE e.base_price < 148;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku",
        "source"."band_size" AS "band_size"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT DISTINCT 
    "b0"."band_size" AS "band_size",
    "b0"."sku" AS "sku",
    "b0"."dimensions" AS "dimensions",
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."base_price" < 148);

-- Q092 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.company_name, e.email, e.password_hash FROM BusinessCustomer e WHERE e.loyalty_tier > 'bronze';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."company_name" AS "company_name",
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."company_name" AS "company_name",
    "b0"."email" AS "email",
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."loyalty_tier" > 'bronze');

-- Q093 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.tag_name, e.tag_id FROM Tag e WHERE e.tag_name < 'premium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."tag_id" AS "tag_id",
        "source"."tag_name" AS "tag_name"
    FROM "relation_6" AS "source"
)
SELECT DISTINCT 
    "b0"."tag_name" AS "tag_name",
    "b0"."tag_id" AS "tag_id"
FROM "b0"
WHERE ("b0"."tag_name" < 'premium');

-- Q094 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.quantity, e2.product_name, e3.warranty_months FROM bundled_phone_accessory r1 JOIN Accessory e1 ON ENDPOINT(r1, Accessory) = REF(e1) JOIN Phone e2 ON ENDPOINT(r1, Phone) = REF(e2) JOIN bundle_phones r2 ON ENDPOINT(r2, phone_id) = REF(e2) JOIN Phone e3 ON ENDPOINT(r2, bundle_phone_id) = REF(e3) WHERE e2.dimensions <= 'medium';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_id" AS "__endpoint_accessory_0",
        "source"."phone_id" AS "__endpoint_phone_0"
    FROM "relation_41" AS "source"
),
"b1" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
),
"b2" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b3" AS (
    SELECT
        "source"."bundle_phone_phone_id" AS "__endpoint_bundle_phone_id_0",
        "source"."phone_id" AS "__endpoint_phone_id_0"
    FROM "relation_40" AS "source"
),
"b4" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b1"."quantity" AS "quantity",
    "b2"."product_name" AS "product_name",
    "b4"."warranty_months" AS "warranty_months"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_accessory_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_phone_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_phone_id_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_bundle_phone_id_0" = "b4"."__reference_0"))
WHERE ("b2"."dimensions" <= 'medium');

-- Q095 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warranty_months, e.accessory_type FROM Accessory e WHERE e.quantity > 22;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."warranty_months" AS "warranty_months",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."warranty_months" AS "warranty_months",
    "b0"."accessory_type" AS "accessory_type"
FROM "b0"
WHERE ("b0"."quantity" > 22);

-- Q096 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.sku, e.dimensions FROM Accessory e WHERE e.quantity < 30;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."sku" AS "sku",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."quantity" < 30);

-- Q097 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.supplier_id, e1.supplier_name, e2.is_active, e2.quantity FROM supplier_products r JOIN Supplier e1 ON ENDPOINT(r, Supplier) = REF(e1) JOIN Accessory e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.base_price < 362;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_36" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b1"."supplier_id" AS "supplier_id",
    "b1"."supplier_name" AS "supplier_name",
    "b2"."is_active" AS "is_active",
    "b2"."quantity" AS "quantity"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."base_price" < 362);

-- Q098 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.tag_id FROM Tag e WHERE e.tag_name > 'exclusive';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."tag_id" AS "tag_id",
        "source"."tag_name" AS "tag_name"
    FROM "relation_6" AS "source"
)
SELECT DISTINCT 
    "b0"."tag_id" AS "tag_id"
FROM "b0"
WHERE ("b0"."tag_name" > 'exclusive');

-- Q099 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.product_name, COUNT(DISTINCT REF(e1)) AS related_count FROM bundle_phones r JOIN Phone e1 ON ENDPOINT(r, phone_id) = REF(e1) JOIN Phone e2 ON ENDPOINT(r, bundle_phone_id) = REF(e2) WHERE e2.base_price > 39 GROUP BY REF(e2), e2.product_name HAVING COUNT(DISTINCT REF(e1)) >= 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_phone_phone_id" AS "__endpoint_bundle_phone_id_0",
        "source"."phone_id" AS "__endpoint_phone_id_0"
    FROM "relation_40" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b2"."product_name" AS "product_name",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bundle_phone_id_0" = "b2"."__reference_0"))
WHERE ("b2"."base_price" > 39)
GROUP BY
    "b2"."__reference_0",
    "b2"."product_name"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 3);

-- Q100 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.is_active, e2.custorder_id, e3.cpu FROM order_returns r1 JOIN Product e1 ON ENDPOINT(r1, Product) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r1, CustOrder) = REF(e2) JOIN order_items r2 ON ENDPOINT(r2, CustOrder) = REF(e2) JOIN Laptop e3 ON ENDPOINT(r2, Product) = REF(e3) WHERE e1.sku > 'SKU-KWhj-56460696';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_33" AS "source"
),
"b1" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
),
"b3" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_31" AS "source"
),
"b4" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT 
    "b1"."is_active" AS "is_active",
    "b2"."custorder_id" AS "custorder_id",
    "b4"."cpu" AS "cpu"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_0" = "b4"."__reference_0"))
WHERE ("b1"."sku" > 'SKU-KWhj-56460696');

ROLLBACK;
