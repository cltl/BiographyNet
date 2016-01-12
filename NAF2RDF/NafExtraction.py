'''
Created on Feb 25, 2015

@author: antske
'''

from KafNafParserPy import *
from rdflib import Graph, Namespace, URIRef, RDF, ConjunctiveGraph, Literal
from rdflib.plugins.memory import IOMemory
from NafInfo import *
from TargetInformationTagging import *
import sys

#making this counter global
counter = 1
# extract all predicates that have semantic roles



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
            roleSpan = pRole.get_span().get_span_ids()
            #FIXME: make object rather than list of length two
            roles.append([roleName,roleSpan])
        #in the current implementation, spans of predicates always have length 1
        myEvents[pSpan[0]] = roles  
    return myEvents


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
            eSpan.append(eType)
            if len(eSpan) == 0:
                print entity.get_id()
            else:
                entityList.append(eSpan)
    
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
        tokenOffset = token.get_offset()
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
                endTokenLength = token.get_length()

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
        myclass = ne[-1]
        nespan = []
        #create span of named entity (all in list except last element)
        for x in range(0, len(ne)-1):
            nespan.append(ne[x])
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
                updated_span = get_termSpan_from_wordSpan(nafobj, wSpan)
                myRole.rolespan = updated_span
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
                return 'pron_3fs'
            else:
                return 'pron_3p'
    #in written language 'ze' should not occur in other functions as subject
    #when feminine singular
    return 'pron_3p'
            

def get_pron_value(nafobj, lemma, tid):
    '''
    Function that looks up the label for a specific pronoun and returns this label
    '''
    lem2lab = {'hij':'pron_3ms',
               'hem':'pron_3ms',
               'haar':'pron_3fs',
               'ik':'pron_1s',
               'me':'pron_1s',
               'jij':'pron_2s',
               'je':'pron_2s',
               'jou':'pron_2s',
               'u':'pron_2',
               'we':'pron_1p',
               'ons':'pron_1p',
               'jullie':'pron_2p',
               'hun':'pron_3p',
               'hen':'pron_3p'}

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
    lem2lab = {'haar':'pron_3fs',
               'zijn':'pron_3ms',
               'mijn':'pron_1s',
               'jouw':'pron_2s',
               'uw':'pron_2',
               'ons':'pron_1p',
               'onze':'pron_1p',
               'jullie':'pron_2p',
               'hun':'pron_3p'}
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
    tid = term.get_id()
    headWord.append(tid)
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
        for t in ne:
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
                    if span_in_overlap_set(TEids, wSpan):
                        #update span (if needed), returns one role
                        myRole = initiate_role_from_overlap_TE(nafobj, wSpan, roleSpan, timeExpressions)
                        get_full_string_and_offsets(nafobj, myRole, myRole.roleSpan)
                        #FIXME: this should be done while checking overlap
                        myRole.wIds = wSpan
                        myRole.roleLabel = roleLab
                        myEvent.roles.append(myRole)
                    else:
                        headWordInfo = get_head_word_and_lemma(nafobj, roleSpan)
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
    if not prefix.endswith('/'):
        prefix += '/'
    for suffix in suffixList:
        prefix += suffix
    return prefix
    
    
def get_NE_triples(nafobj, naffile, NE, BiodesId):
    '''
    Analysis NE object and returns list of relevant triples
    '''
    
    NEtriples = []
    #last element in list is the class
    NEclass = NE.pop()
    wIds = get_span_from_list(nafobj, NE)
    offset, surfaceString = get_offset_and_surface_of_tSpan(nafobj, NE)
    instanceId = create_identifier(naffile, NE)
    mentionId = create_identifier(naffile, wIds)
    surfaceString = surfaceString.replace(',','')
    NEtriples.append(BiodesId + ',bgn:Includes,' + instanceId)
    NEtriples.append(instanceId + ',rdf:type,' + NEclass)
    NEtriples.append(instanceId + ',gaf:denotedBy,' + mentionId)
    NEtriples.append(mentionId + ',nif:beginIndex,"' + str(offset[0]) + '"')
    NEtriples.append(mentionId + ',nif:endIndex,"' + str(offset[1]) + '"')
    NEtriples.append(mentionId + ',nif:anchorOf,"' + surfaceString + '"')
    
    return NEtriples, instanceId, mentionId


def surface_triples_from_wid(nafobj, wid, prefix):
    '''
    Returns surface triples based on wid
    '''
    IDtriples = []
    tok = nafobj.get_token(wid)
    beginOffset = tok.get_offset()
    IDtriples.append(prefix + '/' + wid + ',nif:beginIndex,' + beginOffset)
    endOffset = int(beginOffset) + int(tok.get_length())
    IDtriples.append(prefix + '/' + wid + ',nif:endIndex,' + str(endOffset))
    IDtriples.append(prefix + '/' + wid + ',nif:anchorOf,' + tok.get_text())
    return IDtriples

def get_otherEnt_triples(nafobj, prefix, id2find, BiodesId):
    '''
    Create triples for loose identifiers from targeted relations
    '''
    
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
            IDtriples.append(prefix + '/' + wid + ',a,' + pron)
            IDtriples.append(prefix + '/' + wid + ',nif:head,' + prefix + '/' + id2find)
        
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
  
    
def get_TE_triples(nafobj, naffile, TE, BiodesId):
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
    instanceId = create_identifier(naffile + 'Timex', wSpan)
    mentionId = create_identifier(naffile, wSpan)
    offset, surfaceString = get_offset_and_surface_from_tokens(nafobj, wSpan)
    
    surfaceString = surfaceString.replace(',','')
    TEtriples.append(BiodesId + ',bgn:Includes,' + instanceId)
    TEtriples.append(instanceId + ',rdf:type,' + rdftype)
    TEtriples.append(instanceId + ',' + predval)
    TEtriples.append(instanceId + ',gaf:denotedBy,' + mentionId)
    TEtriples.append(mentionId + ',nif:beginIndex,"' + str(offset[0]) + '"')
    TEtriples.append(mentionId + ',nif:endIndex,"' + str(offset[1]) + '"')
    TEtriples.append(mentionId + ',nif:anchorOf,"' + surfaceString + '"')
    
    return TEtriples
    
    
def get_basic_triples_for_role(naffile, BiodesId, role):
    '''
    Introduced instance based on role that is not NE or TE
    '''
    roleTriples = []
    
    instanceId = create_identifier(naffile, role.roleSpan)
    mentionId = create_identifier(naffile, role.wIds)
    role.roleString = role.roleString.replace(',','')
    roleTriples.append(BiodesId + ',bgn:Includes,' + instanceId)
    roleTriples.append(instanceId + ',rdf:type,http://sw.opencyc.org/2009/04/07/concept/en/SomethingExisting')
    roleTriples.append(instanceId + ',gaf:denotedBy,' + mentionId)
    roleTriples.append(mentionId + ',nif:beginIndex,"' + str(role.offset[0]) + '"')
    roleTriples.append(mentionId + ',nif:endIndex,"' + str(role.offset[1]) + '"')
    roleTriples.append(mentionId + ',nif:anchorOf,' + role.roleString + '"')
    #if head, lemma is lemma of head, else it is lemma of entire mention
    if role.head:
        headId = create_identifier(naffile, [role.head])
        roleTriples.append(mentionId + ',nif:head,' + headId)
        roleTriples.append(headId + ',nif:lemma,"' + role.lemma + '"')
    else:
        roleTriples.append(mentionId + ',nif:lemma,"' + role.lemma + '"')
    if role.pron:
        roleTriples.append(mentionId + ',rdf:type,' + role.pron)
     
    foundIds = set()
    foundIds.add(instanceId.split('/')[1]) 
    foundIds.add(mentionId.split('/')[1])
    return roleTriples, foundIds
    
    
def create_event_triples(naffile, event, BiodesId):
    '''
    Retrieves all relevant information of an event and returns named graphs
    '''
    global counter
    evTriples = []
    foundIds = set()
    instanceId = create_identifier(naffile, [event.predTid])
    mentionId = create_identifier(naffile, event.wIds)
    
    
    evTriples.append(BiodesId + ',bgn:Includes,' + instanceId)
    evTriples.append(instanceId + ',rdf:type,sem:Event')
    evTriples.append(instanceId + ',gaf:denotedBy,' + mentionId)
    evTriples.append(mentionId + ',nif:BeginIndex,"' + str(event.offset[0]) + '"')
    evTriples.append(mentionId + ',nif:endIndex,' + str(event.offset[1]) + '"')
    evTriples.append(mentionId + ',nif:anchorOf,"' + event.predString + '"')
    evTriples.append(mentionId + ',nif:lemma,"' + event.lemma + '"')
    
    NGprefix = 'NG_' + naffile + '_interpreted_'
    
    
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
                    if subExRef.confidence:
                        counter += 1
                        NGname = NGprefix + str(counter)
                        evTriples.append(NGname + ',nif:confidence_of_annotation,' + subExRef.confidence)
            #FIXME: in current output, subvalues of exref have no confidence scores, so they take the one of the main external reference
            #They are now placed in the same named graph, but this may change in the future
                    evTriples.append(instanceId + ',rdf:type,' + subvalue + ',' + NGname)
        if exRef.confidence:
            #confidence scores will be in generic 'from NAF graph' (comes directly from NAF, no special remarks)
            evTriples.append(NGname + ',nif:confidence_of_annotation,' + exRef.confidence)
        
    for role in event.roles:
        if role.lemma and not role.lemma == ',':
            role_triples, newfoundIds = get_basic_triples_for_role(naffile, BiodesId, role)
            for nfd in newfoundIds:
                foundIds.add(nfd)
            evTriples += role_triples
        roleInstanceId = create_identifier(naffile, role.roleSpan)
        evTriples.append(instanceId + ',' + role.roleLabel + ',' +  roleInstanceId)
        foundIds.add(roleInstanceId.split('/')[1])
        foundIds.add(instanceId.split('/')[1])
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
    outfile.write('prov,<http://www.w3.org/TR/prov-o/>\n')
    outfile.write('p-plan,<http://purl.org/net/p-plan#>\n')
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
    np_g.bind('p-plan',PPLAN)
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
    basics = 'bgnProc:' + file_id + '/basics'
    begin = 'bgn:' + file_id
    #should be proxy id
    myQuads.append(begin + '-' + processId + ',a,bgn:BioDes,' + basics)
    myQuads.append(begin + '-' + processId + ',bgn:aggregatedPerson,bgn:Person-' + person_id + ',' + basics)
    myQuads.append(begin + '-' + processId + ',prov:wasDerivedFrom,bgn:original/' + file_id + '.xml,' + basics)
    myQuads.append(begin + '-' + processId + ',prov:wasGeneratedBy,bnProv:' + processId + '/processTotal,' + basics)
    myQuads.append(begin + '/personDes,ore:proxyIn,' + begin + '-' + processId + ',' + basics)
    myQuads.append(begin + '/personDes,ore:proxyFor,bgn:Person-' + person_id + ',' + basics)
    myQuads.append(begin + '/interpreted-naf,prov:wasDerivedFrom,bgnProc:naf/' + file_id + ',' + basics)
    myQuads.append(begin + '/extracted-naf,prov:wasDerivedFrom,bgnProc:naf/' + file_id + ',' + basics)
    myQuads.append('bgnProc:naf/' + file_id + ',prov:wasDerivedFrom,bgn:original' + file_id + '.xml,' + basics)
    myQuads.append('bgnProc:naf/' + file_id + ',prov:wasGeneratedBy,bnProv:' + processId + '/processNLP,' + basics)
    myQuads.append(begin + '/interpreted-naf,prov:wasGenereatedBy,bnProv:' + processId + '/processNAF2RDF,' + basics)
    myQuads.append(begin + '/extracted-naf,prov:wasGeneratedBy,bnProv:' + processId + '/processNAF2RDF,' + basics)
    #we need the proxy to assocuate thing with
    return myQuads

    
def create_quadriples(nafobj, prefix, location):    
    '''
    Function that takes naffile as input and creates a list of quadriples based on that
    '''
    
    ###TODO: call target information from here: the entities from target must be added here as well
    targetTriples = occupation_family_relation_linking(nafobj)
    outfile = open('evaluation/' + prefix, 'w')
    
    for triple in targetTriples:
        outfile.write(','.join(triple) + '\n')
    outfile.close()
    #collect entities
    identififiers_to_get = set()
    for triple in targetTriples:
        if not 'PROXY' in triple[0]:
            identififiers_to_get.add(triple[0])
        if not 'PROXY' in triple[2]:
            identififiers_to_get.add(triple[2])
    
    
    file_id = prefix.split('.')[0]
    begin = 'bgnProc:' + file_id
    proxy = begin + '/personDes'
    newQuadriples = resolve_proxys_and_ids_creating_target_quad(targetTriples, proxy, prefix)
    
    myEvents, NEs, TEs = collect_naf_info(nafobj)
    #We also store the Named Graph Name: initiate this with the generic triples about the process
    myQuadriples = create_basic_quadriples(prefix, location)
    
    myQuadriples += newQuadriples
    #FIXME: we need to make sure versioning is respected here as well (i.e. get some uniqueId element)
    NGdirectId = 'NG_direct_' + prefix
    #FIXME: we should check how we make the new Biodes Id
    BiodesId = 'Biodes_' + prefix
    
    foundIds = set()
    for NE in NEs:
        NEtriples, instId, mentId = get_NE_triples(nafobj, prefix, NE, BiodesId)
        for triple in NEtriples:
            if instId.split('/')[1] in identififiers_to_get:
                foundIds.add(instId.split('/')[1])
            if mentId.split('/')[1] in identififiers_to_get:
                foundIds.add(mentId.split('/')[1])
            myQuadriples.append(triple + ',' + NGdirectId)
    
    
    
    for TE in TEs:
        TEtriples = get_TE_triples(nafobj, prefix, TE, BiodesId)
        for triple in TEtriples:
            myQuadriples.append(triple + ',' + NGdirectId)
                  
    for val in myEvents.values():
        evTrips, fIds = create_event_triples(prefix, val, BiodesId)
        for fid in fIds:
            foundIds.add(fid)
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
            myQuadriples.append(idTrip + ',' + NGdirectId)
                   
    return myQuadriples
    
    
def restructure_quads_for_trig(myQuads):
    '''
    Function that takes list of quads as now structured (csv) and returns a dictionary of named graph names and their triples
    '''
    
    tripleDict = {}
    for quad in myQuads:
        parts = quad.split(',')
        if len(parts) != 4:
            print len(parts)
            print 'Error, skipping entry:\n\n', quad, '\n\n not the right number of values'
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
    if ':' in mystring and not 'http:' in mystring:
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
    
    if 'nif:' in triple[1] or 'xs:' in triple[1]:
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
                new_trip.append(prefix + '/' + unit)
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
        for unit in trip:
            if unit == 'PROXY':
                new_quad += proxy + ','
            elif unit.startswith('t_') or (unit.startswith('w') and unit[-1].isdigit()):
                new_quad += prefix + '/' + unit + ','
            else:
                new_quad += unit + ','
        new_quad += 'targetedExtraction'
        new_quadriples.append(new_quad)
    return new_quadriples   
    
def create_trig_file(naffile, prefix, location, outfile):
    '''
    Function that creates trig file based on NAF output
    '''
    nafobj = KafNafParser(naffile)
    myQuads = create_quadriples(nafobj, prefix, location)
    tripleDict = restructure_quads_for_trig(myQuads)
    #main graph storing namespaces, etc.
    BGN = Namespace('http://purl.org/collections/nl/biographyned/')
    BGNProc = Namespace('http://purl.org/collections/nl/biographyned/' + location + '/')
    PROV = Namespace('http://www.w3.org/TR/prov-o/')
    PPLAN = Namespace('http://purl.org/net/p-plan#')
    GAF= Namespace('http://groundedannotationframework.org/files/2014/01/')
    OWLT = Namespace('http://www.w3.org/TR/owl-time/')
    NIF = Namespace('http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#')
    GEONAMES = Namespace('http://www.sws.geonames.org/')
    BNPROV = Namespace('https://github.com/antske/BiographyNet/provenance/')
    CORNETTO = Namespace('https://temporalurl/cornetto/')
    PB = Namespace('https://temporalurl/propbank/')
    FN = Namespace('https://temporalurl/framenet/')
    FNR = Namespace('https://temporalurl/framenet/roles')
    XSD = Namespace('http://www.w3.org/2001/XMLSchema#')
    SEM = Namespace('http://semanticweb.cs.vu.nl/2009/11/sem/')
    MCR = Namespace('http://unknownresource/mcr/')
    ESO = Namespace('https://github.com/newsreader/eso/')
    FNPB = Namespace('https://temporalurl/framenet_propbank/')
    WN = Namespace('https://temporalurl/wordnet/')
    ORE = Namespace('http://www.openarchives.org/ore/1.0/')
    BNFAM = Namespace('http://purl.org/collections/nl/biographyned/ontologies/family#')
    FAM = Namespace('http://www.cs.man.ac.uk/~stevensr/ontology/family.rdf.owl#')
    DBO = Namespace('http://dbpedia.org/ontology/')
    
    store = IOMemory()
    ns_dict = {}
    np_g = ConjunctiveGraph(store = store)
    
    #bind namespaces to graph and store them with identifier in dict
    np_g.bind('bgn',BGN)
    ns_dict['bgn'] = BGN
    np_g.bind('dbo',DBO)
    ns_dict['dbo'] = DBO
    np_g.bind('bgnProc',BGNProc)
    ns_dict['bgnProc'] = BGNProc
    np_g.bind('prov',PROV)
    ns_dict['prov'] = PROV
    np_g.bind('p-plan',PPLAN)
    ns_dict['p-plan'] = PPLAN
    np_g.bind('gaf',GAF)
    ns_dict['gaf'] = GAF
    np_g.bind('owltime',OWLT)
    ns_dict['owltime'] = OWLT
    np_g.bind('nif',NIF)
    ns_dict['nif'] = NIF
    np_g.bind('geonames',GEONAMES)
    ns_dict['geonames'] = GEONAMES
    np_g.bind('bnProv',BNPROV)
    ns_dict['bnProv'] = BNPROV
    np_g.bind('Cornetto',CORNETTO)
    ns_dict['Cornetto'] = CORNETTO
    np_g.bind('pb',PB)
    ns_dict['pb'] = PB
    np_g.bind('fn',FN)
    ns_dict['fn'] = FN
    np_g.bind('fn-role',FNR)
    ns_dict['fn-role'] = FNR
    np_g.bind('xs',XSD)
    ns_dict['xs'] = XSD
    np_g.bind('sem',SEM)
    ns_dict['sem'] = SEM
    np_g.bind('mcr',MCR)
    ns_dict['mcr'] = MCR
    np_g.bind('eso',ESO)
    ns_dict['eso'] = ESO
    np_g.bind('fn-pb-role',FNPB)
    ns_dict['fn-pb-role'] = FNPB
    np_g.bind('WordNet',WN)
    ns_dict['WordNet'] = WN
    np_g.bind('ore',ORE)
    ns_dict['ore'] = ORE
    np_g.bind('bnFam',BNFAM)
    ns_dict['bnFam'] = BNFAM
    np_g.bind('stevensFam',FAM)
    ns_dict['stevensFam'] = FAM
    
    
    for k, v in tripleDict.items():
        #named graph name only starts after /, therefore always start with /
        ng_name = URIRef('/' + k)
        g = Graph(store=store, identifier=ng_name)
        for triple in v:
            subj, pred, obj = get_triple_components(triple, ns_dict)
            if subj and pred and obj:
                g.add((subj,pred,obj))
                    
    
   # targetTriples = occupation_family_relation_linking(nafobj)
   # newTriples = resolve_proxys_and_ids(targetTriples, proxy, prefix)
   # ng_name = URIRef('/targetedExtraction')
   # g = Graph(store=store, identifier=ng_name)
    
   # for triple in newTriples:
   #     subj, pred, obj = get_triple_components(triple, ns_dict)
   #     if subj and pred and obj:
   #         g.add((subj,pred,obj))               
                    
    with open(outfile,'w') as f:
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
        print 'Error: you must provide a prefix and a location as doc specific identifiers'
        
    elif len(argv) < 4:
        prefix = argv[1]
        outfile = prefix.split('.')[0] + '.trig'
        location = argv[2]
        create_trig_file(inputfile, prefix, location, outfile)
    else:
        prefix = argv[1]
        location = argv[2]
        outfile = argv[3]
        create_trig_file(inputfile, prefix, location, outfile)
    
if __name__ == '__main__':
    main()