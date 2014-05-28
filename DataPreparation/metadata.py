#!/usr/bin/python

'''Defines classes for representing metadata found in Biographies'''



class Date:
    '''Object to represent dates. Dates can consist of regular day-month-year, but also descriptions (before, after, ca.). Object has attributes for regular parts and one for description, default is empty string.'''

    def __init__( self,  year='YY', month='YY', day='YY', description='', dateInterval = ''):
        self.year = year
        self.month = month
        self.day = day
        self.description = description
        self.interval = dateInterval


    def returnDate(self):
        myDate = self.year + '-' + self.month + '' + self.day
        if self.description:
            myDate += ' (' + self.description + ')'
        return myDate



class DateInterval:
    '''Object to represent date intervales. consists of a begin date and an end date, each of which can be underspecified'''
    def __init__(self, beginDate = '', endDate = ''):
        self.beginDate = beginDate
        self.endDate  = endDate


class Name:
    '''Object to describe person names. It has fields for initials, first name, last name, infixes and titles.'''
    
    def __init__(self, lastname, firstname = '', initials = '', infix = ''):
        self.lastname = lastname
        self.firstname = firstname
        self.initials = initials
        self.infix = infix
        self.title = ''

    def addTitle(self, title):
        self.title = title

    def defineName(self, name):
        self.lastname = name

    def addFirstname(self, firstname):
        self.firstname = firstname

    def addInitials(self, initials):
        self.initials = initials
    
    def addInfix(self, infix):
        self.infix = infix

    def returnName(self):
        '''prefer full first name if known, else initials. If neither are known, this will be the empty string.'''
        if self.firstname:
            name = self.title + ' ' + self.firstname + ' ' + self.infix + self.lastname
        else:
            name = self.title + ' ' + self.initials + ' ' + self.infix + self.lastname
        return name



class Event:
    '''Object that can describe an event (time, place, description)'''
    
    def __init__(self, label, location = '', date = Date):
        self.label = label
        self.location = location
        self.date = date

    def setDate(self, date):
        self.date = date

    def setLocation(self, location):
        self.location = location



class State:
    '''Object that can describe a state (begin time, end time, place, description)'''
    
    def __init__(self, label, description = '', location = '', beginDate = Date, endDate = Date):
        self.label = label
        self.location = location
        self.beginDate = beginDate
        self.endDate = endDate
        self.description = description
    
    def setBeginDate(self, date):
        self.beginDate = date
    
    def setEndDate(self, date):
        self.endDate = date
    
    def setLocation(self, location):
        self.location = location

    def setDescription(self, description):
        self.description = description

class MetadataSingle:
    '''Object that represents the metadata from a single biography'''

    def __init__(self, idNr, name):
        self.id = idNr
        self.name = name
        self.birth = Event('birth')
        self.death = Event('death')
        self.father = Name('')
        self.mother = Name('')
        self.education = []
        self.occupation = []
        self.gender = ''
        self.religion = []
        self.residence = []
        self.otherEvents = []
        self.otherStates = []
        self.text = ''

    def defineBirthDay(self, date, location=''):
        self.birth.date = date
        if location:
            self.birth.location = location

    def defineDeathDay(self, date, location=''):
        self.death.date = date
        if location:
            self.death.location = location

    def defineFather(self, name):
        self.father = name

    def defineMother(self, name):
        self.mother = name

    def addEducation(self, educEvent):
        self.education.append(educEvent)

    def addOccupation(self, occEvent):
        self.occupation.append(occEvent)

    def defineGender(self, gender):
        self.gender = gender

    def addReligion(self, religion):
        self.religion.append(religion)
    
    def addResidence(self, religion):
        self.residence.append(religion)
    
    def defineText(self, text):
        self.text = text


class MetadataComplete:
    '''Object that represents all available metadata for an individual. All except id number are represented as lists'''
    
    def __init__(self, idNr):
        self.id = idNr
        self.name = []
        self.birth = []
        self.death = []
        self.father = []
        self.mother = []
        self.education = []
        self.occupation = []
        self.gender = []
        self.religion = []
        self.otherEvents = []
        self.otherStates = []
        self.text = []

    def addName(self, name):
        self.name.append(name)
    
    def addBirthDay(self, birthEvent):
        self.birth.append(birthEvent)
    
    def addDeathDay(self, deathEvent):
        self.death.append(deathEvent)
    
    def addFather(self, fatherName):
        self.father.append(name)
    
    def defineMother(self, motherName):
        self.mother.append(motherName)
    
    def addEducation(self, eduList):
        self.education.append(eduList)
    
    def addOccupation(self, occList):
        self.occupation.append(occList)
    
    def defineGender(self, gender):
        self.gender.append(gender)
    
    def addReligion(self, religionList):
        self.religion.append(religionList)
    
    def.addOtherEvents(self, otherElist):
        self.otherEvents.append(otherElist)
    
    def.addOtherStates(self, otherSlist):
        self.otherStates.append(otherSlist)

    def defineText(self, text):
        self.text.append(text)