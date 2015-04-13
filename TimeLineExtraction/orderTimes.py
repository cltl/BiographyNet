#!/usr/bin/python

import sys
import os



# timelines ordering:



# Task 1: create time lines per document

# step 1: create objects for each time expression (t2, any time indication we may have)
# step 2: resolve time indications as much as possible (if t1 before t2 and t2 has anchor, then t1 before anchor)
# step 3: place timelines with explicit time anchor on a list (object with time anchor, term, etc.
# step 4: insert non-specified time expressions


# Task 2: merge time lines different documents

# step 1: merge co-referring events
# step 2: compare anchors, merge those
# step 3: merge other events



#####TODO, TODO: FOR ALL DATES: IMPLEMENT FUNCTION THAT MAKES SURE THEY HAVE THE SAME DATE...




# class for events

class Event:
	"""Basic class for events. Only contains information for ordering them based on time"""
	
	
	def __init__(self, docId, eId, entity = ''):
		"""Events may only be initiated if they have an identifier a docId"""
		self.docId = docId
		self.eventId = eId
		self.entity = [entity]
		self.time = Time()
		self.simultaneous = []
		#registers identifier of earliest possible event occurring after this event (if known)
		self.beforeEvent = []
		#registers identifier of latest possible event occurring before this event (if known)
		self.afterEvent = []
		
		self.beforeTime = Time()
		self.afterTime = Time()
		self.includedInEvent = []
		self.duration = Duration()
		
	def set_time(self, time):
		self.time = time
		
		
	def setReferentialTime(self, refTime):
	
		if 'FUTURE' in refTime:
			self.afterTime.dct = True
		elif 'PAST' in refTime:
			self.beforeTime.dct = True
		
	def set_relativeTime(self, tId, rel):
		if rel == 'BEFORE' or rel == 'ENDED_BY':
			self.beforeEvent.append(tId)
		elif rel == 'SIMULTANEOUS':
			self.simultaneous.append(tId)
		elif rel == 'IS_INCLUDED':
			self.includedInEvent.append(tId)
		else:
			print rel
		
	def updateTimeInformation(self, timestring, rel):
		myTime = Time()
		myTime.setTimeFromString(timestring)
		if rel == 'INCLUDES':
			self.time = myTime
		elif rel == 'BEFORE' or rel == 'ENDED_BY':
			self.beforeTime = myTime
		elif rel == 'AFTER':
			self.afterTime = myTime
		
	def setDuration(self, refTime, rel):
		self.duration.duration = refTime
		if not rel == 'INCLUDES':
			print rel
		
# class for time expressions

class Time:

	def __init__(self, year=0, month=0,day=0):
		self.year = year
		self.month = month
		self.day = day
		self.dct = False
	
	def setTimeFromString(self, timestring):
		timeParts = timestring.split('-')
		if 'XXXX' in timeParts[0]:
			self.year = 0
		else:
			self.year = int(timeParts[0])
		if len(timeParts) > 1:
			#FIX_ME: converting W indication to entire month for now
			if timeParts[1].startswith('W'):
				self.month = int(int(timeParts[1].lstrip('W'))/4.5) + 1
			elif timeParts[1].startswith('Q'):
				#put this on the first month of whatever quarter it is
				self.month = int(timeParts[1].lstrip('Q')) * 3 - 3
			elif 'XX':
				self.month = 0
			else:
				self.month = int(timeParts[1])
				if len(timeParts) > 2:
					if 'XX' in timeParts[2]:
						self.day = 0
					else:
						self.day = int(timeParts[2].rstrip('TMO').rstrip('TNI'))
				
	
# class to model durations	

class Duration:

	def __init__(self, duration=''):
	
		#duration in number of days
		self.duration = duration
		self.beginDate = Time()
		self.endDate = Time()
		
		
		
def defineEvent(parts, docId, line):			
	tId = parts[3].rstrip()
	rel = parts[2]
	refTime = parts[1]
	entity = parts[0]
	myEvent = Event(docId, tId, entity)
	if '-' in refTime or refTime.isdigit():
		myEvent.updateTimeInformation(refTime, rel)
		#keeping old format for now...(startswithT, will be removed later on)
	elif ('_' in refTime and not refTime.endswith('_REF')) or refTime.startswith('t'):
		myEvent.set_relativeTime(refTime, rel)
	#REF should be checked before duration (PAST_REF...)	
	elif refTime.endswith('_REF'):
		myEvent.setReferentialTime(refTime)
	elif refTime.startswith('P'):
		myEvent.setDuration(refTime, rel)
	else:
		print 'Cannot interpret from ', docId, '\n', line
	
	return myEvent
		
		
def interpretEvent(line, docId):
	docId = docId
	parts = line.split()
	if len(parts) < 4:
		print 'Illformed line in extraction, skipping', line
		myEvent = None
	else:
		myEvent = defineEvent(parts, docId, line)
	return myEvent			
				

	
def updateDuration(duration1, duration2):
	#FIX_ME: we should merge durations 	
	if duration2.duration and not duration1.duration:
		duration1.duration = duration2.duration
	duration1.beginDate = compareBeforeTime(duration1.beginDate, duration2.beginDate)
	duration2.endDate = compareAfterTime(duration1.endDate, duration2.endDate)
	
	return duration1	
		
	
def updateTime(time1, time2):
	#FIX_ME: we need to do something better if there are conflicting times: for now: first time stands
	if time1.year == 0 and not time2.year == 0:
		time1.year = time2.year
	if time1.month == 0 and not time2.month == 0:
		time1.month = time2.month
	if time1.day == 0 and not time2.day == 0:
		time1.day = time2.day
		
	return time1

def compareBeforeTime(time1, time2):

	if not time2.year == 0:
		if time2.year < time1.year:
			time1.year = time2.year
			time1.month = time2.month
			time1.day = time2.day
		elif not time2.month == 0 and not time2.year > time1.year:
			if time2.month < time1.month:
				time1.month = time2.month
				time1.day = time2.day
			elif not time2.day == 0 and time2.day < time1.day and not time2.month > time1.month:
				time1.day = time2.day
	return time1		
			
def compareAfterTime(time1, time2):

	if not time2.year == 0:
		if time2.year > time1.year:
			time1.year = time2.year
			time1.month = time2.month
			time1.day = time2.day
		elif time2.year == time1.year:
			if time2.month > time1.month:
				time1.month = time2.month
				time1.day = time2.day
			elif time2.month == time1.month and time2.day > time1.day:
				time1.day = time2.day
	return time1	
		
			
def updateEventInfo(myEvent, event):
	#appending new entities
	for entity in event.entity:
		if not entity in myEvent.entity:
			myEvent.entity.append(entity)
	#add new time information from next event, if present
	myEvent.time = updateTime(myEvent.time, event.time)
	#add new simultaneous events, before events, after events, included events
	for simE in event.simultaneous:
		if not simE in myEvent.simultaneous:
			myEvent.simultaneous.append(simE)
	for bE in event.beforeEvent:
		if not bE in myEvent.beforeEvent:
			myEvent.beforeEvent.append(bE)
	for aE in event.afterEvent:
		if not aE in myEvent.afterEvent:
			myEvent.afterEvent.append(aE)			
	for iiE in event.includedInEvent:
		if not iiE in myEvent.includedInEvent:
			myEvent.includedInEvent.append(iiE)
	#compare before time and after time			
	myEvent.beforeTime = compareBeforeTime(myEvent.time, event.time)			
	myEvent.afterTime = compareAfterTime(myEvent.time, event.time)	
	myEvent.duration = updateDuration(myEvent.duration, event.duration)
	
	
		
def mergeTimeInfo(eventList):
	
	#if only one event on list: no merging, else start with last event on list, then add the others
	myEvent = eventList.pop()
	if len(eventList) > 0:
		#first Event for initiation (this information is the same for all in the list)
		for event in eventList:
			updateEventInfo(myEvent, event)
	
	return myEvent	




def mergeInformation(eventDict):
	
	mergedDict = {}
	#takes all lists of events that are identical, merges information and stores this as identifier event pair in new dict
	for key, value in eventDict.items():
		if key == 'dct':
			mergedDict[key] = value
		else:
			myEvent = mergeTimeInfo(value)		
			mergedDict[key] = myEvent
	
	return mergedDict	
				
def create_docTimedEvents(myInput, inputfile):		
	
	myTimedEvents = {}
	for line in myInput:
		parts = line.split()
		#inputfile will be used as docId
		if '[DCT]' in line:
			pubTime = Time()
			pubTime.setTimeFromString(parts[1])
			myTimedEvents['dct'] = pubTime
		else:
			if not parts[1] == parts[3]:
				myEvent = interpretEvent(line, inputfile)
				eId = myEvent.eventId
				if not eId in myTimedEvents:
					myTimedEvents[eId] = [myEvent]
				else:
					myTimedEvents[eId].append(myEvent)
	
	
	return myTimedEvents
		


def get_allSimultaneous(simList, eventDict):

	completeList = simList
	added = False
	
	for event in simList:
		if event in eventDict:
			eInfo = eventDict.get(event)
			for eId in eInfo.simultaneous:
				if not eId in completeList:
					completeList.append(eId)
					added = True
				
	if added:
		completeList = get_allSimultaneous(completeList, eventDict)
		
	return completeList		

def getBeforeChain(bEvs, eventDict):

	beforeChain = bEvs
	
	for ev in bEvs:
		if ev in eventDict:
			sucEv = eventDict.get(ev)
			if sucEv.beforeEvent:
				additionalBevs = getBeforeChain(sucEv.beforeEvent, eventDict)
				beforeChain += additionalBevs	
	return beforeChain

def getAfterChain(aEvs, eventDict):

	afterChain = aEvs
	
	for ev in aEvs:
		if ev in eventDict:
			precEv = eventDict.get(ev)
			if precEv.afterEvent:
				additionalAfts = getAfterChain(precEv.afterEvent, eventDict)
				afterChain += additionalAfts
			
	return afterChain

def getIncludedChain(iEvs, eventDict):

	includedChain = iEvs
	
	for ev in iEvs:
		if ev in eventDict:
			incEv = eventDict.get(ev)
			if incEv.includedInEvent:
				additionalincs = getIncludedChain(incEv.includedInEvent, eventDict)
				includedChain += additionalincs
			
	return includedChain			
		
		
		
def flipEventRels(eventDict):

	updatedDict = eventDict
	
	for k, val in eventDict.items():
		if not k == 'dct':
			if val.beforeEvent:
				for e in val.beforeEvent:
					if e in updatedDict:
						if not k in updatedDict[e].afterEvent:
							updatedDict[e].afterEvent.append(k)
			if val.afterEvent:
				for e in val.afterEvent:
					if e in updatedDict:
						if not k in updatedDict[e].beforeEvent:
							updatedDict[e].beforeEvent.append(k)
	return updatedDict
	
def is_complete_time(time):
	if time.year > 0 and time.month > 0 and time.day > 0:
		return True
	else:
		return False


def has_time(time):
	if time.year > 0:
		return True
	else:
		return False


def findOutTime(event, eventDict):

	if event.simultaneous:
		for e in event.simultaneous:
			if e in eventDict:
				cE = eventDict.get(e)
				event.time = updateTime(event.time, cE.time)
	if event.includedInEvent:
		for e in event.includedInEvent:
			if e in eventDict:
				cE = eventDict.get(e)
				event.time = updateTime(event.time, cE.time)
	return event.time


def getEarliestBeforeTime(event, eventDict):

	myTime = event.beforeTime
	for e in event.beforeEvent:
		if e in eventDict:
			cE = eventDict.get(e)
			myTime = compareBeforeTime(myTime, cE.time)
	return myTime


def getLatestAfterTime(event, eventDict):
	myTime = event.afterTime
	for e in event.afterEvent:
		if e in eventDict:
			cE = eventDict.get(e)
			myTime = compareAfterTime(myTime, cE.time)
	return myTime



def integrateTimes(eventDict):

	updatedDict = {}
	docTime = eventDict.get('dct')
	if not docTime:
		docTime = Time()
	#collect as many times as possible
	for k, v in eventDict.items():
		if not k == 'dct':
			if not is_complete_time(v.time):
				newtime = findOutTime(v, eventDict)
				v.time = newtime	
			updatedDict[k] = v
	eventDict = updatedDict		
	
	#now see which we can integrate through before after relation
	for k, v in eventDict.items():
		if not k == 'dct':
			if v.afterTime.dct:
				v.afterTime = compareAfterTime(v.afterTime, docTime)
			if v.beforeTime.dct:
				v.beforeTime = compareBeforeTime(v.beforeTime, docTime)
			if v.beforeEvent:
				v.beforeTime = getEarliestBeforeTime(v, eventDict)
			if v.afterEvent:
				v.afterTime = getLatestAfterTime(v, eventDict)	
			#TODO: add combined information about duration
		updatedDict[k] = v
		
	return updatedDict		
			
				
	#2. collect possible before or after
		
		
		
def completeEventInfo(eventDict):
	
	updatedDict = {}
	for key, val in eventDict.items():
		if key == 'dct':
			updatedDict[key] = val
		else:
			if val.simultaneous:
				val.simultaneous = get_allSimultaneous(val.simultaneous, eventDict)
			if val.beforeEvent:
				val.beforeEvent = getBeforeChain(val.beforeEvent, eventDict)
			if val.afterEvent:
				val.afterEvent = getAfterChain(val.afterEvent, eventDict)
			if val.includedInEvent:
				val.includedInEvent = getIncludedChain(val.includedInEvent, eventDict)
			updatedDict[key] = val
	
	return updatedDict		

def is_earlier(time1, time2):
	
	if time1.year != 0:
		if time1.year < time2.year:
			return True
		elif time1.year == time2.year:
			if time1.month < time2.month:
				return True
			elif time1.month == time2.month:
				if time1.day < time2.day:
					return True
	return False

def getIndexToInsert(timeLine, time):

	if len(timeLine) == 0:
		return 0
	else:
		for x in range(0,len(timeLine)):
			#there's always at least one event on list
			compEv = timeLine[x][0][0]
			if is_earlier(time, compEv.time):
				return x
	return len(timeLine)


def updateIndexDict(iDict, timeLine, insertLoc):

	for x in range(insertLoc + 1, len(timeLine)):
		myEvs = timeLine[x]
		for ev in myEvs:
			iDict[ev.eventId] += 1

	return iDict
	
def findIndexAfter(afterevs, indexDict):

	myIndex = 0
	
	for ea in afterevs:
		if ea in indexDict:
			eaInd = indexDict.get(ea) + 1
			if eaInd > myIndex:
				myIndex = eaInd
				
	return myIndex


def findIndexBefore(beforeevs, indexDict):

	myIndex = len(indexDict)
	for be in beforeevs:
		if be in indexDict:
			beInd = indexDict.get(be)
			if beInd < myIndex:
				myIndex = beInd
	return myIndex



def order_same_slot_events(evLists):

	mini_timeline = []
	for events in evLists:
		if not mini_timeline:
			mini_timeline.append(events)
		else:
			myEv = events[0]
			inserted = False
			for x in range(len(mini_timeline) -1, -1, -1):
				evs = mini_timeline[x]
				
				for ev in evs:
					evId = ev.eventId
					
					if evId in myEv.afterEvent and not inserted:
						if len(mini_timeline) == x+1:
							mini_timeline.append(events)
							inserted = True
						else:
							mini_timeline[x+1] += events
							inserted = True
					elif evId in myEv.beforeEvent and not inserted:
						if x > 0:
							prevEv = mini_timeline[x-1]
							before = False
							for pEv in prevEv:
								if pEv in myEv.afterEvent:
									mini_timeline.insert(x, events)
									inserted = True
								elif pEv in myEv.beforeEvent:
									before= True
							if not inserted:
								if not before:
									mini_timeline[x] += events
									inserted = True
				if not inserted:
					evId = evs[0].eventId
				if evId in myEv.includedInEvent or myEv.eventId in ev	.includedInEvent:
					mini_timeline[x] += events
					#DOES THE SAME WITHOUT EVIDENCE, IS CORRECT FOR SHARED TASK, BUT NOT NECESSARILY FOR FUTURE
			if not inserted:
				mini_timeline[0] += events
		
	return mini_timeline
	
	
def createIndexDict(myTimeline):
		
	indexDict = {}
	for x in range(0, len(myTimeline)):
		myEvs = myTimeline[x]
		for ev in myEvs:
			indexDict[ev.eventId] = x
			
	return indexDict
	
	
def updateDictAfterSwap(bInd, myInd, indexDict, timeline):

	#update events moved back
	for x in range(bInd, myInd): 	
		myEvs = timeline[x]
		for ev in myEvs:
			indexDict[ev.eventId] -= 1
	#update events moved forward
	for x in range(myInd + 1):
		myEvs = timeline[x]
		for ev in myEvs:
			indexDict[ev.eventId] += 1
	#update swapped events
	myEvs = timeline[myInd]
	for ev in myEvs:
		indexDict[ev.eventId] = myInd
		
	return indexDict
	
	
def prepareTimeLineForReorderingUnmarked(timeline):

	nestedTimeline = []
	
	evList = []
	for evSet in timeline:
		
		myEv = evSet[0]
		if has_time(myEv.time):
			#append previous collected eventSets
			if evList:
				
				nestedTimeline.append(evList)
				evList = []
			#append eventSet with date itself
			nestedTimeline.append([evSet])
		else:
			evList.append(evSet)
	if evList:
		nestedTimeline.append(evList)
	return nestedTimeline
		
	
	
def initiateTimeLine(eventDict):
		
	timeLine = []	
	indexDict = {}
	appendAll = False
	merge = False
	debug = False
	for k, val in eventDict.items():
		merge = False	
		if not k in indexDict:
			if has_time(val.time):
				myEvents = [val]
				insertLoc = getIndexToInsert(timeLine, val.time)
				if insertLoc > 0:
					prevTime = timeLine[insertLoc - 1][0][0].time
					if time_equals(val.time, prevTime):
						insertLoc -= 1
						merge = True
				indexDict[k] = insertLoc
				if val.simultaneous:
					for e in val.simultaneous:
						if not e in indexDict:
							indexDict[e] = insertLoc
							if e in eventDict:
								myEvents.append(eventDict.get(e))
				if not merge:
					timeLine.insert(insertLoc,[myEvents])
			#		updateIndexDict(indexDict, timeLine, insertLoc)
				else:
					if insertLoc < len(timeLine): 
						timeLine[insertLoc].append(myEvents)
					else:
						timeLine.append([myEvents])
				#FIXME: no need for dict here, can be changed to other checking mechanism
				for ev in myEvents:
					indexDict[ev.eventId] = insertLoc
	
	myTimeline = []
	for evSets in timeLine:
		#no need to stretch out if only one set
		if len(evSets) == 1:
			myTimeline.append(evSets[0])
		else:
			miniTL = order_same_slot_events(evSets)
			myTimeline += miniTL
	
	indexDict = createIndexDict(myTimeline)
	
	
	for k, val in eventDict.items():
		if k == 't98':
			debug = True
		else:
			debug = False
		insert = False
		bInd = ''
		if not k in indexDict:
			myEvents = [val]
			if val.afterEvent:
				
				myInd = findIndexAfter(val.afterEvent, indexDict)
				if val.beforeEvent:
					bInd = findIndexBefore(val.beforeEvent, indexDict)
					#no need to do anything with this if bInd comes after myInd (or is equal)
					if not bInd < myInd:
						bInd = ''
			#if an event occurs before events in the very first slot, they should be inserted, not added (so that first slot moves up)
			elif val.beforeEvent:
				myInd = findIndexBefore(val.beforeEvent, indexDict)
				if myInd == 0:
					insert = True
				#all events for which no evidence that they are after another event, must be placed at the beginning
				myInd = 0
			else:
				myInd = 0
				
			indexDict[k] = myInd
			if val.simultaneous:
				for e in val.simultaneous:
					if not e in indexDict:
						indexDict[e] = myInd
						if e in eventDict:
							myEvents.append(eventDict.get(e))
			if bInd:
				myTimeline.insert(myInd, myEvents)
				oldEv = myTimeline.pop(bInd)
				myTimeline.insert(myInd, oldEv)
				updateDictAfterSwap(bInd, myInd, indexDict, myTimeline)
			else:
				myTimeline.insert(myInd, myEvents)
				updateIndexDict(indexDict,myTimeline, myInd)
				
	
	#add function that creates timeline blocks again
	nestedTimeline = prepareTimeLineForReorderingUnmarked(myTimeline)
	
	finaltimeline = []
	for evSets in nestedTimeline:
		if len(evSets) == 1:
			#print evSets[0]
			finaltimeline.append(evSets[0])
		else:
			miniTL = order_same_slot_events(evSets)
			finaltimeline += miniTL

	
	
	return finaltimeline
			

def getIdList(eventList):
	idList = []
	for e in eventList:
		idList.append(e.eventId)
		
	return idList
	
def time_equals(time1, time2):
	if time1.year == time2.year and time1.month == time2.month and time1.day == time2.day:
		return True
	else:
		return False
	
	
def time_loosely_equals(time1, time2):
	if not time1.year == time2.year:
		if not time1.year == 0 and not time2.year == 0:
			return False
	if not time1.month == time2.month:
		if not time1.month == 0 and not time2.month == 0:
			return False
	if not time1.day == time2.day:
		if not time1.day == 0 and not time2.day == 0:
			return False
	return True
	
	
def precedesInOrdering(pEvent, sInfo):

	if pEvent.eventId in sInfo.afterEvent:
		return True
	if sInfo.eventId in pEvent.beforeEvent:
		return True
		
	return False
	
	
def checkTimeLine(timeline):

	updatedTimeline = []
	previousEvents = []	
	latestTime = Time()
	latestEvent = Event('','')
	prevDated = False
	changed = False
	
	for x in range(0, len(timeline)):
		slot = timeline[x]
		slotSet = getIdList(slot)
		sInfo = slot[0]
		if not previousEvents:
			updatedTimeline.append(slot)
			previousEvents += slotSet
			latestEvent = sInfo
			if has_time(sInfo.time):
				prevDated = True
				latestTime = sInfo.time
		elif has_time(sInfo.time):
			if not is_earlier(latestTime, sInfo.time) and not time_equals(latestTime, sInfo.time):
				if is_complete_time(latestTime):
					if is_complete_time(sInfo.time):
						print 'Debugging problem: reordering required'
					else:
						updatedTimeline.insert(x-1,slot)
				else:
					updatedTimeline.insert(x,slot)
			else:	
				updatedTimeline.append(slot)	
			previousEvents += slotSet
			latestTime = sInfo.time
			latestEvent = sInfo
			prevDated = True
		else:
			if prevDated:
				updatedTimeline.append(slot)
			else:
				if precedesInOrdering(latestEvent, sInfo):
					updatedTimeline.append(slot)
				elif precedesInOrdering(sInfo, latestEvent):
					updatedTimeline.insert(x-1,slot)
					changed = True
				else:
					updatedTimeline[-1] += slot
					changed = True
			previousEvents += slotSet
			latestEvent = sInfo
			prevDated = False		
					
	if changed:
		updatedTimeline = checkTimeLine(updatedTimeline)
	else:
		return updatedTimeline		
	return updatedTimeline		

def createPrintOuttime(myTime):
	time = ''
	if myTime.year == 0:
		time += 'XXXX-' 
	else:
		time += str(myTime.year) + '-' 
	if myTime.month == 0:
		time += 'XX-'
	else:	
		time += str(myTime.month) + '-' 
	if myTime.day == 0:
		time += 'XX' 
	else:
		time += str(myTime.day)
		
	return time


def printOutTimeline(cleanedTimeline):
	outputDoc = open('mytimeline.txt','w')
	score = 0
	for slot in cleanedTimeline:
		for event in slot:
			time = createPrintOuttime(event.time)
			outputDoc.write(str(score) + '\t' + time  + '\t' +  event.eventId  + '\t' + str(event.entity) + '\n')
		score += 1
	
def placeEventsOnTimeLine(eventDict):		
		
	timeline = initiateTimeLine(eventDict)	
# 	cleanedTimeline = checkTimeLine(timeline)
	
	return timeline
	
def cleantimeline(timeline):
	
	cleaned_tl = []
	for slot in timeline:
		new_slot = []
		for event in slot:
			if isinstance(event, list):
				new_slot += event
			else:
				new_slot.append(event)
		cleaned_tl.append(slot)
	return cleaned_tl
	

def mergeTimelines(timelineList):

	allTimes = []
	for timeline in timelineList:
		#timeline = cleantimeline(timeline)
		if not allTimes:
		
			allTimes = timeline
			
		else:
			currentLoc = 0
			addTilnewDate = False
			idTimeslot = False
			justAppend = False
			currentDate = Time()
			for slot in timeline:
				myEv = slot[0]
				#FIX ME: not the most efficient way to do this...make more scalable
				if justAppend:
					
					allTimes.append(slot)
				elif has_time(myEv.time):
					if time_equals(myEv.time, currentDate):
						if addTilnewDate:
							allTimes.insert(currentLoc, slot)
							if currentLoc < len(allTimes):
								currentLoc += 1
							else:
								justAppend = True
						elif idTimeslot:	
							compEv = allTimes[currentLoc][0]
							#is both within same time slot, append
							if has_time(compEv.time) and time_equals(compEv.time, currentDate):
								allTimes[currentLoc] += slot
								
								
							else:
								allTimes.insert(currentLoc,slot)
								
							if currentLoc < len(allTimes):
								currentLoc += 1
							else:
								justAppend = True
					else:
						idTimeslot = False
						addTilnewDate = False
						inserted = False
						while True:
							if currentLoc < len(allTimes):
								compEv = allTimes[currentLoc][0]
								if has_time(compEv.time):
									if is_earlier(myEv.time, compEv.time):
										allTimes.insert(currentLoc, slot)
										inserted = True
										addTilnewDate = True
										currentDate = myEv.time
									elif time_equals(myEv.time, compEv.time):
										allTimes[currentLoc] += slot
										inserted = True
										currentDate = myEv.time
										idTimeslot = True
										currentLoc -= 1	
								currentLoc += 1
							else:
								justAppend = True
							
							if inserted:
								break
							elif justAppend:
								allTimes.append(slot)
								break
				else:
					if addTilnewDate:
						allTimes.insert(currentLoc, slot)	
						if currentLoc < len(allTimes):
							currentLoc += 1
						else:
							justAppend = True
					else:
						if currentLoc < len(allTimes):
							cEv = allTimes[currentLoc][0]
							if has_time(cEv.time):
								allTimes.insert(currentLoc,slot)
								addTilnewDate = True
							else:
								allTimes[currentLoc] += slot
								
							currentLoc += 1
						else:
							allTimes.append(slot)
							justAppend = True
					
	return allTimes					

def majorityVote(events):

	disTimeList = {}
	for e in events:
		if not disTimeList:
			disTimeList[e.time] = 1
		else:
			inserted = False
			for k, v in disTimeList.items():
				if time_equals(k, e.time):
					disTimeList[k] += 1
					inserted = True
			if not inserted:
				disTimeList[e.time] = 1
	max_val = 0
	tie = False
	myTime = Time()
	for k, v in disTimeList.items():
		if v > max_val:
			myTime = k
			max_val = v
			tie = False
		elif v == max_val:
			tie = True
	if tie:
		return False
	else:
		return myTime

def conflictingTimes(events):

	eventT = events[0].time
	for e in events:
		if not time_loosely_equals(eventT, e.time):
			return True
	return False

	

def checkForContradictions(EventDict):

	myTime = False
	for key, events in EventDict.items():
		if not key == 'dct':
			if len(events) > 1:
				if conflictingTimes(events):
					if len(events) > 2:
						myTime = majorityVote(events)
						if myTime:
							new_events = []
							for e in events:
								e.time = myTime
								new_events.append(e)
							EventDict[key] = new_events
					if not myTime:
						print 'Remaining conflicting events'
	return EventDict
		
def addDocIds(timelinelist, docname):

	updatedDocnames = []
	
	for slot in timelinelist:
		up_slot = []
		for event in slot:
			event.eventId = docname + '_' + event.eventId
			up_slot.append(event)		
				
		updatedDocnames.append(up_slot)
		
	return updatedDocnames
				
				
def well_defined_file(inputfile):
	for line in inputfile:
		parts = line.split()
		if len(parts) == 4:
			return True
		else:
			return False
						
						
def check_if_wellFormed(inputfile):

	myfile = open(inputfile, 'r')
	for line in myfile:
		parts = line.split()
		if len(parts) == 4:
			return True
		else:
			return False

							
def create_timeline(inputdir):

	timelineList = []
	for inputfile in os.listdir(inputdir):
		if check_if_wellFormed(inputdir + inputfile):
			myinput = open(inputdir + inputfile, 'r')
			doc_timedEvents = create_docTimedEvents(myinput, inputfile)
			myinput.close()
			doc_timedEvents = checkForContradictions(doc_timedEvents)
		
			mergedEvents = mergeInformation(doc_timedEvents)
			completedEvents = completeEventInfo(mergedEvents)
			completedFlipEvents = flipEventRels(completedEvents) 
			completedTimesAndEvents = integrateTimes(completedFlipEvents)
			mytimeline = placeEventsOnTimeLine(completedTimesAndEvents)
			
			
			if len(mytimeline) > 0 and isinstance(mytimeline[0], list):
				mytimeline = addDocIds(mytimeline, inputfile)
				timelineList.append(mytimeline)
		
		
		
	finalTimeline = mergeTimelines(timelineList)
	printOutTimeline(finalTimeline)	
		
		
		
		#update dictionary, by merging information from different lines + interpreting information where possible
		#create timeline based on complete information
		#return time line
		
def main(argv=None):
	if argv == None:
		argv = sys.argv
	
	if len(argv) > 1:
		create_timeline(argv[1])
	else:
		print 'Error: you must provide an input'	
			
if __name__ == '__main__':
	main()