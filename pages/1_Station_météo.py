import folium
import streamlit as st
from streamlit_folium import st_folium
from geopy import distance

from utils import load_weather_stations_list


# -- Application functions

@st.cache_data(show_spinner=True)
def find_nearest_stations(coordinates: list[float], n_stations: int = 5) -> list[dict]:
    if not coordinates[0] and not coordinates[1]:
        return []

    df_stations = load_weather_stations_list()

    df_stations['distance_km'] = df_stations.apply(
        lambda x: round(
            distance.distance([x['latitude'], x['longitude']], coordinates).km, 0),
        axis='columns'
    )

    return (df_stations.nsmallest(n=n_stations, columns='distance_km')
            .to_dict(orient='records'))


def create_folium_map(coordinates: list[float] = None) -> folium.Map:
    if coordinates is None:
        coordinates = [46.227638, 2.213749]

    return folium.Map(location=coordinates,
                      zoom_start=5, tiles='GeoportailFrance_plan')


def create_selected_city_marker(coordinates: list[float]) -> folium.Marker:
    return folium.Marker(
        location=coordinates,
        popup=f'{st.session_state.selected_city["label"]}, {st.session_state.selected_city["context"]}',
        tooltip=st.session_state.selected_city['label'],
        icon=folium.Icon(icon='glyphicon-home', color='darkred', prefix='glyphicon')
    )


def create_stations_markers(station_dict: dict) -> folium.Marker:
    return folium.Marker(
        location=[station_dict['latitude'], station_dict['longitude']],
        popup=f'{station_dict["distance_km"]} km de {st.session_state.selected_city["label"]}',
        tooltip=f'Station : {station_dict["nom_usuel"]}',
        icon=folium.Icon(icon='glyphicon-star', color='green', prefix='glyphicon')
        if nearest_stations.index(station_dict) == 0
        else folium.Icon(icon='glyphicon-map-marker', color='blue', prefix='glyphicon')
    )


# -- Initialize variables

selected_city_coordinates = [
    st.session_state.selected_city['lat'],
    st.session_state.selected_city['lon']
]

nearest_stations = find_nearest_stations(selected_city_coordinates)

nearest_station = nearest_stations[0]

# -- Weather station page sidebar layout

with st.sidebar:
    if st.session_state['selected_city']:
        container = st.container(border=True)
        container.write(st.session_state['selected_city'].get('label'))
        container.write(st.session_state['selected_city'].get('context'))

# -- Weather station page layout

st.subheader('Stations d\'observation météorologique')

st.markdown(f'''
    La station ***{nearest_station['nom_usuel']}***
    est la plus proche de *{st.session_state.selected_city['label']}* 
    avec une distance de *{nearest_station['distance_km']} km*.  
    Cette station est sélectionnée par défaut, vous pouvez en choisir 
    une autre en bas de cette page.
''')

with st.expander(label='Informations détaillées', expanded=False):
    st.write(nearest_station)

# Initialize Folium map
m = create_folium_map(selected_city_coordinates)

# Add selected city marker
selected_city_marker = create_selected_city_marker(selected_city_coordinates)
selected_city_marker.add_to(m)

# Add nearest stations markers
for station in nearest_stations:
    station_marker = create_stations_markers(station)
    station_marker.add_to(m)

# Fit map bounds to nearest stations coordinates
m.fit_bounds(
    [[station['latitude'], station['longitude']] for station in nearest_stations])

# Render map
st_data = st_folium(m, width=725, height=350)

st.subheader('Choisir une autre station')

selected_station = st.selectbox(
    label='Autres stations',
    options=nearest_stations,
    format_func=lambda x: f'{x["nom_usuel"]} (distance : {x["distance_km"]} km)',
    label_visibility='collapsed')

st.session_state['selected_station'] = selected_station
