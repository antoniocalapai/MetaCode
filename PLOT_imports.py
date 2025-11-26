import json
from pathlib import Path
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter

# -----------------------------------------
# CONFIG
# -----------------------------------------
SAVE_PLOTS = 1        # Save plots to disk (1 = yes, 0 = no)
CLOSE_PLOTS = 1       # Close plots after saving (1 = yes, 0 = no)
MIN_IMPORT_COUNT = 10 # Only visualize imports used >= this number of times

# Paths
BASE = Path("/Users/acalapai/Desktop/CodeAnalysis")
RESULTS_DIR = BASE / "results"
ANALYSIS_FILE = RESULTS_DIR / "analysis.json"

# Load the analysis results
if not ANALYSIS_FILE.exists():
    raise FileNotFoundError(f"{ANALYSIS_FILE} not found. Run main.py first.")

with open(ANALYSIS_FILE, "r") as f:
    report = json.load(f)

# -----------------------------------------
# LOAD GLOBAL STATS (SAFE PARSING)
# -----------------------------------------

raw_abs = report["_global"]["global_import_counts"]
raw_rel = report["_global"]["global_import_relative_freq"]
total_source_files = report["_global"]["total_source_files"]

# Convert list entries into {module: count} format, safely
global_counts = {}
for item in raw_abs:
    if isinstance(item, list) and len(item) >= 2:
        module, count = item[0], item[1]
        global_counts[module] = count

# Convert relative entries into {module: relative_frequency}
relative_counts = {}
for item in raw_rel:
    if isinstance(item, list) and len(item) >= 2:
        module, rel = item[0], item[1]
        relative_counts[module] = rel

# -----------------------------------------
# FILTER imports by MIN_IMPORT_COUNT
# -----------------------------------------
filtered_abs = {mod: cnt for mod, cnt in global_counts.items()
                if cnt >= MIN_IMPORT_COUNT}

filtered_rel = {mod: relative_counts[mod] for mod in filtered_abs}

print(f"\nImports (absolute >= {MIN_IMPORT_COUNT}):")
for mod, cnt in sorted(filtered_abs.items(), key=lambda x: -x[1]):
    print(f"{mod}: abs={cnt}, rel={filtered_rel[mod]:.4f}")

if not filtered_abs:
    print("\nNo imports meet the threshold. Nothing to visualize.")
    exit(0)

# -----------------------------------------
# ABSOLUTE FREQUENCY BAR PLOT
# -----------------------------------------
modules = list(filtered_abs.keys())
abs_values = list(filtered_abs.values())

plt.figure(figsize=(12, 6))
plt.bar(modules, abs_values)
plt.xticks(rotation=45, ha='right')
plt.title(f"Absolute Import Frequency (≥ {MIN_IMPORT_COUNT} uses)")
plt.ylabel("Absolute Count")
plt.tight_layout()

if SAVE_PLOTS:
    path = RESULTS_DIR / "absolute_imports_barplot.png"
    plt.savefig(path)
    print(f"Saved absolute bar plot to {path}")

if CLOSE_PLOTS:
    plt.close()
else:
    plt.show()

# -----------------------------------------
# RELATIVE FREQUENCY BAR PLOT
# -----------------------------------------
rel_values = [filtered_rel[m] for m in modules]

plt.figure(figsize=(12, 6))
plt.bar(modules, rel_values)
plt.xticks(rotation=45, ha='right')
plt.title("Relative Import Frequency (per Python file)")
plt.ylabel("Relative Frequency")
plt.tight_layout()

if SAVE_PLOTS:
    path = RESULTS_DIR / "relative_imports_barplot.png"
    plt.savefig(path)
    print(f"Saved relative bar plot to {path}")

if CLOSE_PLOTS:
    plt.close()
else:
    plt.show()

# -----------------------------------------
# WORDCLOUD (ABSOLUTE)
# -----------------------------------------
wc_abs = WordCloud(
    width=1600, height=900, background_color="white"
).generate_from_frequencies(filtered_abs)

plt.figure(figsize=(16, 9))
plt.imshow(wc_abs, interpolation="bilinear")
plt.axis("off")
plt.title(f"Wordcloud (Absolute ≥ {MIN_IMPORT_COUNT})")

if SAVE_PLOTS:
    path = RESULTS_DIR / "absolute_imports_wordcloud.png"
    wc_abs.to_file(path)
    print(f"Saved absolute wordcloud to {path}")

if CLOSE_PLOTS:
    plt.close()
else:
    plt.show()

# -----------------------------------------
# WORDCLOUD (RELATIVE)
# -----------------------------------------
wc_rel = WordCloud(
    width=1600, height=900, background_color="white"
).generate_from_frequencies(filtered_rel)

plt.figure(figsize=(16, 9))
plt.imshow(wc_rel, interpolation="bilinear")
plt.axis("off")
plt.title("Wordcloud (Relative frequency)")

if SAVE_PLOTS:
    path = RESULTS_DIR / "relative_imports_wordcloud.png"
    wc_rel.to_file(path)
    print(f"Saved relative wordcloud to {path}")

if CLOSE_PLOTS:
    plt.close()
else:
    plt.show()