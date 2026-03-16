#!/usr/bin/env python3
"""Quick smoke test for PromptQC using MiniMax (MiniMax-M2.5, 204K context).

Usage:
    export MINIMAX_API_KEY="your-key-here"
    python test_suite/run_test_minimax.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from promptqc.analyzer import PromptAnalyzer

if not os.environ.get("MINIMAX_API_KEY"):
    print("MINIMAX_API_KEY not set – skipping MiniMax test")
    sys.exit(0)

analyzer = PromptAnalyzer(judge_model="minimax/MiniMax-M2.5")
path = Path("test_suite/bad_prompts/05_confused_bot.txt")
result = analyzer.analyze(path.read_text())
print(f"Score: {result.quality_score.total}")
