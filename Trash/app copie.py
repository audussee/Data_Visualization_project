import streamlit as st
import pandas as pd
import altair as alt

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/dataprofessor/data/refs/heads/master/penguins_cleaned.csv"
    penguins = pd.read_csv(url)
    return penguins

st.header('Penguin Dataset')

penguins = load_data()

col1, col2 = st.columns(2)

# if 'counter' not in st.session_state:
#     st.session_state.counter = 0

# st.session_state.counter +=1

# st.header("This page has runed : ", st.session_state.counter, ' Times')
#  with col1 : 
#     x_var = st.selectbox("X-axis", penguins.columns.values[3:5], index =0)
# with col2 : 
#     y_var = st.selectbox("Y-axis", penguins.columns.values[2:6], index =1)

x_var = st.sidebar.selectbox("X-axis", penguins.columns.values[3:5], index =0)
y_var = st.sidebar.selectbox("Y-axis", penguins.columns.values[2:6], index =1)


species = st.sidebar.multiselect("Species", 
                         set(penguins['species']),
                         set(penguins['species']))

brush = alt.selection_interval('brush')


points = alt.Chart(penguins).mark_point(filled=True).encode(
    x=alt.X(f'{x_var}:Q', scale=alt.Scale(zero=False)),
    y=alt.Y(f'{y_var}:Q', scale=alt.Scale(zero=False)),
    color=alt.Color('species:N', scale=alt.Scale(domain=['Adelie', 'Gentoo', 'Chinstrap'])),
    shape='sex:N'
).transform_filter(
    alt.FieldOneOfPredicate(field = 'species', oneOf = species)
).add_params(brush)

event = st.altair_chart(points, key='scatterplot', on_select='rerun', theme = None)

def filtered_table(event):
    selection = event['selection']['brush']


    # 0. Prevent an error if selection object is None or empty.
    if selection == dict():
        return penguins


    # 1. Create a query string to filter the data
    query = ' & '.join(
        f'{crange[0]} <= `{col}` <= {crange[1]}'
        for col, crange in selection.items())


    # 2. Filter the penguin data frame from the query
    df = penguins[penguins['species'].isin(species)].query(query)


    # 3. Add the DataFrame pane that render pandas object
    return df


penguins_sel = filtered_table(event)
st.dataframe(penguins_sel)

bg = alt.Chart(penguins).mark_bar(color='lightgrey').encode(
    x=alt.X('count()').scale(domain=(0, 160)),
    y=alt.Y('species:N').scale(domain=set(penguins['species'])),
)


bars = alt.Chart(penguins_sel).mark_bar().encode(
    x=alt.X('count()').scale(domain=(0, 160)),
    y=alt.Y('species:N').scale(domain=set(penguins['species'])),
    color=alt.Color('species:N', scale=alt.Scale(domain=['Adelie', 'Gentoo', 'Chinstrap']))
)
st.altair_chart(bg + bars, theme=None)