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
        tSpanObj = timex.get_span()
        if tSpanObj:
            tSpan = tSpanObj.get_span_ids()
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



def create_prof_fam_dicts(nafobj):
    '''
    Retrieves all occupation and family relations present in NAF
    '''
    
    profSpans = {}
    famRelSpans = {}
    otherInfo = {}
    for markable in nafobj.get_markables():
        #assumes there's only one span per mark_id
        mark_id = markable.get_id()
        for exref in markable.get_external_references():
            span = markable.get_span().get_span_ids()
            if not 'family' in exref.get_resource():
                profSpans[mark_id] = span
            #for now we only have occupation and family
            else:
                famRelSpans[mark_id] = span
            ###these are embedded in externalReferences, but not used for now anyway
            #resource = markable.get_resource()
            #reference = markable.get_reference()
            lemma = markable.get_lemma()
            #information for class and span
            otherInfo[mark_id] = [lemma, span]
                    
    return profSpans, famRelSpans, otherInfo


def create_entity_sentence_dict(nafobj):
    '''
    Looks up for all named entities of type PER(SON) in which sentence they occur
    And all markables that refer to a family member
    Stores the entities occurring in a specific sentence
    '''
    sent2entity = {}
    for entity in nafobj.get_entities():
        if entity.get_type() == 'PER':
            #for now entity typically has only one ref (each ref has own entity entry coreference is found in coref layer)
            for reference in entity.get_references():
                ref = reference
            span = ref.get_span().get_span_ids()
            term = nafobj.get_term(span[0])
            tspan = term.get_span().get_span_ids()
            tok = nafobj.get_token(tspan[0])
            sent_nr = tok.get_sent()
            if sent_nr in sent2entity:
                sent2entity[sent_nr].append(entity)
            else:
                sent2entity[sent_nr] = [entity]

    for markable in nafobj.get_markables():
        for exRef in markable.get_external_references():
            if 'family' in exRef.get_resource():
                span = markable.get_span().get_span_ids()
                #markables have span of tokens
                tok = nafobj.get_token(span[0])
                sent_nr = tok.get_sent()
                if sent_nr in sent2entity:
                    sent2entity[sent_nr].append(markable)
                else:
                    sent2entity[sent_nr] = [markable]


    return sent2entity


def get_term_that_includes_token(nafobj, tokId):
    '''
    goes through naf file and returns the identifier of the term that has a specific token in its span
    in current pipeline setup, tokens do not appear in the span of more than one term
    '''
    for term in nafobj.get_terms():
        span = term.get_span().get_span_ids()
        if tokId in span:
            return term.get_id()


def is_single_np_pattern(dep_pattern):
    '''
    Checks if dep_pattern entails that two phrases are part of the same overall np
    '''
    #Assumption: if no head-argument (other than mod) in dep chain: the nouns occur in the same np
    singlePhrase = True
    for drel in dep_pattern:
        if 'hd' in drel and not 'mod' in drel:
            singlePhrase = False
    return singlePhrase


def get_entity_span(nafobj, entity):
    '''
    Returns the span of an entity
    '''
    #we only take the first, since each entity has, at this point, it's own entry
    #(mutliple references per entity should not occur, this is captured in coref layer)
    counter = 0
    for ref in entity.get_references():
        counter += 1
        eRef = ref
    eSpan = eRef.get_span().get_span_ids()
    if counter > 1:
        print >> sys.stderr, 'entity with multiple references'
    
    return eSpan

def obtain_depchain_entity_tid(nafobj, depextr, entId, tid):
    '''
    Returns the dependency chain between an entity and term id
    '''
    eSpan = get_entity_span(nafobj, entId)
    depchain = depextr.get_shortest_path(tid,eSpan[0])

    return depchain

def obtain_depchain_markable_wid(nafobj, depextr, markable, tid):
    '''
    Returns the dependency chain between a markable and term id
    '''
    tokSpan = markable.get_span().get_span_ids()
    firstTerm = get_term_that_includes_token(nafobj, tokSpan[0])
    depchain = depextr.get_shortest_path(tid, firstTerm)
    
    return depchain
    

def entities_from_known_prof_pattern(nafobj, profSpans, sent2entity):
    '''
    Checks if we have an appositive structure where profession follows a name or family relation
    '''
    depextr = nafobj.get_dependency_extractor()
    
    #create dictionary from prof to all entities it can be linked to according to algorithm
    prof2entities = {}
    for prof, span in profSpans.items():
        ftok = nafobj.get_token(span[0])
        sent_nr = ftok.get_sent()
        if sent_nr in sent2entity:
            #get list of all entities in sent_nr
            entities = sent2entity.get(sent_nr)
            #get term id of markable
            mark_tid = get_term_that_includes_token(nafobj, span[0])
            #for all entities get dependency path between mark_tid and first term:
            for entity in entities:
                if isinstance(entity, entity_data.Centity):
                    depchain = obtain_depchain_entity_tid(nafobj, depextr, entity, mark_tid)
                else:
                    depchain = obtain_depchain_markable_wid(nafobj, depextr, entity, mark_tid)
                    
                if is_single_np_pattern(depchain):
                    if not prof in prof2entities:
                        prof2entities[prof] = [entity]
                    else:
                        prof2entities[prof].append(entity)
                                       
    #reduce multiple entries to one
    print prof2entities
    prof2ent = {}
    for p, ents in prof2entities.items():
        if len(ents) == 1:
            entityId = get_entity_bio_id(nafobj, ents[0])
            prof2ent[p] = entityId
        else:
            dlength = 100
            ent = ents[0]
            p_wid = profSpans.get(p)[0]
            p_tid = get_term_that_includes_token(nafobj, p_wid)
            for entity in ents:
                if isinstance(entity, entity_data.Centity):
                    depchain = obtain_depchain_entity_tid(nafobj, depextr, entity, p_tid)
                else:
                    depchain = obtain_depchain_markable_wid(nafobj, depextr, entity, mark_tid)
                    
                    ###FIXME
                #if closer to profession, more likely interpretation
                ###FIXME: if multiple entities and pattern is PERS profession and PERS, it should be first person, not path
                
                ####FIXME: HOW DO ENTITIES FROM OTHER SENTENCES END UP HERE?
                if depchain and len(depchain) < dlength:
                    dlength = len(depchain)
                    ent = entity
            
            entityId = get_entity_bio_id(nafobj, ent)
            prof2ent[p] = entityId
            
            
    return prof2ent
                
def update_prof_spandict(profSpans, profFound):
    '''
    Creates new dictionary only containing profs en spans not accounted for yet
    '''    
    newPspans = {}            
    for prof in profSpans:
        if not prof in profFound:
            newPspans[prof] = profSpans.get(prof)
    return newPspans


def create_dep_dict(nafobj):
    '''
    Creates dictionary of terms to their head with label
    '''
    dep_dict = {}
    for dep in nafobj.get_dependencies():
        target = dep.get_to()
        info = [dep.get_from(), dep.get_function()]
        #some targets have multiple heads (structure sharing)
        if not target in dep_dict:
            dep_dict[target] = [info]
        else:
            dep_dict[target].append(info)
    return dep_dict
    
def find_heads_dep(head_dict, headOfent, soughtRel):
    '''
    Returns the identifier of the subject of the head, if given.
    '''
    #consider making this recursive, if more structures can be found that way
    deps = head_dict.get(headOfent)
    for info in deps:
        if soughtRel in info[1]:
            return info[0]


def reform_identified_entities(nafobj, targets2ents, sent2entity):
    '''
    Check if only one entity found in pred structures and check if named entity
    '''
    #reduce entity to one per target and see if it is a named entity
    target2entity = {}
    for t, ents in targets2ents.items():
        my_ent_term = ents[0]
        term = nafobj.get_term(my_ent_term)
        #if pronoun, do nothing
        if term.get_pos() == 'pron':
            entityId = get_entity_bio_id(nafobj, ents[0])
            target2entity[t] = entityId
        else:
            #take first token of term for retrieving sentence
            headwid = term.get_span().get_span_ids()[0]
            tok = nafobj.get_token(headwid)
            sent_nr = tok.get_sent()
            myent = ''
            
            if sent_nr in sent2entity:
                for ent in sent2entity.get(sent_nr):
                    if isinstance(ent, entity_data.Centity):
                        eSpan = get_entity_span(nafobj, ent)
                    else:
                        #markables have tokens in span
                        wSpan = ent.get_span().get_span_ids()
                        eSpan = get_term_span_from_tokspan(nafobj, wSpan)
                    if my_ent_term in eSpan:
                        myent = ent
            if myent:
                entityId = get_entity_bio_id(nafobj, myent)
                target2entity[t] = entityId            
            
            
        if len(ents) > 1:
            print >> sys.stderr, 'term is predicative to more than one element'

    return target2entity


def find_copula_structures(targetSpans, dep_dict, head_dict, nafobj, sent2entity):
    '''
    Identifies whether identity is expressed connecting target and entity through a copula
    '''
    targets2ents = {}
    for t, span in targetSpans.items():
        for wid in span:
            termId = get_term_that_includes_token(nafobj, wid)
            deps = dep_dict.get(termId)
            #print wid, deps
            for info in deps:
                
                if 'hd/predc' in info[1]:
                    headOfent = info[0]
                    entity = find_heads_dep(head_dict, headOfent, 'hd/su')
                    if entity:
                        if not t in targets2ents:
                            targets2ents[t] = [entity]
                        else:
                            targets2ents[t].append(entity)
                    else:
                        print >> sys.stderr, 'INFO: no subject found in predicative structure for', headOfent
                elif 'crd/cnj' in info[1]:
                    headOfent = info[0]
                    onedepsup = dep_dict.get(headOfent)
                    for upinfo in onedepsup:
                        if 'hd/predc' in upinfo[1]:
                            headOfent = info[0]
                            entity = find_heads_dep(head_dict, headOfent, 'hd/su')
                            if entity:
                                if not t in targets2ents:
                                    targets2ents[t] = [entity]
                                else:
                                    targets2ents[t].append(entity)
                            else:
                                print >> sys.stderr, 'INFO: no subject found in predicative structure for', headOfent
    #reduce entity to one per target and see if it is a named entity
    target2entity = reform_identified_entities(nafobj, targets2ents, sent2entity)
    
    return target2entity

def get_entity_bio_id(nafobj, entity):
    '''
    Gets the id for entity as used in biographynet output from entity or markable object
    '''
    if isinstance(entity, entity_data.Centity):
        span = get_entity_span(nafobj, entity)
    elif isinstance(entity, markable_data.Cmarkable):
        wspan = entity.get_span().get_span_ids()
        span = get_term_span_from_tokspan(nafobj, wspan)
    else:
        span = [entity]
    span_string = ''.join(span)
    return span_string



def get_term_span_from_tokspan(nafobj, wspan):
    '''
    Goes through a list of token and returns list of terms in which they occur
    '''
    tspan = []
    for term in nafobj.get_terms():
        myspan = term.get_span().get_span_ids()
        for wid in myspan:
            if wid in wspan:
                tspan.append(term.get_id())
    
    return sorted(tspan)

def get_related_triples(prof2ent, nafobj, otherInfo):
    '''
    Returns a list of triples connecting entities to the profession they represent
    '''
    triples = []
    for prof, ent in prof2ent.items():
        info = otherInfo.get(prof)
        wspan = info[-1]
        tspan = get_term_span_from_tokspan(nafobj, info[1])
        pid = ''.join(tspan)
        triples.append([pid,'bgn:isAssociatedWith','PROXY'])
        triples.append([pid,'a','bgn:profession'])
        triples.append([ent,'dbo:profession',pid])
        mentionId = ''.join(wspan)
        triples.append([pid,'gaf:denotedBy',mentionId])
        
    return triples   


def create_head_dict(nafobj):
    '''
    Goes through nafobj and creates dictionary indicating for each term all its dependents
    '''
    head2deps = {}
    for dep in nafobj.get_dependencies():
        head = dep.get_from()
        info = [dep.get_to(), dep.get_function()]
        if not head in head2deps:
            head2deps[head] = [info]
        else:
            head2deps[head].append(info)

    return head2deps


def find_closest_link_core_arg(head_dict, dep_dict, head, dep):
    '''
    recursive function that takes head and dependent as input and returns the term 
    that is closest linked su/obj other than the dependent
    '''
    deps = head_dict.get(head)
    term = ''
    for info in deps:
        if not info[0] == dep:
            if 'obj' in info[1]:
                term = info[0]
            #if both su and obj occur on equal level, the obj is the preferred candidate
            elif not term and 'su' in info[1]:
                term = info[0]
    if term:
        return term
    
    new_head = dep_dict.get(head)[0][0]
    return find_closest_link_core_arg(head_dict, dep_dict, new_head, head)

def identify_as_occupation_relations(nafobj, dep_dict, head_dict, targetSpans, sent2entity):
    '''
    Checks if occupation is related to entity in construction 'started/worked/Xed as...'
    '''
    targets2ents = {}
    #create head_dict (that provides information on all dependents of a given term
    for t, span in targetSpans.items():
        for wid in span:
            termId = get_term_that_includes_token(nafobj, wid)
            deps = dep_dict.get(termId)
            for info in deps:
                if 'cmp/body' in info[1]:
                    #possibly also check if head has indeed label 'als'
                    struc_head = info[0]
                    #go back up through head of structure until reaching a head that also has an obj1 (first choice) or su (second choice)
                    eTermId = find_closest_link_core_arg(head_dict, dep_dict, struc_head, termId)
                    if not t in targets2ents:
                        targets2ents[t] = [eTermId]
                    else:
                        targets2ents[t].append(eTermId)
    #store
    #as for copula: check if pronoun, if entity, else print that it's neither
    target2entity = {}
    for t, ents in targets2ents.items():
        entityId = get_entity_bio_id(nafobj, ents[0])
        my_ent_term = entityId
        term = nafobj.get_term(ents[0])
        #if pronoun, do nothing
        if term.get_pos() == 'pron':
            target2entity[t] = entityId
        else:
            #take first token of term for retrieving sentence
            headwid = term.get_span().get_span_ids()[0]
            tok = nafobj.get_token(headwid)
            sent_nr = tok.get_sent()
            myent = ''
            if sent_nr in sent2entity:
                for ent in sent2entity.get(sent_nr):
                    if isinstance(ent, entity_data.Centity):
                        eSpan = get_entity_span(nafobj, ent)
                    else:
                        wSpan = ent.get_span().get_span_ids()
                        eSpan = get_term_span_from_tokspan(nafobj, wSpan)
                    if my_ent_term in eSpan:
                        myent = ent
            if myent:
                entityId = get_entity_bio_id(nafobj, ent)
                target2entity[t] = entityId            
                    
            
        if len(ents) > 1:
            print >> sys.stderr, 'term is predicative to more than one element'

    return target2entity               


def identify_possessive_relations(nafobj, famRelSpans, head_dict):
    '''
    identifies relation between 'his' and 'daughter' in 'his daughter'
    '''
    
    famOfX = {}
    for fam, wspan in famRelSpans.items():
        #family names in our ontology are only one word
        termId = get_term_that_includes_token(nafobj, wspan[0])
        depRels = head_dict.get(termId)
        #not every term is a head
        if depRels:
            for dRel in depRels:
                if 'hd/det' in dRel[1]:
                    mydepTerm = nafobj.get_term(dRel[0])
                    if 'VNW(bez' in mydepTerm.get_morphofeat():
                        famOfX[fam] = [mydepTerm]

    return famOfX


def identify_family_of_patterns(nafobj, famRelSpans, sent2entity, head_dict):
    '''
    identifies structures such as brother van X
    '''
    famOfX = {}
    for fam, wspan in famRelSpans.items():
        #family names in our ontology are only one word
        termId = get_term_that_includes_token(nafobj, wspan[0])
        depRels = head_dict.get(termId)
        if depRels:
            for dRel in depRels:
                if 'hd/mod' in dRel[1]:
                    potPPhead = nafobj.get_term(dRel[0])
                    if potPPhead.get_lemma() == 'van':
                        embRels = head_dict.get(dRel[0])
                        for eRel in embRels:
                            if 'hd/obj1' in eRel[1]:
                                eTerm = nafobj.get_term(eRel[0])
                            
                            #if conjunction, we need to go one level deeper, else we're there..
                                if not eTerm.get_pos() == 'vg':
                                    famOfX[fam] = [eRel[0]]
                                else:
                                    conKids = head_dict.get(eRel[0])
                                    for dep in conKids:
                                        if 'crd/cnj' in dep[1]:
                                            if not fam in famOfX:
                                                famOfX[fam] = [dep[0]]
                                            else:
                                                famOfX[fam].append(dep[0])
                                                
    #check if entity
    
    famOfXfin = {}                              
    for fam, ents in famOfX.items():
        for ent in ents:
            term = nafobj.get_term(ent)
            wspan = term.get_span().get_span_ids()
            mytok = nafobj.get_token(wspan[0])
            sent_nr = mytok.get_sent()
            if sent_nr in sent2entity:
                for myent in sent2entity.get(sent_nr):
                    
                    if isinstance(myent, entity_data.Centity):
                        eSpan = get_entity_span(nafobj, myent)
                    else:
                        wSpan = myent.get_span().get_span_ids()
                        eSpan = get_term_span_from_tokspan(nafobj, wSpan)
                    #store entity if entity
                    if ent in eSpan:
                        if not fam in famOfXfin:
                            famOfXfin[fam] = [myent]
                        else:
                            famOfXfin[fam].append(myent)
                   
                    #else keep termId, we'll check later if it belongs to a profession
            if not fam in famOfXfin:
                famOfXfin[fam] = [ent]
    
    return famOfXfin
                        
                    
            


def extract_Ofwhom_family(nafobj, famRelSpans, sent2entity, head_dict):
    '''
    Functions that aim to determine of whom someone is family
    '''
    #check if determiner is possessive
    famOfXpos = identify_possessive_relations(nafobj, famRelSpans, head_dict)
    famOfXvan = identify_family_of_patterns(nafobj, famRelSpans, sent2entity, head_dict)
    
    #merge the two dictionaries
    for fam, val in famOfXpos.items():
        #this is unlikely to occur, not sure what the right interpretation would be
        if fam in famOfXvan:
            for v in val:
                famOfXvan.append(v)
        else:
            famOfXvan[fam] = val  
    return famOfXvan


def separated_by_verb_or_prep(nafobj, entity, tokId):
    '''
    Returns true if between a token and entity some verb or preposition is placed
    '''
    separated = False
    term = get_term_that_includes_token(nafobj, tokId)
    for ref in entity.get_references():
        entSpan = ref.get_span().get_span_ids()
        termNr = int(term.split('_')[1])
    #if entity preceeds term, start at the end
        if int(entSpan[0].split('_')[1]) < termNr:
            eStart = int(entSpan[-1].split('_')[1]) + 1
            for x in range(eStart, termNr):
                myTermId = 't_' + str(x)
                myTerm = nafobj.get_term(myTermId)
                if myTerm.get_pos() == 'verb' or myTerm.get_pos() == 'prep':
                    separated = True
        else:
            eEnd = int(entSpan[0].split('_')[1])
            for x in range(termNr + 1, eEnd):
                myTermId = 't_' + str(x)
                myTerm = nafobj.get_term(myTermId)
                if myTerm.get_pos() == 'verb' or myTerm.get_pos() == 'prep':
                    separated = True
    return separated


def get_distance_between_dist(nafobj, ent, compTok):
    '''
    Checks distance between entity and comparing token
    '''
    cTerm = get_term_that_includes_token(nafobj, compTok)
    difference = 100
    for ref in ent.get_references():
        entSpan = ref.get_span().get_span_ids()
        cTnr = int(cTerm.split('_')[1])
        if int(entSpan[0].split('_')[1]) < cTnr:
            dist = cTnr - int(entSpan[-1].split('_')[1])
            
        else:
            dist = int(entSpan[0].split('_')[1]) - cTnr
        if dist < difference:
            difference = dist
    return difference

def identify_family_member_in_pattern(nafobj, famRelSpans, sent2entity):
    '''
    Checks if name of family member is mentioned before or after fam relation name without syntactic connections
    '''
    famMems = {}
    for fam, wspan in famRelSpans.items():
        ftok = nafobj.get_token(wspan[0])
        sent_nr = ftok.get_sent()
        if sent_nr in sent2entity:
            myents = sent2entity.get(sent_nr)
            for ent in myents:
                #we're only interested in named entities at this point
                if isinstance(ent, entity_data.Centity):
                    if not separated_by_verb_or_prep(nafobj, ent, wspan[0]):
                        if not fam in famMems:
                            famMems[fam] = ent
                        else:
                            cur_ent = famMems.get(fam)
                            cDist = get_distance_between_dist(nafobj, cur_ent, wspan[0])
                            #if newly found is closer to term than old one, take new one
                            if  cDist > get_distance_between_dist(nafobj, ent, wspan[0]):
                                famMems[fam] = ent
    return famMems                      
    #select unique one if multiple found (closest)
   
def subj_of_copula(targetSpans, dep_dict, head_dict, nafobj, sent2entity):
    '''
    Identify who family member is when family term is subject and name is object
    '''
    targets2ents = {}
    for t, span in targetSpans.items():
        for wid in span:
            termId = get_term_that_includes_token(nafobj, wid)
            deps = dep_dict.get(termId)
            for info in deps:
                if 'hd/su' in info[1]:
                    headOfent = info[0]
                    entity = find_heads_dep(head_dict, headOfent, 'hd/predc')
                    
                    if entity:
                        if not t in targets2ents:
                            targets2ents[t] = [entity]
                        else:
                            targets2ents[t].append(entity)
                elif 'crd/cnj' in info[1]:
                    depsup = dep_dict.get(info[0])
                    for info in depsup:
                        if 'hd/su' in info[1]:
                            headOfent = info[0]
                            entity = find_heads_dep(head_dict, headOfent, 'hd/predc')
                            if entity:
                                print t, entity
                                if not t in targets2ents:
                                    targets2ents[t] = [entity]
                                else:
                                    targets2ents[t].append(entity)
                    
    #check if only one entity and if named ent (retrieving the named entity)
   
    target2entity = reform_identified_entities(nafobj, targets2ents, sent2entity)
    print target2entity
    return target2entity

def extract_who_is_family(nafobj, famRelSpans, sent2entity, dep_dict, head_dict):
    '''
    Functions that determine who the family member is
    '''
    #patterns
    
    famMems = identify_family_member_in_pattern(nafobj, famRelSpans, sent2entity)
    #copula
   
    famMems.update(find_copula_structures(famRelSpans, dep_dict, head_dict, nafobj, sent2entity))
    
    famMems.update(subj_of_copula(famRelSpans, dep_dict, head_dict, nafobj, sent2entity))
    
    
    
    return famMems


def get_namespace(exRef):
    '''
    Determines the namespace we should use based on exRef resource
    '''
    if 'stevensr' in exRef.get_resource():
        prefix = 'stevensFam:'
    else:
        prefix = 'bnFam:'
    return prefix


def create_family_triples(nafobj, fam_members, famOfX):
    '''
    derive triples that indicate family relations
    '''
    my_triples = []
    intriple = set()
    for f, mem in fam_members.items():
        
        if isinstance(mem, entity_data.Centity):
            bioId = get_entity_bio_id(nafobj, mem)
        elif isinstance(mem, str):
            bioId = mem
        #get family relation for triple
        markable = nafobj.get_markable(f)
        for exRef in markable.get_external_references():
            #check which is ontology of relation
            prefix = get_namespace(exRef)
            pred = prefix + exRef.get_reference()
            triple = [bioId, pred]
            
            if f in famOfX:
                tripObjs = famOfX.get(f)
                for tObj in tripObjs:
                    if isinstance(tObj, entity_data.Centity):
                        obBioId = get_entity_bio_id(nafobj, tObj)
                    elif isinstance(tObj, str):
                        obBioId = tObj
                    else:
                        obBioId = ''
                    if obBioId:    
                        new_trip = []   
                        for t in triple:
                            new_trip.append(t)
                        new_trip.append(obBioId)
                        my_triples.append(new_trip)
                        intriple.add(f)
                    
                            
            #else:    
            #    print f, mem, triple
 
    for f, x in famOfX.items():
        #we already have triples for markables in intriple
        if not f in intriple:
            #get id of family relation word, create triple
            markable = nafobj.get_markable(f)
            wSpan = markable.get_span().get_span_ids()
            tSpan = get_term_span_from_tokspan(nafobj, wSpan)
            bioId = ''.join(tSpan)
            for exRef in markable.get_external_references():
                prefix = get_namespace(exRef)
                pred = prefix + exRef.get_reference()
                for ent in x:
                    if isinstance(ent, entity_data.Centity):
                        ObjBId = get_entity_bio_id(nafobj, ent)
                    elif isinstance(ent, term_data.Cterm):
                        ObjBId = ent.get_id()
                    triple = [bioId, pred, ObjBId]
                    my_triples.append(triple)
    return my_triples 

def occupation_family_relation_linking(nafobj):
    '''
    Checks for all found occupations who they belong to
    '''
    print '++++++++++++'
    #collect professions, family terms and other relevant information
    profSpans, famRelSpans, otherInfo = create_prof_fam_dicts(nafobj)
    dep_dict = create_dep_dict(nafobj)
    head_dict = create_head_dict(nafobj)
    #create dictionary that indicates entities mentioned in a sentence
    sent2entity = create_entity_sentence_dict(nafobj)
    #1. see if part of pattern
    prof2ent = entities_from_known_prof_pattern(nafobj, profSpans, sent2entity)
    
    #only take next steps for professions not accounted for (reduced dict)
    profSpans = update_prof_spandict(profSpans, prof2ent)
    #2. see if part of structure with copula: link to subj
    
    prof2ent.update(find_copula_structures(profSpans, dep_dict, head_dict, nafobj, sent2entity))
    #3. again: only those we don't have yet
    
    profSpans = update_prof_spandict(profSpans, prof2ent)
    #3. see if part of 'als' structure: link to head noun or other most likely candidate noun
    prof2ent.update(identify_as_occupation_relations(nafobj, dep_dict, head_dict, profSpans, sent2entity))
    profSpans = update_prof_spandict(profSpans, prof2ent)
    
    #create triples based on prof2ent information
    mytriples = get_related_triples(prof2ent, nafobj, otherInfo)

    #maps markables to of whom family members
    famOfX = extract_Ofwhom_family(nafobj, famRelSpans, sent2entity, head_dict)
    
    #obtain who is family member
    fam_members = extract_who_is_family(nafobj, famRelSpans, sent2entity, dep_dict, head_dict)
    
    #patterns: if named entity before or after, no prep or verb in between
    #predicative in both directions
    fam_triples = create_family_triples(nafobj, fam_members, famOfX)
    
    mytriples += fam_triples

    if len(profSpans) > 0:
        print >> sys.stderr, 'PROFESSIONS LEFT', len(profSpans), profSpans


    return mytriples

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
   
    occupation_triples = occupation_family_relation_linking(nafobj)
    #print occupation_triples

if __name__ == '__main__':
    main()   