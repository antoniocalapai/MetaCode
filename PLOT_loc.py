import json
from pathlib import Path
import matplotlib.pyplot as plt
import squarify
from collections import defaultdict

# -----------------------------------------
# CONFIG
# -----------------------------------------
SAVE_PLOTS = 0
CLOSE_PLOTS = 0

# -----------------------------------------
# PATHS
# -----------------------------------------
BASE = Path("/Users/acalapai/Desktop/CodeAnalysis")
RESULTS_DIR = BASE / "results"
ANALYSIS_FILE = RESULTS_DIR / "analysis.json"

# -----------------------------------------
# LOAD DATA
# -----------------------------------------
with open(ANALYSIS_FILE, "r") as f:
    report = json.load(f)

# -----------------------------------------
# EXTRACT LOC AND FILE-LEVEL METRICS
# -----------------------------------------
repo_names = []
repo_loc = []
repo_num_files = []
file_loc_per_repo = defaultdict(list)

for repo_name, repo_data in report.items():
    if repo_name == "_global":
        continue  # skip summary

    repo_names.append(repo_name)
    repo_loc.append(repo_data["total_lines"])
    repo_num_files.append(repo_data["num_source_files"])

    for fpath, fdata in repo_data["files"].items():
        file_loc_per_repo[repo_name].append(fdata["loc"])

# ----------------------------------------------------------
# 1. HORIZONTAL BAR PLOT
# ----------------------------------------------------------
plt.figure(figsize=(10, 6))
plt.barh(repo_names, repo_loc)
plt.xlabel("Lines of Code")
plt.title("LOC per Repository (horizontal)")
plt.tight_layout()

if SAVE_PLOTS:
    plt.savefig(RESULTS_DIR / "loc_horizontal.png")
if CLOSE_PLOTS:
    plt.close()
else:
    plt.show()

# ----------------------------------------------------------
# 2. PIE CHART
# ----------------------------------------------------------
plt.figure(figsize=(8, 8))
plt.pie(repo_loc, labels=repo_names, autopct='%1.1f%%')
plt.title("LOC share per repository")
plt.tight_layout()

if SAVE_PLOTS:
    plt.savefig(RESULTS_DIR / "loc_pie.png")
if CLOSE_PLOTS:
    plt.close()
else:
    plt.show()

# ----------------------------------------------------------
# 3. TREEMAP (with zero-size protection)
# ----------------------------------------------------------
treemap_sizes = []
treemap_labels = []

for name, loc in zip(repo_names, repo_loc):
    if loc > 0:  # squarify cannot handle zeroes
        treemap_sizes.append(loc)
        treemap_labels.append(name)

if treemap_sizes:
    plt.figure(figsize=(12, 8))
    squarify.plot(sizes=treemap_sizes, label=treemap_labels, alpha=0.8)
    plt.title("LOC Treemap")
    plt.axis("off")

    if SAVE_PLOTS:
        plt.savefig(RESULTS_DIR / "loc_treemap.png")
    if CLOSE_PLOTS:
        plt.close()
    else:
        plt.show()
else:
    print("No repositories with LOC > 0 — treemap skipped.")

# ----------------------------------------------------------
# 4. SCATTER: LOC vs NUMBER OF FILES
# ----------------------------------------------------------
plt.figure(figsize=(10, 6))
plt.scatter(repo_num_files, repo_loc, s=120)

for i, name in enumerate(repo_names):
    plt.text(repo_num_files[i], repo_loc[i], name)

plt.xlabel("Number of source files")
plt.ylabel("Total LOC")
plt.title("LOC vs Number of Files per Repository")
plt.tight_layout()

if SAVE_PLOTS:
    plt.savefig(RESULTS_DIR / "loc_vs_files.png")
if CLOSE_PLOTS:
    plt.close()
else:
    plt.show()

# ----------------------------------------------------------
# 5. BOXPLOT: FILE SIZE DISTRIBUTION PER REPO
# ----------------------------------------------------------
plt.figure(figsize=(12, 6))
plt.boxplot(file_loc_per_repo.values(), labels=file_loc_per_repo.keys(), vert=True)
plt.xticks(rotation=45, ha="right")
plt.ylabel("LOC per file")
plt.title("Per-file LOC distribution per repository")
plt.tight_layout()

if SAVE_PLOTS:
    plt.savefig(RESULTS_DIR / "loc_boxplot.png")
if CLOSE_PLOTS:
    plt.close()
else:
    plt.show()

# ----------------------------------------------------------
# 6. HISTOGRAM: ALL FILE LOC DISTRIBUTION
# ----------------------------------------------------------
all_locs = [loc for repos in file_loc_per_repo.values() for loc in repos]

plt.figure(figsize=(10, 6))
plt.hist(all_locs, bins=40)
plt.xlabel("LOC")
plt.ylabel("File count")
plt.title("Histogram of LOC across all files")
plt.tight_layout()

if SAVE_PLOTS:
    plt.savefig(RESULTS_DIR / "loc_histogram.png")
if CLOSE_PLOTS:
    plt.close()
else:
    plt.show()