import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sys

INPUT_FILE = "data/specified_area_data/ferry_data.csv"
TARGET_COLUMN = "PM2.5"
OUTPUT_IMAGE = "plots/Ferry_PM25_plot.pdf"

SAVE_IMG    = True
FONTSIZE    = 12
Y_AXIS_MIN  = 0
Y_AXIS_MAX  = 150

try:
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} records from {INPUT_FILE}.")
except FileNotFoundError:
    print(f"{INPUT_FILE} not found. Run the extraction script first.")
    sys.exit()

df["Timestamp"] = pd.to_datetime(df["Timestamp"])
df = df.sort_values("Timestamp")

fig, ax = plt.subplots(figsize=(3,3))

ax.scatter(
    pd.to_datetime(df["Timestamp"]),
    df[TARGET_COLUMN],
    color="dodgerblue",
    marker=".",
    alpha=1,
    label="PM 2.5",
)

# ax.set_title("Stężenie PM 2.5 w czasie (Trasa promu)", fontsize=FONTSIZE, fontweight="bold")
# ax.set_xlabel("Czas pomiaru", fontsize=12)
ax.set_ylabel(f"PM 2.5 [µg/"+r"m$^3$]", fontsize=FONTSIZE)

ax.set_ylim(Y_AXIS_MIN, Y_AXIS_MAX)
# plt.xticks(fontsize=FONTSIZE-2)

ax.grid(True, linestyle=":", alpha=0.7)

ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.autofmt_xdate()

plt.tight_layout()
if SAVE_IMG:
    plt.savefig(OUTPUT_IMAGE)
    print(f"Time-series plot generated and saved as {OUTPUT_IMAGE}")
plt.show()
