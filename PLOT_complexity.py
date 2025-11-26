import json
from pathlib import Path
import matplotlib.pyplot as plt
import radon

# -----------------------------------------
# CONFIG
# -----------------------------------------
SAVE_PLOTS = 1
CLOSE_PLOTS = 1

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
# EXTRACT COMPLEXITY DATA
# -----------------------------------------
all_cc_values = []        # all function complexities across all repos
repo_avg_complexity = []  # avg file complexity per repo
repo_max_complexity = []  # max file complexity per repo
repo_names = []

for repo_name, repo_data in report.items():
    if repo_name == "_global":
        continue

    repo_names.append(repo_name)

    per_file_avg = []
    per_file_max = []

    for fpath, fdata in repo_data["files"].items():
        cc = fdata["complexity"]["cc_values"]  # list of function CC values

        if cc:
            all_cc_values.extend(cc)
            per_file_avg.append(fdata["complexity"]["avg_cc"])
            per_file_max.append(fdata["complexity"]["max_cc"])

    # Repo-level aggregates
    avg_cplx = sum(per_file_avg) / len(per_file_avg) if per_file_avg else 0
    max_cplx = max(per_file_max) if per_file_max else 0

    repo_avg_complexity.append(avg_cplx)
    repo_max_complexity.append(max_cplx)

# ----------------------------------------------------------
# 1. HISTOGRAM OF ALL COMPLEXITY VALUES
# ----------------------------------------------------------
if all_cc_values:
    plt.figure(figsize=(10, 6))
    plt.hist(all_cc_values, bins=30, edgecolor='black')
    plt.xlabel("Cyclomatic Complexity")
    plt.ylabel("Number of Functions")
    plt.title("Cyclomatic Complexity Distribution (all repos)")
    plt.tight_layout()

    if SAVE_PLOTS:
        plt.savefig(RESULTS_DIR / "complexity_histogram.png")
    if CLOSE_PLOTS:
        plt.close()
    else:
        plt.show()
else:
    print("No complexity values found (likely no Python functions).")

# ----------------------------------------------------------
# 2. BAR PLOT: MAX COMPLEXITY PER REPO
# ----------------------------------------------------------
plt.figure(figsize=(12, 6))
plt.bar(repo_names, repo_max_complexity)
plt.xticks(rotation=45, ha='right')
plt.ylabel("Max Complexity")
plt.title("Maximum Cyclomatic Complexity per Repository")
plt.tight_layout()

if SAVE_PLOTS:
    plt.savefig(RESULTS_DIR / "complexity_max_per_repo.png")
if CLOSE_PLOTS:
    plt.close()
else:
    plt.show()

# ----------------------------------------------------------
# 3. BAR PLOT: AVERAGE COMPLEXITY PER REPO
# ----------------------------------------------------------
plt.figure(figsize=(12, 6))
plt.bar(repo_names, repo_avg_complexity)
plt.xticks(rotation=45, ha='right')
plt.ylabel("Average Complexity")
plt.title("Average Cyclomatic Complexity per Repository")
plt.tight_layout()

if SAVE_PLOTS:
    plt.savefig(RESULTS_DIR / "complexity_avg_per_repo.png")
if CLOSE_PLOTS:
    plt.close()
else:
    plt.show()