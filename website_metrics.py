import json
from pathlib import Path
import matplotlib.pyplot as plt
from collections import Counter, defaultdict

BASE = Path("/Users/acalapai/Desktop/CodeAnalysis")
RESULTS = BASE / "results"
ANALYSIS = RESULTS / "analysis.json"

# -------------------------
# Load main report
# -------------------------
with open(ANALYSIS, "r") as f:
    data = json.load(f)

python_loc = 0
python_files = 0
python_functions = 0
import_counter = Counter()
function_lengths = []

cc_values = []

# -------------------------
# Iterate repos
# -------------------------
for repo, repo_data in data.items():
    if repo.startswith("_"):
        continue

    for file, metrics in repo_data["files"].items():
        if metrics["language"] != "python":
            continue

        python_files += 1
        python_loc += metrics["loc"]
        python_functions += metrics["num_functions"]
        import_counter.update(metrics["imports"])

        # Complexity values (radon)
        cc_values.extend(metrics["complexity"].get("cc_values", []))

        # Function length distribution
        # (approx. from LOC / num_functions; optional)
        if metrics["num_functions"] > 0:
            avg_len = metrics["loc"] / metrics["num_functions"]
            function_lengths.append(avg_len)

# -------------------------
# Make import frequency plot
# -------------------------
top_imports = import_counter.most_common(15)
modules = [m for m, _ in top_imports]
counts = [c for _, c in top_imports]

plt.figure(figsize=(10, 6))
plt.barh(modules[::-1], counts[::-1])
plt.title("Most Frequent Python Imports")
plt.xlabel("Count")
plt.tight_layout()
plt.savefig(RESULTS / "python_imports.png", dpi=300)
plt.close()

# -------------------------
# Save aggregated summary for HTML
# -------------------------
summary = {
    "python_loc": python_loc,
    "python_files": python_files,
    "python_functions": python_functions,
    "top_imports": top_imports,
    "avg_function_length": sum(function_lengths) / len(function_lengths) if function_lengths else 0,
    "avg_cyclomatic_complexity": sum(cc_values) / len(cc_values) if cc_values else 0,
}

with open(RESULTS / "python_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("✓ Generated python_imports.png and python_summary.json")