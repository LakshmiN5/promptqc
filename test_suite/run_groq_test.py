#!/usr/bin/env python3
"""
Comprehensive test runner for PromptQC using Groq (free)
Tests good prompts, bad prompts, and edge cases
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
    elif expected_quality == "bad":
        passed = grade in ['C', 'D', 'F']  # Bad prompts should score C, D, or F
    else:  # edge case - just check it doesn't crash
        passed = True
    
    return {
        'file': filepath.name,
        'expected': expected_quality,
        'score': score,
        'grade': grade,
        'passed': passed,
        'issues': len(result.issues),
        'errors': sum(1 for issue in result.errors),
        'warnings': sum(1 for issue in result.warnings),
        'suggestions': sum(1 for issue in result.suggestions),
        'result': result
    }


def print_detailed_issues(result_dict: dict):
    """Print detailed issue information"""
    result = result_dict['result']
    if result.issues:
        print(f"\n  Issues found:")
        for issue in result.issues[:5]:  # Show first 5 issues
            print(f"    [{issue.severity.value}] {issue.rule_id}: {issue.message}")
            if issue.line_content:
                print(f"      Line {issue.line}: {issue.line_content[:60]}...")
        if len(result.issues) > 5:
            print(f"    ... and {len(result.issues) - 5} more issues")


def run_test_suite():
    """Run the full test suite with Groq"""
    print(f"\n{'='*80}")
    print(f"PromptQC Comprehensive Test Suite - Using Groq (Free)")
    print(f"{'='*80}\n")
    
    # Check for Groq API key
    if not os.environ.get('GROQ_API_KEY'):
        print("⚠️  WARNING: GROQ_API_KEY not set in environment")
        print("   Get your free API key from: https://console.groq.com/keys")
        print("   Set it with: export GROQ_API_KEY='your-key-here'\n")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Setup analyzer with Groq's Llama model (llama-3.3-70b-versatile)
    # Other options: llama-3.1-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it
    # Note: Use models from https://console.groq.com/docs/models
    print("Initializing analyzer with Groq model: llama-3.3-70b-versatile...")
    try:
        analyzer = PromptAnalyzer(judge_model="groq/llama-3.3-70b-versatile")
        print("✓ Analyzer initialized successfully\n")
    except Exception as e:
        print(f"✗ Failed to initialize analyzer: {e}")
        print("\nMake sure you have:")
        print("  1. Installed litellm: pip install litellm")
        print("  2. Set GROQ_API_KEY environment variable")
        sys.exit(1)
    
    # Get test directories
    test_dir = Path(__file__).parent
    good_dir = test_dir / "good_prompts"
    bad_dir = test_dir / "bad_prompts"
    edge_dir = test_dir / "edge_cases"
    
    results = {
        'good': [],
        'bad': [],
        'edge': []
    }
    
    # Test good prompts
    print("="*80)
    print("TESTING GOOD PROMPTS (should score A or B)")
    print("="*80)
    for filepath in sorted(good_dir.glob("*.txt")):
        print(f"\nTesting: {filepath.name}")
        try:
            result = test_prompt_file(filepath, analyzer, "good")
            results['good'].append(result)
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            print(f"{status} | Score: {result['score']:5.1f} | Grade: {result['grade']} | "
                  f"Issues: {result['issues']} (E:{result['errors']}, W:{result['warnings']}, S:{result['suggestions']})")
            if not result['passed']:
                print_detailed_issues(result)
        except Exception as e:
            print(f"✗ ERROR: {e}")
            results['good'].append({
                'file': filepath.name,
                'expected': 'good',
                'score': 0,
                'grade': 'F',
                'passed': False,
                'issues': 0,
                'errors': 0,
                'warnings': 0,
                'suggestions': 0,
                'error': str(e)
            })
    
    # Test bad prompts
    print("\n" + "="*80)
    print("TESTING BAD PROMPTS (should score C, D, or F)")
    print("="*80)
    for filepath in sorted(bad_dir.glob("*.txt")):
        print(f"\nTesting: {filepath.name}")
        try:
            result = test_prompt_file(filepath, analyzer, "bad")
            results['bad'].append(result)
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            print(f"{status} | Score: {result['score']:5.1f} | Grade: {result['grade']} | "
                  f"Issues: {result['issues']} (E:{result['errors']}, W:{result['warnings']}, S:{result['suggestions']})")
            if not result['passed']:
                print_detailed_issues(result)
        except Exception as e:
            print(f"✗ ERROR: {e}")
            results['bad'].append({
                'file': filepath.name,
                'expected': 'bad',
                'score': 100,
                'grade': 'A',
                'passed': False,
                'issues': 0,
                'errors': 0,
                'warnings': 0,
                'suggestions': 0,
                'error': str(e)
            })
    
    # Test edge cases
    print("\n" + "="*80)
    print("TESTING EDGE CASES (should not crash)")
    print("="*80)
    for filepath in sorted(edge_dir.glob("*.txt")):
        print(f"\nTesting: {filepath.name}")
        try:
            result = test_prompt_file(filepath, analyzer, "edge")
            results['edge'].append(result)
            print(f"✓ PASS | Score: {result['score']:5.1f} | Grade: {result['grade']} | "
                  f"Issues: {result['issues']} (E:{result['errors']}, W:{result['warnings']}, S:{result['suggestions']})")
        except Exception as e:
            print(f"✗ FAIL: {e}")
            results['edge'].append({
                'file': filepath.name,
                'expected': 'edge',
                'score': 0,
                'grade': 'F',
                'passed': False,
                'issues': 0,
                'errors': 0,
                'warnings': 0,
                'suggestions': 0,
                'error': str(e)
            })
    
    # Calculate accuracy
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    good_passed = sum(1 for r in results['good'] if r['passed'])
    good_total = len(results['good'])
    bad_passed = sum(1 for r in results['bad'] if r['passed'])
    bad_total = len(results['bad'])
    edge_passed = sum(1 for r in results['edge'] if r['passed'])
    edge_total = len(results['edge'])
    total_passed = good_passed + bad_passed + edge_passed
    total_tests = good_total + bad_total + edge_total
    
    print(f"\nGood Prompts:  {good_passed}/{good_total} correct ({100*good_passed/good_total if good_total else 0:.1f}%)")
    print(f"Bad Prompts:   {bad_passed}/{bad_total} correct ({100*bad_passed/bad_total if bad_total else 0:.1f}%)")
    print(f"Edge Cases:    {edge_passed}/{edge_total} passed ({100*edge_passed/edge_total if edge_total else 0:.1f}%)")
    print(f"\nOverall:       {total_passed}/{total_tests} ({100*total_passed/total_tests if total_tests else 0:.1f}%)")
    
    # Show failures
    all_results = results['good'] + results['bad'] + results['edge']
    failures = [r for r in all_results if not r['passed']]
    if failures:
        print(f"\n{'='*80}")
        print(f"FAILURES ({len(failures)} total)")
        print("="*80)
        for failure in failures:
            print(f"\n{failure['file']} (expected {failure['expected']}):")
            if 'error' in failure:
                print(f"  ERROR: {failure['error']}")
            else:
                print(f"  Score: {failure['score']:.1f} | Grade: {failure['grade']}")
                print(f"  Issues: {failure['issues']} total ({failure['errors']} errors, "
                      f"{failure['warnings']} warnings, {failure['suggestions']} suggestions)")
    
    print("\n" + "="*80)
    print(f"Test {'PASSED ✓' if total_passed == total_tests else 'FAILED ✗'}")
    print("="*80 + "\n")
    
    return total_passed == total_tests


if __name__ == "__main__":
    try:
        success = run_test_suite()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
