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
REPOS_DIR = Path("/Users/acalapai/Desktop/CodeAnalysis/repos")
RESULTS_DIR = Path("/Users/acalapai/Desktop/CodeAnalysis/results")
RESULTS_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------
# LANGUAGE MAP (ext -> language label)
# -------------------------------------------------------

LANGUAGE_MAP = {
    ".py": "python",
    ".m": "matlab",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".js": "javascript",
    ".ts": "typescript",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".c": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".xml": "xml",
}

# -------------------------------------------------------
# PSEUDO-COMPLEXITY (simple model + dict comprehensions)
# -------------------------------------------------------

def compute_pseudo_complexity(text: str):
    """Counts decision-making keywords + dictionary comprehensions."""
    keywords = [
        "if ", "elif ", "for ", "while ",
        "try:", "except", " and ", " or "
    ]
    decision_points = 0

    for kw in keywords:
        decision_points += text.count(kw)

    dict_pattern = r"\{[^}]*for[^}]*\}"
    dict_matches = re.findall(dict_pattern, text, flags=re.DOTALL)

    decision_points += len(dict_matches)

    return {
        "decision_points": decision_points,
        "dict_comprehensions": len(dict_matches),
    }

# -------------------------------------------------------
# FUNCTION CALL EXTRACTION (Python)
# -------------------------------------------------------

def extract_function_calls(tree):
    """
    Extract all function calls from Python AST, e.g.:
      cv2.imread -> "cv2.imread"
      os.path.join -> "os.path.join"
      myfunc -> "myfunc"
    """
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
# COMMENT COUNTING PER LANGUAGE
# -------------------------------------------------------

def count_comments(text: str, language: str) -> int:
    lines = text.splitlines()
    num_comments = 0

    # Hash-based comments (Python, shell, yaml)
    if language in ("python", "shell", "yaml"):
        for l in lines:
            if l.strip().startswith("#"):
                num_comments += 1

    # MATLAB (%)
    elif language == "matlab":
        for l in lines:
            if l.strip().startswith("%"):
                num_comments += 1

    # C / C++ / JS / TS / CSS : // and /* ... */
    elif language in ("c", "cpp", "c_header", "javascript", "typescript", "css"):
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
                if "*/" not in s or s.index("/*") < s.index("*/"):
                    in_block = True

    # HTML / XML / Markdown-style HTML comments: <!-- ... -->
    elif language in ("html", "xml", "markdown"):
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
                if "-->" not in s or s.index("<!--") < s.index("-->"):
                    in_block = True

    # JSON / text / svg / others: no structured comments counted
    else:
        num_comments = 0

    return num_comments

# -------------------------------------------------------
# FILE DISCOVERY
# -------------------------------------------------------

def get_source_files(repo_path: Path):
    """
    Return list of (path, language) for files whose extension
    is in LANGUAGE_MAP.
    """
    files = []
    for p in repo_path.rglob("*"):
        if not p.is_file():
            continue
        lang = LANGUAGE_MAP.get(p.suffix.lower())
        if lang:
            files.append((p, lang))
    return files

# -------------------------------------------------------
# PYTHON FILE ANALYSIS
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

        function_calls = extract_function_calls(tree)

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

    pseudo = compute_pseudo_complexity(text)

    return {
        "language": "python",
        "loc": loc,
        "num_comments": num_comments,
        "num_blank": num_blank,
        "num_functions": num_functions,
        "function_names": function_names,
        "num_classes": num_classes,
        "imports": dict(imports_counter),
        "complexity": complexity,
        "pseudo_complexity": pseudo,
        "function_calls": function_calls,
    }

# -------------------------------------------------------
# MATLAB FILE ANALYSIS
# -------------------------------------------------------

def analyze_matlab_file(file_path: Path):
    try:
        text = file_path.read_text(errors="ignore")
    except Exception:
        m = empty_metrics()
        m["language"] = "matlab"
        return m

    lines = text.splitlines()
    loc = len(lines)
    num_blank = sum(1 for l in lines if not l.strip())
    num_comments = count_comments(text, "matlab")
    pseudo = compute_pseudo_complexity(text)

    return {
        "language": "matlab",
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
        "function_calls": [],
    }

# -------------------------------------------------------
# GENERIC FILE ANALYSIS (non-Python/MATLAB)
# -------------------------------------------------------

def analyze_generic_file(file_path: Path, language: str):
    try:
        text = file_path.read_text(errors="ignore")
    except Exception:
        m = empty_metrics()
        m["language"] = language
        return m

    lines = text.splitlines()
    loc = len(lines)
    num_blank = sum(1 for l in lines if not l.strip())
    num_comments = count_comments(text, language)
    pseudo = compute_pseudo_complexity(text)

    return {
        "language": language,
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
        "function_calls": [],
    }

# -------------------------------------------------------
# DEFAULT METRICS
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
            "avg_cc": 0.0,
            "max_cc": 0.0,
            "total_cc": 0.0,
            "num_entities": 0,
            "cc_values": []
        },
        "pseudo_complexity": {
            "decision_points": 0,
            "dict_comprehensions": 0
        },
        "function_calls": [],
    }

# -------------------------------------------------------
# ANALYZE ALL REPOS
# -------------------------------------------------------

report = {}
global_imports = Counter()
global_total_loc = 0
global_total_functions = 0
total_source_files = 0

language_stats = defaultdict(lambda: {
    "total_loc": 0,
    "total_pseudo_complexity": 0,
    "total_radon_complexity": 0,
    "total_comments": 0,
    "total_blank": 0,
    "num_files": 0
})

for repo in REPOS_DIR.iterdir():
    if not repo.is_dir():
        continue

    print(f"Analyzing repository: {repo.name}")

    files_with_lang = get_source_files(repo)
    total_source_files += len(files_with_lang)

    repo_total_loc = 0
    repo_total_functions = 0
    repo_import_counter = Counter()

    files_metrics = {}

    for p, lang in files_with_lang:

        if lang == "python":
            metrics = analyze_python_file(p)
        elif lang == "matlab":
            metrics = analyze_matlab_file(p)
        else:
            metrics = analyze_generic_file(p, lang)

        rel_path = str(p.relative_to(repo))
        files_metrics[rel_path] = metrics

        # Repo stats
        repo_total_loc += metrics["loc"]
        repo_total_functions += metrics["num_functions"]
        repo_import_counter.update(metrics["imports"])

        # Global stats
        global_total_loc += metrics["loc"]
        global_total_functions += metrics["num_functions"]
        global_imports.update(metrics["imports"])

        # Language stats
        language_stats[lang]["total_loc"] += metrics["loc"]
        language_stats[lang]["total_pseudo_complexity"] += metrics["pseudo_complexity"]["decision_points"]
        language_stats[lang]["total_comments"] += metrics["num_comments"]
        language_stats[lang]["total_blank"] += metrics["num_blank"]
        language_stats[lang]["num_files"] += 1

        if lang == "python":
            language_stats[lang]["total_radon_complexity"] += metrics["complexity"]["total_cc"]

    report[repo.name] = {
        "total_lines": repo_total_loc,
        "num_source_files": len(files_with_lang),
        "total_functions": repo_total_functions,
        "avg_functions_per_file": (
            repo_total_functions / len(files_with_lang) if files_with_lang else 0.0
        ),
        "imports": repo_import_counter.most_common(),
        "files": files_metrics,
    }

# -------------------------------------------------------
# GLOBAL SUMMARY + LANGUAGE SUMMARY
# -------------------------------------------------------

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
report["_languages"] = {lang: stats for lang, stats in language_stats.items()}

# -------------------------------------------------------
# SAVE
# -------------------------------------------------------

with open(RESULTS_DIR / "analysis.json", "w") as f:
    json.dump(report, f, indent=2)

print("\n▶ Done! Results saved to results/analysis.json")
print(f"Total files scanned (tracked types): {total_source_files}")
print(f"Global total LOC: {global_total_loc}")
print(f"Global total functions: {global_total_functions}")
print("Languages found:", list(language_stats.keys()))