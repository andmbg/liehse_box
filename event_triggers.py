import logging
from config import record
import blinkt
import threading
import time

blinkt.set_brightness(0.1)

def on_entry():
	logging.debug("on_entry() record length: %s" % record.len())
	
	test_button_press(record) # on any button or chord
	test_full_chord(record) # on red + green + white



#  Tests:
# --------

def test_button_press(record):
	logging.debug("test_button_press(record = %s)" % record)
	threading.Thread(target = led_redtick).start()
		


def test_full_chord(record):
	last = record.last()
	logging.debug("test_full_chord: last = %s" % last)
	if last.red and last.green and last.white:
		logging.debug("test_full_chord: red=%i, green=%i, white=%i" % \
			(last.red, last.green, last.white))
		threading.Thread(target = led_bluenote, args = (1,)).start()
		
	
	


#  Outcomes:
# -----------

def led_bluenote(duration = 1):
	logging.debug("led_bluenote(%f)" % duration)
	time.sleep(0.1)
	blinkt.set_pixel(4, 0,0,255)
	blinkt.show()
	time.sleep(duration)
	blinkt.set_pixel(4, 0,0,0)
	blinkt.show()



def led_redtick(duration = 0.1):
	logging.debug("led_redtick()")
	blinkt.set_pixel(0, 255,0,0)
	blinkt.show()
	time.sleep(duration)
	blinkt.set_pixel(0, 0,0,0)
	blinkt.show()
	
