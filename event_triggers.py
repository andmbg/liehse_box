import logging
from config import record
import blinkt
import threading
import time

blinkt.set_brightness(0.1)



# whenever a new Record_entry is sent to record:
def on_entry(newentry):
	#logger.warning("on_entry() record length: %s | newentry: %s" % (record.len(), newentry.string()))
	
	test_button_press(newentry) # on any button or chord
	test_full_chord(newentry) # on red + green + white



#  Tests:
# --------

def test_button_press(newentry):
	global record
	# was it just a below-threshold short press [0,0,0,0]? Remove from log.
	lastentry = record.last()
	logger.debug("(test_button_press) last entry: %s | newentry: %s" % (lastentry, newentry.is_empty()))
		
	if newentry.is_empty():
		if lastentry == None or lastentry.is_empty(): return
	
	record.add_entry(newentry)
	threading.Thread(target = led_redtick).start()
		


def test_full_chord(newentry):
	#logger.debug("test_full_chord: last = %s" % newentry.string())
	if newentry.red and newentry.green and newentry.white:
		#logger.debug("test_full_chord: red=%i, green=%i, white=%i" % \
		#	(newentry.red, newentry.green, newentry.white))
		threading.Thread(target = led_bluenote, args = (1,)).start()
		
	
	


#  Outcomes:
# -----------

def led_bluenote(duration = 1):
	#logger.debug("led_bluenote(%f)" % duration)
	time.sleep(0.1)
	blinkt.set_pixel(4, 0,0,255)
	blinkt.show()
	time.sleep(duration)
	blinkt.set_pixel(4, 0,0,0)
	blinkt.show()



def led_redtick(duration = 0.1):
	#logger.debug("led_redtick()")
	blinkt.set_pixel(0, 255,0,0)
	blinkt.show()
	time.sleep(duration)
	blinkt.set_pixel(0, 0,0,0)
	blinkt.show()
	
