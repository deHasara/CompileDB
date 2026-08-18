\set ON_ERROR_STOP on
\pset pager off
-- CompileDB mapping-aware relational workload
-- Conceptual workload: example2_schema_driven_selectivity_100_w09
-- Mapping ID: f015fd00db116d7c19ae94a5f40a6e34250534220293ca53b7b6086b1499e981
-- Query shapes: 100
-- Executed statements: 100
BEGIN TRANSACTION READ ONLY;

-- Q001 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.dimensions, e.is_active FROM Appliance e WHERE e.energy_rating > 'A';
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
    "b0"."product_name" AS "product_name",
    "b0"."dimensions" AS "dimensions",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."energy_rating" > 'A');

-- Q002 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.device, w.session_id, o.password_hash FROM BrowsingSession w JOIN User o ON OWNER(w) = REF(o) WHERE o.password_hash >= '19c716d8af3d5dce1f622af1acde19736a8d049634907253b387fce96f7c5251';
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
WHERE ("b1"."password_hash" >= '19c716d8af3d5dce1f622af1acde19736a8d049634907253b387fce96f7c5251');

-- Q003 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.password_hash, COUNT(DISTINCT REF(e3)) AS related_count FROM software_downloads r1 JOIN Software e1 ON ENDPOINT(r1, Software) = REF(e1) JOIN PrimeCustomer e2 ON ENDPOINT(r1, Customer) = REF(e2) JOIN customer_orders r2 ON ENDPOINT(r2, Customer) = REF(e2) JOIN CustOrder e3 ON ENDPOINT(r2, CustOrder) = REF(e3) WHERE e1.license_type < 'subscription' GROUP BY REF(e2), e2.password_hash HAVING COUNT(DISTINCT REF(e3)) >= 1;
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
        "source"."license_type" AS "license_type",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
),
"b2" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
),
"b3" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_30" AS "source"
),
"b4" AS (
    SELECT
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b2"."password_hash" AS "password_hash",
    COUNT(DISTINCT "b4"."__reference_0") AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_software_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_customer_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_customer_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_custorder_0" = "b4"."__reference_0"))
WHERE ("b1"."license_type" < 'subscription')
GROUP BY
    "b2"."__reference_0",
    "b2"."password_hash"
HAVING (COUNT(DISTINCT "b4"."__reference_0") >= 1);

-- Q004 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.webhook_url, COUNT(DISTINCT REF(e2)) AS related_count FROM courier_shipments r JOIN CourierPartner e1 ON ENDPOINT(r, CourierPartner) = REF(e1) JOIN Shipment e2 ON ENDPOINT(r, Shipment) = REF(e2) WHERE e1.courierpartner_id <= 31533 GROUP BY REF(e1), e1.webhook_url HAVING COUNT(DISTINCT REF(e2)) >= 3;
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
        "source"."courierpartner_id" AS "courierpartner_id",
        "source"."webhook_url" AS "webhook_url",
        "source"."courierpartner_id" AS "__reference_0"
    FROM "relation_22" AS "source"
),
"b2" AS (
    SELECT
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_14" AS "source"
)
SELECT 
    "b1"."webhook_url" AS "webhook_url",
    COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
WHERE ("b1"."courierpartner_id" <= 31533)
GROUP BY
    "b1"."__reference_0",
    "b1"."webhook_url"
HAVING (COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) >= 3);

-- Q005 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.courierpartner_id, COUNT(DISTINCT REF(e2)) AS related_count FROM courier_shipments r JOIN CourierPartner e1 ON ENDPOINT(r, CourierPartner) = REF(e1) JOIN Shipment e2 ON ENDPOINT(r, Shipment) = REF(e2) WHERE e2.shipped_at > '2023-02-11' GROUP BY REF(e1), e1.courierpartner_id HAVING COUNT(DISTINCT REF(e2)) >= 2;
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
        "source"."courierpartner_id" AS "courierpartner_id",
        "source"."courierpartner_id" AS "__reference_0"
    FROM "relation_22" AS "source"
),
"b2" AS (
    SELECT
        "source"."shipped_at" AS "shipped_at",
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_14" AS "source"
)
SELECT 
    "b1"."courierpartner_id" AS "courierpartner_id",
    COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
WHERE ("b2"."shipped_at" > '2023-02-11')
GROUP BY
    "b1"."__reference_0",
    "b1"."courierpartner_id"
HAVING (COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) >= 2);

-- Q006 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.cart_id, o.email FROM Cart w JOIN BusinessCustomer o ON OWNER(w) = REF(o) WHERE w.cart_id < 5999287;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cart_id" AS "cart_id",
        "source"."user_id" AS "__owner_0"
    FROM "relation_9" AS "source"
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."cart_id" AS "cart_id",
    "b1"."email" AS "email"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."cart_id" < 5999287);

-- Q007 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.user_id, e2.custorder_id, e3.last4 FROM customer_orders r1 JOIN Customer e1 ON ENDPOINT(r1, Customer) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r1, CustOrder) = REF(e2) JOIN payment_order r2 ON ENDPOINT(r2, CustOrder) = REF(e2) JOIN PaymentMethod e3 ON ENDPOINT(r2, PaymentMethod) = REF(e3) WHERE e1.loyalty_tier < 'silver';
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
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."user_id" AS "user_id",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
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
        "source"."payment_order_customer_id" AS "__endpoint_paymentmethod_0",
        "source"."payment_order_payment_method_id" AS "__endpoint_paymentmethod_1"
    FROM "relation_32" AS "source"
),
"b4" AS (
    SELECT
        "source"."last4" AS "last4",
        "source"."user_id" AS "__reference_0",
        "source"."payment_method_id" AS "__reference_1"
    FROM "relation_8" AS "source"
)
SELECT 
    "b1"."user_id" AS "user_id",
    "b2"."custorder_id" AS "custorder_id",
    "b4"."last4" AS "last4"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_paymentmethod_0" = "b4"."__reference_0" AND "b3"."__endpoint_paymentmethod_1" = "b4"."__reference_1"))
WHERE ("b1"."loyalty_tier" < 'silver');

-- Q008 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.quantity, COUNT(DISTINCT REF(e1)) AS related_count FROM category_products r JOIN Category e1 ON ENDPOINT(r, Category) = REF(e1) JOIN Footwear e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.category_name <= 'top' GROUP BY REF(e2), e2.quantity HAVING COUNT(DISTINCT REF(e1)) >= 5;
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
        "source"."category_name" AS "category_name",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
),
"b2" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
)
SELECT 
    "b2"."quantity" AS "quantity",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."category_name" <= 'top')
GROUP BY
    "b2"."__reference_0",
    "b2"."quantity"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 5);

-- Q009 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.wishlist_name, o.user_id FROM Wishlist w JOIN Customer o ON OWNER(w) = REF(o) WHERE w.wishlist_id < 6015590;
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
        "source"."user_id" AS "user_id",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b0"."wishlist_name" AS "wishlist_name",
    "b1"."user_id" AS "user_id"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."wishlist_id" < 6015590);

-- Q010 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.email, e2.custorder_id FROM customer_orders r JOIN Customer e1 ON ENDPOINT(r, Customer) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e2.custorder_id <= 48572;
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
    "b1"."email" AS "email",
    "b2"."custorder_id" AS "custorder_id"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b2"."custorder_id" <= 48572);

-- Q011 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.supplier_name, e2.created_at FROM supplier_pos r JOIN Supplier e1 ON ENDPOINT(r, Supplier) = REF(e1) JOIN PurchaseOrder e2 ON ENDPOINT(r, PurchaseOrder) = REF(e2) WHERE e1.supplier_name >= 'Gonzalez and Sons';
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
        "source"."supplier_name" AS "supplier_name",
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
),
"b2" AS (
    SELECT
        "source"."created_at" AS "created_at",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
)
SELECT 
    "b1"."supplier_name" AS "supplier_name",
    "b2"."created_at" AS "created_at"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_supplier_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_purchaseorder_0" = "b2"."__reference_0"))
WHERE ("b1"."supplier_name" >= 'Gonzalez and Sons');

-- Q012 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.title, e2.format, e3.wishlist_name FROM reviews r1 JOIN Review e1 ON ENDPOINT(r1, Review) = REF(e1) JOIN Media e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN wishlist_contains r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN Wishlist e3 ON ENDPOINT(r2, Wishlist) = REF(e3) WHERE e3.wishlist_id >= 3999749;
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
        "source"."title" AS "title",
        "source"."user_id" AS "__reference_0",
        "source"."review_id" AS "__reference_1"
    FROM "relation_11" AS "source"
),
"b2" AS (
    SELECT
        "source"."format" AS "format",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_wishlist_0",
        "source"."wishlist_id" AS "__endpoint_wishlist_1"
    FROM "relation_28" AS "source"
),
"b4" AS (
    SELECT
        "source"."wishlist_id" AS "wishlist_id",
        "source"."wishlist_name" AS "wishlist_name",
        "source"."user_id" AS "__reference_0",
        "source"."wishlist_id" AS "__reference_1"
    FROM "relation_10" AS "source"
)
SELECT 
    "b1"."title" AS "title",
    "b2"."format" AS "format",
    "b4"."wishlist_name" AS "wishlist_name"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_review_0" = "b1"."__reference_0" AND "b0"."__endpoint_review_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_wishlist_0" = "b4"."__reference_0" AND "b3"."__endpoint_wishlist_1" = "b4"."__reference_1"))
WHERE ("b4"."wishlist_id" >= 3999749);

-- Q013 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.sku, e1.warranty_months, e2.warranty_months FROM bought_together r JOIN Camera e1 ON ENDPOINT(r, product_id) = REF(e1) JOIN Electronics e2 ON ENDPOINT(r, bought_together_product_id) = REF(e2) WHERE e2.is_active >= 1;
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
        "source"."warranty_months" AS "warranty_months",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
),
"b2" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b1"."sku" AS "sku",
    "b1"."warranty_months" AS "warranty_months",
    "b2"."warranty_months" AS "warranty_months"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bought_together_product_id_0" = "b2"."__reference_0"))
WHERE ("b2"."is_active" >= 1);

-- Q014 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.status, COUNT(DISTINCT REF(e1)) AS related_count FROM payment_order r JOIN PaymentMethod e1 ON ENDPOINT(r, PaymentMethod) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.is_default <= 'false' GROUP BY REF(e2), e2.status HAVING COUNT(DISTINCT REF(e1)) >= 4;
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
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b2"."status" AS "status",
    COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_paymentmethod_0" = "b1"."__reference_0" AND "b0"."__endpoint_paymentmethod_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."is_default" <= 'false')
GROUP BY
    "b2"."__reference_0",
    "b2"."status"
HAVING (COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) >= 4);

-- Q015 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.sku, COUNT(DISTINCT REF(e3)) AS related_count FROM bundle_components r1 JOIN Product e1 ON ENDPOINT(r1, bundle_product_id) = REF(e1) JOIN Footwear e2 ON ENDPOINT(r1, product_id) = REF(e2) JOIN po_items r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN PurchaseOrder e3 ON ENDPOINT(r2, PurchaseOrder) = REF(e3) WHERE e2.dimensions > 'large' GROUP BY REF(e2), e2.sku HAVING COUNT(DISTINCT REF(e3)) >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_product_product_id" AS "__endpoint_bundle_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('footwear'))
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."purchaseorder_id" AS "__endpoint_purchaseorder_0"
    FROM "relation_38" AS "source"
),
"b4" AS (
    SELECT
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
)
SELECT 
    "b2"."sku" AS "sku",
    COUNT(DISTINCT "b4"."__reference_0") AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_bundle_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_id_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_purchaseorder_0" = "b4"."__reference_0"))
WHERE ("b2"."dimensions" > 'large')
GROUP BY
    "b2"."__reference_0",
    "b2"."sku"
HAVING (COUNT(DISTINCT "b4"."__reference_0") >= 1);

-- Q016 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.product_id FROM PhysicalProduct e WHERE e.base_price <= 120;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."base_price" <= 120);

-- Q017 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.category_name, e1.category_id, e2.sku, e2.dimensions FROM category_products r JOIN Category e1 ON ENDPOINT(r, Category) = REF(e1) JOIN Tablet e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.quantity > 8;
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
        "source"."category_name" AS "category_name",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
),
"b2" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b1"."category_name" AS "category_name",
    "b1"."category_id" AS "category_id",
    "b2"."sku" AS "sku",
    "b2"."dimensions" AS "dimensions"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."quantity" > 8);

-- Q018 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.is_active, COUNT(DISTINCT REF(e3)) AS related_count FROM bought_together r1 JOIN Footwear e1 ON ENDPOINT(r1, bought_together_product_id) = REF(e1) JOIN Computer e2 ON ENDPOINT(r1, product_id) = REF(e2) JOIN supplier_products r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN Supplier e3 ON ENDPOINT(r2, Supplier) = REF(e3) WHERE e1.base_price >= 59 GROUP BY REF(e2), e2.is_active HAVING COUNT(DISTINCT REF(e3)) >= 4;
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
    WHERE ("source"."role" IN ('footwear'))
),
"b2" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('computer', 'desktop', 'laptop'))
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."supplier_id" AS "__endpoint_supplier_0"
    FROM "relation_36" AS "source"
),
"b4" AS (
    SELECT
        "source"."supplier_id" AS "__reference_0"
    FROM "relation_19" AS "source"
)
SELECT 
    "b2"."is_active" AS "is_active",
    COUNT(DISTINCT "b4"."__reference_0") AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_bought_together_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_id_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_supplier_0" = "b4"."__reference_0"))
WHERE ("b1"."base_price" >= 59)
GROUP BY
    "b2"."__reference_0",
    "b2"."is_active"
HAVING (COUNT(DISTINCT "b4"."__reference_0") >= 4);

-- Q019 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.is_active, e2.supplier_name, e3.created_at FROM supplier_products r1 JOIN Product e1 ON ENDPOINT(r1, Product) = REF(e1) JOIN Supplier e2 ON ENDPOINT(r1, Supplier) = REF(e2) JOIN supplier_pos r2 ON ENDPOINT(r2, Supplier) = REF(e2) JOIN PurchaseOrder e3 ON ENDPOINT(r2, PurchaseOrder) = REF(e3) WHERE e3.status > 'draft';
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
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
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
        "source"."created_at" AS "created_at",
        "source"."status" AS "status",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
)
SELECT 
    "b1"."is_active" AS "is_active",
    "b2"."supplier_name" AS "supplier_name",
    "b4"."created_at" AS "created_at"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_supplier_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_supplier_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_purchaseorder_0" = "b4"."__reference_0"))
WHERE ("b4"."status" > 'draft');

-- Q020 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Electronics e WHERE e.product_id < 9017243;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."product_id" < 9017243);

-- Q021 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.cpu, e.dimensions FROM Computer e WHERE e.base_price >= 59;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('computer', 'desktop', 'laptop'))
)
SELECT 
    "b0"."cpu" AS "cpu",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."base_price" >= 59);

-- Q022 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.is_active_variant, o.is_active FROM ProductVariant w JOIN Electronics o ON OWNER(w) = REF(o) WHERE w.variant_id > 5066821;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active_variant" AS "is_active_variant",
        "source"."variant_id" AS "variant_id",
        "source"."product_id" AS "__owner_0"
    FROM "relation_4" AS "source"
),
"b1" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."is_active_variant" AS "is_active_variant",
    "b1"."is_active" AS "is_active"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."variant_id" > 5066821);

-- Q023 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.product_name, COUNT(DISTINCT REF(e2)) AS related_count FROM product_tags r JOIN Desktop e1 ON ENDPOINT(r, Product) = REF(e1) JOIN Tag e2 ON ENDPOINT(r, Tag) = REF(e2) WHERE e2.tag_name < 'popular' GROUP BY REF(e1), e1.product_name HAVING COUNT(DISTINCT REF(e2)) >= 1;
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
    WHERE ("source"."role" IN ('desktop'))
),
"b2" AS (
    SELECT
        "source"."tag_name" AS "tag_name",
        "source"."tag_id" AS "__reference_0"
    FROM "relation_6" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    COUNT(DISTINCT "b2"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_tag_0" = "b2"."__reference_0"))
WHERE ("b2"."tag_name" < 'popular')
GROUP BY
    "b1"."__reference_0",
    "b1"."product_name"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 1);

-- Q024 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.carrier_code, e2.shipped_at FROM courier_shipments r JOIN CourierPartner e1 ON ENDPOINT(r, CourierPartner) = REF(e1) JOIN Shipment e2 ON ENDPOINT(r, Shipment) = REF(e2) WHERE e1.carrier_code >= 'CAR-Zqgk';
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
        "source"."courierpartner_id" AS "__reference_0"
    FROM "relation_22" AS "source"
),
"b2" AS (
    SELECT
        "source"."shipped_at" AS "shipped_at",
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_14" AS "source"
)
SELECT 
    "b1"."carrier_code" AS "carrier_code",
    "b2"."shipped_at" AS "shipped_at"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
WHERE ("b1"."carrier_code" >= 'CAR-Zqgk');

-- Q025 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.warranty_months, e2.base_price FROM bundled_phone_accessory r JOIN Phone e1 ON ENDPOINT(r, Phone) = REF(e1) JOIN Accessory e2 ON ENDPOINT(r, Accessory) = REF(e2) WHERE e2.warranty_months < 36;
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
        "source"."warranty_months" AS "warranty_months",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "source"."warranty_months" AS "warranty_months",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b1"."warranty_months" AS "warranty_months",
    "b2"."base_price" AS "base_price"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_accessory_0" = "b2"."__reference_0"))
WHERE ("b2"."warranty_months" < 36);

-- Q026 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.state FROM Address w WHERE w.address_id < 5980571;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."address_id" AS "address_id",
        "source"."state" AS "state"
    FROM "relation_7" AS "source"
)
SELECT 
    "b0"."state" AS "state"
FROM "b0"
WHERE ("b0"."address_id" < 5980571);

-- Q027 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.base_price, COUNT(DISTINCT REF(e1)) AS related_count FROM category_products r JOIN Category e1 ON ENDPOINT(r, Category) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.category_name < 'marriage' GROUP BY REF(e2), e2.base_price HAVING COUNT(DISTINCT REF(e1)) >= 1;
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
        "source"."category_name" AS "category_name",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
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
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."category_name" < 'marriage')
GROUP BY
    "b2"."__reference_0",
    "b2"."base_price"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 1);

-- Q028 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.contact_id, w.email FROM SupplierContact w WHERE w.phone <= '597-986-7639x537';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."contact_id" AS "contact_id",
        "source"."email" AS "email",
        "source"."phone" AS "phone"
    FROM "relation_20" AS "source"
)
SELECT 
    "b0"."contact_id" AS "contact_id",
    "b0"."email" AS "email"
FROM "b0"
WHERE ("b0"."phone" <= '597-986-7639x537');

-- Q029 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.purchaseorder_id, e.status FROM PurchaseOrder e WHERE e.status <= 'received';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."purchaseorder_id" AS "purchaseorder_id",
        "source"."status" AS "status"
    FROM "relation_21" AS "source"
)
SELECT 
    "b0"."purchaseorder_id" AS "purchaseorder_id",
    "b0"."status" AS "status"
FROM "b0"
WHERE ("b0"."status" <= 'received');

-- Q030 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sku, e.dimensions FROM Appliance e WHERE e.energy_rating < 'B';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."energy_rating" AS "energy_rating",
        "source"."dimensions" AS "dimensions",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('appliance', 'kitchenappliance'))
)
SELECT DISTINCT 
    "b0"."sku" AS "sku",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."energy_rating" < 'B');

-- Q031 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.sku FROM DigitalProduct e WHERE e.delivery_type >= 'download';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('digitalproduct', 'media', 'software'))
)
SELECT DISTINCT 
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."delivery_type" >= 'download');

-- Q032 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.coupon_code, w.max_uses, w.per_user_limit, o.discount_value, o.starts_at FROM Coupon w JOIN Promotion o ON OWNER(w) = REF(o) WHERE o.ends_at < '2026-12-07';
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
    "b0"."coupon_code" AS "coupon_code",
    "b0"."max_uses" AS "max_uses",
    "b0"."per_user_limit" AS "per_user_limit",
    "b1"."discount_value" AS "discount_value",
    "b1"."starts_at" AS "starts_at"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."ends_at" < '2026-12-07');

-- Q033 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.warehouse_name, e.warehouse_id, e.region FROM Warehouse e WHERE e.warehouse_name <= 'Lewis-Hartman';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."region" AS "region",
        "source"."warehouse_id" AS "warehouse_id",
        "source"."warehouse_name" AS "warehouse_name"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."warehouse_name" AS "warehouse_name",
    "b0"."warehouse_id" AS "warehouse_id",
    "b0"."region" AS "region"
FROM "b0"
WHERE ("b0"."warehouse_name" <= 'Lewis-Hartman');

-- Q034 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system, e.product_id, e.fit_type_women FROM WomenClothing e WHERE e.sku >= 'SKU-KKYN-92026277';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."product_id" AS "product_id",
        "source"."sku" AS "sku",
        "source"."fit_type_women" AS "fit_type_women"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."size_system" AS "size_system",
    "b0"."product_id" AS "product_id",
    "b0"."fit_type_women" AS "fit_type_women"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-KKYN-92026277');

-- Q035 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.loyalty_tier, COUNT(DISTINCT REF(e1)) AS related_count FROM software_downloads r JOIN Software e1 ON ENDPOINT(r, Software) = REF(e1) JOIN Customer e2 ON ENDPOINT(r, Customer) = REF(e2) WHERE e1.quantity <= 54 GROUP BY REF(e2), e2.loyalty_tier HAVING COUNT(DISTINCT REF(e1)) >= 3;
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
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b2"."loyalty_tier" AS "loyalty_tier",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_software_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_customer_0" = "b2"."__reference_0"))
WHERE ("b1"."quantity" <= 54)
GROUP BY
    "b2"."__reference_0",
    "b2"."loyalty_tier"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 3);

-- Q036 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.product_name, e.base_price FROM Accessory e WHERE e.base_price <= 185;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."product_name" AS "product_name",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."base_price" <= 185);

-- Q037 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name, e.quantity, e.base_price FROM DigitalProduct e WHERE e.product_name >= 'Distributed responsive Graphical User Interface';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('digitalproduct', 'media', 'software'))
)
SELECT 
    "b0"."product_name" AS "product_name",
    "b0"."quantity" AS "quantity",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."product_name" >= 'Distributed responsive Graphical User Interface');

-- Q038 [selection_projection] occurrence 1/1
-- Original E/R: SELECT DISTINCT e.base_price, e.carrier_lock, e.dimensions FROM Phone e WHERE e.product_name < 'Triple-buffered discrete contingency';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."carrier_lock" AS "carrier_lock",
        "source"."dimensions" AS "dimensions",
        "source"."base_price" AS "base_price",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
)
SELECT DISTINCT 
    "b0"."base_price" AS "base_price",
    "b0"."carrier_lock" AS "carrier_lock",
    "b0"."dimensions" AS "dimensions"
FROM "b0"
WHERE ("b0"."product_name" < 'Triple-buffered discrete contingency');

-- Q039 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.sku, COUNT(DISTINCT REF(e1)) AS related_count FROM wishlist_contains r JOIN Wishlist e1 ON ENDPOINT(r, Wishlist) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.wishlist_name >= 'default' GROUP BY REF(e2), e2.sku HAVING COUNT(DISTINCT REF(e1)) >= 3;
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
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b2"."sku" AS "sku",
    COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_wishlist_0" = "b1"."__reference_0" AND "b0"."__endpoint_wishlist_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."wishlist_name" >= 'default')
GROUP BY
    "b2"."__reference_0",
    "b2"."sku"
HAVING (COUNT(DISTINCT ROW("b1"."__reference_0", "b1"."__reference_1")) >= 3);

-- Q040 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.state, w.line1, w.address_id, o.user_id FROM Address w JOIN BusinessCustomer o ON OWNER(w) = REF(o) WHERE w.postal_code < '60207';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."address_id" AS "address_id",
        "source"."line1" AS "line1",
        "source"."postal_code" AS "postal_code",
        "source"."state" AS "state",
        "source"."user_id" AS "__owner_0"
    FROM "relation_7" AS "source"
),
"b1" AS (
    SELECT
        "source"."user_id" AS "user_id",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."state" AS "state",
    "b0"."line1" AS "line1",
    "b0"."address_id" AS "address_id",
    "b1"."user_id" AS "user_id"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."postal_code" < '60207');

-- Q041 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_name FROM Appliance e WHERE e.sku < 'SKU-kiOl-20372260';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('appliance', 'kitchenappliance'))
)
SELECT 
    "b0"."product_name" AS "product_name"
FROM "b0"
WHERE ("b0"."sku" < 'SKU-kiOl-20372260');

-- Q042 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.line1, o.password_hash FROM Address w JOIN PrimeCustomer o ON OWNER(w) = REF(o) WHERE w.city >= 'Johnsonberg';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."city" AS "city",
        "source"."line1" AS "line1",
        "source"."user_id" AS "__owner_0"
    FROM "relation_7" AS "source"
),
"b1" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT 
    "b0"."line1" AS "line1",
    "b1"."password_hash" AS "password_hash"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."city" >= 'Johnsonberg');

-- Q043 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.brand, e2.placed_at, e3.email FROM payment_order r1 JOIN PaymentMethod e1 ON ENDPOINT(r1, PaymentMethod) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r1, CustOrder) = REF(e2) JOIN customer_orders r2 ON ENDPOINT(r2, CustOrder) = REF(e2) JOIN PrimeCustomer e3 ON ENDPOINT(r2, Customer) = REF(e3) WHERE e3.user_id > 345714;
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
        "source"."placed_at" AS "placed_at",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
),
"b3" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_30" AS "source"
),
"b4" AS (
    SELECT
        "source"."email" AS "email",
        "source"."user_id" AS "user_id",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT 
    "b1"."brand" AS "brand",
    "b2"."placed_at" AS "placed_at",
    "b4"."email" AS "email"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_paymentmethod_0" = "b1"."__reference_0" AND "b0"."__endpoint_paymentmethod_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_customer_0" = "b4"."__reference_0"))
WHERE ("b4"."user_id" > 345714);

-- Q044 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.delivered_at FROM Shipment w WHERE w.carrier <= 'FedEx';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."carrier" AS "carrier",
        "source"."delivered_at" AS "delivered_at"
    FROM "relation_14" AS "source"
)
SELECT 
    "b0"."delivered_at" AS "delivered_at"
FROM "b0"
WHERE ("b0"."carrier" <= 'FedEx');

-- Q045 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.category_name, e2.is_active, e2.base_price FROM category_products r JOIN Category e1 ON ENDPOINT(r, Category) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.category_name > 'market';
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
    "b2"."is_active" AS "is_active",
    "b2"."base_price" AS "base_price"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."category_name" > 'market');

-- Q046 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.updated_at, e2.product_name FROM cart_contains r JOIN Cart e1 ON ENDPOINT(r, Cart) = REF(e1) JOIN Smartwatch e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.updated_at > '2025-08-21';
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
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b1"."updated_at" AS "updated_at",
    "b2"."product_name" AS "product_name"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_cart_0" = "b1"."__reference_0" AND "b0"."__endpoint_cart_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."updated_at" > '2025-08-21');

-- Q047 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price, e.is_active FROM PhysicalProduct e WHERE e.product_name <= 'Re-contextualized stable emulation';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."is_active" AS "is_active",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."base_price" AS "base_price",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."product_name" <= 'Re-contextualized stable emulation');

-- Q048 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.exp_month, e2.status FROM payment_order r JOIN PaymentMethod e1 ON ENDPOINT(r, PaymentMethod) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.is_default >= 'false';
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
        "source"."is_default" AS "is_default",
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
    "b1"."exp_month" AS "exp_month",
    "b2"."status" AS "status"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_paymentmethod_0" = "b1"."__reference_0" AND "b0"."__endpoint_paymentmethod_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."is_default" >= 'false');

-- Q049 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.category_name, e1.parent, e2.sku FROM category_products r JOIN Category e1 ON ENDPOINT(r, Category) = REF(e1) JOIN DigitalProduct e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.product_name >= 'Focused stable knowledge user';
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
        "source"."category_name" AS "category_name",
        "source"."parent" AS "parent",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
),
"b2" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('digitalproduct', 'media', 'software'))
)
SELECT 
    "b1"."category_name" AS "category_name",
    "b1"."parent" AS "parent",
    "b2"."sku" AS "sku"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."product_name" >= 'Focused stable knowledge user');

-- Q050 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.material FROM WomenClothing e WHERE e.quantity < 29;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."material" AS "material",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."material" AS "material"
FROM "b0"
WHERE ("b0"."quantity" < 29);

-- Q051 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.user_id, e.password_hash, e.employee_no FROM Employee e WHERE e.employee_no > 'EMP-29876878';
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
SELECT 
    "b0"."user_id" AS "user_id",
    "b0"."password_hash" AS "password_hash",
    "b0"."employee_no" AS "employee_no"
FROM "b0"
WHERE ("b0"."employee_no" > 'EMP-29876878');

-- Q052 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.status, e2.supplier_id, e3.quantity FROM supplier_pos r1 JOIN PurchaseOrder e1 ON ENDPOINT(r1, PurchaseOrder) = REF(e1) JOIN Supplier e2 ON ENDPOINT(r1, Supplier) = REF(e2) JOIN supplier_products r2 ON ENDPOINT(r2, Supplier) = REF(e2) JOIN Product e3 ON ENDPOINT(r2, Product) = REF(e3) WHERE e1.purchaseorder_id < 67054;
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
        "source"."purchaseorder_id" AS "purchaseorder_id",
        "source"."status" AS "status",
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
),
"b2" AS (
    SELECT
        "source"."supplier_id" AS "supplier_id",
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
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."status" AS "status",
    "b2"."supplier_id" AS "supplier_id",
    "b4"."quantity" AS "quantity"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_purchaseorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_supplier_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_supplier_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_0" = "b4"."__reference_0"))
WHERE ("b1"."purchaseorder_id" < 67054);

-- Q053 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.dimensions, COUNT(DISTINCT REF(e2)) AS related_count FROM bundled_phone_accessory r JOIN Phone e1 ON ENDPOINT(r, Phone) = REF(e1) JOIN Accessory e2 ON ENDPOINT(r, Accessory) = REF(e2) WHERE e2.base_price < 186 GROUP BY REF(e1), e1.dimensions HAVING COUNT(DISTINCT REF(e2)) >= 3;
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
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b1"."dimensions" AS "dimensions",
    COUNT(DISTINCT "b2"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_accessory_0" = "b2"."__reference_0"))
WHERE ("b2"."base_price" < 186)
GROUP BY
    "b1"."__reference_0",
    "b1"."dimensions"
HAVING (COUNT(DISTINCT "b2"."__reference_0") >= 3);

-- Q054 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.dimensions, COUNT(DISTINCT REF(e3)) AS related_count FROM bundle_components r1 JOIN Product e1 ON ENDPOINT(r1, product_id) = REF(e1) JOIN Clothing e2 ON ENDPOINT(r1, bundle_product_id) = REF(e2) JOIN reviews r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN Review e3 ON ENDPOINT(r2, Review) = REF(e3) WHERE e3.review_id > 3005059 GROUP BY REF(e2), e2.dimensions HAVING COUNT(DISTINCT REF(e3)) >= 5;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."bundle_product_product_id" AS "__endpoint_bundle_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b2" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('clothing', 'menclothing', 'womenclothing'))
),
"b3" AS (
    SELECT
        "source"."reviews_product_id" AS "__endpoint_product_0",
        "source"."customer_id" AS "__endpoint_review_0",
        "source"."review_id" AS "__endpoint_review_1"
    FROM "relation_29" AS "source"
),
"b4" AS (
    SELECT
        "source"."review_id" AS "review_id",
        "source"."user_id" AS "__reference_0",
        "source"."review_id" AS "__reference_1"
    FROM "relation_11" AS "source"
)
SELECT 
    "b2"."dimensions" AS "dimensions",
    COUNT(DISTINCT ROW("b4"."__reference_0", "b4"."__reference_1")) AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_id_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_bundle_product_id_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_review_0" = "b4"."__reference_0" AND "b3"."__endpoint_review_1" = "b4"."__reference_1"))
WHERE ("b4"."review_id" > 3005059)
GROUP BY
    "b2"."__reference_0",
    "b2"."dimensions"
HAVING (COUNT(DISTINCT ROW("b4"."__reference_0", "b4"."__reference_1")) >= 5);

-- Q055 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.delivered_at, COUNT(DISTINCT REF(e1)) AS related_count FROM courier_shipments r JOIN CourierPartner e1 ON ENDPOINT(r, CourierPartner) = REF(e1) JOIN Shipment e2 ON ENDPOINT(r, Shipment) = REF(e2) WHERE e2.carrier >= 'FedEx' GROUP BY REF(e2), e2.delivered_at HAVING COUNT(DISTINCT REF(e1)) >= 5;
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
        "source"."carrier" AS "carrier",
        "source"."delivered_at" AS "delivered_at",
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_14" AS "source"
)
SELECT 
    "b2"."delivered_at" AS "delivered_at",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
WHERE ("b2"."carrier" >= 'FedEx')
GROUP BY
    "b2"."__reference_0",
    "b2"."__reference_1",
    "b2"."delivered_at"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 5);

-- Q056 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.sku, e.product_name, e.base_price FROM PhysicalProduct e WHERE e.quantity < 30;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."sku" AS "sku",
    "b0"."product_name" AS "product_name",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."quantity" < 30);

-- Q057 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.product_name, e1.quantity, e2.bin_id FROM stock r JOIN Camera e1 ON ENDPOINT(r, Product) = REF(e1) JOIN WarehouseBin e2 ON ENDPOINT(r, WarehouseBin) = REF(e2) WHERE e1.quantity >= 23;
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
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
),
"b2" AS (
    SELECT
        "source"."bin_id" AS "bin_id",
        "source"."warehouse_id" AS "__reference_0",
        "source"."bin_id" AS "__reference_1"
    FROM "relation_18" AS "source"
)
SELECT 
    "b1"."product_name" AS "product_name",
    "b1"."quantity" AS "quantity",
    "b2"."bin_id" AS "bin_id"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_warehousebin_0" = "b2"."__reference_0" AND "b0"."__endpoint_warehousebin_1" = "b2"."__reference_1"))
WHERE ("b1"."quantity" >= 23);

-- Q058 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.custorder_id, e2.base_price FROM order_items r JOIN CustOrder e1 ON ENDPOINT(r, CustOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e1.placed_at > '2024-04-11';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_31" AS "source"
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
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."custorder_id" AS "custorder_id",
    "b2"."base_price" AS "base_price"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b1"."placed_at" > '2024-04-11');

-- Q059 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.user_id, e1.password_hash, e2.status, e2.custorder_id FROM customer_orders r JOIN BusinessCustomer e1 ON ENDPOINT(r, Customer) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.loyalty_tier <= 'bronze';
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
        "source"."loyalty_tier" AS "loyalty_tier",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "user_id",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
),
"b2" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b1"."user_id" AS "user_id",
    "b1"."password_hash" AS "password_hash",
    "b2"."status" AS "status",
    "b2"."custorder_id" AS "custorder_id"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_customer_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."loyalty_tier" <= 'bronze');

-- Q060 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.delivery_type, e.sku FROM DigitalProduct e WHERE e.is_active >= 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."delivery_type" AS "delivery_type",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('digitalproduct', 'media', 'software'))
)
SELECT 
    "b0"."delivery_type" AS "delivery_type",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."is_active" >= 1);

-- Q061 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.status, COUNT(DISTINCT REF(e3)) AS related_count FROM order_items r1 JOIN Electronics e1 ON ENDPOINT(r1, Product) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r1, CustOrder) = REF(e2) JOIN order_returns r2 ON ENDPOINT(r2, CustOrder) = REF(e2) JOIN Apparel e3 ON ENDPOINT(r2, Product) = REF(e3) WHERE e3.is_active <= 1 GROUP BY REF(e2), e2.status HAVING COUNT(DISTINCT REF(e3)) >= 2;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."custorder_id" AS "__endpoint_custorder_0",
        "source"."product_id" AS "__endpoint_product_0"
    FROM "relation_31" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
),
"b2" AS (
    SELECT
        "source"."status" AS "status",
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
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear'))
)
SELECT 
    "b2"."status" AS "status",
    COUNT(DISTINCT "b4"."__reference_0") AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_product_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_custorder_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_0" = "b4"."__reference_0"))
WHERE ("b4"."is_active" <= 1)
GROUP BY
    "b2"."__reference_0",
    "b2"."status"
HAVING (COUNT(DISTINCT "b4"."__reference_0") >= 2);

-- Q062 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.started_at, w.device, w.session_id FROM BrowsingSession w WHERE w.started_at >= '2025-02-27';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."device" AS "device",
        "source"."session_id" AS "session_id",
        "source"."started_at" AS "started_at"
    FROM "relation_12" AS "source"
)
SELECT 
    "b0"."started_at" AS "started_at",
    "b0"."device" AS "device",
    "b0"."session_id" AS "session_id"
FROM "b0"
WHERE ("b0"."started_at" >= '2025-02-27');

-- Q063 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.category_name, e1.parent, e2.product_name, e2.base_price FROM category_products r JOIN Category e1 ON ENDPOINT(r, Category) = REF(e1) JOIN Product e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.quantity < 86;
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
        "source"."category_name" AS "category_name",
        "source"."parent" AS "parent",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
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
    "b1"."category_name" AS "category_name",
    "b1"."parent" AS "parent",
    "b2"."product_name" AS "product_name",
    "b2"."base_price" AS "base_price"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."quantity" < 86);

-- Q064 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.is_active, e.product_id FROM PhysicalProduct e WHERE e.sku >= 'SKU-VHHJ-72832451';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."is_active" AS "is_active",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."sku" >= 'SKU-VHHJ-72832451');

-- Q065 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.exp_year, e1.brand, e2.status FROM payment_order r JOIN PaymentMethod e1 ON ENDPOINT(r, PaymentMethod) = REF(e1) JOIN CustOrder e2 ON ENDPOINT(r, CustOrder) = REF(e2) WHERE e1.is_default > 'false';
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
        "source"."is_default" AS "is_default",
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
    "b1"."exp_year" AS "exp_year",
    "b1"."brand" AS "brand",
    "b2"."status" AS "status"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_paymentmethod_0" = "b1"."__reference_0" AND "b0"."__endpoint_paymentmethod_1" = "b1"."__reference_1")) INNER JOIN "b2" ON ("b0"."__endpoint_custorder_0" = "b2"."__reference_0"))
WHERE ("b1"."is_default" > 'false');

-- Q066 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku FROM Accessory e WHERE e.base_price > 77;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."base_price" > 77);

-- Q067 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.password_hash, COUNT(DISTINCT REF(e1)) AS related_count FROM software_downloads r JOIN Software e1 ON ENDPOINT(r, Software) = REF(e1) JOIN Customer e2 ON ENDPOINT(r, Customer) = REF(e2) WHERE e1.license_type <= 'subscription' GROUP BY REF(e2), e2.password_hash HAVING COUNT(DISTINCT REF(e1)) >= 5;
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
        "source"."license_type" AS "license_type",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
),
"b2" AS (
    SELECT
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b2"."password_hash" AS "password_hash",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_software_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_customer_0" = "b2"."__reference_0"))
WHERE ("b1"."license_type" <= 'subscription')
GROUP BY
    "b2"."__reference_0",
    "b2"."password_hash"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 5);

-- Q068 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.payment_method_id, w.exp_year, w.is_default, o.email FROM PaymentMethod w JOIN BusinessCustomer o ON OWNER(w) = REF(o) WHERE w.is_default <= 'false';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."exp_year" AS "exp_year",
        "source"."is_default" AS "is_default",
        "source"."payment_method_id" AS "payment_method_id",
        "source"."user_id" AS "__owner_0"
    FROM "relation_8" AS "source"
),
"b1" AS (
    SELECT
        "source"."email" AS "email",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
)
SELECT 
    "b0"."payment_method_id" AS "payment_method_id",
    "b0"."exp_year" AS "exp_year",
    "b0"."is_default" AS "is_default",
    "b1"."email" AS "email"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."is_default" <= 'false');

-- Q069 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.email, COUNT(DISTINCT REF(e3)) AS related_count FROM software_downloads r1 JOIN Software e1 ON ENDPOINT(r1, Software) = REF(e1) JOIN BusinessCustomer e2 ON ENDPOINT(r1, Customer) = REF(e2) JOIN customer_orders r2 ON ENDPOINT(r2, Customer) = REF(e2) JOIN CustOrder e3 ON ENDPOINT(r2, CustOrder) = REF(e3) WHERE e1.is_active <= 1 GROUP BY REF(e2), e2.email HAVING COUNT(DISTINCT REF(e3)) >= 3;
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
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
),
"b2" AS (
    SELECT
        "source"."email" AS "email",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('businesscustomer'))
),
"b3" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_30" AS "source"
),
"b4" AS (
    SELECT
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b2"."email" AS "email",
    COUNT(DISTINCT "b4"."__reference_0") AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_software_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_customer_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_customer_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_custorder_0" = "b4"."__reference_0"))
WHERE ("b1"."is_active" <= 1)
GROUP BY
    "b2"."__reference_0",
    "b2"."email"
HAVING (COUNT(DISTINCT "b4"."__reference_0") >= 3);

-- Q070 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.sku, COUNT(DISTINCT REF(e1)) AS related_count FROM po_items r JOIN PurchaseOrder e1 ON ENDPOINT(r, PurchaseOrder) = REF(e1) JOIN WomenClothing e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.quantity >= 17 GROUP BY REF(e2), e2.sku HAVING COUNT(DISTINCT REF(e1)) >= 1;
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
        "source"."purchaseorder_id" AS "__reference_0"
    FROM "relation_21" AS "source"
),
"b2" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b2"."sku" AS "sku",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_purchaseorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."quantity" >= 17)
GROUP BY
    "b2"."__reference_0",
    "b2"."sku"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 1);

-- Q071 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.is_active_variant FROM ProductVariant w WHERE w.barcode < '8043143497919';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."barcode" AS "barcode",
        "source"."is_active_variant" AS "is_active_variant"
    FROM "relation_4" AS "source"
)
SELECT 
    "b0"."is_active_variant" AS "is_active_variant"
FROM "b0"
WHERE ("b0"."barcode" < '8043143497919');

-- Q072 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.contact_id, w.phone FROM SupplierContact w WHERE w.email >= 'jacksonlisa@example.net';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."contact_id" AS "contact_id",
        "source"."email" AS "email",
        "source"."phone" AS "phone"
    FROM "relation_20" AS "source"
)
SELECT 
    "b0"."contact_id" AS "contact_id",
    "b0"."phone" AS "phone"
FROM "b0"
WHERE ("b0"."email" >= 'jacksonlisa@example.net');

-- Q073 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system FROM Apparel e WHERE e.quantity < 23;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."quantity" AS "quantity"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear'))
)
SELECT 
    "b0"."size_system" AS "size_system"
FROM "b0"
WHERE ("b0"."quantity" < 23);

-- Q074 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.tracking_no, w.carrier, w.shipped_at, o.status, o.placed_at FROM Shipment w JOIN CustOrder o ON OWNER(w) = REF(o) WHERE w.tracking_no > 'Ut9912159629';
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
        "source"."placed_at" AS "placed_at",
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b0"."tracking_no" AS "tracking_no",
    "b0"."carrier" AS "carrier",
    "b0"."shipped_at" AS "shipped_at",
    "b1"."status" AS "status",
    "b1"."placed_at" AS "placed_at"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."tracking_no" > 'Ut9912159629');

-- Q075 [aggregation] occurrence 1/1
-- Original E/R: SELECT e1.carrier_code, COUNT(DISTINCT REF(e2)) AS related_count FROM courier_shipments r JOIN CourierPartner e1 ON ENDPOINT(r, CourierPartner) = REF(e1) JOIN Shipment e2 ON ENDPOINT(r, Shipment) = REF(e2) WHERE e2.shipped_at < '2025-01-02' GROUP BY REF(e1), e1.carrier_code HAVING COUNT(DISTINCT REF(e2)) >= 3;
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
        "source"."courierpartner_id" AS "__reference_0"
    FROM "relation_22" AS "source"
),
"b2" AS (
    SELECT
        "source"."shipped_at" AS "shipped_at",
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_14" AS "source"
)
SELECT 
    "b1"."carrier_code" AS "carrier_code",
    COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
WHERE ("b2"."shipped_at" < '2025-01-02')
GROUP BY
    "b1"."__reference_0",
    "b1"."carrier_code"
HAVING (COUNT(DISTINCT ROW("b2"."__reference_0", "b2"."__reference_1")) >= 3);

-- Q076 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.sku, e1.warranty_months, e2.sku, e2.accessory_type FROM bundled_phone_accessory r JOIN Phone e1 ON ENDPOINT(r, Phone) = REF(e1) JOIN Accessory e2 ON ENDPOINT(r, Accessory) = REF(e2) WHERE e2.is_active < 1;
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
        "source"."warranty_months" AS "warranty_months",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('phone'))
),
"b2" AS (
    SELECT
        "source"."accessory_type" AS "accessory_type",
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('accessory'))
)
SELECT 
    "b1"."sku" AS "sku",
    "b1"."warranty_months" AS "warranty_months",
    "b2"."sku" AS "sku",
    "b2"."accessory_type" AS "accessory_type"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_phone_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_accessory_0" = "b2"."__reference_0"))
WHERE ("b2"."is_active" < 1);

-- Q077 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.sku FROM Smartwatch e WHERE e.is_active < 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."is_active" AS "is_active",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('smartwatch'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."is_active" < 1);

-- Q078 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.user_id, COUNT(DISTINCT REF(e3)) AS related_count FROM software_downloads r1 JOIN Software e1 ON ENDPOINT(r1, Software) = REF(e1) JOIN PrimeCustomer e2 ON ENDPOINT(r1, Customer) = REF(e2) JOIN customer_orders r2 ON ENDPOINT(r2, Customer) = REF(e2) JOIN CustOrder e3 ON ENDPOINT(r2, CustOrder) = REF(e3) WHERE e3.custorder_id < 72513 GROUP BY REF(e2), e2.user_id HAVING COUNT(DISTINCT REF(e3)) >= 1;
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
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
),
"b2" AS (
    SELECT
        "source"."user_id" AS "user_id",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
),
"b3" AS (
    SELECT
        "source"."customer_orders_customer_id" AS "__endpoint_customer_0",
        "source"."custorder_id" AS "__endpoint_custorder_0"
    FROM "relation_30" AS "source"
),
"b4" AS (
    SELECT
        "source"."custorder_id" AS "custorder_id",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
)
SELECT 
    "b2"."user_id" AS "user_id",
    COUNT(DISTINCT "b4"."__reference_0") AS "related_count"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_software_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_customer_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_customer_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_custorder_0" = "b4"."__reference_0"))
WHERE ("b4"."custorder_id" < 72513)
GROUP BY
    "b2"."__reference_0",
    "b2"."user_id"
HAVING (COUNT(DISTINCT "b4"."__reference_0") >= 1);

-- Q079 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.review_id, w.body, o.renewal_date, o.password_hash FROM Review w JOIN PrimeCustomer o ON OWNER(w) = REF(o) WHERE w.rating > 4;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."body" AS "body",
        "source"."rating" AS "rating",
        "source"."review_id" AS "review_id",
        "source"."user_id" AS "__owner_0"
    FROM "relation_11" AS "source"
),
"b1" AS (
    SELECT
        "source"."renewal_date" AS "renewal_date",
        "source"."password_hash" AS "password_hash",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('primecustomer'))
)
SELECT 
    "b0"."review_id" AS "review_id",
    "b0"."body" AS "body",
    "b1"."renewal_date" AS "renewal_date",
    "b1"."password_hash" AS "password_hash"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."rating" > 4);

-- Q080 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.created_at, e2.base_price FROM po_items r JOIN PurchaseOrder e1 ON ENDPOINT(r, PurchaseOrder) = REF(e1) JOIN Tablet e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.is_active <= 1;
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
    WHERE ("source"."role" IN ('tablet'))
)
SELECT 
    "b1"."created_at" AS "created_at",
    "b2"."base_price" AS "base_price"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_purchaseorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."is_active" <= 1);

-- Q081 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.status, e2.sensor_mp FROM order_returns r JOIN CustOrder e1 ON ENDPOINT(r, CustOrder) = REF(e1) JOIN Camera e2 ON ENDPOINT(r, Product) = REF(e2) WHERE e2.dimensions >= 'oversize';
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
        "source"."status" AS "status",
        "source"."custorder_id" AS "__reference_0"
    FROM "relation_13" AS "source"
),
"b2" AS (
    SELECT
        "source"."sensor_mp" AS "sensor_mp",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('camera'))
)
SELECT 
    "b1"."status" AS "status",
    "b2"."sensor_mp" AS "sensor_mp"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_custorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0"))
WHERE ("b2"."dimensions" >= 'oversize');

-- Q082 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.base_price FROM KitchenAppliance e WHERE e.product_name <= 'Persistent directional project';
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
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."product_name" <= 'Persistent directional project');

-- Q083 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id, e.base_price FROM Laptop e WHERE e.cpu < 'Ryzen 7';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."cpu" AS "cpu",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('laptop'))
)
SELECT 
    "b0"."product_id" AS "product_id",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."cpu" < 'Ryzen 7');

-- Q084 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.barcode, o.quantity FROM ProductVariant w JOIN Product o ON OWNER(w) = REF(o) WHERE o.quantity < 56;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."barcode" AS "barcode",
        "source"."product_id" AS "__owner_0"
    FROM "relation_4" AS "source"
),
"b1" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b0"."barcode" AS "barcode",
    "b1"."quantity" AS "quantity"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."quantity" < 56);

-- Q085 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e2.supplier_id, COUNT(DISTINCT REF(e3)) AS related_count FROM supplier_products r1 JOIN Media e1 ON ENDPOINT(r1, Product) = REF(e1) JOIN Supplier e2 ON ENDPOINT(r1, Supplier) = REF(e2) JOIN supplier_pos r2 ON ENDPOINT(r2, Supplier) = REF(e2) JOIN PurchaseOrder e3 ON ENDPOINT(r2, PurchaseOrder) = REF(e3) WHERE e2.supplier_id > 20894 GROUP BY REF(e2), e2.supplier_id HAVING COUNT(DISTINCT REF(e3)) >= 3;
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
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('media'))
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
    FROM "relation_37" AS "source"
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
WHERE ("b2"."supplier_id" > 20894)
GROUP BY
    "b2"."__reference_0",
    "b2"."supplier_id"
HAVING (COUNT(DISTINCT "b4"."__reference_0") >= 3);

-- Q086 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.material, e.fit_type_women, e.dimensions, e.product_id FROM WomenClothing e WHERE e.fit_type_women <= 'regular';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."material" AS "material",
        "source"."dimensions" AS "dimensions",
        "source"."product_id" AS "product_id",
        "source"."fit_type_women" AS "fit_type_women"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."material" AS "material",
    "b0"."fit_type_women" AS "fit_type_women",
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."fit_type_women" <= 'regular');

-- Q087 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.size_system, e.product_name, e.product_id, e.base_price FROM MenClothing e WHERE e.material >= 'cotton';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."size_system" AS "size_system",
        "source"."material" AS "material",
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "product_id",
        "source"."product_name" AS "product_name"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('menclothing'))
)
SELECT 
    "b0"."size_system" AS "size_system",
    "b0"."product_name" AS "product_name",
    "b0"."product_id" AS "product_id",
    "b0"."base_price" AS "base_price"
FROM "b0"
WHERE ("b0"."material" >= 'cotton');

-- Q088 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.price_id, w.ends_at, o.fit_type_women, o.sku FROM PriceHistory w JOIN WomenClothing o ON OWNER(w) = REF(o) WHERE w.price_id > 2958584;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."ends_at" AS "ends_at",
        "source"."price_id" AS "price_id",
        "source"."product_id" AS "__owner_0"
    FROM "relation_5" AS "source"
),
"b1" AS (
    SELECT
        "source"."sku" AS "sku",
        "source"."fit_type_women" AS "fit_type_women",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('womenclothing'))
)
SELECT 
    "b0"."price_id" AS "price_id",
    "b0"."ends_at" AS "ends_at",
    "b1"."fit_type_women" AS "fit_type_women",
    "b1"."sku" AS "sku"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."price_id" > 2958584);

-- Q089 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.product_id FROM Footwear e WHERE e.quantity <= 53;
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
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."quantity" <= 53);

-- Q090 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.sku, e1.quantity, e2.bin_id, e2.code FROM stock r JOIN Product e1 ON ENDPOINT(r, Product) = REF(e1) JOIN WarehouseBin e2 ON ENDPOINT(r, WarehouseBin) = REF(e2) WHERE e1.sku < 'SKU-fRiT-80477349';
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
WHERE ("b1"."sku" < 'SKU-fRiT-80477349');

-- Q091 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.status, e2.quantity, e3.tag_id FROM po_items r1 JOIN PurchaseOrder e1 ON ENDPOINT(r1, PurchaseOrder) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN product_tags r2 ON ENDPOINT(r2, Product) = REF(e2) JOIN Tag e3 ON ENDPOINT(r2, Tag) = REF(e3) WHERE e3.tag_name < 'sale';
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
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."product_id" AS "__endpoint_product_0",
        "source"."tag_id" AS "__endpoint_tag_0"
    FROM "relation_24" AS "source"
),
"b4" AS (
    SELECT
        "source"."tag_id" AS "tag_id",
        "source"."tag_name" AS "tag_name",
        "source"."tag_id" AS "__reference_0"
    FROM "relation_6" AS "source"
)
SELECT 
    "b1"."status" AS "status",
    "b2"."quantity" AS "quantity",
    "b4"."tag_id" AS "tag_id"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_purchaseorder_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_tag_0" = "b4"."__reference_0"))
WHERE ("b4"."tag_name" < 'sale');

-- Q092 [relationship_join] occurrence 1/1
-- Original E/R: SELECT e1.carrier_code, e2.delivered_at, e2.shipment_id FROM courier_shipments r JOIN CourierPartner e1 ON ENDPOINT(r, CourierPartner) = REF(e1) JOIN Shipment e2 ON ENDPOINT(r, Shipment) = REF(e2) WHERE e2.delivered_at <= '2026-08-07';
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
        "source"."courierpartner_id" AS "__reference_0"
    FROM "relation_22" AS "source"
),
"b2" AS (
    SELECT
        "source"."delivered_at" AS "delivered_at",
        "source"."shipment_id" AS "shipment_id",
        "source"."custorder_id" AS "__reference_0",
        "source"."shipment_id" AS "__reference_1"
    FROM "relation_14" AS "source"
)
SELECT 
    "b1"."carrier_code" AS "carrier_code",
    "b2"."delivered_at" AS "delivered_at",
    "b2"."shipment_id" AS "shipment_id"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_courierpartner_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_shipment_0" = "b2"."__reference_0" AND "b0"."__endpoint_shipment_1" = "b2"."__reference_1"))
WHERE ("b2"."delivered_at" <= '2026-08-07');

-- Q093 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.shipment_id, COUNT(DISTINCT REF(e1)) AS related_count FROM courier_shipments r JOIN CourierPartner e1 ON ENDPOINT(r, CourierPartner) = REF(e1) JOIN Shipment e2 ON ENDPOINT(r, Shipment) = REF(e2) WHERE e1.courierpartner_id > 12668 GROUP BY REF(e2), e2.shipment_id HAVING COUNT(DISTINCT REF(e1)) >= 1;
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
        "source"."courierpartner_id" AS "courierpartner_id",
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
WHERE ("b1"."courierpartner_id" > 12668)
GROUP BY
    "b2"."__reference_0",
    "b2"."__reference_1",
    "b2"."shipment_id"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 1);

-- Q094 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.url, w.alt_text, o.product_name FROM ProductImage w JOIN Appliance o ON OWNER(w) = REF(o) WHERE w.alt_text <= 'Recognize cup poor pay.';
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."alt_text" AS "alt_text",
        "source"."url" AS "url",
        "source"."product_id" AS "__owner_0"
    FROM "relation_3" AS "source"
),
"b1" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('appliance', 'kitchenappliance'))
)
SELECT 
    "b0"."url" AS "url",
    "b0"."alt_text" AS "alt_text",
    "b1"."product_name" AS "product_name"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b0"."alt_text" <= 'Recognize cup poor pay.');

-- Q095 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.is_active, e.dimensions, e.product_id FROM PhysicalProduct e WHERE e.is_active < 1;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."product_id" AS "product_id"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('physicalproduct', 'apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear', 'appliance', 'kitchenappliance', 'electronics', 'accessory', 'camera', 'computer', 'desktop', 'laptop', 'phone', 'smartwatch', 'tablet'))
)
SELECT 
    "b0"."is_active" AS "is_active",
    "b0"."dimensions" AS "dimensions",
    "b0"."product_id" AS "product_id"
FROM "b0"
WHERE ("b0"."is_active" < 1);

-- Q096 [aggregation] occurrence 1/1
-- Original E/R: SELECT e2.user_id, COUNT(DISTINCT REF(e1)) AS related_count FROM software_downloads r JOIN Software e1 ON ENDPOINT(r, Software) = REF(e1) JOIN Customer e2 ON ENDPOINT(r, Customer) = REF(e2) WHERE e1.license_type >= 'open_source' GROUP BY REF(e2), e2.user_id HAVING COUNT(DISTINCT REF(e1)) >= 5;
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
        "source"."license_type" AS "license_type",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('software'))
),
"b2" AS (
    SELECT
        "source"."user_id" AS "user_id",
        "source"."user_id" AS "__reference_0"
    FROM "relation_2" AS "source"
    WHERE ("source"."role" IN ('customer', 'businesscustomer', 'primecustomer'))
)
SELECT 
    "b2"."user_id" AS "user_id",
    COUNT(DISTINCT "b1"."__reference_0") AS "related_count"
FROM (("b0" INNER JOIN "b1" ON ("b0"."__endpoint_software_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_customer_0" = "b2"."__reference_0"))
WHERE ("b1"."license_type" >= 'open_source')
GROUP BY
    "b2"."__reference_0",
    "b2"."user_id"
HAVING (COUNT(DISTINCT "b1"."__reference_0") >= 5);

-- Q097 [complex_multi_join] occurrence 1/1
-- Original E/R: SELECT e1.parent, e2.quantity, e3.base_price FROM category_products r1 JOIN Category e1 ON ENDPOINT(r1, Category) = REF(e1) JOIN Product e2 ON ENDPOINT(r1, Product) = REF(e2) JOIN bundle_components r2 ON ENDPOINT(r2, bundle_product_id) = REF(e2) JOIN Product e3 ON ENDPOINT(r2, product_id) = REF(e3) WHERE e1.category_id <= 127050;
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
        "source"."parent" AS "parent",
        "source"."category_id" AS "__reference_0"
    FROM "relation_0" AS "source"
),
"b2" AS (
    SELECT
        "source"."quantity" AS "quantity",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
),
"b3" AS (
    SELECT
        "source"."bundle_product_product_id" AS "__endpoint_bundle_product_id_0",
        "source"."product_id" AS "__endpoint_product_id_0"
    FROM "relation_25" AS "source"
),
"b4" AS (
    SELECT
        "source"."base_price" AS "base_price",
        "source"."product_id" AS "__reference_0"
    FROM "relation_1" AS "source"
)
SELECT 
    "b1"."parent" AS "parent",
    "b2"."quantity" AS "quantity",
    "b4"."base_price" AS "base_price"
FROM (((("b0" INNER JOIN "b1" ON ("b0"."__endpoint_category_0" = "b1"."__reference_0")) INNER JOIN "b2" ON ("b0"."__endpoint_product_0" = "b2"."__reference_0")) INNER JOIN "b3" ON ("b3"."__endpoint_bundle_product_id_0" = "b2"."__reference_0")) INNER JOIN "b4" ON ("b3"."__endpoint_product_id_0" = "b4"."__reference_0"))
WHERE ("b1"."category_id" <= 127050);

-- Q098 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.quantity, e.product_name, e.sku FROM Apparel e WHERE e.quantity > 8;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."product_name" AS "product_name",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('apparel', 'clothing', 'menclothing', 'womenclothing', 'footwear'))
)
SELECT 
    "b0"."quantity" AS "quantity",
    "b0"."product_name" AS "product_name",
    "b0"."sku" AS "sku"
FROM "b0"
WHERE ("b0"."quantity" > 8);

-- Q099 [selection_projection] occurrence 1/1
-- Original E/R: SELECT e.sku, e.dimensions, e.quantity, e.is_active FROM Appliance e WHERE e.is_active > 0;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."dimensions" AS "dimensions",
        "source"."is_active" AS "is_active",
        "source"."quantity" AS "quantity",
        "source"."sku" AS "sku"
    FROM "relation_1" AS "source"
    WHERE ("source"."role" IN ('appliance', 'kitchenappliance'))
)
SELECT 
    "b0"."sku" AS "sku",
    "b0"."dimensions" AS "dimensions",
    "b0"."quantity" AS "quantity",
    "b0"."is_active" AS "is_active"
FROM "b0"
WHERE ("b0"."is_active" > 0);

-- Q100 [weak_owner] occurrence 1/1
-- Original E/R: SELECT w.code, o.region FROM WarehouseBin w JOIN Warehouse o ON OWNER(w) = REF(o) WHERE o.warehouse_id > 26870;
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON, FORMAT TEXT)
WITH
"b0" AS (
    SELECT
        "source"."code" AS "code",
        "source"."warehouse_id" AS "__owner_0"
    FROM "relation_18" AS "source"
),
"b1" AS (
    SELECT
        "source"."region" AS "region",
        "source"."warehouse_id" AS "warehouse_id",
        "source"."warehouse_id" AS "__reference_0"
    FROM "relation_17" AS "source"
)
SELECT 
    "b0"."code" AS "code",
    "b1"."region" AS "region"
FROM ("b0" INNER JOIN "b1" ON ("b0"."__owner_0" = "b1"."__reference_0"))
WHERE ("b1"."warehouse_id" > 26870);

ROLLBACK;
