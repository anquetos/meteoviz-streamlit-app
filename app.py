from io import StringIO
from datetime import datetime, timedelta, date, time
from zoneinfo import ZoneInfo
import json
from time import sleep

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px

import constants
import utils
from meteo_france import Client

# -- Application functions

@st.cache_data
def import_api_daily_parameters() -> pd.DataFrame:
    """Import climatological api parameters in a DataFrame"""
    df = pd.read_csv('datasets/api-clim-table-parametres-quotidiens.csv',
                     sep=';')

    return df


@st.cache_data(max_entries=5)
def get_station_info(coordinates: list[float]) -> dict:
    """Call function with cache decorator to retrieve nearest observation
    station information.

    Args:
        coordinates (list[float]): nearest station latitude and longitude.

    Returns:
        dict: station information
    """

    return utils.filter_nearest_station_information(coordinates)


@st.cache_data(ttl=timedelta(minutes=20))
def get_observation(id_station: str) -> tuple[dict]:
    """Call function with cache decorator to get current hourly observation and
    the one an hour before.

    Args:
        id_station (str): id of nearest observation station.

    Returns:
        tuple[dict]: observations.
    """
    
    # Get current available observation
    current_response = Client().get_hourly_observation(
        id_station, '')
    
    if current_response.status_code == requests.codes.ok:
        try:
            # Convert response to dictionnary
            current_observation = current_response.json()[0]
            # Calculate the previous validity time
            previous_validity_time = (
                datetime.strptime(current_observation.get('validity_time'), constants.DATETIME_FORMAT)
                - timedelta(hours=1)
            ).strftime(constants.DATETIME_FORMAT)
        except json.JSONDecodeError:
            raise Exception('Erreur de décodage de la réponse JSON.')
    else:
        raise Exception(
            f'''Echec de la récupération des données.  
            {current_response.status_code} : {current_response.reason}
            ''')

    # Get the previous observation before the last one available
    previous_response = Client().get_hourly_observation(
        id_station, previous_validity_time)
    
    if previous_response.status_code == requests.codes.ok:
        try:
            # Convert response to dictionnary
            previous_observation = previous_response.json()[0]
        except json.JSONDecodeError:
            raise Exception('Erreur de décodage de la réponse JSON.')
    else:
        raise Exception(
            f'''Echec de la récupération des données.  
            {current_response.status_code} : {current_response.reason}
            ''')

    return current_observation, previous_observation

    
@st.cache_data(max_entries=3)
def get_other_date_observation(id_station: str, requested_date: date, requested_time: time) -> dict:
    """"Call function with cache decorator to get hourly observation and
    the one an hour before at another date and time than the current one.

    Args:
        id_station (str): id of nearest observation station ;
        requested_date (date): date of requested data ;
        requested_time (time): time of requested data.

    Returns:
        dict: observations.
    """

    # Set datetimes for the api requests
    other_datetime_end = datetime.combine(
        requested_date, requested_time, tzinfo=ZoneInfo('Europe/Paris'))
    other_datetime_end_utc = other_datetime_end.astimezone(tz=ZoneInfo('UTC'))
    other_datetime_start_utc = other_datetime_end_utc - timedelta(hours=1)

    # Get order id from the api
    other_date_order_response = Client().order_hourly_climatological_data(
        id_station,
        other_datetime_start_utc.strftime(constants.DATETIME_FORMAT),
        other_datetime_end_utc.strftime(constants.DATETIME_FORMAT)
    )
    if other_date_order_response.status_code == 202:
        try:
            other_date_order_id = (
                other_date_order_response
                .json() 
                .get('elaboreProduitAvecDemandeResponse')
                .get('return')
            )
        except json.JSONDecodeError:
            raise Exception('Erreur de décodage de la réponse JSON.')
    else:
        raise Exception(
            f'''Echec de la récupération des données.  
            {other_date_order_response.status_code} : {other_date_order_response.reason}
            ''')

    # Get data from order id and retry if data not yet ready (code 204)
    response_code = 204
    n_tries = 0
    while response_code == 204 and n_tries < 5:
        other_date_climatological_response = Client().order_recovery(
            other_date_order_id)
        response_code = other_date_climatological_response.status_code
        n_tries =+ 1
        sleep(10)
    
    if other_date_climatological_response.status_code == 201:
        try:
            other_date_climatological_data = other_date_climatological_response.text
            # Import data in a DataFrame
            df = pd.read_csv(
                StringIO(other_date_climatological_data), sep=';')
            # Convert 'object' data to 'float'
            string_col = df.select_dtypes(include=['object']).columns
            for col in string_col:
                df[col] = df[col].str.replace(',', '.')
                df[col] = df[col].astype('float')
            # Replace Pandas 'NaN' with 'None'
            df = df.replace(np.nan, None)
            # Set index with 'previous' and 'current' label
            df['OBS'] = ['previous_observation', 'current_observation']
            df = df.set_index('OBS')
        except Exception as e:
            f'Echec lors de la lecture de la réponse : {e}.'
    else:
        raise Exception(
            f'''Echec de la récupération des données.  
            {other_date_climatological_response.status_code} : {other_date_climatological_response.reason}
            ''')
        
    return df.to_dict('index') 

       
@st.cache_data(max_entries=3)
def get_year_climatological_data(id_station: str, year: int) -> pd.DataFrame:
    """Call function with cache decorator to get climatological data for a full
    year.

    Args:
        id_station (str): id of nearest observation station ;
        year (int): year of requested data.

    Returns:
        pd.DataFrame: climatological data.
    """
    if year == st.session_state.nearest_station_info.get('date_ouverture').year:
        start_date = f'''{st.session_state.nearest_station_info.get('date_ouverture')}T00:00:00Z'''
    else:
        start_date = f'{year}-01-01T00:00:00Z'
    # Define the end datetime (if selected year is the current year we probably
    # can't end the period at end of December)
    if year == datetime.now().year:
        end_date = (datetime.now()-timedelta(days=2)).strftime('%Y-%m-%dT00:00:00Z')
    else:
        end_date = f'{year}-12-31T00:00:00Z'

    # Get data from the api
    visualization_order_response = Client().order_daily_climatological_data(
        id_station, start_date, end_date)

    if visualization_order_response.status_code == 202:
        try:
            visualization_order_id = (
                visualization_order_response
                .json() 
                .get('elaboreProduitAvecDemandeResponse')
                .get('return')
            )
        except json.JSONDecodeError:
            raise Exception('Erreur de décodage de la réponse JSON.')
    else:
        raise Exception(
            f'''Echec de la récupération des données.  
            {visualization_order_response.status_code} : {visualization_order_response.reason}
            ''')

    # Get data from order id and retry if data not yet ready (code 204)
    response_code = 204
    n_tries = 0
    while response_code == 204 and n_tries < 5:
        visualization_climatological_response = Client().order_recovery(
                visualization_order_id)
        response_code = visualization_climatological_response.status_code
        n_tries =+ n_tries
        sleep(10)
    
    if visualization_climatological_response.status_code == 201:
        try:
            visualization_climatological_data = visualization_climatological_response.text

            # Import data in DataFrame
            df = pd.read_csv(StringIO(visualization_climatological_data), sep=';',
                            parse_dates=['DATE'])
            # Convert 'object' to 'float'
            string_col = df.select_dtypes(include=['object']).columns
            for col in string_col:
                df[col] = df[col].str.replace(',', '.')
                df[col] = df[col].astype('float')
            # Remove all variables with only NaN
            df =  df.dropna(axis='columns')
        except Exception as e:
            f'Echec lors de la lecture de la réponse : {e}.'
    else:
        raise Exception(
            f'''Echec de la récupération des données.  
            {visualization_climatological_data.status_code} : {visualization_climatological_data.reason}
            ''')

    return df


def api_parameters_in_selected_category(category: str) -> list:
    """List api parameters for selected category with radio button

    Args:
        category (str): category of variables.

    Returns:
        list: list of variables.
    """   
    return api_daily_parameters.loc[
        api_daily_parameters['parameter_category'] == category, 'parameter'
    ].tolist()


def filter_climatological_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Filter columns of all retrieved climatological data in order to keep
    only the columns which correspond to the variables in the selected
    category.

    Args:
        raw_data (pd.DataFrame): the DataFrame to filter.

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    if len(raw_data.index) != 0:
        cols_to_keep = (
            ['POSTE', 'DATE']
            + list(set(api_parameters_in_selected_category(
            st.session_state.selected_category_for_visualization
            ))
            .intersection(raw_data.columns))
        )

        return raw_data[cols_to_keep]


def describe_climatological_data(data: pd.DataFrame) -> pd.DataFrame:
    """Create descriptive statistics for climatological data.

    Args:
        data (pd.DataFrame): data to describe.

    Returns:
        pd.DataFrame: descriptive statistics.
    """
    df = data.iloc[:, 2:].describe().loc[['min', 'max', 'mean', '50%']]
    df = df.rename(index={'min': 'Minimum','max': 'Maximum','mean': 'Moyenne',
                          '50%': 'Médiane'})
    return df


# -- Set page config
st.set_page_config(page_title='MétéoViz', page_icon='🌤️',
                   initial_sidebar_state='expanded')

# -- Set application title
st.title('Visualisation de données météo')

# -- Application sidebar

with st.sidebar:

    st.markdown('## Sélectionnez une commune')

    st.text_input(
        label='Quelle commune cherchez-vous ?',
        placeholder='Saisissez votre recherche...',
        value='',
        key='city_search'
    )

    # Search for cities from the text input and list the results
    city_search_response = utils.search_city(st.session_state.city_search)
    if city_search_response.status_code == requests.codes.ok:
        city_search_options = []
        for _ in city_search_response.json().get('features'):
            city_search_options.append(
                {
                'label': _['properties']['label'],
                'context': _['properties']['context'],
                'coordinates': _['geometry']['coordinates'][::-1]
                }
            )
    else:
        city_search_options = []
        
    st.selectbox(
        label='Faites votre choix',
        options=city_search_options,
        index=None,
        format_func=lambda x: f'''{x['label']} ({x['context'].split(',')[0]})''',
        key='selected_city',
        placeholder='Sélectionnez un résultat...'
    )

    def del_searched_and_selected_city():
        """Remove search and selected city from session state and clear cache."""
        st.session_state.city_search = ''
        st.session_state.selected_city = None
    
    st.button('Effacer', on_click=del_searched_and_selected_city)
    
    if st.session_state.selected_city:
        st.markdown('## Station météo la plus proche')

        st.session_state.nearest_station_info = get_station_info(
            st.session_state.selected_city.get('coordinates'))

        # Display nearest station information in expander
        with st.expander(
            f'''{st.session_state.nearest_station_info.get('nom_usuel')} '''
            f'''({st.session_state.nearest_station_info.get('city')}, '''
            f'''{st.session_state.nearest_station_info.get('context')})'''
        ):

            nearest_station_text = f'''
                * id : {st.session_state.nearest_station_info.get('id_station')}
                * Altitude : {st.session_state.nearest_station_info.get('altitude')} m
                * Distance de {st.session_state.selected_city.get('label')} : 
                {st.session_state.nearest_station_info.get('distance'):.1f} km
                * Date d'ouverture : {
                    st.session_state.nearest_station_info.get('date_ouverture'):%d/%m/%Y}
            '''

            st.markdown(nearest_station_text)

    if 'selected_category_for_visualization' not in st.session_state:
        st.session_state.selected_category_for_visualization = []

    if st.session_state.selected_category_for_visualization:
        st.markdown('## Définition des variables')

        api_daily_parameters = import_api_daily_parameters()

        parameters_list = api_parameters_in_selected_category(
            st.session_state.selected_category_for_visualization
        )

        text = ''
        for row in api_daily_parameters.loc[
            api_daily_parameters['parameter'].isin(parameters_list)
        ].itertuples():
            parameter_text = f'* **{row.parameter} ({row.unit})** : {row.label.lower()}\n'
            text = text + parameter_text

        with st.expander('Afficher les définitions', expanded=True):
            st.markdown(text)
    
# -- Application main page

if st.session_state.selected_city:

    # -- Display current observation section

    st.subheader('Observations en temps réel')

    try:
        # Get observation data
        current_observation, previous_observation = get_observation(
            st.session_state.nearest_station_info.get('id_station'))
    except Exception as e:
        st.error(f'''☔ Une erreur est apparue !  
                {str(e)}
        ''')
        st.stop()


    # Layout observation in metric widgets
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            c = current_observation.get('t')
            d = utils.calculate_delta(
                current_observation.get('t'), previous_observation.get('t'), 0)
            st.metric(
                label='Température',
                value=(f'{(c-273):.1f} °C') if c is not None else None,
                delta=(f'{d:.1f} °C') if d is not None else None
            )
        with col2:
            c = current_observation.get('u')
            d = utils.calculate_delta(
                current_observation.get('u'), previous_observation.get('u'), 0)
            st.metric(
                label='Humidité',
                value=(f'{c} %') if c is not None else None,
                delta=(f'{d} %') if d is not None else None
            )
        with col3:
            c = current_observation.get('ff')
            d = utils.calculate_delta(
                current_observation.get('ff'), previous_observation.get('ff'), 0)
            st.metric(
                label='Vent',
                value=(f'{(c*3.6):.0f} km/h') if c is not None else None,
                delta=(f'{(d*3.6):.0f} km/h') if d is not None else None
            )
        with col4:
            c = current_observation.get('rr1')
            d = utils.calculate_delta(
                current_observation.get('rr1'), previous_observation.get('rr1'), 0)
            st.metric(
                label='Précipitations 1h',
                value=(f'{c:.1f} mm') if c is not None else None,
                delta=(f'{d:.1f} mm') if d is not None else None
            )

        col5, col6, col7, col8 = st.columns(4)
        with col5:
            c = current_observation.get('vv')
            d = utils.calculate_delta(
                current_observation.get('vv'), previous_observation.get('vv'), 0)
            st.metric(
                label='Visibilité',
                value=(f'{(c/1000):.1f} km') if c is not None else None,
                delta=(f'{(d/1000):.1f} km') if d is not None else None
            )
        with col6:
            c = current_observation.get('sss')
            d = utils.calculate_delta(
                current_observation.get('sss'), previous_observation.get('sss'), 0)
            st.metric(
                label='Neige',
                value=(f'{(c*100):.0f} cm') if c is not None else None,
                delta=(f'{(d*100):.0f} cm') if d is not None else None
            )
        with col7:
            c = current_observation.get('insolh')
            d = utils.calculate_delta(
                current_observation.get('insolh'), previous_observation.get('insolh'), 0)
            st.metric(
                label='Ensoleillement',
                value=(f'{c} min') if c is not None else None,
                delta=(f'{d} min') if d is not None else None
            )
        with col8:
            c = current_observation.get('pres')
            d = utils.calculate_delta(
                current_observation.get('pres'), previous_observation.get('pres'), 0.1)
            st.metric(
                label='Pression',
                value=(f'{(c/100):.0f} hPa') if c is not None else None,
                delta=(f'{(d/100):.0f} hPa') if d is not None else None
            )
        
        if 'validity_time' in current_observation:
            observation_datetime_utc = datetime.strptime(
                current_observation.get('validity_time'),
                constants.DATETIME_FORMAT
            ).replace(tzinfo=ZoneInfo('UTC'))
            st.caption(
                f'''📅 {observation_datetime_utc.astimezone(tz=ZoneInfo('Europe/Paris'))}''')

    # -- Display observation at another date section

    st.subheader('Observations à une date antérieure')

    # Layout requested date and time of observation in form widget
    with st.form('other_date'):
        st.write('''
            **Remontez le temps** et afficher le relevé de la station 
            d'observation **à une date antérieure**.
        ''')

        # Set date and time limit for the selection
        now = datetime.now()
        now_utc = datetime.now().astimezone(tz=ZoneInfo('UTC'))

        if now_utc.time() < time(11, 45, 0):
            max_date_value = now_utc.date() - timedelta(days=1)
            date_value = max_date_value
        else:
            max_date_value = now_utc.date()
            date_value = max_date_value

        time_limit = (
        datetime(2023, 1, 1, 5, 0, 0, tzinfo=ZoneInfo('UTC'))
        .astimezone(ZoneInfo('Europe/Paris'))
        .time()
        )

        # Layout date and time selection in date and time input widgets
        col9, col10 = st.columns(2)
        with col9:
            st.date_input(
                label='Précisez une date...',
                value=date_value,
                max_value=max_date_value,
                key='other_date_selected',
                format='DD/MM/YYYY'
            )
        with col10:
            st.time_input(
                label='...et une heure',
                value=time_limit,
                step=3600,
                key='other_time_selected'
            )

        other_date_validated = st.form_submit_button('Afficher les observations')


    if other_date_validated:

        def check_datetime_limit():
            """Check if selected date and time respect Météo France api rules"""
            return ((st.session_state.other_date_selected == max_date_value) 
                    and (st.session_state.other_time_selected > time_limit))

        # Get observation data
        if not check_datetime_limit():
            try:
                dict_other_date = get_other_date_observation(
                    st.session_state.nearest_station_info.get('id_station'),
                    st.session_state.other_date_selected,
                    st.session_state.other_time_selected
                )
            except Exception as e:
                st.error(f'''☔ Une erreur est apparue !  
                        {str(e)}
                ''')
                st.stop()

            if dict_other_date:
                # Layout observation in metric widgets
                with st.container(border=True):
                    col11, col12, col13, col14 = st.columns(4)
                    with col11:
                        c = dict_other_date.get('current_observation').get('T')
                        d = utils.calculate_delta(
                            dict_other_date.get('current_observation').get('T'),
                            dict_other_date.get('previous_observation').get('T'),
                            0
                        )
                        st.metric(
                            label='Température',
                            value=(f'{(c):.1f} °C') if c is not None else None,
                            delta=(f'{d:.1f} °C') if d is not None else None
                        )
                    with col12:
                        c = dict_other_date.get('current_observation').get('U')
                        d = utils.calculate_delta(
                            dict_other_date.get('current_observation').get('U'), 
                            dict_other_date.get('previous_observation').get('U'),
                            0
                        )
                        st.metric(
                            label='Humidité',
                            value=(f'{c} %') if c is not None else None,
                            delta=(f'{d} %') if d is not None else None
                        )
                    with col13:
                        c = dict_other_date.get('current_observation').get('FF')
                        d = utils.calculate_delta(
                            dict_other_date.get('current_observation').get('FF'),
                            dict_other_date.get('previous_observation').get('FF'),
                            0
                        )
                        st.metric(
                            label='Vent',
                            value=(f'{(c*3.6):.0f} km/h') if c is not None else None,
                            delta=(f'{(d*3.6):.0f} km/h') if d is not None else None
                        )
                    with col14:
                        c = dict_other_date.get('current_observation').get('RR1')
                        d = utils.calculate_delta(
                            dict_other_date.get('current_observation').get('RR1'),
                            dict_other_date.get('previous_observation').get('RR1'),
                            0
                        )
                        st.metric(
                            label='Précipitations 1h',
                            value=(f'{c:.1f} mm') if c is not None else None,
                            delta=(f'{d:.1f} mm') if d is not None else None
                        )

                    col15, col16, col17, col18 = st.columns(4)
                    with col15:
                        c = dict_other_date.get('current_observation').get('VV')
                        d = utils.calculate_delta(
                            dict_other_date.get('current_observation').get('VV'),
                            dict_other_date.get('previous_observation').get('VV'),
                            0
                        )
                        st.metric(
                            label='Visibilité',
                            value=(f'{(c/1000):.1f} km') if c is not None else None,
                            delta=(f'{(d/1000):.1f} km') if d is not None else None
                        )
                    with col16:
                        c = dict_other_date.get('current_observation').get('NEIGETOT')
                        d = utils.calculate_delta(
                            dict_other_date.get('current_observation').get('NEIGETOT'),
                            dict_other_date.get('previous_observation').get('NEIGETOT'),
                            0
                        )
                        st.metric(
                            label='Neige',
                            value=(f'{(c*100):.0f} cm') if c is not None else None,
                            delta=(f'{(d*100):.0f} cm') if d is not None else None
                        )
                    with col17:
                        c = dict_other_date.get('current_observation').get('INS')
                        d = utils.calculate_delta(
                            dict_other_date.get('current_observation').get('INS'),
                            dict_other_date.get('previous_observation').get('INS'),
                            0
                        )
                        st.metric(
                            label='Ensoleillement',
                            value=(f'{c} min') if c is not None else None,
                            delta=(f'{d} min') if d is not None else None
                        )
                    with col18:
                        c = dict_other_date.get('current_observation').get('PSTAT')
                        d = utils.calculate_delta(
                            dict_other_date.get('current_observation').get('PSTAT'),
                            dict_other_date.get('previous_observation').get('PSTAT'),
                            0.1
                        )
                        st.metric(
                            label='Pression',
                            value=(f'{(c):.0f} hPa') if c is not None else None,
                            delta=(f'{(d):.0f} hPa') if d is not None else None
                        )

        else:
            st.warning(f'⏲️ L\'heure sélectionnée est trop récente : elle ne peut '
                       f'pas dépasser {time_limit:%Hh%M}.')
            
    else:
        st.info(f'👆 Pour afficher les observations désirées, validez votre '
                f'choix en cliquant sur le bouton ci-dessus.')

    # -- Display yearly evolution and statistics section
        
    st.subheader('Evolution annuelle et statistiques')

    # Layout year selection
    with st.container(border=True):
        st.write('''Visualisez **l'évolution** des **variables** pour 
                 **l'année** de votre choix.''')
        
        # List years from the station opening until now
        select_year_options = list(
            range(
                st.session_state.nearest_station_info.get('date_ouverture').year,
                (datetime.now().year+1),
                1
            )
        )

        if 'climatological_data' not in st.session_state:
            st.session_state.climatological_data = pd.DataFrame()
    
        def clear_visualization_data():
            """Clear the DataFrame used for visualization, clear the selected 
            category and change button state each time the year changes."""
            st.session_state.climatological_data = pd.DataFrame()
            st.session_state.visualization_button_clicked = False
            st.session_state.selected_category_for_visualization = []

        # Layout year selection in widget
        st.selectbox(
            label='Sélectionnez une année',
            options=select_year_options[::-1],
            index=1,
            on_change=clear_visualization_data,
            key='year_for_visualization'
        )

        if 'visualization_button_clicked' not in st.session_state:
            st.session_state.visualization_button_clicked = False

        def click_visualization_button():
            st.session_state.visualization_button_clicked = True

        st.button('Récupérer les données', on_click=click_visualization_button)

    # Get data for selected year
    if st.session_state.visualization_button_clicked:
        try:
            st.session_state.climatological_data = get_year_climatological_data(
                st.session_state.nearest_station_info.get('id_station'),
                st.session_state.year_for_visualization
            )
        except Exception as e:
            st.error(f'''☔ Une erreur est apparue !  
                    {str(e)}
            ''')
            st.stop()

        # Layout category of variables selection in radio widget
        st.radio(
            label='Quelle catégorie de variables souhaitez-vous visualiser ?',
            options=['Température', 'Humidité', 'Vent', 'Précipitations',
                    'Ensoleillement', 'Neige'],
            index=None,
            horizontal=True,
            key='selected_category_for_visualization'
        )

    else:
        st.info(f'👆 Pour visualiser les données, cliquez d\'abord sur le '
                'bouton ci-dessus pour les récupérer.')

    # Initialize and prepare data to plot
    data_to_plot = pd.DataFrame()

    if st.session_state.selected_category_for_visualization:
        data_to_plot = filter_climatological_data(st.session_state.climatological_data)

        
    if len(data_to_plot.columns) > 2 and not (data_to_plot.iloc[:, 2:] == 0).all().all():

        # -- Display yearly evolution in plotly widget

        st.markdown('#### Evolution annuelle')

        # Set type of plot for each category of parameters
        plot_type_per_category = {
            'Vent': 'line',
            'Ensoleillement': 'bar',
            'Neige': 'bar',
            'Précipitations': 'bar',
            'Température': 'line',
            'Humidité': 'line'
        }

        # Plot evolution in line or bar plot
        if plot_type_per_category[st.session_state.selected_category_for_visualization] == 'line':
            fig = px.line(
                data_to_plot,
                x='DATE',
                y=data_to_plot.iloc[:, 2:].columns,
                labels={'DATE': 'Date', 'value': 'Valeur', 'variable': 'Variable(s)'}
            )
        if plot_type_per_category[st.session_state.selected_category_for_visualization] == 'bar':
            fig = px.bar(
                data_to_plot,
                x='DATE',
                y=data_to_plot.iloc[:, 2:].columns,
                labels={'DATE': 'Date', 'value': 'Valeur', 'variable': 'Variable(s)'}
            )
        fig.update_layout(legend=dict(x=0, y=1.15, orientation='h'))

        if len(fig.data) != 0:
            st.plotly_chart(fig)

        # -- Display description of data in DataFrame widget

        st.markdown('#### Statistiques descriptives')

        st.dataframe(
            describe_climatological_data(data_to_plot).style.format(precision=1),
            use_container_width=True
        )

        # -- Display data histogram in plotly widget

        st.markdown('#### Distribution des variables')

        fig = px.histogram(
            data_to_plot,
            x=data_to_plot.iloc[:, 2:].columns,
            labels={'value': 'Valeur', 'variable': 'Variable(s)'}
        )

        fig.update_layout(yaxis=dict(title='Fréquence'))
        fig.update_layout(legend=dict(x=0, y=1.15, orientation='h'))
        
        st.plotly_chart(fig)

        # -- Display data histogram in plotly widget

        st.markdown('#### Dispersion des variables')

        fig = px.box(
            data_to_plot,
            x=data_to_plot.iloc[:, 2:].columns,
            labels={'value': 'Valeur', 'variable': 'Variable(s)'}
        )

        st.plotly_chart(fig)

    elif st.session_state.selected_category_for_visualization:
        st.info(
            f'Les données de **« {st.session_state.selected_category_for_visualization} »** '
            f'ne sont pas disponibles pour l\'année  **{st.session_state.year_for_visualization}**. '
            f'Sélectionnez une autre année et/ou une autre catégorie.'
        )
                
else:
    st.info('''
        ### 📢 Aucune commune n'est sélectionnée !
        Pour afficher les informations et les relevés d\'une station 
        d\'observation, commencez par **sélectionner une commune**. 
            
        Pour cela, utilisez la **zone de recherche** située dans le **menu 
        latéral** puis **faites votre choix** parmi les **résultats proposés**.
    ''')

# -- Display 'about' section

st.subheader('A propos de l\'application')

st.markdown('''
    L' application MétéoViz permet d\'afficher les **données publiques d\'observation 
    ou de climatologie pour la France** à partir des API de Météo France.
''')

st.caption('''
    Auteur : T. Anquetil ([GitHub](https://github.com/anquetos) & 
           [LinkedIn](https://www.linkedin.com/in/thomas-anquetil-132a73123)) 
           · Février 2024
''')