#!usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import getopt
import nltk
import extract_from_xml
import xml.etree.ElementTree as ET
from HTMLParser import HTMLParser


#version number (update after revisions that influence output)

version_nr = '1.0'


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
    #assign default name to out_dir if non-given
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

# 
def print_version():
    """ Print current version of implementation """
    print version_nr


# standard function for usage 
def usage(command=None):
    """ Print appropriate usage message and exit. """
    
    def p(msg, nobreak=False):
        """ Print the message with necessary indentation and linebreaks. """
        if nobreak:
            print " " + msg,
        else:
            print " " + msg
    p ("Usage: clean_html_texts.py input_dir (output_dir).")

    if not command:
        p ("run: clean_html_texts.py --usage for more explanations or")
        p ("run: clean_html_texts.py --all for a complete overview of options")
    elif command == 'usage':
    
        p ("You must provide an input directory with xml files containing text with html mark up.\n")
        p ("You may optionally provide an output directory where cleaned files need to be placed. If you do not provide an output directory, the cleaned files will be placed in a new directory ending in 'html-cleaned'.\n This directory is located in the same directory as the input directory.\n")
        p ("python clean_html_text.py --version\n Prints out the current version of this program.")
    elif command == 'all':

        p ("OPTIONS:")
        p ("--version (-v): prints out current version of the program. If an input directory is given, the program is also executed.")
        p ("--usage (-u): prints out an explanation of how to use this program. The program is not executed.")
        p ("--all (-a): prints out a full overview of how to use this program. The program is not executed.")
        

        p ("ARGUMENTS:")
        p ("input_dir: path to directory where files that need to be cleaned are located")
        p ("output_dir: (optional) path to directory where files that are cleaned will be stored. If none given a default output directory ending in '-html-cleaned' is created in the same directory as the input directory.")
    

def main(argv=None):

    #option to print version
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vua', ['version','usage','all'])
    except IOError as err:
        print str(err)
        usage()

    #boolean storing whether program is executed or not (default is True)
    execute = True
    
    for o in opts[0]:
        if o in ('-v','--version'):
            print_version()
            if len(args) < 1:
                execute = False
        elif o in ('-a','--all'):
            usage('all')
            execute = False
        elif o in ('-u','--usage'):
            execute = False
            usage('usage')

    if execute:
    #check if at least one argument was provided (argv[0] is program name)
        if len(args) < 1:
            usage()
        else:
            #first argument is input dir
            in_dir = args[0]
            #check if second argument is given
            if len(args) > 1:
                #second argument if given, is outdir
                out_dir = args[1]
            else:
            #outdir is default which will be created by the program
                out_dir = ''
        #call program
            clean_data_in_dir(in_dir, out_dir)


if __name__ == '__main__':
    main()
