# --------------------------------------------------------------
# DO NOT EDIT BELOW OF THIS UNLESS REALLY SURE
NFDUMP_FIELDS = []

NFDUMP_FIELDS.append( { "ID": "pr",     "AggrType_A": "proto",          "AggrType_s": "proto",          "Name": "Protocol" } )
NFDUMP_FIELDS.append( { "ID": "exp",    "AggrType_A": None,             "AggrType_s": "sysid",          "Name": "Exporter ID" } )
NFDUMP_FIELDS.append( { "ID": "sa",     "AggrType_A": "srcip",          "AggrType_s": "srcip",          "Name": "Source Address",               "Details": "IP" } )
NFDUMP_FIELDS.append( { "ID": "da",     "AggrType_A": "dstip",          "AggrType_s": "dstip",          "Name": "Destination Address",          "Details": "IP" } )
NFDUMP_FIELDS.append( { "ID": "sp",     "AggrType_A": "srcport",        "AggrType_s": "srcport",        "Name": "Source Port" } )
NFDUMP_FIELDS.append( { "ID": "dp",     "AggrType_A": "dstport",        "AggrType_s": "dstport",        "Name": "Destination Port" } )
NFDUMP_FIELDS.append( { "ID": "nh",     "AggrType_A": "next",           "AggrType_s": "nhip",           "Name": "Next-hop IP Address",          "Details": "IP" } )
NFDUMP_FIELDS.append( { "ID": "nhb",    "AggrType_A": "bgpnext",        "AggrType_s": "nhbip",          "Name": "BGP Next-hop IP Address",      "Details": "IP" } )
NFDUMP_FIELDS.append( { "ID": "ra",     "AggrType_A": "router",         "AggrType_s": "router",         "Name": "Router IP Address",            "Details": "IP" } )
NFDUMP_FIELDS.append( { "ID": "sas",    "AggrType_A": "srcas",          "AggrType_s": "srcas",          "Name": "Source AS",                    "Details": "AS" } )
NFDUMP_FIELDS.append( { "ID": "das",    "AggrType_A": "dstas",          "AggrType_s": "dstas",          "Name": "Destination AS",               "Details": "AS" } )
NFDUMP_FIELDS.append( { "ID": "nas",    "AggrType_A": "nextas",         "AggrType_s": None,             "Name": "Next AS",                      "Details": "AS" } )
NFDUMP_FIELDS.append( { "ID": "pas",    "AggrType_A": "prevas",         "AggrType_s": None,             "Name": "Previous AS",                  "Details": "AS" } )
NFDUMP_FIELDS.append( { "ID": "in",     "AggrType_A": "inif",           "AggrType_s": "inif",           "Name": "Input Interface num" } )
NFDUMP_FIELDS.append( { "ID": "out",    "AggrType_A": "outif",          "AggrType_s": "outif",          "Name": "Output Interface num" } )

NFDUMP_FIELDS.append( { "ID": "sn4",    "AggrType_A": "srcip4/%s",      "AggrType_s": None,             "Name": "IPv4 source network",          "Details": "IP",
			"OutputField": "sa", "ArgRequired": True } )

NFDUMP_FIELDS.append( { "ID": "sn6",    "AggrType_A": "srcip6/%s",      "AggrType_s": None,             "Name": "IPv6 source network",          "Details": "IP",
			"OutputField": "sa", "ArgRequired": True } )

NFDUMP_FIELDS.append( { "ID": "dn4",    "AggrType_A": "dstip4/%s",      "AggrType_s": None,             "Name": "IPv4 destination network",     "Details": "IP",
			"OutputField": "da", "ArgRequired": True } )

NFDUMP_FIELDS.append( { "ID": "dn6",    "AggrType_A": "dstip6/%s",      "AggrType_s": None,             "Name": "IPv6 destination network",     "Details": "IP",
			"OutputField": "da", "ArgRequired": True } )

