'''
Created on Feb 25, 2015

@author: antske
'''

from KafNafParserPy import *
from rdflib import Graph, Namespace, URIRef, RDF, ConjunctiveGraph
from rdflib.plugins.memory import IOMemory
from NafInfo import *
import sys

# extract all predicates that have semantic roles


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
    entities = nafobj.get_entities()
    entityList = []
    for entity in entities:
        eType = entity.get_type()
        eReferences = entity.get_references()
        for ref in eReferences:
            eSpan = ref.get_span().get_span_ids()
            eSpan.append(eType)
            entityList.append(eSpan)
    
    return entities

def collect_time_expressions(nafobj):
    '''
    Function that retrieves time expressions from naf file
    '''
    timeExpressions = nafobj.get_timeExpressions()
    timeList = []
    for te in timeExpressions:
        tType = te.get_type()
        tValue = te.get_value()
        tSpan = te.get_span().get_span_ids()
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


def get_term_external_references(term):
    '''
    Function that retrieves external references and confidence scores of a term
    '''
    myRefs = []
    exRefs = term.get_external_references()
    for exRef in exRefs:
        myExRef = interpret_external_reference(exRef)
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
        #remove classtype from list
        myclass = ne.pop()
        #check if identical
        if list_overlap(ne, roleSpan):
            myRole = NafRole(entityType = myclass)
            if is_constituent(ne, nafobj) or len(ne) < len(roleSpan):
                myRole.roleSpan = ne
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
                


def get_head_word_and_lemma(nafobj, roleSpan):
    '''
    Function that retrieves the head word of a span and returns it's lemma
    '''
    headWord = []
    if len(roleSpan) == 1:
        term = nafobj.get_term(roleSpan[0])
    else:
        termId = identify_chunk_head(nafobj, roleSpan)  
        term = nafobj.get_term(termId)
      
    headWord.append(roleSpan[0])
    headWord.append(term.get_lemma())
    headWord.append(get_term_external_references(term))
    headWord.append(term.get_id())
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
            myEvent = NafEvent(predTid=tId,exrefs=tExRefs,offset=tOffsets, predString=surfacestring, lemma=tLemma)
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
                        myRole = NafRole(roleSpan = roleSpan, lemma=headWordInfo[1], exrefs=headWordInfo[2], head=headWordInfo[3])
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
    
    return NEtriples
    
def get_predobj_from_TE_datevalue(tValue):

    if tValue.startswith('P'):
        predval = 'xsd:period,' + tValue
    else:
        if len(tValue) == 4:
            predval = 'xsd:gYear,' + tValue
        elif len(tValue) == 7:
            predval = 'xsd:gYearMonth,' + tValue
        else:
            predval = 'xsd:date,' + tValue
            
    return predval
  
    
def get_TE_triples(nafobj, naffile, TE, BiodesId):
    '''
    Analysis TE object and returns list of relevant triples
    '''
    TEtriples = []
    tType = TE[0]
    tValue = TE[1]
    rdftype = 'xsd:date'
    if 'DURATION' in tType:
        rdftype = 'xsd:duration'
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
        roleTriples.append(mentionId + ',nif:lemma"' + role.lemma + '"')
        
    return roleTriples
    
    
def create_event_triples(naffile, event, BiodesId):
    '''
    Retrieves all relevant information of an event and returns named graphs
    '''
    evTriples = []
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
    counter = 1
    
    for exRef in event.exRefs:
        #we use resource indication as prefix
        value = exRef.resource + ':' + exRef.reference
        #each NG should have unique ID
        NGname = NGprefix + str(counter)
        counter += 1
        evTriples.append(instanceId + ',rdf:type,' + value + ',' + NGname)
        for subExRef in exRef.externalRefs:
            subvalue = subExRef.resource + ':' + subExRef.reference
            #FIXME: in current output, subvalues of exref have no confidence scores, so they take the one of the main external reference
            #They are now placed in the same named graph, but this may change in the future
            evTriples.append(instanceId + ',rdf:type,' + subvalue + ',' + NGname)
        if exRef.confidence:
            #confidence scores will be in generic 'from NAF graph' (comes directly from NAF, no special remarks)
            evTriples.append(NGname + ',nif:confidence_of_annotation,' + exRef.confidence)
        
    for role in event.roles:
        if role.lemma and not role.lemma == ',':
            role_triples = get_basic_triples_for_role(naffile, BiodesId, role)
            evTriples += role_triples
        roleInstandceId = create_identifier(naffile, role.roleSpan)
        evTriples.append(instanceId + ',' + role.roleLabel + ',' +  roleInstandceId)
        for exr in role.exRefs:
            exrRole = exr.resource + ':' + exr.reference
            NGname = NGprefix + str(counter)
            counter += 1
            evTriples.append(instanceId + ',' + exrRole + ',' + roleInstandceId + ',' + NGname)
            evTriples.append(NGname + ',nif:confidence_of_annotation,' + exr.confidence)
            
    return evTriples
            

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
    
    BGN = Namespace('http://purl.org/collections/nl/biographyned/')
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
    begin = 'bgnProc:' + file_id
    myQuads.append(begin + '/biodes,a,bgn:BioDes,' + basics)
    myQuads.append(begin + '/biodes,bgn:aggregatedPerson,bgn:person/' + person_id + ',' + basics)
    myQuads.append(begin + '/biodes,prov:wasDerivedFrom,bgn:original/' + file_id + '.xml,' + basics)
    myQuads.append(begin + '/biodes,prov:wasGeneratedBy,bnProv:' + processId + '/processTotal,' + basics)
    myQuads.append(begin + '/personDes,ore:proxyIn,' + begin + '/biodes,' + basics)
    myQuads.append(begin + '/personDes,ore:proxyFor,bgn:person/' + person_id + ',' + basics)
    myQuads.append(begin + '/interpreted-naf,prov:wasDerivedFrom,bgnProc:naf/' + file_id + ',' + basics)
    myQuads.append(begin + '/extracted-naf,prov:wasDerivedFrom,bgnProc:naf/' + file_id + ',' + basics)
    myQuads.append('bgnProc:naf/' + file_id + ',prov:wasDerivedFrom,bgn:orgiginal' + file_id + '.xml,' + basics)
    myQuads.append('bgnProc:naf/' + file_id + ',prov:wasGenereatedBy,bnProv:' + processId + '/processNLP,' + basics)
    myQuads.append(begin + '/interpreted-naf,prov:wasGenereatedBy,bnProv:' + processId + '/processNAF2RDF,' + basics)
    myQuads.append(begin + '/extracted-naf,provwasGenereatedBy,bnProv:' + processId + '/processNAF2RDF,' + basics)
    
    return myQuads

    
def create_quadriples(naffile, prefix, location):    
    '''
    Function that takes naffile as input and creates a list of quadriples based on that
    '''
    nafobj = KafNafParser(naffile)
    myEvents, NEs, TEs = collect_naf_info(nafobj)
    #We also store the NamedGraph Name: initiate this with the generic triples about the process
    myQuadriples = create_basic_quadriples(prefix, location)
    #FIXME: we need to make sure versioning is respected here as well (i.e. get some uniqueId element)
    NGdirectId = 'NG_direct_' + prefix
    #FIXME: we should check how we make the new Biodes Id
    BiodesId = 'Biodes_' + prefix
    
    for NE in NEs:
        NEtriples = get_NE_triples(nafobj, prefix, NE, BiodesId)
        for triple in NEtriples:
            myQuadriples.append(triple + ',' + NGdirectId)
    
    for TE in TEs:
        TEtriples = get_TE_triples(nafobj, prefix, TE, BiodesId)
        for triple in TEtriples:
            myQuadriples.append(triple + ',' + NGdirectId)
            
    for val in myEvents.values():
        evTrips = create_event_triples(prefix, val, BiodesId)
        for triple in evTrips:
            #already named graph added
            if ',NG_' in triple:
                myQuadriples.append(triple)
            else:
                myQuadriples.append(triple + ',' + NGdirectId)
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
    if ':' in mystring:
        if 'rdf:' in mystring:
            uri = RDF[mystring.lstrip('rdf:')] 
        else:
            s_nsname = mystring.split(':')[0]
            s_ns = ns_dict.get(s_nsname)
            if not s_ns:
                print triple, s_nsname
            uri = s_ns[mystring.lstrip(s_nsname + ':')]
    elif mystring == 'a':
        uri = RDF.type
    else:
        uri = URIRef(mystring)
    
    return uri

    
def get_triple_components(triple, ns_dict): 
    '''
    Function that checks whether a string should be abbreviated and connected to a namespace or whether it should be a URI as a whole
    '''   
    subj = create_uri_from_string(ns_dict, triple[0], triple)
    pred = create_uri_from_string(ns_dict, triple[1], triple)
    obj = create_uri_from_string(ns_dict, triple[2], triple)
    
    
    return subj, pred, obj
    
    
def create_trig_file(naffile, prefix, location, outfile):
    '''
    Function that creates trig file based on NAF output
    '''
    
    myQuads = create_quadriples(naffile, prefix, location)
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
    PB = Namespace('https://temporalurl/propbank')
    FN = Namespace('https://temporalurl/framenet')
    XSD = Namespace('http://www.w3.org/2001/XMLSchema#')
    SEM = Namespace('http://semanticweb.cs.vu.nl/2009/11/sem/')
    
    store = IOMemory()
    ns_dict = {}
    np_g = ConjunctiveGraph(store = store)
    
    #bind namespaces to graph and store them with identifier in dict
    np_g.bind('bgn',BGN)
    ns_dict['bgn'] = BGN
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
    np_g.bind('xsd',XSD)
    ns_dict['xsd'] = XSD
    np_g.bind('sem',SEM)
    ns_dict['sem'] = SEM
    
    
    for k, v in tripleDict.items():
        #named graph name only starts after /, therefore always start with /
        ng_name = URIRef('/' + k)
        g = Graph(store=store, identifier=ng_name)
        for triple in v:
            subj, pred, obj = get_triple_components(triple, ns_dict)
            g.add((subj,pred,obj))
            
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