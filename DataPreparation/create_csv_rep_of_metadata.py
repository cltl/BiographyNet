#!usr/bin/python
# -*- coding: utf-8 -*-

from xml.etree.ElementTree import ElementTree
import metadata
import create_metadata_object
import merge_metadata_objects
import os
import sys


def getnames(nameList):
    all_names = []
    for names in nameList:
        for name in names:
            name_s = name.returnName()
            if name_s not in all_names:
                all_names.append(name_s)
    n_value = ''
    for n in all_names:
        n_value += n + ','
    n_value = n_value.rstrip(',')
    return n_value


def retrieve_dates(eventList):
    my_dates = []
    for event in eventList:
        date = event.date
        date_s = date.returnDate()
        if not date_s in my_dates:
            my_dates.append(date_s)

    dates = ''
    for d in my_dates:
        dates += d + ','

    return dates.rstrip(',')


def retrieve_locations(eventList):
    locs = []
    for event in eventList:
        loc = event.location
        if not loc in locs:
            locs.append(loc)
    locations = ''
    for l in locs:
        locations += l + ','
    return locations.rstrip(',')


def write_birth_and_death_info(outfile, cMetadata):
    birth_date = retrieve_dates(cMetadata.birth)
    if birth_date:
        outfile.write('birthdate,' + birth_date + '\n')
    birth_place = retrieve_locations(cMetadata.birth)
    if birth_place:
        outfile.write('birthplace,' + birth_place + '\n')
    death_date = retrieve_dates(cMetadata.death)
    if death_date:
        outfile.write('deathdate,' + death_date + '\n')
    death_place = retrieve_locations(cMetadata.death)
    if death_place:
        outfile.write('deathplace,' + death_place + '\n')


def write_out_parents(outfile, cMetadata):
    father = getnames(cMetadata.father)
    if father:
        outfile.write('father,' + father + '\n')
    mother = getnames(cMetadata.mother)
    if mother:
        outfile.write('mother,' + mother + '\n')

def create_state_value(state):
    my_val = ''
    if state.beginDate:
        bdate = state.beginDate.returnDate()
        my_val += '|' + bdate + ';'
    if state.endDate:
        edate = state.endDate.returnDate()
        if ';' in my_val:
            my_val += edate
        else:
            my_val += '|;' + edate
    if state.location:
        my_val += '|' + state.location
    if state.description:
        my_val += '|' + state.description

    return my_val

def checkvals(knownvals, val):
    if val in knownvals:
        return True
    else:
        return False



def retrieve_other_states(stateList):
    my_states = ''
    for sList in stateList:
        my_states += retrieve_states(sList)
    return my_states.rstrip(',')

def retrieve_states(sList):
    my_states = {}
    for state in sList:
        label = state.label
        #create value for state
        val = create_state_value(state)
        #make sure no empty states are added
        if val:
            if not label in my_states:
                my_states[label] = [val]
            elif not checkvals(my_states[label], val):
                my_states[label].append(val)

    states = ''
    for label, vals in my_states.items():
        for v in vals:
            states += label + v + ','
    return states

def write_out_states(outfile, cMetadata):
    states = retrieve_other_states(cMetadata.otherStates)
    if states:
        outfile.write('states,' + states + '\n')

# 1. go through other parts of corpus and see what we can create for them
# religion
# otherEvents
# 2. when done: double check all categories are covered

def retrieve_events(eventList):
    events = ''
    for event in eventList:
        label = event.label
        date = event.date.returnDate()
        location = event.location
        
        if label and (location or date != 'YY-YY-YY'):
            new_event = label + '|' + location + '|' + date
            events += new_event + ','
    
    return events

def retrieve_other_events(eventList):
    my_events = ''
    for eList in eventList:
        my_events += retrieve_events(eList)
    return my_events.rstrip(',')


def write_out_other_events(outfile, cMetadata):
    my_events = retrieve_other_events(cMetadata.otherEvents)
    if my_events:
       
        try:
            outline = 'events,' + my_events + '\n'
            outline = outline.encode('utf8')
            outfile.write(outline)
        except:
                print outfile, my_events

def write_out_education_occupation(outfile, cMetadata):
    #education and occupation are repeated in values, but this is not a problem for now
    for education in cMetadata.education:
        if education:
            educList = retrieve_states(education)
            outfile.write('education,' + educList + '\n')

    for occupation in cMetadata.occupation:
        if occupation:
            occupList = retrieve_states(occupation)
            outfile.write('occupation,' + occupList + '\n')

def write_out_metadata(cMetadata, current_id, outdir):
   
    my_outfile = open(outdir + current_id + '.csv', 'w')
    my_outfile.write('name,' + getnames(cMetadata.name) + '\n')
    write_birth_and_death_info(my_outfile, cMetadata)
    write_out_parents(my_outfile, cMetadata)
    write_out_states(my_outfile, cMetadata)
    write_out_education_occupation(my_outfile, cMetadata)
    write_out_other_events(my_outfile, cMetadata)

def process_files(indir, outdir):

    my_infiles = os.listdir(indir)
    current_id = ''
    meta_list = []
    for f in my_infiles:
        if f.endswith('.xml'):
            fid = f.split('_')[0]
            my_bio = ElementTree().parse(indir + f)
            myMetadata = create_metadata_object.create_metadataObject(my_bio)
            if fid == current_id:
                meta_list.append(myMetadata)
            else:
                #should not be done for the first biography
                if current_id:
                    complete_metadata = merge_metadata_objects.merge_metadata_objects(meta_list)
                    write_out_metadata(complete_metadata, current_id, outdir)
                meta_list = [myMetadata]
                current_id = fid
#make sure last data is also written out
    complete_metadata = merge_metadata_objects.merge_metadata_objects(meta_list)
    write_out_metadata(complete_metadata, current_id, outdir)


def main(argv=None):
    
    if argv is None:
        argv = sys.argv
        if len(argv) < 3:
            print 'Error, you must provide an input and output directory'
        else:
            process_files(argv[1], argv[2])


if __name__ == '__main__':
    main()