import collections

Chord = collections.namedtuple("Chord",
                               "timestamp black green red white")

class Record_entry():
    def __init__(self, timestamp, chord):
        # check arguments:
        #assert type(btn_states) is list and \
        #           len(btn_states) == 4 and \
        #           sum([i in (0, 1) for i in btn_states]) == 4, \
        #       "btn_states must be a list (0,1) of length 4."
        
        assert type(timestamp) is float, "timestamp must be float."
        
        self.timestamp = timestamp
        self.red       = chord['red']
        self.green     = chord['green']
        self.white     = chord['white']
        self.black     = chord['black']
    
        self.number_pressed = self.red + \
                              self.green + \
                              self.white + \
                              self.black
        
    def string(self):
        return("%f: [%i, %i, %i, %i]" % (self.timestamp, self.black, self.green, self.red, self.white))

    def is_empty(self):
        if self.red + self.green + self.white + self.black == 0: return True
    


class Record():
    def __init__(self):
        self.entries = []

    def add_entry(self, entry):
        assert type(entry) is Record_entry, "attempt to add something other than a Record_entry to Record."
        self.entries.append(entry)
    
    def string(self):
        return [ entry.string() for entry in self.entries ]
    
    def last(self):
        if len(self.entries) > 0:
            return(self.entries[-1])
            
    def len(self):
        return(len(self.entries))






