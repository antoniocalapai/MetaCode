import json
from pathlib import Path
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter, defaultdict

# ---------------- CONFIG ----------------
SAVE_PLOTS = 0
CLOSE_PLOTS = 0
TOP_N = 50           # top N function calls to plot
FILTER_PACKAGES = ["torch", "cv2", "numpy", "PIL", "sklearn"]

BASE = Path("/Users/acalapai/Desktop/CodeAnalysis")
RESULTS_DIR = BASE / "results"
ANALYSIS_FILE = RESULTS_DIR / "analysis.json"

# ------------ LOAD DATA -----------------
with open(ANALYSIS_FILE, "r") as f:
    report = json.load(f)

call_counts = Counter()
file_call_counts = []
file_locs = []

package_specific = {pkg: Counter() for pkg in FILTER_PACKAGES}

# -------- Extract function call data -----
for repo_name, repo in report.items():
    if repo_name == "_global":
        continue

    for fpath, fdata in repo["files"].items():
        calls = fdata["function_calls"]
        loc = fdata["loc"]

        call_counts.update(calls)
        file_call_counts.append(len(calls))
        file_locs.append(loc)

        # package-specific classification
        for c in calls:
            for pkg in FILTER_PACKAGES:
                if c.startswith(pkg + "."):
                    package_specific[pkg][c] += 1

# ------------- Helper --------------------
def show_or_save(path=None):
    if SAVE_PLOTS and path:
        plt.savefig(path)
        print(f"Saved {path}")
    if CLOSE_PLOTS:
        plt.close()
    else:
        plt.show()

# -------- 1. Wordcloud — all function calls
if call_counts:
    wc = WordCloud(width=1600, height=900, background_color="white")
    img = wc.generate_from_frequencies(call_counts)

    plt.figure(figsize=(16,9))
    plt.imshow(img, interpolation="bilinear")
    plt.axis("off")
    plt.title("All Called Functions (full codebase)")
    show_or_save(RESULTS_DIR / "called_functions_wordcloud_all.png")

# -------- 2. Bar plot — top N calls -------
topN = call_counts.most_common(TOP_N)
if topN:
    labels = [t[0] for t in topN]
    counts = [t[1] for t in topN]

    plt.figure(figsize=(15,7))
    plt.bar(labels, counts)
    plt.xticks(rotation=90)
    plt.ylabel("Call Count")
    plt.title(f"Top {TOP_N} Called Functions")
    plt.tight_layout()
    show_or_save(RESULTS_DIR / "called_functions_topN.png")

# -------- 3. Histogram: calls per file ----
plt.figure(figsize=(10,6))
plt.hist(file_call_counts, bins=30, edgecolor='black')
plt.xlabel("# Calls per File")
plt.ylabel("File count")
plt.title("Distribution of Function Calls per File")
plt.tight_layout()
show_or_save(RESULTS_DIR / "calls_per_file_hist.png")

# -------- 4. Scatter: LOC vs number of calls
plt.figure(figsize=(10,6))
plt.scatter(file_locs, file_call_counts, s=40, alpha=0.7)
plt.xlabel("LOC")
plt.ylabel("# Calls")
plt.title("LOC vs Function Calls per File")
plt.tight_layout()
show_or_save(RESULTS_DIR / "loc_vs_calls_scatter.png")

# -------- 5. Package-specific analysis ----
for pkg, counter in package_specific.items():
    if not counter:
        continue

    wc = WordCloud(width=1600, height=900, background_color="white")
    img = wc.generate_from_frequencies(counter)

    plt.figure(figsize=(16,9))
    plt.imshow(img, interpolation="bilinear")
    plt.axis("off")
    plt.title(f"{pkg} — Called Functions")
    show_or_save(RESULTS_DIR / f"called_functions_{pkg}.png")