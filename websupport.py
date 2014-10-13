# Copyright (c) 2014 Pier Carlo Chiodi - http://www.pierky.com
# Licensed under The MIT License (MIT) - http://opensource.org/licenses/MIT

import json
import time
import urllib2
import uuid
import socket
import subprocess
import re
from core import *
from config import *

Cache = {}
"""
Cache = { <resource_id1>: <CacheObject>, <resource_id2>: <CacheObject> }

CacheObject = {
	TS: <epoch>
	Description: <string>	
}
"""

# All functions return an object that will be converted to JSON
# for client-server exchange.
# Errors are returned in the form { "error": "<error text>" }

def GetDetails(resource_type,resource):
	ResourceID = "%s-%s" % ( resource_type, resource )

	if ResourceID in Cache:
		if Cache[ResourceID]["TS"] >= int(time.time()) - MAX_CACHE_RES_DETAILS:
			return Cache[ResourceID]

	if resource_type == "AS":
		URL = "https://stat.ripe.net/data/as-overview/data.json?resource=AS%s" % resource

	elif resource_type == "IP":
		URL = "https://stat.ripe.net/data/prefix-overview/data.json?resource=%s" % resource

	elif resource_type == "WHOIS":
		URL = "https://stat.ripe.net/data/whois/data.json?resource=%s" % resource

	else:
		return { "error": "Unknown resource type: %s" % resource_type }

	try:
		data = json.loads( urllib2.urlopen(URL).read() )
	except:
		return { "error": "Can't get resource details - error while loading RIPE Stat JSON response" }

	if data["status"] == "ok":

		if "data" in data:
			Cache[ResourceID] = {}
			Cache[ResourceID]["TS"] = int(time.time())

			if resource_type == "AS":
				if data["data"]["announced"]:
					Cache[ResourceID]["Description"] = "<span class=\"resource_details\">AS%s</span> - %s" % ( resource, data["data"]["holder"] )
				else:
					Cache[ResourceID]["Description"] = "AS%s - not announced" % resource

			elif resource_type == "IP":
				Cache[ResourceID]["Description"] = "<span class=\"resource_details\">%s</span>" % ( resource )

				try:
					Reverse = socket.getfqdn( resource )
					if Reverse != resource:
						Cache[ResourceID]["Description"] += " <span class=\"resource_details\">%s</span>" % Reverse
				except:
					pass

				if "data" in data:
					if data["data"]["resource"] != resource:
						Cache[ResourceID]["Description"] += "\nannounced as part of <span class=\"resource_details\">%s</span>" % data["data"]["resource"]

					if "asns" in data["data"]:
						if data["data"]["asns"] != []:
							Cache[ResourceID]["Description"] += "\nannounced by <span class=\"resource_details\">AS%d</span> - %s" % ( data["data"]["asns"][0]["asn"], data["data"]["asns"][0]["holder"] )

							ASResourceID = "AS-%s" % data["data"]["asns"][0]["asn"]
							Cache[ASResourceID] = {}
							Cache[ASResourceID]["TS"] = int(time.time())
							Cache[ASResourceID]["Description"] = "AS%d - %s" % ( data["data"]["asns"][0]["asn"], data["data"]["asns"][0]["holder"] )

					WhoisResult = GetDetails( "WHOIS", resource )

					if not "error" in WhoisResult:
						if WhoisResult["Description"]:
							Cache[ResourceID]["Description"] += "\n"
							Cache[ResourceID]["Description"] += WhoisResult["Description"]

			elif resource_type == "WHOIS":
				Cache[ResourceID]["Description"] = ""

				if "data" in data:
					if "records" in data["data"]:
						for Record in data["data"]["records"]:
							for Entry in Record:
								if Entry["key"] in [ "inetnum", "inet6num", "netname" ]:
									Cache[ResourceID]["Description"] += "%s: <span class=\"resource_details\">%s</span>\n" % ( Entry["key"], Entry["value"] )
								elif Entry["key"] in [ "descr" ]:
									Cache[ResourceID]["Description"] += "%s: %s\n" % ( Entry["key"], Entry["value"] )
				
	else:
		if "message" in data:
			return { "error": "Can't get resource details: %s" % data["message"] }
		else:
			return { "error": "Can't get resource details" }

	return Cache[ResourceID]

def InvalidatingCache( Query ):
	Error = NormalizeQuery( Query )

	if not Error is None:
		return { "error": Error }

	if CacheFileExists( Query ):
		Error, CacheData = GetCacheIfValid( Query )

		if not Error is None:
			return { "error": Error }

		if CacheData == {}:
			return { "invalidatingcache": True }

	return { "invalidatingcache": False }

def GetChartData( Graph ):
	Error = None
	Output = {}

	Query = Graph["Query"]
	Start = datetime.datetime.fromtimestamp( Graph["Start"] )
	Stop = datetime.datetime.fromtimestamp( Graph["Stop"] )

	Error = NormalizeQuery( Query )

	if not Error is None:
		return { "error": Error }

	if not "ColName" in Graph:
		Graph["ColName"] = Query["OrderBy"]["ColName"]

	(Error, Results) = ProcessFiles( Start, Stop, Query )

	if not Error is None:
		return { "error": Error }

	Output["Graph"] = Graph
	Output["Data"] = Results

	return Output

def SaveGraph( Graph ):
	if "Query" in Graph:
		Error = NormalizeQuery( Graph["Query"] )

		if not Error is None:
			return { "error": Error }
	else:
		return { "error": "Missing query" }

	Graphs = LoadGraphs()

	if "error" in Graphs:
		return { "error": Graphs["error"] }

	if not "ID" in Graph:
		Graph["ID"] = None
	if not Graph["ID"]:
		Graph["ID"] = str( uuid.uuid4() )

	if Graph["ID"] in Graphs:
		del Graphs[ Graph["ID"] ]

	Graph["LastUpdated"] = int(time.time())

	Graphs[ Graph["ID"] ] = Graph

	Result = SaveGraphs( Graphs )

	if "error" in Result:
		return { "error": Result["error"] }

	return { "ID": Graph["ID"] }

def SaveGraphs( Graphs ):
	try:
		with open( "%s/%s" % ( VAR_DIR, GRAPHS_FILENAME ), 'w' ) as OutputJSONFile:
			json.dump( Graphs, OutputJSONFile, sort_keys=True )
	except:
		return { "error": "Can't write graphs to file" }

	return {}

def LoadGraphs():
	Graphs = {}

	if os.path.isfile( "%s/%s" % ( VAR_DIR, GRAPHS_FILENAME ) ):
		try:
			JSON_Data = open( "%s/%s" % ( VAR_DIR, GRAPHS_FILENAME ) )
			Graphs = json.load(JSON_Data)
			JSON_Data.close()
		except:
			return { "error": "Can't read graphs" }

	return Graphs

def RemoveGraph( GraphID ):
	Graphs = LoadGraphs()

	if "error" in Graphs:
		return { "error": Graphs["error"] }

	if GraphID in Graphs:
		del Graphs[ GraphID ]

	Result = SaveGraphs( Graphs )

	if "error" in Result:
		return { "error": Result["error"] }

	return {}

# this function returns an HTML page
def GetNfDumpFilterMan():
	try:
		Man = subprocess.Popen( [ "man", NFDUMP_PATH ], stdout=subprocess.PIPE, stderr=subprocess.PIPE )
	except:
		try:
			Man = subprocess.Popen( [ "man", "nfdump" ], stdout=subprocess.PIPE, stderr=subprocess.PIPE )
		except:
			Error = "Error while executing man nfdump: %s" % GetException()
			return Error

	try:
		(Output, Error) = Man.communicate()
		Man.wait()
	except:
		Error = "Error while reading man nfdump output: %s" % GetException()
		return Error

	if Error:
		return Error

	Match = re.search( r'^FILTER.+', Output, re.MULTILINE|re.DOTALL )
	if Match:
		Output = Match.group(0)
		Match = re.search( '(.+(\n|\r\n))EXAMPLES', Output, re.MULTILINE|re.DOTALL )

		if Match:
			Output = Match.group(1)

	return """<!DOCTYPE html>
<html>
<head>
<title>NfDump syntax man page</title>
</head>
<body>
<p><b>NfDump syntax man page</b></p>
<p>The %%filters%% macro will be expanded with 
the local FlowGraph <em>var</em> directory, 
where files containing NfDump filters can be 
saved for later usage with the @include statement.</p>
<pre style="background-color: #EFEFEF; font-family: monospace,monospace; font-size:1em;">%s</pre>
</body>
</html>""" % Output

def GetConfigData():
	Output = {
		"NFDUMP_FIELDS": NFDUMP_FIELDS,
		"NETFLOW_SOURCESID": NETFLOW_SOURCESID
	}

	return Output

