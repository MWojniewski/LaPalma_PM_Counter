import pandas as pd
import os
import glob
import sys

# Measurement boundaries
LAT_MIN = 27.95
LAT_MAX = 28.78
LON_MIN = -18.05
LON_MAX = -16.71

TARGET_COLUMN = "PM2.5"

file = glob.glob("data/valid_gps_data/valid*.csv")

if not file:
    print("No file was found.")
    sys.exit()

df = pd.read_csv(file[0])

# Checking if spatial and target columns exist in the dataset
required_columns = ["Latitude", "Longitude", TARGET_COLUMN]
for col in required_columns:
    if col not in df.columns:
        print(f"CRITICAL ERROR: Column '{col}' not found in the dataset.")
        sys.exit()

df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")

# Isolation of spatial data strictly within the defined bounding box
df_filtered = df[
    df["Latitude"].between(LAT_MIN, LAT_MAX) & df["Longitude"].between(LON_MIN, LON_MAX)
].copy()

df_filtered = df_filtered.dropna(subset=[TARGET_COLUMN])

data_points = len(df_filtered)

if data_points > 0:
    mean_val = df_filtered[TARGET_COLUMN].mean()
    std_val = df_filtered[TARGET_COLUMN].std()

    print("\n--- SPATIAL STATISTICAL ANALYSIS ---")
    print(f"Target Variable : {TARGET_COLUMN}")
    print(f"Bounding Box    : Lat [{LAT_MIN}, {LAT_MAX}], Lon [{LON_MIN}, {LON_MAX}]")
    print(f"Valid Samples   : {data_points}")
    print(f"Mean            : {mean_val:.2f}")
    print(f"Std Dev         : {std_val:.2f}")
    print("------------------------------------")
else:
    print(
        f"\nWARNING: No valid '{TARGET_COLUMN}' data points found within the specified bounding box."
    )
