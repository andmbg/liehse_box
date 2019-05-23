import collections

Chord = collections.namedtuple("Chord",
                               "timestamp black green red white")

class Record_entry():
    def __init__(self, timestamp, chord, target_chord):
        # check arguments:
        #assert type(btn_states) is list and \
        #           len(btn_states) == 4 and \
        #           sum([i in (0, 1) for i in btn_states]) == 4, \
        #       "btn_states must be a list (0,1) of length 4."
        
        assert type(timestamp) is float, "timestamp must be float."
        
        self.timestamp = timestamp
        self.black     = chord['black']
        self.green     = chord['green']
        self.red       = chord['red']
        self.white     = chord['white']
        
        self.target_chord = target_chord

    def number_pressed(self):
        return(self.black + self.green + self.red + self.white)
        
    def string(self):
        return("%f [%i, %i, %i, %i] tgt: %s" % \
            (self.timestamp, \
             self.black, self.green, self.red, self.white, \
             self.target_chord))

    def csv(self):
        return("%f, %i, %i, %i, %i, %s" % (self.timestamp, self.black, self.green, self.red, self.white, self.target_chord))
        
        
    def is_empty(self): return self.black + self.green + self.red + self.white == 0
 
    def code(self):
        return(self.black + 2*self.green + 4*self.red + 8*self.white)
        

    


class Record():
    def __init__(self):
        self.entries = []

    def add_entry(self, entry):
        assert type(entry) is Record_entry, "attempt to add something other than a Record_entry to Record."
        self.entries.append(entry)
    
    def csv(self):
        entrylist = [ entry.csv() for entry in self.entries ]
        return('\n'.join(entrylist))
    
    def last(self):
        if len(self.entries) > 0:
            return(self.entries[-1])
    
    def second_last(self):
        if len(self.entries) > 1:
            return(self.entries[-2])
            
    def len(self):
        return(len(self.entries))
        
    def chop(self, n=1):
        self.entries = self.entries[:-n]
    
    # test if the Record ends on the codes given in codeseq
    # used for manipulating the box (new session etc.)
    def testcode(self, codeseq):
        if len(codeseq) > len(self.entries): return
        reference = [ i.code() for i in self.entries[-len(codeseq):] ]
        return(codeseq == reference)
        






