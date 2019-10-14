# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 10:09:31 2019

@author: SAli
"""

from utils.rosetta import xml_json
import xml.etree.ElementTree as ET
import os 
from os import listdir
import json

# Insert directory of your RO-Crates and load ALTO files for a specific book
cratedir = data_path= os.path.join(os.getcwd(), "RO-Crates")
bookID = "IE13384794"
altodir = os.path.join(cratedir, bookID, "ALTO")
altofiles = [f for f in listdir(altodir) if os.path.isfile(os.path.join(altodir, f))]


def findkeys(node, kv):
    if isinstance(node, list):
        for i in node:
            for x in findkeys(i, kv):
               yield x
    elif isinstance(node, dict):
        if kv in node:
            yield node[kv]
        for j in node.values():
            for x in findkeys(j, kv):
                yield x

fulltext = ""

for altoxml in altofiles:
    
    # Load the xml into an element tree
    tree = ET.parse(os.path.join(altodir, altoxml))
    root = tree.getroot()
    
    # Convert the element tree to json
    root_str = ET.tostring(root,encoding='utf-8').decode('utf-8')
    alto_ordereddict = xml_json(root_str)
    alto_json = json.dumps([alto_ordereddict])
    alto_dict = json.loads(alto_json)
    
    # Extract words from the alto json
    pagetext=" ".join(list(findkeys(alto_dict, 'CONTENT')))
    fulltext = fulltext + pagetext
    

print(fulltext.replace("\\" , ""))




