import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data

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
selected_iso = list(iso_to_country.keys())

# -- Selection (via dropdown for compatibility with Streamlit) --
selected_country = st.selectbox("Select a country to view rankings:", list(dataframes.keys()))
selected_iso_code = country_to_iso[selected_country]

# -- Display Altair map (highlight selected country) --
map_chart = alt.Chart(countries).mark_geoshape(
    stroke='white'
).transform_filter(
    alt.FieldOneOfPredicate(field="id", oneOf=selected_iso)
).encode(
    color=alt.condition(
        f"datum.id === '{selected_iso_code}'", 
        alt.value('steelblue'), 
        alt.value('lightgray')
    ),
    tooltip=alt.Tooltip("id:N", title="Country")
).project(
    type='mercator',
    scale=350,
    center=[20, 50],
    clipExtent=[[0, 0], [400, 300]]
).properties(
    width=400,
    height=300,
    title='Europe Map (Simplified)'
)

st.altair_chart(map_chart)

# -- Show song ranking for selected country --
st.subheader(f"Top Songs in {selected_country}")
df = dataframes[selected_country]

# Top 10 songs bar chart
top_10 = df.head(10)
chart = alt.Chart(top_10).mark_bar().encode(
    x=alt.X("streams:Q", title="Number of Streams"),  # Fixed scale
    y=alt.Y("track_name:N", sort="-x"),
    color="artist_names:N",
    tooltip=["rank", "track_name", "artist_names", "streams"]
    ).properties(width=700, height=500)

st.altair_chart(chart)
