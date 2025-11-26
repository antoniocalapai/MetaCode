import os
import zipfile
import json
from pathlib import Path
from collections import Counter
import ast

BASE = Path(".")
ZIP_DIR = BASE / "zips"
EXTRACT_DIR = BASE / "extracted"
RESULTS_DIR = BASE / "results"

EXTRACT_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# -----------------------------
# 1. UNZIP ALL REPOS
# -----------------------------
for zip_path in ZIP_DIR.glob("*.zip"):
    repo_name = zip_path.stem
    out_path = EXTRACT_DIR / repo_name

    if not out_path.exists():
        print(f"Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(out_path)


# -----------------------------
# 2. METRIC FUNCTIONS
# -----------------------------
def get_python_files(repo_path):
    """Return list of all Python files in a repo."""
    return list(repo_path.rglob("*.py"))


def count_lines(file_path):
    """Count lines in file (robust)."""
    try:
        with open(file_path, "r", errors="ignore") as f:
            return sum(1 for _ in f)
    except:
        return 0


def extract_imports(pyfile):
    """Extract imported modules from a Python file."""
    try:
        tree = ast.parse(pyfile.read_text(errors="ignore"))
    except SyntaxError:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports += [name.name.split(".")[0] for name in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])
    return imports


# -----------------------------
# 3. ANALYZE PER-REPO
# -----------------------------
report = {}

for repo in EXTRACT_DIR.iterdir():
    if not repo.is_dir():
        continue

    print(f"Analyzing: {repo.name}")

    pyfiles = get_python_files(repo)
    total_lines = sum(count_lines(p) for p in pyfiles)

    import_counter = Counter()
    for p in pyfiles:
        import_counter.update(extract_imports(p))

    report[repo.name] = {
        "total_lines": total_lines,
        "num_py_files": len(pyfiles),
        "top_imports": import_counter.most_common(20),
    }


# -----------------------------
# 4. SAVE RESULTS
# -----------------------------
with open(RESULTS_DIR / "analysis.json", "w") as f:
    json.dump(report, f, indent=2)

print("Done! Results saved to results/analysis.json")