"""Constants needed for the modules and the Streamlit application"""

# Météo France apis
TOKEN_URL = 'https://portail-api.meteofrance.fr/token'
STATION_LIST_URL = 'https://public-api.meteofrance.fr/public/DPObs/v1/liste-stations'
HOURLY_OBSERVATION_URL = 'https://public-api.meteofrance.fr/public/DPObs/v1/station/horaire'
ORDER_HOURLY_CLIMATOLOGICAL_URL = 'https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/horaire'
ORDER_DAILY_CLIMATOLOGICAL_URL = 'https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/quotidienne'
ORDER_RECOVERY_URL = 'https://public-api.meteofrance.fr/public/DPClim/v1/commande/fichier'

# Adresse apis
ADRESS_SEARCH_URL = 'https://api-adresse.data.gouv.fr/search/'
REVERSE_ADRESS_URL = 'https://api-adresse.data.gouv.fr/reverse/'

# Files
WEATHER_STATION_LIST_PATH = 'datasets/weather-stations-list.csv'

# Date and time format
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'