# Demo data

Aggregates exported by `python -m olist_bi export` from the warehouse built on the
**Brazilian E-Commerce Public Dataset by Olist** (Kaggle,
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)). These files are an
adaptation of that dataset and are shared under the same license: attribution required,
non-commercial use only, derivatives under the same terms.

| File | Grain |
|---|---|
| `orders.parquet` | month × customer state × valid/invalid order status |
| `categories.parquet` | month × customer state × product category (valid orders) |
| `sellers.parquet` | seller × month × customer state (valid orders) |
| `delivery_buckets.parquet` | month × customer state × calendar days late |
| `kpi_reference.json` | `reporting.vw_executive_summary` at export time |
| `export_metadata.json` | order date range and export date |
