#!usr/bin/python
# -*- coding: utf-8 -*-


import sys
import os
import extract_from_xml
from os import listdir
from xml.etree.ElementTree import ElementTree







#takes parsed xml as input, identifies person information
#and returns an interpretation of this information
def retrieve_info(elem):
    pers_info = []
    for ch in elem.getchildren():
        if ch.tag == 'person':
            pers_info = extract_from_xml.extract_person_information(ch)
    return pers_info


def print_output(outputfile, my_info):

    my_out = open(outputfile, 'w')

    for k, v in my_info.items():
        try:
            my_v = v.encode('utf-8')
            my_out.write(k + ',' + my_v + '\n')
        except:
            print k, v

    my_out.close()


def process_xml_file(xmlfile, output_dir, print_out):
    
    #parse xml
    my_biography = ElementTree().parse(xmlfile)
    #retrieve metadata about person
    my_info = retrieve_info(my_biography)
    if print_out:
        #outfile is called as xmlfile, but with different suffix
        xmlname = xmlfile.split('/')[-1]
        filename = xmlname.replace('.xml','.csv')
        out_file = output_dir + filename
        print_output(out_file, my_info)
    return my_info



# function that retrieves information from xml and returns dictionary
# of these values. If print_out is True, it will also print an output file
# per XML where tags and values are represented as comma sperated values
def process_files(input_dir, output_dir, print_out = False):
    
    
    # make sure input_dir ends with '/'
    if not input_dir.endswith('/'):
        input_dir += '/'


    #if print, make sure output_dir is well defined
    # if no output_dir, set default output_dir else make sure it ends in '/'
    if print_out:
        if not output_dir:
            # default output dir is new directory in input dir
            output_dir = input_dir + 'metadata_values/'
        elif not output_dir.endswith('/'):
            output_dir += '/'
        #make sure that output_dir exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        

    for my_file in listdir(input_dir):
        #check if indeed xml file
        if my_file.endswith('.xml'):
            xmlfile = input_dir + my_file
            process_xml_file(xmlfile, output_dir, print_out)


def main(argv=None):

    if argv is None:
        argv = sys.argv
    if len(argv) < 2:
        print 'Error: you must provide an input directory and may optionally provide an output directory.'
    else:
        #first argument is input dir
        input_dir = argv[1]
        #second argument is output dir
        #if no output directory is given, a default output directory is created.
        output_dir = ''
        if len(argv) >= 3:
            output_dir = argv[2]

        #call function, third argument indicates whether information from XML
        #should be print out. This is always the case when this function is called from here.
        print_out = True
        process_files(input_dir, output_dir, print_out)
            


if __name__ == '__main__':
    main()
