import pandas as pd
import json
import glob
import os
import sys

JSON_PATH = "data/specified_area_data/Ferry_data.json"
DATA_DIR = "data/valid_gps_data"
FILE_PREFIX = "valid*.csv"
TARGET_COLUMN = "PM2.5"
OUTPUT_FILE = "data/specified_area_data/ferry_data.csv"

try:
    with open(JSON_PATH, "r", encoding="utf-8") as file:
        ferry_config = json.load(file)
    bounds = ferry_config["Ferry_bounds"]
except Exception as e:
    print(f"Failed to parse {JSON_PATH}. {e}")
    sys.exit()

search_pattern = os.path.join(DATA_DIR, FILE_PREFIX)
all_files = glob.glob(search_pattern)

if not all_files:
    print(f"No telemetry data found matching {search_pattern}")
    sys.exit()

df_list = []
for file_path in all_files:
    try:
        df_list.append(pd.read_csv(file_path))
    except Exception as e:
        print(f"Skipping file {file_path}. {e}")

df = pd.concat(df_list, ignore_index=True)

df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

df = df.dropna(subset=["Timestamp", "Latitude", "Longitude", TARGET_COLUMN])

lat_min, lat_max = min(bounds["lat"]), max(bounds["lat"])
lng_min, lng_max = min(bounds["lng"]), max(bounds["lng"])

spatial_mask = df["Latitude"].between(lat_min, lat_max) & df["Longitude"].between(
    lng_min, lng_max
)
df_ferry = df[spatial_mask].copy()

if "min_time" in bounds:
    df_ferry = df_ferry[df_ferry["Timestamp"] >= pd.to_datetime(bounds["min_time"])]
if "max_time" in bounds:
    df_ferry = df_ferry[df_ferry["Timestamp"] <= pd.to_datetime(bounds["max_time"])]

df_ferry = df_ferry.sort_values("Timestamp")
df_ferry.to_csv(OUTPUT_FILE, index=False)

print(f"Valid data points saved: {len(df_ferry)}")
print(f"Exported to: {OUTPUT_FILE}")
