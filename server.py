from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import RPi.GPIO as GPIO
import time
import collections
import buttons

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



# create the container of our log, the thing that we will save later:
button_record = buttons.Record()



# setup single logs for debouncing (these don't end up in the result):
red_log   = [("red", timestamp(), 0)]
green_log = [("green", timestamp(), 0)]
white_log = [("white", timestamp(), 0)]
black_log = [("black", timestamp(), 0)]



# setup checklist for 2-chords already pressed:
checklist = buttons.Checklist()

# inbox filters parasitic keylogs, returns chords
inbox = buttons.Inbox()



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
    print("{ ,  ,  , %i} raw" % state)
    # returns (button, time, state):
    res = button_log(channel,
                     red_log,
                     timestamp(),
                     state)
    if res == None: return
    
    red_log.append(res)
    if res[2] == 1: inbox.schedule_on("red", delay = DELAY)
    if res[2] == 0: inbox.schedule_off("red", delay = DELAY)
        
def green_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    state = 1 - GPIO.input(channel)
    print("{ ,  ,  , %i} raw" % state)
    # returns (button, time, state):
    res = button_log(channel,
                     green_log,
                     timestamp(),
                     1 - GPIO.input(channel))
    
    if not res == None:
        green_log.append(res)
        if res[2] == 1: inbox.schedule_on("green", delay = DELAY)
        if res[2] == 0: inbox.schedule_off("green", delay = DELAY)
        
def white_callback(channel):
    # hack against bouncing:
    time.sleep(.01)
    state = 1 - GPIO.input(channel)
    print("{ ,  ,  , %i} raw" % state)
    # returns (button, time, state):
    res = button_log(channel,
                     white_log,
                     timestamp(),
                     1 - GPIO.input(channel))
    if not res == None:
        white_log.append(res)
        if res[2] == 1: inbox.schedule_on("white", delay = DELAY)
        if res[2] == 0: inbox.schedule_off("white", delay = DELAY)
        
def black_callback(channel):
    # returns (button, time, state):
    print("(   %i, %i, %i)" % (1-GPIO.input(18), 1-GPIO.input(15), 1-GPIO.input(14)))


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
