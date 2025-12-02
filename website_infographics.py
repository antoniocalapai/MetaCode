import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

BASE = Path("/Users/acalapai/Desktop/CodeAnalysis")
RESULTS = BASE / "results"
ANALYSIS = RESULTS / "analysis.json"

with open(ANALYSIS, "r") as f:
    data = json.load(f)

import_counter = Counter()
cc_values = []
function_lengths = []
python_loc = 0
python_files = 0

# --- Dark theme ---
plt.style.use("default")
plt.rcParams.update({
    "figure.facecolor": (0, 0, 0, 0),
    "axes.facecolor":   (0, 0, 0, 0),
    "axes.edgecolor":   "#E8ECF2",
    "axes.labelcolor":  "#E8ECF2",
    "xtick.color":      "#E8ECF2",
    "ytick.color":      "#E8ECF2",
    "text.color":       "#E8ECF2",
    "font.family":      "DejaVu Sans",
    "font.size":        11,
    "axes.spines.top":  False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": False,
    "savefig.transparent": True,
})

# --- Gather metrics ---
for repo, repo_data in data.items():
    if repo.startswith("_"):
        continue

    for file, metrics in repo_data["files"].items():
        if metrics["language"] != "python":
            continue

        python_files += 1
        python_loc += metrics["loc"]
        import_counter.update(metrics["imports"])
        cc_values.extend(metrics["complexity"].get("cc_values", []))

        if metrics["num_functions"] > 0:
            function_lengths.append(metrics["loc"] / metrics["num_functions"])

# ================================
#  PLOT 1 — TOP 5 IMPORTS
# ================================
top5 = import_counter.most_common(5)
mods  = [m for m, _ in top5]
counts = [c for _, c in top5]

fig, ax = plt.subplots(figsize=(6, 2.8))
ax.barh(mods[::-1], counts[::-1], color="#4BA3FF", edgecolor="none")
ax.set_title("Top 5 Imports")
ax.tick_params(axis="both", length=0)
plt.tight_layout()
plt.savefig(RESULTS / "python_top5_imports.png", dpi=300, transparent=True)
plt.close()

# ================================
#  PLOT 2 — COMPLEXITY HISTOGRAM
# ================================
fig, ax = plt.subplots(figsize=(6, 2.8))
ax.hist(cc_values, bins=10, color="#00D5A1", alpha=0.9)
ax.set_title("Cyclomatic Complexity Distribution")
ax.tick_params(axis="both", length=0)
plt.tight_layout()
plt.savefig(RESULTS / "python_complexity_small.png", dpi=300, transparent=True)
plt.close()

# ================================
#  PLOT 3 — FUNCTION LENGTH DIST
# ================================
fig, ax = plt.subplots(figsize=(6, 2.8))
ax.hist(function_lengths, bins=10, color="#FFB547", alpha=0.9)
ax.set_title("Function Length Distribution")
ax.tick_params(axis="both", length=0)
plt.tight_layout()
plt.savefig(RESULTS / "python_functionlen_small.png", dpi=300, transparent=True)
plt.close()

print("✓ Infographic images generated!")