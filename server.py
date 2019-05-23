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
from os import system


# some preliminary settings


# B. is for direct mechanical debouncing, replacing the insufficient
# built-in mechanism. D. is for dealing with parasitic keylogs.
BOUNCETIME = 0.2 # seconds
DELAY = 0.2
DEBUGLEVEL = logging.INFO

record = buttons.Record()
listener = 0
target_chord = None # anything outside 1:15
checklist = {9: None, 10: None, 12: None}

def new_participant():
    # setup logging once per starting the box:
    session_date = time.localtime()
    global sessionid
    sessionid = "%d%0.2d%0.2d_[%s]_%0.2d%0.2d%0.2d" % ( \
        session_date.tm_year, session_date.tm_mon, session_date.tm_mday, \
        ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][session_date.tm_wday],
        session_date.tm_hour, session_date.tm_min, session_date.tm_sec)
    global record
    record = buttons.Record()
    global start_time
    start_time = time.time()
    
    # setup single logs for debouncing (these don't end up in the result):
    global black_debouncelog
    global green_debouncelog
    global red_debouncelog
    global white_debouncelog
    black_debouncelog = [("black", timestamp(), 0)]
    green_debouncelog = [("green", timestamp(), 0)]
    red_debouncelog   = [("red", timestamp(), 0)]
    white_debouncelog = [("white", timestamp(), 0)]

    # inbox filters parasitic keylogs, returns chords
    global inbox
    inbox = { 'red': 0,
              'green': 0,
              'white': 0,
              'black': 0 }
    global listener
    listener = 0
    global target_chord
    target_chord = None
    global checklist
    checklist = {9: None, 10: None, 12: None}
   

    
    
def timestamp(): return time.time() - start_time

    


def schedule_set(logentry, delay = 0.2):
    global inbox
    global listener
    timerID = random.random()
    slot = logentry[0]
    inbox[slot] = logentry[2]
    listener = timerID
    threading.Timer(delay, send_chord, [inbox, timerID]).start()

# form Record_entry from inbox chord. Check if it should trigger events,
# then add to record.
def send_chord(chord, timerID):
    global record
    if listener == timerID:
        newentry = buttons.Record_entry(timestamp(), chord)
        logging.debug("send_chord(): %s" % newentry.string())
        on_entry(newentry) # check for event triggers
               


# return clean single button events. Clean means no bouncing.
def button_log(channel, log, this_time, this_state):
    # get time & on/off of the last entry:
    last_time, last_state = log[-1][1:3]
    button = {14: "black",
              15: "green",
              18: "red",
              25: "white"}[channel]
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


#### diagnostic function of black button for debugging
#def black_callback(channel):
#    # hack against bouncing:
#    time.sleep(.01)
#    state = 1 - GPIO.input(channel)
#
#    if state == 0: return
#
#    global record
#    pprint.pprint(record.string())
####

def black_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    state = 1 - GPIO.input(channel)
    logging.debug("(%i,  ,  ,  )" % state)
    # returns (button, time, state):
    logentry = button_log(channel,
                          black_debouncelog,
                          timestamp(),
                          1 - GPIO.input(channel))
    
    if logentry == None: return

    black_debouncelog.append(logentry)
    schedule_set(logentry, delay = DELAY)

def green_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    state = 1 - GPIO.input(channel)
    logging.debug("( , %i,  ,  )" % state)
    # returns (button, time, state):
    logentry = button_log(channel,
                          green_debouncelog,
                          timestamp(),
                          1 - GPIO.input(channel))
    
    if logentry == None: return

    green_debouncelog.append(logentry)
    schedule_set(logentry, delay = DELAY)

def red_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    state = 1 - GPIO.input(channel)
    logging.debug("( ,  , %i,  )" % state)
    # returns (button, time, state):
    logentry = button_log(channel, red_debouncelog, timestamp(), state)
    if logentry == None: return
    
    red_debouncelog.append(logentry)
    schedule_set(logentry, delay = DELAY)

def white_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    state = 1 - GPIO.input(channel)
    logging.debug("( ,  ,  , %i)" % state)
    # returns (button, time, state):
    logentry = button_log(channel,
                          white_debouncelog,
                          timestamp(),
                          1 - GPIO.input(channel))
    if logentry == None: return

    white_debouncelog.append(logentry)
    schedule_set(logentry, delay = DELAY)







# Handling newly recorded entries
# whenever a new Record_entry is sent to record:
def on_entry(newentry):
    logging.debug("on_entry() record length: %s | newentry: %s" % (record.len(), newentry.string()))
    
    # on any button or chord above delay threshold
    # THIS IS WHERE WE LOG CHORDS!
    test_button_press(newentry)

    test_first(newentry)
    test_flush_record(newentry)
    test_new_session(newentry)
    test_target_chord(newentry, interval = 5)








# ===============================================================
#  Tests:
# ---------------------------------------------------------------

def test_button_press(newentry):
    # was it just a below-threshold short press [0,0,0,0]? Remove from log.
    lastentry = record.last()
    logging.debug("(test_button_press) last entry: %s | newentry: %s" % (lastentry, newentry.is_empty()))
        
    if newentry.is_empty():
        if lastentry == None or lastentry.is_empty(): return
    
    record.add_entry(newentry)
    logging.debug("button pressed: %s" % newentry.string())
    #threading.Thread(target = led_redtick).start()

def test_first(newentry):
    global start_time
    if record.len() == 1:
        start_time = time.time()
        record.entries[0].timestamp = start_time
        logging.debug("registered first press in session")

def test_flush_record(newentry):
    global record
    global sessionid
    if record.testcode([9,11,9,13,9,0]):
        record.chop(6)
        with open("records/%s.record" % sessionid, 'w') as f:
            f.write(record.csv())
        logging.info("wrote record to records/%s.record" % sessionid)
        threading.Thread(target = led_matrix, args = ("led patterns/knight",255,0,0,2)).start()

def test_new_session(newentry):
    global record
    if record.testcode([6,0,6,0]):
        logging.info("starting new session")
        threading.Thread(target = led_matrix, args = ("led patterns/police",0,0,255,4)).start()
        new_participant()
        

# if interval (30s?) has elapsed and newentry contains white, success.
def test_target_chord(newentry, interval = 30):
    global record
    global target_chord
    global checklist
    print("target: %s  |  entry: %s  |  time: %f" % (target_chord, newentry.code(), newentry.timestamp))
    print(newentry.timestamp)
    
    if target_chord in checklist.keys():
        if newentry.code() == target_chord:
            print("Success")
            return
    
    else:
        # interval up:
        if newentry.timestamp > interval:
            if newentry.code() in checklist.keys():
                if sum([ i == None for i in checklist.values() ]) == 0:
                    # oldest
                    target_chord = [ i[0] for i in checklist.items() if i[1] == min(checklist.items()) ][0]
                    print("Set target_chord to oldest; Success!")
                else:
                    #sample from untested
                    target_chord = random.sample([i[0] for i in checklist.items() if i[1] == None ], 1)[0]

        # interval not up:
        elif newentry.code() in checklist.keys():
            checklist[newentry.code()] = newentry.timestamp
            print("interval running, updating checklist... %s" % checklist)
            
    
    


#  LED actions:
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
    
    

def led_matrix(infile, r,g,b, times):
    contents = open(infile).read()
    mat = [ item.split() for item in contents.split('\n')[:-1] ]
    
    for i in range(times):
        for line in mat:
            blinkt.clear()
            for column in range(len(line)):
                val = int(line[column])
                blinkt.set_pixel(column, r*val,g*val,b*val)
            blinkt.show()
            time.sleep(0.01)
        blinkt.clear()
    blinkt.show()


                
            
        







# =====================================================================
#  Beginning of app:
# ---------------------------------------------------------------------



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)



# How RPi numbers GPIO pins. Consider BOARD as alternative:
GPIO.setmode(GPIO.BCM)

pins = {
    14: {'name': 'black'},
    15: {'name': 'green'},
    18: {'name': 'red'},
    25: {'name': 'white'}
    }
for pin in pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

# Set up listeners on GPIOs:
GPIO.add_event_detect(14,
                      GPIO.BOTH,
                      bouncetime = 20,
                      callback = black_callback)

GPIO.add_event_detect(15,
                      GPIO.BOTH,
                      bouncetime = 20,
                      callback = green_callback)

GPIO.add_event_detect(18,
                      GPIO.BOTH,
                      bouncetime = 20,
                      callback = red_callback)

GPIO.add_event_detect(25,
                      GPIO.BOTH,
                      bouncetime = 20,
                      callback = white_callback)




new_participant()

logfilename = "log/%s.log" % sessionid
logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s", level=DEBUGLEVEL,
                        filename=logfilename, filemode='w')
logging.info("Log %s start.\n-----------------------" % sessionid)


@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")
def on_connect():
    payload = dict(data = "Connected")
    emit("log", payload, broadcast = True)

if __name__ == "__main__":
    socketio.run(app)

