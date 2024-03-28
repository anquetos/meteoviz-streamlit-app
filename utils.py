from io import StringIO
from pathlib import Path
import math

import requests
import pandas as pd
from geopy import distance

from meteo_france import Client
import constants
from weather_parameters import obs_parameters_dict, hourly_clim_parameters_dict

WEATHER_STATION_LIST_PATH = 'datasets/weather-stations-list.csv'


# --- NEW functions

def load_weather_stations_list() -> pd.DataFrame:
    df = pd.read_csv(WEATHER_STATION_LIST_PATH, sep=';', dtype={'Id_station': object},
                     parse_dates=['Date_ouverture'])

    df.columns = df.columns.str.lower()
    df['nom_usuel'] = df['nom_usuel'].str.title()

    return df


def observation_data_to_df(data: dict, id_station: str) -> pd.DataFrame:
    df = pd.json_normalize(data)

    # Filter rows with desired 'id_station'
    df = df.loc[df['geo_id_insee'] == id_station]

    # Subset the DataFrame with desired weather parameters
    df = df[[key for key in obs_parameters_dict.keys() if key in df.columns]]

    # Convert 'validity_time' to local datetime
    df['validity_time'] = pd.to_datetime(df['validity_time'], format='%Y-%m-%dT%H:%M:%SZ', utc=True)
    df['validity_time'] = df['validity_time'].dt.tz_convert('Europe/Paris')

    # Drop columns with only 'None' value
    df = df.dropna(axis='columns', how='all')

    # Convert unit of numerical values
    for column in df.select_dtypes(include='number').columns:
        conversion = obs_parameters_dict[column].get('conversion')
        df[column] = df[column].apply(conversion)

    return df


def climatological_data_to_df(data: str) -> pd.DataFrame:
    # Import data in a DataFrame
    df = pd.read_csv(StringIO(data), sep=';', dtype={'POSTE': 'string'})

    if 'DATE' not in df.columns:
        return pd.DataFrame()

    # Subset the DataFrame with desired weather parameters
    df = df[[key for key in hourly_clim_parameters_dict.keys() if key in df.columns]]

    # Convert 'DATE' to local datetime
    df['DATE'] = pd.to_datetime(df['DATE'], format='%Y%m%d%H', utc=True)
    # df['DATE'] = df['DATE'].dt.tz_convert('Europe/Paris')

    # Drop columns with only 'None' value
    df = df.dropna(axis='columns', how='all')

    # Convert 'object' data to 'float'
    string_col = df.select_dtypes(include=['object']).columns
    for col in string_col:
        df[col] = df[col].str.replace(',', '.')
        df[col] = df[col].astype('float')

    # Convert unit of numerical values
    # for column in df.select_dtypes(include='number').columns:
    #     conversion = hourly_clim_parameters_dict[column].get('conversion')
    #     df[column] = df[column].apply(conversion)

    return df


# ---
# #####################################################################"""

def download_station_list_to_csv():
    """Download in csv the stations list requested from Météo France API."""
    # Set folder and filename
    DATASETS_FOLDER = 'datasets'
    FILENAME = 'weather-stations-list.csv'

    client = Client()
    r = client.get_stations_list()

    if r.status_code == requests.codes.ok:
        # Generate the csv filepath
        p = Path(__file__).parent.absolute()
        q = p / DATASETS_FOLDER
        Path(q).mkdir(parents=True, exist_ok=True)
        csv_filepath = q / FILENAME

        # Write response text to the csv file
        with open(csv_filepath, 'w', encoding='utf-8') as f:
            f.write(r.text)

        print('Création du fichier réalisée avec succès.')
    else:
        print(f'Erreur : status_code {r.status_code} - {r.reason}')


# def search_city(query: str) -> requests.Response:
#     """Search for an adresse with the Adresse API.
#
#     Args:
#         query (str): searched city.
#
#     Returns:
#         requests.Response: response from the API.
#     """
#     r = requests.get(
#     constants.ADRESS_SEARCH_URL,
#     params={
#         'q': query,
#         'type': 'municipality',
#         'limit': 5,
#         'autocomplete': 0
#     }
# )
#
#     return r
#
#
# def _reverse_search_city(lat_lon: list) -> requests.Response:
#     """search a city from its coordinates.
#
#     Args:
#         lat_lon (list): city coordinates.
#
#     Returns:
#         requests.Response: response from the API or an empty list if no result
#         found.
#     """
#     lat = lat_lon[0]
#     lon = lat_lon[1]
#     x = len(str(lat))
#
#     while x > 0:
#         url = constants.REVERSE_ADRESS_URL
#         payload = {
#             'lon': lon,
#             'lat': str(lat)[:x],
#             'type': 'street',
#             'limit': 1
#         }
#         r = requests.get(url, params=payload)
#
#         if r.json().get('features'):
#                 return r.json().get('features')[0]
#         else:
#             x -= 1
#
#     return r.json().get('features')
#

def _get_nearest_station_information(lat_lon: list) -> dict:
    """Get information for the nearest observation station calculated with
    geodesic distance.

    Args:
        lat_lon (list): coordinates to calculate distance from. 

    Returns:
        dict: nearest station information.
    """
    df = pd.read_csv(
        constants.WEATHER_STATION_LIST_PATH,
        sep=';',
        dtype={'Id_station': object},
        parse_dates=['Date_ouverture']
    )

    df.columns = df.columns.str.lower()
    df['nom_usuel'] = df['nom_usuel'].str.title()

    if ('latitude' and 'longitude' in df.columns) and lat_lon:
        df['distance'] = df.apply(
            lambda x: distance.distance(
                [x['latitude'], x['longitude']],
                lat_lon).km,
            axis='columns'
        )

        return df.nsmallest(1, 'distance').to_dict('records')[0]


def filter_nearest_station_information(lat_lon: list) -> dict:
    """Get and filter information for the nearest station to only provide
    what is useful for the STreamlit app.

    Args:
        lat_lon (list): city coordinates.

    Returns:
        dict: nearest station information.
    """
    station_info = _get_nearest_station_information(lat_lon)

    reverse_info = _reverse_search_city([station_info['latitude'],
                                         station_info['longitude']])

    if not reverse_info:
        reverse_info = {'properties': {'city': '-', 'context': '-'}}

    return {
        'id_station': station_info.get('id_station'),
        'nom_usuel': station_info.get('nom_usuel'),
        'date_ouverture': station_info.get('date_ouverture'),
        'altitude': station_info.get('altitude'),
        'distance': station_info.get('distance'),
        'city': reverse_info.get('properties').get('city'),
        'context': reverse_info.get('properties').get('context')
    }


def calculate_delta(x: float, y: float, rel_tol: float) -> float:
    """Calculates the difference between two numbers.

    Args:
        x (float): first number ;
        y (float): second number ;
        rel_tol (float): maximum difference for being considered 'close', 
        relative to the magnitude of the input values.

    Returns:
        float: delta
    """
    if x is None or y is None:
        return None

    # Check if delta is close to 0
    if math.isclose(x, y, rel_tol=rel_tol):
        return None

    return x - y


def main():
    pass


if __name__ == '__main__':
    main()
