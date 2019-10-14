# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 14:29:53 2019

@author: SAli
"""

import os 
from os import listdir
import re
import spacy
from spacy import displacy
from collections import Counter
import en_core_web_sm
nlp = en_core_web_sm.load()
nlp.max_length = 4000000

# Extracting list of texts to analyse
texts_path = data_path= os.path.join(os.getcwd(), "text_files")
textfiles = [f for f in listdir(texts_path) if os.path.isfile(os.path.join(texts_path, f))]


for bookID in textfiles:
    
    print("Performing NLP on ", bookID.split(".")[0])

    # load text file from directory
    with open(os.path.join(texts_path,bookID), 'r', encoding="utf-8") as file:
        data = file.read().replace('\n', '')
    
    data = re.sub(' \.\.\. ', ' ',data)
    data = re.sub("\s\s+" , " ",data)
    data = re.sub('- ','',data)

    doc = nlp(data)
    len(doc.ents)
    
    filt = ["PERSON","GPE","LOC","NORP","ORG","PRODUCT","EVENT","WORK OF ART","LANGUAGE"]
    filt1 = ["PERSON", "GPE", "LOC", "NORP"]
    items = [x.text for x in doc.ents if x.label_ in filt1]
    counts = Counter(items).most_common()
    counts    
    
    # Create dictionary of frequencies for most common words
    freq = {}
    for c in counts:
        freq[c[0]] = c[1]
        
    # Write named entity frequency dict in a file
    with open(os.path.join(os.getcwd(),'named_entities',bookID.split(".")[0] + "_names.txt"), "w", encoding="utf-8") as text_file:
        text_file.write(str(freq))
        
    # Read named entities from file        
#    with open(os.path.join(os.getcwd(),'named_entities',bookID.split(".")[0] + "_names.txt"), "r", encoding="utf-8") as text_file:
#        frq = text_file.read().replace('\n', '')
#        frq = eval(frq)
#        
