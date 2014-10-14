# Copyright (c) 2014 Pier Carlo Chiodi - http://www.pierky.com
# Licensed under The MIT License (MIT) - http://opensource.org/licenses/MIT

from flask import Flask, request, jsonify, render_template
from core import *
from websupport import *
import time

flowgraphapp = Flask(__name__)

@flowgraphapp.route('/')
def main():
	if CONFIG_DONE:
		return render_template( "main.html",
			CURRENT_RELEASE=CURRENT_RELEASE,
			CHECKUPDATES_ENABLE=CHECKUPDATES_ENABLE,
			CHECKUPDATES_INTERVAL=CHECKUPDATES_INTERVAL,
			CHECKUPDATES_PRERELEASE=CHECKUPDATES_PRERELEASE
		)
	else:
		return "<html><body><b>Configuration incomplete</b>. Edit conf.py and set CONFIG_DONE = True when done.</body></html>"

@flowgraphapp.route('/getConfig')
def getConfig():
	return jsonify( GetConfigData() )

@flowgraphapp.route('/invalidatingCache', methods=["POST"])
def invalidatingCache():
	Query = request.json['Query']
	return jsonify( InvalidatingCache( Query ) )

@flowgraphapp.route('/saveGraph', methods=["POST"])
def saveGraph():
	Graph = request.json['Graph']
	return jsonify( SaveGraph( Graph ) )

@flowgraphapp.route('/getGraphs')
def getGraphs():
	return jsonify( LoadGraphs() )

@flowgraphapp.route('/deleteGraph', methods=["GET"])
def deleteGraph():
	GraphID = request.args['GraphID'];
	return jsonify( RemoveGraph( GraphID ) );

@flowgraphapp.route('/getDetails', methods=["GET"])
def getDetails():
	resource_type = request.args['resource_type']
	resource = request.args['resource']
	return jsonify( GetDetails( resource_type, resource ) )

@flowgraphapp.route('/getData', methods=["POST"])
def getData():
	Graph = request.json['Graph']
	RequestID = request.json['RequestID']
	return jsonify( GetChartData( Graph, RequestID ) )

@flowgraphapp.route('/getRequestProgress', methods=["GET"])
def getRequestProgress():
	RequestID = request.args['request_id']
	return jsonify( GetRequestProgress( RequestID ) )

@flowgraphapp.route('/cancelRequest', methods=["GET"])
def cancelRequest():
	RequestID = request.args['request_id']
	return jsonify( CancelRequest( RequestID ) )

@flowgraphapp.route('/manNfDumpFilter')
def manNfDumpFilter():
	return GetNfDumpFilterMan()

if __name__ == '__main__':
	SetupLogging()

	flowgraphapp.debug = DEBUG
	flowgraphapp.run(host="0.0.0.0",threaded=True)

