# NDEvent.py
# NDEvent python class
# NDEvents are published by NDTrack classes to listeners that have been
# registered to listen for events

# import standard libraries
from enum import IntEnum, unique

@unique
class NDEventCode(IntEnum):
    ERROR =              -1
    OK =                  0
    INFO =                1
    TIMEOUT =            10
    CONNECTING =       1009
    CONNECTED =        1010
    INITIALIZE =       1011
    DISCONNECT =       1012
    RESET =            1013
    TRACKING_START =   1015
    TRACKING_STOP =    1016
    RECORDING_START =  1018
    RECORDING_STOP =   1019

class NDEvent:
    def __init__(self, source, id, message=""):
        self.id = id
        self.msg = message
        self.tracker = source

    def __str__(self):
        return "{} EV {}: {}".format(self.tracker, self.id, self.msg)

    def is_error(self):
        return self.id == NDEventCode.ERROR
