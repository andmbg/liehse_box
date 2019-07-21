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
    led_matrix("led patterns/police", 1)
    
def led_warning():
    led_matrix("led patterns/warning", 1)
    
def led_sync_success():
    led_matrix("led patterns/knight", 1)

def led_ui_mode():
    blinkt.clear()
    blinkt.set_pixel(4, 50,0,0, .5)
    blinkt.show()

def sound_ui_mode():
    call(["aplay audio/loeffel.wav 2>/dev/null"], shell=True)

