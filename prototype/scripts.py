#make the output vertical - for csv comparison

import re

#var = ("")
var = ("")
#verticalize to stdout
print("\n".join(t for t in re.split(r"[,\s]+", var.strip()) if t))
print("-----------------exec times done printing")

#print(*re.findall(r"[^,\s]+", var), sep="\n")#one liner


data = "tag:11915.7,cart:2318582.043729927,user:169459.4,media:121468.75,phone:77740.11499999999,stock:5624260777.665079,camera:19435.115,coupon:839346.226927908,laptop:16062.050000000001,review:1585966.7551965024,tablet:11500.0,address:6794728.184444504,apparel:316091.622,desktop:215944.46999999997,product:2124792.9229999995,reviews:116876.35167701432,category:13997.800000000001,clothing:266326.01599999995,computer:268766.70699999994,customer:114068.35,employee:22500.0,footwear:3293.83,po_items:63551875.19456295,shipment:494585.6632214946,software:1725.0,supplier:10454.900000000001,wishlist:2522596.3110564556,accessory:16663.27,appliance:41009.14949999999,custorder:10433.800000000001,promotion:14973.800000000001,warehouse:8798.2,smartwatch:53986.175,electronics:1605035.542,menclothing:194350.0,order_items:42969786.73774564,pricehistory:4730346.080785718,product_tags:12973492610.415033,productimage:9615283.829674067,supplier_pos:2290142.384727214,warehousebin:198783.4962171942,bundle_phones:53370829.7867917,cart_contains:18906218.91306182,order_coupons:234216.50728456356,order_returns:7508775.352928059,payment_order:5138900.475425119,paymentmethod:7567843.497027973,primecustomer:10000.0,purchaseorder:15431.39,womenclothing:13496.63,courierpartner:6310.700000000001,digitalproduct:143951.8135,productvariant:14967573.253854698,bought_together:13014983518.193975,browsingsession:3018335.179117119,customer_orders:4080781.534043,physicalproduct:1972998.2359999998,suppliercontact:821249.3817287779,businesscustomer:90000.0,kitchenappliance:30367.244999999995,bundle_components:2670069140.3115153,category_products:13837076.831678005,courier_shipments:364694.6099769013,supplier_products:16056605.667645425,wishlist_contains:28212100.96849233,software_downloads:1980648.7556859688,bundled_phone_accessory:34221937.61931447"

order = [
"category","product","physicalproduct","digitalproduct","electronics","computer","desktop",
"laptop","tablet","smartwatch","camera","phone","accessory","appliance","kitchenappliance",
"apparel","clothing","menclothing","womenclothing","footwear","media","software","user",
"customer","primecustomer","businesscustomer","employee","productimage","productvariant",
"pricehistory","tag","address","paymentmethod","cart","wishlist","review","browsingsession",
"custorder","shipment","promotion","coupon","warehouse","warehousebin","supplier",
"suppliercontact","purchaseorder","courierpartner","category_products","product_tags",
"bundle_components","bought_together","cart_contains","wishlist_contains","reviews",
"customer_orders","order_items","payment_order","order_returns","order_coupons","stock",
"supplier_products","supplier_pos","po_items","courier_shipments","bundle_phones",
"bundled_phone_accessory","software_downloads"
]

# convert key:value string to dictionary
values = dict(item.split(":") for item in data.split(","))

# print values in required order
for key in order:
    print(values.get(key))



