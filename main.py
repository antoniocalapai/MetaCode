import os
import json
from pathlib import Path
from collections import Counter
import ast

# Try to import radon for complexity metrics
try:
    from radon.complexity import cc_visit
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False
    print("[WARNING] radon not installed. Complexity metrics will be skipped.")

# Point to your existing folder of repositories
REPOS_DIR = Path("/Users/acalapai/Desktop/CodeAnalysis/repos")
RESULTS_DIR = Path("/Users/acalapai/Desktop/CodeAnalysis/results")

# Make sure the results directory exists
RESULTS_DIR.mkdir(exist_ok=True)

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
    """Analyze a Python file with LOC, comments, imports, AST, complexity."""
    try:
        text = file_path.read_text(errors="ignore")
    except Exception:
        return empty_metrics()

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

    # Complexity via radon
    complexity = {
        "avg_cc": 0.0,
        "max_cc": 0.0,
        "total_cc": 0.0,
        "num_entities": 0,
        "cc_values": []
    }

    if RADON_AVAILABLE:
        try:
            blocks = cc_visit(text)
            cc_vals = [b.complexity for b in blocks]
            complexity["cc_values"] = cc_vals
            complexity["num_entities"] = len(cc_vals)
            if cc_vals:
                complexity["total_cc"] = float(sum(cc_vals))
                complexity["max_cc"] = float(max(cc_vals))
                complexity["avg_cc"] = complexity["total_cc"] / len(cc_vals)
        except Exception:
            pass

    return {
        "loc": loc,
        "num_comments": num_comments,
        "num_blank": num_blank,
        "num_functions": num_functions,
        "function_names": function_names,
        "num_classes": num_classes,
        "imports": dict(imports_counter),
        "complexity": complexity,
    }

# -----------------------------------------
# MATLAB FILE ANALYSIS
# -----------------------------------------

def analyze_matlab_file(file_path: Path):
    """Basic metrics for MATLAB .m files: LOC, comments, blanks."""
    try:
        text = file_path.read_text(errors="ignore")
    except Exception:
        return empty_metrics()

    lines = text.splitlines()
    loc = len(lines)

    num_comments = sum(1 for l in lines if l.strip().startswith("%"))
    num_blank = sum(1 for l in lines if not l.strip())

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

        # MATLAB file
        if p.suffix == ".m":
            metrics = analyze_matlab_file(p)

        # Python file
        elif p.suffix == ".py":
            metrics = analyze_python_file(p)

        else:
            metrics = empty_metrics()

        rel_path = str(p.relative_to(repo))

        files_metrics[rel_path] = metrics

        # Repo aggregates
        repo_total_loc += metrics["loc"]
        repo_import_counter.update(metrics["imports"])
        repo_total_functions += metrics["num_functions"]

        # Global aggregates
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