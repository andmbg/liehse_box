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
DEBUGLEVEL = logging.DEBUG
blinkt.set_brightness(0.2)

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

    global session_start_time
    session_start_time = time.time()
    global trial_start_time
    trial_start_time = session_start_time
    
    # setup single logs for debouncing (these don't end up in the result):
    global black_debouncelog
    global green_debouncelog
    global red_debouncelog
    global white_debouncelog
    black_debouncelog = [("black", timestamp("session"), 0)]
    green_debouncelog = [("green", timestamp("session"), 0)]
    red_debouncelog   = [("red", timestamp("session"), 0)]
    white_debouncelog = [("white", timestamp("session"), 0)]

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
    
    print("Starting session ", sessionid)
   

    
    
def timestamp(context):
    global session_start_time
    assert context in ["session", "trial"], "Call timestamp() with argument context = 'session' or 'trial'."
    if context == "session":
        return time.time() - session_start_time
    if context == "trial":
        return time.time() - trial_start_time
    

    


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
        newentry = buttons.Record_entry(timestamp("trial"), chord, target_chord)
        logging.debug("%s -> send_chord()" % newentry.string())
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
    ts = timestamp("trial")
    state = 1 - GPIO.input(channel)
    logging.debug("%f (%i,  ,  ,  )" % (ts, state))
    # returns (button, time, state):
    logentry = button_log(channel, black_debouncelog, ts, state)
    if logentry == None: return

    black_debouncelog.append(logentry)
    schedule_set(logentry, delay = DELAY)

def green_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    ts = timestamp("trial")
    state = 1 - GPIO.input(channel)
    logging.debug("%f ( , %i,  ,  )" % (ts, state))
    # returns (button, time, state):
    logentry = button_log(channel, green_debouncelog, ts, state)
    if logentry == None: return

    green_debouncelog.append(logentry)
    schedule_set(logentry, delay = DELAY)

def red_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    ts = timestamp("trial")
    state = 1 - GPIO.input(channel)
    logging.debug("%f ( ,  , %i,  )" % (ts, state))
    # returns (button, time, state):
    logentry = button_log(channel, red_debouncelog, ts, state)
    if logentry == None: return
    
    red_debouncelog.append(logentry)
    schedule_set(logentry, delay = DELAY)

def white_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    ts = timestamp("trial")
    state = 1 - GPIO.input(channel)
    logging.debug("%f ( ,  ,  , %i)" % (ts, state))
    # returns (button, time, state):
    logentry = button_log(channel, white_debouncelog, ts, state)
    if logentry == None: return

    white_debouncelog.append(logentry)
    schedule_set(logentry, delay = DELAY)







# Handling newly recorded entries
# whenever a new Record_entry is sent to record:
def on_entry(newentry):
    logging.debug("%s -> on_entry() | record length: %s" % (newentry.string(), record.len()))
    
    # on any button or chord above delay threshold
    test_button_press(newentry)  # THIS IS WHERE WE LOG CHORDS!


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

    if newentry.is_empty():
        if lastentry == None or lastentry.is_empty():
            logging.debug("%f keypress too short, not logged" % newentry.timestamp)
            return

    record.add_entry(newentry)
    logging.debug("%s -> added to record" % newentry.string())

def test_first(newentry):
    global session_start_time
    global trial_start_time
    if record.len() == 1: # if this is the first entry
        # set the trial timer for interval; needs to be different from session
        # timer, as time passes between box reset and trial start
        trial_start_time = time.time()
        record.entries[0].timestamp = timestamp("trial")
        logging.debug("%f this has been the first logged press in this trial" % newentry.timestamp)

def test_flush_record(newentry):
    global record
    global sessionid
    if record.testcode([9,11,9,13,9,0]):
        record.chop(6)
        csv_record = "timecode, black, green, red, white, target_chord\n"
        csv_record += record.csv()
        with open("records/%s.record" % sessionid, 'w') as f:
            f.write(csv_record)
        logging.info("wrote record to records/%s.record" % sessionid)
        threading.Thread(target = led_matrix, args = ("led patterns/knight",255,0,0,2)).start()

def test_new_session(newentry):
    global record
    if record.testcode([6,0,6,0]):
        logging.info("starting new session")
        threading.Thread(target = led_matrix, args = ("led patterns/police",0,0,255,1)).start()
        new_participant()
        

# if interval (30s?) has elapsed and newentry contains white, success.
def test_target_chord(newentry, interval = 30):
    global record
    global target_chord
    global checklist
    logging.debug("%f newentry code: %s | target code: %s" % (newentry.timestamp, newentry.code(), target_chord))
    
    if target_chord in checklist.keys():
        if newentry.code() == target_chord:
            logging.debug("test_target_chord: interval elapsed, newentry (%s) == target_chord (%s)" % (newentry.code(), target_chord))
            logging.info("SUCCESS")
            threading.Thread(target = led_success).start()
            return
    
    else:
        # interval up:
        if newentry.timestamp > interval:
            if newentry.code() in checklist.keys():
                
                if sum([ i == None for i in checklist.values() ]) == 0:
                    # checklist full during interval; set oldest 2chord as target:
                    logging.debug("test_target_chord: setting oldest 2chord. CL: %s" % checklist)
                    target_chord = [ i[0] for i in checklist.items() if i[1] == min(checklist.values()) ][0]
                    # since this is already logged, correct target_chord column:
                    record.entries[-1].target_chord = target_chord
                    logging.debug("test_target_chord: new target_chord: %s" % target_chord)
                    ## success at bottom
                    
                elif checklist[newentry.code()] == None:
                    # non-full checklist and now hitting a vacant 2chord; set target to this:
                    logging.debug("test_target_chord: target_chord == None & hitting vacant target chord.")
                    target_chord = newentry.code()
                    # since this is already logged, correct target_chord column:
                    record.entries[-1].target_chord = target_chord
                    ## success at bottom
                    
                else:
                    # non-full checklist and now hitting a previously tested 2chord: ignore:
                    logging.debug("test_target_chord: hitting pre-tested chord; no success, keeping target_chord = None. %s" % checklist)

        # interval not up:
        else:
            logging.debug("test_target_chord: interval running.")
            if newentry.code() in checklist.keys():
                checklist[newentry.code()] = newentry.timestamp
                logging.debug("test_target_chord: update checklist: %s" % checklist)
        
        # did the above tests yield a target? then SUCCESS
        if newentry.code() == target_chord:
            logging.info("SUCCESS")
            threading.Thread(target = led_success).start()
            
    
    


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


def led_success():
    led_matrix("led patterns/police", 255,  0,  0, 1)
    led_matrix("led patterns/police", 255, 64,  0, 1)
    led_matrix("led patterns/police",   0,255,  0, 1)
    led_matrix("led patterns/police",   0,  0,255, 1)
            
        







# =====================================================================
#  Beginning of app:
# ---------------------------------------------------------------------



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)



# How RPi numbers GPIO pins. Consider BOARD as alternative:
GPIO.setmode(GPIO.BCM)

# set up pins and callback functions:
pins = {
    14: black_callback,
    15: green_callback,
    18: red_callback,
    25: white_callback }
    
for pin in pins.items():
    GPIO.setup(pin[0], GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.add_event_detect(pin[0], GPIO.BOTH, callback = pin[1], bouncetime = 20)

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

