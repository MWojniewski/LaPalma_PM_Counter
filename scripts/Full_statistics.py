import pandas as pd
import numpy as np
import json
import glob
import os
import sys

JSON_PATH = "data/specified_area_data/Areas_of_interest.json"
DATA_DIR = "data/valid_gps_data"
FILE_PREFIX = "valid*.csv"
TARGET_COLUMN = "PM2.5"
OUTPUT_FILE = "data/specified_area_data/Regional_PM25_Full_Statistics.csv"
OUTLIER_THRESHOLD = 100000


try:
    with open(JSON_PATH, "r", encoding="utf-8") as file:
        areas_of_interest = json.load(file)
    print(f"Successfully loaded spatial configurations from {JSON_PATH}")
except Exception as e:
    print(f"Failed to load {JSON_PATH}. {e}")
    sys.exit()

search_pattern = os.path.join(DATA_DIR, FILE_PREFIX)
all_files = glob.glob(search_pattern)

if not all_files:
    print(f"No telemetry data found matching pattern: {search_pattern}")
    sys.exit()

df_list = []
for file_path in all_files:
    try:
        temp_df = pd.read_csv(file_path)
        df_list.append(temp_df)
    except Exception as e:
        print(f"Data stream corruption in file {file_path}. {e}")

df = pd.concat(df_list, ignore_index=True)

required_columns = ["Timestamp", "Latitude", "Longitude", TARGET_COLUMN]
for col in required_columns:
    if col not in df.columns:
        print(f"Dimensional mismatch. Column '{col}' missing.")
        sys.exit()

df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

# Neutralize extreme outliers before statistical computations - not used by now
outlier_mask = df[TARGET_COLUMN] > OUTLIER_THRESHOLD
df.loc[outlier_mask, TARGET_COLUMN] = np.nan

df = df.dropna(subset=["Timestamp", "Latitude", "Longitude"]).copy()

analytical_results = []

for region_key, params in areas_of_interest.items():
    region_name = params.get("name", region_key)

    lat_bounds = params.get("lat", [0, 0])
    lng_bounds = params.get("lng", [0, 0])

    spatial_mask = df["Latitude"].between(min(lat_bounds), max(lat_bounds)) & df[
        "Longitude"
    ].between(min(lng_bounds), max(lng_bounds))
    df_region = df[spatial_mask].copy()

    if "max_time" in params:
        df_region = df_region[
            df_region["Timestamp"] <= pd.to_datetime(params["max_time"])
        ]

    if "min_time" in params:
        df_region = df_region[
            df_region["Timestamp"] >= pd.to_datetime(params["min_time"])
        ]

    df_region_clean = df_region.dropna(subset=[TARGET_COLUMN])
    sample_size = len(df_region_clean)

    if sample_size > 0:
        min_val = df_region_clean[TARGET_COLUMN].min()
        q1_val = df_region_clean[TARGET_COLUMN].quantile(0.25)
        median_val = df_region_clean[TARGET_COLUMN].median()
        q3_val = df_region_clean[TARGET_COLUMN].quantile(0.75)
        max_val = df_region_clean[TARGET_COLUMN].max()

        mean_val = df_region_clean[TARGET_COLUMN].mean()
        std_val = df_region_clean[TARGET_COLUMN].std()
    else:
        min_val = q1_val = median_val = q3_val = max_val = mean_val = std_val = None

    analytical_results.append(
        {
            "Region_ID": region_key,
            "Location_Name": region_name,
            "Valid_Samples": sample_size,
            f"{TARGET_COLUMN}_Mean": (
                round(mean_val, 2) if mean_val is not None else "N/A"
            ),
            f"{TARGET_COLUMN}_StdDev": (
                round(std_val, 2) if pd.notnull(std_val) else "N/A"
            ),
            f"{TARGET_COLUMN}_Min": round(min_val, 2) if min_val is not None else "N/A",
            f"{TARGET_COLUMN}_Q1": round(q1_val, 2) if q1_val is not None else "N/A",
            f"{TARGET_COLUMN}_Median": (
                round(median_val, 2) if median_val is not None else "N/A"
            ),
            f"{TARGET_COLUMN}_Q3": round(q3_val, 2) if q3_val is not None else "N/A",
            f"{TARGET_COLUMN}_Max": round(max_val, 2) if max_val is not None else "N/A",
        }
    )

output_dataframe = pd.DataFrame(analytical_results)
output_dataframe.to_csv(OUTPUT_FILE, index=False)
