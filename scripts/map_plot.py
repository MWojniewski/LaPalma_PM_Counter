import pandas as pd
import plotly.express as px
import glob
import os


def create_map(directory_path, target_column="PM2.5", file_prefix="valid_gps*.csv"):
    print(f"Scanning directory: {directory_path}")

    search_pattern = os.path.join(directory_path, file_prefix)
    all_files = glob.glob(search_pattern)

    if not all_files:
        print(f"No files matching pattern '{file_prefix}' were found.")
        return

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

    df = df[df["Latitude"] != "INVALID"]
    df = df[df["Longitude"] != "INVALID"]

    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df[target_column] = pd.to_numeric(df[target_column], errors="coerce")

    df = df[df["Latitude"].between(27.95, 28.78)]
    df = df[df["Longitude"].between(-18.05, -16.71)]

    df = df.dropna(subset=["Latitude", "Longitude", target_column])

    if df.empty:
        print("no data to plot")
        return

    print(f"{len(df)} positions found")

    fig = px.scatter_map(
        df,
        lat="Latitude",
        lon="Longitude",
        color=target_column,
        hover_name="Timestamp",
        hover_data=[target_column, "Temp_[C]", "Hum_[%]"],
        color_continuous_scale=px.colors.sequential.Plasma,
        size_max=15,
        range_color=[0, 100],
        zoom=12,
        opacity=0.6,
        title=f"{target_column} - La Palma",
    )

    fig.update_layout(
        mapbox_style="open-street-map", margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    output_html = f"maps/{target_column.replace('/','_').replace('[','').replace(']','')}_La_Palma_map.html"
    fig.write_html(output_html)


create_map("data/valid_gps_data", target_column="PM2.5")


# Lat: 27.95 <-> 28.78
# Long: -18.05  <-> -16.71
