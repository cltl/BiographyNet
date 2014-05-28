#!usr/bin/python
# -*- coding: utf-8 -*-

from xml.etree.ElementTree import ElementTree
import metadata
import os


eventStrings = ['gehuwd','ongehuwd']


'''Function that returns the current version of extract_from_xml'''
def return_version():
  version = '0.1'
  
  return version


def clean_string(stc):
    while True:
        stc = stc.replace('  ', ' ')
        if not '  ' in stc:
            break
    stc = stc.lstrip()
    stc = stc.rstrip()
    return stc


def name_string_nominalisation(namestring):
    an = 'Unknown'
    vn = ''
    if ', ' in namestring:
        n_parts = namestring.split(', ')
        an = n_parts[0]
        vn = n_parts[1]
    else:
        n_parts = namestring.split()
        if len(n_parts) > 1:
            an = n_parts.pop(-1)
            for n in n_parts:
                vn += n + ' '
                vn = vn.rstrip()
        else:
            an = n_parts[0]
    
    an = clean_string(an)
    return [an, vn]


def create_name_from_string(an, vn, infix):
    
    name = metadata.Name(an)
    if vn:
        vn = clean_string(vn)
        name.addFirstname(vn)
    if infix:
        infix = clean_string(infix)
        name.addInfix(infix)



'''retrieves name from xml name child TODO: some are split up in types'''
def retrieve_name(elem):
    for ch in elem.getchildren():
        if ch.tag == 'persName':
            vn = ''
            infix = ''
            #last name is the least we expect to find (set default for exceptions)
            an = 'Unknown'
            if len(ch.getchildren()) > 0:
                for gch in ch.getchildren():
                    if gch.tag == 'name':
                        my_t = gch.get('type')
                        if my_t == 'geslachtsnaam':
                            an = gch.text.lower()
                        elif my_t == 'voornaam':
                        #more than one first name can be given
                            vn += gch.text.rstrip().lower() + ' '
                        elif my_t == 'intrapositie': #
                            infix = gch.text.lower()
                #some sources provide first name as text after element identifying family name
                if not vn and not gch.tail == None:
                    vn = gch.tail.lstrip(', ').lower()
                # some sources provide first name as text before element identifying family name
                if not vn and not ch.text == None:
                    vn = ch.text.rstrip().lower()
                # remove additional space after name if present
                vn = vn.rstrip()


            elif not ch.text == None:
                namestring = ch.text.lower()
                an_vn = name_string_nominalisation(namestring)
                an = an_vn[0]
                vn = an_vn[1]
                    

            name = create_name_from_string(an, vn, infix)
            return name

def createIntervalDate(dateString):
    dateInterval = metadata.DateInterval()
    beginAndEndDates = dateString.split('-')
    if len(beginAndEndDates) == 2:
        dateInterval = metadata.DateInterval()
        bdate = beginAndEndDates[0]
        if 'tussen' in bdate:
            #remove tussen and everything that precedes it
            bdate = bdate.split('tussen')[1].lstrip()
                
        dateInterval.beginDate = bdate
        dateInterval.endDate = string_to_date(beginAndEndDates[1])
    else:
        print dateString
    return dateInterval



def string_to_date(dateString, description = ''):
    global eventStrings
    myDate = metadata.Date()
    if '-' in dateString:
        if 'tussen' in dateString:
            dateInterval = createIntervalDate(dateString)
            myDate.interval = dateInterval
            myDate.year = 'INTERVAL'
        else:
            dateParts = dateString.split('-')
            if len(dateParts) == 3 and (len(dateParts[0]) == 4 or len(dateString) == 3):
                myDate.year = dateParts[0]
                myDate.month = dateParts[1]
                myDate.day = dateParts[2]
            elif len(dateParts) == 2 and (len(dateParts[0]) == 4 or len(dateParts[0]) == 3):
                if len(dateParts[1]) > 2:
            
                    beginAndEndDates = dateString.split('-')
                    if len(beginAndEndDates) == 2:
                        dateInterval = createIntervalDate(dateString)
                        myDate.year = 'INTERVAL'
                        myDate.interval = dateInterval
                    else:
                        print dateString
                else:
                    myDate.year = dateParts[0]
                    myDate.month = dateParts[1]
            else:
                print dateParts
    elif len(dateString) == 4 or len(dateString) == 3:
        myDate.year = dateString
    elif not dateString == '?' and dateString.strip() and not dateString in eventStrings:
        print dateString

    #place holder
    return myDate


def create_date(elem):
    date = None
    if elem.get('when') != None:
        date_string = elem.get('when')
        date = string_to_date(date_string)
    else:
        if elem.get('notBefore') != None:
            date_string = elem.get('notBefore')
            date = string_to_date(date_string, 'not before')
        if elem.get('notAfter') != None:
            date_string = elem.get('notAfter')
            date = string_to_date(date_string, 'not after')
    if date == None:
        dateText = elem.text
        if dateText:
            description = ''
            if 'ca.' in dateText:
                description += 'ca.'
                dateText = dateText.lstrip('ca. ')
            if 'tussen' in dateText:
                description += 'tussen'
                dateText = dateText.lstrip('tussen ')
            date = string_to_date(dateText, description)
        else:
            date = metadata.Date()
    return date


def retrieve_location(elem):
    place = ''
    for ch in elem.getchildren():
        if ch.tag == 'place' and ch.text != None:
            place = ch.text
            place = clean_string(place)
    if not place:
        if elem.text:
            if 'te' in elem.text:
                place = elem.text.split( 'te' )[1].rstrip()
                place = clean_string(place)
    return place


def create_event(elem):
    label = elem.get('type')
    myEvent = metadata.Event(label)
    date = create_date(elem)
    myEvent.setDate(date)
    location = retrieve_location(elem)
    myEvent.setLocation(location)

    return myEvent

def create_state(elem):
    label = elem.get('type')
    myState = metadata.State(label)
    if elem.text != None:
        fromDateString = elem.get('from')
        if fromDateString:
            fromDate = create_date(fromDateString)
            myState.setBeginDate(fromDate)
        toDateString = elem.get('to')
        if toDateString:
            toDate = create_date(toDateString)
            myState.setEndDate(toDate)
        myState.setDescription(elem.text)
    return myState


def retrieve_event_and_state_information(elem, myMetadata):

# where does it find what?
    for ch in elem.getchildren():
        if ch.tag == 'event':
            myEvent = create_event(ch)
            if myEvent.label == 'birth':
                myMetadata.birth = myEvent
            elif myEvent.label == 'death':
                myMetadata.death = myEvent
            else:
                myMetadata.otherEvents.append(myEvent)
        elif ch.tag == 'state':
            myState = create_state(ch)
            if myState.label == 'education':
                myMetadata.addEducation(myState)
            elif myState.label == 'occupation':
                myMetadata.addOccupation(myState)
            elif myState.label == 'religion':
                myMetadata.addReligion(myState)
            elif myState.label == 'residence':
                myMetadata.addResidence(myState)
            else:
                myMetadata.otherStates.append(myState)
    return myMetadata


def determine_relation(elem, id_toInfo):
    
    id_nr = elem.get('active')
    if not id_nr:
        id_nr = elem.get('mutual')
    rel = ch.get('name')
    if not id_nr in id_toInfo:
        print 'Problem in xml: We have a relation with an undefined person'
    else:
        otherInfo = id_toInfo.get(id_nr)
        sex = otherInfo[0]
        name = otherInfo[1]
        if rel == 'parent':
            if sex == '2':
                rel = 'mother'
            elif sex == '1':
                rel = 'father'
        return [rel, name]
        


def retrieve_family_relations(elem, myMetadata):
    id_toInfo = {}
    for ch in elem.getchildren():
        if ch.tag == 'person':
            name = metadata.Name('Unknown')
            for gch in ch.getchildren():
                if gch.tag == 'persName' and gch.text != None:
                    namestring = gch.text
                    an_vn = name_string_nominalisation(namestring)
                    name = create_name_from_string(an_vn[0], an_vn[1], '')
            sex = ch.get('sex')
            rel_id = ch.get('id')
            id_toInfo[rel_id] = [sex, name]
        elif ch.tag == 'relation':
            relation_and_name = determine_relation(ch, id_toInfo)
            rel = relation_and_name[0]
            name = relation_and_name[1]
        #   only 10 biographies in the entire corpus indicate partners: ignoring them for now
            if rel == 'father':
                myMetadata.defineFather(name)
            elif rel == 'mother':
                myMetadata.defineMother(name)
    return myMetadata

def retrieve_idNr(elem):
    for ch in elem.getchildren():
        if ch.tag == 'idno' and ch.get('type') == 'bioport':
            return ch.text


def create_metadataObject(my_biography):
    
    for ch in my_biography.getchildren():
        #all content information is included in person element (the rest is provenance related metadata)
        #Biographies (should) contain only one person element
        if ch.tag == 'person':
            #retrieve id number
            idNr = retrieve_idNr(ch)
            try:
                myMetadata = metadata.MetadataSingle(idNr)
                #set metadata name
                myMetadata.name = retrieve_name(ch)
                #add information about events and states
                myMetadata = retrieve_event_and_state_information(ch, myMetada)
                #add information about relations
                myMetadata = retrieve_family_relations(ch, myMetadata)
                return myMetadata

                    
            except ImportError as e:
                print "Import error({0}): {1}".format(e.errno, e.strerror)
# except:


##### quick test lines
#xmldir = '/Users/antske/BNGithub/BiographyNet/DevelopmentCorpus/jhs/'

                    #for myfile in os.listdir(xmldir):
                    # if '.xml' in myfile:
        #print myfile
                    #      xmlfile = xmldir + myfile
        #      my_biography = ElementTree().parse(xmlfile)
                    #      myMetadata = metadata.MetadataSingle()
        
#       for ch in my_biography.getchildren():
                    #           if ch.tag == 'person':
                #                myMetadata.name = retrieve_name(ch)
#                myMetadata = retrieve_event_and_state_information(ch, myMetada)
