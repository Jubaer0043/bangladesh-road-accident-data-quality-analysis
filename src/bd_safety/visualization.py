"""Charts expose source limitations alongside actual published-record distributions."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import Normalize
import numpy as np
import pandas as pd
import seaborn as sns

from .config import FIGURES, TABLES

BLUE, ORANGE = "#2166AC", "#B35806"
FOOTER = "Published workbook records after exact deduplication. Unresolved identity and chronology; counts do not measure accident risk."


def save(fig, name, footer=FOOTER):
    fig.text(0.035, 0.012, footer, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(
        FIGURES / f"{name}.png", dpi=170, bbox_inches="tight", facecolor="white"
    )
    plt.close(fig)


def charts():
    FIGURES.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", font_scale=1.0)
    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.family": "DejaVu Sans",
        }
    )
    declared = pd.read_csv(TABLES / "declared_years.csv")
    actual = pd.read_csv(TABLES / "date_years.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].bar(declared.declared_year, declared.records, color=BLUE)
    axes[0].set(
        title="Separate Year field", xlabel="Declared year", ylabel="Published records"
    )
    axes[0].set_xticks(declared.declared_year.iloc[::2])
    axes[0].tick_params(axis="x", rotation=45)
    axes[1].bar(actual.date_year.astype(str), actual.records, color=ORANGE)
    axes[1].set(
        title="Year parsed from Date",
        xlabel="Parsed year",
        ylabel="Records with a parseable Date",
    )
    fig.suptitle("Two incompatible chronologies · no valid national annual trend")
    save(fig, "01_year_coverage")

    monthly = (
        pd.read_csv(TABLES / "months.csv")
        .pivot(index="month", columns="basis", values="records")
        .reindex(range(1, 13))
    )
    fig, ax = plt.subplots(figsize=(11, 5))
    monthly.plot.bar(ax=ax, color=[BLUE, ORANGE], width=0.8)
    ax.set(
        title="Month distributions depend on the source field",
        xlabel="Month number",
        ylabel="Published records",
    )
    ax.tick_params(axis="x", rotation=0)
    ax.legend(title="Field basis")
    save(fig, "02_month_fields")

    time = (
        pd.read_csv(TABLES / "time_of_day.csv")
        .set_index("hour")
        .reindex(range(24), fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(time.index, time.records, color=BLUE)
    ax.set(
        title="Recorded hour is dominated by 23:00",
        xlabel="Hour from Time field",
        ylabel="Published records",
        xticks=range(0, 24, 2),
    )
    save(fig, "03_recorded_hour")

    cross = pd.read_csv(TABLES / "cross_severity_label_fatalities.csv", index_col=0)
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.heatmap(
        cross, annot=True, fmt="d", cmap="Blues", ax=ax, cbar_kws={"label": "Records"}
    )
    ax.set(
        title="Severity labels do not consistently match fatality values",
        xlabel="Death Count value in workbook",
        ylabel="Accident_Intensity label",
    )
    save(fig, "04_severity_fatality_consistency")

    participants = pd.read_csv(TABLES / "participants.csv").sort_values("records")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(participants.participant_type, participants.records, color=BLUE)
    ax.set(
        title="Participants mentioned in Vehicle Info",
        xlabel="Records containing participant type",
    )
    save(
        fig,
        "05_participant_mentions",
        "Participant types overlap and include pedestrians. Source-record mentions are not vehicle exposure or accident-risk estimates.",
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    weather = pd.read_csv(TABLES / "cross_weather_x_weather_y.csv", index_col=0)
    light = pd.read_csv(TABLES / "cross_light_original_lighting.csv", index_col=0)
    sns.heatmap(weather, annot=True, fmt="d", cmap="Blues", ax=axes[0], cbar=False)
    sns.heatmap(light, annot=True, fmt="d", cmap="Blues", ax=axes[1], cbar=False)
    axes[0].set(
        title="Weather_x versus Weather_y", xlabel="Weather_y", ylabel="Weather_x"
    )
    axes[1].set(
        title="Light Condition versus Lighting",
        xlabel="Lighting",
        ylabel="Light Condition",
    )
    save(
        fig,
        "06_parallel_field_disagreements",
        "Parallel source fields are retained separately. Lexical disagreement is an audit flag, not proof of which field is correct.",
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, field, title in zip(
        axes,
        ["road_class", "road_condition"],
        ["Road classification", "Road Surface Condition"],
    ):
        table = pd.read_csv(TABLES / f"{field}.csv").sort_values("records")
        ax.barh(table[field], table.records, color=BLUE)
        ax.set(title=title, xlabel="Records · logarithmic scale", xscale="log")
        for row in table.itertuples():
            ax.text(
                row.records * 1.12,
                getattr(row, field),
                f"{row.records:,}",
                va="center",
                fontsize=9,
            )
        ax.set_xlim(0.8, table.records.max() * 4)
    save(fig, "07_road_fields")

    coords = pd.read_csv(TABLES / "coordinates.csv").sort_values(
        "records", ascending=False
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)
    norm = Normalize(vmin=0, vmax=np.log10(coords.records.max()))
    for ax, table, title in [
        (axes[0], coords, "All parsed coordinate pairs"),
        (axes[1], coords.iloc[1:], "Dominant coordinate pair excluded"),
    ]:
        scatter = ax.scatter(
            table.longitude,
            table.latitude,
            s=12 + 35 * np.log10(table.records),
            c=np.log10(table.records),
            cmap="viridis",
            norm=norm,
            alpha=0.8,
        )
        ax.set(title=title, xlabel="Longitude (°E)", ylabel="Latitude (°N)")
    color_ax = fig.add_axes([0.28, 0.125, 0.46, 0.025])
    fig.colorbar(
        scatter,
        cax=color_ax,
        label="log₁₀(records) · shared color scale",
        orientation="horizontal",
    )
    # Explicit axes positions prevent the shared colorbar overlapping longitude labels.
    fig.suptitle("Published coordinate distribution · not a verified hotspot map")
    fig.subplots_adjust(bottom=0.30, top=0.83, wspace=0.25)
    fig.text(
        0.025,
        0.015,
        "Marker area = 12 + 35 × log₁₀(records). Repeated coordinates may reflect reuse; location coverage is not nationally representative.",
        fontsize=8.5,
    )
    fig.savefig(
        FIGURES / "08_coordinate_coverage.png",
        dpi=170,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)

    import json

    q = json.loads((TABLES.parent / "data_quality.json").read_text())
    categories = [
        "Invalid Date",
        "Date / Year conflict",
        "Date / Month conflict",
        "Weather field disagreement",
        "Lighting field disagreement",
        "Severity / fatality flag",
    ]
    values = [
        q[k]
        for k in [
            "invalid_dates",
            "date_year_conflicts",
            "date_month_conflicts",
            "weather_disagreements",
            "light_disagreements",
            "severity_fatality_disagreements",
        ]
    ]
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.barh(categories, values, color=ORANGE)
    ax.invert_yaxis()
    ax.set(
        title="Data-quality flags overlap across the same records",
        xlabel="Flagged cleaned records",
    )
    for label, value in zip(categories, values):
        ax.text(value + 450, label, f"{value:,}", va="center", fontsize=9)
    ax.set_xlim(0, max(values) * 1.18)
    save(
        fig,
        "09_quality_flags",
        "Flag definitions and denominators are in data_quality.json. Overlapping flag counts must not be added.",
    )

    sensitivity = pd.read_csv(TABLES / "duplicate_sensitivity.csv")
    labels = [
        "Exact rows only",
        "First row per source ID",
        "First row per descriptor",
        "Last row per descriptor",
    ]
    fig, axes = plt.subplots(
        1, 2, figsize=(13, 5), sharey=True, gridspec_kw={"width_ratios": [1.5, 1]}
    )
    ax = axes[0]
    y = np.arange(len(labels))
    colors = [BLUE, ORANGE, ORANGE, ORANGE]
    ax.barh(y, sensitivity.fatal_record_share, color=colors)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set(
        xlim=(0, 1.1),
        xlabel="Records with Death Count > 0",
        title="Unverified identity rules change the selected rows",
    )
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{100 * x:.0f}%"))
    for position, row in zip(y, sensitivity.itertuples()):
        ax.text(
            row.fatal_record_share + 0.015,
            position,
            f"{row.fatal_record_share:.1%}; n={row.records:,}",
            va="center",
            fontsize=9,
        )
    axes[1].barh(y, sensitivity.difference_night_minus_day, color=colors)
    axes[1].axvline(0, color="#333333", linewidth=1)
    axes[1].set(
        xlim=(-0.03, 0.03),
        xlabel="Night − Day difference · percentage points",
        title="The descriptive association changes direction",
    )
    axes[1].xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{100 * x:.0f}"))
    axes[1].tick_params(labelleft=False)
    for position, value in zip(y, sensitivity.difference_night_minus_day):
        axes[1].annotate(
            f"{100 * value:.2f}",
            (value, position),
            xytext=(4 if value >= 0 else -4, 0),
            textcoords="offset points",
            ha="left" if value >= 0 else "right",
            va="center",
            fontsize=9,
        )
    save(
        fig,
        "10_duplicate_sensitivity",
        "Alternative identity rules are sensitivity scenarios, not validated deduplication. Fatal-record share is not population accident risk.",
    )
    return [p.name for p in sorted(FIGURES.glob("*.png"))]
