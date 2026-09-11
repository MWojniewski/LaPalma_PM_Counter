import pandas as pd
import os
import glob
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector, Button
from typing import Dict, List, Optional

# Target analytes and environmental variables of scientific interest
TARGET_COLUMNS: List[str] = [
    "CO2_[ppm]",
    "PM1.0",
    "PM2.5",
    "PM4.0",
    "PM10.0",
    "VOC",
    "NO",
]

# Measurement boundaries
INITIAL_LAT = (27.95, 28.78)
INITIAL_LON = (-18.05, -16.71)

VISUALIZATION_METRIC = "PM2.5"


def load_validated_dataset(
    search_pattern: str = "data/valid_gps_data/valid*.csv",
) -> pd.DataFrame:
    """
    Locate and load the pre-filtered, validated GPS measurement dataset.
    """

    matched_files = glob.glob(search_pattern)

    if not matched_files:
        print("No files were found.")
        sys.exit()

    filepath = matched_files[0]
    print(f"Spatial dataset: {filepath}")

    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()
    print(df.columns)

    for coord_col in ["Latitude", "Longitude"]:
        if coord_col not in df.columns:
            print(f"Required coordinate column '{coord_col}' missing.")
            sys.exit()

    # Ensure numeric conversion for coordinates
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df = df.dropna(subset=["Latitude", "Longitude"]).copy()

    # Ensure numeric conversion for present target analytes
    for col in TARGET_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    print(f"Successfully loaded {len(df)} validated coordinate observations.")
    return df


def select_boundaries_interactively(df: pd.DataFrame) -> Optional[Dict[str, float]]:
    """
    Render an interactive map of measurement points and capture user-defined area.
    """
    area_bounds: Dict[str, Optional[float]] = {
        "lat_min": None,
        "lat_max": None,
        "lon_min": None,
        "lon_max": None,
    }

    fig, ax = plt.subplots(figsize=(11, 8.5))
    plt.subplots_adjust(bottom=0.12)

    # Color distribution
    has_color_metric = VISUALIZATION_METRIC in df.columns
    c_values = df[VISUALIZATION_METRIC] if has_color_metric else "tab:blue"

    scatter = ax.scatter(
        df["Longitude"],
        df["Latitude"],
        c=c_values,
        cmap="viridis" if has_color_metric else None,
        alpha=0.6,
        s=12,
        edgecolors="none",
        norm="log",
    )

    if has_color_metric:
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label(f"{VISUALIZATION_METRIC} Concentration", fontsize=10)

    ax.set_title(
        "Interactive Area Selection\n"
        "Click and drag across two points (opposite corners) to define Region of Interest",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel(r"Longitude [$^\circ$]", fontsize=10)
    ax.set_ylabel(r"Latitude [$^\circ$]", fontsize=10)
    ax.set_xlim(INITIAL_LON)
    ax.set_ylim(INITIAL_LAT)
    ax.grid(True, linestyle="--", alpha=0.5)

    def on_boundary_selected(eclick, erelease):
        """Callback to extract coordinates regardless of the drawing direction."""
        area_bounds["lon_min"] = min(eclick.xdata, erelease.xdata)
        area_bounds["lon_max"] = max(eclick.xdata, erelease.xdata)
        area_bounds["lat_min"] = min(eclick.ydata, erelease.ydata)
        area_bounds["lat_max"] = max(eclick.ydata, erelease.ydata)

        print("\n[SELECTION UPDATED]")
        print(
            f"  Latitude  Bounds: [{area_bounds['lat_min']:.6f}, {area_bounds['lat_max']:.6f}]"
        )
        print(
            f"  Longitude Bounds: [{area_bounds['lon_min']:.6f}, {area_bounds['lon_max']:.6f}]"
        )

    # Bind interactive rectangle selection mechanism
    selector = RectangleSelector(
        ax,
        on_boundary_selected,
        useblit=True,
        button=[1],
        minspanx=0.0005,
        minspany=0.0005,
        interactive=True,
    )

    # Attach confirmation button
    btn_ax = fig.add_axes([0.76, 0.02, 0.20, 0.05])
    btn_confirm = Button(btn_ax, "Confirm & Analyze")

    def on_confirm(event):
        if area_bounds["lat_min"] is None:
            print("Select rectangular region before confirming.")
            return
        plt.close(fig)

    btn_confirm.on_clicked(on_confirm)

    print("Select the target area on the plot and click 'Confirm & Analyze'.")
    plt.show()

    if area_bounds["lat_min"] is None:
        return None

    return {k: float(v) for k, v in area_bounds.items()}


def compute_statistics_and_export(df: pd.DataFrame, area: Dict[str, float]):
    """
    Filter data points strictly within selected area, compute statistical estimators,
    and save results to a CSV file.
    """
    lat_min, lat_max = area["lat_min"], area["lat_max"]
    lon_min, lon_max = area["lon_min"], area["lon_max"]

    # Spatial filtering
    area_mask = df["Latitude"].between(lat_min, lat_max) & df["Longitude"].between(
        lon_min, lon_max
    )
    selected_df = df[area_mask].copy()

    total_samples_in_area = len(selected_df)
    print("\n" + "=" * 65)
    print("REGION OF INTEREST EXTRACTION SUMMARY:")
    print("=" * 65)
    print(f"Selected Latitude  : [{lat_min:.6f}, {lat_max:.6f}]")
    print(f"Selected Longitude : [{lon_min:.6f}, {lon_max:.6f}]")
    print(f"Total Spatial Points : {total_samples_in_area}")
    print("=" * 65)

    if total_samples_in_area == 0:
        print("No measurements exist within the selected area")
        return

    # Statistical metrics
    statistical_data = []
    for target in TARGET_COLUMNS:
        if target not in selected_df.columns:
            print(f"Parameter '{target}' not in dataset...")
            continue

        valid_series = selected_df[target].dropna()
        count_valid = len(valid_series)

        if count_valid > 0:
            mean_val = valid_series.mean()
            std_val = valid_series.std() if count_valid > 1 else 0.0
            median_val = valid_series.median()
        else:
            mean_val = np.nan
            std_val = np.nan
            median_val = np.nan

        statistical_data.append(
            {
                "Target": target,
                "Valid_Samples": count_valid,
                "Mean": round(mean_val, 4),
                "Std_Dev": round(std_val, 4),
                "Median": round(median_val, 4),
                "Lat_Min": round(lat_min, 6),
                "Lat_Max": round(lat_max, 6),
                "Lon_Min": round(lon_min, 6),
                "Lon_Max": round(lon_max, 6),
            }
        )

    summary_df = pd.DataFrame(statistical_data)

    print("\nSTATISTICAL ESTIMATION RESULTS:")
    display_cols = ["Target", "Valid_Samples", "Mean", "Std_Dev", "Median"]
    print(summary_df[display_cols].to_string(index=False))
    print("=" * 65)

    default_name = "la_palma_area_analysis.csv"
    user_input = input(
        f"\nEnter output CSV filename - Press Enter for default - '{default_name}': "
    ).strip()
    target_filename = user_input if user_input else default_name

    if not target_filename.lower().endswith(".csv"):
        target_filename += ".csv"

    summary_df.to_csv("data/specified_area_data/" + target_filename, index=False)
    print(f"\nStatistical report saved to: {os.path.abspath(target_filename)}")


def main():
    df = load_validated_dataset()
    area = select_boundaries_interactively(df)

    if area is not None:
        compute_statistics_and_export(df, area)
    else:
        print("\nNo region was confirmed")


if __name__ == "__main__":
    main()
