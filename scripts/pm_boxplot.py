import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/specified_area_data/Regional_PM25_Full_Statistics.csv")

cols_to_convert = [
    "PM2.5_Mean",
    "PM2.5_Min",
    "PM2.5_Q1",
    "PM2.5_Median",
    "PM2.5_Q3",
    "PM2.5_Max",
]
for col in cols_to_convert:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df_plot = df.dropna(subset=cols_to_convert).reset_index(drop=True)

box_stats = []
for _, row in df_plot.iterrows():
    box_stats.append(
        {
            "label": row["Location_Name"],
            "mean": row["PM2.5_Mean"],
            "med": row["PM2.5_Median"],
            "q1": row["PM2.5_Q1"],
            "q3": row["PM2.5_Q3"],
            "whislo": row["PM2.5_Min"],
            "whishi": row["PM2.5_Max"],
            "fliers": [],
        }
    )

fig, ax = plt.subplots(figsize=(14, 7))

ax.bxp(
    box_stats,
    showmeans=True,
    meanline=False,
    boxprops=dict(color="navy", linewidth=1.5),
    whiskerprops=dict(color="navy", linestyle="-", linewidth=1.2),
    capprops=dict(color="navy", linewidth=1.5),
    medianprops=dict(color="crimson", linewidth=2.5),
    meanprops=dict(
        marker="o", markerfacecolor="navy", markeredgecolor="navy", markersize=6
    ),
)

Y_AXIS_LIMIT = 30
ax.set_ylim(0, Y_AXIS_LIMIT)

# Adding annotations
for i, row in df_plot.iterrows():
    max_val = row["PM2.5_Max"]
    ax.text(
        x=i + 1,
        y=Y_AXIS_LIMIT - 2,
        s=f"Max: {max_val:.1f}\nŚr.: {row["PM2.5_Mean"]}",
        ha="center",
        va="top",
        color="crimson",
        fontsize=9,
        fontweight="bold",
        bbox=dict(
            facecolor="white",
            alpha=0.9,
            edgecolor="white",
            boxstyle="round,pad=0.3",
        ),
    )


plt.xticks(rotation=45, ha="right")
plt.ylabel(r"PM 2.5 $[µg/m^3]$", fontsize=14)
# plt.xlabel("Lokalizacja pomiaru")
plt.title(
    "Wykres koncentracji PM 2.5 w zależności od miejsca na wyspie La Palma", fontsize=19
)
plt.grid(axis="y", linestyle="--", alpha=0.7)

plt.hlines(
    [5], xmin=1, xmax=10, linestyles="--", colors=["green"], label="WHO PM (rok)"
)
plt.hlines(
    [10], xmin=1, xmax=10, linestyles="--", colors=["brown"], label="EU PM (rok)"
)
plt.legend(loc=7)

plt.tight_layout()
plt.savefig("plots/PM25_Boxplot.png", dpi=300)
plt.show()
