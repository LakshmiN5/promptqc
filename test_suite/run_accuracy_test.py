#!/usr/bin/env python3
"""
Accuracy test runner for PromptQC
Tests both default mode and judge mode against good and bad prompts
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from promptqc.analyzer import PromptAnalyzer


def test_prompt_file(filepath: Path, analyzer: PromptAnalyzer, expected_quality: str) -> dict:
    """Test a single prompt file and return results"""
    with open(filepath, 'r') as f:
        prompt = f.read()
    
    result = analyzer.analyze(prompt)
    
    # Get score and grade from quality_score
    score = result.quality_score.total if result.quality_score else 0
    grade = result.quality_score.grade if result.quality_score else 'F'
    
    # Determine if test passed based on expected quality
    if expected_quality == "good":
        passed = grade in ['A', 'B']  # Good prompts should score A or B
    else:  # bad
        passed = grade in ['C', 'D', 'F']  # Bad prompts should score C, D, or F
    
    return {
        'file': filepath.name,
        'expected': expected_quality,
        'score': score,
        'grade': grade,
        'passed': passed,
        'issues': len(result.issues),
        'critical_issues': sum(1 for issue in result.errors)
    }


def run_test_suite(use_judge: bool = False):
    """Run the full test suite"""
    print(f"\n{'='*80}")
    print(f"Running PromptQC Accuracy Test Suite")
    print(f"Mode: {'LLM Judge' if use_judge else 'Default (Embeddings)'}")
    print(f"{'='*80}\n")
    
    # Setup analyzer
    if use_judge:
        analyzer = PromptAnalyzer(judge_model="groq/qwen/qwen3-32b")
    else:
        analyzer = PromptAnalyzer()
    
    # Get test directories
    test_dir = Path(__file__).parent
    good_dir = test_dir / "good_prompts"
    bad_dir = test_dir / "bad_prompts"
    
    results = {
        'good': [],
        'bad': []
    }
    
    # Test good prompts
    print("Testing GOOD prompts (should score A or B):")
    print("-" * 80)
    for filepath in sorted(good_dir.glob("*.txt")):
        result = test_prompt_file(filepath, analyzer, "good")
        results['good'].append(result)
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        print(f"{status} | {result['file']:30s} | Score: {result['score']:5.1f} | Grade: {result['grade']} | Issues: {result['issues']}")
    
    print("\n" + "="*80 + "\n")
    
    # Test bad prompts
    print("Testing BAD prompts (should score C, D, or F):")
    print("-" * 80)
    for filepath in sorted(bad_dir.glob("*.txt")):
        result = test_prompt_file(filepath, analyzer, "bad")
        results['bad'].append(result)
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        print(f"{status} | {result['file']:30s} | Score: {result['score']:5.1f} | Grade: {result['grade']} | Issues: {result['issues']}")
    
    # Calculate accuracy
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    good_passed = sum(1 for r in results['good'] if r['passed'])
    good_total = len(results['good'])
    bad_passed = sum(1 for r in results['bad'] if r['passed'])
    bad_total = len(results['bad'])
    total_passed = good_passed + bad_passed
    total_tests = good_total + bad_total
    
    print(f"\nGood Prompts: {good_passed}/{good_total} correct ({100*good_passed/good_total:.1f}%)")
    print(f"Bad Prompts:  {bad_passed}/{bad_total} correct ({100*bad_passed/bad_total:.1f}%)")
    print(f"\nOverall Accuracy: {total_passed}/{total_tests} ({100*total_passed/total_tests:.1f}%)")
    
    # Show failures
    failures = [r for r in results['good'] + results['bad'] if not r['passed']]
    if failures:
        print(f"\n{'='*80}")
        print("FAILURES")
        print("="*80)
        for failure in failures:
            print(f"\n{failure['file']} (expected {failure['expected']}):")
            print(f"  Score: {failure['score']:.1f} | Grade: {failure['grade']}")
            print(f"  Issues: {failure['issues']} total, {failure['critical_issues']} critical")
    
    print("\n" + "="*80 + "\n")
    
    return total_passed == total_tests


if __name__ == "__main__":
    # Test both modes
    print("\n" + "="*80)
    print("PROMPTQC ACCURACY TEST SUITE")
    print("="*80)
    
    # Default mode
    default_passed = run_test_suite(use_judge=False)
    
    # Judge mode (if available)
    try:
        judge_passed = run_test_suite(use_judge=True)
    except Exception as e:
        print(f"\nLLM Judge mode failed: {e}")
        print("Make sure you have:")
        print("  1. Installed litellm: pip install litellm")
        print("  2. Set up Ollama or API keys (GROQ_API_KEY, etc.)")
        judge_passed = False
    
    # Final result
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    print(f"Default Mode: {'✓ PASSED' if default_passed else '✗ FAILED'}")
    print(f"Judge Mode:   {'✓ PASSED' if judge_passed else '✗ FAILED'}")
    print("="*80 + "\n")
    
    sys.exit(0 if (default_passed and judge_passed) else 1)

# Made with Bob
