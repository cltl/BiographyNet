#!usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import nltk
import extract_from_xml
import xml.etree.ElementTree as ET
from HTMLParser import HTMLParser


#parser is global: called by embedded function, but should not be created
#for every file.
parser = ''

def retrieve_text(elem):
    text = ''
    for ch in elem.getchildren():
        if ch.tag == 'biography':
            text = extract_from_xml.extract_text(ch)
    return text


def get_clean_text(my_xml):
    
    # retrieve text:
    bio_text = retrieve_text(my_xml)
    #strip html markup
    raw_text = nltk.clean_html(bio_text)
    #remove odd characters
    #clean_text = raw_text.encode('utf-8')
    #return clean text
    return raw_text

def clean_html_text(in_dir, out_dir, f):
    
    #input file
    xmlfile = in_dir + f
    #parse xml
    my_xml = ET.parse(xmlfile)
    #get root of xml
    root = my_xml.getroot()
    #get clean text of input file
    clean_text = get_clean_text(root)
    #identify text element
    for ch in root.getchildren():
        if ch.tag == 'biography':
            for gch in ch.getchildren():
    #replace value by clean text
                if gch.tag == 'text':
                    new_text = clean_text.decode('utf-8','ignore')
                    gch.text = new_text

    
    my_xml.write(out_dir + '/' + f)


def prepare_out_dir(in_dir, out_dir):
    '''input: string name of input and output directory as given by user (which may be empty string
       returns: string name of output directory, default assigned if user has not given one
        Function assigns default name to output directory if non given and creates this directory if it does not exist.'''
    #assign default name to out_dir if non-given/Users/antske/Desktop/aanvraag.zip
    if not out_dir:
        #if character cleanup has been carried out, indir may already be called
        #-cleaned
        if '-cleaned' in in_dir:
            out_dir = in_dir.rstrip('/').replace('-cleaned', '-html-cleaned')
        else:
            out_dir = in_dir.rstrip('/') + '-html-cleaned'
    
    #create out_dir folder if does not exist
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    return out_dir




def clean_data_in_dir(in_dir, out_dir):
    #get name and create output directory
    out_dir = prepare_out_dir(in_dir, out_dir)

    #initiate html parser
    global parser
    parser = HTMLParser()
    
    for f in os.listdir(in_dir):
        if '.xml' in f:
            clean_html_text(in_dir, out_dir, f)






def main(argv=None):

    if argv is None:
        argv = sys.argv
    #check if at least one argument was provided (argv[0] is program name)
    if len(argv) < 2:
        #print warning and explanation if argument is missing
        print 'You must provide an input directory and may optionally provide an output directory.\n\tUsage: python clean_files.py input_dir (output_dir)\n'
    else:
        #first argument is input dir
        in_dir = argv[1]
        #check if second argument is given
        if len(argv) > 2:
            #second argument if given, is outdir
            out_dir = argv[2]
        else:
            #outdir is default which will be created by the program
            out_dir = ''
        #call program
        clean_data_in_dir(in_dir, out_dir)


if __name__ == '__main__':
    main()
