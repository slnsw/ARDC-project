# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 10:32:30 2019

@author: SAli
"""

import json
import pandas as pd
from xmljson import yahoo
import xml.etree.ElementTree as ET
from utils.rosetta import Rosetta  # this is a rosetta helper class from the SL github
from utils.rosetta import xml_json

df = pd.read_excel('ALTO_IEs.xlsx', sheet_name='Query List 2019-09-23 10.31.03')
df = df[["IE PID", "MMSIDs", "Barcodes","Title (DC)"]]

df.head() # Displaying first 5 rows


api_endpoint = 'http://digital.sl.nsw.gov.au'
api_pds_endpoint = 'https://libprd70.sl.nsw.gov.au/pds'
api_sru_endpoint = 'http://digital.sl.nsw.gov.au/search/permanent/sru'

api_username = 'api_etl'
api_password = 'blahBlah56'
api_institude_code = 'SLNSW'


ros = Rosetta(api_endpoint, api_pds_endpoint, api_sru_endpoint, api_username, api_password, api_institude_code, api_timeout=1200)

IE_PID = df["IE PID"][4]
r = ros.iews_get_ie(IE_PID, 0, raw=True)

json_data = yahoo.data(r)
root_str = ET.tostring(r,encoding='utf-8').decode('utf-8')

mets_ordereddict = xml_json(root_str)
mets_json = json.dumps([mets_ordereddict])
mets_dict = json.loads(mets_json)

with open('mets.json', 'w') as fp:
    json.dump(mets_dict, fp, ensure_ascii=False, indent=2)
