# Problem & Goal:

Hospitals, public distribution systems, and NGOs struggle to keep medicines, food, and other essentials available in the right place at the right time. Data on sales/usage, inventory, and purchase orders often lives in separate systems, so teams spot stock issues only when shelves are already empty or over-full.
‍
Using a simple daily stock dataset (for example: location, item, opening_stock, received, issued, closing_stock, lead_time_days), build a single view of stock health that:

- Shows a heatmap by location and item,
- Warns early about items likely to run out within a few days, and
- Suggests sensible reorder quantities or priority lists, with an easy export that procurement or field teams can act on.

This problem statement we are solving in this project is AI for Good because it helps reduce waste and avoid stock-outs of critical supplies.

## We need to ‍Use Snowflake

Worksheets/SQL, Dynamic Tables (auto-refresh calculations), Streams & Tasks (scheduling), Streamlit (dashboard); optional Snowpark (basic demand estimate); optional Unistore for action logs.

### Cleaned data sample:

| SKU_ID  | SKU_NAME          | CATEGORY      | ABC_CLASS | SUPPLIER_ID | SUPPLIER_NAME         | WAREHOUSE_ID | WAREHOUSE_LOCATION  | BATCH_ID  | RECEIVED_DATE | LAST_PURCHASE_DATE | EXPIRY_DATE | AUDIT_DATE | STOCK_AGE_DAYS | QUANTITY_ON_HAND | QUANTITY_RESERVED | QUANTITY_COMMITTED | DAMAGED_QTY | RETURNS_QTY | AVG_DAILY_SALES | FORECAST_NEXT_30D | DAYS_OF_INVENTORY | SKU_CHURN_RATE | ORDER_FREQUENCY_PER_MONTH | REORDER_POINT | SAFETY_STOCK | LEAD_TIME_DAYS | UNIT_COST_USD | LAST_PURCHASE_PRICE_USD | TOTAL_INVENTORY_VALUE_USD | SUPPLIER_ONTIME_PCT | FIFO_FEFO | INVENTORY_STATUS | COUNT_VARIANCE | AUDIT_VARIANCE_PCT | DEMAND_FORECAST_ACCURACY_PCT | NOTES | UPLOAD_TIMESTAMP     |
| ------- | ----------------- | ------------- | --------- | ----------- | --------------------- | ------------ | ------------------- | --------- | ------------- | ------------------ | ----------- | ---------- | -------------- | ---------------- | ----------------- | ------------------ | ----------- | ----------- | --------------- | ----------------- | ----------------- | -------------- | ------------------------- | ------------- | ------------ | -------------- | ------------- | ----------------------- | ------------------------- | ------------------- | --------- | ---------------- | -------------- | ------------------ | ---------------------------- | ----- | -------------------- |
| SKU0001 | Pantry Product 13 | Pantry        | A         | S005        | PT Agro Raya          | WHBDG        | Bandung - Rancaekek | BATCH2679 | 7/14/2025     | 6/1/2025           | 4/25/2027   | 6/26/2025  | 57             | 359              | 100               | 36                 | 0           | 0           | 2857            | 971               | 1257              | 239            | 500                       | 51            | 22           | 1              | 581           | 571                     | 2.08                      | 0                   | FIFO      | In Stock         | 0              | 0                  | 0                            |       | 2026-01-04T03:05:54Z |
| SKU0002 | Fresh Product 112 | Fresh Produce | C         | S004        | PT Nusantara Supplier | WHDPS        | Denpasar - Tabanan  | BATCH4257 | 4/8/2025      | 2/22/2025          | 4/11/2025   | 8/12/2025  | 154            | 314              | 64                | 0                  | 0           | 1           | 3499            | 796               | 897               | 334            | 1200                      | 744           | 254          | 14             | 145           | 133                     | 45671                     | 0                   | FEFO      | Low Stock        | 4              | 0                  | 0                            |       | 2026-01-04T03:05:54Z |
| SKU0003 | Meat Product 446  | Meat          | B         | S001        | PT Segar Makmur       | WHBDG        | Bandung - Rancaekek | BATCH6574 | 3/15/2025     | 2/26/2025          | 4/2/2025    | 8/13/2025  | 178            | 485              | 28                | 62                 | 3           | 1           | 3655            | 1                 | 1327              | 226            | 1100                      | 225           | 79           | 4              | 186           | 169                     | 90263                     | 0                   | FIFO      | Expiring Soon    | -5             | 0                  | 0                            |       | 2026-01-04T03:05:54Z |
