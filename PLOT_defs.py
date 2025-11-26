import json
from pathlib import Path
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter

# ---------------- CONFIG ----------------
SAVE_PLOTS = 0
CLOSE_PLOTS = 0
MIN_COUNT_FILTER = 2

BASE = Path("/Users/acalapai/Desktop/CodeAnalysis")
RESULTS_DIR = BASE / "results"
ANALYSIS_FILE = RESULTS_DIR / "analysis.json"

# ------------ LOAD DATA -----------------
with open(ANALYSIS_FILE, "r") as f:
    report = json.load(f)

function_counts = Counter()
file_func_counts = []
file_locs = []
file_num_funcs = []

for repo_name, repo in report.items():
    if repo_name == "_global":
        continue

    for fpath, fdata in repo["files"].items():
        fnames = fdata["function_names"]
        loc = fdata["loc"]
        nf = fdata["num_functions"]

        function_counts.update(fnames)
        file_num_funcs.append(nf)
        file_locs.append(loc)

# ------------- Helper --------------------
def show_or_save(path=None):
    if SAVE_PLOTS and path:
        plt.savefig(path)
        print(f"Saved {path}")
    if CLOSE_PLOTS:
        plt.close()
    else:
        plt.show()

# -------- 1. Wordcloud (All) -------------
if function_counts:
    wc = WordCloud(width=1600, height=900, background_color="white")
    img = wc.generate_from_frequencies(function_counts)

    plt.figure(figsize=(16,9))
    plt.imshow(img, interpolation="bilinear")
    plt.axis("off")
    plt.title("Defined Function Names — All")
    show_or_save(RESULTS_DIR / "defined_functions_wordcloud_all.png")

# ---- 2. Wordcloud (Filtered ≥ MIN) -----
filtered = {fn:c for fn,c in function_counts.items() if c >= MIN_COUNT_FILTER}

if filtered:
    wc = WordCloud(width=1600, height=900, background_color="white")
    img = wc.generate_from_frequencies(filtered)

    plt.figure(figsize=(16,9))
    plt.imshow(img, interpolation="bilinear")
    plt.axis("off")
    plt.title(f"Defined Functions — Used ≥ {MIN_COUNT_FILTER} Times")
    show_or_save(RESULTS_DIR / "defined_functions_wordcloud_filtered.png")

# ---- 3. Bar plot (Top 20 defined) -------
top20 = function_counts.most_common(20)
if top20:
    labels = [t[0] for t in top20]
    counts = [t[1] for t in top20]

    plt.figure(figsize=(12,6))
    plt.bar(labels, counts)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Count")
    plt.title("Top 20 Defined Functions")
    plt.tight_layout()
    show_or_save(RESULTS_DIR / "defined_functions_top20.png")

# ---- 4. Histogram — functions per file --
plt.figure(figsize=(10,6))
plt.hist(file_num_funcs, bins=20, edgecolor='black')
plt.xlabel("Number of defined functions")
plt.ylabel("File count")
plt.title("Distribution of Defined Functions per File")
plt.tight_layout()
show_or_save(RESULTS_DIR / "defined_functions_histogram.png")

# ---- 5. Scatter — LOC vs num functions ---
plt.figure(figsize=(10,6))
plt.scatter(file_locs, file_num_funcs, s=40, alpha=0.7)
plt.xlabel("LOC")
plt.ylabel("# Functions")
plt.title("LOC vs # Defined Functions")
plt.tight_layout()
show_or_save(RESULTS_DIR / "defined_functions_scatter.png")