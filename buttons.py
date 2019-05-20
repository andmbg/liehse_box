import RPi.GPIO as GPIO
import time
import collections
import random
from threading import Timer


Chord = collections.namedtuple("Chord",
                               "timestamp black green red white")

class Record_entry():
    def __init__(self, timestamp, black, green, red, white):
        # check arguments:
        #assert type(btn_states) is list and \
        #           len(btn_states) == 4 and \
        #           sum([i in (0, 1) for i in btn_states]) == 4, \
        #       "btn_states must be a list (0,1) of length 4."
        
        assert type(timestamp) is float, "timestamp must be float."
        
        self.timestamp = timestamp
        self.red       = red
        self.green     = green
        self.white     = white
        self.black     = black
    
        self.number_pressed = self.red + \
                              self.green + \
                              self.white + \
                              self.black
        
    def show(self, names = True):
        if names:
            return Chord(timestamp = self.timestamp,
                         black = self.black,
                         green = self.green,
                         red = self.red,
                         white = self.white)
        else:
            return (self.timestamp, self.red, self.green, self.white, self.black)
    


class Record():
    def __init__(self):
        self.entries = []

    def add_entry(self, entry):
        assert type(entry) is Record_entry, \
               "attempt to add something other \
               than a Record_entry to Record."
        self.entries.append(entry)
    
    def show(self, names = True):
        return [ entry.show(names = names) for entry in self.entries ]
    
    def last_entry(self):
        return self.entries[-1]




class Checklist():
    def __init__(self):
        # structure: ID: [timestamp, successful]
        self.entries = { "BG": [None, False],
                         "BR": [None, False],
                         "BW": [None, False],
                         "GR": [None, False],
                         "GW": [None, False],
                         "RW": [None, False] }
    
    def add_if_unique(self, rec):
        assert type(rec) is Record_entry,\
               "argument to add_if_unique must be Record_entry type."
        
        # is this a 2-combo? (no 3- or 4-combo):
        if rec.number_pressed != 2: return
        else:
            if rec.black == 1 and rec.green == 1: combo = "BG"
            if rec.black == 1 and rec.red == 1: combo = "BR"
            if rec.black == 1 and rec.white == 1: combo = "BW"
            if rec.green == 1 and rec.green == 1: combo = "GR"
            if rec.green == 1 and rec.white == 1: combo = "GW"
            if rec.red == 1 and rec.white == 1: combo = "RW"

            if self.entries[combo][0] == None:
                self.entries[combo][0] = rec.timestamp





class Inbox():
    def __init__(self):
        self.slots = { 'red': 0,
                       'green': 0,
                       'white': 0,
                       'black': 0 }
                       
        self.listener = None
    
    def schedule_set(self, logentry, delay = 0.2):
        r = random.random()
        slot = logentry[0]
        self.slots[slot] = logentry[2]
        self.listener = r
        Timer(delay, self.send, [r]).start()
    
    def send(self, r):
        if self.listener == r:
            print(self.slots.values())
