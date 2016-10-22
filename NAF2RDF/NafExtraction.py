'''
Created on Feb 25, 2015

@author: antske
'''

from __future__ import print_function
from KafNafParserPy import *
from rdflib import Graph, Namespace, URIRef, RDF, ConjunctiveGraph, Literal
from rdflib.plugins.memory import IOMemory
from NafInfo import *
from TargetInformationTagging import *
import sys
import ftfy

#making this counter global
counter = 1
# extract all predicates that have semantic roles

#setting standard name, gender file 
#FIXME: temporal hack for development. This information should be taken from rdf
namegender = 'bio_gender_names.tsv'
ngDict = {}
gender = ''
firstname = ''
lastname = ''


instanceIds = []
foundPeople = {}
identityRels = {}



def initiate_ngDict(persId = ''):
    global namegender, ngDict, gender, firstname, lastname
    
    myvaluelines = open(namegender, 'r')
    for line in myvaluelines:
        vals = line.split('\t')
        vid = vals.pop(0)
        ngDict[vid] = vals
    if persId:
        vals = ngDict.get(persId)
        if not vals:
            print('Error, no entry for ' + persId + ' in database', file=sys.stderr)
        else:
            gender = vals[0]
            name = vals[1].split(':')
            lastname = name[1]#.decode('utf8')
            firstname = name[3]#.decode('utf8')
            if ' ' in firstname and firstname.endswith('van') or firstname.endswith('de'):
                firstname = firstname.split()[0]
        
    myvaluelines.close()



def identify_specific_info_from_tokens(nafobj):
    '''
    Function that goes through the token layer
    '''
    a = 1


def retrieve_events_and_roles(nafobj):
    '''
    Function that retrieves all predicates and roles from Naf file
    Returns a dictionary with spanTerm of predicate as key and list of its roles as value
    '''
    mySRL = nafobj.srl_layer
    myEvents = {}
    for pred in mySRL.get_predicates():
        pSpan = pred.get_span().get_span_ids()
        pRoles = pred.get_roles()
        roles = []
        for pRole in pRoles:
            roleName = pRole.get_sem_role()
            if not roleName == '#':
                roleSpan = pRole.get_span().get_span_ids()
                #FIXME: make object rather than list of length two
                roles.append([roleName,roleSpan])
        #in the current implementation, spans of predicates always have length 1
        myEvents[pSpan[0]] = roles  
    return myEvents

def get_external_links(entity):

    myExLinks = []
    for exRef in entity.get_external_references():
        myExLinks.append(exRef.get_reference())
    return myExLinks


def collect_named_entities(nafobj):
    '''
    Function that retrieves all identified named entities from a Naf file
    returns a list of entities represented as list (span + final element NE type)
    '''
    entityList = []
    for entity in nafobj.get_entities():
        eType = entity.get_type()
        eReferences = entity.get_references()
        for ref in eReferences:
            eSpan = ref.get_span().get_span_ids()
            if len(eSpan) == 0:
                print(entity.get_id())
            else:
                myEntity= NafEntity(entity.get_id(),eSpan,eType)
                if eType == 'LOC':
                    exRefLinks = get_external_links(entity)
                    myEntity.exRefs = exRefLinks
                entityList.append(myEntity)

    return entityList

def collect_time_expressions(nafobj):
    '''
    Function that retrieves time expressions from naf file
    '''
    timeExpressions = nafobj.get_timeExpressions()
    timeList = []
    for te in timeExpressions:
        tType = te.get_type()
        tValue = te.get_value()
        tSpanObj = te.get_span()
        if tSpanObj:
            tSpan = tSpanObj.get_span_ids()
            #FIXME: make object
            timeList.append([tType,tValue,tSpan])
        
    return timeList


def get_offset_and_surface_from_tokens(nafobj, wids):
    '''
    Function that takes a list of wIds as input and creates beginOffset, endOffset as output
    '''


    punctuation = ['.',',','?',':',';','"',')']
    surface_string = ''
    beginOffset = ''
    endOffset = ''
    endTokenLength = 0
    for w in wids:
        token = nafobj.get_token(w)
        if surface_string and not token in punctuation:
            surface_string += ' '
        surface_string += token.get_text()
        tokenOffset = int(token.get_offset())
        if not beginOffset:
            beginOffset = int(tokenOffset)
            endOffset = int(tokenOffset)
            endTokenLength = int(token.get_length())
        #we want the smallest offset for the beginning
        else:
            if beginOffset > tokenOffset:
                beginOffset = tokenOffset
            if endOffset < tokenOffset:
                endOffset = tokenOffset
                endTokenLength = int(token.get_length())

    closingOffset = endOffset + endTokenLength
    return [beginOffset, closingOffset], surface_string


def get_offset_and_surface(nafobj, term):
    '''
    Function that returns offset and surface form of a term.
    NB: in most cases, terms have a span of length one
    '''
    tSpan = term.get_span()
    wIds = tSpan.get_span_ids()
    
    offset, surface_string = get_offset_and_surface_from_tokens(nafobj, wIds)
    
    return offset, surface_string


def get_offset_and_surface_of_tSpan(nafobj, tSpan):
    '''
    Takes list of terms and nafobj as input and returns offset and surface string
    '''
    if len(tSpan) == 1:
        termObj = nafobj.get_term(tSpan[0])
        return get_offset_and_surface(nafobj, termObj)
    else:
        punctuation = ['.',',','?',':',';','"',')']
        bOffset = ''
        eOffset = ''
        sString = ''
        for term in tSpan:
            termObj = nafobj.get_term(term)
            offset, surface = get_offset_and_surface(nafobj, termObj)
            if not bOffset:
                bOffset = offset[0]
                eOffset = offset[1]
                sString = surface
            else:
                if offset[0] < bOffset:
                    bOffset = offset[0]
                if offset[1] > eOffset:
                    eOffset = offset[1]
                if not surface in punctuation:
                    sString += ' '
                sString += surface
    return [bOffset, eOffset], sString

def interpret_external_reference(exRef):
    '''
    Function that retrieves and stores information from external reference
    '''
    ref = exRef.get_reference()
    if ref and not 'mcr:' in ref:
        
        refconf = exRef.get_confidence()
        refsource = exRef.get_resource()
        subRefs = exRef.get_external_references()
        mysubrefs = []
        if subRefs:
            for subref in subRefs:
                mySubRef = interpret_external_reference(subref)
                if mySubRef:
                    if isinstance(mySubRef, list):
                        mysubrefs += mySubRef
                    else:
                        mysubrefs.append(mySubRef)
    #set confidence to unknown, if not given (explicitly marking uncertainty)
        if not refconf:
            refconf = 'unknown'
        if refsource and ref:
            
            myExRef = ExternalReference(ref, resource = refsource, confidence = refconf, exRefs = mysubrefs)
            return myExRef
        elif refsource:
            return mysubrefs
        else:
            return None
    
    return None

def get_term_external_references(term):
    '''
    Function that retrieves external references and confidence scores of a term
    '''
    myRefs = []
    exRefs = term.get_external_references()
    for exRef in exRefs:
        myExRef = interpret_external_reference(exRef)
        
        ####FILTER ONE
        #print myExRef
        if myExRef:
            myRefs.append(myExRef)

    return myRefs


def get_span_from_list(nafobj, termlist):
    
    widsList = []
    for t in termlist:
        term = nafobj.get_term(t)
        span_ids = term.get_span().get_span_ids()
        widsList += span_ids
        
    return widsList



def span_in_overlap_set(idList, oSet):
    '''
    returns True if at least one of the ids is part of a span from the set
    else returns False
    '''
    for i in idList:
        if i in oSet:
            return True
        
    return False


def is_constituent(termList, nafobj):
    '''
    Function that determines whether a set of terms forms a constituent
    '''
    firstTerm = termList[0]
    #retrieve all constituents that include the first term of the span
    chunks = nafobj.get_constituency_extractor().get_all_chunks_for_term(firstTerm)
    #check if it includes one that is identical to the list
    for chunk in chunks:
        if set(chunk[1]) == set(termList):
            return True
    return False


def list_overlap(list1, list2):
    '''
    Function that returns True if two list have common elements, else it returns False
    '''
    for e in list1:
        if e in list2:
            return True
    return False


def initiate_role_from_corresponding_NEs(nafobj, roleSpan, NElist):
    '''
    Function that compares NE span and role span and decides whether Span needs to be updated
    (in principle, prefer NE, but not if not constituent). It also returns the class of the NE
    '''
    ##NElist: a list of named entities represented as list (span + class)
    roles = []
    for ne in NElist:
        #classtype is last element in list
        myclass = ne.eType
        nespan = ne.eSpan
        #check if identical
        if list_overlap(nespan, roleSpan):
            myRole = NafRole(entityType = myclass)
            if is_constituent(nespan, nafobj) or len(nespan) < len(roleSpan):
                myRole.roleSpan = nespan
            else:
                myRole.roleSpan = roleSpan
            roles.append(myRole)
            
    return roles

def get_termSpan_from_wordSpan(nafobj, wList):
    my_terms = nafobj.get_terms()
    t_span = []
    for term in my_terms:
        span = term.get_span().get_span_ids()
        if list_overlap(span, wList):
            t_span.append(term.get_id())
    return t_span



def initiate_role_from_overlap_TE(nafobj, wSpan, tSpan, timeExList):
    '''
    Function that maps word span of time expression to term span of role
    Adapts span if necessary
    '''

    for te in timeExList:
        span = te[2]
        if list_overlap(span, wSpan):
            tValue = te[1]
            tClass = 'time_' + te[0]
            myRole = NafRole(entityType=tClass, timeValue=tValue)
            #if timex span corresponds to original span, keep original
            if set(span) == set(wSpan):
                myRole.roleSpan = tSpan
            else:
                #we make timex the new span
                updated_span = get_termSpan_from_wordSpan(nafobj, span)
                myRole.roleSpan = updated_span
    return myRole

def identify_head(phrase, edges):
    '''
    Function that retrieves the head of a phrase using edges
    '''
    head = ''
    daughters = []
    for edge in edges:
        if edge.get_to() == phrase:
            if edge.get_head():
                head = edge.get_from()
            else:
                daughters.append(edge.get_from())
    #FIXME: if no head there should always be exactly one daughter: check this
    if not head:
        head = daughters[0]
    if head.startswith('nt'):
        head = identify_head(head, edges)

    return head


def identify_chunk_head(nafobj, tList):
    '''
    Function that identifies head of a chunk
    '''
    #get all chunks the first term of span is part of
    phrase = nafobj.get_constituency_extractor().get_least_common_subsumer(tList[0],tList[1])

    head = ''
    for tree in nafobj.get_trees():
        terminals = tree.get_terminals_as_list()
        for terminal in terminals:
            tSpan = terminal.get_span().get_span_ids()
            if list_overlap(tSpan, tList):
                edges = tree.get_edges_as_list()
                terminals = tree.get_terminals_as_list()
                head = identify_head(phrase, edges)
                for terminal in terminals:
                    if terminal.get_id() == head:
                        headSpan = terminal.get_span().get_span_ids()
                        #FIXME: currently, all heads have span length one: this might change
                        head = headSpan[0]
                #this is the tree
    return head           
  
  
def disambiguate_pronoun(nafobj, tid):
    '''
    Function that tries to determine whether 'ze/zij' is fsg or pl
    '''
    #find out if term is subject and, if so, of which term 
    for dep in nafobj.get_dependencies():
        if dep.get_to() == tid and dep.get_function() == 'hd/su':
            hterm = nafobj.get_term(dep.get_from())
            hnumber = hterm.get_morphofeat().split(',')[-1].rstrip(')')
            if hnumber == 'ev':
                return 'bgn:pron_3fs'
            else:
                return 'bgn:pron_3p'
    #in written language 'ze' should not occur in other functions as subject
    #when feminine singular
    return 'bgn:pron_3p'
            

def get_pron_value(nafobj, lemma, tid):
    '''
    Function that looks up the label for a specific pronoun and returns this label
    '''
    lem2lab = {'hij':'bgn:pron_3ms',
               'hem':'bgn:pron_3ms',
               'haar':'bgn:pron_3fs',
               'ik':'bgn:pron_1s',
               'me':'bgn:pron_1s',
               'jij':'bgn:pron_2s',
               'je':'bgn:pron_2s',
               'jou':'bgn:pron_2s',
               'u':'bgn:pron_2',
               'we':'bgn:pron_1p',
               'ons':'bgn:pron_1p',
               'jullie':'bgn:pron_2p',
               'hun':'bgn:pron_3p',
               'hen':'bgn:pron_3p'}

    if lemma in lem2lab:
        return lem2lab.get(lemma)
    elif lemma in ['ze','zij']:
        return disambiguate_pronoun(nafobj, tid)
    #if not a clear well-known pronoun, return the empty string
    return ''


def get_poss_pron_value(lemma):
    '''
    Function that looks up the label for a specific possessive pronoun and returns this label
    '''
    lem2lab = {'haar':'bgn:pron_3fs',
               'zijn':'bgn:pron_3ms',
               'mijn':'bgn:pron_1s',
               'jouw':'bgn:pron_2s',
               'uw':'bgn:pron_2',
               'ons':'bgn:pron_1p',
               'onze':'bgn:pron_1p',
               'jullie':'bgn:pron_2p',
               'hun':'bgn:pron_3p'}
    if lemma in lem2lab:
        return lem2lab.get(lemma)
    return ''


def get_head_word_and_lemma(nafobj, roleSpan):
    '''
    Function that retrieves the head word of a span and returns
    its lemma, id, externalReferences and whether it's a pronoun
    '''
    headWord = []
    if len(roleSpan) == 1:
        term = nafobj.get_term(roleSpan[0])
    else:
        termId = identify_chunk_head(nafobj, roleSpan)  
        term = nafobj.get_term(termId)
      
    headWord.append(roleSpan[0])
    lemma = term.get_lemma()
    headWord.append(lemma)
    headWord.append(get_term_external_references(term))
    #get id of span
    termSpan = term.get_span().get_span_ids()
    wid = termSpan[0]
    tid = term.get_id()
    headWord.append(wid)
    if term.get_pos() == 'pron':    
        pron = get_pron_value(nafobj, lemma, tid)
    elif term.get_pos() == 'det' and 'VNW(bez' in term.get_morphofeat():
        pron = get_poss_pron_value(lemma)
    else:
        pron = ''
    headWord.append(pron)
    return headWord

def get_full_string_and_offsets(nafobj, nafrole, tSpan):
    '''
    Function that takes a nafRole and span of words as input and adds full string and offset to the object
    '''
    offset, surfaceString = get_offset_and_surface_of_tSpan(nafobj, tSpan)
    nafrole.offset = offset
    nafrole.roleString = surfaceString

def complete_srl_info(nafobj, srlEvents, namedEntities, timeExpressions):
    '''
    Function that uses term layer and text layer to identify additional information about events
    Link named entities to roles as well as time expressions
    '''
    
    #create set of timex ids and NE ids: for quick check
    NEids = set()
    for ne in namedEntities:
        for t in ne.eSpan:
            NEids.add(t)
    TEids = set()
    for te in timeExpressions:
        tSpan = te[2]
        for t in tSpan:
            TEids.add(t)
    #dictionary to store more complete information
    updatedEventsRoles = {}
    myterms = nafobj.get_terms()
    for term in myterms:
        tId = term.get_id()
        if tId in srlEvents:
            tLemma = term.get_lemma()
            tOffsets, surfacestring = get_offset_and_surface(nafobj, term)
            tExRefs = get_term_external_references(term)
            myEvent = NafEvent(predTid=tId,exrefs=tExRefs,offset=tOffsets, predString=surfacestring, lemma=tLemma,roles=[])
            myEvent.wIds = get_span_from_list(nafobj, [tId])
            #roles is a list, where each role is a list of length 2:
            #first element is role name, second is span ids
            tRoles = srlEvents.get(tId)
            for role in tRoles:
                roleSpan = role[1]

                headWordInfo = get_head_word_and_lemma(nafobj, roleSpan)
                headTerm = nafobj.get_term(headWordInfo[0])
                #for now: all role labels are propbank roles
                roleLab = 'pb:' + role[0]
                wSpan = get_span_from_list(nafobj, role[1])
                if span_in_overlap_set(NEids, roleSpan):
                    #update span (if needed), get class, returns a list of roles
                    myRoles = initiate_role_from_corresponding_NEs(nafobj, roleSpan, namedEntities)
                    
                    for myRole in myRoles:
                        get_full_string_and_offsets(nafobj, myRole, myRole.roleSpan)
                        #FIXME: this should be done while initiating roles..
                        myRole.wIds = wSpan
                        myRole.roleLabel= roleLab
                        myEvent.roles.append(myRole)
                else:
                    #FIXME: ugly; either head word is prep or headword in temp expression
                    if span_in_overlap_set(TEids, wSpan) and (headTerm.get_pos() == 'prep' or span_in_overlap_set(TEids, headTerm.get_span().get_span_ids())):
                        #update span (if needed), returns one role
                        myRole = initiate_role_from_overlap_TE(nafobj, wSpan, roleSpan, timeExpressions)
                        get_full_string_and_offsets(nafobj, myRole, myRole.roleSpan)
                        #FIXME: this should be done while checking overlap
                        myRole.wIds = wSpan
                        myRole.roleLabel = roleLab
                        myEvent.roles.append(myRole)
                    else:
                        #add pronoun info
                        myRole = NafRole(roleSpan = roleSpan, lemma=headWordInfo[1], exrefs=headWordInfo[2], head=headWordInfo[3],pron=headWordInfo[4])
                        get_full_string_and_offsets(nafobj, myRole, myRole.roleSpan)
                        myRole.wIds = wSpan
                        myRole.roleLabel = roleLab
                        myEvent.roles.append(myRole)
            updatedEventsRoles[tId] = myEvent
    
    return updatedEventsRoles               
                



def collect_naf_info(nafobj):
    
    srlEvents = retrieve_events_and_roles(nafobj)
    namedEntities = collect_named_entities(nafobj)
    timeExpressions = collect_time_expressions(nafobj)
    myEvents = complete_srl_info(nafobj, srlEvents, namedEntities, timeExpressions)
    
    return myEvents, namedEntities, timeExpressions

def create_identifier(prefix, suffixList):
    prefix = 'bgnProc:' + prefix
    if not '#' in prefix:
        prefix += '#'
    #if not prefix.endswith('/'):
    #   prefix += '/'
    for suffix in suffixList:
        prefix += suffix
    return prefix
  
  
def establish_identity(namestring):
    global firstname, lastname
    
    namestring = namestring.lower()
    if namestring == firstname or namestring == lastname:
        return True
    elif firstname in namestring and lastname in namestring:
        return True
    if '-' in lastname:
        maidenname = lastname.split('-')[0].rstrip().lstrip()
        if namestring == maidenname:
            return True
        if maidenname in namestring and firstname in namestring:
            return True
    return False
    
    
def update_foundPeople_and_identityRels(surfaceString, instanceId):

    global foundPeople, identityRels
    my_identifier = ''
    if len(foundPeople) == 0:
        foundPeople[surfaceString] = instanceId
    else:
        found = False
        to_add = False
        for k in foundPeople:
            if surfaceString in k or k in surfaceString:
                found = True
                my_identifier = foundPeople.get(k)
                identityRels[instanceId] = my_identifier
                if k in surfaceString:
                    #in this case, also add the longer string to foundPeople
                    to_add = True
        if to_add:
            foundPeople[surfaceString] = my_identifier
        if not found:
            foundPeople[surfaceString] = instanceId
    return my_identifier

def get_NE_triples(nafobj, prefix, NE, BiodesId):
    '''
    Analysis NE object and returns list of relevant triples
    '''
    global instanceIds
    NEtriples = []
    #last element in list is the class
    wIds = get_span_from_list(nafobj, NE.eSpan)
    offset, surfaceString = get_offset_and_surface_of_tSpan(nafobj, NE.eSpan)
    instanceId = create_identifier(prefix, NE.eSpan)
    mentionId = create_identifier(prefix, wIds)
    surfaceString = surfaceString.replace(',','')
    if len(NE.exRefs) > 0:
        for exRef in NE.exRefs:
            label = exRef.split('/')[-1]
            if label == surfaceString:
                instanceId = exRef
    if NE.eType in ['LOC','ORG','PER','MISC']:
        netype = 'bgn:' + NE.eType
    else:
        netype = 'bgn:MISC'
    NEtriples.append('bgnProc:' + prefix + '#personDes,bgn:hasAssociation,' + instanceId)
    NEtriples.append(instanceId + ',rdf:type,' + netype)
    NEtriples.append(instanceId + ',gaf:denotedBy,' + mentionId)
    NEtriples.append(mentionId + ',nif:beginIndex,"' + str(offset[0]) + '"')
    NEtriples.append(mentionId + ',nif:endIndex,"' + str(offset[1]) + '"')
    NEtriples.append(mentionId + ',nif:anchorOf,"' + surfaceString + '"')
    if establish_identity(surfaceString):
        persId = 'bgn:Person-' + BiodesId.split('_')[1]
        NEtriples.append(persId + ',owl:sameAs,' + instanceId + ',NG_nameIdentiy')
        instanceIds.append(instanceId)
    else:
        my_identifier = update_foundPeople_and_identityRels(surfaceString, instanceId)
        if my_identifier != '':
            NEtriples.append(my_identifier + ',owl:sameAs,' + instanceId + ',NG_nameIdentity')

    return NEtriples, instanceId, mentionId


def get_wids_info(nafobj, wid):

    tok = nafobj.get_token(wid)
    beginOffset = tok.get_offset()
    endOffset = int(beginOffset) + int(tok.get_length())
    text = tok.get_text()

    return beginOffset, endOffset, text

def surface_triples_from_wid(nafobj, wid, prefix):
    '''
    Returns surface triples based on wid
    '''
    prefix = 'bgnProc:' + prefix + '#'
    IDtriples = []
    #FIXME: This will need to be capable of dealing with multiwords
    if wid.count('w') > 1:
        print('[INFO] Error in identifier forming', wid, file=sys.stderr)
        wid = 'w' + wid.split('w')[1]
    tok = nafobj.get_token(wid)
    beginOffset = tok.get_offset()
    IDtriples.append(prefix + wid + ',nif:beginIndex,' + beginOffset)
    endOffset = int(beginOffset) + int(tok.get_length())
    IDtriples.append(prefix + wid + ',nif:endIndex,' + str(endOffset))
    IDtriples.append(prefix + wid + ',nif:anchorOf,' + tok.get_text())
    return IDtriples

def get_otherEnt_triples(nafobj, prefix, id2find, BiodesId):
    '''
    Create triples for loose identifiers from targeted relations
    '''
    global gender, instanceIds
    IDtriples = []
    if id2find.startswith('w'):
        IDtriples = surface_triples_from_wid(nafobj, id2find, prefix)
    elif id2find.startswith('t_'):
        term = nafobj.get_term(id2find)
        lemma = term.get_lemma()
        pron = get_pron_value(nafobj, lemma, id2find)
        if not pron:
            pron = get_poss_pron_value(lemma)
        if pron:
            wid = term.get_span().get_span_ids()[0]
            IDtriples = surface_triples_from_wid(nafobj, wid, prefix)
            IDtriples.append('bgnProc:' + prefix + '#' + wid + ',a,' + pron)
            IDtriples.append('bgnProc:' + prefix + '#' + id2find + ',gaf:denotedBy,' + 'bgnProc:' + prefix + '#' + wid)
            if ('fs' in pron and gender == '2') or ('ms' in pron and gender == '1'):
                IDtriples.append('bgn:Person-' + prefix.split('_')[0] + ',owl:sameAs,' + 'bgnProc:' + prefix + '#' + id2find + ',NG_pron2Gender')
                instanceIds.append(id2find)
        
    return IDtriples
    
def get_predobj_from_TE_datevalue(tValue):

    if tValue.startswith('P'):
        predval = 'xs:period,' + tValue
    else:
        if len(tValue) == 4:
            predval = 'xs:gYear,' + tValue
        elif len(tValue) == 7:
            predval = 'xs:gYearMonth,' + tValue
        else:
            predval = 'xs:date,' + tValue
            
    return predval
  
    
def get_TE_triples(nafobj, prefix, TE, BiodesId):
    '''
    Analysis TE object and returns list of relevant triples
    '''
    TEtriples = []
    tType = TE[0]
    tValue = TE[1]
    rdftype = 'xs:date'
    if 'DURATION' in tType:
        rdftype = 'xs:duration'
    predval = get_predobj_from_TE_datevalue(tValue)
    #for timex the spans are wids
    wSpan = TE[2]
    tSpan = get_termSpan_from_wordSpan(nafobj, wSpan)
    instanceId = create_identifier(prefix, tSpan)
    mentionId = create_identifier(prefix, wSpan)
    offset, surfaceString = get_offset_and_surface_from_tokens(nafobj, wSpan)
    
    surfaceString = surfaceString.replace(',','')
    TEtriples.append('bgnProc:' + prefix + '#personDes,bgn:hasAssociation,' + instanceId)
    TEtriples.append(instanceId + ',rdf:type,' + rdftype)
    TEtriples.append(instanceId + ',' + predval)
    TEtriples.append(instanceId + ',gaf:denotedBy,' + mentionId)
    TEtriples.append(mentionId + ',nif:beginIndex,"' + str(offset[0]) + '"')
    TEtriples.append(mentionId + ',nif:endIndex,"' + str(offset[1]) + '"')
    TEtriples.append(mentionId + ',nif:anchorOf,"' + surfaceString + '"')
    
    return TEtriples
    
    
def get_basic_triples_for_role(prefix, BiodesId, role):
    '''
    Introduced instance based on role that is not NE or TE
    '''
    global gender, instanceIds
    roleTriples = []
    
    instanceId = create_identifier(prefix, role.roleSpan)
    mentionId = create_identifier(prefix, role.wIds)
    role.roleString = role.roleString.replace(',','')
    #PREFIX
    roleTriples.append('bgnProc:' + prefix + '#personDes,bgn:hasAssociation,' + instanceId)
    roleTriples.append(instanceId + ',rdf:type,http://sw.opencyc.org/2009/04/07/concept/en/SomethingExisting')
    roleTriples.append(instanceId + ',gaf:denotedBy,' + mentionId)
    roleTriples.append(mentionId + ',nif:beginIndex,"' + str(role.offset[0]) + '"')
    roleTriples.append(mentionId + ',nif:endIndex,"' + str(role.offset[1]) + '"')
    roleTriples.append(mentionId + ',nif:anchorOf,' + role.roleString + '"')
    #if head, lemma is lemma of head, else it is lemma of entire mention
    if role.head:
        headId = create_identifier(prefix, [role.head])
        roleTriples.append(mentionId + ',nif:head,' + headId)
        roleTriples.append(headId + ',nif:lemma,"' + role.lemma + '"')
    else:
        roleTriples.append(mentionId + ',nif:lemma,"' + role.lemma + '"')
    if role.pron:
        roleTriples.append(mentionId + ',rdf:type,' + role.pron)
        if ('fs' in role.pron and gender == '2') or ('ms' in role.pron and gender =='1'):
            persId = 'bgn:Person-' + BiodesId.split('_')[1]
            roleTriples.append(persId + ',owl:sameAs,' + instanceId + ',NG_pron2Gender')
            instanceIds.append(instanceId)
    foundIds = set()
    foundIds.add(instanceId.split(':')[1]) 
    foundIds.add(mentionId.split(':')[1])
    
    return roleTriples, foundIds
    
    
def create_event_triples(prefix, event, BiodesId):
    '''
    Retrieves all relevant information of an event and returns named graphs
    '''
    global counter
    evTriples = []
    foundIds = set()
    instanceId = create_identifier(prefix, [event.predTid])
    mentionId = create_identifier(prefix, event.wIds)

    #PREFIX
    evTriples.append('bgnProc:' + prefix + '#personDes,bgn:hasAssociation,' + instanceId)
    evTriples.append(instanceId + ',rdf:type,sem:Event')
    evTriples.append(instanceId + ',gaf:denotedBy,' + mentionId)
    evTriples.append(mentionId + ',nif:BeginIndex,"' + str(event.offset[0]) + '"')
    evTriples.append(mentionId + ',nif:endIndex,' + str(event.offset[1]) + '"')
    evTriples.append(mentionId + ',nif:anchorOf,"' + event.predString + '"')
    evTriples.append(mentionId + ',nif:lemma,"' + event.lemma + '"')
    
    NGprefix = 'NG_' + prefix + '_interpreted_'
    
    
    for exRef in event.exRefs:
        #we use resource indication as prefix
        if exRef.resource + ':' in exRef.reference:
            value = exRef.reference
        else:
            value = exRef.resource + ':' + exRef.reference
        #each NG should have unique ID
        NGname = NGprefix + str(counter)
        counter += 1
        evTriples.append(instanceId + ',rdf:type,' + value + ',' + NGname)
        for mysubExRef in exRef.externalRefs:
            if '1.1' in mysubExRef.reference:
                for subExRef in mysubExRef.externalRefs:
                    if not subExRef.resource in subExRef.reference:
                        subvalue = subExRef.resource + ':' + subExRef.reference
                    else:
                        subvalue = subExRef.reference
                    if not '-role' in subvalue:
                        if subExRef.confidence:
                            counter += 1
                            NGname = NGprefix + str(counter)
                            if not subExRef.confidence == 'unknown':
                                evTriples.append(NGname + ',nif:confidence,' + subExRef.confidence)
            #FIXME: in current output, subvalues of exref have no confidence scores, so they take the one of the main external reference
            #They are now placed in the same named graph, but this may change in the future
                        evTriples.append(instanceId + ',rdf:type,' + subvalue + ',' + NGname)
        if exRef.confidence:
            #confidence scores will be in generic 'from NAF graph'
            if not exRef.confidence == 'unknown':
                evTriples.append(NGname + ',nif:confidence,' + exRef.confidence)
        
    for role in event.roles:
        if role.lemma and not role.lemma == ',':
            role_triples, newfoundIds = get_basic_triples_for_role(prefix, BiodesId, role)
            for nfd in newfoundIds:
                foundIds.add(nfd)
            evTriples += role_triples
        roleInstanceId = create_identifier(prefix, role.roleSpan)
        if not '#' in role.roleLabel:
            evTriples.append(instanceId + ',' + role.roleLabel + ',' + roleInstanceId)
        foundIds.add(roleInstanceId.split(':')[1])
        foundIds.add(instanceId.split(':')[1])
    #This may become relevant again with the latest version of the pipeline (fn:roles)
       # for exr in role.exRefs:
       #     exrRole = exr.resource + ':' + exr.reference
       #     NGname = NGprefix + str(counter)
       #     counter += 1
       #     evTriples.append(instanceId + ',' + exrRole + ',' + roleInstandceId + ',' + NGname)
       #     evTriples.append(NGname + ',nif:confidence_of_annotation,' + exr.confidence)
            
    return evTriples, foundIds
            

def generate_prefixes(outfile, location):
    '''
    Function that takes opened outfile and adds prefixes (csv, two fields (pref name + reference))
    '''
    
    outfile.write('rdf,<http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n')
    outfile.write('bgn,<http://purl.org/collections/nl/biographyned/>\n')
    outfile.write('bgnProc,<http://purl.org/collections/nl/biographyned/' + location + '/>\n')
    outfile.write('prov,<http://www.w3.org/ns/prov#>\n')
    outfile.write('pplan,<http://purl.org/net/p-plan#>\n')
    outfile.write('gaf,<http://groundedannotationframework.org/files/2014/01/>\n')
    outfile.write('owlTime,<http://www.w3.org/TR/owl-time/>\n')
    outfile.write('nif,<http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#>\n')
    outfile.write('geonames,<http://www.sws.geonames.org/>\n')
    outfile.write('bnProv,<https://github.com/antske/BiographyNet/provenance/>\n')
    
    
    
def initiate_store_graph(location):
    '''
    Function that takes opened outfile and adds prefixes (csv, two fields (pref name + reference))
    '''
    
    BGN = Namespace('http://data.biographynet.nl/rdf/')
    BGNProc = Namespace('http://purl.org/collections/nl/biographyned/' + location + '/')
    PROV = Namespace('http://www.w3.org/TR/prov-o/')
    PPLAN = Namespace('http://purl.org/net/p-plan#')
    GAF= Namespace('http://groundedannotationframework.org/files/2014/01/')
    OWLT = Namespace('http://www.w3.org/TR/owl-time/')
    NIF = Namespace('http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#')
    GEONAMES = Namespace('http://www.sws.geonames.org/')
    BNPROV = Namespace('https://github.com/antske/BiographyNet/provenance/')
    
    
    store = IOMemory()
    
    np_g = ConjunctiveGraph(store = store)
    np_g.bind('bgn',BGN)
    np_g.bind('bgnProc',BGNProc)
    np_g.bind('prov',PROV)
    np_g.bind('pplan',PPLAN)
    np_g.bind('gaf',GAF)
    np_g.bind('owltime',OWLT)
    np_g.bind('nif',NIF)
    np_g.bind('geonames',GEONAMES)
    np_g.bind('bnProv',BNPROV)
    
    return np_g, store
    
    

def create_basic_quadriples(prefix, processId):
    '''
    Function that links what ever information we extract to a biodes object and a person    
    '''
    myQuads = []
    file_id = prefix.split('.')[0]
    person_id = file_id.split('_')[0]
    basics = 'bgnProc:' + prefix + '#' +'basics'
    begin = 'bgnProc:' + prefix + '#'
    # #should be proxy id
    #basics = ''
    #BioDes defining triples
    myQuads.append(begin + 'BioDes,a,bgn:BioDes,' + basics)
    myQuads.append(begin + 'BioDes,a,ore:Aggregation,' + basics)
    myQuads.append(begin + 'BioDes,a,prov:Entity,' + basics)
    myQuads.append(begin + 'BioDes,a,pplan:Entity,' + basics)
    myQuads.append(begin + 'BioDes,bgn:aggregatedPerson,bgn:Person-' + person_id + ',' + basics)
    myQuads.append(begin + 'BioDes,bgn:aggregatedCHO,bgn:Person-' + person_id + ',' + basics)
    myQuads.append(begin + 'BioDes,bgn:hasPersonDes,' + begin + 'PersonDes,' + basics)
    myQuads.append(begin + 'BioDes,ore:aggregates,bgn:BioDes-' + file_id + ',' + basics)
    myQuads.append(begin + 'BioDes,prov:wasDerivedFrom,bgn:BioDes-' + file_id + ',' + basics)
    myQuads.append(begin + 'BioDes,prov:wasGeneratedBy,bnProv:' + processId + '#processTotal,' + basics)
    myQuads.append(begin + 'BioDes,prov:wasAttributedTo,bnProv:' + processId + '#version,' + basics)
    # #Enrichment process triples: discuss with Niels; can this be turned off?
    myQuads.append('bnProv:' + processId + '-' + file_id + '#processTotal,a,bgn:Enrichment,' + basics)
    myQuads.append('bnProv:' + processId + '-' + file_id + '#processTotal,a,prov:Activity,' + basics)
    myQuads.append('bnProv:' + processId + '-' + file_id + '#processTotal,a,pplan:Activity,' + basics)
    myQuads.append('bnProv:' + processId + '-' + file_id + '#processTotal,prov:used,bgn:BioDes-' + file_id + ',' + basics)
    myQuads.append('bnProv:' + processId + '-' + file_id + '#processTotal,prov:qualifiedAssociation,bnProv:' + processId + '-qualifiedAssociation,' + basics)

    #PersonDes triples
    myQuads.append(begin + 'personDes,a,bgn:PersonDes,' + basics)
    myQuads.append(begin + 'personDes,a,ore:Proxy,' + basics)
    myQuads.append(begin + 'personDes,ore:proxyIn,' + begin + 'BioDes,' + basics)
    myQuads.append(begin + 'personDes,ore:proxyFor,bgn:Person-' + person_id + ',' + basics)

    # #triples that define process from NAF to RDF (turned off: now defined in overall process description in generic process)
    # myQuads.append(begin + '/interpreted-naf,prov:wasDerivedFrom,bgnProc:naf/' + file_id + ',' + basics)
    # myQuads.append(begin + '/extracted-naf,prov:wasDerivedFrom,bgnProc:naf/' + file_id + ',' + basics)
    # myQuads.append('bgnProc:naf/' + file_id + ',prov:wasDerivedFrom,bgn:original' + file_id + '.xml,' + basics)
    # myQuads.append('bgnProc:naf/' + file_id + ',prov:wasGeneratedBy,bnProv:' + processId + '/processNLP,' + basics)
    # myQuads.append(begin + '/interpreted-naf,prov:wasGeneratedBy,bnProv:' + processId + '/processNAF2RDF,' + basics)
    # myQuads.append(begin + '/extracted-naf,prov:wasGeneratedBy,bnProv:' + processId + '/processNAF2RDF,' + basics)
    # #we need the proxy to assocuate thing with
    return myQuads

def get_identifications(pred_id, nafobj, NEs):
    '''
    Function that applies basic coreference identifications
    '''
    global ngDict
    
    persInfo = ngDict.get(pred_id)
    if persInfo == None:
        print('person unknown in metadata: something must be wrong with id or name gender file',file=sys.stderr)
    else:
        gender = persInfo[0]
    
    
    
def create_quadriples(nafobj, prefix, location):    
    '''
    Function that takes naffile as input and creates a list of quadriples based on that
    '''
    ###TODO: call target information from here: the entities from target must be added here as well
    global instanceIds
    targetTriples = occupation_family_relation_linking(nafobj)
    outfile = open('evaluation/' + prefix, 'w')
    for triple in targetTriples:
        outfile.write(','.join(triple) + '\n')
    #collect entities
    identififiers_to_get = set()
    for triple in targetTriples:
        if not 'PROXY' in triple[0]:
            identififiers_to_get.add(triple[0])
        if not 'PROXY' in triple[2]:
            identififiers_to_get.add(triple[2])
    
    
    file_id = prefix.split('.')[0]
    begin = 'bgnProc:' + prefix + '#'
    proxy = begin + 'personDes'
    newQuadriples = resolve_proxys_and_ids_creating_target_quad(targetTriples, proxy, prefix)
    
    myEvents, NEs, TEs = collect_naf_info(nafobj)
    #We also store the Named Graph Name: initiate this with the generic triples about the process
    myQuadriples = create_basic_quadriples(prefix, location)
    #
    myQuadriples += newQuadriples
    #FIXME: we need to make sure versioning is respected here as well (i.e. get some uniqueId element)
    NGdirectId = 'NG_direct_' + prefix
    #FIXME: we should check how we make the new Biodes Id
    BiodesId = 'Biodes_' + prefix
    #
    pref_id = prefix.split('_')[0]
    pref_rels = get_identifications(pref_id, nafobj, NEs)
    #
    foundIds = set()
    for NE in NEs:
        NEtriples, instId, mentId = get_NE_triples(nafobj, prefix, NE, BiodesId)
        for triple in NEtriples:
            if len(instId.split(':')[1].split('#')) > 1:
                myfid = instId.split(':')[1].split('#')[1]
                if myfid in identififiers_to_get:
                    foundIds.add(myfid)
            if len(mentId.split(':')[1].split('#')) > 1:
                myfid = mentId.split(':')[1].split('#')[1]
                if myfid in identififiers_to_get:
                    foundIds.add(myfid)

            if len(triple.split(',')) == 3:
                myQuadriples.append(triple + ',' + NGdirectId)
            elif len(triple.split(',')) == 4:
                myQuadriples.append(triple)
    

    for TE in TEs:
        TEtriples = get_TE_triples(nafobj, prefix, TE, BiodesId)
        for triple in TEtriples:
            myQuadriples.append(triple + ',' + NGdirectId)

    for val in myEvents.values():
        evTrips, fIds = create_event_triples(prefix, val, BiodesId)
        for fid in fIds:
            myfid = fid.split('#')[1]
            foundIds.add(myfid)
        for triple in evTrips:
            #already named graph added
            if ',NG_' in triple:
                myQuadriples.append(triple)
            else:
                myQuadriples.append(triple + ',' + NGdirectId)

    ids2find = identififiers_to_get - foundIds
    for id2find in ids2find:
        idTriples = get_otherEnt_triples(nafobj, prefix, id2find, BiodesId)

        for idTrip in idTriples:
            #check if not quadriple already (interpretation algorithm applied)
            if len(idTrip.split(',')) < 4:
                myQuadriples.append(idTrip + ',' + NGdirectId)
            else:
                myQuadriples.append(idTrip)

    for triple in targetTriples:
        if 'Fam' in triple[1]:
            if triple[0] in instanceIds and triple[2] in instanceIds:
                print('Identification error: someone is family of themselves',file=sys.stderr)
            elif triple[0] in instanceIds or triple[2] in instanceIds:
                if triple[0] in instanceIds:
                    outfile.write('personId,owl:sameAs,' + triple[0] + '\n')
                else:
                    outfile.write('personId,owl:sameAs,' + triple[2] + '\n')
                    
                
                  
    
    outfile.close()
    return myQuadriples
    
    
def restructure_quads_for_trig(myQuads):
    '''
    Function that takes list of quads as now structured (csv) and returns a dictionary of named graph names and their triples
    '''
    
    tripleDict = {}
    for quad in myQuads:
        parts = quad.split(',')
        if len(parts) != 4:
            print(len(parts))
            print('Error, skipping entry:\n\n', quad, '\n\n not the right number of values')
        else:
            key = parts[3].rstrip()
            val = [parts[0], parts[1], parts[2]]
            if key in tripleDict:
                tripleDict[key].append(val) 
            else:
                tripleDict[key] = [val]
               
    return tripleDict
            
    
def create_uri_from_string(ns_dict, mystring, triple):
    '''
    Function that takes string as input and creates an URI 
    '''   
    if ':' in mystring and not ('http:' in mystring or 'hisco' in mystring):
        if 'rdf:' in mystring:
            uri = RDF[mystring.lstrip('rdf:')] 
        else:
            parts = mystring.split(':')
            s_nsname = parts[0]
            if len(parts) == 2:
                s_idname = parts[1]
            elif len(parts) > 2:
                s_idname = ''
                for x in range(1, len(parts)):
                    s_idname += parts[x] + ':'
                s_idname = s_idname.rstrip(':')
            else:
                #this should not occur
                s_idname = mystring.lstrip(s_nsname + ':')    
            s_ns = ns_dict.get(s_nsname)
            if s_ns:
                uri = s_ns[s_idname]
            else:
                uri = None
    elif mystring == 'a':
        uri = RDF.type
    else:
        uri = URIRef(mystring)
    
    return uri

    
def get_triple_components(triple, ns_dict): 
    '''
    Function that checks whether a string should be abbreviated and connected to a namespace or whether it should be a URI as a whole
    '''   
    #check in which cases the obj is a literal, then call other function
    subj = create_uri_from_string(ns_dict, triple[0], triple)
    pred = create_uri_from_string(ns_dict, triple[1], triple)

    if 'nif:' in triple[1] or 'xs:' in triple[1] or 'hasNumber' in triple[1]:
        myString = triple[2].replace('"','')
        obj = Literal(myString)
    else:
        obj = create_uri_from_string(ns_dict, triple[2], triple)

    return subj, pred, obj
    
def resolve_proxys_and_ids(triples, proxy, prefix):
    '''
    goes through collection of triples and replaces 'PROXY' dummy for proxyId
    '''
    new_triples = []
    for trip in triples:
        new_trip = []
        for unit in trip:
            if unit == 'PROXY':
                new_trip.append(proxy)
            elif unit.startswith('t_') or (unit.startswith('w') and unit[-1].isdigit()):
                new_trip.append('bgnProc:' + prefix + '#' + unit)
            else:
                new_trip.append(unit)
        new_triples.append(new_trip)
    return new_triples

def resolve_proxys_and_ids_creating_target_quad(triples, proxy, prefix):
    '''
    goes through collection of triples and replaces 'PROXY' dummy for proxyId
    '''
    new_quadriples = []
    for trip in triples:
        new_quad = ''
        #'bgn:Person-' + BiodesId.split('_')[1]
        for unit in trip:
            if unit == 'PROXY':
                new_quad += proxy + ','
            elif unit.startswith('t_') or (unit.startswith('w') and unit[-1].isdigit()):
                new_quad += 'bgnProc:' + prefix + '#' + unit + ','
                #new_quad += prefix + '/' + unit + ','
            elif unit == 'personId':
                new_quad += 'bgn:Person-' + proxy.split('_')[0].lstrip('bgnProc:') + ','
            else:
                new_quad += unit + ','
        new_quad += 'bgnProc:' + prefix + '#' + 'targetedExtraction'
        new_quadriples.append(new_quad)
    return new_quadriples

def initiate_graph(prefix, location, np_g):

    BGN = Namespace('http://data.biographynet.nl/rdf/')
    #removing prefix from BGNproc: must be added every where in identifier...
    BGNProc = Namespace('http://data.biographynet.nl/rdf/' + location + '/')
    PROV = Namespace('http://www.w3.org/ns/prov#')
    PPLAN = Namespace('http://purl.org/net/p-plan#')
    GAF = Namespace('http://groundedannotationframework.org/files/2014/01/')
    OWLT = Namespace('http://www.w3.org/TR/owl-time/')
    NIF = Namespace('http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#')
    GEONAMES = Namespace('http://www.sws.geonames.org/')
    BNPROV = Namespace('https://github.com/antske/BiographyNet/provenance/')
    CORNETTO = Namespace('https:/newsreader-project.eu/ontologies/cornetto/')
    PB = Namespace('https:/newsreader-project.eu/ontologies/propbank/')
    FN = Namespace('https:/newsreader-project.eu/ontologies/framenet/')
    FNR = Namespace('https:/newsreader-project.eu/ontologies/framenet/roles')
    XSD = Namespace('http://www.w3.org/2001/XMLSchema#')
    SEM = Namespace('http://semanticweb.cs.vu.nl/2009/11/sem/')
    MCR = Namespace('http://unknownresource/mcr/')
    ESO = Namespace('https://github.com/newsreader/eso/')
    FNPB = Namespace('https:/newsreader-project.eu/ontologies/framenet_propbank/')
    WN = Namespace('https:/newsreader-project.eu/ontologies/wordnet/')
    ORE = Namespace('http://www.openarchives.org/ore/terms/')
    BNFAM = Namespace('http://purl.org/collections/nl/biographyned/ontologies/family#')
    FAM = Namespace('http://www.cs.man.ac.uk/~stevensr/ontology/family.rdf.owl#')
    DBO = Namespace('http://dbpedia.org/ontology/')
    OWL = Namespace('http://www.w3.org/2002/07/owl#')
    EDM = Namespace('http://www.europeana.eu/schemas/edm/')


    ns_dict = {}

    # bind namespaces to graph and store them with identifier in dict
    np_g.bind('bgn', BGN)
    ns_dict['bgn'] = BGN
    np_g.bind('dbo', DBO)
    ns_dict['dbo'] = DBO
    np_g.bind('bgnProc', BGNProc)
    ns_dict['bgnProc'] = BGNProc
    np_g.bind('prov', PROV)
    ns_dict['prov'] = PROV
    np_g.bind('p-plan', PPLAN)
    ns_dict['pplan'] = PPLAN
    np_g.bind('gaf', GAF)
    ns_dict['gaf'] = GAF
    np_g.bind('owltime', OWLT)
    ns_dict['owltime'] = OWLT
    np_g.bind('nif', NIF)
    ns_dict['nif'] = NIF
    np_g.bind('geonames', GEONAMES)
    ns_dict['geonames'] = GEONAMES
    np_g.bind('bnProv', BNPROV)
    ns_dict['bnProv'] = BNPROV
    np_g.bind('Cornetto', CORNETTO)
    ns_dict['Cornetto'] = CORNETTO
    np_g.bind('pb', PB)
    ns_dict['pb'] = PB
    np_g.bind('fn', FN)
    ns_dict['fn'] = FN
    np_g.bind('fn-role', FNR)
    ns_dict['fn-role'] = FNR
    np_g.bind('xs', XSD)
    ns_dict['xs'] = XSD
    np_g.bind('sem', SEM)
    ns_dict['sem'] = SEM
    np_g.bind('mcr', MCR)
    ns_dict['mcr'] = MCR
    np_g.bind('eso', ESO)
    ns_dict['eso'] = ESO
    np_g.bind('fn-pb-role', FNPB)
    ns_dict['fn-pb-role'] = FNPB
    np_g.bind('WordNet', WN)
    ns_dict['WordNet'] = WN
    np_g.bind('ore', ORE)
    ns_dict['ore'] = ORE
    np_g.bind('bnFam', BNFAM)
    ns_dict['bnFam'] = BNFAM
    np_g.bind('stevensFam', FAM)
    ns_dict['stevensFam'] = FAM
    np_g.bind('owl', OWL)
    ns_dict['owl'] = OWL
    np_g.bind('edm', EDM)
    ns_dict['edm'] = EDM

    return np_g, ns_dict

def initiate_regular_graph(prefix, location, store):

    my_graph = Graph(store=store)
    np_g, ns_dict = initiate_graph(prefix, location, my_graph)

    return np_g, ns_dict

def initiate_conjunctive_graph(prefix, location, store):


    my_graph = ConjunctiveGraph(store=store)
    np_g, ns_dict = initiate_graph(prefix, location, my_graph)

    return np_g, ns_dict



def select_highest_confidence_val(confidence_dict, tripleDict):
    '''
    Function that finds out which of the interpretations assigned to the same event or entity has the highest confidence value
    '''
    highest_ranked = {}
    for k, v in tripleDict.items():
        if k in confidence_dict:
            identifier = v[0][0]
            if not identifier in highest_ranked:
                highest_ranked[identifier] = [v, k, confidence_dict.get(k)]
            elif float(confidence_dict.get(k)) > float(highest_ranked[identifier][-1]):
                highest_ranked[identifier] = [v, k, confidence_dict.get(k)]


    return highest_ranked


def reduce_triples_for_online_demo(tripleDict, prefix):
    '''
    Function that goes through triples, merges identifiers equalized by owl:sameAs and selects highest confidence interpretation
    '''
    #collect all sameAs
    identity_dict = {}
    confidence_dict = {}
    for k, v in tripleDict.items():
        for val in v:
            if 'owl:sameAs' in val:
                identity_dict[val[2]] = val[0]
            elif 'nif:confidence' in val:
                confidence_dict[val[0]] = val[2]

    highest_ranked = select_highest_confidence_val(confidence_dict, tripleDict)

    new_triple_dict = {}
    for k, v in tripleDict.items():
        if 'interpreted' in k or 'direct' in k or 'pron2Gender' in k:
            key = 'bgnProc:' + prefix + '#' + 'interpreted'
        else:
            key = k
        new_v = []
        for val in v:
            include = True
            new_val = []
            if not 'owl:sameAs' in val:
                if 'rdf:type' in val:
                    include = False
                    #values that classified highest should be included
                    if not val[0] in highest_ranked and 'fn:' in val[2] and not '.v' in val[2] and not '.n' in val[2]:
                        include = True
                    elif val[0] in highest_ranked and k in highest_ranked.get(val[0]):
                        include = True
                        #generic classifications should be included as well
                    elif 'sem:Event' in val[2] or 'xs:d' in val[2] or 'bgn:' in val[2]:
                        include = True
                if include:
                    if val[0] in identity_dict:
                        new_val.append(identity_dict.get(val[0]))
                    else:
                        new_val.append(val[0])
                    new_val.append(val[1])
                    if val[2] in identity_dict:
                        new_val.append(identity_dict.get(val[2]))
                    else:
                        new_val.append(val[2])
                    new_v.append(new_val)
        if key in new_triple_dict:
            new_triple_dict[key] += new_v
        else:
            new_triple_dict[key] = new_v
    return new_triple_dict



def create_trig_file(naffile, prefix, location, outfile):
    '''
    Function that creates trig file based on NAF output
    '''
    nafobj = KafNafParser(naffile)
    #initiating dictionary
    persId = prefix.split('_')[0]
    initiate_ngDict(persId)
    
    myQuads = create_quadriples(nafobj, prefix, location)
    tripleDict = restructure_quads_for_trig(myQuads)
    #main graph storing namespaces, etc.

    store = IOMemory()
    np_g, ns_dict = initiate_conjunctive_graph(prefix, location, store)
    small_store = IOMemory()
    nps_g, nss_dict = initiate_regular_graph(prefix, location, small_store)
    
    for k, v in tripleDict.items():

        ng_name = URIRef(k)
        g = Graph(store=store, identifier=k)
        if 'interpreted' in k or 'direct' in k or 'pron2Gender' in k:
            k = 'bgnProc:' + prefix + '#interpreted'
        for triple in v:

            subj, pred, obj = get_triple_components(triple, ns_dict)
            if subj and pred and obj:
                g.add((subj,pred,obj))

    #add function that reduces triples
    new_triple_dict = reduce_triples_for_online_demo(tripleDict, prefix)
    #print(new_triple_dict)

    for k, v in new_triple_dict.items():

        #sg = Graph(store=small_store, identifier=k)
        for triple in v:
            subj, pred, obj = get_triple_components(triple, ns_dict)
            if subj and pred and obj:
                if not 'confidence' in pred:
                    nps_g.add((subj,pred,obj))
                    #sg.add((subj,pred,obj))


    with open(outfile,'wb') as f:
        nps_g.serialize(f, format='turtle', encoding='utf8')

    if '.ttl' in outfile:
        longfile = outfile.replace('.ttl','-full.ttl')
    else:
        longfile = outfile + 'full.ttl'

    with open(longfile,'wb') as f:
        np_g.serialize(f, format='trig', encoding='utf8')
    
    
def create_triple_csv(naffile, prefix, location, outfile):
    '''
    Function that takes naffile name as input and creates csv file with extracted triples as output
    '''
    myQuadriples = create_quadriples(naffile, prefix, location)
    
    myout = open(outfile, 'w')
    generate_prefixes(myout, location)
    for quadr in myQuadriples:
        quadr += '\n'
        myout.write(quadr.encode('utf8'))


def main(argv=None):

    if not argv:
        argv = sys.argv
    inputfile = sys.stdin
    if len(argv) < 3:
        print('Error: you must provide a prefix and a location as doc specific identifiers')
        
    elif len(argv) < 4:
        prefix = argv[1]
        outfile = prefix.split('.')[0] + '.ttl'
        location = argv[2]
        create_trig_file(inputfile, prefix, location, outfile)
    else:
        prefix = argv[1]
        location = argv[2]
        outfile = argv[3]
        create_trig_file(inputfile, prefix, location, outfile)
    
if __name__ == '__main__':
    main()