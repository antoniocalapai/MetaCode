import os
import json
from pathlib import Path
from collections import Counter, defaultdict
import ast
import re

# Try to import radon for complexity metrics
try:
    from radon.complexity import cc_visit
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False
    print("[WARNING] radon not installed. Cyclomatic complexity will be empty.")

# Root folders
REPOS_DIR = Path("/Users/acalapai/Library/Mobile Documents/com~apple~CloudDocs/GitHub")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------
# EXCLUDE DIRS
# -------------------------------------------------------
EXCLUDE_DIRS = {
    "__pycache__", ".git", ".vscode", ".idea",
    "venv", ".venv", "env", "build", "dist",
    "site-packages", "node_modules",
    ".ipynb_checkpoints"
}

# -------------------------------------------------------
# LANGUAGE MAP (3-FIELD: lang + category)
# -------------------------------------------------------
LANGUAGE_MAP = {
    # Code / programming
    ".py":   {"lang": "python",    "category": "code"},
    ".m":    {"lang": "matlab",    "category": "code"},
    ".js":   {"lang": "javascript","category": "code"},
    ".ts":   {"lang": "typescript","category": "code"},
    ".c":    {"lang": "c",         "category": "code"},
    ".cpp":  {"lang": "cpp",       "category": "code"},
    ".hpp":  {"lang": "cpp",       "category": "code"},
    ".cc":   {"lang": "cpp",       "category": "code"},

    # Scripts
    ".sh":   {"lang": "shell",     "category": "script"},
    ".bash": {"lang": "shell",     "category": "script"},
    ".zsh":  {"lang": "shell",     "category": "script"},

    # Web / markup
    ".html": {"lang": "html",      "category": "markup"},
    ".htm":  {"lang": "html",      "category": "markup"},
    ".css":  {"lang": "css",       "category": "style"},

    # Data / config
    ".json": {"lang": "json",      "category": "data"},
    ".yaml": {"lang": "yaml",      "category": "data"},
    ".yml":  {"lang": "yaml",      "category": "data"},
    ".csv":  {"lang": "csv",       "category": "data"},
    ".xls":  {"lang": "excel",     "category": "data"},
    ".xlsx": {"lang": "excel",     "category": "data"},
}

# -------------------------------------------------------
# PSEUDO COMPLEXITY
# -------------------------------------------------------
def compute_pseudo_complexity(text: str):
    keywords = ["if ", "elif ", "for ", "while ", "try:", "except", " and ", " or "]
    decision_points = sum(text.count(kw) for kw in keywords)
    dict_matches = re.findall(r"\{[^}]*for[^}]*\}", text, flags=re.DOTALL)
    return {
        "decision_points": decision_points + len(dict_matches),
        "dict_comprehensions": len(dict_matches),
    }

# -------------------------------------------------------
# PYTHON FUNCTION CALL EXTRACTION
# -------------------------------------------------------
def extract_function_calls(tree):
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.append(func.id)
            elif isinstance(func, ast.Attribute):
                parts = []
                curr = func
                while isinstance(curr, ast.Attribute):
                    parts.append(curr.attr)
                    curr = curr.value
                if isinstance(curr, ast.Name):
                    parts.append(curr.id)
                calls.append(".".join(reversed(parts)))
    return calls

# -------------------------------------------------------
# COMMENT COUNTER
# -------------------------------------------------------
def count_comments(text: str, language: str) -> int:
    lines = text.splitlines()
    num_comments = 0

    if language in ("python", "shell", "yaml"):
        return sum(1 for l in lines if l.strip().startswith("#"))

    if language == "matlab":
        return sum(1 for l in lines if l.strip().startswith("%"))

    if language in ("c", "cpp", "javascript", "typescript", "css"):
        in_block = False
        for l in lines:
            s = l.strip()
            if in_block:
                num_comments += 1
                if "*/" in s:
                    in_block = False
                continue
            if s.startswith("//"):
                num_comments += 1
            elif "/*" in s:
                num_comments += 1
                if "*/" not in s:
                    in_block = True

    if language in ("html", "xml"):
        in_block = False
        for l in lines:
            s = l.strip()
            if in_block:
                num_comments += 1
                if "-->" in s:
                    in_block = False
                continue
            if "<!--" in s:
                num_comments += 1
                if "-->" not in s:
                    in_block = True

    return num_comments

# -------------------------------------------------------
# FILE DISCOVERY
# -------------------------------------------------------
def get_source_files(repo_path: Path):
    files = []
    for p in repo_path.rglob("*"):
        if not p.is_file():
            continue

        if any(ex in p.parts for ex in EXCLUDE_DIRS):
            continue

        info = LANGUAGE_MAP.get(p.suffix.lower())
        if info:
            files.append((p, info["lang"], info["category"]))

    return files

# -------------------------------------------------------
# PYTHON ANALYSIS
# -------------------------------------------------------
def analyze_python_file(file_path: Path):
    try:
        text = file_path.read_text(errors="ignore")
    except Exception:
        m = empty_metrics()
        m["language"] = "python"
        return m

    lines = text.splitlines()
    loc = len(lines)
    num_blank = sum(1 for l in lines if not l.strip())
    num_comments = count_comments(text, "python")

    num_functions = 0
    function_names = []
    num_classes = 0
    imports_counter = Counter()
    function_calls = []

    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None

    if tree:
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

        function_calls = extract_function_calls(tree)

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

    return {
        "language": "python",
        "loc": loc,
        "num_comments": num_comments,
        "num_blank": num_blank,
        "num_functions": num_functions,
        "function_names": function_names,
        "num_classes": num_classes,
        "imports": dict(imports_counter),
        "complexity": {
            "avg_cc": avg_cc,
            "max_cc": max_cc,
            "total_cc": total_cc,
            "num_entities": num_entities,
            "cc_values": cc_values,
        },
        "pseudo_complexity": compute_pseudo_complexity(text),
        "function_calls": function_calls,
    }

# -------------------------------------------------------
# GENERIC ANALYSIS
# -------------------------------------------------------
def analyze_matlab_file(file_path: Path):
    try:
        text = file_path.read_text(errors="ignore")
    except Exception:
        m = empty_metrics()
        m["language"] = "matlab"
        return m

    lines = text.splitlines()
    return {
        "language": "matlab",
        "loc": len(lines),
        "num_comments": count_comments(text, "matlab"),
        "num_blank": sum(1 for l in lines if not l.strip()),
        "num_functions": 0,
        "function_names": [],
        "num_classes": 0,
        "imports": {},
        "complexity": {
            "avg_cc": 0.0, "max_cc": 0.0, "total_cc": 0.0,
            "num_entities": 0, "cc_values": []
        },
        "pseudo_complexity": compute_pseudo_complexity(text),
        "function_calls": [],
    }

def analyze_generic_file(file_path: Path, language: str):
    try:
        text = file_path.read_text(errors="ignore")
    except Exception:
        m = empty_metrics()
        m["language"] = language
        return m

    lines = text.splitlines()
    return {
        "language": language,
        "loc": len(lines),
        "num_comments": count_comments(text, language),
        "num_blank": sum(1 for l in lines if not l.strip()),
        "num_functions": 0,
        "function_names": [],
        "num_classes": 0,
        "imports": {},
        "complexity": {
            "avg_cc": 0.0, "max_cc": 0.0, "total_cc": 0.0,
            "num_entities": 0, "cc_values": []
        },
        "pseudo_complexity": compute_pseudo_complexity(text),
        "function_calls": [],
    }

# -------------------------------------------------------
# EMPTY METRICS TEMPLATE
# -------------------------------------------------------
def empty_metrics():
    return {
        "language": None,
        "loc": 0,
        "num_comments": 0,
        "num_blank": 0,
        "num_functions": 0,
        "function_names": [],
        "num_classes": 0,
        "imports": {},
        "complexity": {
            "avg_cc": 0.0, "max_cc": 0.0, "total_cc": 0.0,
            "num_entities": 0, "cc_values": []
        },
        "pseudo_complexity": {"decision_points": 0, "dict_comprehensions": 0},
        "function_calls": [],
    }

# -------------------------------------------------------
# MAIN ANALYSIS LOOP
# -------------------------------------------------------
report = {}
global_imports = Counter()

language_stats = defaultdict(lambda: {
    "total_loc": 0,
    "total_blank": 0,
    "total_comments": 0,
    "total_functions": 0,
    "total_pseudo_complexity": 0,
    "total_radon_complexity": 0,
    "num_files": 0,
})

category_stats = defaultdict(lambda: {
    "total_loc": 0,
    "total_comments": 0,
    "total_files": 0,
    "total_pseudo_complexity": 0,
})

total_source_files = 0
global_total_loc = 0
global_total_functions = 0

for repo in REPOS_DIR.iterdir():
    if not repo.is_dir():
        continue

    print(f"Analyzing repo: {repo.name}")

    files_with_lang = get_source_files(repo)
    total_source_files += len(files_with_lang)

    repo_total_loc = 0
    repo_total_functions = 0
    repo_import_counter = Counter()
    repo_data = {}

    for file_path, lang, category in files_with_lang:

        # Select correct analysis
        if lang == "python":
            metrics = analyze_python_file(file_path)
        elif lang == "matlab":
            metrics = analyze_matlab_file(file_path)
        else:
            metrics = analyze_generic_file(file_path, lang)

        relative = str(file_path.relative_to(repo))
        repo_data[relative] = metrics

        # Per repo
        repo_total_loc += metrics["loc"]
        repo_total_functions += metrics["num_functions"]
        repo_import_counter.update(metrics["imports"])

        # Global
        global_total_loc += metrics["loc"]
        global_total_functions += metrics["num_functions"]

        # Per-language stats
        language_stats[lang]["total_loc"] += metrics["loc"]
        language_stats[lang]["total_blank"] += metrics["num_blank"]
        language_stats[lang]["total_comments"] += metrics["num_comments"]
        language_stats[lang]["total_functions"] += metrics["num_functions"]
        language_stats[lang]["total_pseudo_complexity"] += metrics["pseudo_complexity"]["decision_points"]
        language_stats[lang]["num_files"] += 1

        # Category stats
        category_stats[category]["total_loc"] += metrics["loc"]
        category_stats[category]["total_comments"] += metrics["num_comments"]
        category_stats[category]["total_files"] += 1
        category_stats[category]["total_pseudo_complexity"] += metrics["pseudo_complexity"]["decision_points"]

        # Python only: radon + imports
        if lang == "python":
            language_stats[lang]["total_radon_complexity"] += metrics["complexity"]["total_cc"]
            global_imports.update(metrics["imports"])

    report[repo.name] = {
        "total_loc": repo_total_loc,
        "total_functions": repo_total_functions,
        "num_source_files": len(files_with_lang),
        "imports": repo_import_counter.most_common(),
        "files": repo_data,
    }

# -------------------------------------------------------
# GLOBAL SUMMARY
# -------------------------------------------------------
relative_imports = {
    m: c / total_source_files for m, c in global_imports.items()
} if total_source_files else {}

report["_global"] = {
    "total_source_files": total_source_files,
    "total_loc": global_total_loc,
    "total_functions": global_total_functions,
    "global_import_counts": global_imports.most_common(),
    "global_import_relative_freq": sorted(relative_imports.items(), key=lambda x: -x[1]),
}

# Store language & category summaries
report["_languages"] = dict(language_stats)
report["_categories"] = dict(category_stats)

# -------------------------------------------------------
# PYTHON SUMMARY
# -------------------------------------------------------
py = language_stats.get("python", None)

if py and py["total_loc"] > 0:
    comment_ratio = py["total_comments"] / py["total_loc"]
else:
    comment_ratio = 0.0

python_summary = {
    "python_loc": py["total_loc"] if py else 0,
    "python_files": py["num_files"] if py else 0,
    "python_functions": py["total_functions"] if py else 0,
    "avg_cyclomatic_complexity": (
        py["total_radon_complexity"] / py["num_files"]
        if py and py["num_files"] > 0 else 0
    ),
    "comment_ratio": comment_ratio,
}

with open(RESULTS_DIR / "python_summary.json", "w") as f:
    json.dump(python_summary, f, indent=2)

print("✓ python_summary.json written")

# -------------------------------------------------------
# SAVE FULL REPORT
# -------------------------------------------------------
with open(RESULTS_DIR / "analysis.json", "w") as f:
    json.dump(report, f, indent=2)

print("\nDone. Languages:", list(language_stats.keys()))
print("Categories:", list(category_stats.keys()))