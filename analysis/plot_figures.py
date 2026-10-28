"""
Recreate Figures 1 and 2 of the thesis from the included analysis dataset.

Run from the analysis/ folder:
    python plot_figures.py

Reads:  ../data/merged_data.csv
Writes: ../figures/figure1_car_by_firm.png
        ../figures/figure2_car_sentiment_timeseries.png

Note: `car` in merged_data is already in percent (e.g. 17.2 = 17.2%).
"""
import os
import pandas as pd
import matplotlib.pyplot as plt

DATA = os.path.join("..", "data", "merged_data.csv")
OUT = os.path.join("..", "figures")

COMPANIES = {
    "Microsoft": {"ticker": "MSFT", "feature": "Microsoft 365 Copilot", "color": "#2E5090"},
    "Spotify": {"ticker": "SPOT", "feature": "AI DJ", "color": "#1DB954"},
    "Google": {"ticker": "GOOGL", "feature": "Gemini", "color": "#DB4437"},
    "Snapchat": {"ticker": "SNAP", "feature": "My AI", "color": "#FFA500"},
    "Adobe": {"ticker": "ADBE", "feature": "Firefly", "color": "#FF0000"},
}

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")

df = pd.read_csv(DATA).sort_values(["firm", "days_from_event"])
os.makedirs(OUT, exist_ok=True)

# --- Figure 1: CAR by firm -------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 7))
for name, info in COMPANIES.items():
    d = df[df["firm"] == name]
    ax.plot(d["days_from_event"], d["car"], marker="o", linewidth=2.5, markersize=4,
            label=f"{name} ({info['ticker']})", color=info["color"], alpha=0.85)
ax.axvline(0, color="black", linestyle="--", linewidth=2, alpha=0.7, label="Event Day")
ax.axhline(0, color="gray", linewidth=1, alpha=0.4)
ax.set_xlabel("Days from Event", fontsize=12, fontweight="bold")
ax.set_ylabel("Cumulative Abnormal Return (%)", fontsize=12, fontweight="bold")
ax.set_title("Cumulative Abnormal Returns Around AI Announcements", fontsize=14, fontweight="bold", pad=15)
ax.set_xlim(-15, 15)
ax.legend(loc="upper left", fontsize=10, frameon=True)
ax.grid(True, alpha=0.3, linestyle="--")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "figure1_car_by_firm.png"), dpi=200, bbox_inches="tight", facecolor="white")
plt.close()

# --- Figure 2: CAR and sentiment, one panel per firm -----------------------
fig, axes = plt.subplots(5, 1, figsize=(12, 15), sharex=True)
for ax, (name, info) in zip(axes, COMPANIES.items()):
    d = df[df["firm"] == name]
    ax.plot(d["days_from_event"], d["car"], color=info["color"], linewidth=2.5,
            marker="o", markersize=3, label="CAR (%)")
    ax2 = ax.twinx()
    ax2.plot(d["days_from_event"], d["daily_vader_mean"], color="gray", linewidth=2,
             linestyle="--", marker="s", markersize=3, alpha=0.75, label="Sentiment (VADER)")
    ax2.grid(False)
    ax.axvline(0, color="black", linestyle="--", linewidth=1.5, alpha=0.5)
    ax.axhline(0, color="gray", linewidth=0.5, alpha=0.4)
    ax.set_ylabel("CAR (%)", fontsize=10, color=info["color"], fontweight="bold")
    ax2.set_ylabel("Sentiment", fontsize=10, color="gray", fontweight="bold")
    ax.tick_params(axis="y", labelcolor=info["color"])
    ax2.tick_params(axis="y", labelcolor="gray")
    ax.set_title(f"{name}: {info['feature']}", fontsize=11, fontweight="bold", pad=8)
    ax.set_xlim(-15, 15)
    ax.grid(True, alpha=0.2, linestyle="--")
axes[-1].set_xlabel("Days from Event", fontsize=11)
plt.suptitle("Cumulative Abnormal Returns and Sentiment Around AI Announcements",
             fontsize=14, fontweight="bold", y=0.995)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "figure2_car_sentiment_timeseries.png"), dpi=200, bbox_inches="tight", facecolor="white")
plt.close()

print("Saved figures to", os.path.abspath(OUT))
