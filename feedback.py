import blinkt
import time
from subprocess import call

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
    led_matrix("led patterns/success", 1)
    
def led_sync_done():
    led_matrix("led patterns/sync_done", 1)

def led_ui_mode():
    blinkt.clear()
    blinkt.set_pixel(0, 50,50,50, .5)
    blinkt.show()

def led_warning():
    led_matrix("led patterns/warning", 4)

def led_new_participant():
    led_matrix("led patterns/new_participant", 1)

def sound_ui_mode():
    call(["aplay audio/voice_uiMode.wav 2>/dev/null"], shell=True)

def sound_exit_ui():
    call(["aplay audio/voice_exit.wav 2>/dev/null"], shell=True)

def sound_success():
    call(["aplay audio/success.wav 2>/dev/null"], shell=True)

def sound_localsave():
    call(["aplay audio/voice_saved.wav 2>/dev/null"], shell=True)

def sound_usberror():
    call(["aplay audio/voice_usberror.wav"], shell=True)
    
def sound_usbaccesserror():
    call(["aplay audio/voice_usbaccesserror.wav"], shell=True)

def sound_new_participant():
    call(["aplay audio/voice_new_participant.wav"], shell=True)

def sound_usbsync_done():
    call(["aplay audio/voice_sync.wav"], shell=True)

def sound_condition(condition):
    if condition == 0:
        call(["aplay audio/voice_cond0.wav"], shell=True)
    if condition == 1:
        call(["aplay audio/voice_cond1.wav"], shell=True)
    if condition == 2:
        call(["aplay audio/voice_cond2.wav"], shell=True)
    if condition == 3:
        call(["aplay audio/voice_cond3.wav"], shell=True)
    if condition == 4:
        call(["aplay audio/voice_cond4.wav"], shell=True)

