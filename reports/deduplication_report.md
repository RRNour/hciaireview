# Deduplication Report

Generated: 2026-07-05

## Summary
Records before deduplication: **3,266**  
Records after deduplication: **3,218**  
Duplicates removed: **48**  

## Rules Applied
1. Exact DOI match → duplicate → remove  
2. Fuzzy title similarity ≥0.95 + same year + same first author → duplicate → remove  
3. Fuzzy similarity 0.85–0.94 → uncertain → keep most complete record  

Detail file: outputs/tables/deduplication_report.csv
