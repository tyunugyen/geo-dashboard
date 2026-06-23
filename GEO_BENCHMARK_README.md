# GEO Multi-Model Benchmark Suite

Comprehensive benchmark suite for testing GoDaddy Payments (GEO) brand awareness across multiple LLM models via GoCaaS proxy.

## Files

### Main Scripts

1. **`geo_benchmark_runner.py`** (Updated)
   - Original single-model runner with fixes
   - Uses Claude Sonnet 4.6
   - Fixed Unicode encoding issues for Windows
   - Ready for GitHub Actions

2. **`geo_benchmark_multi_model.py`** (New)
   - Multi-model benchmark runner
   - Tests Claude, OpenAI, Gemini, and other models
   - Generates comparison reports
   - Highly configurable via CLI arguments

3. **`test_multi_model.py`** (New)
   - Quick test runner with subset of prompts
   - Validates setup before full benchmark
   - Tests 3 models with 5 prompts

## Setup

### Prerequisites

```bash
# Install dependencies
pip install openai

# Set API key (already done in ~/.bashrc)
export CAAS_API_KEY=sk-20yPtGd3ze4thasIsdnkqQ

# Or source your bashrc
source ~/.bashrc
```

### Available Models

The suite includes these model groups:

**Claude Models** (`--models claude`)
- `claude-sonnet-4-6` - Claude Sonnet 4.6
- `claude-opus-4-8` - Claude Opus 4.8
- `claude-haiku-4-5-20251001` - Claude Haiku 4.5

**OpenAI Models** (`--models openai`)
- `gpt-4o` - GPT-4 Optimized
- `gpt-5` - GPT-5
- `o3` - OpenAI o3
- `o3-mini` - OpenAI o3-mini

**Gemini Models** (`--models gemini`)
- `gemini-2.5-pro` - Gemini 2.5 Pro
- `gemini-3.1-pro-preview` - Gemini 3.1 Pro Preview
- `gemini-2.5-flash` - Gemini 2.5 Flash

**Deep Research Models** (`--models research`)
- `o3-deep-research` - o3 Deep Research
- `o4-mini-deep-research` - o4-mini Deep Research

**Other Models** (`--models other`)
- `kimi-k2.5` - Kimi K2.5
- `qwen3-235b-a22b-2507` - Qwen 3 235B

## Usage

### Quick Test (Recommended First)

Test your setup with a small subset:

```bash
python test_multi_model.py
```

This runs 3 models (Claude, GPT, Gemini) with 5 prompts to validate everything works.

### Single Model Benchmark

Run the original single-model benchmark:

```bash
python geo_benchmark_runner.py
```

Output:
- `benchmarks/geo_audit_results_2026-06-W26.csv`
- `public/data.json`

### Multi-Model: All Claude Models (Default)

```bash
python geo_benchmark_multi_model.py
```

Runs all Claude models (Sonnet, Opus, Haiku) against 70 prompts.

### Multi-Model: Specific Model Group

```bash
# Test OpenAI models only
python geo_benchmark_multi_model.py --models openai

# Test Gemini models only
python geo_benchmark_multi_model.py --models gemini

# Test multiple groups
python geo_benchmark_multi_model.py --models claude openai gemini

# Test ALL models (warning: takes a while!)
python geo_benchmark_multi_model.py --models all
```

### Multi-Model: Single Specific Model

```bash
# Test just GPT-4o
python geo_benchmark_multi_model.py --model gpt-4o

# Test just Gemini Pro
python geo_benchmark_multi_model.py --model gemini-2.5-pro
```

### Quiet Mode

Minimal output for automation:

```bash
python geo_benchmark_multi_model.py --quiet
python geo_benchmark_multi_model.py -q --models all
```

## Output Files

### Individual Model Results

Location: `benchmarks/geo_multi_{model_id}_{run_id}.csv`

Example: `benchmarks/geo_multi_claude-sonnet-4-6_2026-06-W26.csv`

Columns:
- `run_id`, `run_date` - Benchmark run metadata
- `model_id`, `model_name` - Model information
- `prompt_id`, `type`, `category` - Prompt details
- `prompt_text` - The actual prompt
- `godaddy_mentioned` - Y/N if GoDaddy was mentioned
- `rate_accurate` - Y/N if pricing was accurate
- `rate_saver_mentioned` - Y/N if Rate Saver mentioned
- `competitors_cited` - Which competitors mentioned
- `response_excerpt` - First 300 chars of response

### Comparison Summary

Location: `benchmarks/geo_multi_comparison_{run_id}.csv`

Example: `benchmarks/geo_multi_comparison_2026-06-W26.csv`

Columns:
- `model_id`, `model_name` - Model information
- `unaided_sov` - % of unaided prompts mentioning GoDaddy
- `aided_sov` - % of aided prompts mentioning GoDaddy
- `rate_saver_sov` - % mentioning Rate Saver feature
- `unaided_hits`, `unaided_prompts` - Hit rate details
- `aided_hits`, `aided_prompts` - Aided hit rate details
- `status` - success or error message

## Understanding Results

### Key Metrics

**Unaided SOV (Share of Voice)**
- % of prompts where GoDaddy was mentioned WITHOUT being in the prompt
- Target varies by category (50-85%)
- Most important metric for brand awareness

**Aided SOV**
- % of prompts where GoDaddy was mentioned WHEN it was in the prompt
- Should be 100% for branded/comparison prompts
- Lower values indicate model issues

**Rate Saver SOV**
- % of prompts mentioning the Rate Saver feature
- Important for feature awareness

### Prompt Types

**U - Unaided** (63 prompts)
- Generic questions like "What is the best POS for retail?"
- Tests true brand awareness
- Example: "What is the cheapest payment processor?"

**B - Branded/Aided** (7 prompts)
- GoDaddy explicitly mentioned in prompt
- Tests model knowledge when asked directly
- Example: "GoDaddy Payments vs Square"

### Categories

1. **pricing_fee** - Pricing and fee-related questions
2. **top_funnel_pos** - General POS system questions
3. **payment_processing** - Payment processing capabilities
4. **vertical_fb** - Food & Beverage specific
5. **vertical_retail** - Retail specific
6. **general_in_person** - Service businesses
7. **support** - Support and migration questions
8. **comparison** - Direct competitor comparisons

## Example Workflows

### Quick Sanity Check

```bash
# Quick test to validate setup
python test_multi_model.py
```

### Compare Claude vs OpenAI vs Gemini

```bash
# Run top model from each provider
python geo_benchmark_multi_model.py --model claude-sonnet-4-6
python geo_benchmark_multi_model.py --model gpt-4o
python geo_benchmark_multi_model.py --model gemini-2.5-pro

# Or run all at once
python geo_benchmark_multi_model.py --models claude openai gemini
```

### Full Competitive Analysis

```bash
# Run all models (warning: ~10-15 minutes per model)
python geo_benchmark_multi_model.py --models all

# View results
cat benchmarks/geo_multi_comparison_2026-06-W26.csv
```

### Weekly Tracking (GitHub Actions)

Keep using the original runner for consistency:

```bash
python geo_benchmark_runner.py
```

Use multi-model runner for deep-dive analysis as needed.

## Fixes Applied

1. **Model Name** - Updated from invalid `claude-3-7-sonnet-20250219` to `claude-sonnet-4-6`
2. **Unicode Issues** - Replaced checkmark emojis (✅/❌) with ASCII ([OK]/[FAIL])
3. **Multi-Model Support** - Added framework for testing any model in GoCaaS proxy
4. **Better Error Handling** - Graceful handling of model failures
5. **Comparison Reports** - Side-by-side comparison of all tested models

## Troubleshooting

### Connection Failed

```bash
# Check API key is set
echo $CAAS_API_KEY

# Check proxy connectivity
curl -H "Authorization: Bearer $CAAS_API_KEY" \
  https://caas-gocode-prod.caas-prod.prod.onkatana.net/v1/models
```

### Model Not Found

```bash
# List available models
curl -H "Authorization: Bearer $CAAS_API_KEY" \
  https://caas-gocode-prod.caas-prod.prod.onkatana.net/v1/models | python -m json.tool
```

### Rate Limiting

If you hit rate limits, increase `DELAY_SECS` in the config section of the script.

## Next Steps

1. Run quick test to validate: `python test_multi_model.py`
2. Run full Claude benchmark: `python geo_benchmark_multi_model.py`
3. Expand to other models: `python geo_benchmark_multi_model.py --models openai gemini`
4. Analyze results in `benchmarks/geo_multi_comparison_*.csv`
5. Continue using original runner for scheduled jobs

## Questions?

- Check model availability: `/v1/models` endpoint
- Adjust `MODEL_GROUPS` in `geo_benchmark_multi_model.py` to add/remove models
- Modify `PROMPTS` array to test different questions
- Adjust `DELAY_SECS` if hitting rate limits
