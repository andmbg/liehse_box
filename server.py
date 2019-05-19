from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import RPi.GPIO as GPIO
import time
import collections

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


# Mechanical buttons are noisy, often producing >1 voltage edges per press;
# this helps to filter parasitic button press logs.
BOUNCETIME = 200 # milliseconds

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



# setup logs:
red_log = collections.OrderedDict()
red_log[time.time()] = 0

green_log = collections.OrderedDict()
green_log[time.time()] = 0

white_log = collections.OrderedDict()
white_log[time.time()] = 0

black_log = collections.OrderedDict()
black_log[time.time()] = 0



# return clean single button events. Clean means no bouncing.
def button_log(channel, log, this_time, this_state):
    # get time & on/off of the last entry:
    last_time, last_state = list(log.items())[-1]
    res = None

    # is this state different? log it:
    if this_state != last_state:
        res = (this_time, this_state)

    # this state is the same? if the interval is > BOUNCETIME,
    # it's a 1 glued right before a 0 -- log it as 0, likely
    # ignore the actual 0, leading to a clean button release:
    if this_state == last_state and \
       this_time - last_time > BOUNCETIME/1000:
            res = (this_time, 1 - this_state)
    
    if res == None: return
    
    button = {14: "red",
              15: "green",
              18: "white",
              25: "black"}[channel]

    print(button, this_time, this_state, "logged as: ", res)
    
    socketio.emit('my_response',
                  { 'time': res[0],
                    'state': res[1] })

    return(res)



def red_callback(channel):
    fresh_time = time.time()
    fresh_state = 1 - GPIO.input(channel)
    this_log_entry = \
        button_log(channel, red_log, fresh_time, fresh_state)
    if not this_log_entry == None:
        red_log[this_log_entry[0]] = this_log_entry[1]

def green_callback(channel):
    fresh_time = time.time()
    fresh_state = 1 - GPIO.input(channel)
    this_log_entry = \
        button_log(channel, green_log, fresh_time, fresh_state)
    if not this_log_entry == None:
        green_log[this_log_entry[0]] = this_log_entry[1]

def white_callback(channel):
    fresh_time = time.time()
    fresh_state = 1 - GPIO.input(channel)
    this_log_entry = \
        button_log(channel, white_log, fresh_time, fresh_state)
    if not this_log_entry == None:
        white_log[this_log_entry[0]] = this_log_entry[1]

def black_callback(channel):
    fresh_time = time.time()
    fresh_state = 1 - GPIO.input(channel)
    this_log_entry = \
        button_log(channel, black_log, fresh_time, fresh_state)
    if not this_log_entry == None:
        black_log[this_log_entry[0]] = this_log_entry[1]



# Set up listeners on GPIOs:
GPIO.add_event_detect(red,
                      GPIO.BOTH,
                      bouncetime = 1,
                      callback = red_callback)

GPIO.add_event_detect(green,
                      GPIO.BOTH,
                      bouncetime = 1,
                      callback = green_callback)

GPIO.add_event_detect(white,
                      GPIO.BOTH,
                      bouncetime = 1,
                      callback = white_callback)

GPIO.add_event_detect(black,
                      GPIO.BOTH,
                      bouncetime = 1,
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
