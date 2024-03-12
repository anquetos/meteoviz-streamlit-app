parameters_dict = {
    'validity_time': {
        'description': 'Date et heure de la mesure',
        'conversion': lambda x: x,
    },
    't': {
        'category': 'Température',
        'description': 'Température de l\'air à 2 mètres au-dessus du sol',
        'label': 'T',
        'unit': '°C',
        'conversion': lambda x: round(x - 273, 1),
        'plot_type': 'area'
    },
    'u': {
        'category': 'Humidité',
        'description': 'Humidité relative à 2 mètres au-dessus du sol',
        'label': 'HR',
        'unit': '%',
        'conversion': lambda x: x,
        'plot_type': 'line'
    },
    'ff': {
        'category': 'Vent',
        'description': 'Vitesse moyenne du vent à 10 mètres au-dessus du sol',
        'label': 'Vmoy',
        'unit': 'km/h',
        'conversion': lambda x: round(x * 3.6, 0),
        'plot_type': 'line'
    },
    'rr_per': {
        'category': 'Précipitations',
        'description': 'Précipitations cumulées',
        'label': 'Hauteur',
        'unit': 'mm',
        'conversion': lambda x: x,
        'plot_type': 'bar'
    },
    'rr1': {
        'category': 'Précipitations',
        'description': 'Précipitations cumulées',
        'label': 'Hauteur',
        'unit': 'mm',
        'conversion': lambda x: x,
        'plot_type': 'bar'
    },
    'vv': {
        'category': 'Visibilité',
        'description': 'Visibilité horizontale',
        'label': 'Distance',
        'unit': 'km',
        'conversion': lambda x: round(x / 1000, 1),
        'plot_type': 'line'
    },
    'sss': {
        'category': 'Neige',
        'description': 'Hauteur totale de la couverture de neige',
        'label': 'Hauteur',
        'unit': 'cm',
        'conversion': lambda x: round(x / 100, 0),
        'plot_type': 'bar'
    },
    'insolh': {
        'category': 'Soleil',
        'description': 'Durée d\'ensoleillement',
        'label': 'Durée',
        'unit': 'min',
        'conversion': lambda x: x,
        'plot_type': 'bar'
    },
    'pmer': {
        'category': 'Pression',
        'description': 'Pression atmosphérique au niveau de la mer',
        'label': 'Pmer',
        'unit': 'hPa',
        'conversion': lambda x: round(x / 100, 1),
        'plot_type': 'line'
    }
}
