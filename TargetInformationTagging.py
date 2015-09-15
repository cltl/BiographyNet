#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on August 10, 2015
Functions for extracting target information from naf
@author: antske
'''

import sys
from KafNafParserPy import *

#global dictionaries that map strings to specific educations and institutes
inst_dict = {}
educ_dict = {}



def initiate_mapping_dictionaries(inst_file, education_file):
    '''
    Takes tsv files (provided as settings) as input and creates mappings from string to specific values for these files
    '''
    global inst_dict, educ_dict
    
    instin = open(inst_file, 'r')
    for line in instin:
        parts = line.split()
        inst_dict[parts[0]] = parts[1].rstrip()
    instin.close()
    
    eduin = open(education_file, 'r')
    for line in eduin:
        parts = line.split()
        educ_dict[parts[0]] = parts[1].rstrip()



def get_tokIds_from_termIds(nafobj, tIds):
    '''
    takes nafobj and list of term ids as input and returns a list of token ids
    '''
    wIds = []
    for tid in tIds:
        term = nafobj.get_term(tid)
        wIds += term.get_span().get_span_ids()
    return wIds

def get_surface_from_wIds(nafobj, wIds):
    '''
    takes nafobj and list of token ids as input and returns a string
    '''
    mysurface = ''
    
    end_offset = 0
    for wid in wIds:
        mytok = nafobj.get_token(wid)
        if not mysurface:
            end_offset = int(mytok.get_offset())
        #if location has multiple tokens, check if there is a space in between
        if not int(mytok.get_offset()) == end_offset:
            mysurface += ' '
            end_offset += 1
        mysurface += mytok.get_text()
        end_offset += int(mytok.get_length()) 

    return mysurface

def blnp_get_event_scope(nafobj):
    '''
    function that creates a dictionary with specific events and the scope of where to find relevant information
    '''
    #dictionary for target tokens of birth, death, study
    myEvents = {}
    
    event = ''
    terms = []
    count_terms = False
    for tok in nafobj.get_tokens():
        ttext = tok.get_text()
        if count_terms:
            terms.append(tok.get_id())
        if '*' in ttext:
            event = 'birth'
            count_terms = True
        elif event == 'birth' and (ttext == 't' or ttext == 'f'):
            myEvents[event] = terms
            terms = []
            event = 'death'
        elif event == 'death' and ttext in ['Zoon', 'Zn.','Dochter','dochter','zoon','was']:
            myEvents[event] = terms
            event = ''
            terms = []
            count_terms = False
        elif ttext == 'stud.' or ttext == 'Stud.' or ttext == 'Studie' or ttext == 'Stud':
            if event:
                if event in myEvents:
                    myEvent[event] += terms
                else:
                    myEvents[event] = terms
                terms = []
            count_terms = True
            event = 'study'
        elif ttext == 'dr.':
            if event:
                if event in myEvents:
                    myEvents[event] += terms
                else:
                    myEvents[event] = terms
                terms = []
            count_terms = True
            event = 'phd'
        elif ttext == 'pred' or ttext == 'pastoor':
            if event:
                if event in myEvents:
                    myEvents[event] += terms
                else:
                    myEvents[event] = terms
                terms = [tok.get_id()]
                event = 'profession'
        elif len(terms) > 15:
            if event:
                if event in myEvents:
                    myEvents[event] += terms
                else:
                    myEvents[event] = terms
            terms = []
            count_terms = False
            event = ''
    if event:
        if event in myEvents:
            myEvents[event] += terms
        else:
            myEvents[event] = terms
    
    return myEvents


def obtain_spans_outermost_bracketed(nafobj):
    '''
    Goes through tokens and returns list of spans that are between brackets
    In case of embeddings, the embedded bracketed string is included in the span (not separately identified)
    '''
    span_candidates = []
    
    brack_count = 0
    span = []
    for tok in nafobj.get_tokens():
        ttext = tok.get_text()
        if brack_count > 0:
            span.append(tok.get_id())
        if ttext == '(':
            brack_count += 1
        elif ttext == ')' and brack_count > 0:
            brack_count -= 1
            if brack_count == 0:
                #remove closing bracket from span
                span.pop()
                span_candidates.append(span)
                span = []
    return span_candidates


def has_birth_death_pattern(nafobj, span, dateDict):
    '''
    Identifies whether span has X date - Y date as pattern
    '''
    datesInBrackets = []
    for tid, val in dateDict.items():
        tSpan = val[0]
        if set(tSpan).issubset(set(span)):
            datesInBrackets.append[tid]
    #if two dates in brackets
    if len(datesInBrackets) == 2:
        fDate = datesInBrackets[0]
        lastId = dateDict[fDate][0][-1]
        nextId = 'w' + str(int(lastId.lstrip('w')) + 1)
        nextTok = nafobj.get_token(nextId)
        if '-' in nextTok:
            sDate = datesInBrackets[0]
            lastId = dateDict[sDate][0][-1]
            if lastId == span[-1]:
                return datesInBrackets
    return None
        
def identify_location_standard_bd_bracket_mapping(nafobj, cspan, fTok, lTok):
    '''
    Function that retrieves the string corresponding to a location from bracketed representation
    '''
    locToks = []
    start = False
    for tok in cspan:
        if start:
            if tok != lTok:
                locToks.append(tok)
            else:
                break
        elif tok == fTok:
            start = True
    location = get_surface_from_wIds(nafobj, locToks)
    return location
  
  

def standard_birth_death_bracket_mapping(nafobj):
    '''
    Function that retrieves birth & death date and location 
    '''
    
    span_candidates = obtain_spans_outermost_bracketed(nafobj)
    dateDict = {}
    
    for time in nafobj.get_timeExpressions():
        if time.get_type() == 'DATE':
            tSpan = time.get_span().get_span_ids()
            tValue = time.get_value()
            dateDict[time.get_id()] = [tSpan, tValue]
    
    myEvents = {}
    for canspan in span_candidates:
        dInB = has_birth_death_pattern(nafobj, canspan, dateDict)
        if dInB:
            firstD = dateDict.get(dInB[0])
            fdateTok = firstD[0][0]
            #first location is beginning of span until first date
            flocation = identify_location_standard_bd_bracket_mapping(nafobj, canspan, 0, fdateTok)
            myEvents['birth'] = [firstD[1],flocation]
            fdateend = firstD[0][-1]
            sStartTok = 'w' + str(int(fdateend.lstrip('w')) + 1)
            secD = dateDict.get(dInB[1])
            sdateTok = secD[0][0]
            slocation = identify_location_standard_bd_bracket_mapping(nafobj, canspan, sStartTok, sdateTok)
            myEvents['death'] = [secD[1],slocation]
            
    return myEvents


def identify_corresponding_wid(nafobj, wids, mystring):
    '''
    returns all wid ids from list of wids that have token that is included in the string
    '''
    rel_wids = []
    for wid in wids:
        tok = nafobj.get_token(wid)
        if tok.get_text() in mystring:
            rel_wids.append(wid)
    return rel_wids
    

def identify_study_institute(nafobj, wids):
    '''
    Checks in tokens associated with a specific study whether it can identify an institute
    '''
    global inst_dict
    relevant_string = get_surface_from_wIds(nafobj, wids)
    institutes = []
    rel_wids = []
    for k, v in inst_dict.items():
        if k in relevant_string:
            institutes.append(v)
            rel_wids += identify_corresponding_wid(nafobj, wids, k)
            
    return institutes, rel_wids
    #uses tsv file as input
    'http://www.seminarium.doopsgezind.nl'


def identify_study_topic(nafobj, wids):
    '''
    Checks in tokens associated with a specific study it can identify a subject
    '''
    global educ_dict
    relevant_string = get_surface_from_wIds(nafobj, wids)
    subjects = []
    rel_wids = []
    for k, v in educ_dict.items():
        if k in relevant_string:
            subjects.append(v)
            rel_wids += identify_corresponding_wid(nafobj, wids, k)
            
    return subjects, rel_wids
            
def checks_multiple_validity(event, oldvals, surface_string):
    '''
    Checks if multiple times or locations are valid (basic)
    '''
    #print event, oldvals, surface_string
    #professions sometimes state until when
    #FIXME: cannot do uncertainty for professions
    if event == 'profession':
        if '-' in surface_string:
            newvals = [oldvals[0]]
            for x in range(1, len(oldvals)):
                if oldvals[x-1] + '-' + oldvals[x] in surface_string:
                    newvals.append(oldvals[x] + '_end')
                else:
                    newvals.append(oldvals[x])
            return newvals, False        
    if ' of ' in surface_string:
        return oldvals, True
    elif '/' in surface_string:
        return oldvals, True
    #if no doubt expressed, check if second is specification of first
    elif '(' in surface_string and ')' in surface_string:
        surface_string = surface_string.replace('( ','(').replace(' )',')')
        if '(' + oldvals[1] + ')' in surface_string:
            newvals = [oldvals[0] + ' (' + oldvals[1] + ')']
            return newvals, False
        elif not event in ['birth','death']:
            if ' en ' in surface_string or ' later ' in surface_string or ' daarna ' in surface_string or ' ook ' in surface_string or ',' in surface_string:
               return oldvals, False
            else:
            #assume only first value is correct
                newval = [oldvals[0]]  
                return newval, False  
        else:
            newval = [oldvals[0]]
            return newval, False 
    #multiple locations or times only valid for education (not for birth/death)
    elif not event in ['birth','death']:
        if ' en ' in surface_string or ' later ' in surface_string or ' daarna ' in surface_string or ' ook ' in surface_string or ',' in surface_string:
            return oldvals, False
        else:
            #assume only first value is correct
            newval = [oldvals[0]]  
        
            return newval, False  
    else:
        newval = [oldvals[0]]
        return newval, False
            
def check_for_uncertainty(surface_string):
    '''
    checks if indication of uncertainty is present (circa, ca. for times) (omgeving/bij) for locations
    '''
    uncertain = []
    if ' ca. ' in surface_string or '(ca.' in surface_string or 'circa' in surface_string or 'rond' in surface_string:
        uncertain.append('time')
    if 'omgeving' in surface_string or 'rond' in surface_string:
        uncertain.append('loc')
    return uncertain
    



def verify_multiple_locs_and_times(eventInfo, eventDict, nafobj):
    '''
    Function that checks if multiple times and locations are indeed appropriate or whether mix-up between events occurred
    Also checks if other uncertainty present
    '''

    for event, vals in eventInfo.items():
        ofs = []
        wids = eventDict.get(event)
        surface_string = get_surface_from_wIds(nafobj, wids)
        if len(vals[0]) > 1:
            times, ofFlag = checks_multiple_validity(event, vals[0], surface_string)
            vals[0] = times
            if ofFlag:
                ofs.append('time')
        if len(vals[1]) > 1:
            locs, ofFlag = checks_multiple_validity(event, vals[1], surface_string)
            vals[1] = locs
            if ofFlag:
                ofs.append('loc')
        #uncertainty check for all values
        fuzzy = check_for_uncertainty(surface_string)
        vals.append(ofs)
        vals.append(fuzzy)
        eventInfo[event] = vals
    


def blnp_specific_events(nafobj):
    '''
    Gets events that are marked a specific way in the blnp
    '''
    eventDict = blnp_get_event_scope(nafobj)
    
    #register which tokens are used (for code expanding recall)
    used_wids = []
    eventInfo = {}
    #get dates of events
    for timex in nafobj.get_timeExpressions():
        tSpan = timex.get_span().get_span_ids()
        for ev, tids in eventDict.items():
            inRange = False
            for tid in tSpan:
                if tid in tids:
                    inRange = True
                else:
                    inRange = False
            if inRange:
                used_wids += tSpan
                if not ev in eventInfo:
                    eventInfo[ev] = [[timex.get_value()]]
                else:
                    eventInfo[ev][0].append(timex.get_value())
                
    
    #get locations of events
    for ne in nafobj.get_entities():
        if ne.get_type() == 'LOC':
            for ref in ne.get_references():
                eSpan = ref.get_span().get_span_ids()
                ewSpan = get_tokIds_from_termIds(nafobj, eSpan)
                for ev, wids in eventDict.items():
                    inRange = False
                    for wid in ewSpan:
                        if wid in wids:
                            inRange = True
                        else:
                            inRange = False
                    if inRange:
                        used_wids += ewSpan
                        location = get_surface_from_wIds(nafobj, ewSpan)
                        if ev in eventInfo:
                            if len(eventInfo[ev]) > 1:
                                eventInfo[ev][1].append(location)
                            else:
                                eventInfo[ev].append([location])
                        else:
                            #location should always be second item on the list
                            eventInfo[ev] = [[], [location]]
    #make sure there are enough vals for event
    for ev, vals in eventInfo.items():
        if len(vals) < 2:
            vals.append([])
            eventInfo[ev] = vals                  
    #get study and phd topics (if mentioned)
    if 'study' in eventDict:
        wids = eventDict.get('study')
        study_inst, newwids = identify_study_institute(nafobj, wids)
        used_wids += newwids
        if 'study' in eventInfo:
            eventInfo['study'].append(study_inst)
        else:
            #institute should always be the third item
            eventInfo['study'] = [[],[],study_inst]
        study_topic, newwids = identify_study_topic(nafobj, wids)
        eventInfo['study'].append(study_topic)
        
    if 'phd' in eventDict:
        wids = eventDict.get('phd')
        study_inst, newwids = identify_study_institute(nafobj, wids)
        used_wids += newwids
        if 'phd' in eventInfo:
            eventInfo['phd'].append(study_inst)
        else:
            #institute should always be the third item
            eventInfo['phd'] = [[],[],study_inst]
        study_topic, newwids = identify_study_topic(nafobj, wids)
        eventInfo['phd'].append(study_topic)
        
    verify_multiple_locs_and_times(eventInfo, eventDict, nafobj)   
    return eventInfo


def main(argv=None):
    
    if argv==None:
        argv = sys.argv

    if len(argv) < 3:
        print 'Please provides path to an institute mapping file and an education mapping file'
    else: 
        if len(argv) < 4:
            naffile = sys.stdin
            nafobj = KafNafParser(naffile)
        else:
            nafobj = argv[3]
        
        initiate_mapping_dictionaries(argv[1], argv[2])
        myEvents = blnp_specific_events(nafobj)
    for k, v in myEvents.items():
        print k, v

if __name__ == '__main__':
    main()   