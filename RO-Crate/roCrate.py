# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 10:27:34 2019

@author: SAli
"""

import os 
import json
import time
import xml.etree.ElementTree as ET
#from utils.rosetta import Rosetta  # this is a rosetta helper class from the SL github
from utils.rosetta import xml_json
import requests
import shutil



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
        
        originalName = list(filter(lambda file: file['id'] == 'fileOriginalName', generalFileChars[0]['record']['key']))[0]['content']
        
        try:
            originalPath = list(filter(lambda file: file['id'] == 'fileOriginalPath', generalFileChars[0]['record']['key']))[0]['content']
            originalPath_id = originalPath.split('/')[-2]
        except:
            originalPath_id = list(filter(lambda file: file['id'] == 'fileExtension', generalFileChars[0]['record']['key']))[0]['content']
            
        
        record = internalIdentifier[0]['record']
        try:
            pid = list(filter(lambda file: file['key'][0]['content'] == 'PID', record))
            fl_id = pid[0]['key'][1]['content']
        except:
            fl_id = record['key'][1]['content']
        
        item = {'id':originalPath_id, 'name':originalName, 'FLID':fl_id}
        allobjectfiles.append(item)

    dmdSec = mets_dict[0]['dmdSec']
    mmsid = list(filter(lambda file: file['ID'] == 'ie-dmd', dmdSec))

    return allobjectfiles,mmsid    
    



def roCrateJsonld(IE_PID, objfiles, mmsid):
    
    altotypes = ['ALTO','ACCESS_TRANSCRIPT_LINKED']
    imagetypes = ['SCREEN','ACCESS','jpg']
    pdftypes = ['PDF','ACCESS_2','pdf']
    epubtypes = ['EPUB','ACCESS_3','epub']
    
    altoFiles = list(filter(lambda file: file['id'] in altotypes, objfiles))
    screenFiles = list(filter(lambda file: file['id'] in imagetypes, objfiles))
    pdfFiles = list(filter(lambda file: file['id'] in pdftypes, objfiles))
    epubFiles = list(filter(lambda file: file['id'] in epubtypes, objfiles))
    altoFiles = sorted(altoFiles, key = lambda i: i['name'])
    screenFiles =sorted(screenFiles, key = lambda i: i['name'])
    
    # Defining constants
    bookJSONLD = 'ro-crate-metadata.jsonld'
    name = mmsid[0]['mdWrap']['xmlData']['record']['title'].title()
    
    mms_id = mmsid[0]['mdWrap']['xmlData']['record']['identifier']
    bookName = 'Scanned pages'

    # Base URL for fetching bib data
    base_url = "https://api-ap.hosted.exlibrisgroup.com/almaws/v1/bibs"
    #API Key (input your own key here)
    apikey = "l8xxa0faef03a6bd47c08bb9de14d8015225"
    
    # Retrieving bib xml from ALMA API
    response = requests.get(base_url, params={'mms_id': mms_id,'apikey':apikey})
    bib_ordereddict = xml_json(response.text)
    bib_json = json.dumps([bib_ordereddict])
    bib_dict = json.loads(bib_json)
    
    # Set book description (if there is one within the title)
    try:
        description = name.split(':')[1]
    except:
        description = "."

    # Set book's date of publishing
    try:
        datePublished = bib_dict[0]['bib']['date_of_publication']
    except:
        datePublished = "."
        
    # Set book's author
    try:
        author = mmsid[0]['mdWrap']['xmlData']['record']['creator']
    except:
        author = "."
    
    # Reading in the template JSONLD file
    template_dir = os.path.join(os.getcwd(), 'template', 'ro-crate-metadata.jsonld')
    with open(template_dir, 'r') as myfile:
        j=myfile.read()
    roCrateTemplate_dict = json.loads(j)
    jsonLD = roCrateTemplate_dict
    
    # Find the root dataset
    # First find the item that is the root dataset
    rootDatasetDescriptor = [d for d in jsonLD["@graph"] if d["@id"] == "ro-crate-metadata.jsonld"]
    rootDatasetDescriptor = rootDatasetDescriptor[0]
    # Then find the rootDataset that it is about.
    print("desc", rootDatasetDescriptor)
    rootDataset = [r for r in jsonLD["@graph"] if r["@id"] == rootDatasetDescriptor["about"]["@id"]]
    rootDataset = rootDataset[0]
    rootDataset['name'] = name
    rootDataset['description'] = description
    rootDataset['datePublished'] = datePublished
    rootDataset['author'][0]['@id'] = author
    try:
        rootDataset['publisher']['@id'] = bib_dict[0]['bib']['publisher_const']
        publisherObj = {
            "@id": bib_dict[0]['bib']['publisher_const'],
            "address": bib_dict[0]['bib']['place_of_publication'],
            "@type": "Organization"            
            }
    except:
        rootDataset['publisher']['@id'] = bib_dict[0]['bib']['place_of_publication']
        publisherObj = {
            "@id": bib_dict[0]['bib']['place_of_publication'],
            "address": bib_dict[0]['bib']['place_of_publication'],
            "@type": "Organization"            
            }        
                   
    rootDataset['source'] = [{"@id": "https://ror.org/04evq8811"}]

    rootHasFile=[]
    
    authorObj = {
            "@id": author,
            "@type": "Person"
            }
    jsonLD['@graph'].append(authorObj)
    

    jsonLD['@graph'].append(publisherObj)
    
    sourceObj = {
            "@id": "https://ror.org/04evq8811",
            "name": "State Library of NSW",
            "address": "Sydney, Australia",
            "@type": "Organization"
            }
    jsonLD['@graph'].append(sourceObj)
    
    try:
        pdfObj = {
                '@id': 'PDF/' + pdfFiles[0]['name'],
                '@type': 'File',
                'name' : 'PDF version of book'
                }
        jsonLD['@graph'].append(pdfObj)
        rootHasFile.append({'@id' : 'PDF/' + pdfFiles[0]['name']})
    except:
        pass
    
    try:
        epubObj = {
                '@id': 'EPUB/' + epubFiles[0]['name'],
                '@type': 'File',
                'name' : 'EPUB version of book'
                }
        jsonLD['@graph'].append(epubObj)
        rootHasFile.append({'@id' : 'EPUB/' + epubFiles[0]['name']})
    except:
        pass
    
    rootDataset['hasFile'] = rootHasFile
    
    hasPart = []
    # Filling in the template JSONLD
    # Filling in details of screens, altos and anything else present in the mets
    for index, file in enumerate(screenFiles):
        screen = file['name']
        basename = screen.split('.')[0]
        try:
            alto = [r for r in altoFiles if r["name"] == basename+".xml"][0]['name']
        except:
            alto = None
        if screen:
            hasPart.append({'@id': basename})
            fileId = 'SCREEN/' + screen
            screenObj = {
                    '@id': screen,
                    'name': 'Page ' + str((index + 1)) + ' image ',
                    '@type': 'File',
                    'path': fileId
                    }
    
            jsonLD['@graph'].append(screenObj)
        if alto:
            fileId = 'ALTO/' + alto
            altoObj = {
                    '@id': alto,
                    'name': 'Page ' + str((index + 1)) + ' xml ',
                    '@type': 'File',
                    'path': fileId
                    }
            jsonLD['@graph'].append(altoObj)
        hasPartPage=[]
        if screen:
            hasPartPage.append({'@id': screen})
        if alto:
            hasPartPage.append({'@id': alto})
        pageObj = {
                '@id': basename,
                'name': 'Page ' + str((index + 1)),
                '@type': 'RepositoryObject',
                'hasPart': hasPartPage
                }
        jsonLD['@graph'].append(pageObj)
        
    book = {
            '@id': '_:book',
            'name': bookName,
            '@type': ['Dataset'],
            'hasPart': hasPart
            }
    rootDataset['hasPart'] = [
            {
                    '@id': '_:book'
                    }
            ]
    
    jsonLD['@graph'].append(book)
    
    # Writing JSONLD file into the book's RO-Crate
    crateDir = os.path.join(os.getcwd(),'RO-Crates',IE_PID)
    if not os.path.exists(crateDir):
        os.makedirs(crateDir)
    with open(os.path.join(crateDir, bookJSONLD), 'w') as fp:
        json.dump(jsonLD, fp, ensure_ascii=True, indent=2)
    

    
def getFiles(IE_PID, objfiles):
    altotypes = ['ALTO','ACCESS_TRANSCRIPT_LINKED']
    imagetypes = ['SCREEN','ACCESS']
    pdftypes = ['PDF','ACCESS_2']
    epubtypes = ['EPUB','ACCESS_3']
    
    altoFiles = list(filter(lambda file: file['id'] in altotypes, objfiles))
    screenFiles = list(filter(lambda file: file['id'] in imagetypes, objfiles))
    pdfFiles = list(filter(lambda file: file['id'] in pdftypes, objfiles))
    epubFiles = list(filter(lambda file: file['id'] in epubtypes, objfiles))
    altoFiles = sorted(altoFiles, key = lambda i: i['name'])
    screenFiles =sorted(screenFiles, key = lambda i: i['name'])
    
    altoFiles = sorted(altoFiles, key = lambda i: i['name'])
    screenFiles =sorted(screenFiles, key = lambda i: i['name'])
    
    url = "http://digital.sl.nsw.gov.au/delivery/DeliveryManagerServlet"
    print("************* Fetching the ALTO files ****************")
    for x in altoFiles:
        print("Fetching ALTO file ",x['name'])
        resp1 = requests.get(url,params={'dps_pid':x['FLID'], 'dps_func':'stream'})
        if resp1.status_code == 200:
            tree = ET.ElementTree()
            root = ET.fromstring(resp1.text)
            tree._setroot(root)
    
            crateDir = os.path.join(os.getcwd(),'RO-Crates',IE_PID,"ALTO")
            if not os.path.exists(crateDir):
                os.makedirs(crateDir)
            filename = crateDir + "/" + x['name']
            tree.write(filename)
        else:
            print("Error retrieving ALTOs")

    print("************* Fetching the Screen files ****************")        
    for x in screenFiles:
        print("Fetching SCREEN file ",x['name'])
        resp1 = requests.get(url,params={'dps_pid':x['FLID'], 'dps_func':'stream'},stream=True)
        if resp1.status_code == 200:
            crateimgDir = os.path.join(os.getcwd(),'RO-Crates',IE_PID,"SCREEN")
            if not os.path.exists(crateimgDir):
                os.makedirs(crateimgDir)
            with open(crateimgDir + "/" + x['name'], 'wb') as f:
                resp1.raw.decode_content = True
                shutil.copyfileobj(resp1.raw, f)   
        else:
            print("Error retrieving Screens")  
            
    print("************* Fetching the PDF file ****************")  
    resp_pdf = requests.get(url,params={'dps_pid':pdfFiles[0]['FLID'], 'dps_func':'stream'},stream=True)
    if resp_pdf.status_code == 200:
        cratepdfDir = os.path.join(os.getcwd(),'RO-Crates',IE_PID,"PDF")
        if not os.path.exists(cratepdfDir):
            os.makedirs(cratepdfDir)
        with open(cratepdfDir + "/" + pdfFiles[0]['name'], 'wb') as f:
            resp_pdf.raw.decode_content = True
            shutil.copyfileobj(resp_pdf.raw, f)   
    else:
        print("Error retrieving PDF") 
    
    try:
        resp_epub = requests.get(url,params={'dps_pid':epubFiles[0]['FLID'], 'dps_func':'stream'},stream=True)
        if resp_epub.status_code == 200:
            print("************* Fetching the EPUB files **************** \n")  
            cratepdfDir = os.path.join(os.getcwd(),'RO-Crates',IE_PID,"EPUB")
            if not os.path.exists(cratepdfDir):
                os.makedirs(cratepdfDir)
            with open(cratepdfDir + "/" + epubFiles[0]['name'], 'wb') as f:
                resp_epub.raw.decode_content = True
                shutil.copyfileobj(resp_epub.raw, f)   
        else:
            print("Error retrieving EPUB") 
    except: 
        print("Epub file not present")
