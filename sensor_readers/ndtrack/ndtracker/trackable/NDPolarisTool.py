# NDPolarisTool.py
# Definition of NDI Vega Tools in python
# Implementation of NDVegaTool python class

from ndtrack.ndtracker.trackable.NDTrackable import *
from ndtrack.ndtypes.NDError import *
from ndtrack.capi.gbf import Item3D, Component3D, Component6D
from ndtrack.capi.bx import BXPortHandle


class NDVegaMarker(NDMarker):
    """ Describes a Vega Marker
    Vega Markers have position and status
    """
    def __init__(self, marker_id):
        super().__init__()
        self.id = marker_id

    @property
    def name(self):
        return f"M_{self.id}"

    def updateError(self, error):
        # update the marker error
        self.pos.meas_err = error


class NDPolarisTool(NDTool):
    """ Describes a Vega Tool
    Polaris Tools have pose and status
    Polaris tools can obtain data from system using BX2 command. The GBF Component6D contains tool information.
    Polaris tools can obtain data from system using BX command. The BX data is converted into GBF compatible information.
    """
    def __init__(self, port_handle_id):
        super().__init__()
        self.id = port_handle_id

    @property
    def name(self):
        return f"T_{self.id}"

    def get_marker(self, marker_index: int):
        for marker in self.markers:
            if marker.id == marker_index:
                return marker

        # marker not found. add marker to the tool
        self.markers.append(NDVegaMarker(marker_index))
        return self.markers[-1]

    @property
    def is_missing(self):
        """ Status Bit 8 - Transform Missing """
        return (self.status & 0x0100) == 0x0100

    @property
    def face(self):
        """ Status Bits 13-15 - Which face is being tracked """
        return self.status & 0xE000

    def is_error_code(self, code):
        """ Status Bits 0-7 - Error codes """
        return (self.status & 0x00FF) == code

    @property
    def enabled(self):
        """ Error Code 0 - Enabled """
        return self.is_error_code(0)

    @property
    def partially_oov(self):
        """ Error Code 3 - Tool is partially or of the characterized measurement volume """
        return self.is_error_code(3)

    @property
    def partially_averaged(self):
        """ Error Code 5 - Data is partially averaged; averaging depth is less than specified """
        return self.is_error_code(5)

    @property
    def out_of_volume(self):
        """ Error Code 9 - Tool is out of the characterized measurement volume """
        return self.is_error_code(9)

    @property
    def too_few_markers(self):
        """ Error Code 13 - Too few markers detected """
        return self.is_error_code(13)

    @property
    def ir_interference(self):
        """ Error Code 14 - IR interference (a large bright IR object) """
        return self.is_error_code(14)

    @property
    def bad_fit(self):
        """ Error Code 17 - Bad transformation fit """
        return self.is_error_code(17)

    @property
    def buffer_overrun(self):
        """ Error Code 18 - Data buffer limitation (too much data; for example, too many markers) """
        return self.is_error_code(18)

    @property
    def algorithm_limitation(self):
        """ Error Code 19 - Algorithm limitation (processing requires more buffer than is available) """
        return self.is_error_code(19)

    @property
    def fell_behind(self):
        """ Error Code 20 - Fell behind while processing """
        return self.is_error_code(20)

    @property
    def synch_error(self):
        """ Error Code 21 - Position sensors out of synch """
        return self.is_error_code(21)

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
        """ Error Code 33 - Tool has ben unplugged from the System Control Unit """
        return self.is_error_code(33)
