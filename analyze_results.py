#!/usr/bin/env python3
"""
analyze_results.py
Analyzes GEO benchmark results and generates insights.

Usage:
    python analyze_results.py benchmarks/geo_multi_comparison_2026-06-W26.csv
    python analyze_results.py benchmarks/  # Analyze all files in directory
"""

import sys, csv, os, glob
from collections import defaultdict

def load_comparison_csv(filepath):
    """Load a comparison CSV file"""
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def load_individual_csv(filepath):
    """Load an individual model's detailed results"""
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def parse_percentage(pct_str):
    """Parse percentage string to float"""
    return float(pct_str.strip('%'))

def analyze_comparison(results):
    """Analyze comparison results"""
    print("\n" + "="*70)
    print("GEO BENCHMARK ANALYSIS")
    print("="*70)

    # Sort by unaided SOV
    results_sorted = sorted(results, key=lambda x: parse_percentage(x['unaided_sov']), reverse=True)

    print(f"\n{'Model':<35} {'Unaided SOV':<15} {'Aided SOV':<15} {'Rate Saver':<12}")
    print("-"*70)

    for row in results_sorted:
        model_name = row['model_name'][:33]
        unaided = row['unaided_sov']
        aided = row['aided_sov']
        rate_saver = row.get('rate_saver_sov', 'N/A')

        print(f"{model_name:<35} {unaided:<15} {aided:<15} {rate_saver:<12}")

    # Calculate statistics
    unaided_sovs = [parse_percentage(r['unaided_sov']) for r in results]
    aided_sovs = [parse_percentage(r['aided_sov']) for r in results]

    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    print(f"Models tested: {len(results)}")
    print(f"\nUnaided SOV:")
    print(f"  Best:    {max(unaided_sovs):.1f}% ({[r['model_name'] for r in results_sorted if parse_percentage(r['unaided_sov']) == max(unaided_sovs)][0]})")
    print(f"  Worst:   {min(unaided_sovs):.1f}% ({[r['model_name'] for r in results_sorted if parse_percentage(r['unaided_sov']) == min(unaided_sovs)][0]})")
    print(f"  Average: {sum(unaided_sovs)/len(unaided_sovs):.1f}%")
    print(f"  Median:  {sorted(unaided_sovs)[len(unaided_sovs)//2]:.1f}%")

    print(f"\nAided SOV:")
    print(f"  Best:    {max(aided_sovs):.1f}%")
    print(f"  Worst:   {min(aided_sovs):.1f}%")
    print(f"  Average: {sum(aided_sovs)/len(aided_sovs):.1f}%")

    # Count how many models mention GoDaddy
    mention_count = sum(1 for sov in unaided_sovs if sov > 0)
    print(f"\nModels mentioning GoDaddy (unaided): {mention_count}/{len(results)}")

    return results_sorted

def analyze_individual(filepath):
    """Analyze individual model results in detail"""
    results = load_individual_csv(filepath)
    model_name = results[0]['model_name'] if results else "Unknown"

    print("\n" + "="*70)
    print(f"DETAILED ANALYSIS: {model_name}")
    print("="*70)

    # Group by category
    by_category = defaultdict(list)
    for row in results:
        by_category[row['category']].append(row)

    print(f"\n{'Category':<25} {'Total':<8} {'GD Hits':<10} {'SOV':<10}")
    print("-"*70)

    for category in sorted(by_category.keys()):
        rows = by_category[category]
        total = len(rows)
        hits = sum(1 for r in rows if r['godaddy_mentioned'] == 'Y')
        sov = (hits / total * 100) if total > 0 else 0

        print(f"{category:<25} {total:<8} {hits:<10} {sov:>5.1f}%")

    # Show all GoDaddy mentions
    gd_mentions = [r for r in results if r['godaddy_mentioned'] == 'Y']
    if gd_mentions:
        print(f"\n{'='*70}")
        print(f"GODADDY MENTIONS ({len(gd_mentions)} total)")
        print("="*70)

        for row in gd_mentions:
            print(f"\n[{row['prompt_id']}] {row['prompt_text']}")
            print(f"  Category: {row['category']} | Type: {row['type']}")
            print(f"  Competitors: {row['competitors_cited']}")
            print(f"  Excerpt: {row['response_excerpt'][:150]}...")

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <file_or_directory>")
        print("\nExamples:")
        print("  python analyze_results.py benchmarks/geo_multi_comparison_2026-06-W26.csv")
        print("  python analyze_results.py benchmarks/")
        sys.exit(1)

    path = sys.argv[1]

    # Check if it's a directory
    if os.path.isdir(path):
        # Find comparison files
        comparison_files = glob.glob(os.path.join(path, "geo_multi_comparison_*.csv"))
        if comparison_files:
            # Use the most recent one
            latest = max(comparison_files, key=os.path.getmtime)
            print(f"Analyzing: {latest}")
            results = load_comparison_csv(latest)
            analyze_comparison(results)

            # Ask if user wants detailed analysis
            print("\n" + "="*70)
            print("Individual model results available:")
            individual_files = glob.glob(os.path.join(path, "geo_multi_*.csv"))
            individual_files = [f for f in individual_files if "comparison" not in f]

            if individual_files:
                print(f"Found {len(individual_files)} individual result files")
                print("\nTo see detailed analysis for a specific model, run:")
                print(f"  python analyze_results.py {individual_files[0]}")
        else:
            print(f"No comparison files found in {path}")
            print("Run geo_benchmark_multi_model.py first")

    # Check if it's a specific file
    elif os.path.isfile(path):
        if "comparison" in path:
            results = load_comparison_csv(path)
            analyze_comparison(results)
        else:
            analyze_individual(path)
    else:
        print(f"Path not found: {path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
