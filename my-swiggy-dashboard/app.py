# ----------------------------------------------------------------------------------
# STAGE 1: IMPORT LIBRARIES
# ----------------------------------------------------------------------------------
# These are the tools we need to build our app.
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

# ----------------------------------------------------------------------------------
# STAGE 2: LOAD AND PREPARE THE DATA
# ----------------------------------------------------------------------------------
# Dash will look for this CSV file in the same folder as this app.py file.
try:
    df = pd.read_csv('swiggy state .csv')
except FileNotFoundError:
    print("Error: 'swiggy state .csv' not found. Make sure the file is in the same folder as app.py")
    exit()

# Basic data cleaning
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
df['Avg ratings'] = pd.to_numeric(df['Avg ratings'], errors='coerce')
df.dropna(subset=['Price', 'Avg ratings', 'State', 'City', 'Food type'], inplace=True)

# Get a sorted, unique list of cuisines for our filter dropdown
all_cuisines = sorted(df['Food type'].str.split(', ').explode().str.strip().unique())

# ----------------------------------------------------------------------------------
# STAGE 3: CREATE THE DASH APP
# ----------------------------------------------------------------------------------
# This initializes our Dash application.
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
server = app.server # This line is needed for deployment.

# ----------------------------------------------------------------------------------
# STAGE 4: DEFINE THE APP'S LAYOUT
# ----------------------------------------------------------------------------------
# This section defines the visual structure of the dashboard (like HTML).
app.layout = html.Div(children=[
    
    # --- HEADER ---
    html.H1(
        children='Interactive Swiggy Restaurant Dashboard',
        style={'textAlign': 'center', 'color': '#333'}
    ),
    html.Div(
        children='Analyze restaurant prices, ratings, and cuisines across different cities.',
        style={'textAlign': 'center', 'marginBottom': '40px'}
    ),

    # --- FILTERS ---
    html.Div(className='row', children=[
        # State Filter
        html.Div(className='four columns', children=[
            html.Label('State:'),
            dcc.Dropdown(
                id='state-filter',
                options=[{'label': i, 'value': i} for i in sorted(df['State'].unique())],
                multi=True,
                placeholder='Select a state...'
            ),
        ]),
        # City Filter (its options are updated by the state filter)
        html.Div(className='four columns', children=[
            html.Label('City:'),
            dcc.Dropdown(id='city-filter', multi=True, placeholder='Select a city...'),
        ]),
        # Cuisine Filter
        html.Div(className='four columns', children=[
            html.Label('Cuisine:'),
            dcc.Dropdown(
                id='cuisine-filter',
                options=[{'label': i, 'value': i} for i in all_cuisines],
                multi=True,
                placeholder='Select a cuisine...'
            ),
        ]),
    ], style={'padding': '20px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px'}),
    
    # Price Range Slider
    html.Div(children=[
        html.Label('Price Range (₹):', style={'marginTop': '20px'}),
        dcc.RangeSlider(
            id='price-slider',
            min=df['Price'].min(),
            max=df['Price'].max(),
            step=100,
            value=[df['Price'].min(), df['Price'].max()],
            marks={i: f'₹{i}' for i in range(0, int(df['Price'].max()) + 1, 500)}
        ),
    ], style={'padding': '20px'}),
    
    # --- CHARTS ---
    html.Div(className='row', children=[
        html.Div(dcc.Graph(id='restaurants-by-city-bar'), className='six columns'),
        html.Div(dcc.Graph(id='top-cuisines-pie'), className='six columns'),
    ]),
    html.Div(className='row', children=[
        html.Div(dcc.Graph(id='price-vs-rating-scatter'), className='twelve columns'),
    ]),
])

# ----------------------------------------------------------------------------------
# STAGE 5: DEFINE THE INTERACTIVITY (CALLBACKS)
# ----------------------------------------------------------------------------------
# A callback is a function that automatically runs whenever a user changes a filter.

# Callback 1: Update the City dropdown based on what State is selected
@app.callback(
    Output('city-filter', 'options'),
    Input('state-filter', 'value')
)
def set_cities_options(selected_states):
    if not selected_states:
        return []
    filtered_df = df[df['State'].isin(selected_states)]
    return [{'label': i, 'value': i} for i in sorted(filtered_df['City'].unique())]

# Callback 2: Update all three charts based on ALL filters
@app.callback(
    Output('restaurants-by-city-bar', 'figure'),
    Output('top-cuisines-pie', 'figure'),
    Output('price-vs-rating-scatter', 'figure'),
    Input('state-filter', 'value'),
    Input('city-filter', 'value'),
    Input('cuisine-filter', 'value'),
    Input('price-slider', 'value')
)
def update_graphs(selected_states, selected_cities, selected_cuisines, price_range):
    # If no filters are selected, start with the full dataset
    if not selected_states and not selected_cities and not selected_cuisines:
        filtered_df = df.copy()
    else:
        # Filter down the data based on user selections
        filtered_df = df[
            (df['Price'] >= price_range[0]) &
            (df['Price'] <= price_range[1])
        ]
        if selected_states:
            filtered_df = filtered_df[filtered_df['State'].isin(selected_states)]
        if selected_cities:
            filtered_df = filtered_df[filtered_df['City'].isin(selected_cities)]
        if selected_cuisines:
            mask = filtered_df['Food type'].apply(lambda x: any(cuisine in x for cuisine in selected_cuisines))
            filtered_df = filtered_df[mask]

    # --- Create the figures ---
    # Bar Chart
    city_counts = filtered_df['City'].value_counts().nlargest(10).reset_index()
    bar_fig = px.bar(city_counts, x='index', y='City', title='Top 10 Cities by Restaurant Count', labels={'index': 'City', 'City': 'Number of Restaurants'})

    # Pie Chart
    cuisine_counts = filtered_df['Food type'].str.split(', ').explode().str.strip().value_counts().nlargest(10)
    pie_fig = px.pie(cuisine_counts, values=cuisine_counts.values, names=cuisine_counts.index, title='Top 10 Most Common Cuisines')

    # Scatter Plot
    scatter_fig = px.scatter(
        filtered_df, x='Price', y='Avg ratings', title='Price vs. Average Rating',
        hover_name='Restaurant', color='Avg ratings',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    return bar_fig, pie_fig, scatter_fig

# ----------------------------------------------------------------------------------
# STAGE 6: RUN THE APP
# ----------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
