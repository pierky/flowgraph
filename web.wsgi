BASE_DIR = "/usr/local/src/flowgraph"

import sys
sys.path.insert( 0, BASE_DIR )

from web import flowgraphapp as application
from core import SetupLogging
from config import *

SetupLogging()
application.debug = DEBUG

