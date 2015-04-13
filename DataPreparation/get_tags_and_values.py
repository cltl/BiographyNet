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


def print_version():
    """ Prints out version nr of the program """
    print version_nr


# standard function for usage
def usage(command=None):
    """ Print appropriate usage message and exit. """
    
    
    def p(msg, nobreak=False):
        """ Print the message with necessary indentation and linebreaks. """
        if nobreak:
            print " " * indent + msg,
        else:
            print " " * indent + msg
    p ("Usage: get_tags_and_values.py input_dir (output_dir).")
    
    if not command:
        p ("run: get_tags_and_values.py --usage for more explanations or")
        p ("run: get_tags_and_values.py --all for a complete overview of options")
    elif command == 'usage':
        
        p ("You must provide an input directory with xml files containing text with xml files.\n")
        p ("You may optionally provide an output directory where cleaned files need to be placed. If you do not provide an output directory, the cleaned files will be placed in a new directory called 'metadata_values'.\n This directory is located in the input directory.\n")
        p ("python get_tags_and_values.py --version\n Prints out the current version of this program.")
    elif command == 'all':
        
        p ("OPTIONS:")
        p ("--printout (-p): print output in outputfiles and pairs that cannot be dealt with because of encoding issues in the commandline.")
        p ("--version (-v): prints out current version of the program. If an input directory is given, the program is also executed.")
        p ("--usage (-u): prints out an explanation of how to use this program. The program is not executed.")
        p ("--all (-a): prints out a full overview of how to use this program. The program is not executed.")
        
        
        p ("ARGUMENTS:")
        p ("input_dir: path to directory where files that need to be cleaned are located")
        p ("output_dir: (optional) path to directory where files that are cleaned will be stored. If none given a default output directory called 'metadata_values' is created in the input directory.")


def main(argv=None):

    #option to print version
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vuap', ['version','usage','all','printout'])
    except:
        print str(err)
        usage()
    
            
    for o in opts:
        
        if o in ('-p','--printout'):
            print_out = True
        else:
            print_out = False

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
        
            
    #boolean storing whether program is executed or not (default is True)
    execute = True
    
    if execute:

        if len(args) < 1:
            usage()

        else:
            #first argument is input dir
            input_dir = args[0]
            #second argument is output dir
            #if no output directory is given, a default output directory is created.
            output_dir = ''
            if len(args) >= 2:
                output_dir = args[1]

            process_files(input_dir, output_dir, print_out)
            


if __name__ == '__main__':
    main()
