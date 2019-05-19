from buttons import Record_entry, Record
import time

r = Record_entry( time.time(), [1, 0, 0, 1] )

Rec = Record()

Rec.add_entry(Record_entry(time.time(), [1,0,0,1]))
Rec.add_entry(Record_entry(time.time(), [1,0,0,0]))
