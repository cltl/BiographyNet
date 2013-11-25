#!usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
from HTMLParser import HTMLParser


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
