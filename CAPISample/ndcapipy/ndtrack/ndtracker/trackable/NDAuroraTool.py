# NDAuroraTool.py
# Definition of NDI Aurora Tools in python
# Implementation of NDAuroraTool python class

from ndtrack.ndtracker.trackable.NDTrackable import *
from ndtrack.ndtypes.NDError import *
from ndtrack.capi.bx import BXPortHandle


class NDAuroraTool(NDTool):
    """ Describes an Aurora Tool
    Aurora Tools have pose and status
    Aurora tools can obtain data from system using BX command.
    """
    def __init__(self, port_handle_id):
        super().__init__()
        self.id = port_handle_id

    @property
    def name(self):
        return f"T_{self.id}"

    @property
    def is_missing(self):
        """ Status Bit 8 - Transform Missing """
        return (self.status & 0x0100) == 0x0100

    def is_error_code(self, code):
        """ Status Bits 0-7 - Error codes """
        return (self.status & 0x00FF) == code

    @property
    def enabled(self):
        """ Error Code 0 - Enabled """
        return self.is_error_code(0)

    @property
    def out_of_volume(self):
        """ Error Code 9 - Tool is out of the characterized measurement volume """
        return self.is_error_code(9)

    @property
    def bad_fit(self):
        """ Error Code 17 - Bad transformation fit """
        return self.is_error_code(17)

    @property
    def fell_behind(self):
        """ Error Code 20 - Fell behind while processing """
        return self.is_error_code(20)

    @property
    def processing_exception(self):
        """ Error Code 22 - Processing exception """
        return self.is_error_code(22)

    @property
    def missing(self):
        """ Error Code 31 - Tool is missing """
        return self.is_error_code(31)

    @property
    def disabled(self):
        """ Error Code 32 - Tracking is not enabled for this tool """
        return self.is_error_code(32)

    @property
    def disconnected(self):
        """ Error Code 33 - Tool has ben unplugged from the Sensor Interface Unit """
        return self.is_error_code(33)