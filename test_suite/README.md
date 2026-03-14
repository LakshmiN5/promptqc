# PromptQC Test Suite

This directory contains the comprehensive test suite for PromptQC validation.

## Structure

```
test_suite/
├── README.md                    # This file
├── TEST_OBSERVATIONS.md         # Detailed test results and analysis
├── RUN_TESTS.md                # How to run tests
├── good_prompts/               # High-quality prompts (should score A/B)
├── bad_prompts/                # Low-quality prompts (should score D/F)
├── edge_cases/                 # Edge cases and stress tests
├── examples/                   # Example prompts for manual testing
├── run_accuracy_test.py        # Main accuracy test runner
├── run_groq_test.py           # LLM judge test runner (requires API key)
└── run_test_qwen.py           # Alternative LLM judge test
```

## Quick Start

### Run Accuracy Tests
```bash
cd test_suite
python3 run_accuracy_test.py
```

### Run with LLM Judge (requires GROQ_API_KEY)
```bash
export GROQ_API_KEY="your-key-here"
python3 run_groq_test.py
```

### Test Individual Prompts
```bash
# Good prompt
promptqc check good_prompts/01_customer_service.txt

# Bad prompt
promptqc check bad_prompts/02_security_issues.txt

# With LLM judge
promptqc check bad_prompts/01_contradictions.txt --judge groq/llama3-8b-8192
```

## Test Categories

### Good Prompts (Expected: Grade A/B)
- `01_customer_service.txt` - Professional customer service agent
- `02_code_reviewer.txt` - Comprehensive code review guidelines
- `03_data_scientist.txt` - Data analysis assistant
- `04_markdown_formatter.txt` - Document formatting bot
- `05_devops_engineer.txt` - DevOps automation assistant

### Bad Prompts (Expected: Grade D/F)
- `01_contradictions.txt` - Contains conflicting instructions
- `02_security_issues.txt` - Critical security vulnerabilities
- `03_vague_incomplete.txt` - Extremely vague and incomplete
- `04_token_inefficient.txt` - Verbose and redundant
- `05_confused_bot.txt` - Unclear role and purpose
- `06_script_runner_injection.txt` - Injection vulnerabilities

### Edge Cases
- `01_empty_prompt.txt` - Empty file
- `02_single_word.txt` - Single word prompt
- `03_only_special_chars.txt` - Only special characters
- `04_extremely_long.txt` - 5000+ word prompt
- `05_mixed_languages.txt` - Multiple languages
- `06_code_injection_attempt.txt` - Injection attempt

## Current Results

**Overall Accuracy**: 83.3% (5/6 tests passed)
- Good prompts: 100% (2/2)
- Bad prompts: 75% (3/4)

See [TEST_OBSERVATIONS.md](TEST_OBSERVATIONS.md) for detailed analysis.

## Adding New Tests

1. Create a new `.txt` file in the appropriate directory
2. Add expected score/grade to the test runner
3. Run tests and verify results
4. Update TEST_OBSERVATIONS.md with findings

## Test Maintenance

- Review tests after each major version release
- Update expected scores if scoring algorithm changes
- Add new test cases for reported issues
- Keep TEST_OBSERVATIONS.md up to date