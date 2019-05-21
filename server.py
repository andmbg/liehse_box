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

logging.basicConfig(level = logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


# remove mechanical button bounce and parasitic keylogs:
BOUNCETIME = 0.5 # seconds
DELAY = 0.2

# How RPi numbers GPIO pins. Consider BOARD as alternative:
GPIO.setmode(GPIO.BCM)

# Check numbering mode above and check where buttons are connected,
# amend below as needed:
red = 14
green = 15
white = 18
black = 25



GPIO.setup(red,
           GPIO.IN,
           pull_up_down = GPIO.PUD_UP)

GPIO.setup(green,
           GPIO.IN,
           pull_up_down = GPIO.PUD_UP)

GPIO.setup(white,
           GPIO.IN,
           pull_up_down = GPIO.PUD_UP)

GPIO.setup(black,
           GPIO.IN,
           pull_up_down = GPIO.PUD_UP)



start_time = time.time()
def timestamp(): return time.time() - start_time




# setup single logs for debouncing (these don't end up in the result):
red_debouncelog   = [("red", timestamp(), 0)]
green_debouncelog = [("green", timestamp(), 0)]
white_debouncelog = [("white", timestamp(), 0)]
black_debouncelog = [("black", timestamp(), 0)]



# setup checklist for 2-chords already pressed:
#checklist = 



# inbox filters parasitic keylogs, returns chords
inbox = { 'red': 0,
          'green': 0,
          'white': 0,
          'black': 0 }

# only the last button press's Timer should be relevant:
listener = 0

# our log:
record = buttons.Record()
logging.debug(type(record))



def schedule_set(logentry, delay = 0.2):
    
    def send_chord(chord, timerID):
        global record
        if listener == timerID:
            newentry = buttons.Record_entry(timestamp(), chord)
            record.add_entry(newentry)
            logging.debug("send_chord(): %s" % record.last().string())
            logging.debug(id(record))
 
    global inbox
    global listener
    timerID = random.random()
    slot = logentry[0]
    inbox[slot] = logentry[2]
    listener = timerID
    threading.Timer(delay, send_chord, [inbox, timerID]).start()



# return clean single button events. Clean means no bouncing.
def button_log(channel, log, this_time, this_state):
    # get time & on/off of the last entry:
    last_time, last_state = log[-1][1:3]
    button = {14: "red",
              15: "green",
              18: "white",
              25: "black"}[channel]
    res = None

    # is this state different? log it:
    if this_state != last_state:
        res = (button, this_time, this_state)

    # this state is the same? if the interval is > BOUNCETIME,
    # it's a 1 glued right before a 0 -- log it as 0, likely
    # ignore the actual 0, leading to a clean button release:
    if this_state == last_state and \
       this_time - last_time > BOUNCETIME:
            res = (button, this_time, 1 - this_state)
    
    #print(res, 1 - GPIO.input(15))
    return(res)



def red_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    state = 1 - GPIO.input(channel)
    print("( ,  ,  , %i)" % state)
    # returns (button, time, state):
    logentry = button_log(channel,
                          red_debouncelog,
                          timestamp(),
                          state)
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
GPIO.add_event_detect(red,
                      GPIO.BOTH,
                      bouncetime = 20,
                      callback = red_callback)

GPIO.add_event_detect(green,
                      GPIO.BOTH,
                      bouncetime = 20,
                      callback = green_callback)

GPIO.add_event_detect(white,
                      GPIO.BOTH,
                      bouncetime = 20,
                      callback = white_callback)

GPIO.add_event_detect(black,
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

