import csv

with open('benchmarks/geo_multi_comparison_2026-07-W27.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print(f"Keys: {list(rows[0].keys()) if rows else 'empty'}")
    for row in rows:
        mid = row.get('model_id', '').lower().replace('-','_').replace('.','_').replace(' ','_')
        print(f"{row.get('model_id', 'MISSING'):35} -> {mid}")
