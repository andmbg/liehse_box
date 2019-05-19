import RPi.GPIO as GPIO
import time
import collections

Quintet = collections.namedtuple("Quintet",
                                 "ts red green white black")

class Record_entry():
    def __init__(self, timestamp, btn_states):
        # check arguments:
        assert type(btn_states) is list and \
                   len(btn_states) == 4 and \
                   sum([i in (0, 1) for i in btn_states]) == 4, \
               "btn_states must be a list (0,1) of length 4."
        
        assert type(timestamp) is float, "timestamp must be float."
        
        self.timestamp = timestamp
        self.red       = btn_states[0]
        self.green     = btn_states[1]
        self.white     = btn_states[2]
        self.black     = btn_states[3]
    
        self.chord = [self.red, self.green, self.white, self.black]
        
        self.number_pressed = self.red + \
                         self.green + \
                         self.white + \
                         self.black
        
    def show(self, names = True):
        if names:
            return Quintet(ts = self.timestamp,
                           red = self.red,
                           green = self.green,
                           white = self.white,
                           black = self.black )
        else:
            return (self.timestamp, self.red, self.green, self.white, self.black)
    


class Record():
    def __init__(self):
        self.entries = [Record_entry(0.0, [0,0,0,0])]

    def add_entry(self, entry):
        assert type(entry) is Record_entry, \
               "attempt to add something other \
               than a Record_entry to Record."
        self.entries.append(entry)
    
    def show(self, names = True):
        return [ entry.show(names = names) for entry in self.entries ]
    
    def last_entry(self):
        return self.entries[-1]



