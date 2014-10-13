# Copyright (c) 2014 Pier Carlo Chiodi - http://www.pierky.com
# Licensed under The MIT License (MIT) - http://opensource.org/licenses/MIT

import logging
from logging.handlers import RotatingFileHandler
from logging.handlers import SMTPHandler
import subprocess
import os
import sys
import traceback
import csv
import datetime
import json
from copy import deepcopy
from config import *
import hashlib

CURRENT_RELEASE = "v0.1.0"

def SetupLogging():
	logger = logging.getLogger("FlowGraph")

	hdlr = logging.handlers.RotatingFileHandler( LOG_FILEPATH, maxBytes=1000000, backupCount=3 )
	formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
	hdlr.setFormatter(formatter)
	logger.addHandler(hdlr)

	if SEND_ERROR_VIA_EMAIL:
		hdlr = logging.handlers.SMTPHandler( ( SEND_ERROR_SMTP, SEND_ERROR_SMTP_PORT ), SEND_ERROR_FROM_EMAIL, [ SEND_ERROR_TO_EMAIL ], "FlowGraph error" )
		hdlr.setFormatter(formatter)
		hdlr.setLevel(logging.ERROR)
		logger.addHandler(hdlr)

	if DEBUG:
		logger.setLevel(logging.DEBUG)
	else:
		logger.setLevel(logging.INFO)

	if sys.__stdin__.isatty():
		Debug( "Interactive - logging to stdout too" )

def Log( lev, msg, exc_info=False ):
	logger = logging.getLogger("FlowGraph")
	logger.log( lev, msg, exc_info=exc_info )

	if sys.__stdin__.isatty():
		print( msg )

def Error(s):
	Log( logging.ERROR, s )

def Debug(s):
	Log( logging.DEBUG, s )

def GetException():
	Log( logging.ERROR, "Exception", True )

	runtimeerr = ""
	try:
		type, value, tb = sys.exc_info()
		if not( type is None and value is None ):
			runtimeerr += "\n--------------------------------------------------\n"
			runtimeerr += "type: %s\n" % type
			runtimeerr += "value: %s\n" % value
			runtimeerr += "\n"
			runtimeerr += traceback.format_exc()
	except:
		runtimeerr += "Error while getting sys.exc_info() data"

	return runtimeerr
	
def GetNfDumpField( FieldName ):
	for Field in NFDUMP_FIELDS:
		if Field["ID"] == FieldName:
			return Field
	return None

def CSVFromNfDump( File, Query ):

	Error = None
	CSV = None

	Args = [ NFDUMP_PATH ]

	Args.extend( [ "-M", "%s/%s" % ( Query["SourceFiles"]["BaseDir"] or NETFLOW_DATA_DIR, ":".join( Query["SourceFiles"]["SourceIDs"] ) ) ] )
	Args.extend( [ "-r", File ] )
	Args.extend( [ "-N" ] )
	Args.extend( [ "-o", "csv" ] )

	NfDumpField = GetNfDumpField( Query["AggrField"] )

	AggrField = NfDumpField["AggrType_%s" % Query["AggrType"] ]

	if NfDumpField.has_key("ArgRequired"):
		if NfDumpField["ArgRequired"]:
			AggrField = AggrField % Query["AggrFieldArg"]

	if Query["AggrType"] == "s":
		Args.extend( [ "-s", "%s/%s" % ( AggrField, Query["OrderBy"]["ColName"] ) ] )
		Args.extend( [ "-n", str( Query["TopN"] ) ] )
	else:
		Args.extend( [ "-A", AggrField ] )

	if Query["Filter"]:
		Filter = Query["Filter"]
		Filter = Filter.replace( '%filters%', VAR_DIR )
		Args.extend( [ Filter ] )

	Debug( "Running nfdump: %s" % " ".join(Args) )

	try:
		NfDump = subprocess.Popen( Args, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
	except:
		Error = "Error while trying to execute NfDump: Args %s\n%s" % ( Args, GetException() )
		return Error, CSV

	try:
		(NfDump_stdout, NfDump_stderr) = NfDump.communicate()

		NfDump_ExitCode = NfDump.wait()
	except:
		Error = "Error while trying to read NfDump output: Args %s\n%s" % ( Args, GetException() )
		return Error, CSV

	if not NfDump_stderr:
		if NfDump_ExitCode == 0:
			try:
				CSV = list( csv.reader(NfDump_stdout.split('\n')) )
			except:
				Error = "Error while reading CSV from NfDump output.\n%s" % GetException()
				return Error, CSV
		else:
			Error = "NfDump exit code != 0: %s." % NfDump_ExitCode
	else:
		Error = "NfDump reported errors: %s" % NfDump_stderr

	return Error, CSV

# returns: Error, array of <Record>
def ReadRecordsetFromCSV( CSV, Query ):
	Error = None
	Recordset = []

	ColIdx_Key = None

	# ----------------------------------
	# Key field

	try:
		if Query["AggrType"] == "s":
			# 'ts', 'te', 'td', 'pr', 'val', 'fl', 'flP', 'ipkt', 'ipktP', 'ibyt', 'ibytP', 'ipps', 'ipbs', 'ibpp'
			KeyField = "val"

			ColMap = [
				{ "name": "bytes",	"fields": [ "ibyt" ] },
				{ "name": "packets",	"fields": [ "ipkt" ] },
				{ "name": "flows",	"fields": [ "fl" ] },
				{ "name": "bps",	"fields": [ "ipbs", "pbs" ] },	# depending on nfdump version,
				{ "name": "pps",	"fields": [ "ipps", "pps" ] },	# output fields have different
				{ "name": "bpp",	"fields": [ "ibpp", "bpp" ] }	# names (ipps or pps, ...)
			]
		else:
			# ts,te,td,sa,da,sp,dp,pr,flg,fwd,stos,ipkt,ibyt,opkt,obyt,in,out,sas,das,smk,dmk,dtos,dir,nh,nhb,svln,dvln,ismc,odmc,idmc,osmc,mpls1,mpls2,mpls3,mpls4,mpls5,mpls6,mpls7,mpls8,mpls9,mpls10,cl,sl,al,ra,eng,exid,tr
			NfDumpField = GetNfDumpField( Query["AggrField"] )

			if NfDumpField.has_key("OutputField"):
				KeyField = NfDumpField["OutputField"]
			else:
				KeyField = Query["AggrField"]

			ColMap = [
				{ "name": "bytes",	"fields": [ "ibyt" ] },
				{ "name": "packets",	"fields": [ "ipkt" ] }
			]

		ColIdx_Key = CSV[0].index(KeyField)
	except:
		Error = "Can't find key field index: %s" %KeyField
		return Error, Recordset

	if Query["AggrType"] == "A":
		OrderByColFound = False

		for Col in ColMap:
			if Col["name"] == Query["OrderBy"]["ColName"]:
				OrderByColFound = True
				break

		if not OrderByColFound:
			Error = "Can't sort by %s, field not present in the output." % Query["OrderBy"]["ColName"]
			return Error, Recordset
	# ----------------------------------
	# Read data

	Recordset = []

	ParsingSummary = 0	# 0 = summary not reached;
				# 1 = previous line = "Summary", processing summary's header line
				# 2 = processing summary's data

	SummaryHeader = None
	SummaryValues = None

	Line = CSV[0]

	for Col in ColMap:
		for Field in Col["fields"]:
			if Field in Line:
				Col["pos"] = Line.index( Field )

	for Line in CSV[1:]:
		if len(Line) > 0:
			if ParsingSummary == 0:
				if Line[0] == "Summary":
					ParsingSummary = 1
				else:
					Key = Line[ColIdx_Key]
					Record = {}
					Record["key"] = Key

					for Col in ColMap:
						if "pos" in Col:
							Record[ Col["name"] ] = int( Line[ Col["pos"] ] )

					Recordset.append( Record )

			elif ParsingSummary == 1:
				SummaryHeader = deepcopy( Line ) 
				ParsingSummary += 1

			elif ParsingSummary == 2:
				SummaryValues = deepcopy( Line )
                                ParsingSummary += 1

			elif ParsingSummary > 2:
				break

	if Query["AggrType"] == "A":
		Recordset = sorted( Recordset, key=lambda Record: int(Record["bytes"]), reverse=( Query["OrderBy"]["Order"] == "DESC" ) )[:Query["TopN"]]

	if SummaryValues:
		ColMap = [
			{ "name": "bytes",	"fields": [ "bytes" ] },
			{ "name": "packets",	"fields": [ "packets" ] },
			{ "name": "flows",	"fields": [ "flows" ] },
			{ "name": "bps",	"fields": [ "avg_bps" ] },
			{ "name": "pps",	"fields": [ "avg_pps" ] },
			{ "name": "bpp",	"fields": [ "avg_bpp" ] }
		]
		for Col in ColMap:
			for Field in Col["fields"]:
				if Field in SummaryHeader:
					Col["pos"] = SummaryHeader.index( Field )
	
		Record = {}
		Record['key'] = 'summary'

		for Col in ColMap:
			if "pos" in Col:
				Record[ Col["name"] ] = int( SummaryValues[ Col["pos"] ] )

		Recordset.append( Record )

	return Error, Recordset

# returns: Error, array of <Record>
def GetRecordsetForEpoch( Epoch, Query, CacheData ):
	Error = None
	Recordset = []

	try:
		FileName = datetime.datetime.fromtimestamp(Epoch).strftime( Query["SourceFiles"]["FileNameFormat"] or NETFLOW_FILENAME_FORMAT )
	except:
		Error = "Error building netflow files name from epoch %d and format %s" % ( Epoch, Query["SourceFiles"]["FileNameFormat"] or NETFLOW_FILENAME_FORMAT )
		return Error, Recordset

	if CacheData.has_key( str(Epoch) ):
		Debug( "Cache hit for epoch %d (%s)" % ( Epoch, FileName ) )

		return Error, CacheData[str(Epoch)]
	else:
		Debug( "Processing netflow data for epoch %d (%s)" % ( Epoch, FileName ) )

		CSV = []
		(Error, CSV) = CSVFromNfDump ( FileName, Query )

		if not Error is None:
			return Error, Recordset

		(Error, Recordset) = ReadRecordsetFromCSV( CSV, Query )

		if not Error is None:
			return Error, Recordset

		CacheData[str(Epoch)] = Recordset

	return Error, Recordset

def GetCacheFile( Query ):
	if "CacheFile" in Query:
		if Query["CacheFile"]:
			return Query["CacheFile"]

	return "%s.cache" % hashlib.md5( json.dumps( Query, sort_keys=True ).encode() ).hexdigest()

def CacheFileExists( Query ):
	CacheFile = GetCacheFile( Query )

	if os.path.isfile( "%s/%s" % ( VAR_DIR, CacheFile ) ):
		return os.path.getsize( "%s/%s" % ( VAR_DIR, CacheFile ) ) > 0
	else:
		return False

# returns: Error, <CacheData>
def GetCacheIfValid( Query ):
	Error = None
	CacheData = {}

	CacheFile = GetCacheFile( Query )

	if CacheFileExists( Query ):
		try:
			JSON_Data = open( "%s/%s" % ( VAR_DIR, CacheFile ) )
			CacheData = json.load(JSON_Data)
			JSON_Data.close()
		except:
			Error = "Error reading cache file: %s - %s" % ( "%s/%s" % ( VAR_DIR, CacheFile ), GetException() )
			return Error, CacheData

		if "Query" in CacheData:
			if json.dumps( CacheData["Query"], sort_keys=True ) != json.dumps( Query, sort_keys=True ):
				Debug( "Cached data don't match query - Ignoring cache (%s)" % ( "%s/%s" % ( VAR_DIR, CacheFile ) ) )
				CacheData = {}
			else:
				Debug( "Cache data is valid (%s)" % ( "%s/%s" % ( VAR_DIR, CacheFile ) ) )
		else:
			Debug( "Invalid cache data - Ignoring cache (%s)" % ( "%s/%s" % ( VAR_DIR, CacheFile ) ) )
			CacheData = {}
	else:
		Debug( "Cache file %s does not exist." % ( "%s/%s" % ( VAR_DIR, CacheFile ) ) );

	return Error, CacheData

# if CacheData == None just performs a writing test
def WriteCache( Query, CacheData ):
	Error = None

	CacheFile = GetCacheFile( Query )

	try:
		with open( "%s/%s" % ( VAR_DIR, CacheFile ), 'w' ) as OutputJSONFile:
			if CacheData:
				CacheData["Query"] = Query
				json.dump( CacheData, OutputJSONFile, sort_keys=True )

			OutputJSONFile.close()	
	except:
		Error = "Error writing cache file: %s - %s" % ( "%s/%s" % ( VAR_DIR, CacheFile ), GetException() )

	return Error

# CacheData is optional:
# 	- if given, the function first verifies if data are already
#	present in cache;
#	- if missing, the function only verifies if netflow data file
#	exists.
def FilesExist( Start, Stop, Query, CacheData={} ):
	StartEpoch = int(Start.strftime('%s'))
	StopEpoch = int(Stop.strftime('%s'))

	CurrEpoch = int( StartEpoch / ( Query["SourceFiles"]["Interval"] or NETFLOW_INTERVAL ) ) * ( Query["SourceFiles"]["Interval"] or NETFLOW_INTERVAL )

	MissingFiles = []

	while CurrEpoch <= StopEpoch:
		if not ( CacheData or {} ).has_key( str(CurrEpoch) ):
			CurrDate = datetime.datetime.fromtimestamp(CurrEpoch)
			FileName = CurrDate.strftime( Query["SourceFiles"]["FileNameFormat"] or NETFLOW_FILENAME_FORMAT )

			for SourceID in Query["SourceFiles"]["SourceIDs"]:
				FilePath = "%s/%s/%s" % ( Query["SourceFiles"]["BaseDir"] or NETFLOW_DATA_DIR, SourceID, FileName )

				if not os.path.isfile( FilePath ):
					MissingFiles.append( FilePath )
				else:
					if not ( os.path.getsize( FilePath ) > 0 ):
						MissingFiles.append( FilePath )

		CurrEpoch = CurrEpoch + ( Query["SourceFiles"]["Interval"] or NETFLOW_INTERVAL )

	if MissingFiles != []:
		return "Missing files for the selected time window: %s" % ", ".join( MissingFiles )
	else:
		return None

# MaxCache in days
# returns: Error, <ChartData>
def ProcessFiles( Start, Stop, Query, MaxCache=None ):
	Error = None
	Results = {
		"DistinctKeys": [],
		"Epoches": []
	}

	Error = NormalizeQuery( Query )

	if not Error is None:
		return Error, Results

	# ----------------------------------
	# Load cache

	( Error, CacheData ) = GetCacheIfValid( Query )

	if not Error is None:
		return Error, Results

	# ----------------------------------
	# File exists?

	Error = FilesExist( Start, Stop, Query, CacheData )

	if not Error is None:
		return Error, Results

	# ----------------------------------
	# Cache writable?

	Error = WriteCache( Query, None )

	if not Error is None:
		return Error, Results

	# ----------------------------------
	# Process files within date range

	StartEpoch = int(Start.strftime('%s'))
	StopEpoch = int(Stop.strftime('%s'))

	CurrEpoch = int( StartEpoch / ( Query["SourceFiles"]["Interval"] or NETFLOW_INTERVAL ) ) * ( Query["SourceFiles"]["Interval"] or NETFLOW_INTERVAL )

	while CurrEpoch <= StopEpoch:
		CurrDate = datetime.datetime.fromtimestamp(CurrEpoch)
		FileName = CurrDate.strftime( Query["SourceFiles"]["FileNameFormat"] or NETFLOW_FILENAME_FORMAT )

		Error, Recordset = GetRecordsetForEpoch( CurrEpoch, Query, CacheData )

		if not Error is None:
			break

		for Record in Recordset:
			if not Record["key"] in Results["DistinctKeys"]:
				Results["DistinctKeys"].append( Record["key"] )

		Results["Epoches"].append( { "Epoch": CurrEpoch, "Recordset": Recordset } )

		CurrEpoch = CurrEpoch + ( Query["SourceFiles"]["Interval"] or NETFLOW_INTERVAL )

	if Error is None:
		if MaxCache:
			NowEpoch = int( datetime.datetime.now().strftime('%s') )

			for CacheKey in CacheData.keys():
				if CacheKey.isdigit():
					Epoch = int( CacheKey )
					if Epoch < NowEpoch - ( MaxCache * 86400 ):
						del CacheData[CacheKey]

		Error = WriteCache( Query, CacheData )

	return Error, Results

def NormalizeQuery( Query ):
	Errors = []

	if not Query.has_key("SourceFiles"):
		Errors.append("Missing source files information.")
	else:
		if not Query["SourceFiles"].has_key("SourceIDs"):
			Errors.append("Missing source files source IDs.")
		else:
			if not Query["SourceFiles"]["SourceIDs"]:
				Errors.append("Missing source files source IDs.")
			else:
				for SourceID in Query["SourceFiles"]["SourceIDs"]:
					if not SourceID in NETFLOW_SOURCESID:
						Errors.append("Source ID %s not found in the configuration file (NETFLOW_SOURCESID)" % SourceID)

	if not "Interval" in Query["SourceFiles"]:
		Query["SourceFiles"]["Interval"] = None
	Query["SourceFiles"]["Interval"] = Query["SourceFiles"]["Interval"] or None

	if not "BaseDir" in Query["SourceFiles"]:
		Query["SourceFiles"]["BaseDir"] = None
	Query["SourceFiles"]["BaseDir"] = Query["SourceFiles"]["BaseDir"] or None

	if not "FileNameFormat" in Query["SourceFiles"]:
		Query["SourceFiles"]["FileNameFormat"] = None
	Query["SourceFiles"]["FileNameFormat"] = Query["SourceFiles"]["FileNameFormat"] or None


	if not Query.has_key("AggrType"):
		Errors.append("Missing aggregation type.")
	else:
		if Query["AggrType"] != "A" and Query["AggrType"] != "s":
			Errors.append("Aggregation type can be 'A' or 's'; unknown value: %s." % Query["AggrType"] )

	if not Query.has_key("AggrField"):
		Errors.append("Missing aggregation field.")
	else:
		if not Query["AggrField"]:
			Errors.append("Missing aggregation field.")
		else:
			NfDumpField = GetNfDumpField( Query["AggrField"] )

			if NfDumpField is None:
				Errors.append("Aggregation field unknown: %s" % Query["AggrField"])
			else:
				if NfDumpField.has_key("ArgRequired"):
					if NfDumpField["ArgRequired"]:
						if not Query.has_key("AggrFieldArg"):
							Errors.append("Aggregation field requires an argument: %s" % Query["AggrField"])
						else:
							if not Query["AggrFieldArg"]:
								Errors.append("Aggregation field requires an argument: %s" % Query["AggrField"])
					else:
						Query.pop("AggrFieldArg", None)
				else:
					Query.pop("AggrFieldArg", None)

				if not NfDumpField.has_key("AggrType_%s" % Query["AggrType"]):
					Errors.append("Aggregation field '%s' does not support aggregation type '%s'" % ( Query["AggrField"], Query["AggrType"] ) )
				else:
					if not NfDumpField["AggrType_%s" % Query["AggrType"]]:
						Errors.append("Aggregation field '%s' does not support aggregation type '%s'" % ( Query["AggrField"], Query["AggrType"] ) )

	if not Query["OrderBy"].has_key("ColName"):
		Errors.append("Missing order by column name")
	else:
		if not Query["OrderBy"]["ColName"]:
			Errors.append("Missing order by column name")

	if not Query.has_key("TopN"):
		Errors.append("Missing TopN parameter.")

	if Errors:
		return "\n".join(Errors)
	else:
		return None


