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
# 2) Import counter
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
# 3) Style
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

# ============================================
# PYTHON PANEL MOCKUP
# ============================================

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
# plt.close()

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
# plt.close()

# ---- JSON summary for python panel ----
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

# ============================================
# 5) MATLAB SUMMARY (small panel backend)
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

# ============================================
# 6) LANGUAGES PANEL (non-Python)
# ============================================

languages = data.get("_languages", {})

panel_lang = {
    "languages": [],
    "total_non_python_loc": 0,
    "language_count": 0,
}

for lang, stats in languages.items():
    if lang == "python":
        continue

    loc = stats["total_loc"]
    comments = stats["total_comments"]
    files = stats["num_files"]
    pseudo = stats["total_pseudo_complexity"]

    if loc == 0:
        continue

    panel_lang["languages"].append({
        "language": lang,
        "loc": loc,
        "files": files,
        "comment_ratio": comments / loc if loc else 0,
        "pseudo_per_kloc": pseudo / (loc / 1000) if loc else 0,
    })

    panel_lang["total_non_python_loc"] += loc

panel_lang["language_count"] = len(panel_lang["languages"])
panel_lang["languages"].sort(key=lambda x: x["loc"], reverse=True)

with open(RESULTS / "languages_panel.json", "w") as f:
    json.dump(panel_lang, f, indent=2)

print("✓ languages_panel.json written")

# ======================================================
# 7) VISUALIZE LANGUAGES PANEL (mockup)
# ======================================================

LANG_PANEL = RESULTS / "languages_panel.json"
with open(LANG_PANEL, "r") as f:
    lp = json.load(f)

langs_list = lp["languages"]
names = [x["language"] for x in langs_list]
locs = [x["loc"] for x in langs_list]
comments = [x["comment_ratio"] for x in langs_list]

# Plot 1: LOC per language
fig, ax = plt.subplots(figsize=(10, 6))
colors = [(0.4 * c, 0.7, 1.0) for c in np.linspace(0.3, 1.0, len(names))]

ax.barh(names[::-1], locs[::-1], color=colors[::-1], edgecolor="none")
ax.set_title("LOC per Language", pad=14, fontsize=14)
ax.set_xlabel("Lines of Code")
ax.tick_params(axis="both", which="both", length=0)

plt.tight_layout()
plt.savefig(RESULTS / "languages_loc.png", dpi=300, transparent=True)
# plt.close()

# Plot 2: Comment ratio vs LOC
fig, ax = plt.subplots(figsize=(10, 6))

ax.scatter(locs, comments, s=180, alpha=0.85, c="#4FC3F7")
for i, name in enumerate(names):
    ax.text(locs[i] * 1.01, comments[i], name, fontsize=10, va="center")

ax.set_title("Comment Ratio per Language", pad=14, fontsize=14)
ax.set_xlabel("LOC")
ax.set_ylabel("Comment Ratio")
ax.tick_params(axis="both", which="both", length=0)

plt.tight_layout()
plt.savefig(RESULTS / "languages_comment_ratio.png", dpi=300, transparent=True)
# plt.close()

print("✓ languages_loc.png")
print("✓ languages_comment_ratio.png")

# ============================================
# 8) CATEGORIES / DATA PANEL (mockup)
# ============================================

categories = data.get("_categories", {})

panel_cat = {
    "categories": [],
    "total_loc": 0,
}

for cat, stats in categories.items():
    loc = stats["total_loc"]
    comments = stats["total_comments"]
    files = stats["total_files"]
    pseudo = stats["total_pseudo_complexity"]

    if loc == 0:
        continue

    panel_cat["categories"].append({
        "category": cat,
        "loc": loc,
        "files": files,
        "comment_ratio": comments / loc if loc else 0,
        "pseudo_per_kloc": pseudo / (loc / 1000) if loc else 0,
    })

    panel_cat["total_loc"] += loc

panel_cat["categories"].sort(key=lambda x: x["loc"], reverse=True)

with open(RESULTS / "categories_panel.json", "w") as f:
    json.dump(panel_cat, f, indent=2)

print("✓ categories_panel.json written")

# ---- Visual: LOC per category ----
cat_names = [c["category"] for c in panel_cat["categories"]]
cat_locs = [c["loc"] for c in panel_cat["categories"]]
cat_comments = [c["comment_ratio"] for c in panel_cat["categories"]]

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(cat_names, cat_locs, edgecolor="none")
ax.set_title("LOC per Category", pad=12, fontsize=13)
ax.set_ylabel("Lines of Code")
ax.tick_params(axis="both", which="both", length=0)

plt.tight_layout()
plt.savefig(RESULTS / "categories_loc.png", dpi=300, transparent=True)
# plt.close()

# ---- Visual: Comment ratio per category ----
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(cat_names, cat_comments, edgecolor="none")
ax.set_title("Comment Ratio per Category", pad=12, fontsize=13)
ax.set_ylabel("Comment Ratio")
ax.tick_params(axis="both", which="both", length=0)

plt.tight_layout()
plt.savefig(RESULTS / "categories_comment_ratio.png", dpi=300, transparent=True)
# plt.close()

print("✓ categories_loc.png")
print("✓ categories_comment_ratio.png")

# ============================================
# 9) STATS / METHODS PANEL (mockup wordcloud)
# ============================================

# Hard-coded frequencies for now: mockup for website card
stats_methods = {
    "GLM / regression": 12,
    "Bayesian modeling": 10,
    "GAM / GAMM": 8,
    "PCA / dimensionality reduction": 11,
    "Time-series analysis": 9,
    "Psychophysics modeling": 7,
    "CNNs / deep learning": 8,
    "Pose estimation": 7,
    "3D triangulation": 6,
    "Reverse correlation": 5,
    "Spike-triggered analysis": 5,
}

stats_panel = {
    "methods": [{"name": k, "weight": v} for k, v in stats_methods.items()],
    "num_methods": len(stats_methods),
}

with open(RESULTS / "stats_panel.json", "w") as f:
    json.dump(stats_panel, f, indent=2)

wc_stats = WordCloud(
    width=1600,
    height=900,
    background_color=None,
    mode="RGBA",
    colormap="viridis",
    contour_width=2,
    contour_color="white",
    prefer_horizontal=0.9,
    max_words=50,
    min_font_size=12,
    max_font_size=200,
)
wc_stats.generate_from_frequencies(stats_methods)

plt.figure(figsize=(14, 8))
plt.imshow(wc_stats, interpolation="bilinear")
plt.axis("off")
plt.tight_layout()
plt.savefig(RESULTS / "stats_methods_wordcloud.png", dpi=300, transparent=True)
# plt.close()

print("✓ stats_panel.json")
print("✓ stats_methods_wordcloud.png")