from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import RPi.GPIO as GPIO
import time
import collections
import buttons
import random
import threading
import logging
import pprint
import blinkt
from math import sin, pi
import event_triggers
from config import record

# B. is for direct mechanical debouncing, replacing the insufficient
# built-in mechanism. D. is for dealing with parasitic keylogs.
BOUNCETIME = 0.2 # seconds
DELAY = 0.2



logging.basicConfig(level = logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


# setup pins to listen to:
pins = {
    14: {'name': 'red'},
    15: {'name': 'green'},
    18: {'name': 'white'},
    25: {'name': 'black'}
    }
    
# How RPi numbers GPIO pins. Consider BOARD as alternative:
GPIO.setmode(GPIO.BCM)

for pin in pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)



start_time = time.time()
def timestamp(): return time.time() - start_time



# setup single logs for debouncing (these don't end up in the result):
red_debouncelog   = [("red", timestamp(), 0)]
green_debouncelog = [("green", timestamp(), 0)]
white_debouncelog = [("white", timestamp(), 0)]
black_debouncelog = [("black", timestamp(), 0)]



# inbox filters parasitic keylogs, returns chords
inbox = { 'red': 0,
          'green': 0,
          'white': 0,
          'black': 0 }

# only the last button press's Timer should be relevant:
listener = 0

# our log:
#record = buttons.Record()
#logging.debug("variable 'record' set up as %s" % type(record))



def schedule_set(logentry, delay = 0.2):
    global inbox
    global listener
    timerID = random.random()
    slot = logentry[0]
    inbox[slot] = logentry[2]
    listener = timerID
    threading.Timer(delay, send_chord, [inbox, timerID]).start()

# form Record_entry from inbox chord, add to the record, check record
# to trigger events (success, others):
def send_chord(chord, timerID):
    global record
    if listener == timerID:
        newentry = buttons.Record_entry(timestamp(), chord)
        logging.debug("send_chord(): %s" % newentry.string())
        event_triggers.on_entry(newentry) # check for event triggers
               


# return clean single button events. Clean means no bouncing.
def button_log(channel, log, this_time, this_state):
    # get time & on/off of the last entry:
    last_time, last_state = log[-1][1:3]
    button = {14: "red",
              15: "green",
              18: "white",
              25: "black"}[channel]
    logentry = None

    # is this state different? log it:
    if this_state != last_state:
        logentry = (button, this_time, this_state)

    # this state is the same? if the interval is > BOUNCETIME,
    # it's a 1 glued right before a 0 -- log it as 0, likely
    # ignore the actual 0, leading to a clean button release:
    if this_state == last_state and \
       this_time - last_time > BOUNCETIME:
            logentry = (button, this_time, 1 - this_state)
    return(logentry)



def red_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    state = 1 - GPIO.input(channel)
    logging.debug("( ,  ,  , %i)" % state)
    # returns (button, time, state):
    logentry = button_log(channel, red_debouncelog, timestamp(), state)
    if logentry == None: return
    
    red_debouncelog.append(logentry)
    schedule_set(logentry, delay = DELAY)
    
            
def green_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    state = 1 - GPIO.input(channel)
    print("( ,  , %i,  )" % state)
    # returns (button, time, state):
    logentry = button_log(channel,
                          green_debouncelog,
                          timestamp(),
                          1 - GPIO.input(channel))
    
    if logentry == None: return

    green_debouncelog.append(logentry)
    schedule_set(logentry, delay = DELAY)

def white_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    state = 1 - GPIO.input(channel)
    print("( , %i,  ,  )" % state)
    # returns (button, time, state):
    logentry = button_log(channel,
                          white_debouncelog,
                          timestamp(),
                          1 - GPIO.input(channel))
    if logentry == None: return

    white_debouncelog.append(logentry)
    schedule_set(logentry, delay = DELAY)

def black_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    state = 1 - GPIO.input(channel)

    if state == 0: return

    global record
    pprint.pprint(record.string())






    


# Set up listeners on GPIOs:
GPIO.add_event_detect(14,
                      GPIO.BOTH,
                      bouncetime = 20,
                      callback = red_callback)

GPIO.add_event_detect(15,
                      GPIO.BOTH,
                      bouncetime = 20,
                      callback = green_callback)

GPIO.add_event_detect(18,
                      GPIO.BOTH,
                      bouncetime = 20,
                      callback = white_callback)

GPIO.add_event_detect(25,
                      GPIO.BOTH,
                      bouncetime = 20,
                      callback = black_callback)



@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")
def on_connect():
    payload = dict(data = "Connected")
    emit("log", payload, broadcast = True)


if __name__ == "__main__":
    socketio.run(app)

