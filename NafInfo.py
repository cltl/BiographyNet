'''
Created on Feb 25, 2015

@author: antske
'''

class NafEvent(object):
    '''
    classdocs
    '''

    def __init__(self, predTid = '', exrefs = [], lemma = '', predString = '', offset = [], roles = [], wIds = []):
        '''
        Constructor
        '''
        self.predTid = predTid
        self.exRefs = exrefs
        self.lemma = lemma
        self.predString = predString
        self.offset = offset
        self.roles = roles
        self.wIds = []
        
class NafRole():
    
    def __init__(self, roleLabel = '', roleSpan = [], exrefs = [], lemma = '', roleString = '', offset = [], entityType = '', timeValue = '', wIds = [], head = ''):
        '''
        Role construction
        '''
        self.roleLabel = roleLabel
        self.roleSpan = roleSpan
        self.exRefs = exrefs
        self.lemma = lemma
        self.roleString = roleString
        self.offset = []
        self.entityType = entityType    
        self.timeValue = timeValue
        self.wIds = []
        self.head = head

class ExternalReference():
    
    def __init__(self, reference, resource = '', confidence = '', exRefs = []):
        '''
        External references 
        '''
        self.reference = reference
        self.resource = resource 
        self.confidence = confidence
        self.externalRefs = exRefs
        
        
        
                