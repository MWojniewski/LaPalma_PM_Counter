import pandas as pd
import os
import glob
import sys

directory_path = "data/all_data"
file_prefix = "Data_*.csv"
search_pattern = os.path.join(directory_path, file_prefix)
all_files = glob.glob(search_pattern)

if not all_files:
    print(f"No files matching pattern '{file_prefix}' were found.")
    sys.exit()

all_files.sort()
print(f"Found {len(all_files)} files. Aggregating datasets...")

df_list = []
for file in all_files:
    try:
        temp_df = pd.read_csv(file)
        df_list.append(temp_df)
    except Exception as e:
        print(f"Error parsing file {file}: {e}")

df = pd.concat(df_list, ignore_index=True)

df_invalid = df[df["Latitude"] == "INVALID"]
df_valid = df[df["Longitude"] != "INVALID"]

rows1, columns1 = df_invalid.shape
rows2, columns2 = df_valid.shape


print(rows1, "\n", rows2)
print(rows1 / (rows1 + rows2))
print(rows2 / (rows1 + rows2))

df_valid["Latitude"] = pd.to_numeric(df_valid["Latitude"], errors="coerce")
df_valid["Longitude"] = pd.to_numeric(df_valid["Longitude"], errors="coerce")

df_valid = df_valid[df_valid["Latitude"].between(27.95, 28.78)]
df_valid = df_valid[df_valid["Longitude"].between(-18.05, -16.71)]

df_valid.to_csv("data/valid_gps_data/valid_gps_data.csv")
