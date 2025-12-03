import json
from pathlib import Path
import matplotlib.pyplot as plt
from collections import Counter
import numpy as np
from wordcloud import WordCloud

BASE = Path("/Users/acalapai/Desktop/CodeAnalysis")
RESULTS = BASE / "results"
ANALYSIS = RESULTS / "analysis.json"

# -------------------------
# Load big analysis.json
# -------------------------
with open(ANALYSIS, "r") as f:
    data = json.load(f)

# ============================================
# 1) PYTHON SUMMARY (from _languages block)
# ============================================

if "_languages" in data and "python" in data["_languages"]:
    py = data["_languages"]["python"]
else:
    py = None

if py:
    python_loc = py["total_loc"]
    python_files = py["num_files"]
    python_functions = py["total_functions"]
    comment_ratio = py["total_comments"] / python_loc if python_loc else 0
else:
    python_loc = python_files = python_functions = 0
    comment_ratio = 0.0

# ============================================
# 2) Import counter still needs per-file scanning
# ============================================

import_counter = Counter()
cc_values = []
function_lengths = []

for repo, repo_data in data.items():
    if repo.startswith("_"):
        continue

    for file, metrics in repo_data["files"].items():
        if metrics["language"] != "python":
            continue

        import_counter.update(metrics["imports"])
        cc_values.extend(metrics["complexity"].get("cc_values", []))

        if metrics["num_functions"] > 0:
            avg_len = metrics["loc"] / metrics["num_functions"]
            function_lengths.append(avg_len)

# ============================================
# 3) Plots
# ============================================

plt.style.use("default")
plt.rcParams.update({
    "figure.facecolor": (0, 0, 0, 0),
    "axes.facecolor":   (0, 0, 0, 0),
    "axes.edgecolor": "#E8ECF2",
    "axes.labelcolor": "#E8ECF2",
    "xtick.color":     "#E8ECF2",
    "ytick.color":     "#E8ECF2",
    "text.color":      "#E8ECF2",
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": False,
    "axes.grid": False,
    "savefig.transparent": True,
})

# ---- Bar chart: imports ----
top_imports = import_counter.most_common(15)
modules = [m for m, _ in top_imports]
counts = [c for _, c in top_imports]

fig, ax = plt.subplots(figsize=(10, 6))
colors = [(0.4 * c, 0.7, 1.0) for c in np.linspace(0.3, 1.0, len(modules))]

ax.barh(modules[::-1], counts[::-1], color=colors[::-1], edgecolor="none")
ax.set_title("Most Frequent Python Imports", pad=14, fontsize=14)
ax.set_xlabel("Count")
ax.tick_params(axis="both", which="both", length=0)

plt.tight_layout()
plt.savefig(RESULTS / "python_imports.png", dpi=300, transparent=True)
plt.close()

# ---- Wordcloud ----
wc = WordCloud(
    width=1800,
    height=1000,
    background_color=None,
    mode="RGBA",
    colormap="viridis",
    contour_width=2,
    contour_color="white",
    prefer_horizontal=0.9,
    max_words=50,
    min_font_size=12,
    max_font_size=220,
)
wc.generate_from_frequencies(dict(import_counter))

plt.figure(figsize=(14, 8))
plt.imshow(wc, interpolation="bilinear")
plt.axis("off")
plt.tight_layout()
plt.savefig(RESULTS / "python_imports_wordcloud.png", dpi=300, transparent=True)
plt.close()

# ============================================
# 4) Save python_summary.json
# ============================================

defs_per_file = python_functions / python_files if python_files else 0
defs_per_kloc = python_functions / (python_loc / 1000) if python_loc else 0

summary = {
    "python_loc": python_loc,
    "python_files": python_files,
    "python_functions": python_functions,
    "defs_per_file": defs_per_file,
    "defs_per_kloc": defs_per_kloc,
    "top_imports": top_imports,
    "avg_function_length": (
        sum(function_lengths) / len(function_lengths) if function_lengths else 0
    ),
    "avg_cyclomatic_complexity": (
        sum(cc_values) / len(cc_values) if cc_values else 0
    ),
    "comment_ratio": comment_ratio,
}

with open(RESULTS / "python_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("✓ python_summary.json updated")
print("Python LOC =", python_loc)
print("Files =", python_files)
print("Functions =", python_functions)
print("Defs per file =", defs_per_file)
print("Defs per KLOC =", defs_per_kloc)
print("Comment ratio =", comment_ratio)

# ============================================
# 5) MATLAB SUMMARY — CORRECTED
# ============================================

if "_languages" in data and "matlab" in data["_languages"]:
    m = data["_languages"]["matlab"]

    matlab_summary = {
        "matlab_loc": m["total_loc"],
        "matlab_files": m["num_files"],
        "matlab_functions": m["total_functions"],
        "comment_ratio": (
            m["total_comments"] / m["total_loc"] if m["total_loc"] else 0.0
        ),
        "pseudo_complexity": m["total_pseudo_complexity"],
    }

else:
    matlab_summary = {
        "matlab_loc": 0,
        "matlab_files": 0,
        "matlab_functions": 0,
        "comment_ratio": 0.0,
        "pseudo_complexity": 0,
    }

with open(RESULTS / "matlab_summary.json", "w") as f:
    json.dump(matlab_summary, f, indent=2)

print("✓ matlab_summary.json written")