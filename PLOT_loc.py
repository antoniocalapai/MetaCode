import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import squarify

# Seaborn style
sns.set_theme(style="whitegrid")

SAVE_PLOTS = 1
CLOSE_PLOTS = 1

BASE = Path("/Users/acalapai/Desktop/CodeAnalysis")
RESULTS_DIR = BASE / "results"
ANALYSIS_FILE = RESULTS_DIR / "analysis.json"

with open(ANALYSIS_FILE, "r") as f:
    report = json.load(f)

# ============================================================
# EXTRACT DATA
# ============================================================

# Languages
languages = report["_languages"]
lang_names = list(languages.keys())
lang_loc = [languages[l]["total_loc"] for l in lang_names]

# Repositories
repo_names = []
repo_loc = []
repo_num_files = []
file_loc_per_repo = {}

for repo_name, repo_data in report.items():
    if repo_name.startswith("_"):
        continue

    repo_names.append(repo_name)
    repo_loc.append(repo_data["total_lines"])
    repo_num_files.append(repo_data["num_source_files"])
    file_loc_per_repo[repo_name] = [f["loc"] for f in repo_data["files"].values()]

# Histogram data
all_locs = [loc for repo in file_loc_per_repo.values() for loc in repo]


# ============================================================
# ONE-PAGE DASHBOARD
# ============================================================

fig, axs = plt.subplots(3, 2, figsize=(14, 18))
fig.suptitle(
    "LOC Dashboard\nLOC = Lines of Code (including comments + blanks)",
    fontsize=18, weight="bold", y=0.98
)

# ------------------------------------------------------------
# (1) LOC per language
# ------------------------------------------------------------
ax = axs[0, 0]
sns.barplot(x=lang_names, y=lang_loc, ax=ax, palette="Blues_d")
ax.set_xticklabels(lang_names, rotation=45, ha="right")
ax.set_title("LOC per Language")
ax.set_ylabel("LOC")

# ------------------------------------------------------------
# (2) Pie chart
# ------------------------------------------------------------
ax = axs[0, 1]
ax.pie(lang_loc, labels=lang_names, autopct='%1.1f%%')
ax.set_title("Language LOC Share")

# ------------------------------------------------------------
# (3) LOC per repository
# ------------------------------------------------------------
ax = axs[1, 0]
sns.barplot(y=repo_names, x=repo_loc, ax=ax, palette="Greens_d")
ax.set_title("LOC per Repository")
ax.set_xlabel("LOC")

# ------------------------------------------------------------
# (4) Treemap
# ------------------------------------------------------------
ax = axs[1, 1]
sizes = [loc for loc in repo_loc if loc > 0]
labels = [repo_names[i] for i, loc in enumerate(repo_loc) if loc > 0]
if sizes:
    squarify.plot(sizes=sizes, label=labels, ax=ax, alpha=0.8)
ax.set_title("Repository LOC Treemap")
ax.axis("off")

# ------------------------------------------------------------
# (5) LOC vs number of files
# ------------------------------------------------------------
ax = axs[2, 0]
sns.scatterplot(x=repo_num_files, y=repo_loc, s=100, ax=ax)
for i, name in enumerate(repo_names):
    ax.text(repo_num_files[i], repo_loc[i], name)
ax.set_title("LOC vs Number of Files (per Repo)")
ax.set_xlabel("# Files")
ax.set_ylabel("LOC")

# ------------------------------------------------------------
# (6) LOC histogram
# ------------------------------------------------------------
ax = axs[2, 1]
sns.histplot(all_locs, bins=40, ax=ax, kde=False, color="purple")
ax.set_title("LOC Histogram (All Files)")
ax.set_xlabel("LOC")
ax.set_ylabel("File Count")

plt.tight_layout(rect=[0, 0, 1, 0.95])

# SAVE
out = RESULTS_DIR / "loc_dashboard.png"
if SAVE_PLOTS:
    plt.savefig(out)
    print("Saved", out)

if CLOSE_PLOTS:
    plt.close()
else:
    plt.show()