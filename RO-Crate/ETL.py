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
    
    api_username = 'xxxxxxx'
    api_password = 'xxxxxxxxxxx'
    api_institude_code = 'SLNSW'
        
    ros = Rosetta(api_endpoint, api_pds_endpoint, api_sru_endpoint, api_username, api_password, api_institude_code, api_timeout=1200)
    
    # Reading in the excel file
    df = pd.read_excel('ALTO_IEs.xlsx', sheet_name='Query List 2019-09-23 10.31.03')
    df = df[["IE PID", "MMSIDs", "Barcodes","Title (DC)"]]
    
    # Formatting MMSID column to numerical type
    df["MMSIDs"] = df["MMSIDs"].str[1:]
    df["MMSIDs"] = pd.to_numeric(df["MMSIDs"])
    
    print(df.head()) # Displaying first 5 rows
    
    # Picking out 100 unique MMSIDs to look up
    mms = list(df["MMSIDs"].unique())
    mms_select = random.sample(mms, 100)
    
    # Picking out unique IE PIDs
    IE_PIDs = []
    Titles = []
    for i in mms_select:
        y = df.loc[df["MMSIDs"]==i]['IE PID'].values[0]
        z = df.loc[df["MMSIDs"]==i]['Title (DC)'].values[0]
        IE_PIDs.append(y)
        Titles.append(z)
        
    # Creating the RO-Crates for the 100 books         

    objectfiles = []
    mmsid = []
    
    #restore bookinfo
    #IE_PIDs,mmsid,objectfiles = restorebooksinfo()
    
    for index, IE_PID in enumerate(IE_PIDs):
        print("\n ******************** Book ",index, " - IE PID: ", IE_PID, " ******************** \n")
        obj_x,mmsid_x = glean(IE_PID, ros)   
        objectfiles.append(obj_x)
        mmsid.append(mmsid_x)
        
    savebooksinfo(IE_PIDs,mmsid,objectfiles)
        
    for index, IE_PID in enumerate(IE_PIDs):
        print("\n ******************** Creating JSONLD for Book ",index, " ******************** \n")
        roCrateJsonld(IE_PID, objectfiles[index], mmsid[index])
        
    for index, IE_PID in enumerate(IE_PIDs):
        print("\n ******************** Retrieving files for Book ",index," - IE PID: ", IE_PID, " ******************** \n")
        getFiles(IE_PID, objectfiles[index])




def savebooksinfo(IE_PIDs,mmsid,objectfiles):
    # Saving 100 books IE PID, MMSID and Objectfiles to external csv (optional)
    booksinfo = pd.DataFrame(
            {'IE PIDs': IE_PIDs,
             'MMSIDs': mmsid,
             'OBJ FILES': objectfiles
             })
    booksinfo.head()
    booksinfo.to_csv("booksinfo1.csv", sep='\t', index=False, encoding='utf-8')
    
    
def restorebooksinfo():
    # Restoring booksinfo (optional)
    bookdf = pd.read_csv('booksinfo.csv', sep='\t')
    IE_PIDs1 = list(bookdf["IE PIDs"])
    MMSID1 = [] 
    for i in range(100):
        MMSID1.append(eval(bookdf["MMSIDs"][i]))
    OBJFILES1 = []
    for i in range(100):
        OBJFILES1.append(eval(bookdf["OBJ FILES"][i]))
    return IE_PIDs1,MMSID1,OBJFILES1
        
    


# Retrieving titles of 100 books
#titles = []
#df1 = df[df['IE PID'].isin(IE_PIDs)]
#
## SAVE TO EXCEL
#from pandas import ExcelWriter
#
#df1=df1.drop(axis=1,columns=['MMSIDs','Barcodes'])
#writer = ExcelWriter('100BooksExport.xlsx')
#df1.to_excel(writer,'Sheet1')
#writer.save()
#    




    
if __name__ == '__main__':
    main()
