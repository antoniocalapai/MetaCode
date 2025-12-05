import json
from pathlib import Path
import matplotlib.pyplot as plt
from collections import Counter
import numpy as np
from wordcloud import WordCloud
import colorsys
from matplotlib import cm

BASE = Path("/Users/acalapai/Desktop/CodeAnalysis")
RESULTS = BASE / "results"
ANALYSIS = RESULTS / "analysis.json"

# ---------------------------------------------------------
# CUSTOM IMPORTS TO HIDE (your internal modules)
# ---------------------------------------------------------
CUSTOM_IMPORTS = {
    "utilities", "_utilities", "utils",
    "config", "_webserver", "run_webserver",
    "anc_mci_configuration", "_datalogger",
    "touchtraining_v04", "doublereward_v01",
    "dprime_2afc", "configurations",
    "touchtraining_v03", "catchgame",
    "thinkgame", "optionspage",
    "_webserver_v02", "games",
    "touchtraining_v05"
}

CUSTOM_IMPORTS = {c.lower() for c in CUSTOM_IMPORTS}

# ---------------------------------------------------------
# COLOR FIX FOR WORDCLOUD
# ---------------------------------------------------------
viridis = cm.get_cmap("viridis")

def no_dark_purple(word, font_size, position, orientation, random_state=None, **kwargs):
    for _ in range(20):
        t = np.random.rand()
        r, g, b, a = viridis(t)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if not (0.72 < h < 0.86 and v < 0.55):
            return f"rgb({int(r*255)},{int(g*255)},{int(b*255)})"
    r, g, b, a = viridis(0.6)
    return f"rgb({int(r*255)},{int(g*255)},{int(b*255)})"

# -------------------------
# Load analysis.json
# -------------------------
with open(ANALYSIS, "r") as f:
    data = json.load(f)

# ============================================
# PYTHON SUMMARY
# ============================================
py = data.get("_languages", {}).get("python", {})
python_loc = py.get("total_loc", 0)
python_files = py.get("num_files", 0)
python_functions = py.get("total_functions", 0)
comment_ratio = py.get("total_comments", 0) / python_loc if python_loc else 0

# ============================================
# COLLECT IMPORT COUNTS
# ============================================
import_counter = Counter()

for repo, repo_data in data.items():
    if repo.startswith("_"):
        continue

    for file, metrics in repo_data["files"].items():
        if metrics["language"] != "python":
            continue

        imports_raw = metrics.get("imports_third_party") or metrics.get("imports", {})

        cleaned = {
            mod.lower(): count
            for mod, count in imports_raw.items()
            if mod.lower() not in CUSTOM_IMPORTS
        }
        import_counter.update(cleaned)

# ============================================
# MATPLOTLIB STYLE
# ============================================
plt.style.use("default")
plt.rcParams.update({
    "figure.facecolor": (0, 0, 0, 0),
    "axes.facecolor":   (0, 0, 0, 0),
    "text.color":      "#E8ECF2",
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "savefig.transparent": True,
})

# ============================================
# GENERATE 10 WORDCLOUD VARIANTS
# ============================================

for i in range(1, 11):

    wc = WordCloud(
        width=1800,
        height=1000,
        background_color=None,
        mode="RGBA",
        colormap="viridis",
        contour_width=0,        # keep disabled to avoid RGBA errors
        prefer_horizontal=0.9,
        max_words=500,
        min_font_size=12,
        max_font_size=220,
        color_func=no_dark_purple,
        random_state=np.random.randint(0, 10_000_000)   # <-- KEY FOR VARIATION
    )

    wc.generate_from_frequencies(dict(import_counter))

    plt.figure(figsize=(14, 8))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout()

    out = RESULTS / f"python_imports_wordcloud_{i:02d}.png"
    plt.savefig(out, dpi=300, transparent=True)
    plt.close()

    print(f"✓ Saved {out}")

print("\n✓ All 10 wordclouds generated\n")