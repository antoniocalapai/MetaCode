import json
from pathlib import Path
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import defaultdict, Counter

# -----------------------------------------
# CONFIG
# -----------------------------------------
SAVE_PLOTS = 0
CLOSE_PLOTS = 0
MIN_COUNT_FILTER = 2     # For filtered wordcloud

BASE = Path("/Users/acalapai/Desktop/CodeAnalysis")
RESULTS_DIR = BASE / "results"
ANALYSIS_FILE = RESULTS_DIR / "analysis.json"

# -----------------------------------------
# LOAD DATA
# -----------------------------------------
with open(ANALYSIS_FILE, "r") as f:
    report = json.load(f)

# -----------------------------------------
# COLLECT FUNCTION NAMES
# -----------------------------------------
function_counts = Counter()
function_weighted_by_loc = Counter()
functions_per_file = []
loc_values = []
num_funcs_values = []
top_files = []

for repo_name, repo in report.items():
    if repo_name == "_global":
        continue

    for fpath, fdata in repo["files"].items():
        fnames = fdata["function_names"]
        loc = fdata["loc"]
        num_funcs = fdata["num_functions"]

        # global stats
        function_counts.update(fnames)

        for fn in fnames:
            function_weighted_by_loc[fn] += loc

        functions_per_file.append(num_funcs)
        loc_values.append(loc)
        num_funcs_values.append(num_funcs)

        top_files.append((repo_name, fpath, num_funcs))

# Sort top files by number of functions
top_files_sorted = sorted(top_files, key=lambda x: -x[2])[:10]

# -----------------------------------------
# WORDCLOUD HELPERS
# -----------------------------------------
def show_or_save(figpath=None):
    if SAVE_PLOTS and figpath:
        plt.savefig(figpath)
        print(f"Saved {figpath}")
    if CLOSE_PLOTS:
        plt.close()
    else:
        plt.show()

# -----------------------------------------
# 1. WORDCLOUD — SIMPLE
# -----------------------------------------
if function_counts:
    wc = WordCloud(width=1600, height=900, background_color="white")
    img = wc.generate_from_frequencies(function_counts)

    plt.figure(figsize=(16,9))
    plt.imshow(img, interpolation="bilinear")
    plt.axis("off")
    plt.title("Function Names — Simple Frequency")
    show_or_save(RESULTS_DIR / "functions_wordcloud_simple.png")
else:
    print("No function names found.")

# -----------------------------------------
# 2. WORDCLOUD — WEIGHTED BY OCCURRENCES (same as simple, but kept separate)
# -----------------------------------------
if function_counts:
    wc = WordCloud(width=1600, height=900, background_color="white")
    img = wc.generate_from_frequencies(function_counts)

    plt.figure(figsize=(16,9))
    plt.imshow(img, interpolation="bilinear")
    plt.axis("off")
    plt.title("Function Names — Weighted by Count")
    show_or_save(RESULTS_DIR / "functions_wordcloud_weighted.png")

# -----------------------------------------
# 3. WORDCLOUD — WEIGHTED BY FILE LOC
# -----------------------------------------
if function_weighted_by_loc:
    wc = WordCloud(width=1600, height=900, background_color="white")
    img = wc.generate_from_frequencies(function_weighted_by_loc)

    plt.figure(figsize=(16,9))
    plt.imshow(img, interpolation="bilinear")
    plt.axis("off")
    plt.title("Function Names — Weighted by LOC of Defining File")
    show_or_save(RESULTS_DIR / "functions_wordcloud_loc_weight.png")

# -----------------------------------------
# 4. WORDCLOUD — FILTERED (only ≥ MIN_COUNT_FILTER)
# -----------------------------------------
filtered = {fn:c for fn,c in function_counts.items() if c >= MIN_COUNT_FILTER}

if filtered:
    wc = WordCloud(width=1600, height=900, background_color="white")
    img = wc.generate_from_frequencies(filtered)

    plt.figure(figsize=(16,9))
    plt.imshow(img, interpolation="bilinear")
    plt.axis("off")
    plt.title(f"Function Names — Used ≥ {MIN_COUNT_FILTER} Times")
    show_or_save(RESULTS_DIR / "functions_wordcloud_filtered.png")

# -----------------------------------------
# 5. BAR PLOT — TOP 20 FUNCTION NAMES
# -----------------------------------------
top20 = function_counts.most_common(20)

if top20:
    labels = [t[0] for t in top20]
    values = [t[1] for t in top20]

    plt.figure(figsize=(12,6))
    plt.bar(labels, values)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Count")
    plt.title("Top 20 Function Names Across Repositories")
    plt.tight_layout()
    show_or_save(RESULTS_DIR / "functions_top20_barplot.png")

# -----------------------------------------
# 6. HISTOGRAM — FUNCTIONS PER FILE
# -----------------------------------------
plt.figure(figsize=(10,6))
plt.hist(functions_per_file, bins=30, edgecolor='black')
plt.xlabel("Number of Functions in File")
plt.ylabel("File Count")
plt.title("Distribution of Number of Functions per File")
plt.tight_layout()
show_or_save(RESULTS_DIR / "functions_per_file_histogram.png")

# -----------------------------------------
# 7. SCATTER — LOC vs NUMBER OF FUNCTIONS
# -----------------------------------------
plt.figure(figsize=(10,6))
plt.scatter(loc_values, num_funcs_values, s=40, alpha=0.7)
plt.xlabel("LOC")
plt.ylabel("Number of Functions")
plt.title("LOC vs Number of Functions per File")
plt.tight_layout()
show_or_save(RESULTS_DIR / "loc_vs_num_functions_scatter.png")

# -----------------------------------------
# 8. TOP 10 FILES WITH MOST FUNCTIONS
# -----------------------------------------
plt.figure(figsize=(12,6))
names = [f"{r}/{p}" for r,p,_ in top_files_sorted]
values = [n for _,_,n in top_files_sorted]

plt.bar(names, values)
plt.xticks(rotation=45, ha='right')
plt.ylabel("Function Count")
plt.title("Top 10 Files with Most Functions")
plt.tight_layout()
show_or_save(RESULTS_DIR / "top_10_function_rich_files.png")