import os
import json
from pathlib import Path
from collections import Counter
import ast
import re

# Try to import radon for complexity metrics
try:
    from radon.complexity import cc_visit
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False
    print("[WARNING] radon not installed. Cyclomatic complexity will be empty.")

# Point to your existing folder of repositories
REPOS_DIR = Path("/Users/acalapai/Desktop/CodeAnalysis/repos")
RESULTS_DIR = Path("/Users/acalapai/Desktop/CodeAnalysis/results")

# Make sure the results directory exists
RESULTS_DIR.mkdir(exist_ok=True)

# -----------------------------------------
# PSEUDO-COMPLEXITY (simple model + dict comprehensions)
# -----------------------------------------

def compute_pseudo_complexity(text: str):
    """
    Simple pseudo-complexity:
    Counts decision-making keywords + dictionary comprehensions.
    """
    keywords = [
        "if ", "elif ", "for ", "while ",
        "try:", "except", " and ", " or "
    ]

    decision_points = 0

    # Count keywords
    for kw in keywords:
        decision_points += text.count(kw)

    # Detect dictionary comprehensions: { ... for ... in ... }
    dict_pattern = r"\{[^}]*for[^}]*\}"
    dict_matches = re.findall(dict_pattern, text, flags=re.DOTALL)
    dict_comp_count = len(dict_matches)

    decision_points += dict_comp_count  # add dict comp weight

    return {
        "decision_points": decision_points,
        "dict_comprehensions": dict_comp_count,
    }

# -----------------------------------------
# FILE DISCOVERY
# -----------------------------------------

def get_source_files(repo_path: Path):
    """Return all source-code files (Python + MATLAB)."""
    exts = [".py", ".m"]
    return [p for p in repo_path.rglob("*") if p.suffix in exts]

# -----------------------------------------
# PYTHON FILE ANALYSIS
# -----------------------------------------

def analyze_python_file(file_path: Path):
    """Analyze a Python file with LOC, comments, imports, AST, radon, pseudo-complexity."""
    try:
        text = file_path.read_text(errors="ignore")
    except Exception:
        m = empty_metrics()
        m["pseudo_complexity"] = compute_pseudo_complexity("")
        return m

    lines = text.splitlines()
    loc = len(lines)

    num_comments = sum(1 for l in lines if l.strip().startswith("#"))
    num_blank = sum(1 for l in lines if not l.strip())

    # AST metrics
    num_functions = 0
    function_names = []
    num_classes = 0
    imports_counter = Counter()

    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None

    if tree is not None:
        for node in ast.walk(tree):

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                num_functions += 1
                function_names.append(node.name)

            elif isinstance(node, ast.ClassDef):
                num_classes += 1

            elif isinstance(node, ast.Import):
                for name in node.names:
                    imports_counter[name.name.split(".")[0]] += 1

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports_counter[node.module.split(".")[0]] += 1

    # Radon complexity
    avg_cc = max_cc = total_cc = 0.0
    num_entities = 0
    cc_values = []

    if RADON_AVAILABLE:
        try:
            blocks = cc_visit(text)
            cc_values = [b.complexity for b in blocks]
            num_entities = len(cc_values)
            if cc_values:
                total_cc = float(sum(cc_values))
                max_cc = float(max(cc_values))
                avg_cc = total_cc / num_entities
        except Exception:
            pass

    complexity = {
        "avg_cc": avg_cc,
        "max_cc": max_cc,
        "total_cc": total_cc,
        "num_entities": num_entities,
        "cc_values": cc_values,
    }

    # Pseudo complexity (works always)
    pseudo = compute_pseudo_complexity(text)

    return {
        "loc": loc,
        "num_comments": num_comments,
        "num_blank": num_blank,
        "num_functions": num_functions,
        "function_names": function_names,
        "num_classes": num_classes,
        "imports": dict(imports_counter),
        "complexity": complexity,
        "pseudo_complexity": pseudo,
    }

# -----------------------------------------
# MATLAB FILE ANALYSIS
# -----------------------------------------

def analyze_matlab_file(file_path: Path):
    """Basic metrics for MATLAB .m files + pseudo complexity."""
    try:
        text = file_path.read_text(errors="ignore")
    except Exception:
        m = empty_metrics()
        m["pseudo_complexity"] = compute_pseudo_complexity("")
        return m

    lines = text.splitlines()
    loc = len(lines)

    num_comments = sum(1 for l in lines if l.strip().startswith("%"))
    num_blank = sum(1 for l in lines if not l.strip())

    pseudo = compute_pseudo_complexity(text)

    return {
        "loc": loc,
        "num_comments": num_comments,
        "num_blank": num_blank,
        "num_functions": 0,
        "function_names": [],
        "num_classes": 0,
        "imports": {},
        "complexity": {
            "avg_cc": 0.0,
            "max_cc": 0.0,
            "total_cc": 0.0,
            "num_entities": 0,
            "cc_values": []
        },
        "pseudo_complexity": pseudo,
    }

# -----------------------------------------
# DEFAULT METRIC STRUCTURE
# -----------------------------------------

def empty_metrics():
    return {
        "loc": 0,
        "num_comments": 0,
        "num_blank": 0,
        "num_functions": 0,
        "function_names": [],
        "num_classes": 0,
        "imports": {},
        "complexity": {
            "avg_cc": 0.0,
            "max_cc": 0.0,
            "total_cc": 0.0,
            "num_entities": 0,
            "cc_values": []
        },
        "pseudo_complexity": {
            "decision_points": 0,
            "dict_comprehensions": 0
        }
    }

# -----------------------------------------
# ANALYZE ALL REPOSITORIES
# -----------------------------------------

report = {}
global_imports = Counter()
global_total_loc = 0
global_total_functions = 0
total_source_files = 0

for repo in REPOS_DIR.iterdir():
    if not repo.is_dir():
        continue

    print(f"Analyzing repository: {repo.name}")

    files = get_source_files(repo)
    total_source_files += len(files)

    repo_total_loc = 0
    repo_import_counter = Counter()
    repo_total_functions = 0

    files_metrics = {}

    for p in files:

        if p.suffix == ".m":
            metrics = analyze_matlab_file(p)
        elif p.suffix == ".py":
            metrics = analyze_python_file(p)
        else:
            metrics = empty_metrics()

        rel_path = str(p.relative_to(repo))
        files_metrics[rel_path] = metrics

        repo_total_loc += metrics["loc"]
        repo_import_counter.update(metrics["imports"])
        repo_total_functions += metrics["num_functions"]

        global_total_loc += metrics["loc"]
        global_total_functions += metrics["num_functions"]
        global_imports.update(metrics["imports"])

    report[repo.name] = {
        "total_lines": repo_total_loc,
        "num_source_files": len(files),
        "total_functions": repo_total_functions,
        "avg_functions_per_file": (
            repo_total_functions / len(files) if files else 0.0
        ),
        "imports": repo_import_counter.most_common(),
        "files": files_metrics,
    }

# -----------------------------------------
# GLOBAL STATISTICS
# -----------------------------------------

relative_imports = {
    module: count / total_source_files if total_source_files else 0.0
    for module, count in global_imports.items()
}

global_summary = {
    "total_source_files": total_source_files,
    "total_loc": global_total_loc,
    "total_functions": global_total_functions,
    "global_import_counts": global_imports.most_common(),
    "global_import_relative_freq": sorted(
        [(m, f) for m, f in relative_imports.items()],
        key=lambda x: -x[1]
    )
}

report["_global"] = global_summary

# -----------------------------------------
# SAVE RESULTS
# -----------------------------------------

with open(RESULTS_DIR / "analysis.json", "w") as f:
    json.dump(report, f, indent=2)

print("\n▶ Done! Results saved to results/analysis.json")
print(f"Total source files scanned: {total_source_files}")
print(f"Global total LOC: {global_total_loc}")
print(f"Global total functions: {global_total_functions}")