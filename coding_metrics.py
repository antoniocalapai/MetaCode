import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# =========================================================
# PATHS
# =========================================================
BASE = Path("/Users/acalapai/Desktop/CodeAnalysis")
RESULTS = BASE / "results"
ANALYSIS = RESULTS / "analysis.json"

PRIVATE_DATA = Path("/Users/acalapai/Desktop/CodeAnalysis/private_data")
REPOS_DIR = BASE / "repos"  # used for technique keyword scan

RESULTS.mkdir(exist_ok=True)

# =========================================================
# EXCLUSION LOGIC
# =========================================================
def should_exclude_file(path: Path) -> bool:
    """
    Exclude files if:
      - they sit inside a folder named '_exclude'
      - OR their filename starts with '_MV_'
    """
    parts = {p.lower() for p in path.parts}
    if "_exclude" in parts:
        return True
    if path.name.startswith("_MV_"):
        return True
    return False

# =========================================================
# LOAD analysis.json
# =========================================================
with open(ANALYSIS, "r") as f:
    data = json.load(f)

languages = data.get("_languages", {})
categories = data.get("_categories", {})

# =========================================================
# GLOBAL STYLE
# =========================================================
sns.set_theme(style="white")

plt.rcParams.update({
    "figure.facecolor": "#0a1324",
    "axes.facecolor":   "#0a1324",
    "axes.labelcolor":  "#E8ECF2",
    "xtick.color":       "#E8ECF2",
    "ytick.color":       "#E8ECF2",
    "text.color":        "#E8ECF2",
    "font.family":      "DejaVu Sans",
    "font.size":        12,
})

# =========================================================
# PANEL 1 — PYTHON vs EVERYTHING ELSE
# =========================================================
py = languages.get("python", {})

py_loc        = py.get("total_loc", 0)
py_comments   = py.get("total_comments", 0)
py_complexity = py.get("total_radon_complexity", 0)
py_files      = py.get("num_files", 0)

other_loc        = sum(v["total_loc"] for k, v in languages.items() if k != "python")
other_comments   = sum(v["total_comments"] for k, v in languages.items() if k != "python")
other_complexity = sum(v["total_pseudo_complexity"] for k, v in languages.items() if k != "python")
other_files      = sum(v["num_files"] for k, v in languages.items() if k != "python")

metric_labels = ["Lines of Code", "Comment Ratio (%)", "Complexity per KLOC", "File Count"]

python_vals = [
    py_loc,
    100 * py_comments / py_loc if py_loc else 0,
    py_complexity / (py_loc / 1000) if py_loc else 0,
    py_files,
]

other_vals = [
    other_loc,
    100 * other_comments / other_loc if other_loc else 0,
    other_complexity / (other_loc / 1000) if other_loc else 0,
    other_files,
]

fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(12, 10))
colors = {"python": "#4FC3F7", "other": "#81C784"}

for idx, ax in enumerate(axes):
    label = metric_labels[idx]
    v_py  = python_vals[idx]
    v_ot  = other_vals[idx]

    y_py = 0
    y_ot = 1

    ax.barh(y_py, v_py, height=0.35, color=colors["python"], label="Python" if idx == 0 else None)
    ax.barh(y_ot, v_ot, height=0.35, color=colors["other"],  label="Other"  if idx == 0 else None)

    ax.set_yticks([y_py, y_ot])
    ax.set_yticklabels(["Python", "Other"])

    max_val = max(v_py, v_ot, 1)
    ax.set_xlim(0, max_val * 1.15)

    ax.text(v_py, y_py, f"{v_py:.1f}", ha="left", va="center", color="white")
    ax.text(v_ot, y_ot, f"{v_ot:.1f}", ha="left", va="center", color="white")

    ax.set_title(label, loc="left", fontsize=11)
    sns.despine(ax=ax, left=True, bottom=True)
    ax.tick_params(axis="y", length=0)

axes[0].legend(
    loc="upper right",
    frameon=True,
    framealpha=0.3,
    facecolor="#0a1324",
    edgecolor="#E8ECF2"
)

fig.suptitle("CODEBASE — PYTHON vs OTHER LANGUAGES", x=0.02, y=0.995, ha="left", fontsize=14)
fig.tight_layout(rect=[0, 0, 1, 0.96])

fig.savefig(RESULTS / "panel1_codebase.png", dpi=300, transparent=True)

# =========================================================
# PANEL 2 — DATA FORMATS (DONUT) WITH EXCLUSIONS
# =========================================================
DATA_EXT = {".csv", ".json", ".yaml", ".yml", ".xls", ".xlsx"}

data_lines = {}

# ---------------------------------------------------------
# CONTRIBUTIONS FROM language_stats (analysis.json)
# ---------------------------------------------------------
lang_to_ext = {
    "csv": ".csv",
    "json": ".json",
    "yaml": ".yaml",
    "excel": ".xls",
}

for lang, st in languages.items():
    if lang in lang_to_ext:
        ext = lang_to_ext[lang]
        lines = st.get("total_loc", 0)
        if lines > 0:
            data_lines.setdefault(ext, 0)
            data_lines[ext] += lines

# ---------------------------------------------------------
# SUBTRACT :: MACHINE-VISION or EXCLUDED FILES in REPOS_DIR
# ---------------------------------------------------------
csv_excluded_lines = 0

for repo_name, repo_data in data.items():
    if repo_name.startswith("_"):
        continue

    for rel_path in repo_data["files"].keys():
        fp = REPOS_DIR / repo_name / rel_path

        if not fp.is_file():
            continue
        if fp.suffix.lower() != ".csv":
            continue
        if should_exclude_file(fp):
            try:
                with fp.open("r", errors="ignore") as f:
                    for _ in f:
                        csv_excluded_lines += 1
            except:
                pass

if ".csv" in data_lines:
    data_lines[".csv"] = max(0, data_lines[".csv"] - csv_excluded_lines)

# ---------------------------------------------------------
# ADD PRIVATE DATA (but exclude MV or _exclude)
# ---------------------------------------------------------
if PRIVATE_DATA.exists():
    for p in PRIVATE_DATA.rglob("*"):
        if should_exclude_file(p):
            continue
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext not in DATA_EXT:
            continue

        try:
            n_lines = sum(1 for _ in p.open("r", errors="ignore"))
        except:
            n_lines = 0

        data_lines.setdefault(ext, 0)
        data_lines[ext] += n_lines

# ---------------------------------------------------------
# DONUT PLOT
# ---------------------------------------------------------
if not data_lines:
    print("[INFO] No data formats found for Panel 2.")
else:
    labels = list(data_lines.keys())
    values = np.array([data_lines[k] for k in labels], dtype=float)

    total_lines = values.sum()
    percentages = values / total_lines * 100 if total_lines > 0 else np.zeros_like(values)

    fig, ax = plt.subplots(figsize=(9, 9))

    wedges, texts = ax.pie(
        percentages,
        labels=[f"{lbl} ({p:.1f}%)" for lbl, p in zip(labels, percentages)],
        colors=sns.color_palette("Set2", len(labels)),
        wedgeprops=dict(width=0.35, edgecolor="#0a1324"),
        textprops=dict(color="#E8ECF2"),
        startangle=90
    )

    centre_circle = plt.Circle((0, 0), 0.70, fc="#0a1324")
    fig.gca().add_artist(centre_circle)

    ax.text(
        0, 0,
        f"{int(total_lines):,} lines\n(total data points)",
        ha="center", va="center",
        fontsize=14, color="white"
    )

    ax.set_title("DATA FORMATS — Donut Plot (exclusions applied)", fontsize=15, loc="right")

    fig.tight_layout()
    fig.savefig(RESULTS / "panel2_dataformats.png", dpi=300, transparent=True)

    print("✓ panel2_dataformats.png updated")


# =========================================================
# PANEL 3 — TECHNIQUES
# =========================================================
TECHNIQUES = {
    "Machine learning / deep learning": {
        "imports": ["tensorflow", "keras", "torch", "sklearn", "xgboost", "lightgbm", "catboost"],
        "keywords": ["neural", "cnn", "rnn", "lstm", "transformer", "classifier", "regressor", "deep learning"],
    },
    "Computer vision / pose": {
        "imports": ["cv2", "mmpose", "mediapipe", "torchvision", "ultralytics", "yolov5", "yolov8"],
        "keywords": ["pose", "keypoint", "bounding box", "segmentation"],
    },
    "Statistics / GLM / inference": {
        "imports": ["statsmodels", "pymc", "scipy", "pingouin"],
        "keywords": ["glm", "regression", "anova", "bayesian"],
    },
    "Time-series / signal processing": {
        "imports": ["scipy.signal", "mne", "neurokit2"],
        "keywords": ["fft", "spectral", "filter", "bandpass"],
    },
    "Data visualization / plots": {
        "imports": ["matplotlib", "seaborn", "plotly"],
        "keywords": ["heatmap", "scatter", "boxplot"],
    },
}

for spec in TECHNIQUES.values():
    spec["keywords"] = [k.lower() for k in spec["keywords"]]

def classify_file(repo_name, rel_path, metrics):
    tech_found = set()
    imports = metrics.get("imports", {}) or {}

    text = ""
    try:
        fp = REPOS_DIR / repo_name / rel_path
        if fp.is_file() and not should_exclude_file(fp):
            text = fp.read_text(errors="ignore")
    except:
        pass

    t = text.lower()

    for tech, info in TECHNIQUES.items():
        imp_hit = any(im in imports for im in info["imports"])
        key_hit = any(kw in t for kw in info["keywords"])
        if imp_hit or key_hit:
            tech_found.add(tech)

    return tech_found

tech_counts = {k: 0 for k in TECHNIQUES.keys()}

for repo_name, repo_data in data.items():
    if repo_name.startswith("_"):
        continue

    for rel_path, metrics in repo_data["files"].items():
        fp = REPOS_DIR / repo_name / rel_path
        if should_exclude_file(fp):
            continue

        techs = classify_file(repo_name, rel_path, metrics)
        for t in techs:
            tech_counts[t] += 1

tech_counts = {k: v for k, v in tech_counts.items() if v > 0}

if tech_counts:
    tech_names = list(tech_counts.keys())
    vals = np.array([tech_counts[k] for k in tech_names])

    fig, ax = plt.subplots(figsize=(12, 7))
    y = np.arange(len(tech_names))

    bars = ax.barh(y, vals, color=sns.color_palette("Set2", len(tech_names)))
    ax.set_yticks(y)
    ax.set_yticklabels(tech_names)
    ax.invert_yaxis()

    for i, b in enumerate(bars):
        ax.text(
            b.get_width() + 0.1,
            b.get_y() + b.get_height()/2,
            str(vals[i]),
            ha="left", va="center", color="white"
        )

    ax.set_title("ANALYTICAL & COMPUTATIONAL TECHNIQUES", fontsize=14, loc="right")
    sns.despine(left=True, bottom=True)

    fig.tight_layout()
    fig.savefig(RESULTS / "panel3_techniques.png", dpi=300, transparent=True)

print("\n✓ All panels saved:")
print(" - panel1_codebase.png")
print(" - panel2_dataformats.png")
print(" - panel3_techniques.png")