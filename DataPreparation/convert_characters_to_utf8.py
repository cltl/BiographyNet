#!usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
from HTMLParser import HTMLParser

#version_nr

version_nr = "1.0"

#parser is global: called by embedded function, but should not be created 
#for every file.
parser = ''





def clean_text(intext):
    check_pb = open('dump.txt', 'w')
    clean_lines = ''
    for line in intext:
        nohtml_line = parser.unescape(line)
        utf8_line = nohtml_line.encode('utf-8')
        clean_lines += utf8_line
        try:
            check_pb.write(utf8_line)
        except:
            print utf8_line
    return clean_lines



def clean_data_in_dir(indir, outdir):

    #assign default dir name to outdir if none is given
    if not outdir:
        if '-html-cleaned' in indir:
            outdir = indir.replace('-html','')
        else:
            outdir = indir.rstrip('/') + '-cleaned/'
    #make sure outdir exists
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    #initiate html parser
    global parser
    parser = HTMLParser()

    #go through files in input dir
    #print cleaned text and cleaned fields in outputdir
    for f in os.listdir(indir):
        if f.endswith('.xml'):
            my_text = open(indir + f, 'r')
            cleaned_text = clean_text(my_text)
            outfile = open(outdir + f, 'w')
            outfile.write(cleaned_text)
            outfile.close()
            my_text.close()

def print_version():
    """ Print current version of implementation """
    print version_nr


# standardly structured function for usage
def usage(command=None):
    """ Print appropriate usage message and exit. """
    
    def p(msg, nobreak=False):
        """ Print the message with necessary indentation and linebreaks. """
        if nobreak:
            print " " * indent + msg,
        else:
            print " " * indent + msg
    p ("Usage: convert_characters_to_utf8.py input_dir (output_dir).")
    
    if not command:
        p ("run: convert_characters_to_utf8.py --usage for more explanations or")
        p ("run: convert_characters_to_utf8.py --all for a complete overview of options")
    elif command == 'usage':
        
        p ("You must provide an input directory with xml files containing text with html mark up.\n")
        p ("You may optionally provide an output directory where cleaned files need to be placed. If you do not provide an output directory, the cleaned files will be placed in a new directory ending in '-cleaned' (if input was html-cleaned, 'html' is removed from the directory name).\n This directory is located in the same directory as the input directory.\n")
        p ("python convert_characters_to_utf8.py --version\n Prints out the current version of this program.")
    elif command == 'all':
        
        p ("OPTIONS:")
        p ("--version (-v): prints out current version of the program. If an input directory is given, the program is also executed.")
        p ("--usage (-u): prints out an explanation of how to use this program. The program is not executed.")
        p ("--all (-a): prints out a full overview of how to use this program. The program is not executed.")
        
        
        p ("ARGUMENTS:")
        p ("input_dir: path to directory where files that need to be cleaned are located")
        p ("output_dir: (optional) path to directory where files that are cleaned will be stored. If none given a default output directory ending in '-cleaned' is created in the same directory as the input directory. If the input directory ends with 'html-cleaned', 'html' is removed to creat the name of the output directory.")


def main(argv=None):

    #option to print version
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vua', ['version','usage','all'])
    except:
        print str(err)
        usage()
    
    #boolean storing whether program is executed or not (default is True)
    execute = True
    
    for o in opts:
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


        if len(args) < 1:
        #print warning and explanation if argument is missing
            usage()
        else:
            #first argument is input dir
            in_dir = args[0]
            #check if second argument is given
            if len(argv) > 1:
                #second argument if given, is outdir
                out_dir = args[1]
            else:
                #outdir is default which will be created by the program
                out_dir = ''

            #call program
            clean_data_in_dir(in_dir, out_dir)


if __name__ == '__main__':
    main()
