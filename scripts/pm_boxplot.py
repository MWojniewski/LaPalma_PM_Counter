import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

df = pd.read_csv("data/specified_area_data/Regional_PM25_Full_Statistics.csv")

# opcje
TITLE_ON    = False
TEXT_LABEL  = False
SAVE_IMG    = False
EXTRA_LABELS= False
HANDLE_MEAN = True

Y_AXIS_MAX = 20.0
Y_AXIS_MIN = 0.0
FONTSIZE   = 13

WHO_PM  = 5
EU_PM   = 10


font = {'family' : 'Helvetica',
        'size'   : 12}

matplotlib.rc('font', **font)

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

box_stats   = []
extra_stats = []
for i, row in df_plot.iterrows():
    if TEXT_LABEL: 
        label= row["Location_Name"]
    else: 
        label= f"{i+1:d}."

    mean_corr = row["PM2.5_Mean"]
    if HANDLE_MEAN:
        if row["PM2.5_Mean"]>Y_AXIS_MAX: 
            mean_corr = Y_AXIS_MAX
            extra_stats.append(
                {
                    "mean": f"{row["PM2.5_Mean"]:.1f}",
                }
            )
        else: 
            extra_stats.append(
                {
                    "mean": "",
                }
            )
    
    box_stats.append(
        {
            "label": label,
            "mean": mean_corr,
            "med": row["PM2.5_Median"],
            "q1": row["PM2.5_Q1"],
            "q3": row["PM2.5_Q3"],
            "whislo": row["PM2.5_Min"],
            "whishi": row["PM2.5_Max"],
            "fliers": [],
        }
    )

fig, ax = plt.subplots(figsize=(8,4))

bp = ax.bxp(
    box_stats,
    showmeans=True,
    showcaps = False,
    meanline=False,
    boxprops=dict(color="navy", linewidth=1.5),
    whiskerprops=dict(color="navy", linestyle="-", linewidth=0),
    capprops=dict(color="navy", linewidth=1.5),
    medianprops=dict(color="crimson", linewidth=2.5),
    meanprops=dict(
        marker="x", markerfacecolor="crimson", markeredgecolor="crimson", markersize=10
    ),
)

ax.set_ylim(Y_AXIS_MIN, Y_AXIS_MAX)
ax.set_xlim(0.5, 9.5)

# Adding annotations
if EXTRA_LABELS:
    for i, row in df_plot.iterrows():
        max_val = row["PM2.5_Max"]
        ax.text(
            x=i + 1,
            y=Y_AXIS_MAX - 2,
            s=f"{max_val:.1f}\n{row["PM2.5_Mean"]}",
            # s=f"Max: {max_val:.1f}\nŚr.: {row["PM2.5_Mean"]}",
            ha="left",
            va="top",
            color="crimson",
            fontsize=FONTSIZE,
            fontweight="bold",
            bbox=dict(
                facecolor="white",
                alpha=0.9,
                edgecolor="white",
                boxstyle="round,pad=0.3",
            ),
        )
else:
    for i, entry in enumerate(extra_stats):
        ax.text(
            x=i + 1,
            y=Y_AXIS_MAX - 1,
            s=entry["mean"],
            # s=f"Max: {max_val:.1f}\nŚr.: {row["PM2.5_Mean"]}",
            ha="center",
            va="top",
            color="crimson",
            fontsize=FONTSIZE,
            bbox=dict(
                facecolor="white",
                alpha=0.9,
                edgecolor="white",
                boxstyle="round,pad=0.3",
            ),
        )


if TEXT_LABEL: 
    plt.xticks(rotation=45, ha="right")
# else:
    # plt.xticks(ha="left")
plt.xticks(fontsize=FONTSIZE)
plt.yticks(fontsize=FONTSIZE)

plt.ylabel(r"PM 2.5 [µg/m$^3$]", fontsize=FONTSIZE)
# plt.xlabel("Lokalizacja pomiaru")
if TITLE_ON: plt.title(
    "Wykres koncentracji PM 2.5 w zależności od miejsca na wyspie La Palma", fontsize=19
)
plt.grid(axis="y", linestyle="--", alpha=0.7)

plt.hlines(
    [WHO_PM], xmin=0.5, xmax=9.5, linestyles="-.", colors=["green"], label="WHO PM (rok)"
)
ax.text(
            x=0.5+.1,
            y=WHO_PM+.5,
            s=f"WHO (rok): {WHO_PM:.1f}",
            ha="left",
            va="bottom",
            color="green",
            fontsize=FONTSIZE-2,
)
plt.hlines(
    [EU_PM], xmin=0.5, xmax=9.5, linestyles="-.", colors=["orange"], label="EU PM (rok)"
)
ax.text(
            x=0.5+.1,
            y=EU_PM+.5,
            s=f"EU (rok): {EU_PM:.1f}",
            ha="left",
            va="bottom",
            color="orange",
            fontsize=FONTSIZE-2,
)

median_artist = bp["medians"][0]
mean_artist = bp["means"][0]

# Add legend using the extracted artists
plt.legend([median_artist, mean_artist], ["Median", "Mean"],loc = 'upper left')

plt.tight_layout()
if SAVE_IMG: 
    plt.savefig("plots/PM25_Boxplot.pdf")
plt.show()
