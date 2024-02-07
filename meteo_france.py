"""
Querying 'Observation data' and 'Climatological data' apis of Météo France 
while managing token regeneration.

Token regeneration code comes from Météo France API portal FAQ 
(https://portail-api.meteofrance.fr/web/fr/faq).

An APPLICATION_ID is needed, to get it :
1. Click on the user account in connected mode (top right) 
> 'My API' > Choose an API > Click 'Generate Token'.
2. The APPLICATION_ID can be found in the cURL command at the bottom of the page.
"""

import requests
from streamlit import secrets

import constants

APPLICATION_ID = secrets.APPLICATION_ID

class Client(object):

    def __init__(self):
        self.session = requests.Session()


    def request(self, method, url, **kwargs):
        # First request will always need to obtain a token first
        if 'Authorization' not in self.session.headers:
            self.obtain_token()

        # Optimistically attempt to dispatch request
        response = self.session.request(method, url, **kwargs)
        if self.token_has_expired(response):
            # We got an 'Access token expired' response => refresh token
            self.obtain_token()
            # Re-dispatch the request that previously failed
            response = self.session.request(method, url, **kwargs)

        return response


    def token_has_expired(self, response):
        status = response.status_code
        content_type = response.headers['Content-Type']
        repJson = response.text
        if status == 401 and 'application/json' in content_type:
            repJson = response.text
            if 'Invalid JWT token' in repJson['description']:

                return True
            
        return False


    def obtain_token(self):
        # Obtain new token
        data = {'grant_type': 'client_credentials'}
        headers = {'Authorization': 'Basic ' + APPLICATION_ID}
        access_token_response = requests.post(
            constants.TOKEN_URL,
            data=data,
            verify=True,
            allow_redirects=False,
            headers=headers
        )
        token = access_token_response.json()['access_token']
        # Update session with fresh token
        self.session.headers.update({'Authorization': 'Bearer %s' % token})


    def get_stations_list(self) -> requests.Response:
        """Get the list of observation stations from the API.

        Returns:
            requests.Response: Response from the API with the data in csv.
        """
        self.session.headers.update({'Accept': 'application/json'})
        r = self.request(
            method='GET',
            url=constants.STATION_LIST_URL
        )

        return r
    

    def get_hourly_observation(self, id_station: str, date: str) -> requests.Response:
        """Get all available parameters for the requested station and for the 
        date/time closest to the requested date according to available data.

        Args:
            id_station (str): station id number ;
            date (str): requested date (ISO 8601 format with
        TZ UTC AAAA-MM-JJThh:00:00Z).

        Returns:
            requests.Response: Response from the API with the data in json.
        """
        self.session.headers.update({'Accept': 'application/json'})
        payload={
            'id_station': id_station,
            'date': date,
            'format': 'json'
        }
        r = self.request(
            method='GET',
            url=constants.HOURLY_OBSERVATION_URL,
            params=payload
        )

        return r
    

    def order_hourly_climatological_data(
            self, id_station: str, start_date: str, end_date: str) -> requests.Response:
        """Order climatological data for the requested station for the period
        defined by the start date and the end date at an hourly frequency.

        Args:
            id_station (str): station id number ;
            start_date (str): requested start date (ISO 8601 format with
        TZ UTC AAAA-MM-JJThh:00:00Z).
            end_date (str): requested end date (ISO 8601 format with
        TZ UTC AAAA-MM-JJThh:00:00Z).

        Returns:
            requests.Response: Response from the API with order id in a json.
        """
        self.session.headers.update({'Accept': 'application/json'})
        payload={
            'id-station': id_station,
            'date-deb-periode': start_date,
            'date-fin-periode': end_date
        }
        r = self.request(
            method='GET',
            url=constants.ORDER_HOURLY_CLIMATOLOGICAL_URL,
            params=payload
        )

        return r


    def order_daily_climatological_data(
            self, id_station: str, start_date: str, end_date: str) -> requests.Response:
        """Order climatological data for the requested station for the period
        defined by the start date and the end date at a daily frequency.

        Args:
            id_station (str): station id number ;
            start_date (str): requested start date (ISO 8601 format with
        TZ UTC AAAA-MM-JJThh:00:00Z).
            end_date (str): requested end date (ISO 8601 format with
        TZ UTC AAAA-MM-JJThh:00:00Z).

        Returns:
            requests.Response: Response from the API with order id in a json.
        """
        '''
        Get an order number for asynchronous download of daily weather
        information for one observation station in a period of date.
        Parameters :
        - id_station : id number (string) ;
        - start_date : start of period for the order (string) in ISO 8601 format
        with TZ UTC AAAA-MM-JJThh:00:00Z ;
        - end_date : end of period for the order (string) in ISO 8601 format
        with TZ UTC AAAA-MM-JJThh:00:00Z.
        '''
        self.session.headers.update({'Accept': 'application/json'})
        payload={
            'id-station': id_station,
            'date-deb-periode': start_date,
            'date-fin-periode': end_date
        }
        r = self.request(
            method='GET',
            url=constants.ORDER_DAILY_CLIMATOLOGICAL_URL,
            params=payload
        )

        return r
    

    def order_recovery(self, order_id: str) -> requests.Response:
        """Retrieve data from an order.

        Args:
            order_id (str): id of the order.

        Returns:
            requests.Response: Response from the API with the data in csv.
        """
        self.session.headers.update({'Accept': 'application/json'})
        payload={'id-cmde': order_id}
        r = self.request(
            method='GET',
            url=constants.ORDER_RECOVERY_URL,
            params=payload
        )

        return r


def main():
    client = Client()
    # r = client.order_hourly_climatological_data('76540009', '2024-02-04T04:00:00Z', '2024-02-04T04:00:00Z')
    # print(r.json().get('elaboreProduitAvecDemandeResponse').get('return'))

    r = client.order_recovery('761044914939')
    print(r.text)


if __name__ == '__main__':
    main()