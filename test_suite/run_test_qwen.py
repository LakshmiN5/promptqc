import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from promptqc.analyzer import PromptAnalyzer

analyzer = PromptAnalyzer(judge_model="groq/qwen-2.5-32b")
path = Path("test_suite/bad_prompts/05_confused_bot.txt")
result = analyzer.analyze(path.read_text())
print(f"Score: {result.quality_score.total}")
