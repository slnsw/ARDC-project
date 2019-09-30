""" This module is used to hold class for making request to Alma API
    and manipulate the response.
"""
import requests
from utils import xml_util as xml


class Alma(object):
    """
    Class to wrap the functions to manipulate the response received
    from the ALMA API

    Attributes:
        api_endpoint (str): The API endpoint where the request will be made
        api_key (str): The API key to be sent with request
    """

    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key

    def retrieve_record(self, mms_id: str) -> dict:
        """ This function is used to retrieve the response from
        ALMA Bibliographic API by providing the mms_id to the API.

        Args:
            mms_id (int): The MMS ID of the Alma record

        Returns:
            dict: The dictionary of fields extracted from ALMA API
        """
        # make the request URL
        api_request = self.api_endpoint + 'bibs?mms_id=' + str(mms_id)
        # Add Authorization header as required by the API
        api_headers = {'Authorization': 'apikey ' + self.api_key}
        r = requests.get(api_request, headers=api_headers)
        http_response = r.text
        values = xml.load_xml(http_response)
        data = xml.xml_json(values)

        return {'url': api_request, 'values': values, 'data': data}
