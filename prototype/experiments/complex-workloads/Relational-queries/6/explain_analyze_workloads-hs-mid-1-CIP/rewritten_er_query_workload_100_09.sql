\set ON_ERROR_STOP on
\pset pager off
-- CompileDB mapping-aware relational workload
-- Conceptual workload: example2_schema_driven_selectivity_100_w09
-- Mapping ID: fa68ce77642be474c0e91514ccfa5d29b037566d0f2e42ffd246fae48a9fc668
-- Query shapes: 100
-- Executed statements: 100
BEGIN TRANSACTION READ ONLY;

-- Q001 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.ends_at, e.starts_at, e.promo_name FROM Promotion e WHERE e.promo_name > 'Object-based responsive policy';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ends_at" AS "ends_at",
        "source"."promo_name" AS "promo_name",
        "source"."starts_at" AS "starts_at"
    FROM "relation_15" AS "source"
)
SELECT 
    "b0"."ends_at" AS "ends_at",
    "b0"."starts_at" AS "starts_at",
    "b0"."promo_name" AS "promo_name"
FROM "b0"
WHERE ("b0"."promo_name" > 'Object-based responsive policy');

-- Q002 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.device, w.session_id, o.password_hash FROM BrowsingSession w JOIN User o ON OWNER(w) = REF(o) WHERE o.password_hash >= '7f77e1d72ca05f11515ce34eb13029810461de5058fa890e4a72e479fef250d6';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."device" AS "device",
        "source"."session_id" AS "session_id",
        "source"."user_id" AS "__owner_0"
    FROM "relation_12" AS "source"
),
"b1" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
)
SELECT 
    "b0"."device" AS "device",
    "b0"."session_id" AS "session_id",
    "b1"."password_hash" AS "password_hash"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."password_hash" >= '7f77e1d72ca05f11515ce34eb13029810461de5058fa890e4a72e479fef250d6');

-- Q003 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.supplier_id, COUNT(DISTINCT REF(e3)) AS related_count FROM supplier_products r1 JOIN Product e1 ON ENDPOINT(r1, Product) = REF(e1) JOIN Supplier e2 ON ENDPOINT(r1, Supplier) = REF(e2) JOIN supplier_pos r2 ON ENDPOINT(r2, Supplier) = REF(e2) JOIN PurchaseOrder e3 ON ENDPOINT(r2, PurchaseOrder) = REF(e3) WHERE e2.supplier_id <= 10516 GROUP BY REF(e2), e2.supplier_id HAVING COUNT(DISTINCT REF(e3)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_31" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b3" AS (
    SELECT
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0",
        "source"."supplier_pos_supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_21" AS "source"
    WHERE ("source"."supplier_pos_supplier_id" IS NOT NULL)
),
"b4" AS (
    SELECT
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
)
SELECT 
    "b2"."supplier_id" AS "supplier_id",
    COUNT(DISTINCT "b4"."__reference_0") AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_supplier_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_supplier_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_purchaseorder_0" = "b4"."__reference_0"))
WHERE ("b2"."supplier_id" <= 10516)
GROUP BY
    "b2"."__reference_0",
    "b2"."supplier_id"
HAVING (COUNT(DISTINCT "b4"."__reference_0") >= 2);

-- Q004 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.delivered_at, COUNT(DISTINCT REF(e1)) AS related_count FROM courier_shipments r JOIN CourierPartner e1 ON ENDPOINT(r, CourierPartner) = REF(e1) JOIN Shipment e2 ON ENDPOINT(r, Shipment) = REF(e2) WHERE e1.webhook_url < 'http://horn.com/' GROUP BY REF(e2), e2.delivered_at HAVING COUNT(DISTINCT REF(e1)) >= 4;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."courier_shipments_courierpartner_id" AS "__endpoint_courierpartner_0",
        "source"."custorder_id" AS "__endpoint_shipment_0",
        "source"."shipment_id" AS "__endpoint_shipment_1"
    FROM "relation_14" AS "source"
    WHERE ("source"."courier_shipments_courierpartner_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."webhook_url" AS "webhook_url",
        "source"."courierpartner_id" AS "__reference_0"
    FROM "relation_22" AS "source"
),
"b2" AS (
    SELECT
        "source"."delivered_at" AS "delivered_at",
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_14" AS "source"
)
SELECT 
    "b2"."delivered_at" AS "delivered_at",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
WHERE ("b1"."webhook_url" < 'http://horn.com/')
GROUP BY
    "b2"."__reference_0",
    "b2"."__reference_1",
    "b2"."delivered_at"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 4);

-- Q005 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.brand, COUNT(DISTINCT REF(e2)) AS related_count FROM payment_order r JOIN PaymentMethod e1 ON ENDPOINT(r, PaymentMethod) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e2.placed_at <= '2023-05-03' GROUP BY REF(e1), e1.brand HAVING COUNT(DISTINCT REF(e2)) >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."payment_order_customer_id" AS "__endpoint_paymentmethod_0",
        "source"."payment_order_payment_method_id" AS "__endpoint_paymentmethod_1"
    FROM "relation_13" AS "source"
    WHERE ("source"."payment_order_customer_id" IS NOT NULL) AND ("source"."payment_order_payment_method_id" IS NOT NULL)
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
        "source"."placed_at" AS "placed_at",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b1"."brand" AS "brand",
    COUNT(DISTINCT "b2"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_paymentmethod_0" = "b1"."__reference_0" AND "b0"."__endpoint_paymentmethod_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b2"."placed_at" <= '2023-05-03')
GROUP BY
    "b1"."__reference_0",
    "b1"."__reference_1",
    "b1"."brand"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 1);

-- Q006 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.wishlist_name, w.wishlist_id, o.password_hash FROM Wishlist w JOIN Customer o ON OWNER(w) = REF(o) WHERE o.password_hash >= 'cd94b32f6ece0a42e85bf394c7927439ba8e207a59c3a2f039d1af18522b09b0';
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
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."wishlist_name" AS "wishlist_name",
    "b0"."wishlist_id" AS "wishlist_id",
    "b1"."password_hash" AS "password_hash"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."password_hash" >= 'cd94b32f6ece0a42e85bf394c7927439ba8e207a59c3a2f039d1af18522b09b0');

-- Q007 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.product_id, e2.is_active, e3.cart_id FROM bundle_components r1 JOIN Product e1 ON ENDPOINT(r1, product_id) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, bundle_product_id) = REF(e2) JOIN cart_contains r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN Cart e3 ON ENDPOINT(r2, Cart) = REF(e3) WHERE e1.sku >= 'SKU-klfZ-12422029';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_product_product_id" AS "__endpoint_bundle_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_24" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_cart_0",
        "source"."cart_id" AS "__endpoint_cart_1",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_26" AS "source"
),
"b4" AS (
    SELECT
        "source"."cart_id" AS "cart_id",
        "source"."user_id" AS "__reference_0",
        "source"."cart_id" AS "__reference_1"
    FROM "relation_9" AS "source"
)
SELECT 
    "b1"."product_id" AS "product_id",
    "b2"."is_active" AS "is_active",
    "b4"."cart_id" AS "cart_id"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bundle_product_id_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_cart_0" = "b4"."__reference_0" AND "b3"."__endpoint_cart_1" = "b4"."__reference_1"))
WHERE ("b1"."sku" >= 'SKU-klfZ-12422029');

-- Q008 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.sku, COUNT(DISTINCT REF(e1)) AS related_count FROM bought_together r JOIN Product e1 ON ENDPOINT(r, product_id) = REF(e1) JOIN Product e2 ON ENDPOINT(r, bought_together_product_id) = REF(e2) WHERE e1.product_id < 8432208 GROUP BY REF(e2), e2.sku HAVING COUNT(DISTINCT REF(e1)) >= 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
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
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bought_together_product_id_0" = "b2"."__reference_0"))
WHERE ("b1"."product_id" < 8432208)
GROUP BY
    "b2"."__reference_0",
    "b2"."sku"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 3);

-- Q009 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.price_id, w.ends_at, w.price, o.base_price FROM PriceHistory w JOIN Product o ON OWNER(w) = REF(o) WHERE o.sku < 'SKU-KWpp-43251915';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ends_at" AS "ends_at",
        "source"."price" AS "price",
        "source"."price_id" AS "price_id",
        "source"."product_id" AS "__owner_0"
    FROM "relation_5" AS "source"
),
"b1" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b0"."price_id" AS "price_id",
    "b0"."ends_at" AS "ends_at",
    "b0"."price" AS "price",
    "b1"."base_price" AS "base_price"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."sku" < 'SKU-KWpp-43251915');

-- Q010 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.dimensions, e2.accessory_type FROM bundled_phone_accessory r JOIN Phone e1 ON ENDPOINT(r, Phone) = REF(e1) JOIN Accessory e2 ON ENDPOINT(r, Accessory) = REF(e2) WHERE e2.quantity <= 8;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_id" AS "__endpoint_accessory_0",
        "source"."phone_id" AS "__endpoint_phone_0"
    FROM "relation_34" AS "source"
),
"b1" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b1"."dimensions" AS "dimensions",
    "b2"."accessory_type" AS "accessory_type"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_accessory_0" = "b2"."__reference_0"))
WHERE ("b2"."quantity" <= 8);

-- Q011 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.custorder_id, e2.sku, e2.quantity FROM order_items r JOIN CustOrder e1 ON ENDPOINT(r, CustOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.status > 'pending';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_28" AS "source"
),
"b1" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
),
"b2" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."custorder_id" AS "custorder_id",
    "b2"."sku" AS "sku",
    "b2"."quantity" AS "quantity"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."status" > 'pending');

-- Q012 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.bin_id, e2.is_active, e3.created_at FROM stock r1 JOIN WarehouseBin e1 ON ENDPOINT(r1, WarehouseBin) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN po_items r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN PurchaseOrder e3 ON ENDPOINT(r2, PurchaseOrder) = REF(e3) WHERE e3.status < 'cancelled';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."warehouse_id" AS "__endpoint_warehousebin_0",
        "source"."bin_id" AS "__endpoint_warehousebin_1"
    FROM "relation_30" AS "source"
),
"b1" AS (
    SELECT
        "source"."bin_id" AS "bin_id",
        "source"."warehouse_id" AS "__reference_0",
        "source"."bin_id" AS "__reference_1"
    FROM "relation_18" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0"
    FROM "relation_32" AS "source"
),
"b4" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."status" AS "status",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
)
SELECT 
    "b1"."bin_id" AS "bin_id",
    "b2"."is_active" AS "is_active",
    "b4"."created_at" AS "created_at"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_warehousebin_0" = "b1"."__reference_0" AND "b0"."__endpoint_warehousebin_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_purchaseorder_0" = "b4"."__reference_0"))
WHERE ("b4"."status" < 'cancelled');

-- Q013 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.supplier_name, e2.status FROM supplier_pos r JOIN Supplier e1 ON ENDPOINT(r, Supplier) = REF(e1) JOIN PurchaseOrder e2 ON ENDPOINT(r, PurchaseOrder) = REF(e2) WHERE e1.supplier_name > 'Pittman, Wagner and Kelly';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0",
        "source"."supplier_pos_supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_21" AS "source"
    WHERE ("source"."supplier_pos_supplier_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b2" AS (
    SELECT
        "source"."status" AS "status",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
)
SELECT 
    "b1"."supplier_name" AS "supplier_name",
    "b2"."status" AS "status"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_purchaseorder_0" = "b2"."__reference_0"))
WHERE ("b1"."supplier_name" > 'Pittman, Wagner and Kelly');

-- Q014 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.category_id, COUNT(DISTINCT REF(e2)) AS related_count FROM category_products r JOIN Category e1 ON ENDPOINT(r, Category) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.category_name > 'our' GROUP BY REF(e1), e1.category_id HAVING COUNT(DISTINCT REF(e2)) >= 4;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."category_products_category_id" AS "__endpoint_category_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."category_products_category_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."category_id" AS "category_id",
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
    "b1"."category_id" AS "category_id",
    COUNT(DISTINCT "b2"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."category_name" > 'our')
GROUP BY
    "b1"."__reference_0",
    "b1"."category_id"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 4);

-- Q015 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.product_id, COUNT(DISTINCT REF(e3)) AS related_count FROM product_tags r1 JOIN Tag e1 ON ENDPOINT(r1, Tag) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN order_returns r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN CustOrder e3 ON ENDPOINT(r2, CustOrder) = REF(e3) WHERE e2.quantity > 55 GROUP BY REF(e2), e2.product_id HAVING COUNT(DISTINCT REF(e3)) >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."tag_id" AS "__endpoint_tag_0"
    FROM "relation_23" AS "source"
),
"b1" AS (
    SELECT
        "source"."tag_id" AS "__reference_0"
    FROM "relation_6" AS "source"
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
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_29" AS "source"
),
"b4" AS (
    SELECT
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b2"."product_id" AS "product_id",
    COUNT(DISTINCT "b4"."__reference_0") AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_tag_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_custorder_0" = "b4"."__reference_0"))
WHERE ("b2"."quantity" > 55)
GROUP BY
    "b2"."__reference_0",
    "b2"."product_id"
HAVING (COUNT(DISTINCT "b4"."__reference_0") >= 1);

-- Q016 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.email, e.user_id, e.password_hash, e.renewal_date FROM PrimeCustomer e WHERE e.renewal_date >= '2027-10-14';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."renewal_date" AS "renewal_date",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT 
    "b0"."email" AS "email",
    "b0"."user_id" AS "user_id",
    "b0"."password_hash" AS "password_hash",
    "b0"."renewal_date" AS "renewal_date"
FROM "b0"
WHERE ("b0"."renewal_date" >= '2027-10-14');

-- Q017 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.password_hash, e2.status, e2.placed_at FROM customer_orders r JOIN Customer e1 ON ENDPOINT(r, Customer) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.email <= 'jeffreybentley@example.org';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_13" AS "source"
    WHERE ("source"."customer_orders_customer_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
),
"b2" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b1"."password_hash" AS "password_hash",
    "b2"."status" AS "status",
    "b2"."placed_at" AS "placed_at"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."email" <= 'jeffreybentley@example.org');

-- Q018 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.supplier_id, e2.product_name, e3.sku FROM supplier_products r1 JOIN Supplier e1 ON ENDPOINT(r1, Supplier) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN bought_together r2 ON ENDPOINT(r2, product_id) = REF(e2) JOIN Product e3 ON ENDPOINT(r2, bought_together_product_id) = REF(e3) WHERE e2.product_id < 6628845;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_31" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
),
"b4" AS (
    SELECT
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."supplier_id" AS "supplier_id",
    "b2"."product_name" AS "product_name",
    "b4"."sku" AS "sku"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_id_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_bought_together_product_id_0" = "b4"."__reference_0"))
WHERE ("b2"."product_id" < 6628845);

-- Q019 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.base_price, COUNT(DISTINCT REF(e3)) AS related_count FROM bundle_components r1 JOIN Product e1 ON ENDPOINT(r1, bundle_product_id) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, product_id) = REF(e2) JOIN bought_together r2 ON ENDPOINT(r2, product_id) = REF(e2) JOIN Product e3 ON ENDPOINT(r2, bought_together_product_id) = REF(e3) WHERE e3.sku < 'SKU-PTjD-46248744' GROUP BY REF(e2), e2.base_price HAVING COUNT(DISTINCT REF(e3)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_product_product_id" AS "__endpoint_bundle_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_24" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
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
    FROM "relation_25" AS "source"
),
"b4" AS (
    SELECT
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b2"."base_price" AS "base_price",
    COUNT(DISTINCT "b4"."__reference_0") AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_bundle_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_id_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_id_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_bought_together_product_id_0" = "b4"."__reference_0"))
WHERE ("b4"."sku" < 'SKU-PTjD-46248744')
GROUP BY
    "b2"."__reference_0",
    "b2"."base_price"
HAVING (COUNT(DISTINCT "b4"."__reference_0") >= 2);

-- Q020 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash, e.renewal_date, e.loyalty_tier FROM PrimeCustomer e WHERE e.email > 'perezrodney@example.com';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."renewal_date" AS "renewal_date",
        "source"."email" AS "email",
        "source"."password_hash" AS "password_hash"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT 
    "b0"."password_hash" AS "password_hash",
    "b0"."renewal_date" AS "renewal_date",
    "b0"."loyalty_tier" AS "loyalty_tier"
FROM "b0"
WHERE ("b0"."email" > 'perezrodney@example.com');

-- Q021 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity FROM Tablet e WHERE e.warranty_months < 24;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b0"."quantity" AS "quantity"
FROM "b0"
WHERE ("b0"."warranty_months" < 24);

-- Q022 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.wishlist_id, w.wishlist_name, o.email FROM Wishlist w JOIN Customer o ON OWNER(w) = REF(o) WHERE w.wishlist_name > 'holiday';
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
        "source"."email" AS "email",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."wishlist_id" AS "wishlist_id",
    "b0"."wishlist_name" AS "wishlist_name",
    "b1"."email" AS "email"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."wishlist_name" > 'holiday');

-- Q023 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.product_name, COUNT(DISTINCT REF(e1)) AS related_count FROM bought_together r JOIN Product e1 ON ENDPOINT(r, product_id) = REF(e1) JOIN Product e2 ON ENDPOINT(r, bought_together_product_id) = REF(e2) WHERE e1.quantity < 4 GROUP BY REF(e2), e2.product_name HAVING COUNT(DISTINCT REF(e1)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
),
"b1" AS (
    SELECT
        "source"."quantity" AS "quantity",
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
    "b2"."product_name" AS "product_name",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bought_together_product_id_0" = "b2"."__reference_0"))
WHERE ("b1"."quantity" < 4)
GROUP BY
    "b2"."__reference_0",
    "b2"."product_name"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 2);

-- Q024 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.wishlist_id, e2.sku FROM wishlist_contains r JOIN Wishlist e1 ON ENDPOINT(r, Wishlist) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.base_price >= 358;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_wishlist_0",
        "source"."wishlist_id" AS "__endpoint_wishlist_1"
    FROM "relation_27" AS "source"
),
"b1" AS (
    SELECT
        "source"."wishlist_id" AS "wishlist_id",
        "source"."user_id" AS "__reference_0",
        "source"."wishlist_id" AS "__reference_1"
    FROM "relation_10" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."wishlist_id" AS "wishlist_id",
    "b2"."sku" AS "sku"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_wishlist_0" = "b1"."__reference_0" AND "b0"."__endpoint_wishlist_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."base_price" >= 358);

-- Q025 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.is_active, e2.is_active, e2.product_name FROM bundle_components r JOIN Product e1 ON ENDPOINT(r, product_id) = REF(e1) JOIN Product e2 ON ENDPOINT(r, bundle_product_id) = REF(e2) WHERE e1.quantity < 23;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_product_product_id" AS "__endpoint_bundle_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_24" AS "source"
),
"b1" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity",
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
    "b1"."is_active" AS "is_active",
    "b2"."is_active" AS "is_active",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bundle_product_id_0" = "b2"."__reference_0"))
WHERE ("b1"."quantity" < 23);

-- Q026 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.shipped_at, w.tracking_no, w.delivered_at, o.status FROM Shipment w JOIN CustOrder o ON OWNER(w) = REF(o) WHERE w.tracking_no < 'KT0862261685';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivered_at" AS "delivered_at",
        "source"."shipped_at" AS "shipped_at",
        "source"."tracking_no" AS "tracking_no",
        "source"."custorder_id" AS "__owner_0"
    FROM "relation_14" AS "source"
),
"b1" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b0"."shipped_at" AS "shipped_at",
    "b0"."tracking_no" AS "tracking_no",
    "b0"."delivered_at" AS "delivered_at",
    "b1"."status" AS "status"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."tracking_no" < 'KT0862261685');

-- Q027 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.custorder_id, COUNT(DISTINCT REF(e1)) AS related_count FROM customer_orders r JOIN Customer e1 ON ENDPOINT(r, Customer) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.password_hash < '1954c55d5d08b48e85e9b1d50237be6a53a0dfbbd25cbe55d26a823a4e7a31e9' GROUP BY REF(e2), e2.custorder_id HAVING COUNT(DISTINCT REF(e1)) >= 4;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_13" AS "source"
    WHERE ("source"."customer_orders_customer_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
),
"b2" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b2"."custorder_id" AS "custorder_id",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."password_hash" < '1954c55d5d08b48e85e9b1d50237be6a53a0dfbbd25cbe55d26a823a4e7a31e9')
GROUP BY
    "b2"."__reference_0",
    "b2"."custorder_id"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 4);

-- Q028 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.review_id, w.created_at, w.rating, o.user_id, o.password_hash FROM Review w JOIN Customer o ON OWNER(w) = REF(o) WHERE w.created_at >= '2025-03-18';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."rating" AS "rating",
        "source"."review_id" AS "review_id",
        "source"."user_id" AS "__owner_0"
    FROM "relation_11" AS "source"
),
"b1" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."review_id" AS "review_id",
    "b0"."created_at" AS "created_at",
    "b0"."rating" AS "rating",
    "b1"."user_id" AS "user_id",
    "b1"."password_hash" AS "password_hash"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."created_at" >= '2025-03-18');

-- Q029 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.dimensions FROM Apparel e WHERE e.is_active >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear'))
)
SELECT 
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."is_active" >= 1);

-- Q030 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sku FROM Electronics e WHERE e.product_id < 2749696;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT DISTINCT 
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."product_id" < 2749696);

-- Q031 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price FROM Electronics e WHERE e.quantity < 23;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."quantity" < 23);

-- Q032 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.code, o.warehouse_id, o.warehouse_name FROM WarehouseBin w JOIN Warehouse o ON OWNER(w) = REF(o) WHERE w.bin_id >= 4986645;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bin_id" AS "bin_id",
        "source"."code" AS "code",
        "source"."warehouse_id" AS "__owner_0"
    FROM "relation_18" AS "source"
),
"b1" AS (
    SELECT
        "source"."warehouse_id" AS "warehouse_id",
        "source"."warehouse_name" AS "warehouse_name",
        "source"."warehouse_id" AS "__reference_0"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."code" AS "code",
    "b1"."warehouse_id" AS "warehouse_id",
    "b1"."warehouse_name" AS "warehouse_name"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."bin_id" >= 4986645);

-- Q033 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warehouse_id FROM Warehouse e WHERE e.region <= 'Midwest';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."region" AS "region",
        "source"."warehouse_id" AS "warehouse_id"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."warehouse_id" AS "warehouse_id"
FROM "b0"
WHERE ("b0"."region" <= 'Midwest');

-- Q034 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.delivery_type FROM DigitalProduct e WHERE e.delivery_type > 'download';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('digitalproduct', 'media', 'software'))
)
SELECT 
    "b0"."delivery_type" AS "delivery_type"
FROM "b0"
WHERE ("b0"."delivery_type" > 'download');

-- Q035 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.base_price, COUNT(DISTINCT REF(e1)) AS related_count FROM bought_together r JOIN Product e1 ON ENDPOINT(r, product_id) = REF(e1) JOIN Product e2 ON ENDPOINT(r, bought_together_product_id) = REF(e2) WHERE e1.quantity < 18 GROUP BY REF(e2), e2.base_price HAVING COUNT(DISTINCT REF(e1)) >= 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
),
"b1" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b2"."base_price" AS "base_price",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bought_together_product_id_0" = "b2"."__reference_0"))
WHERE ("b1"."quantity" < 18)
GROUP BY
    "b2"."__reference_0",
    "b2"."base_price"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 3);

-- Q036 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Apparel e WHERE e.sku < 'SKU-PpUx-53765904';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."sku" < 'SKU-PpUx-53765904');

-- Q037 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.status, e.custorder_id FROM CustOrder e WHERE e.status >= 'paid';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."status" AS "status"
    FROM "relation_13" AS "source"
)
SELECT 
    "b0"."status" AS "status",
    "b0"."custorder_id" AS "custorder_id"
FROM "b0"
WHERE ("b0"."status" >= 'paid');

-- Q038 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.sku, e.base_price FROM DigitalProduct e WHERE e.is_active < 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('digitalproduct', 'media', 'software'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."sku" AS "sku",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."is_active" < 1);

-- Q039 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.custorder_id, COUNT(DISTINCT REF(e2)) AS related_count FROM order_items r JOIN CustOrder e1 ON ENDPOINT(r, CustOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.placed_at < '2024-04-12' GROUP BY REF(e1), e1.custorder_id HAVING COUNT(DISTINCT REF(e2)) >= 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_28" AS "source"
),
"b1" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."placed_at" AS "placed_at",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."custorder_id" AS "custorder_id",
    COUNT(DISTINCT "b2"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."placed_at" < '2024-04-12')
GROUP BY
    "b1"."__reference_0",
    "b1"."custorder_id"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 3);

-- Q040 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.payment_method_id, o.password_hash FROM PaymentMethod w JOIN Customer o ON OWNER(w) = REF(o) WHERE w.exp_month > 10;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."exp_month" AS "exp_month",
        "source"."payment_method_id" AS "payment_method_id",
        "source"."user_id" AS "__owner_0"
    FROM "relation_8" AS "source"
),
"b1" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."payment_method_id" AS "payment_method_id",
    "b1"."password_hash" AS "password_hash"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."exp_month" > 10);

-- Q041 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.loyalty_tier, e.company_name, e.password_hash, e.user_id FROM BusinessCustomer e WHERE e.password_hash >= 'b48c2613361ebf036b633a98d1a425fe0973362b038e19b9fb3c62a3be45a7c4';
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
    "b0"."company_name" AS "company_name",
    "b0"."password_hash" AS "password_hash",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."password_hash" >= 'b48c2613361ebf036b633a98d1a425fe0973362b038e19b9fb3c62a3be45a7c4');

-- Q042 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.rating, w.title, o.loyalty_tier, o.password_hash FROM Review w JOIN Customer o ON OWNER(w) = REF(o) WHERE o.loyalty_tier <= 'bronze';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."rating" AS "rating",
        "source"."title" AS "title",
        "source"."user_id" AS "__owner_0"
    FROM "relation_11" AS "source"
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
    "b0"."rating" AS "rating",
    "b0"."title" AS "title",
    "b1"."loyalty_tier" AS "loyalty_tier",
    "b1"."password_hash" AS "password_hash"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."loyalty_tier" <= 'bronze');

-- Q043 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.product_id, e2.product_name, e3.base_price FROM bought_together r1 JOIN Product e1 ON ENDPOINT(r1, bought_together_product_id) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, product_id) = REF(e2) JOIN bundle_components r2 ON ENDPOINT(r2, product_id) = REF(e2) JOIN Product e3 ON ENDPOINT(r2, bundle_product_id) = REF(e3) WHERE e3.product_name <= 'Front-line client-driven middleware';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "product_id",
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
        "source"."bundle_product_product_id" AS "__endpoint_bundle_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_24" AS "source"
),
"b4" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."product_id" AS "product_id",
    "b2"."product_name" AS "product_name",
    "b4"."base_price" AS "base_price"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_bought_together_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_id_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_id_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_bundle_product_id_0" = "b4"."__reference_0"))
WHERE ("b4"."product_name" <= 'Front-line client-driven middleware');

-- Q044 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.shipped_at, w.carrier, w.tracking_no, o.custorder_id, o.status FROM Shipment w JOIN CustOrder o ON OWNER(w) = REF(o) WHERE w.shipped_at >= '2026-02-02';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."carrier" AS "carrier",
        "source"."shipped_at" AS "shipped_at",
        "source"."tracking_no" AS "tracking_no",
        "source"."custorder_id" AS "__owner_0"
    FROM "relation_14" AS "source"
),
"b1" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b0"."shipped_at" AS "shipped_at",
    "b0"."carrier" AS "carrier",
    "b0"."tracking_no" AS "tracking_no",
    "b1"."custorder_id" AS "custorder_id",
    "b1"."status" AS "status"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."shipped_at" >= '2026-02-02');

-- Q045 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.loyalty_tier, e1.user_id, e2.placed_at FROM customer_orders r JOIN Customer e1 ON ENDPOINT(r, Customer) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.loyalty_tier <= 'bronze';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_13" AS "source"
    WHERE ("source"."customer_orders_customer_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."user_id" AS "user_id",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
),
"b2" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b1"."loyalty_tier" AS "loyalty_tier",
    "b1"."user_id" AS "user_id",
    "b2"."placed_at" AS "placed_at"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."loyalty_tier" <= 'bronze');

-- Q046 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.category_id, e1.parent, e2.product_name FROM category_products r JOIN Category e1 ON ENDPOINT(r, Category) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.parent < 5297;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."category_products_category_id" AS "__endpoint_category_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."category_products_category_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."category_id" AS "category_id",
        "source"."parent" AS "parent",
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
    "b1"."parent" AS "parent",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."parent" < 5297);

-- Q047 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.status, e.created_at FROM PurchaseOrder e WHERE e.status <= 'draft';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."status" AS "status"
    FROM "relation_21" AS "source"
)
SELECT 
    "b0"."status" AS "status",
    "b0"."created_at" AS "created_at"
FROM "b0"
WHERE ("b0"."status" <= 'draft');

-- Q048 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.carrier_code, e1.webhook_url, e2.tracking_no FROM courier_shipments r JOIN CourierPartner e1 ON ENDPOINT(r, CourierPartner) = REF(e1) JOIN Shipment e2 ON ENDPOINT(r, Shipment) = REF(e2) WHERE e2.delivered_at <= '2025-01-11';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."courier_shipments_courierpartner_id" AS "__endpoint_courierpartner_0",
        "source"."custorder_id" AS "__endpoint_shipment_0",
        "source"."shipment_id" AS "__endpoint_shipment_1"
    FROM "relation_14" AS "source"
    WHERE ("source"."courier_shipments_courierpartner_id" IS NOT NULL)
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
        "source"."delivered_at" AS "delivered_at",
        "source"."tracking_no" AS "tracking_no",
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_14" AS "source"
)
SELECT 
    "b1"."carrier_code" AS "carrier_code",
    "b1"."webhook_url" AS "webhook_url",
    "b2"."tracking_no" AS "tracking_no"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
WHERE ("b2"."delivered_at" <= '2025-01-11');

-- Q049 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.product_id, e2.email FROM software_downloads r JOIN Software e1 ON ENDPOINT(r, Software) = REF(e1) JOIN Customer e2 ON ENDPOINT(r, Customer) = REF(e2) WHERE e1.product_name >= 'Re-contextualized asymmetric implementation';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_customer_0",
        "source"."software_id" AS "__endpoint_software_0"
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
        "source"."email" AS "email",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b1"."product_id" AS "product_id",
    "b2"."email" AS "email"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_software_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_customer_0" = "b2"."__reference_0"))
WHERE ("b1"."product_name" >= 'Re-contextualized asymmetric implementation');

-- Q050 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.carrier_code, e.courierpartner_id, e.webhook_url FROM CourierPartner e WHERE e.webhook_url >= 'https://www.cummings.com/';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."carrier_code" AS "carrier_code",
        "source"."courierpartner_id" AS "courierpartner_id",
        "source"."webhook_url" AS "webhook_url"
    FROM "relation_22" AS "source"
)
SELECT 
    "b0"."carrier_code" AS "carrier_code",
    "b0"."courierpartner_id" AS "courierpartner_id",
    "b0"."webhook_url" AS "webhook_url"
FROM "b0"
WHERE ("b0"."webhook_url" >= 'https://www.cummings.com/');

-- Q051 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.warehouse_id, e.region, e.warehouse_name FROM Warehouse e WHERE e.region > 'Southwest';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."region" AS "region",
        "source"."warehouse_id" AS "warehouse_id",
        "source"."warehouse_name" AS "warehouse_name"
    FROM "relation_17" AS "source"
)
SELECT DISTINCT 
    "b0"."warehouse_id" AS "warehouse_id",
    "b0"."region" AS "region",
    "b0"."warehouse_name" AS "warehouse_name"
FROM "b0"
WHERE ("b0"."region" > 'Southwest');

-- Q052 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.purchaseorder_id, e2.is_active, e3.tag_id FROM po_items r1 JOIN PurchaseOrder e1 ON ENDPOINT(r1, PurchaseOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN product_tags r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN Tag e3 ON ENDPOINT(r2, Tag) = REF(e3) WHERE e3.tag_id > 106964;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0"
    FROM "relation_32" AS "source"
),
"b1" AS (
    SELECT
        "source"."purchaseorder_id" AS "purchaseorder_id",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."tag_id" AS "__endpoint_tag_0"
    FROM "relation_23" AS "source"
),
"b4" AS (
    SELECT
        "source"."tag_id" AS "tag_id",
        "source"."tag_id" AS "__reference_0"
    FROM "relation_6" AS "source"
)
SELECT 
    "b1"."purchaseorder_id" AS "purchaseorder_id",
    "b2"."is_active" AS "is_active",
    "b4"."tag_id" AS "tag_id"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_purchaseorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_tag_0" = "b4"."__reference_0"))
WHERE ("b4"."tag_id" > 106964);

-- Q053 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.warranty_months, COUNT(DISTINCT REF(e1)) AS related_count FROM bundle_phones r JOIN Phone e1 ON ENDPOINT(r, phone_id) = REF(e1) JOIN Phone e2 ON ENDPOINT(r, bundle_phone_id) = REF(e2) WHERE e2.product_name <= 'Front-line bi-directional system engine' GROUP BY REF(e2), e2.warranty_months HAVING COUNT(DISTINCT REF(e1)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_phone_phone_id" AS "__endpoint_bundle_phone_id_0",
        "source"."phone_id" AS "__endpoint_phone_id_0"
    FROM "relation_33" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b2"."warranty_months" AS "warranty_months",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bundle_phone_id_0" = "b2"."__reference_0"))
WHERE ("b2"."product_name" <= 'Front-line bi-directional system engine')
GROUP BY
    "b2"."__reference_0",
    "b2"."warranty_months"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 2);

-- Q054 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.sku, COUNT(DISTINCT REF(e3)) AS related_count FROM po_items r1 JOIN PurchaseOrder e1 ON ENDPOINT(r1, PurchaseOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN bundle_components r2 ON ENDPOINT(r2, product_id) = REF(e2) JOIN Product e3 ON ENDPOINT(r2, bundle_product_id) = REF(e3) WHERE e3.sku >= 'SKU-klfZ-12422029' GROUP BY REF(e2), e2.sku HAVING COUNT(DISTINCT REF(e3)) >= 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0"
    FROM "relation_32" AS "source"
),
"b1" AS (
    SELECT
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
),
"b2" AS (
    SELECT
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."bundle_product_product_id" AS "__endpoint_bundle_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_24" AS "source"
),
"b4" AS (
    SELECT
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b2"."sku" AS "sku",
    COUNT(DISTINCT "b4"."__reference_0") AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_purchaseorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_id_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_bundle_product_id_0" = "b4"."__reference_0"))
WHERE ("b4"."sku" >= 'SKU-klfZ-12422029')
GROUP BY
    "b2"."__reference_0",
    "b2"."sku"
HAVING (COUNT(DISTINCT "b4"."__reference_0") >= 5);

-- Q055 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.supplier_id, COUNT(DISTINCT REF(e2)) AS related_count FROM supplier_products r JOIN Supplier e1 ON ENDPOINT(r, Supplier) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.product_name < 'Intuitive asynchronous task-force' GROUP BY REF(e1), e1.supplier_id HAVING COUNT(DISTINCT REF(e2)) >= 4;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_31" AS "source"
),
"b1" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."supplier_id" AS "supplier_id",
    COUNT(DISTINCT "b2"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."product_name" < 'Intuitive asynchronous task-force')
GROUP BY
    "b1"."__reference_0",
    "b1"."supplier_id"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 4);

-- Q056 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.password_hash, e.user_id, e.loyalty_tier, e.email FROM Customer e WHERE e.loyalty_tier > 'platinum';
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
    "b0"."password_hash" AS "password_hash",
    "b0"."user_id" AS "user_id",
    "b0"."loyalty_tier" AS "loyalty_tier",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."loyalty_tier" > 'platinum');

-- Q057 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.placed_at, e2.is_active FROM order_items r JOIN CustOrder e1 ON ENDPOINT(r, CustOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.status > 'returned';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_28" AS "source"
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
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."placed_at" AS "placed_at",
    "b2"."is_active" AS "is_active"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."status" > 'returned');

-- Q058 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.loyalty_tier, e2.status FROM customer_orders r JOIN Customer e1 ON ENDPOINT(r, Customer) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.email > 'uhunt@example.org';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_13" AS "source"
    WHERE ("source"."customer_orders_customer_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
),
"b2" AS (
    SELECT
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b1"."loyalty_tier" AS "loyalty_tier",
    "b2"."status" AS "status"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."email" > 'uhunt@example.org');

-- Q059 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.updated_at, e1.cart_id, e2.product_id FROM cart_contains r JOIN Cart e1 ON ENDPOINT(r, Cart) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.sku >= 'SKU-vFdW-79279946';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_cart_0",
        "source"."cart_id" AS "__endpoint_cart_1",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_26" AS "source"
),
"b1" AS (
    SELECT
        "source"."cart_id" AS "cart_id",
        "source"."updated_at" AS "updated_at",
        "source"."user_id" AS "__reference_0",
        "source"."cart_id" AS "__reference_1"
    FROM "relation_9" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."updated_at" AS "updated_at",
    "b1"."cart_id" AS "cart_id",
    "b2"."product_id" AS "product_id"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_cart_0" = "b1"."__reference_0" AND "b0"."__endpoint_cart_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."sku" >= 'SKU-vFdW-79279946');

-- Q060 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.ends_at FROM Promotion e WHERE e.starts_at <= '2024-04-21';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ends_at" AS "ends_at",
        "source"."starts_at" AS "starts_at"
    FROM "relation_15" AS "source"
)
SELECT 
    "b0"."ends_at" AS "ends_at"
FROM "b0"
WHERE ("b0"."starts_at" <= '2024-04-21');

-- Q061 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.bin_id, e2.base_price, e3.product_id FROM stock r1 JOIN WarehouseBin e1 ON ENDPOINT(r1, WarehouseBin) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN bundle_components r2 ON ENDPOINT(r2, bundle_product_id) = REF(e2) JOIN Product e3 ON ENDPOINT(r2, product_id) = REF(e3) WHERE e3.is_active >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."warehouse_id" AS "__endpoint_warehousebin_0",
        "source"."bin_id" AS "__endpoint_warehousebin_1"
    FROM "relation_30" AS "source"
),
"b1" AS (
    SELECT
        "source"."bin_id" AS "bin_id",
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
        "source"."bundle_product_product_id" AS "__endpoint_bundle_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_24" AS "source"
),
"b4" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."bin_id" AS "bin_id",
    "b2"."base_price" AS "base_price",
    "b4"."product_id" AS "product_id"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_warehousebin_0" = "b1"."__reference_0" AND "b0"."__endpoint_warehousebin_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_bundle_product_id_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_id_0" = "b4"."__reference_0"))
WHERE ("b4"."is_active" >= 1);

-- Q062 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.wishlist_name, o.loyalty_tier FROM Wishlist w JOIN Customer o ON OWNER(w) = REF(o) WHERE w.wishlist_name > 'default';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."wishlist_name" AS "wishlist_name",
        "source"."user_id" AS "__owner_0"
    FROM "relation_10" AS "source"
),
"b1" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."wishlist_name" AS "wishlist_name",
    "b1"."loyalty_tier" AS "loyalty_tier"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."wishlist_name" > 'default');

-- Q063 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.status, e1.placed_at, e2.sku FROM order_items r JOIN CustOrder e1 ON ENDPOINT(r, CustOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.status >= 'paid';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_28" AS "source"
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
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."status" AS "status",
    "b1"."placed_at" AS "placed_at",
    "b2"."sku" AS "sku"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."status" >= 'paid');

-- Q064 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id FROM Footwear e WHERE e.product_id >= 15719843;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."product_id" >= 15719843);

-- Q065 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.product_name, e1.quantity, e2.product_id FROM bought_together r JOIN Product e1 ON ENDPOINT(r, product_id) = REF(e1) JOIN Product e2 ON ENDPOINT(r, bought_together_product_id) = REF(e2) WHERE e1.quantity >= 30;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
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
        "source"."product_id" AS "product_id",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    "b1"."quantity" AS "quantity",
    "b2"."product_id" AS "product_id"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bought_together_product_id_0" = "b2"."__reference_0"))
WHERE ("b1"."quantity" >= 30);

-- Q066 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.quantity, e.size_system FROM MenClothing e WHERE e.fit_type_men <= 'athletic';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."fit_type_men" AS "fit_type_men",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."quantity" AS "quantity",
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."fit_type_men" <= 'athletic');

-- Q067 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.sku, COUNT(DISTINCT REF(e2)) AS related_count FROM reviews r JOIN Product e1 ON ENDPOINT(r, Product) = REF(e1) JOIN Review e2 ON ENDPOINT(r, Review) = REF(e2) WHERE e1.quantity >= 30 GROUP BY REF(e1), e1.sku HAVING COUNT(DISTINCT REF(e2)) >= 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."reviews_product_id" AS "__endpoint_product_0",
        "source"."user_id" AS "__endpoint_review_0",
        "source"."review_id" AS "__endpoint_review_1"
    FROM "relation_11" AS "source"
    WHERE ("source"."reviews_product_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."user_id" AS "__reference_0",
        "source"."review_id" AS "__reference_1"
    FROM "relation_11" AS "source"
)
SELECT 
    "b1"."sku" AS "sku",
    COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_review_0" = "b2"."__reference_0" AND "b0"."__endpoint_review_1" = "b2"."__reference_1"))
WHERE ("b1"."quantity" >= 30)
GROUP BY
    "b1"."__reference_0",
    "b1"."sku"
HAVING (COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) >= 3);

-- Q068 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.cart_id, w.updated_at, o.user_id, o.loyalty_tier FROM Cart w JOIN Customer o ON OWNER(w) = REF(o) WHERE o.user_id >= 1111339;
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
    "b0"."cart_id" AS "cart_id",
    "b0"."updated_at" AS "updated_at",
    "b1"."user_id" AS "user_id",
    "b1"."loyalty_tier" AS "loyalty_tier"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."user_id" >= 1111339);

-- Q069 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.wishlist_name, e2.product_id, e3.cart_id FROM wishlist_contains r1 JOIN Wishlist e1 ON ENDPOINT(r1, Wishlist) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN cart_contains r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN Cart e3 ON ENDPOINT(r2, Cart) = REF(e3) WHERE e3.cart_id > 5998881;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_wishlist_0",
        "source"."wishlist_id" AS "__endpoint_wishlist_1"
    FROM "relation_27" AS "source"
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
        "source"."product_id" AS "product_id",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_cart_0",
        "source"."cart_id" AS "__endpoint_cart_1",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_26" AS "source"
),
"b4" AS (
    SELECT
        "source"."cart_id" AS "cart_id",
        "source"."user_id" AS "__reference_0",
        "source"."cart_id" AS "__reference_1"
    FROM "relation_9" AS "source"
)
SELECT 
    "b1"."wishlist_name" AS "wishlist_name",
    "b2"."product_id" AS "product_id",
    "b4"."cart_id" AS "cart_id"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_wishlist_0" = "b1"."__reference_0" AND "b0"."__endpoint_wishlist_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_cart_0" = "b4"."__reference_0" AND "b3"."__endpoint_cart_1" = "b4"."__reference_1"))
WHERE ("b4"."cart_id" > 5998881);

-- Q070 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.is_active, COUNT(DISTINCT REF(e2)) AS related_count FROM bundle_phones r JOIN Phone e1 ON ENDPOINT(r, phone_id) = REF(e1) JOIN Phone e2 ON ENDPOINT(r, bundle_phone_id) = REF(e2) WHERE e2.base_price >= 245 GROUP BY REF(e1), e1.is_active HAVING COUNT(DISTINCT REF(e2)) >= 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_phone_phone_id" AS "__endpoint_bundle_phone_id_0",
        "source"."phone_id" AS "__endpoint_phone_id_0"
    FROM "relation_33" AS "source"
),
"b1" AS (
    SELECT
        "source"."is_active" AS "is_active",
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
    "b1"."is_active" AS "is_active",
    COUNT(DISTINCT "b2"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bundle_phone_id_0" = "b2"."__reference_0"))
WHERE ("b2"."base_price" >= 245)
GROUP BY
    "b1"."__reference_0",
    "b1"."is_active"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 3);

-- Q071 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.bin_id FROM WarehouseBin w WHERE w.bin_id >= 5974866;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bin_id" AS "bin_id"
    FROM "relation_18" AS "source"
)
SELECT 
    "b0"."bin_id" AS "bin_id"
FROM "b0"
WHERE ("b0"."bin_id" >= 5974866);

-- Q072 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.exp_month, w.last4, o.user_id, o.loyalty_tier FROM PaymentMethod w JOIN Customer o ON OWNER(w) = REF(o) WHERE w.is_default > 'false';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."exp_month" AS "exp_month",
        "source"."is_default" AS "is_default",
        "source"."last4" AS "last4",
        "source"."user_id" AS "__owner_0"
    FROM "relation_8" AS "source"
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
    "b0"."exp_month" AS "exp_month",
    "b0"."last4" AS "last4",
    "b1"."user_id" AS "user_id",
    "b1"."loyalty_tier" AS "loyalty_tier"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."is_default" > 'false');

-- Q073 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.tag_id, e.tag_name FROM Tag e WHERE e.tag_name > 'sale';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."tag_id" AS "tag_id",
        "source"."tag_name" AS "tag_name"
    FROM "relation_6" AS "source"
)
SELECT 
    "b0"."tag_id" AS "tag_id",
    "b0"."tag_name" AS "tag_name"
FROM "b0"
WHERE ("b0"."tag_name" > 'sale');

-- Q074 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.city, w.kind, w.state, o.loyalty_tier, o.email FROM Address w JOIN Customer o ON OWNER(w) = REF(o) WHERE o.loyalty_tier <= 'bronze';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."city" AS "city",
        "source"."kind" AS "kind",
        "source"."state" AS "state",
        "source"."user_id" AS "__owner_0"
    FROM "relation_7" AS "source"
),
"b1" AS (
    SELECT
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."email" AS "email",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."city" AS "city",
    "b0"."kind" AS "kind",
    "b0"."state" AS "state",
    "b1"."loyalty_tier" AS "loyalty_tier",
    "b1"."email" AS "email"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."loyalty_tier" <= 'bronze');

-- Q075 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.created_at, COUNT(DISTINCT REF(e1)) AS related_count FROM supplier_pos r JOIN Supplier e1 ON ENDPOINT(r, Supplier) = REF(e1) JOIN PurchaseOrder e2 ON ENDPOINT(r, PurchaseOrder) = REF(e2) WHERE e2.purchaseorder_id > 106773 GROUP BY REF(e2), e2.created_at HAVING COUNT(DISTINCT REF(e1)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0",
        "source"."supplier_pos_supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_21" AS "source"
    WHERE ("source"."supplier_pos_supplier_id" IS NOT NULL)
),
"b1" AS (
    SELECT
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
    "b2"."created_at" AS "created_at",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_purchaseorder_0" = "b2"."__reference_0"))
WHERE ("b2"."purchaseorder_id" > 106773)
GROUP BY
    "b2"."__reference_0",
    "b2"."created_at"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 2);

-- Q076 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.cart_id, e1.updated_at, e2.base_price, e2.product_name FROM cart_contains r JOIN Cart e1 ON ENDPOINT(r, Cart) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.is_active > 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_cart_0",
        "source"."cart_id" AS "__endpoint_cart_1",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_26" AS "source"
),
"b1" AS (
    SELECT
        "source"."cart_id" AS "cart_id",
        "source"."updated_at" AS "updated_at",
        "source"."user_id" AS "__reference_0",
        "source"."cart_id" AS "__reference_1"
    FROM "relation_9" AS "source"
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."cart_id" AS "cart_id",
    "b1"."updated_at" AS "updated_at",
    "b2"."base_price" AS "base_price",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_cart_0" = "b1"."__reference_0" AND "b0"."__endpoint_cart_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."is_active" > 0);

-- Q077 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.purchaseorder_id, e.created_at FROM PurchaseOrder e WHERE e.purchaseorder_id >= 120363;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."purchaseorder_id" AS "purchaseorder_id"
    FROM "relation_21" AS "source"
)
SELECT 
    "b0"."purchaseorder_id" AS "purchaseorder_id",
    "b0"."created_at" AS "created_at"
FROM "b0"
WHERE ("b0"."purchaseorder_id" >= 120363);

-- Q078 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.purchaseorder_id, e2.is_active, e3.is_active FROM po_items r1 JOIN PurchaseOrder e1 ON ENDPOINT(r1, PurchaseOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN bought_together r2 ON ENDPOINT(r2, product_id) = REF(e2) JOIN Product e3 ON ENDPOINT(r2, bought_together_product_id) = REF(e3) WHERE e3.product_name < 'Object-based 3rdgeneration instruction set';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0"
    FROM "relation_32" AS "source"
),
"b1" AS (
    SELECT
        "source"."purchaseorder_id" AS "purchaseorder_id",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
),
"b4" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."purchaseorder_id" AS "purchaseorder_id",
    "b2"."is_active" AS "is_active",
    "b4"."is_active" AS "is_active"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_purchaseorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_id_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_bought_together_product_id_0" = "b4"."__reference_0"))
WHERE ("b4"."product_name" < 'Object-based 3rdgeneration instruction set');

-- Q079 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.shipped_at, o.custorder_id, o.status FROM Shipment w JOIN CustOrder o ON OWNER(w) = REF(o) WHERE w.shipped_at < '2022-07-08';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."shipped_at" AS "shipped_at",
        "source"."custorder_id" AS "__owner_0"
    FROM "relation_14" AS "source"
),
"b1" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b0"."shipped_at" AS "shipped_at",
    "b1"."custorder_id" AS "custorder_id",
    "b1"."status" AS "status"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."shipped_at" < '2022-07-08');

-- Q080 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.quantity, e1.dimensions, e2.accessory_type, e2.product_name FROM bundled_phone_accessory r JOIN Phone e1 ON ENDPOINT(r, Phone) = REF(e1) JOIN Accessory e2 ON ENDPOINT(r, Accessory) = REF(e2) WHERE e2.quantity > 22;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."accessory_id" AS "__endpoint_accessory_0",
        "source"."phone_id" AS "__endpoint_phone_0"
    FROM "relation_34" AS "source"
),
"b1" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b1"."quantity" AS "quantity",
    "b1"."dimensions" AS "dimensions",
    "b2"."accessory_type" AS "accessory_type",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_accessory_0" = "b2"."__reference_0"))
WHERE ("b2"."quantity" > 22);

-- Q081 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.custorder_id, e2.quantity, e2.product_name FROM order_returns r JOIN CustOrder e1 ON ENDPOINT(r, CustOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.base_price < 41;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_29" AS "source"
),
"b1" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
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
    "b1"."custorder_id" AS "custorder_id",
    "b2"."quantity" AS "quantity",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."base_price" < 41);

-- Q082 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.delivery_type, e.product_name, e.product_id FROM Media e WHERE e.format >= 'video';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."format" AS "format",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
)
SELECT 
    "b0"."delivery_type" AS "delivery_type",
    "b0"."product_name" AS "product_name",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."format" >= 'video');

-- Q083 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warehouse_name FROM Warehouse e WHERE e.warehouse_name > 'Lewis-Hartman';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."warehouse_name" AS "warehouse_name"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."warehouse_name" AS "warehouse_name"
FROM "b0"
WHERE ("b0"."warehouse_name" > 'Lewis-Hartman');

-- Q084 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.wishlist_id, w.wishlist_name, o.loyalty_tier FROM Wishlist w JOIN Customer o ON OWNER(w) = REF(o) WHERE o.email < 'jeffreybryant@example.com';
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
        "source"."email" AS "email",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."wishlist_id" AS "wishlist_id",
    "b0"."wishlist_name" AS "wishlist_name",
    "b1"."loyalty_tier" AS "loyalty_tier"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."email" < 'jeffreybryant@example.com');

-- Q085 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.custorder_id, e2.product_id, e3.product_name FROM order_items r1 JOIN CustOrder e1 ON ENDPOINT(r1, CustOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN bought_together r2 ON ENDPOINT(r2, bought_together_product_id) = REF(e2) JOIN Product e3 ON ENDPOINT(r2, product_id) = REF(e3) WHERE e2.product_id >= 10098074;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_28" AS "source"
),
"b1" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
),
"b4" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."custorder_id" AS "custorder_id",
    "b2"."product_id" AS "product_id",
    "b4"."product_name" AS "product_name"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_bought_together_product_id_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_id_0" = "b4"."__reference_0"))
WHERE ("b2"."product_id" >= 10098074);

-- Q086 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.ram_gb FROM Desktop e WHERE e.product_id > 10269581;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ram_gb" AS "ram_gb",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('desktop'))
)
SELECT 
    "b0"."ram_gb" AS "ram_gb"
FROM "b0"
WHERE ("b0"."product_id" > 10269581);

-- Q087 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.is_active FROM KitchenAppliance e WHERE e.product_id >= 13097966;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('kitchenappliance'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_id" >= 13097966);

-- Q088 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.code, w.bin_id, o.warehouse_name FROM WarehouseBin w JOIN Warehouse o ON OWNER(w) = REF(o) WHERE o.warehouse_id <= 26870;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bin_id" AS "bin_id",
        "source"."code" AS "code",
        "source"."warehouse_id" AS "__owner_0"
    FROM "relation_18" AS "source"
),
"b1" AS (
    SELECT
        "source"."warehouse_id" AS "warehouse_id",
        "source"."warehouse_name" AS "warehouse_name",
        "source"."warehouse_id" AS "__reference_0"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."code" AS "code",
    "b0"."bin_id" AS "bin_id",
    "b1"."warehouse_name" AS "warehouse_name"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."warehouse_id" <= 26870);

-- Q089 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.base_price, e.is_active, e.product_id FROM Product e WHERE e.is_active >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."base_price" AS "base_price",
    "b0"."is_active" AS "is_active",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."is_active" >= 1);

-- Q090 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.sku, e1.quantity, e2.bin_id, e2.code FROM stock r JOIN Product e1 ON ENDPOINT(r, Product) = REF(e1) JOIN WarehouseBin e2 ON ENDPOINT(r, WarehouseBin) = REF(e2) WHERE e1.product_id < 3392411;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."warehouse_id" AS "__endpoint_warehousebin_0",
        "source"."bin_id" AS "__endpoint_warehousebin_1"
    FROM "relation_30" AS "source"
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
        "source"."bin_id" AS "bin_id",
        "source"."code" AS "code",
        "source"."warehouse_id" AS "__reference_0",
        "source"."bin_id" AS "__reference_1"
    FROM "relation_18" AS "source"
)
SELECT 
    "b1"."sku" AS "sku",
    "b1"."quantity" AS "quantity",
    "b2"."bin_id" AS "bin_id",
    "b2"."code" AS "code"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_warehousebin_0" = "b2"."__reference_0" AND "b0"."__endpoint_warehousebin_1" = "b2"."__reference_1"))
WHERE ("b1"."product_id" < 3392411);

-- Q091 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.parent, e2.sku, e3.tag_name FROM category_products r1 JOIN Category e1 ON ENDPOINT(r1, Category) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN product_tags r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN Tag e3 ON ENDPOINT(r2, Tag) = REF(e3) WHERE e2.is_active >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."category_products_category_id" AS "__endpoint_category_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."category_products_category_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."parent" AS "parent",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."tag_id" AS "__endpoint_tag_0"
    FROM "relation_23" AS "source"
),
"b4" AS (
    SELECT
        "source"."tag_name" AS "tag_name",
        "source"."tag_id" AS "__reference_0"
    FROM "relation_6" AS "source"
)
SELECT 
    "b1"."parent" AS "parent",
    "b2"."sku" AS "sku",
    "b4"."tag_name" AS "tag_name"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_tag_0" = "b4"."__reference_0"))
WHERE ("b2"."is_active" >= 1);

-- Q092 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.is_active, e2.product_name, e2.dimensions FROM bundle_phones r JOIN Phone e1 ON ENDPOINT(r, phone_id) = REF(e1) JOIN Phone e2 ON ENDPOINT(r, bundle_phone_id) = REF(e2) WHERE e2.warranty_months > 12;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_phone_phone_id" AS "__endpoint_bundle_phone_id_0",
        "source"."phone_id" AS "__endpoint_phone_id_0"
    FROM "relation_33" AS "source"
),
"b1" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."dimensions" AS "dimensions",
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT 
    "b1"."is_active" AS "is_active",
    "b2"."product_name" AS "product_name",
    "b2"."dimensions" AS "dimensions"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bundle_phone_id_0" = "b2"."__reference_0"))
WHERE ("b2"."warranty_months" > 12);

-- Q093 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.sku, COUNT(DISTINCT REF(e2)) AS related_count FROM reviews r JOIN Product e1 ON ENDPOINT(r, Product) = REF(e1) JOIN Review e2 ON ENDPOINT(r, Review) = REF(e2) WHERE e2.review_id <= 3997278 GROUP BY REF(e1), e1.sku HAVING COUNT(DISTINCT REF(e2)) >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."reviews_product_id" AS "__endpoint_product_0",
        "source"."user_id" AS "__endpoint_review_0",
        "source"."review_id" AS "__endpoint_review_1"
    FROM "relation_11" AS "source"
    WHERE ("source"."reviews_product_id" IS NOT NULL)
),
"b1" AS (
    SELECT
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."review_id" AS "review_id",
        "source"."user_id" AS "__reference_0",
        "source"."review_id" AS "__reference_1"
    FROM "relation_11" AS "source"
)
SELECT 
    "b1"."sku" AS "sku",
    COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_review_0" = "b2"."__reference_0" AND "b0"."__endpoint_review_1" = "b2"."__reference_1"))
WHERE ("b2"."review_id" <= 3997278)
GROUP BY
    "b1"."__reference_0",
    "b1"."sku"
HAVING (COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) >= 1);

-- Q094 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.shipment_id, o.status FROM Shipment w JOIN CustOrder o ON OWNER(w) = REF(o) WHERE o.placed_at <= '2023-05-03';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."shipment_id" AS "shipment_id",
        "source"."custorder_id" AS "__owner_0"
    FROM "relation_14" AS "source"
),
"b1" AS (
    SELECT
        "source"."placed_at" AS "placed_at",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b0"."shipment_id" AS "shipment_id",
    "b1"."status" AS "status"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."placed_at" <= '2023-05-03');

-- Q095 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.password_hash, e.employee_no, e.user_id FROM Employee e WHERE e.employee_no <= 'EMP-09774576';
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
    "b0"."password_hash" AS "password_hash",
    "b0"."employee_no" AS "employee_no",
    "b0"."user_id" AS "user_id"
FROM "b0"
WHERE ("b0"."employee_no" <= 'EMP-09774576');

-- Q096 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.updated_at, COUNT(DISTINCT REF(e2)) AS related_count FROM cart_contains r JOIN Cart e1 ON ENDPOINT(r, Cart) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.cart_id > 4994665 GROUP BY REF(e1), e1.updated_at HAVING COUNT(DISTINCT REF(e2)) >= 3;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."customer_id" AS "__endpoint_cart_0",
        "source"."cart_id" AS "__endpoint_cart_1",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_26" AS "source"
),
"b1" AS (
    SELECT
        "source"."cart_id" AS "cart_id",
        "source"."updated_at" AS "updated_at",
        "source"."user_id" AS "__reference_0",
        "source"."cart_id" AS "__reference_1"
    FROM "relation_9" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."updated_at" AS "updated_at",
    COUNT(DISTINCT "b2"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_cart_0" = "b1"."__reference_0" AND "b0"."__endpoint_cart_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."cart_id" > 4994665)
GROUP BY
    "b1"."__reference_0",
    "b1"."__reference_1",
    "b1"."updated_at"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 3);

-- Q097 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.bin_id, e2.is_active, e3.quantity FROM stock r1 JOIN WarehouseBin e1 ON ENDPOINT(r1, WarehouseBin) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN bought_together r2 ON ENDPOINT(r2, bought_together_product_id) = REF(e2) JOIN Product e3 ON ENDPOINT(r2, product_id) = REF(e3) WHERE e1.bin_id <= 4985556;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."warehouse_id" AS "__endpoint_warehousebin_0",
        "source"."bin_id" AS "__endpoint_warehousebin_1"
    FROM "relation_30" AS "source"
),
"b1" AS (
    SELECT
        "source"."bin_id" AS "bin_id",
        "source"."warehouse_id" AS "__reference_0",
        "source"."bin_id" AS "__reference_1"
    FROM "relation_18" AS "source"
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."bought_together_product_product_id" AS "__endpoint_bought_together_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
),
"b4" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."bin_id" AS "bin_id",
    "b2"."is_active" AS "is_active",
    "b4"."quantity" AS "quantity"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_warehousebin_0" = "b1"."__reference_0" AND "b0"."__endpoint_warehousebin_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_bought_together_product_id_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_id_0" = "b4"."__reference_0"))
WHERE ("b1"."bin_id" <= 4985556);

-- Q098 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id, e.password_hash FROM User e WHERE e.password_hash < '663fbac28ef983d2a9a257a1fdfe87d570db7cf21f735454baaba71abfbbe744';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id"
    FROM "relation_2" AS "source"
)
SELECT 
    "b0"."user_id" AS "user_id",
    "b0"."password_hash" AS "password_hash"
FROM "b0"
WHERE ("b0"."password_hash" < '663fbac28ef983d2a9a257a1fdfe87d570db7cf21f735454baaba71abfbbe744');

-- Q099 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sku FROM Apparel e WHERE e.is_active < 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear'))
)
SELECT DISTINCT 
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."is_active" < 1);

-- Q100 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.bin_id, w.code, o.warehouse_name FROM WarehouseBin w JOIN Warehouse o ON OWNER(w) = REF(o) WHERE w.code < 'Pl-104-pP';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bin_id" AS "bin_id",
        "source"."code" AS "code",
        "source"."warehouse_id" AS "__owner_0"
    FROM "relation_18" AS "source"
),
"b1" AS (
    SELECT
        "source"."warehouse_name" AS "warehouse_name",
        "source"."warehouse_id" AS "__reference_0"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."bin_id" AS "bin_id",
    "b0"."code" AS "code",
    "b1"."warehouse_name" AS "warehouse_name"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."code" < 'Pl-104-pP');

ROLLBACK;
