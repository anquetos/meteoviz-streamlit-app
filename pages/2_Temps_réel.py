import streamlit as st
import plotly.express as px

from weather_parameters import parameters_dict
from meteo_france import ObservationsPackages
from utils import prepare_api_data_for_plot

# df = pd.read_csv(
#     constants.WEATHER_STATION_LIST_PATH,
#     sep=';',
#     dtype={'Id_station': object},
#     parse_dates=['Date_ouverture']
# )

st.header('Observation en temps réel', divider='rainbow')

# id_station = st.selectbox('Id_station', df['Id_station'])

id_station = st.session_state['selected_station']['id_station']
st.write(id_station)

id_departement = int(id_station[:2])

obs = ObservationsPackages()
# obs_data = obs.every_six_minutes(id_station)
obs_data = obs.every_hour(id_departement)
obs_df = prepare_api_data_for_plot(obs_data, id_station)
obs_parameters = obs_df.select_dtypes(include='number').columns

st.subheader('Actuellement')

row1 = st.columns(3)
row2 = st.columns(3)
row3 = st.columns(3)

if len(obs_parameters) <= 3:
    rows = row1
elif len(obs_parameters) <= 6:
    rows = row1 + row2
else:
    rows = row1 + row2 + row3

for i, col in enumerate(rows):
    if i < len(obs_parameters):
        parameter = obs_parameters[i]
        unit = parameters_dict[parameter].get('unit')
        value = f'{obs_df[parameter].values[0]} '
        delta = round(obs_df[parameter].values[0] - obs_df[parameter].values[1], 1)
        tile = col.container(height=130)
        tile.metric(
            label=parameters_dict[parameter].get('category'),
            value=f'{value} {unit}',
            delta=f'{delta} {unit}' if delta != 0 else None
        )
    else:
        tile = col.container(height=130, border=False)

st.subheader('Dernières 24 h')

for column in obs_parameters:
    if parameters_dict[column].get('plot_type') == 'line':
        fig = px.line(obs_df, x='validity_time', y=column)
    elif parameters_dict[column].get('plot_type') == 'bar':
        fig = px.bar(obs_df, x='validity_time', y=column)
        fig.update_yaxes(rangemode='tozero')
    elif parameters_dict[column].get('plot_type') == 'area':
        fig = px.area(obs_df, x='validity_time', y=column)
    else:
        break

    description = parameters_dict[column].get('description')
    label = parameters_dict[column].get('label')
    unit = parameters_dict[column].get('unit')

    fig.update_layout(
        title_text=description,
        xaxis_title='',
        yaxis_title=f'{label} ({unit})',
        margin=dict(b=0),
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)
