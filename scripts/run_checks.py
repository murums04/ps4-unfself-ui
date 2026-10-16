import argparse
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("suite", choices=("core", "ui"))
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
test = "test_converter.py" if args.suite == "core" else "test_ui.py"
subprocess.run([sys.executable, "-m", "pytest", f"tests/{test}", "-q"], cwd=root, check=True)
print(f"{args.suite.upper()}_SUITE_PASSED")
