# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 10:27:34 2019

@author: SAli
"""

import json
import time
import xml.etree.ElementTree as ET
#from utils.rosetta import Rosetta  # this is a rosetta helper class from the SL github
from utils.rosetta import xml_json


def glean(IE_PID, ros):

    print("1- Requesting METS file from Rosetta")    
    t0=time.time()
    r = ros.iews_get_ie(IE_PID, 0, raw=True)
    t1=time.time()
    print("Completed in: \n", t1-t0, " seconds. \n")
    
    print("2- Converting METS xml data to json")
    t2=time.time()
    root_str = ET.tostring(r,encoding='utf-8').decode('utf-8')
    
    mets_ordereddict = xml_json(root_str)
    mets_json = json.dumps([mets_ordereddict])
    mets_dict = json.loads(mets_json)
    t3=time.time()
    print("Completed in: \n", t3-t2, " seconds. \n")
    
    print("3- Extracting file IDs from METS \n \n")
    amdSec = mets_dict[0]['amdSec']
    
    amdSec_obj = list(filter(lambda file: file['techMD']['mdWrap']['xmlData']['dnx']['section'][0]['record']['key'][0]['id'] == 'objectType', amdSec))
    
    allobjectfiles = []    
    for i in range(len(amdSec_obj)):
        objChars = amdSec_obj[i]['techMD']['mdWrap']['xmlData']['dnx']['section']
        internalIdentifier = list(filter(lambda file: file['id'] == 'internalIdentifier', objChars))
        generalFileChars = list(filter(lambda file: file['id'] == 'generalFileCharacteristics', objChars))
        
        originalPath = list(filter(lambda file: file['id'] == 'fileOriginalPath', generalFileChars[0]['record']['key']))[0]['content']
        originalPath_split = originalPath.split('/')
        
        record = internalIdentifier[0]['record']
        pid = list(filter(lambda file: file['key'][0]['content'] == 'PID', record))
        fl_id = pid[0]['key'][1]['content']
        
        item = {'id':originalPath_split[0], 'name':originalPath_split[1], 'FLID':fl_id}
        allobjectfiles.append(item)

    dmdSec = mets_dict[0]['dmdSec']
    mmsid = list(filter(lambda file: file['ID'] == 'ie-dmd', dmdSec))

    return allobjectfiles,mmsid    
    


def roCrateJsonld(IE_PID, objfiles, mmsid):
    print("This is for creating the RO Crate directory and JSONLD")
    

def getFiles(IE_PID, objfiles):
    print("This is for creating content folders in the RO Crate and retrieving files")