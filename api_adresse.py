"""Module designed to search for addresses in France using the address API."""

import requests

SEARCH_URL = 'http://api-adresse.data.gouv.fr/search/'
REVERSE_URL = 'https://api-adresse.data.gouv.fr/reverse'


def search_address(q: str, limit: int = 5, autocomplete: int = 0, search_type: str = 'municipality') -> list[dict]:
    """Search for an address in France.

    Args:
        q: Research string.
        limit: Maximum number of results.
        autocomplete: Activate/deactivate autocomplete.
        search_type: Type of results expected.

    Returns:
        Search result(s) with geocoding information.
    """
    payload = {
        'q': q,
        'limit': limit,
        'autocomplete': autocomplete,
        'type': search_type
    }

    r = requests.get(SEARCH_URL, params=payload)

    if r.status_code != 200 or not r.json().get('features'):
        return []

    return _format_response(r)


def reverse_address(lon: float, lat: float, limit: int = 1, search_type: str = 'street') -> list[dict]:
    """Find an address from coordinates in France.

    Args:
        lon: Search longitude.
        lat: Search latitude.
        limit: Maximum number of results.
        search_type: Type of results expected.

    Returns:
        Search result(s) with geocoding information.
    """
    payload = {
        'lon': lon,
        'lat': lat,
        'limit': limit,
        'type': search_type
    }

    n_loop = len(str(lat).split('.')[1])

    while n_loop != 0:
        r = requests.get(REVERSE_URL, params=payload)

        if r.status_code != 200:
            return []

        if r.json().get('features'):
            return _format_response(r=r)

        lat = float(str(lat)[:-1])
        payload['lat'] = lat
        n_loop -= 1

    return []


def _format_response(r: requests.Response) -> list[dict]:
    """Formats the response returned by the API.

    Args:
        r: Response object from the API.

    Returns:
        List of unpacked features dictionaries from the geojson returned by the API.
    """
    results = []
    for feature in r.json().get('features'):
        lon, lat = feature.get('geometry').get('coordinates')
        results.append({**feature.get('properties'), **{"lon": lon, "lat": lat}})

    return results


if __name__ == '__main__':
    pass
