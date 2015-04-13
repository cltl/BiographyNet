#!usr/bin/python
# -*- coding: utf-8 -*-

from xml.etree.ElementTree import ElementTree
import metadata
import create_metadata_object
import merge_metadata_objects
import os
import sys

literals = ['birthplace','deathplace','occupation','education','father','mother']
dates = ['birthdate','deathdate']
month_dict = {}


def initiate_month_dict():
    global month_dict
    try:
        my_months = open('months_file')
        for line in my_months:
            #clear off newline at the end of the line
            clean_line = line.rstrip()
            key_val = clean_line.split(',')
            key = key_val[0]
            val = key_val[1].split('|')
            month_dict[key] = val
    except:
        print 'Could not create dictionary of month names: no file called months_file'


def check_for_month(month, s):
    '''Function that checks if month is mentioned in sentence and returns string that mentions it'''
    global month_dict
    if not month == 'YY':
        m_strings = month_dict.get(month)
        
        for m in m_strings:
            if m in s:
                return m
    #if string indicating month is not found, it may be indicated by numbers (actual name is prefered value)
        if month in s:
            return month
        elif month.lstrip('0') in s:
            return month.lstrip('0')
    return ''


def create_one_digit_day(day):
    if day.startswith('0'):
        return day.lstrip('0')
    else:
        return day


def tag_dates(tag, val, sentences):
  
    my_sents = sentences
 
    for date in val:
        parts = date.split('-')
        year = parts[0]
        month = parts[1]
        day = parts[2].rstrip()
        if not year == 'YYYY':
            new_sents = []
            for s in my_sents:
                if not tag in s:
                    s = s.replace('  ', ' ')
                    if year in s:
                        #get string refering to month in sentence
                        m = check_for_month(month, s)
                        #check if m is non-empty and if so, if it occurs in s
                        if m in s and m:
                            red_day = create_one_digit_day(day)
                            if ' ' + red_day + ' ' in s and not ' ' + day + ' ' in s:
                                day = red_day
                            if red_day + '-' in s and not day + '-' in s:
                                day = red_day
                            if day in s:
                                date = day + ' ' + m + ' ' + year
                                fdate = day + '-' + m + '-' + year
                                space_missed_date = day + m + ' ' + year
                                #old fashioned dates occur in vdaa, which uses one digit days for 1-9
                                old_fashioned_d1 = red_day + 'sten ' + m + ' ' + year
                                old_fashioned_d2 = red_day + 'den ' + m + ' ' + year
                                if date in s:
                                    s = s.replace(date, '<' + tag + '>' + date + '</' + tag + '>')
                                elif fdate in s:
                                    s = s.replace(fdate, '<' + tag + '>' + fdate + '</' + tag + '>')
                                elif space_missed_date in s:
                                    date = space_missed_date
                                    s = s.replace(date, '<' + tag + '>' + date + '</' + tag + '>')
                                elif old_fashioned_d1 in s:
                                    date = old_fashioned_d1
                                    s = s.replace(date, '<' + tag + '>' + date + '</' + tag + '>')
                                elif old_fashioned_d2 in s:
                                    date = old_fashioned_d2
                                    s = s.replace(date, '<' + tag + '>' + date + '</' + tag + '>')
                
                                else:
                                #tag at least year if complete date cannot be found
                                    s = s.replace(year, '<' + tag + '>' + year + '</' + tag + '>')

                            else:
                                m_y = m + ' ' + year
                                if m_y in s:
                                    s = s.replace(m_y, '<' + tag + '>' + m_y + '</' + tag + '>')
                                else:
                                    s = s.replace(year, '<' + tag + '>' + year + '</' + tag + '>')
                                
                        else:
                            s = s.replace(year, '<' + tag + '>' + year + '</' + tag + '>')
                
                new_sents.append(s)
            #each round should update my_sents
            my_sents = new_sents
   
    return my_sents


def check_and_replace_literalval(my_sents, v, tag):
  
    new_sents = []
    for s in my_sents:
        
        if v in s:
            s = s.replace(v, '<' + tag + '>' + v + '</' + tag + '>')
        elif v.lower() in s:
            s = s.replace(v.lower(), '<' + tag + '>' + v.lower() + '</' + tag + '>')
        new_sents.append(s)
    return new_sents


def create_sentences_and_truth_value(my_sents, v, tag):
    new_sents = []
    found = False
    for s in my_sents:
        if v in s:
            s = s.replace(v, '<' + tag + '>' + v + '</' + tag + '>')
            found = True
        elif v.lower() in s:
            s = s.replace(v.lower(), '<' + tag + '>' + v.lower() + '</' + tag + '>')
            found = True
        new_sents.append(s)
    return [new_sents, True]



def tag_multipleInfoVals(tag, val, sentences):
    my_sents = sentences
    for v in val:
        v = v.rstrip()
        if '|' in v:
            
            parts = v.split('|')
            tag = parts.pop(0)
            #if tag is same as type: special case, do nothing
            if tag in ['category','claim_to_fame','faith']:
                for p in parts:
                    if ';' in p:
                        fparts = p.split(';')
                        for fp in fparts:
                            my_sents = check_and_replace_literalval(my_sents, fp, tag)
                    else:
                        my_sents = check_and_replace_literalval(my_sents, p, tag)
            elif tag in ['marriage','baptism','funeral']:
                if len(parts) == 2:
                    ltag = tag + '-location'
                    my_sents = check_and_replace_literalval(my_sents, parts[0], ltag)
                    dtag = tag + '-time'
    
                    my_sents = tag_dates(dtag, [parts[1]], my_sents)
                    
                elif len(parts) == 1:
                    if '-' in parts[0]:
                        dtag = tag + '-time'
                        my_sents = tag_dates(dtag, [parts[0]], my_sents)
                    else:
                        ltag = tag + '-location'
                        my_sents = check_and_replace_literalval(my_sents, parts[0], ltag)
            else:
                print tag
   
    return my_sents



def tag_literals(tag, val, sentences):
    my_sents = sentences
    
    for v in val:
        v = v.rstrip()
        if '|' in v:
            parts = v.split('|')
            if tag in parts[0]:
                v = parts[-1]
        #if sentences already in my_sent, they should be updated
        if v:
            my_sents = check_and_replace_literalval(my_sents, v, tag)
        
    return my_sents

def tag_sentences(tag, val, sentences):
    global literals, dates
    my_sents = sentences
    
    if tag in literals:
        
        my_sents = tag_literals(tag, val, sentences)
    elif tag in dates:
        my_sents = tag_dates(tag, val, sentences)
    elif tag in ['events','states']:
        my_sents = tag_multipleInfoVals(tag, val, sentences)

    return my_sents

def write_out_sentences(outdir, tag, sentf, tagged_sentences):
    d = outdir + tag
    if not os.path.exists(d):
        os.makedirs(d)
    outfile = open(d + '/' + sentf, 'w')
    for sentence in tagged_sentences:
        outfile.write(sentence)
    outfile.close()


def tag_values(val_dict, sentf, outdir):
    my_text = open(sentf, 'r')
    #file size is generally not too big and we need to go through them several times
    sentences = my_text.readlines()
    for tag, val in val_dict.items():
        if not tag == 'name':
            tagged_sentences = tag_sentences(tag, val, sentences)
            sfname = sentf.split('/')[-1]
            write_out_sentences(outdir, tag, sfname, tagged_sentences)


def create_value_dictionary(inputfile):
    text = open(inputfile, 'r')
    my_val_dict = {}
    for line in text:
        parts = line.split(',')
        #first element is the key
        key = parts.pop(0)
        my_val_dict[key] = parts

    return my_val_dict


def process_files(indir, sentdir, outdir = ''):
    initiate_month_dict()
    for f in os.listdir(indir):
        if '.csv' in f:
            my_val_dict = create_value_dictionary(indir + f)
            my_id = f.split('.')[0]
            if '_' in my_id:
                my_id = my_id.split('_')[0]
        #    for fn in sentdir:
        #        if my_id in fn:
        #                   tag_values(my_val_dict, sentdir + fn, outdir)
        #not optimal: this goes through the entire file every single time...
            for fn in os.listdir(sentdir):
                if my_id in fn:
                    sfile = sentdir + fn
                    tag_values(my_val_dict, sfile, outdir)


def main(argv=None):
    
    if argv is None:
        argv = sys.argv
        if len(argv) < 3:
            print 'Error, you must provide an input (.csv files) and a sentence directory. You may optionally define an output directory'
        elif len(argv) < 4:
            process_files(argv[1], argv[2])
        else:
            process_files(argv[1], argv[2], argv[3])

if __name__ == '__main__':
    main()