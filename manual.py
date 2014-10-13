#!/usr/bin/env python

# Copyright (c) 2014 Pier Carlo Chiodi - http://www.pierky.com
# Licensed under The MIT License (MIT) - http://opensource.org/licenses/MIT

import json
import datetime
import sys
from core import *
from config import *

def ProcessGraph( DateTime, Graph ):
	Error = None

	print( "\n\nProcessing schedules for graph '%s'" % Graph["Title"] )

	if not ( "Schedules" in Graph["Scheduler"] ):
		return

	for Schedule in Graph["Scheduler"]["Schedules"]:
		FailureReason = DoesScheduleMatch( DateTime, Schedule )

		if not FailureReason:
			print( "DateTime %s OK for %s!" % ( DateTime, Schedule ) )
			break
		else:
			print( "DateTime %s does not match for %s because of %s!" % ( DateTime, Schedule, FailureReason ) )

	Query = Graph["Query"]

	Error = FilesExist( DateTime, DateTime, Query )

	if Error is None:
		Error = ProcessFiles( DateTime, DateTime, Query )[0]
	else:
		# if files from the last run are still not ready, try with files from the previous run

		PreviousDateTime = DateTime - datetime.timedelta( seconds = Query["SourceFiles"]["Interval"] or NETFLOW_INTERVAL )
		Error = FilesExist( PreviousDateTime, PreviousDateTime, Query )

		if Error is None:
			Error = ProcessFiles( PreviousDateTime, PreviousDateTime, Query )[0]

	return Error

def Main():
	if os.path.isfile( "%s/%s" % ( VAR_DIR, GRAPHS_FILENAME ) ):
		try:
			JSON_Data = open( "%s/%s" % ( VAR_DIR, GRAPHS_FILENAME ) )
			Graphs = json.load(JSON_Data)
			JSON_Data.close()
		except:
			print( "Error while reading graphs from %s" % ( "%s/%s" % ( VAR_DIR, GRAPHS_FILENAME ) ) )
			return

	# ---------------------------------

	if len(sys.argv) == 1:
		print( "" )
		print( "FlowGraph %s - script to manually process data queries from graphs" % CURRENT_RELEASE )
		print( "Copyright (c) 2014 Pier Carlo Chiodi - http://www.pierky.com\n" )
		print( "Usage:\n\t%s\tinteractive\n\t%s <graph_id> \"<start_datetime>\" \"<stop_datetime>\"\n" % ( sys.argv[0], sys.argv[0] ) )

	if len(sys.argv) > 1:
		SelectedGraphID = sys.argv[1]
	else:
		for GraphID in Graphs:
			Graph = Graphs[GraphID]

			print( "ID: %s - %s" % ( GraphID, Graph["Title"] ) )

		print("")
		sys.stdout.write( "Type the ID of the graph you want to execute the query for: " )
		SelectedGraphID = raw_input()

	if SelectedGraphID:
		if not SelectedGraphID in Graphs:
			print( "Invalid or not existent graph ID; aborting." )
			return
	else:
		print( "Missing graph ID; aborting." )
		return

	# ---------------------------------

	if len(sys.argv) > 2:
		InputDateTime = sys.argv[2]
	else:
		sys.stdout.write( "Enter the start date and time (YYYY-MM-DD HH:NN): " )
		InputDateTime = raw_input()

	try:
		StartDate = datetime.datetime.strptime( InputDateTime, "%Y-%m-%d %H:%M" )
	except:
		print( "Invalid start date/time; aborting." )
		return

	# ---------------------------------

	if len(sys.argv) > 3:
		InputDateTime = sys.argv[3]
	else:
		sys.stdout.write( "Enter the stop date and time (YYYY-MM-DD HH:NN): " )
		InputDateTime = raw_input()

	try:
		StopDate = datetime.datetime.strptime( InputDateTime, "%Y-%m-%d %H:%M" )
	except:
		print( "Invalid stop date/time; aborting." )
		return

	# ---------------------------------

	if not len(sys.argv) > 3:
		sys.stdout.write( "Confirm processing graph ID %s (%s) from %s to %s? [yes] " % 
			( SelectedGraphID, Graphs[SelectedGraphID]["Title"], StartDate.strftime("%Y-%m-%d %H:%M"), StopDate.strftime("%Y-%m-%d %H:%M")  ))

		Confirm = raw_input()

		if not Confirm == "yes":
			print( "Aborting." )
			return

	print( "Processing files..." )
	Error = ProcessFiles( StartDate, StopDate, Graphs[SelectedGraphID]["Query"] )[0]

	if Error:
		print( "Processing complete with errors: %s" % ( Error ) )
	else:
		print( "Processing complete successfully." )

Main()
