import streamlit as st
import pandas as pd
import folium
import altair as alt
from streamlit_folium import st_folium

# Load the data
data_files = {
    "Germany": "Country_csv/Germany.csv",
    "France": "Country_csv/France.csv",
    "Denmark": "Country_csv/Denmark.csv",
    "Belgium": "Country_csv/Belgium.csv"
}

# Load CSVs into a dictionary of dataframes
dataframes = {country: pd.read_csv(file) for country, file in data_files.items()}

# Country coordinates (for placing markers)
country_coords = {
    "Germany": [51.1657, 10.4515],
    "France": [46.6034, 1.8883],
    "Denmark": [56.2639, 9.5018],
    "Belgium": [50.8503, 4.3517]
}
# Streamlit layout
st.title("European Music Rankings")

# Initialize map
map_center = [50, 10]  # Approximate center of Europe
m = folium.Map(location=map_center, zoom_start=4)

# Add markers for each country with unique IDs
for country, coords in country_coords.items():
    folium.Marker(
        location=coords,
        popup=country,
        tooltip="Click to view rankings",
        icon=folium.Icon(color="blue")
    ).add_to(m)

# Display the interactive map and capture user clicks
map_data = st_folium(m, height=500, width=700)

# Extract the clicked location
if map_data and "last_clicked" in map_data:
    lat, lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]

    # Find the closest country based on coordinates
    selected_country = None
    min_distance = float("inf")

    for country, coords in country_coords.items():
        distance = (coords[0] - lat) ** 2 + (coords[1] - lon) ** 2  # Simple distance metric
        if distance < min_distance:
            min_distance = distance
            selected_country = country

    # Display ranking chart if a country was clicked
    if selected_country:
        st.subheader(f"Top Songs in {selected_country}")

        # Get the data for the selected country
        df = dataframes[selected_country]

        # Create a scrollable dataframe view
        st.subheader(f"Scrollable Song Rankings for {selected_country}")
        st.dataframe(df[["rank", "track_name", "artist_names", "streams"]], height=300)

        # Display Altair chart for top 10 songs initially
        df_top_10 = df.head(10)

        chart = alt.Chart(df_top_10).mark_bar().encode(
            x=alt.X("streams:Q", title="Number of Streams"),  # Fixed scale
            y=alt.Y("track_name:N", sort="-x"),
            color="artist_names:N",
            tooltip=["rank", "track_name", "artist_names", "streams"]
        ).properties(width=700, height=500)

        st.altair_chart(chart)
