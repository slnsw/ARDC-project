# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 09:39:07 2019

@author: SAli
"""

import random
import pandas as pd
from roCrate import *
from utils.rosetta import Rosetta  # this is a rosetta helper class from the SL github

def main():
    
    api_endpoint = 'http://digital.sl.nsw.gov.au'
    api_pds_endpoint = 'https://libprd70.sl.nsw.gov.au/pds'
    api_sru_endpoint = 'http://digital.sl.nsw.gov.au/search/permanent/sru'
    
    api_username = 'api_etl'
    api_password = 'blahBlah56'
    api_institude_code = 'SLNSW'
        
    ros = Rosetta(api_endpoint, api_pds_endpoint, api_sru_endpoint, api_username, api_password, api_institude_code, api_timeout=1200)
    
    df = pd.read_excel('ALTO_IEs.xlsx', sheet_name='Query List 2019-09-23 10.31.03')
    df = df[["IE PID", "MMSIDs", "Barcodes","Title (DC)"]]
    print(df.head()) # Displaying first 5 rows
    
    IE_PID = df["IE PID"][500]
    
    objfiles,mmsid = glean(IE_PID, ros)
    roCrateJsonld(IE_PID, objfiles=[1], mmsid='1')
    getFiles(IE_PID, objfiles=[1])
    
#    booklist = random.sample(range(1, len(df["IE PID"])), 10)
    
#    objectfiles = []
#    mmsid = []
    
#    for i in booklist:
#        IE_PID = df["IE PID"][i]
#        print("******************** BOOK ",i,": IE PID ", IE_PID, " ********************")
#        objectfiles[i],mmsid[i] = glean(IE_PID, ros)   
    
#    for i in booklist:
#        IE_PID = df["IE PID"][i]
#        print("******************** BOOK ",i,": IE PID ", IE_PID, " ********************")
#        objectfiles[i],mmsid[i] = roCrateJsonld(IE_PID,objectfiles[i], mmsid[i]) 
    
#    for i in booklist:
#        IE_PID = df["IE PID"][i]
#        print("******************** BOOK ",i,": IE PID ", IE_PID, " ********************")
#        objectfiles[i],mmsid[i] = roCrateJsonld(IE_PID,objectfiles[i]) 
    
        
        
    
if __name__ == '__main__':
    main()