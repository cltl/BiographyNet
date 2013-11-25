#!usr/bin/python
# -*- coding: utf-8 -*-

from xml.etree.ElementTree import ElementTree


'''Function that returns the current version of extract_from_xml'''
def return_version():
  version = '0.2'
  
  return version


'''retrieves family relations'''
def retrieve_family_relations(elem):
  relatives = {}
  rels = {}
  father = 0
  mother = 0
  partner = 0
  for ch in elem.getchildren():
    if ch.tag == 'person':
      my_id = ch.get('id')
      name = 'unknown'
      for gch in ch.getchildren():
        if gch.tag == 'persName' and gch.text != None:
          name = gch.text
          name = clean_string(name)
      sex = ch.get('sex')
      relatives[my_id] = [sex,name]
    elif ch.tag == 'relation':
      act = ch.get('active')
      pat = ch.get('passive')
      mut = ch.get('mutual')
      rel = ch.get('name')
      if act:
        val = [rel,pat]
        rels[act] = val
      elif mut:
        participants = mut.split(' ')
        val = [rel, participants[0]]
        rels[participants[1]] = val
  for r in rels.iterkeys():
    if not r in relatives:
      print 'Error: unidentified relation in metadata'
      print f
    else:
      val = rels[r]
      if val[0] == 'parent':
        if relatives[r][0] == '1':
          father = relatives[r][1]
        elif relatives[r][0] == '2':
          mother = relatives[r][1]
      elif val[0] == 'marriage' or val[0] == 'partner':
        partner = relatives[r][1]
      else:  
        print 'Found relation: '
        print val[0]   
      if not val[1] == '#1':
        print 'relation was not with person in bio, but '
        print val[1]
  return [father, mother, partner]


def clean_string(stc):
  while True:
    stc = stc.replace('  ', ' ')
    if not '  ' in stc:
       break
  stc = stc.lstrip()
  stc = stc.rstrip()
  return stc  


'''retrieves name from xml name child TODO: some are split up in types'''
def retrieve_name(elem):
    pname = '0'
    for ch in elem.getchildren():
        if ch.tag == 'persName':
            if len(ch.getchildren()) > 0:
              
              # create name from parts, ignoring prefix
              
                vn = ''
                infix = ''
                an = ''
                for gch in ch.getchildren():
                    if gch.tag == 'name':
                        my_t = gch.get('type')
                        if my_t == 'geslachtsnaam':
                            an = gch.text.lower()
                        elif my_t == 'voornaam':
                            vn = gch.text.lower()
                        elif my_t == 'intrapositie': #
                            infix = gch.text.lower()
                if not vn and not ch.text == None:
                    vn = ch.text.lower()
                name = vn
                if infix:
                    name += ' ' + infix
                name += ' ' + an
            elif not ch.text == None:
                name = ch.text.lower()
                if ', ' in name:
                    n_parts = name.split(', ')
                    name = n_parts[1] + ' ' + n_parts[0]
                name = clean_string(name)
            if pname == '0':
                pname = name
            else:
                pname += '|' + name
    return pname

'''returns when and where for events'''
def retrieve_when_and_where(ch):
  date = 0
  place = 0
  if ch.get('when') != None:
    date = ch.get('when')
  else:
    if ch.get('notBefore') != None:
      date = ch.get('notBefore') + '~'
    if ch.get('notAfter') != None:
      if '~' in date:
        date += ch.get('notAfter')
      else:
        date = '~' + ch.get('notAfter')
  for gch in ch.getchildren():
    if gch.tag == 'place' and gch.text != None:
      place = gch.text
      place = clean_string(place)
  return [date, place]


'''returns list of birth date, birth place, baptise date, baptise place if known'''
def retrieve_date_time_information_two_elements(elem, x, y):
  x_info = ['0','0']
  y_info = ['0','0']
  for ch in elem.getchildren():
    if ch.tag == 'event':
      if ch.get('type') == x:
        x_info = retrieve_when_and_where(ch)
  
      elif ch.get('type') == y:
        y_info = retrieve_when_and_where(ch)
  return x_info + y_info

'''returns marked value for gender'''
def retrieve_gender(elem):
  gender = 0
  for ch in elem.getchildren():
    if ch.tag == 'sex' and ch.get('value') != None:
      gender = ch.get('value')
  return gender

'''retrieves information on states marked with identification numbers'''
def extract_info_with_idnr(elem, info_type):
  idno = 0
  for ch in elem.getchildren():
    if ch.tag == 'state':
      if ch.get('type') == info_type and ch.get('idno') != None:
        idno = ch.get('idno')        
  return idno

'''extracts value for given type from states'''
def extract_state_information(elem, info_type):
  all_info = []
  info = '0'
  for ch in elem.getchildren():
    if ch.tag == 'state' and ch.get('type') == info_type:
      if ch.text != None:
        my_fr = ''
        if ch.get('from') != None:
          my_fr = ch.get('from')
        to = ''
        if ch.get('to') != None:
          to = ch.get('to')
        if info == 0:
          info = ch.text
          info = clean_string(info)
        else:
          new_info = ch.text
          info += '|' + clean_string(new_info)
        if my_fr or to:
          info += '(' + my_fr + '-' + to + ')'
        all_info.append(info)
        info = '0' 
  return all_info

# function that adds information about a certain state to dictionary
def add_state_information(elem, cat, my_dict):
  #set counter to 1
  number = 1

  #go through children
  for ch in elem.getchildren():
    #check if type is requested category
    if ch.tag == 'state' and ch.get('type') == cat:
      #if info is defined:
      if ch.text != None:
        # create tag and add to dictionary
        tag = '<' + cat + '-' + str(number) + '>'
        my_dict[tag] = ch.text
        # check if begin date is known
        if ch.get('from') != None:
          # if known, add begin date to dictionary
          b_tag = tag.replace('>', '-begin>')
          my_dict[b_tag] = ch.get('from')
        #check if end date is known
        if ch.get('to') != None:
          #if known, add end date to dictionary 
          e_tag = tag.replace('>', '-end>')
          my_dict[e_tag] = ch.get('to')
        #increase counter so that next tag is unique
        number += 1
  #make sure dictionary is updated
  return my_dict

#function that updates a dictionary with time and location of an event
def add_time_place_information(elem, cat, my_dict):

  my_info = []
  # go through children of xml element
  for ch in elem.getchildren():
    # this information is for events
    if ch.tag == 'event':
      # check if this is the event we're looking for
      if ch.get('type') == cat:
        #if so, retrieve information
        my_info = retrieve_when_and_where(ch)
  # check if value find
  if my_info:
    #double-check if length is correct, else print warning
    if len(my_info) == 2:
      #check if meaningful value (value is 0 is none was found)
      if my_info[0]:
        tag = '<' + cat + '-time>'
        my_dict[tag] = my_info[0]
      if my_info[1]:
        tag = '<' + cat + '-place>'
        my_dict[tag] = my_info[1]
    else:
      print 'Warning: retrieval of date and time for ', cat, 'lead to incorrect return value'

  #make sure value is indeed updated (through side effect)
  return my_dict

'''function that updates dictionary with value if this is marked through an id number'''
def add_no_marked_information(elem, cat, my_dict):
  #retrieve information from the element
  cat_val = extract_info_with_idnr(elem, cat)
  #check if information was found
  if cat_val:
    tag = '<' + cat + '>'
    my_dict[tag] = cat_val

  #return dictionary so that it will be updated
  return my_dict
 

def update_info_with_when_and_wheres(elem, cat_list, my_dict):

  # go through list of information and call function to update dictionary
  # with info from this category
  for cat in cat_list:
    add_time_place_information(elem, cat, my_dict)

  #making sure dictionary gets updated
  return my_dict

def update_info_identified_in_nr(elem, cat_list, my_dict):

  #go through items on cat list
  for cat in cat_list:
    #for each item, call function that adds information on it to dictionary
    add_no_marked_information(elem, cat, my_dict)

  #make sure the dictionary gets updated as side effect
  return my_dict


def update_state_information(elem, cat_list, my_dict):

  # go through list of requested categories
  for cat in cat_list:
    #update dictionary with information for each category if found
    add_state_information(elem, cat, my_dict)

  #make sure overall dictionary is updated
  return my_dict


'''extracts all dates related to a person in the metadata'''
def extract_all_dates_for_person(elem):
  
  birth_baptism = retrieve_date_time_information_two_elements(elem, 'birth', 'baptism')
  death_funeral = retrieve_date_time_information_two_elements(elem, 'death', 'funeral')

'''calls function retrieving family relations and adds it to dictionary'''
def add_family_relations(elem, my_dict):

  # call function that retrieves family relations
  rels = retrieve_family_relations(elem)
  if len(rels) == 3:
    # first element on list is father
    if rels[0]:
      my_dict['father'] = rels[0]
    # second element on list mother
    if rels[1]:
      my_dict['mother'] = rels[1]
    # third element on list is partner
    if rels[2]:
      my_dict['partner'] = rels[2]
  else:
    print 'Warning: Something went wrong retrieving relations, wrong number of elements on list'

  #make sure updated information is there
  return my_dict


'''extracts standard package of information from person. Input=xml element identified as person. Change made on 2013-11-12: make it return a dictionary.'''
def extract_person_information(elem):
  my_person_info = {}
  #add name to dictionary
  my_person_info['<name>'] = retrieve_name(elem)
  #update dictionary with information about birth, baptism, death and funeral
  #create list with all category names
  my_events = ['birth', 'baptism', 'death', 'funeral']
  #call function that updates my_person_info with all this information
  update_info_with_when_and_wheres(elem, my_events, my_person_info)
  
  #check if gender information is present, add to dictionary
  gender = retrieve_gender(elem)
  if gender:
    my_person_info['<gender>'] = gender
  
  #add information included in metadata via idnumbers
  #create list of categories
  info_in_nr = ['category','religion']
  #call function that updates my_person_info with information on these categories
  update_info_identified_in_nr(elem, info_in_nr, my_person_info)

  #create list of relevant state information
  my_states = ['education','faith','occupation']
  #add information on all these categories to my_person_info
  update_state_information(elem, my_states, my_person_info)

  #call function that adds family relations
  add_family_relations(elem, my_person_info)

  #return person info
  return my_person_info


'''creates dictionary of sources with their id number. To Do: assumes required lists are present in directory for now (more general solution required)'''
def retrieve_biography_ids():
  bio_names = {}
  data_base1 = open('biography_selection.txt', 'r')
  data_base2 = open('author_list.txt', 'r')
  for line in data_base1:
    parts = line.split('\t')
    if len(parts) != 2:
      print 'Error: identified wrongly defined resource-id pair'
      print line
    else:
      bio_names[parts[0]] = parts[1]
  for line in data_base2:
    parts = line.split('\t')
    if len(parts) != 2:
      print 'Error: identified wrongly defined resource-id pair'
      print line
    else:
      bio_names[parts[0]] = '4_' + parts[1]

  data_base1.close()
  data_base2.close()
  return bio_names


'''retrieves the source idno from the biography'''
def retrieve_source(elem):
  for ch in elem.getchildren():
    if ch.tag == 'idno' and ch.get('type') == 'source':
      return ch.text


'''returns name of publisher, if defined else returns unknown or None: used when we still had to derive the source from the publisher: there are idno now'''
def retrieve_source_old(elem):
  bron = 'unknown'
  for ch in elem.getchildren():
    if ch.tag == 'publisher':
      if len(ch.getchildren()) > 0:
        for gch in ch.getchildren():
          if gch.tag == 'name':
            bron = gch.text
      elif ch.text != None:
        bron = ch.text
  return bron


'''returns identifier number for sources'''
def retrieve_source_id(bron, source_map):
  id_nr = '5_x'
  for k in source_map.iterkeys():
    if k in bron.encode("utf-8"):
      id_nr = source_map[k]
  return id_nr


'''retrieves source from element, returns id_code if source_map is given, else string, old function that uses hacked interpretation of the source'''
def retrieve_source_info(elem, number_ids = True):
  bron = retrieve_source(elem)
  if number_ids:
    source_map = retrieve_biography_ids()
    bron_id = retrieve_source_id(bron, source_map)
    return bron_id
  else:
    return bron

'''returns text length (as string)'''
def extract_text_info(elem):  
  words = 0
  for ch in elem.getchildren():
    if ch.tag == 'text' or ch.tag == 'tekst':
      if not ch.text == None:
        my_text = ch.text
        words = len(my_text.split(' '))
  return str(words)
  

  
'''returns text'''
def extract_text(elem):  
  my_text = ''
  for ch in elem.getchildren():
    if ch.tag == 'text' or ch.tag == 'tekst':
      if not ch.text == None:
        my_text = ch.text.encode('utf-8')
  return str(my_text)
