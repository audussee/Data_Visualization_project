import pandas as pd
import altair as alt
import panel as pn
import numpy as np
from vega_datasets import data
pn.extension('vega')

# -- Data loading --
data_files = {
    "Germany": "Country_csv/Germany.csv", 
    "France": "Country_csv/France.csv", 
    "Denmark": "Country_csv/Denmark.csv", 
    "Belgium": "Country_csv/Belgium.csv",  
    "Italy": "Country_csv/Italy.csv", 
    "Spain": "Country_csv/Spain.csv", 
    "United Kingdom of Great Britain and Northern Ireland": "Country_csv/England.csv", 
    "Netherlands, Kingdom of the": "Country_csv/Netherlands.csv", 
    "Switzerland": "Country_csv/Switzerland.csv", 
    "Portugal" : "Country_csv/Portugal.csv" 
}

# Load CSVs into a dictionary of dataframes
dataframes = {country: pd.read_csv(file) for country, file in data_files.items()}
dataframes_all = pd.concat([dataframes[country] for country in dataframes.keys()])

# -- Mapping of ISO 3166-1 alpha-3 codes to country names --
iso_to_country = {'DEU': 'Germany', 'FRA': 'France', 'DNK': 'Denmark', 'BEL': 'Belgium', 'GBR' : 'United Kingdom of Great Britain and Northern Ireland', 
                  'ESP' : 'Spain', 'ITA' : 'Italy', 'PRT' : 'Portugal', 'CHE' : 'Switzerland', 'NLD' : 'Netherlands, Kingdom of the'}

country_to_iso = {v: k for k, v in iso_to_country.items()}

# Load map data
countries = alt.topo_feature(data.world_110m.url, 'countries')

# Dropdown for country and week
country_select = pn.widgets.Select(name='Select Country', options=list(dataframes.keys()), value='Germany')
week_slider = pn.widgets.Select(name='Select Week', options=[], value=None)

# Output panes
map_pane = pn.pane.Vega(sizing_mode='stretch_width', height=350)
bar_pane = pn.pane.Vega(sizing_mode='stretch_width', height=500)
df_pane = pn.pane.DataFrame(height=300)
df_song_detail = pn.pane.DataFrame(height=300)

# -- Reactive function --
def update_visuals(country):
    df = dataframes[country]
    weeks = sorted(df['week'].unique())
    week_slider.options = weeks
    week_slider.value = weeks[0] if weeks else None
    return

country_select.param.watch(lambda e: update_visuals(e.new), 'value')
update_visuals(country_select.value)

def create_map(selected_song, selected_week):
    if not selected_song or not selected_week:
        return alt.Chart().mark_text(text="Select a song to view map", align="center", dy=150
                                   ).properties(width=400, height=300)
    
    ids = pd.read_json('https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/refs/heads/master/all/all.json')
    ids['geo'] = ids['alpha-3'].str.lower()

    # Filter data for selected song/week
    df_song = dataframes_all[(dataframes_all['track_name'] == selected_song) & 
                            (dataframes_all['week'] == selected_week)]
    df_song['name'] = df_song['country']
    df_song = df_song.merge(ids[['name', 'country-code']], how='left', on='name')
    df_song['id'] = df_song['name'].map(country_to_iso)
    df_song = df_song.dropna(subset=['id'])

    # Background map (grey countries)
    background = alt.Chart(countries).mark_geoshape(
        fill='lightgrey',
        stroke='white'
    ).project(
    type='mercator',
    center=[10, 50],     # Slightly west and lower center for better Europe framing
    scale=500,           # Zoom in a bit more
    translate=[200, 150]  # Center the map visually (half of width and height)
    ).properties(
        width=400,
        height=300
    )

    # Countries with data
    choropleth = alt.Chart(countries).mark_geoshape(
        stroke='white'
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(df_song, key='country-code', fields=['streams', 'name'])
    ).encode(
        color=alt.Color('streams:Q', 
                       scale=alt.Scale(scheme='blues'), 
                       title="Streams"),
        tooltip=['name:N', 'streams:Q']
    ).project(
    type='mercator',
    center=[10, 50],     # Slightly west and lower center for better Europe framing
    scale=500,           # Zoom in a bit more
    translate=[200, 150]  # Center the map visually (half of width and height)
    ).properties(
        width=400,
        height=300
    )

    return (background + choropleth).configure_view(stroke=None)
# -- Modify your existing code --

# Add a song selector widget (will be populated in update_all)
song_select = pn.widgets.Select(name='Select Song', options=[], sizing_mode='stretch_width')

# -- Update the update_all function --
def update_all(event=None):
    country = country_select.value
    week = week_slider.value
    if not week:
        return

    df = dataframes[country]
    df_week = df[(df['week'] == week)]
    df_top_10 = df_week.head(10)
    
    # Update song selector options
    song_options = df_top_10['track_name'].tolist()
    song_select.options = song_options
    song_select.value = song_options[0] if song_options else None
    
    # Update bar chart (without selection)
    bars = alt.Chart(df_top_10).mark_bar().encode(
        x=alt.X('streams:Q', title='Number of Streams'),
        y=alt.Y('track_name:N', sort='-x', title='Song Title'),
        color='track_name:N',
        tooltip=['rank', 'track_name', 'artist_names', 'streams']
    ).properties(width=700, height=500)
    
    bar_pane.object = bars
    df_pane.object = df_week[['rank', 'track_name', 'artist_names', 'streams']]
    
    # Function to update details when song changes
    def update_song_details(event=None):
        selected_song = song_select.value
        if selected_song:
            # Update song details
            df_selected = df_week[df_week['track_name'] == selected_song]
            df_song_detail.object = df_selected[["rank", "track_name", "artist_names", "streams"]]
            
            # Update map
            map_pane.object = create_map(selected_song, week)
        else:
            df_song_detail.object = pd.DataFrame()
            map_pane.object = alt.Chart().mark_text(text="No song selected").properties(width=400, height=300)
    
    # Watch for song selection changes
    song_select.param.watch(update_song_details, 'value')
    
    # Initial update
    update_song_details()

# -- Update your layout --
app = pn.Column(
    pn.Row(country_select, week_slider),
    pn.Column(map_pane),
    pn.Row(song_select),
    pn.Column(bar_pane),
    pn.pane.Markdown("## Scrollable Song Rankings"),
    df_pane,
    pn.pane.Markdown("## Selected Song Details"),
    df_song_detail
)

# Trigger updates
country_select.param.watch(update_all, 'value')
week_slider.param.watch(update_all, 'value')
update_all()

app.servable()