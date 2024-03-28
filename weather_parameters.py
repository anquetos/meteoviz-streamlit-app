obs_parameters_dict = {
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
        'plot_type': 'line'
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

daily_clim_parameters_dict = {
    'DATE': {
            'description': 'Date de l\'enregistrement',
            'conversion': lambda x: x,
        },
    'TM': {
        'category': 'Température',
        'description': 'Température moyenne sous abri quotidienne',
        'label': 'T',
        'unit': '°C',
        'conversion': lambda x: round(x - 273, 1),
        'plot_type': 'line'
    },
    'UM': {
        'category': 'Humidité',
        'description': 'Humidité relative moyenne quotidienne',
        'label': 'HR',
        'unit': '%',
        'conversion': lambda x: x,
        'plot_type': 'line'
    },
    'FFM': {
        'category': 'Vent',
        'description': 'Moyenne des vitesses du vent quotidienne',
        'label': 'Vmoy',
        'unit': 'km/h',
        'conversion': lambda x: round(x * 3.6, 0),
        'plot_type': 'line'
    },
    'RR': {
        'category': 'Précipitations',
        'description': 'Hauteur de précipitations quotidienne',
        'label': 'Hauteur',
        'unit': 'mm',
        'conversion': lambda x: x,
        'plot_type': 'bar'
    },
    'INST': {
        'category': 'Soleil',
        'description': 'Durée d\'insolation quotidienne',
        'label': 'Durée',
        'unit': 'min',
        'conversion': lambda x: x,
        'plot_type': 'bar'
    },
    'PMERM': {
        'category': 'Pression',
        'description': 'Pression mer moyenne quotidienne',
        'label': 'Pmer',
        'unit': 'hPa',
        'conversion': lambda x: round(x / 100, 1),
        'plot_type': 'line'
    }
}

hourly_clim_parameters_dict = {
    'DATE': {
            'description': 'Date et heure de l\'enregistrement',
            'conversion': lambda x: x,
        },
    'T': {
        'category': 'Température',
        'description': 'Température sous abri horaire',
        'label': 'T',
        'unit': '°C',
        'conversion': lambda x: round(x - 273, 1),
        'plot_type': 'line'
    },
    'U': {
            'category': 'Humidité',
            'description': 'Humidité relative horaire',
            'label': 'HR',
            'unit': '%',
            'conversion': lambda x: x,
            'plot_type': 'line'
        },
    'FF': {
            'category': 'Vent',
            'description': 'Vitesse du vent horaire',
            'label': 'Vmoy',
            'unit': 'km/h',
            'conversion': lambda x: round(x * 3.6, 0),
            'plot_type': 'line'
        },
    'RR1': {
            'category': 'Précipitations',
            'description': 'Hauteur de précipitations horaire',
            'label': 'Hauteur',
            'unit': 'mm',
            'conversion': lambda x: x,
            'plot_type': 'bar'
        },
    'VV': {
            'category': 'Visibilité',
            'description': 'Visibilité horaire',
            'label': 'Distance',
            'unit': 'km',
            'conversion': lambda x: round(x / 1000, 1),
            'plot_type': 'line'
        },
    'INS': {
            'category': 'Soleil',
            'description': 'Durée d\'insolation horaire',
            'label': 'Durée',
            'unit': 'min',
            'conversion': lambda x: x,
            'plot_type': 'bar'
        },
    'PMER': {
            'category': 'Pression',
            'description': 'Pression mer horaire',
            'label': 'Pmer',
            'unit': 'hPa',
            'conversion': lambda x: round(x / 100, 1),
            'plot_type': 'line'
        }
}

