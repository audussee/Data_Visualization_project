import pandas as pd
import altair as alt
from vega_datasets import data
import streamlit as st
import numpy as np  

# Load the data
data_files = {
    "Germany": "Country_csv/Germany.csv",
    "France": "Country_csv/France.csv",
    "Denmark": "Country_csv/Denmark.csv",
    "Belgium": "Country_csv/Belgium.csv"
}

# Load CSVs into a dictionary of dataframes
dataframes = {country: pd.read_csv(file) for country, file in data_files.items()}

# -- Mapping of ISO 3166-1 alpha-3 codes to country names --
iso_to_country = {
    'DEU': 'Germany',
    'FRA': 'France',
    'DNK': 'Denmark',
    'BEL': 'Belgium'
}
country_to_iso = {v: k for k, v in iso_to_country.items()}

# -- Load and filter TopoJSON for just those 4 countries --
countries = alt.topo_feature(data.world_110m.url, 'countries')
# -- Selection (via dropdown for compatibility with Streamlit) --
selected_country = st.selectbox("Select a country to view rankings:", list(dataframes.keys()))
selected_iso_code = country_to_iso[selected_country]

# Load the ISO-3166 contry code data
ids = pd.read_json('https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/refs/heads/master/all/all.json')
ids['geo'] = ids['alpha-3'].str.lower()

test_df = pd.DataFrame([[selected_country, 1]], columns=['name', 'Value'])
test_df = test_df.merge(ids[['name', 'country-code']], how='left', on='name')

# Merge with the gapminder2000 data frame
# Merge gapminder dataset with the latitude and longitude coordinates


background = alt.Chart(countries).mark_geoshape(fill = 'lightgrey', stroke = 'grey').project(
    type= 'mercator',
    scale= 350,                          # Magnify
    center= [20,50],                     # [lon, lat]
    clipExtent= [[0, 0], [400, 300]],    # [[left, top], [right, bottom]]
).properties(
    title='Europe (Mercator)',
    width=400, height=300
)

main = alt.Chart(countries).mark_geoshape(stroke = 'grey').transform_lookup(
    lookup = 'id', from_=alt.LookupData(data = test_df, key = 'country-code', fields = ['Value', 'Country'])
).encode(
    color = 'Value:Q',
    tooltip='Country:N'
).project(
    type= 'mercator',
    scale= 350,                          # Magnify
    center= [20,50],                     # [lon, lat]
    clipExtent= [[0, 0], [400, 300]],    # [[left, top], [right, bottom]]
).properties(
    title='Europe (Mercator)',
    width=400, height=300
)

st.altair_chart(background + main)

#Selection of the week 
selected_week = st.select_slider("Select a week to view rankings:", np.unique(dataframes[selected_country]['week']))

# Display ranking chart if a country was clicked
if selected_country and selected_week:
    st.subheader(f"Top Songs in {selected_country}")

    # Get the data for the selected country
    df = dataframes[selected_country]
    df = df[df['week'] == selected_week]

    # Create a scrollable dataframe view
    st.subheader(f"Scrollable Song Rankings for {selected_country}")
    st.dataframe(df[["rank", "track_name", "artist_names", "streams"]], height=300)

    # Display Altair chart for top 10 songs initially
    df_top_10 = df.head(10)
    selected_song = alt.selection_point(name = 'selected_song', fields = ['track_name'])
    color = alt.Color('track_name:N')
    chart = alt.Chart(df_top_10).mark_bar().encode(
        x=alt.X("streams:Q", title="Number of Streams"),  # Fixed scale
        y=alt.Y("track_name:N", sort="-x"),
        color=alt.when(selected_song).then(color).otherwise(alt.value('lightgrey')),
        tooltip=["rank", "track_name", "artist_names", "streams"]
    ).properties(width=700, height=500).add_params(selected_song)

    st_chart = st.altair_chart(chart)
    selected = st_chart.selection()
    st.subheader(f"{selected_song}")

    df_filtered = df[df['track_name'] == selected]
    st.dataframe(df_filtered[["rank", "track_name", "artist_names", "streams"]], height=300)
