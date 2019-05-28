import RPi.GPIO as GPIO
import time
import buttons
import random
import threading
import logging
import blinkt
from subprocess import call


# some preliminary settings

FREQUENCY   = 100
DELAY       = 0.2 # seconds; min duration to count as button press
DARKSTRETCH = 10 # seconds; how long exploration should remain unsuccessful
DEBUGLEVEL  = logging.INFO # also see logging.basicConfig() at the bottom
blinkt.set_brightness(1)

# set up pins and callback functions:
pins = {
    14: 'black',
    15: 'green',
    18: 'red',
    25: 'white' }

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
    global listener
    listener = 0.0
    global target_chord
    target_chord = None
    global checklist
    checklist = {9: None, 10: None, 12: None}
    global ui_mode
    ui_mode = False
    global warmup
    warmup = True
    global last_poll
    last_poll = None

    print("Starting session ", sessionid)



def timestamp(context):
    global session_start_time
    assert context in ["session", "trial"], "Call timestamp() with argument context = 'session' or 'trial'."
    if context == "session":
        return time.time() - session_start_time
    if context == "trial":
        return time.time() - trial_start_time






def poll():
    global last_poll
    global target_chord
    global record
    global listener
    new_poll = buttons.Record_entry(
        timestamp = timestamp("trial"),
        chord = { pin[1]: 1-GPIO.input(pin[0]) for pin in pins.items() },
        target_chord = target_chord)
    if new_poll == last_poll: return
    
    last_poll = new_poll
        
    # deal with parasitic keypresses:
    listener = random.random()
    entryID = listener
    threading.Timer(DELAY, catch_entry, [new_poll, entryID]).start()
    
    logging.debug("poll: %s" % new_poll)

def catch_entry(entry, entryID):
    global listener
    if entryID == listener:
        on_entry(entry) # check for event triggers





# Handling newly recorded entries
# whenever a new Record_entry is sent to record:
def on_entry(newentry):
    logging.debug("on_entry() | record length: %s" % record.len())

    # on any button or chord above delay threshold
    test_button_press(newentry)  # THIS IS WHERE WE LOG CHORDS!

    if warmup:
        logging.debug("%f in warmup mode" % timestamp("session"))
        test_demo_chord()
    else:
        test_ui_mode(newentry)
        if ui_mode:
            test_flush_record()
            test_new_participant(newentry)
            test_quit_ui_mode(newentry)
        else:
            test_first(newentry)
            test_target_chord(newentry, interval = DARKSTRETCH)




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
        else:
            blinkt.clear()
            blinkt.show()
    else:
        sound_click()

    record.add_entry(newentry)
    logging.info("%s -> added to record" % str(newentry))


def test_first(newentry):
    global trial_start_time
    if record.len() == 1: # if this is the first entry
        # set the trial timer for interval; needs to be different from session
        # timer, as time passes between box reset and trial start
        trial_start_time = time.time()
        record.entries[0].timestamp = timestamp("trial")
        logging.debug("%f this has been the first logged press in this trial" % newentry.timestamp)

def test_demo_chord():
    global record
    global trial_start_time
    global warmup
    if record.testcode([8,0]):
        time.sleep(2)
        record.entries = []
        warmup = False
        threading.Thread(target = led_success).start()
        sound_success()

def test_flush_record():
    global record
    global sessionid
    if record.testcode([2,0]):
        record.chop(6)
        csv_record = "timecode, black, green, red, white, target_chord\n"
        csv_record += record.csv()
        with open("records/%s.record" % sessionid, 'w') as f:
            f.write(csv_record)
        logging.info("wrote record to records/%s.record" % sessionid)
        led_matrix("led patterns/knight",1)
        led_ui_mode()

def test_new_participant(newentry):
    global record
    if record.testcode([8,0]):
        logging.info("%f ========= [ STARTING NEW SESSION ] =========" % newentry.timestamp)
        threading.Thread(target = led_matrix, args = ("led patterns/flash",1)).start()
        new_participant()

def test_quit_ui_mode(newentry):
    global record
    if record.testcode([1,0]):
        logging.info("%f exit user interface mode" % newentry.timestamp)
        record.chop(2)
        threading.Thread(target = led_off).start()
        ui_mode = False

def test_ui_mode(newentry):
    global record
    global ui_mode
    if record.testcode([6,0,6,0]):
        logging.info("%f enter user interface mode" % newentry.timestamp)
        threading.Thread(target = led_ui_mode).start()
        sound_ui_mode()
        ui_mode = True

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
            sound_success()
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
            sound_success()





#  LED & audio actions:
# ----------------------

def led_off():
    blinkt.clear()
    blinkt.show()

def led_matrix(infile, times):
    contents = open(infile).read()
    mat = [ item.split() for item in contents.split('\n')[:-1] ]

    for i in range(times):
        for line in mat:
            blinkt.clear()
            r,g,b = [ int(i) for i in line[8:11] ]
            for column in range(len(line)-3):
                val = int(line[column])
                blinkt.set_pixel(column, r*val,g*val,b*val)
            blinkt.show()
            time.sleep(0.05)
        blinkt.clear()
    blinkt.show()


def led_success():
    led_matrix("led patterns/police", 1)

def led_ui_mode():
    blinkt.clear()
    blinkt.set_pixel(4, 50,0,0, .5)
    blinkt.show()


def sound_click():
    call(["aplay audio/Voltage.wav 2>/dev/null"], shell=True)


def sound_success():
    call(["aplay audio/schuettel2.wav 2>/dev/null"], shell=True)

def sound_ui_mode():
    call(["aplay audio/loeffel.wav 2>/dev/null"], shell=True)








# =====================================================================
#  Beginning of app:
# ---------------------------------------------------------------------

# How RPi numbers GPIO pins. Consider BOARD as alternative:
GPIO.setmode(GPIO.BCM)

for pin in pins.items():
    GPIO.setup(pin[0], GPIO.IN, pull_up_down = GPIO.PUD_UP)

new_participant()

# one log per run of the program; means many records can be logged in one log:
logfilename = "log/%s.log" % sessionid
logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s", level=DEBUGLEVEL,
                        filename=logfilename, filemode='w'
                        )
logging.info("Log %s start.\n-----------------------" % sessionid)

call(['aplay audio/wargames.wav 2>/dev/null'], shell=True)

while True:
    time.sleep(1 / FREQUENCY)
    poll()

