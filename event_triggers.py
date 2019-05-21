import logging
from config import record

def on_entry():
	logging.debug("on_entry() record length: %s" % record.len())
	
