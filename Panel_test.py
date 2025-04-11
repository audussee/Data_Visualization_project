import pandas as pd
import altair as alt
import panel as pn
import numpy as np
from vega_datasets import data

pn.extension("vega")

# -- Data loading --
data_files = {
    "Germany": "Country_csv/Germany.csv",
    "France": "Country_csv/France.csv",
    "Denmark": "Country_csv/Denmark.csv",
    "Belgium": "Country_csv/Belgium.csv",
    "Italy": "Country_csv/Italy.csv",
    "Spain": "Country_csv/Spain.csv",
    "United Kingdom": "Country_csv/England.csv",
    "Netherlands": "Country_csv/Netherlands.csv",
    "Switzerland": "Country_csv/Switzerland.csv",
    "Portugal": "Country_csv/Portugal.csv",
}

# Load CSVs into a dictionary of dataframes
dataframes = {
    country: pd.read_csv(file, index_col=False) for country, file in data_files.items()
}
dataframes_all = pd.concat([dataframes[country] for country in dataframes.keys()])

# -- Mapping of ISO 3166-1 alpha-3 codes to country names --
iso_to_country = {
    "DEU": "Germany",
    "FRA": "France",
    "DNK": "Denmark",
    "BEL": "Belgium",
    "GBR": "United Kingdom",
    "ESP": "Spain",
    "ITA": "Italy",
    "PRT": "Portugal",
    "CHE": "Switzerland",
    "NLD": "Netherlands",
}

country_to_iso = {v: k for k, v in iso_to_country.items()}

# Load map data
countries = alt.topo_feature(data.world_110m.url, "countries")

# Dropdown for country and week
country_select = pn.widgets.Select(
    name="Select Country", options=list(dataframes.keys()), value="Germany"
)
week_slider = pn.widgets.Select(name="Select Week", options=[], value=None)

# Output panes
map_pane = pn.pane.Vega(sizing_mode="stretch_width", height=350)
bar_pane = pn.pane.Vega(sizing_mode="stretch_width", height=500)
df_pane = pn.pane.DataFrame(height=300)
df_song_detail = pn.pane.DataFrame(height=300)
song_trend_pane = pn.pane.Vega(sizing_mode="stretch_width", height=300)


# Reactive function
def update_visuals(country):
    df = dataframes[country]
    weeks = sorted(df["week"].unique())
    week_slider.options = weeks
    week_slider.value = weeks[0] if weeks else None
    return


country_select.param.watch(lambda e: update_visuals(e.new), "value")
update_visuals(country_select.value)


def create_map(selected_song, selected_week, mode):
    if not selected_song or not selected_week:
        return (
            alt.Chart()
            .mark_text(text="Select a song to view map", align="center", dy=150)
            .properties(width=400, height=300)
        )

    ids = pd.read_json("ids.json")
    # ids = pd.read_json(
    #     "https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/refs/heads/master/all/all.json"
    # )
    ids["geo"] = ids["alpha-3"].str.lower()

    # Filter song data for selected week
    df_song = dataframes_all[
        (dataframes_all["track_name"] == selected_song)
        & (dataframes_all["week"] == selected_week)
    ].copy()

    # Get total streams per country for normalization
    if mode == "Relative Streams":
        df_total = (
            dataframes_all[dataframes_all["week"] == selected_week]
            .groupby("country")["streams"]
            .sum()
            .reset_index()
        )
        df_total = df_total.rename(columns={"streams": "total_streams"})

        df_song = df_song.merge(df_total, on="country", how="left")
        df_song["streams"] = (df_song["streams"] / df_song["total_streams"]) * 100

    df_song["name"] = df_song["country"]
    df_song = df_song.merge(ids[["name", "country-code"]], how="left", on="name")
    df_song["id"] = df_song["name"].map(country_to_iso)
    df_song = df_song.dropna(subset=["id"])

    # Background map
    background = (
        alt.Chart(countries)
        .mark_geoshape(fill="lightgrey", stroke="white")
        .project(
            type="mercator",
            center=[10, 50],
            scale=500,
            translate=[200, 150],
        )
        .properties(width=400, height=300)
    )

    # Choropleth layer
    choropleth = (
        alt.Chart(countries)
        .mark_geoshape(stroke="white")
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(
                df_song, key="country-code", fields=["streams", "name"]
            ),
        )
        .encode(
            color=alt.Color(
                "streams:Q",
                scale=alt.Scale(scheme="blues"),
                title=(
                    "Relative Streams (%)" if mode == "Relative Streams" else "Streams"
                ),
            ),
            tooltip=["name:N", "streams:Q"],
        )
        .project(
            type="mercator",
            center=[10, 50],
            scale=500,
            translate=[200, 150],
        )
        .properties(width=400, height=300)
    )

    return (background + choropleth).configure_view(stroke=None)


# Add a song selector widget (will be populated in update_all)
song_select = pn.widgets.Select(
    name="Select Song", options=[], sizing_mode="stretch_width"
)

map_mode_toggle = pn.widgets.RadioButtonGroup(
    name="Map Mode",
    options=["Absolute Streams", "Relative Streams"],
    button_type="success",
    value="Absolute Streams",
)


def update_all(event=None):
    country = country_select.value
    week = week_slider.value
    if not week:
        return

    df = dataframes[country]
    df_week = df[(df["week"] == week)]
    df_top_10 = df_week.head(10)

    # song selector options
    song_options = df_top_10["track_name"].tolist()
    song_select.options = song_options
    song_select.value = song_options[0] if song_options else None

    # Update bar chart (without selection)
    bars = (
        alt.Chart(df_top_10)
        .mark_bar()
        .encode(
            x=alt.X("streams:Q", title="Number of Streams"),
            y=alt.Y("track_name:N", sort="-x", title="Song Title"),
            color="track_name:N",
            tooltip=["rank", "track_name", "artist_names", "streams"],
        )
        .properties(width=700, height=500)
    )

    bar_pane.object = bars
    df_pane.object = df_week[
        ["rank", "track_name", "artist_names", "streams"]
    ].style.hide(axis="index")

    # Function to update details when song changes
    def update_song_details(event=None):
        selected_song = song_select.value
        if selected_song:
            # Update song details
            df_selected = df_week[df_week["track_name"] == selected_song]
            df_song_detail.object = df_selected[
                ["rank", "track_name", "artist_names", "streams"]
            ]

            # Update map
            map_pane.object = create_map(selected_song, week, map_mode_toggle.value)

            # Create trend chart
            # Get full list of weeks for the selected country
            df_country = dataframes[country_select.value]
            all_weeks = sorted(df_country["week"].unique())

            # Create a base DataFrame with all weeks
            df_all_weeks = pd.DataFrame({"week": all_weeks})

            # Get data for the selected song
            df_song_history = df_country[df_country["track_name"] == selected_song][
                ["week", "streams"]
            ]

            # Merge to ensure all weeks are included, missing ones will have NaN
            df_song_history_full = df_all_weeks.merge(
                df_song_history, on="week", how="left"
            )

            # Generate the line chart
            trend_chart = (
                alt.Chart(df_song_history_full)
                .mark_line(point=True)
                .encode(
                    x=alt.X("week:N", title="Week", sort=all_weeks),
                    y=alt.Y("streams:Q", title="Streams"),
                    tooltip=["week", "streams"],
                )
                .properties(
                    title="Stream Evolution Of The Selected Song Over Time In The Selected Country",
                    height=300,
                )
            )
            song_trend_pane.object = trend_chart

        else:
            df_song_detail.object = pd.DataFrame()
            map_pane.object = (
                alt.Chart()
                .mark_text(text="No song selected")
                .properties(width=400, height=300)
            )
            song_trend_pane.object = None

    # Watch for song selection changes
    song_select.param.watch(update_song_details, "value")
    # Watch for map mode change
    map_mode_toggle.param.watch(update_song_details, "value")

    # Initial update
    update_song_details()


app = pn.Column(
    pn.pane.Markdown("# 🎵 European Streaming Dashboard"),
    pn.pane.Markdown(
        "Explore the most streamed songs across Europe, filter by country and week, "
        "and dive into song-specific stats and their geographic spread."
    ),
    pn.pane.Markdown("### 1. Choose a country and week"),
    pn.Row(country_select, week_slider),
    pn.pane.Markdown("### 2. Top 10 streamed songs"),
    pn.pane.Markdown(
        "The bar chart below shows the top 10 songs in your selected country and week."
    ),
    pn.Column(bar_pane),
    pn.Spacer(height=20),
    pn.pane.Markdown("### 3. Full weekly ranking"),
    pn.pane.Markdown(
        "This table provides all the available songs for the selected country and week."
    ),
    df_pane,
    pn.pane.Markdown("### 4. Explore a specific song across Europe"),
    pn.pane.Markdown(
        "Pick a song from the top 10 to visualize its popularity across other European countries."
    ),
    pn.Row(song_select),
    map_mode_toggle,
    pn.Column(map_pane),
    pn.pane.Markdown("### 5. Song details"),
    pn.pane.Markdown(
        "This chart shows how the number of streams for the selected song evolved in the selected country."
    ),
    song_trend_pane,
)


# Trigger updates
country_select.param.watch(update_all, "value")
week_slider.param.watch(update_all, "value")
update_all()

# pn.extension()
# app.save("dashboard.html", embed=True)

app.servable()
