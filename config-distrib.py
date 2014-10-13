# =================================================================
#
#		   Rename this file to config.py,
#		then edit it to configure FlowGraph.
#	When done, set CONFIG_DONE at the end of this file to True.
#
# =================================================================

import os
from nffields import *

DEBUG		= True	# True or False - case sensitive!

BASE_DIR	= os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------
# Where cache, graphs and filters will be stored.
# No trailing slash. Default: <BASE_DIR>/var
VAR_DIR			= "%s/var" % BASE_DIR

GRAPHS_FILENAME		= "graphs.json"

# --------------------------------------------------------------
# Log file path, automatically rotated every 1MB with 3 backup.
# Default: <VAR_DIR>/flowgraph.log
LOG_FILEPATH		= "%s/flowgraph.log" % VAR_DIR

# --------------------------------------------------------------
# Path to the nfdump binary.
NFDUMP_PATH		= "nfdump"

# --------------------------------------------------------------
# NetFlow data path
# -----------------
#
# The NETFLOW_* variables will be used to build the netflow 
# files path that will be passed to nfdump in the -M and -r 
# arguments:
#
# -M <NETFLOW_DATA_DIR>/<NETFLOW_SOURCESID_1>:<NETFLOW_SOURCESID_n>
#
# -r <NETFLOW_FILENAME_FORMAT>
#
# These variables are strongly related to the layout of files 
# and directories used by the collector daemon (nfcapd).
#
# See description of -I, -l, -n and -t options on 'man nfcapd'.
#
# Example:
#
# NETFLOW_DATA_DIR = "/netflow"
# NETFLOW_SOURCESID = [ "CoreRouter1", "CoreRouter2", "Border1" ]
# NETFLOW_FILENAME_FORMAT = "%Y/%m/%d/nfcapd.%Y%m%d%H%M"
#
# A graph that uses data from all the sources for a query 
# that starts on 1st October 2014 at 9:05 AM will use the
# following nfdump arguments:
#
# -M will be /netflow/CoreRouter1:CoreRouter2:Border1
# -r will be 2014/10/01/nfcapd.201410010905

# --------------------------------------------------------------
# NetFlow data base dir. No trailing slash.
#
# See "NetFlow data path" section of this file for more details.
NETFLOW_DATA_DIR	= "/netflow"

# --------------------------------------------------------------
# List of netflow data sources: graphs will be configured to use 
# one or more sources from this list.
# SourcesID correspond to the nfcapd Ident (see nfcapd options
# -I and -n).
#
# See "NetFlow data path" section of this file for more details.
#
# Example:
# NETFLOW_SOURCESID = [ "CoreRouter1", "CoreRouter2", "Border1" ]
NETFLOW_SOURCESID	= [ ]

# --------------------------------------------------------------
# Date time format from
# https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
#
# See "NetFlow data path" section of this file for more details.
#
# commonly used:
#	%Y	Year with century as a decimal number.
#	%m	Month as a zero-padded decimal number.
#	%d	Day of the month as a zero-padded decimal number.
#	%H	Hour (24-hour clock) as a zero-padded decimal number.
#	%M	Minute as a zero-padded decimal number.
NETFLOW_FILENAME_FORMAT	= "%Y/%m/%d/nfcapd.%Y%m%d%H%M"

# --------------------------------------------------------------
# Rotation interval of netflow data files (in seconds).
# See nfcapd -t option.
#
# See "NetFlow data path" section of this file for more details.
NETFLOW_INTERVAL	= 300		# seconds (default: 5 min)

# --------------------------------------------------------------
# How many days to keep cached netflow data gathered by scheduler
# (can also be configured for every graph where scheduler is
# enabled).
MAX_CACHE_NFDATA	= 7		# days (default: 7 days)

# --------------------------------------------------------------
# How long to keep details about resources (ASes, IP addresses,
# whois output).
# Resource cache will be kept in memory and will be lost at 
# every application reload. Expressed in seconds.
MAX_CACHE_RES_DETAILS	= 604800	# seconds (default: 1 week)

# --------------------------------------------------------------
# Used by scheduler to send error notifications.
SEND_ERROR_VIA_EMAIL	= False	# True or False - case sensitive!
SEND_ERROR_FROM_EMAIL	= "your_address@your_domain.tld"
SEND_ERROR_TO_EMAIL	= "your_address@your_domain.tld"
SEND_ERROR_SMTP		= "smtp.yourserver.tld"
SEND_ERROR_SMTP_PORT	= 25

# --------------------------------------------------------------
# Automatically check for updates.
# Enable a client-side script that checks for new releases
# using GitHub API.
CHECKUPDATES_ENABLE	= True	# True or False - case sensitive!
CHECKUPDATES_INTERVAL	= 7	# days
CHECKUPDATES_PRERELEASE = False	# True or False - case sensitive!

# --------------------------------------------------------------
# Configuration completed?
# Set the following variable to True once you completed your
# configuration.
CONFIG_DONE		= False	# set to True when done

