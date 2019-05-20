import collections

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







