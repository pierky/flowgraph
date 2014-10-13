#!/usr/bin/env python

# Copyright (c) 2014 Pier Carlo Chiodi - http://www.pierky.com
# Licensed under The MIT License (MIT) - http://opensource.org/licenses/MIT

import json
import datetime
import smtplib
from core import *
from config import *

# returns None or failure reason
def DoesScheduleMatch( DateTime, Schedule ):
	if "StartDate" in Schedule:
		if DateTime.date() < datetime.datetime.strptime( Schedule["StartDate"], "%Y-%m-%d" ).date():
			return "StartDate"

	if "StopDate" in Schedule:
		if DateTime.date() > datetime.datetime.strptime( Schedule["StopDate"], "%Y-%m-%d" ).date():
			return "StopDate"

	if "StartTime" in Schedule:
		StartTime = datetime.datetime.strptime( Schedule["StartTime"], "%H:%M" ).time()
	else:
		StartTime = None

	if "StopTime" in Schedule:
		StopTime = datetime.datetime.strptime( Schedule["StopTime"], "%H:%M" ).time()
	else:
		StopTime = None

	if StartTime and StopTime:
		if StartTime < StopTime:
			if DateTime.time() < StartTime or DateTime.time() > StopTime:
				return "StartTime/StopTime"
		else:
			if DateTime.time() > StopTime and DateTime.time() < StartTime:
				return "StopTime/StartTime"
	elif StartTime:
		if DateTime.time() < StartTime:
			return "StartTime"
	elif StopTime:
		if DateTime.time() > StopTime:
			return "StopTime"

	if "DoW" in Schedule:
		if not ( DateTime.date().isoweekday() in Schedule["DoW"] ):
			return "DoW"

	return None

def ProcessGraph( Graph ):
	Error = None

	Debug( "Processing schedules for graph '%s'" % Graph["Title"] )

	if not ( "Schedules" in Graph["Scheduler"] ):
		Error = "No schedules for this graph"
		return Error

	Query = Graph["Query"]

	Error = NormalizeQuery( Query )

	if not Error is None:
		return Error

	MaxCache = Graph["Scheduler"]["MaxCache"] if "MaxCache" in Graph["Scheduler"] else MAX_CACHE_NFDATA

	Now = datetime.datetime.now()

	Interval = datetime.timedelta( seconds = Query["SourceFiles"]["Interval"] or NETFLOW_INTERVAL )

	Errors = []

	StartDateTime = None
	StopDateTime = None
	SchedulesMatchFound = 0

	# test 2 intervals before the current one + the current one
	for DateTime in [ Now - Interval - Interval,
				Now - Interval,
				Now ]:

		for Schedule in Graph["Scheduler"]["Schedules"]:
			FailureReason = DoesScheduleMatch( DateTime, Schedule )

			if FailureReason is None:
				Debug( "DateTime %s OK for %s!" % ( DateTime, Schedule ) )
				break
			else:
				Debug( "DateTime %s does not match for %s because of %s!" % ( DateTime, Schedule, FailureReason ) )

		if FailureReason is None:
			SchedulesMatchFound += 1

			Error = FilesExist( DateTime, DateTime, Query )

			if Error is None:
				if StartDateTime is None:
					StartDateTime = DateTime
					StopDateTime = DateTime
				else:
					StopDateTime = DateTime
			else:
				Debug( Error )

	if not StartDateTime is None:
		Error = ProcessFiles( StartDateTime, StopDateTime, Query, MaxCache )[0]

		if not Error is None:
			Errors.append( Error )
	else:
		# error only if more than one datetime have been tested and none could be processed
		if SchedulesMatchFound > 1:
			Errors.append( "Can't find netflow data files to process for this graph" )

	if Errors != []:
		return ", ".join( Errors )
	else:
		return None

def SchedulerMain():
	SetupLogging()

	if os.path.isfile( "%s/%s" % ( VAR_DIR, GRAPHS_FILENAME ) ):
		try:
			JSON_Data = open( "%s/%s" % ( VAR_DIR, GRAPHS_FILENAME ) )
			Graphs = json.load(JSON_Data)
			JSON_Data.close()
		except:
			Error( "Scheduler error while reading graphs from %s" % ( "%s/%s" % ( VAR_DIR, GRAPHS_FILENAME ) ) )

	for GraphID in Graphs:
		Graph = Graphs[GraphID]
		if "Scheduler" in Graph:
			Error = ProcessGraph( Graph )

			if not Error is None:
				Error( "Scheduler error while processing graph '%s'\n\n%s" % ( Graph["Title"], Error ) )

SchedulerMain()
