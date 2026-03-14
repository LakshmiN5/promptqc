# Running PromptQC Tests with Groq

## Setup

1. **Get a free Groq API key:**
   - Visit: https://console.groq.com/keys
   - Sign up and create an API key

2. **Set the API key in your terminal:**
   ```bash
   export GROQ_API_KEY='your-api-key-here'
   ```

3. **Install dependencies (if not already installed):**
   ```bash
   pip install litellm
   ```

## Run All Tests

```bash
cd test_suite
python3 run_groq_test.py
```

This will test:
- ✅ 5 good prompts (should score A or B)
- ❌ 6 bad prompts (should score C, D, or F)
- 🔧 6 edge cases (should not crash)

## Alternative: Run Without LLM Judge

If you want to test without Groq (using only embeddings):

```bash
python3 run_accuracy_test.py
```

## Quick Test Single Prompt

```bash
# Test a good prompt
promptqc test_suite/good_prompts/01_customer_service.txt --judge groq/llama3-8b-8192

# Test a bad prompt
promptqc test_suite/bad_prompts/01_contradictions.txt --judge groq/llama3-8b-8192
```

## Available Groq Models (Free)

- `groq/qwen-2.5-32b-instruct` (recommended, balanced)
- `groq/llama-3.3-70b-versatile` (most accurate)
- `groq/mixtral-8x7b-32768` (good balance)
- `groq/gemma2-9b-it` (alternative)

See: https://console.groq.com/docs/models for full list