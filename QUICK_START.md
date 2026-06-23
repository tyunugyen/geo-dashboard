# GEO Multi-Model Benchmark - Quick Start Guide

## What You Have Now

✅ **Fixed original script** (`geo_benchmark_runner.py`)
- Model updated to `claude-sonnet-4-6`
- Unicode issues fixed
- Ready for production use

✅ **New multi-model runner** (`geo_benchmark_multi_model.py`)
- Test Claude, OpenAI, Gemini, and 10+ other models
- Side-by-side comparison reports
- Flexible CLI interface

✅ **Test suite** (`test_multi_model.py`)
- Quick validation with 3 models, 5 prompts
- Takes ~2 minutes to run

✅ **Analysis tool** (`analyze_results.py`)
- Generate insights from benchmark results
- Category breakdowns and detailed reports

## 30-Second Quick Start

```bash
# 1. Make sure API key is set (already done!)
echo $CAAS_API_KEY

# 2. Run quick test (2 minutes)
cd ~/geo-dashboard
python test_multi_model.py

# 3. Run full Claude benchmark (5 minutes)
python geo_benchmark_multi_model.py

# 4. View results
cat benchmarks/geo_multi_comparison_*.csv
```

## Common Commands

### Test Single Model
```bash
# Test Claude Sonnet
python geo_benchmark_multi_model.py --model claude-sonnet-4-6

# Test GPT-4o
python geo_benchmark_multi_model.py --model gpt-4o

# Test Gemini Pro
python geo_benchmark_multi_model.py --model gemini-2.5-pro
```

### Test Model Groups
```bash
# Just Claude models (default)
python geo_benchmark_multi_model.py

# OpenAI models
python geo_benchmark_multi_model.py --models openai

# Gemini models
python geo_benchmark_multi_model.py --models gemini

# Claude + OpenAI + Gemini
python geo_benchmark_multi_model.py --models claude openai gemini

# Everything (warning: 10+ models, takes 30+ min)
python geo_benchmark_multi_model.py --models all
```

### Analyze Results
```bash
# Analyze latest comparison
python analyze_results.py benchmarks/

# Analyze specific file
python analyze_results.py benchmarks/geo_multi_comparison_2026-06-W26.csv

# Detailed analysis of one model
python analyze_results.py benchmarks/geo_multi_claude-sonnet-4-6_2026-06-W26.csv
```

## What Gets Generated

### `benchmarks/geo_multi_comparison_{run_id}.csv`
Summary comparison of all tested models showing:
- Unaided SOV (% of generic questions mentioning GoDaddy)
- Aided SOV (% of branded questions mentioning GoDaddy)
- Hit counts and totals

Example output:
```
model_name              unaided_sov  aided_sov  unaided_hits  aided_hits
Claude Sonnet 4.6       0.0%         100.0%     0/63          7/7
GPT-4o                  0.0%         100.0%     0/63          7/7
Gemini 2.5 Pro          1.6%         100.0%     1/63          7/7
```

### `benchmarks/geo_multi_{model_id}_{run_id}.csv`
Detailed results for each model showing:
- All 70 prompt responses
- GoDaddy detection (Y/N)
- Competitors mentioned
- Response excerpts
- Rate Saver mentions

## Understanding Results

### Unaided SOV (Most Important)
- Measures brand awareness without prompting
- Example: "What is the best POS for retail?" → Model mentions GoDaddy
- **Current baseline: ~0-2%** (GoDaddy rarely mentioned unprompted)
- **Target: 50-85%** depending on category

### Aided SOV (Should be 100%)
- Measures model knowledge when asked directly
- Example: "GoDaddy Payments vs Square" → Model should know about both
- **Expected: 100%** for all major models
- If < 100%, model has gaps in training data

### By Category
- **pricing_fee** (Target: 85%) - "cheapest processor", "lowest fees"
- **vertical_retail** (Target: 55%) - "best POS for retail store"
- **vertical_fb** (Target: 50%) - "best POS for coffee shop"
- **comparison** (Target: 70%) - "alternatives to Square"

## Available Models

| Provider | Models | Count |
|----------|--------|-------|
| **Claude** | Sonnet 4.6, Opus 4.8, Haiku 4.5 | 3 |
| **OpenAI** | gpt-4o, gpt-5, o3, o3-mini | 4 |
| **Gemini** | 2.5-pro, 3.1-pro-preview, 2.5-flash | 3 |
| **Research** | o3-deep-research, o4-mini-deep-research | 2 |
| **Other** | Kimi K2.5, Qwen 3 235B | 2 |
| **TOTAL** | | **14** |

Full list: See `MODEL_GROUPS` in `geo_benchmark_multi_model.py`

## Next Steps

1. **Validate Setup**
   ```bash
   python test_multi_model.py
   ```

2. **Baseline Current State**
   ```bash
   python geo_benchmark_multi_model.py --models claude openai gemini
   python analyze_results.py benchmarks/
   ```

3. **Track Over Time**
   - Run weekly/monthly
   - Compare run IDs to see trends
   - Monitor SOV improvements

4. **Deep Dive Analysis**
   - Which models know about GoDaddy?
   - Which categories need work?
   - How do competitors compare?

## Files Overview

| File | Purpose | Usage |
|------|---------|-------|
| `geo_benchmark_runner.py` | Original single-model (fixed) | GitHub Actions, scheduled runs |
| `geo_benchmark_multi_model.py` | Multi-model comparison | Ad-hoc analysis, model comparison |
| `test_multi_model.py` | Quick validation | Setup testing, sanity checks |
| `analyze_results.py` | Results analysis | Generate insights, reports |
| `GEO_BENCHMARK_README.md` | Full documentation | Reference guide |
| `QUICK_START.md` | This file | Quick reference |

## Troubleshooting

### "CAAS_API_KEY not set"
```bash
export CAAS_API_KEY=sk-20yPtGd3ze4thasIsdnkqQ
# or
source ~/.bashrc
```

### "Connection FAILED"
```bash
# Test proxy
curl -H "Authorization: Bearer $CAAS_API_KEY" \
  https://caas-gocode-prod.caas-prod.prod.onkatana.net/v1/models
```

### "Model not found"
```bash
# List available models
curl -H "Authorization: Bearer $CAAS_API_KEY" \
  https://caas-gocode-prod.caas-prod.prod.onkatana.net/v1/models | python -m json.tool
```

### Script runs slow
- Increase `DELAY_SECS` in config (default: 0.5)
- Use `--quiet` flag for less output
- Test fewer models at once

## Tips

💡 **Start small** - Use `test_multi_model.py` before full runs

💡 **Focus on key models** - Claude, GPT-4o, and Gemini Pro are most important

💡 **Watch aided SOV** - Should always be 100%; if not, model has training gaps

💡 **Compare categories** - Some categories naturally perform better than others

💡 **Track trends** - Run regularly and compare `run_id` over time

💡 **Use quiet mode for automation** - `--quiet` flag for cleaner logs

## Questions?

See `GEO_BENCHMARK_README.md` for full documentation.
