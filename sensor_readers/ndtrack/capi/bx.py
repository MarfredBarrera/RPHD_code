# bx.py
# Data class for NDI CAPI BX response

import math
from ndtrack.capi.packer import *
from ndtrack.capi.defines import *
from ndtrack.ndtypes.NDDataTypes import *


class ReplyOption(IntEnum):
    """ BX parameter specifies which information will be returned.
    The reply option are enumarated flags. They can be OR'd together.
    If multiple reply options are used, replies are returned for each port handle in order of increasing option value.
    Reply option 0x0800 (AllTransforms) enables the system to return certain information in the other options.
    Reply option 0x1000 (StrayPassive) is reported after all handle-specific options but before the System Status
    Reply option 0x2000 (StrayPassiveExtended) appends extended stray passive marker status
    """
    Transformation = 0x0001
    ToolAndMarkerInfo = 0x0002
    StrayActiveMarker = 0x0004
    ToolMarkers = 0x0008
    AllTransforms = 0x0800
    HandleData = 0x000F
    StrayPassive = 0x1000
    StrayPassiveExtended = 0x2000


class HandleStatus(IntEnum):
    """ BX handles can have the following status:
    """
    Valid = 1
    Missing = 2
    Disabled = 4


class PortStatus(IntEnum):
    """ Port status is returned in a bit field
        bit 0   - Occupied
        bit 1   - Switch 1 closed
        bit 2   - Switch 2 closed
        bit 3   - Switch 3 closed
        bit 4   - Initialized
        bit 5   - Enabled
        bit 6   - Out of volume
        bit 7   - Partially out of volume
        bit 8   - Algorithm Limitation (processing requires more buffer than is available)
        bit 9   - IR inteference (a large bright IR object)
        bit 10  - Reserved
        bit 11  - Reserved
        bit 12  - Processing exception (same as tool information bit 7 in reply option 0002)
        bit 13  - Reserved
        bit 14  - Fell behind while processing (same as tool information bit 3 in reply option 0002)
        bit 15  - Data buffer limitation (too much data; for example, too many markers)
    """
    Occupied = 0x0001
    Switch1 = 0x0002
    Switch2 = 0x0004
    Switch3 = 0x0005
    Initialized = 0x0010
    Enabled = 0x0020
    OutOfVolume = 0x0040
    PartiallyOutOfVolume = 0x0080
    BufferOverrun = 0x0100
    IRInterference = 0x0200
    Reserved_10 = 0x0400
    Reserved_11 = 0x0800
    ProcessingException = 0x1000
    Reserved_13 = 0x2000
    FellBehind = 0x4000
    DataBufferLimit = 0x8000


class SystemStatus(IntEnum):
    """ System status is returned in a bit field
        bit 0   - System communication synchronization error
        bit 3   - Recoverable system processing exception
        bit 6   - Some port handle has become occupied
        bit 7   - Some port handle has become unoccupied
        bit 8   - Diagnostic pending
        bit 9   - System is not within operating temperature range
        bit 10  - Hardware confiruration changed
    """
    OK = 0x0000
    SynchError = 0x0001
    Reserved_1 = 0x0002
    Reserved_2 = 0x0004
    ProcessingException = 0x0008
    Reserved_4 = 0x0010
    Reserved_5 = 0x0020
    HandleOccupied = 0x0040
    HandleUnoccupied = 0x0080
    Diagnostic = 0x0100
    Temperature = 0x0200
    ConfigChange = 0x0400
    Reserved_11 = 0x0800
    Reserved_12 = 0x1000
    Reserved_13 = 0x2000
    Reserved_14 = 0x4000
    Reserved_15 = 0x8000


class ToolInformation(IntEnum):
    """ Tool information is a 1 byte bit field
        bit 0   - Bad transformation fit
        bit 1   - Not enough acceptable markers for transformation
        bit 2   - IR interference
        bit 3   - Fell behind while processing
        bit 4-6 - Tool face used
        bit 7   - Processing exception
    """
    OK = 0x00
    BadTransform = 0x01
    NotEnoughMarkers = 0x02
    IRInterference = 0x04
    FellBehind = 0x08
    ToolFace = 0x70
    ProcessingException = 0x80


class MarkerInformation(IntEnum):
    """ Marker information is a 4-bit bit field
        0000    - Not used because it was missing
        0001    - Not used because it exceeded the maximum marker angle
        0010    - Not used because it exceeded the maximum 3D error for the tool
        0011    - Used to calculate the transformation
        0100    - Used to calculate the transformation, but it is out of volume
        0101    - Not used because it was outside the characterized measurement and was not needed for transformation
    """
    Missing = 0
    OffAngle = 1
    Max3DError = 2
    Used = 3
    OutOfVolume = 4
    OutOfCharacterized = 5


def marker_index(index):
    """ Obtain the marker index within an array
    When a complete array of marker information is present, the markers can be accessed using
    - a numeric index (0..19)
    - their letter designation (A..T)
    NOTE: Tracking Systems that use BX can have a maximum of 20 markers

    Args:
        index: numeric array index or letter designation

    Returns:
        numeric array index of specified marker (0..19)
    """
    # markers can be accessed by their letter designation
    if type(index) is str:
        # convert letter to numeric index A=0,B=1,...,T=20
        i = ord(index.upper()) - ord('A')
    else:
        # use the numeric index provided
        i = index

    return i


class BXComponent(ABC):
    """ A BX response if made up of BXComponents
    BXComponent is an abstract base class
    BXComponent subclasses must override the `parse` functions
    BXComponent subclasses must call `super().__init__(buffer, options)` if they override `__init__`
    Each BXComponent has a 'data' member where the parsed response data is stored

    Args:
        buffer: bytearray containing data to be parsed
        options: BX Reply Options. Must be the Reply Options sent to the system. Specify data is contained in buffer
    """
    def __init__(self, buffer, options=0x0001):
        self.options = options
        self.data = []

        # parse the buffer
        # the `parse` override will store the parsed data into self.data
        try:
            self.parse(buffer)
        except NDError as err:
            raise NDError(NDStatusCode.SYSTEM_ERROR, "Error parsing BX response", self) from err

    @abstractmethod
    def parse(self, buffer):
        """ Every BXComponent subclass must override the `parse` abstract method """
        return False

    def is_option(self, option):
        """ Indicate if the specified option has been specified in BX options """
        return (self.options & option) > 0

    def add_data(self, data_item):
        """ Add one item of data to the data list """
        self.data.append(data_item)


class BX(BXComponent):
    """ Contains data obtained from a BX response
    BX response has the following format:
        <Number of Handles>
        <Handle 1><Handle 1 Status><Reply Opt 0001 Data>...<Reply Opt 0008 Data>
        ...
        <Handle n><Handle n Status><Reply Opt 0001 Data>...<Reply Opt 0008 Data>
        <Reply Option 1000 Data>
        <System Status>

    To access specific BX data, access the appropriate data member
    e.g.    Given bx = BX(buffer, options) then
            Number of port handles              = bx.num_handles
            Status for nth port handle          = bx.get_handle(n).valid
                                                  bx.get_handle(n).missing
                                                  bx.get_handle(n).disabled
            Tool transform for nth port handle  = bx.get_handle(n).pose
            Frame number for nth port handle    = bx.get_handle(n).frame_number

    Members
    num_handles     Number of Port Handles
    data            Data from each Port Handle
    stray_passive   (optional) Stray Marker Data, if StrayPassive option is specified
    status          System Status
    """
    def __init__(self, buffer, options: int):
        # initialize data members
        self.num_handles = 0
        self.stray_passive = None
        self.status = None

        # initialize BX Component
        super().__init__(buffer, options)

    def __str__(self):
        out = f"Number of Handles: {self.num_handles}\n"

        # output information for each port handle
        for item in self.data:
            out += "\t" + str(item) + "\n"

        # output system status
        out += "\tStatus: " + str(self.status) + "\n"

        return out

    def parse(self, buffer):
        """ Parse the BX data response

            The buffer contains
                - Number of Handles     1 byte
                - Data for each handle  n handles
                - optional 3D Position of Stray Passive Markers (Reply Option 1000) if specified in options
                - System Status         2 bytes

        Args:
            buffer: buffer containing BX data, starting at the number of handles
        """
        # Number of handles - 1 byte
        self.num_handles = unpack_int(buffer, 1)

        # add one item to self.data for each port handle
        for h in range(self.num_handles):
            self.add_data(BXPortHandle(buffer, self.options))

        # if stray passive marker data has been requested, parse the stray marker data
        if self.is_option(ReplyOption.StrayPassive):
            self.stray_passive = BXStrayPassiveMarkers(buffer, self.options)

        # parse the system status. 2 bytes
        self.status = BXSystemStatus(buffer)

    def get_handle(self, index):
        if self.num_handles <= index:
            raise NDError(NDStatusCode.USE_ERROR,
                          f"Handle index ({index}) out of range. {self.num_handles} port handles reported.", self)

        # return the handle data for the specified index
        return self.data[index]


class BXPortHandle(BXComponent):
    """ Contains data for one port handle in the BX response

    Each port handle contains data depending on the reply option specified
    <Handle n><Handle n Status><Reply Opt 0001 Data>...<Reply Opt 0008 Data>

    Reply Options may indicate the following data
    Reply Option 0001   Transformation Data
    Reply Option 0002   Tool and Marker Information
    Reply Option 0004   3D position of single stray active marker
    Reply Option 0008   3D position of markers on tools
    """
    def __init__(self, buffer, options: int):
        # initialize data members
        self.handle = None
        self.handle_status = None
        self.port_status = None
        self.frame_number = None
        self.tool_marker_info = None
        self.stray_active_marker = None
        self.markers = None

        # initialize BX Component
        super().__init__(buffer, options)

    def __str__(self):
        return f"PH_{self.handle}: ({self.status_str}) {self.pose}"

    def parse(self, buffer):
        """ Parse one handle's data from the BX data response

            The buffer contains
                - Handle ID             1 byte
                - Handle Status         1 byte
                - optional Transformation Data (Reply Option 0001) if specified in options
                - optional Tool and Marker Information (Reply Option 0002) if specified in options
                - optional 3D Position of Single Stray Active Marker (Reply Option 0004) if specified in options
                - optional 3D Position of Markers on Tools (Reply Option 0008) if specified in options

        Args:
            buffer: buffer containing BX response data, starting at the desired handle data
        """
        self.handle = unpack_int(buffer, 1)
        self.handle_status = unpack_int(buffer, 1)

        # optional Transformation Data
        # <Reply Opt 0001 Data> = <Q0><Qx><Qy><Qz><Tx><Ty><Tz><Error><Port Status><Frame Number>
        # or, if handle status is "missing",
        # <Reply Opt 0001 Data> = <Port Status><Frame Number>
        if self.is_option(ReplyOption.Transformation):
            # if the handle status is "disabled", nothing is reported
            if self.disabled:
                # nothing left to look at
                return;
            
            # if the handle status is "missing", the system does not return a transformation
            pose = NDPose()
            if not self.missing:
                # dat is available. parse the transformation
                q0 = unpack_float(buffer)
                qx = unpack_float(buffer)
                qy = unpack_float(buffer)
                qz = unpack_float(buffer)
                tx = unpack_float(buffer)
                ty = unpack_float(buffer)
                tz = unpack_float(buffer)
                err_val = unpack_float(buffer)
                pose = NDPose([q0, qx, qy, qz, tx, ty, tz], err=err_val)
            # add pose
            self.add_data(pose)
            # port status - 4 bytes
            self.port_status = unpack_int(buffer, 4)
            # frame number - 4 byte unsigned integer
            self.frame_number = unpack_uint(buffer, 4)

        # optional Tool And Marker Information
        if self.is_option(ReplyOption.ToolAndMarkerInfo):
            self.tool_marker_info = BXToolAndMarkerInformation(buffer, self.handle, self.options)

        # optional 3D Position of Single Stray Active Marker
        if self.is_option(ReplyOption.StrayActiveMarker):
            self.stray_active_marker = BXStrayActiveMarker(buffer, self.options)

        # optional 3D Position of Markers on Tools
        if self.is_option(ReplyOption.ToolMarkers):
            self.markers = BXToolMarkers(buffer, self.handle, self.options)

    @property
    def pose(self):
        """ self.data holds the Port Handle tool transformation """
        # Pose is available only if the Reply Option is specified
        if self.is_option(ReplyOption.Transformation) and len(self.data) > 0:
            return self.data[0]
        else:
            return None

    def is_status(self, status):
        """ Check if the handle status has the specified status
        Possible port handle status are enumarated in HandleStatus
        """
        return (self.handle_status & status) == status

    def is_port_status(self, status):
        """ Check if the port status has the specified status
        Possible status are enumerated in PortStatus
        """
        return (self.port_status & status) == status

    @property
    def status_str(self):
        """ Return the port handle status as a string """
        if self.valid:
            return "Valid"
        if self.missing:
            return "Missing"
        if self.disabled:
            return "Disabled"
        return "Unknown"

    @property
    def valid(self):
        """ Handle Status 2 is Valid """
        return self.is_status(HandleStatus.Valid)

    @property
    def ok(self):
        """ Handle Status is 'ok' if it is Valid """
        return self.valid

    @property
    def missing(self):
        """ Handle Status 2 indicates Missing """
        return self.is_status(HandleStatus.Missing)

    @property
    def disabled(self):
        """ Handle Status 4 indicates Disabled """
        return self.is_status(HandleStatus.Disabled)

    @property
    def occupied(self):
        return self.is_port_status(PortStatus.Occupied)

    @property
    def initialized(self):
        return self.is_port_status(PortStatus.Initialized)

    @property
    def enabled(self):
        return self.is_port_status(PortStatus.Enabled)

    @property
    def out_of_volume(self):
        return self.is_port_status(PortStatus.OutOfVolume)

    @property
    def partially_oov(self):
        return self.is_port_status(PortStatus.PartiallyOutOfVolume)

    @property
    def switch_1_closed(self):
        return self.is_port_status(PortStatus.Switch1)

    @property
    def switch_2_closed(self):
        return self.is_port_status(PortStatus.Switch2)

    @property
    def switch_3_closed(self):
        return self.is_port_status(PortStatus.Switch3)

    @property
    def buffer_overrun(self):
        return self.is_port_status(PortStatus.BufferOverrun)

    @property
    def ir_inteference(self):
        return self.is_port_status(PortStatus.IRInterference)

    @property
    def processing_exception(self):
        return self.is_port_status(PortStatus.ProcessingException)

    @property
    def fell_behind(self):
        return self.is_port_status(PortStatus.FellBehind)

    @property
    def data_buffer_limitation(self):
        return self.is_port_status(PortStatus.DataBufferLimit)

    @property
    def too_few_markers(self):
        if self.tool_marker_info is None:
            return False
        else:
            return self.tool_marker_info.not_enough_markers

    @property
    def bad_transform(self):
        if self.tool_marker_info is None:
            return False
        else:
            return self.tool_marker_info.bad_transform


class BXToolAndMarkerInformation(BXComponent):
    """ Contains Tool and Marker information

    BX Tool and Marker information is obtained if the BX Reply Option contains 0002
        <Reply Option 0002 Data> = <Tool Information><Marker Information>

        Tool Information - 1 byte
        Marker Information - 10 bytes (4 bits per marker)

    The tool and marker information is parsed and interpreted. Users can call the appropriate functions to check status.
    """
    def __init__(self, buffer, handle: int, options: int):
        # initialize Tool and Marker data
        self.tool_info = None
        self.handle = handle

        # initialize BX Component
        super().__init__(buffer, options)

    def __str__(self):
        out = ""

        # Tool Status
        if self.ok:
            out += "OK\n"
        if self.bad_transform:
            out += "Bad Transform\n"
        if self.not_enough_markers:
            out += "Not Enough Markers\n"
        if self.ir_interference:
            out += "IR Interference\n"
        if self.fell_behind:
            out += "Fell Behind\n"
        if self.processing_exception:
            out += "Processing Exception\n"
        if self.face_used != 0:
            out += f"Face Used: {self.face_used}\n"

        # Markers Status
        for m in iter("ABCDEFGHIJKLMNOPQRST"):
            if self.is_marker_used(m):
                out += "U"
            elif self.is_marker_missing(m):
                out += "m"
            elif self.is_marker_off_angle(m):
                out += "a"
            elif self.is_marker_max_3d_error(m):
                out += "x"
            elif self.is_marker_out_of_volume(m):
                out += "o"
            elif self.is_marker_out_of_characterized(m):
                out += "c"

        return out

    def parse(self, buffer):
        # if the BX command options include 'Tool and Marker Information', parse the tool and marker info
        if self.is_option(ReplyOption.ToolAndMarkerInfo):
            # 1 byte - Tool Information
            self.tool_info = unpack_uint(buffer, 1)

            # 10 bytes (4 bits per marker) - Marker Information
            marker_info = unpack_bytes(buffer, 10)
            # each byte contains information for 2 markers - 4 bits per marker
            # little endian. 10 bytes = [
            for b in range(10):
                self.add_data(marker_info[-b-1] & 0x0F)
                self.add_data(marker_info[-b-1] >> 4 & 0x0F)

    def is_tool_status(self, status):
        return (self.tool_info & status) == status

    @property
    def ok(self):
        return self.tool_info == 0x00

    @property
    def bad_transform(self):
        return self.is_tool_status(ToolInformation.BadTransform)

    @property
    def not_enough_markers(self):
        return self.is_tool_status(ToolInformation.NotEnoughMarkers)

    @property
    def ir_interference(self):
        return self.is_tool_status(ToolInformation.IRInterference)

    @property
    def fell_behind(self):
        return self.is_tool_status(ToolInformation.FellBehind)

    @property
    def processing_exception(self):
        return self.is_tool_status(ToolInformation.ProcessingException)

    @property
    def face_used(self):
        # bits 4 to 6 of the Tool Information
        return (self.tool_info & ToolInformation.ToolFace) >> 4

    def get_marker_info(self, index):
        try:
            return self.data[marker_index(index)]
        except IndexError as err:
            raise NDError(NDStatusCode.USE_ERROR, f"Invalid marker index ({index}) specified", self) from err

    def is_marker_used(self, index):
        return self.get_marker_info(index) == MarkerInformation.Used

    def is_marker_missing(self, index):
        return self.get_marker_info(index) == MarkerInformation.Missing

    def is_marker_off_angle(self, index):
        return self.get_marker_info(index) == MarkerInformation.OffAngle

    def is_marker_max_3d_error(self, index):
        return self.get_marker_info(index) == MarkerInformation.Max3DError

    def is_marker_out_of_volume(self, index):
        return self.get_marker_info(index) == MarkerInformation.OutOfVolume

    def is_marker_out_of_characterized(self, index):
        return self.get_marker_info(index) == MarkerInformation.OutOfCharacterized


class BXStrayActiveMarker(BXComponent):
    """ Contains 3D Position of Single Stray Active Marker

    BX Stray Active Marker information is obtained if the BX Reply Option contains 0004
        <Reply Option 0004 Data> = <Status><Tx><Ty><Tz>
            or
        <Reply Option 0004 Data> = <Status>

        Status  - 1 byte
        Tx      - 4 bytes
        Ty      - 4 bytes
        Tz      - 4 bytes

    If no stray active marker is defined, the status is 00 and no position information is returned.
    If the marker is MISSING, the system returns only the status.
    If the marker is out of volume and reply option 0800 is not used, the system returns only the status.
    """
    def __init__(self, buffer, options: int):
        # initialize component members. set status to MISSING
        self.status = 0x02

        # initialize BX Component
        super().__init__(buffer, options)

    def __str__(self):
        return str(self.pos) + f"\tValid: {self.valid}\tMissing: {self.missing}\tOOV: {self.out_of_volume}"

    def parse(self, buffer):
        # if the BX command options include '3D Position of Single Stray Active Marker'
        if self.is_option(ReplyOption.StrayActiveMarker):
            # stray active marker status - 1 byte
            self.status = unpack_uint(buffer, 1)

            # position is reported if marker is valid or marker is OOV and AllTransforms Reply Option is provided
            if self.valid or (self.out_of_volume and self.is_option(ReplyOption.AllTransforms)):
                # if the marker status is 'valid', the succeeding data is the 3D position
                tx = unpack_float(buffer)
                ty = unpack_float(buffer)
                tz = unpack_float(buffer)
                self.add_data(NDPosition(tx, ty, tz))
            else:
                # set position to MISSING
                self.add_data(NDPosition)

    def is_status(self, status):
        return self.status == status

    @property
    def valid(self):
        return self.is_status(0x01)

    @property
    def missing(self):
        return self.is_status(0x02)

    @property
    def out_of_volume(self):
        return self.is_status(0x08)

    @property
    def pos(self):
        """ Return the 3D position of the stray active marker
        The 3D position is stored as NDPosition. It is the only item in the 'data' member of this class.
        """
        return self.data[0]


class ToolMarker:
    """ Implementation of a Tool Marker """
    def __init__(self, position, out_of_volume):
        self.position = position
        self.status = Status3D.OKAY
        if out_of_volume == 0x01:
            self.status = Status3D.OOV

    def __str__(self):
        return str(self.pos) + "\tOOV:" + str(self.is_oov)

    @property
    def pos(self):
        return self.position

    @property
    def ok(self):
        return self.status == Status3D.OKAY

    @property
    def is_oov(self):
        return self.status == Status3D.OOV


class BXToolMarkers(BXComponent):
    """ Contains 3D Position of Markers on Tools

    BX Markers on Tools is obtained when the BX Reply Option contains 0008
        <Reply Option 0008 Data> = <Number of Markers><Out of Volume><Tx_n><Ty_n><Tz_n>

        Number of Markers   - 1 byte
        Out of Volume       - 1 byte/8 markers (1 bit per marker)
        Tx_n, Ty_n, Tz_n    - 4 bytes each for each marker
    """
    def __init__(self, buffer, handle: int, options: int):
        # initialize component members
        self.num_markers = 0
        self.handle = handle

        # initialize BX Component
        super().__init__(buffer, options)

    def __str__(self):
        out = ""
        for m in range(self.num_markers):
            out += str(self.get_marker(m)) + "\n"
        return out

    def parse(self, buffer):
        # if the BX command options include '3D Position of Markers On Tools', parse tool markers
        if self.is_option(ReplyOption.ToolMarkers):
            # Number of markers - 1 byte
            self.num_markers = unpack_int(buffer, 1)

            # Out of Volume - 1 byte/8 markers (1 bit per marker)
            # reply size = (number of markers)/8, rounded up to the nearest integer
            reply_size = math.ceil(self.num_markers / 8)
            oov_bytes = unpack_bytes(buffer, reply_size)

            # Txn, Tyn, Tzn - 4 bytes each. Position of the nth marker
            for m in range(self.num_markers):
                tx = unpack_float(buffer)
                ty = unpack_float(buffer)
                tz = unpack_float(buffer)

                # determine out of volume status
                oov_bytes_dim = divmod(m, 8)
                byte = oov_bytes_dim[0]
                bit = oov_bytes_dim[1]
                oov = (oov_bytes[-(byte + 1)] >> bit) & 0x01
                # create a ToolMarker with the 3d position and out of volume status
                self.add_data(ToolMarker(NDPosition(tx, ty, tz), oov))

    def get_marker(self, index):
        """ Obtain the desired tool marker """
        try:
            return self.data[marker_index(index)]
        except IndexError as err:
            raise NDError(NDStatusCode.USE_ERROR, f"Invalid index ({index}) specified", self) from err


class StrayPassiveMarker(ToolMarker):
    """ Implementation of a Stray Passive Marker """
    def __init__(self, position, out_of_volume, extended_marker_status):
        super().__init__(position, out_of_volume)
        self.extended_marker_status = extended_marker_status

    def __str__(self):
        return str(self.pos) + "\tOOV:" + str(self.is_oov) + "\tPhantom:" + str(self.is_possible_phantom)

    @property
    def is_possible_phantom(self):
        """ status bit 0 = 1 when marker shares lines of sight with other markers and is possible phantom """
        return (self.extended_marker_status & 0x1) == 0x1


class BXStrayPassiveMarkers(BXComponent):
    """ Contains 3D Position of Stray Passive Markers

    BX Stray Passive Markers are reported when BX Reply Option contains 1000
        <Reply Option 1000 Data> = <Number of Markers><Out of Volume><Tx_n><Ty_n><Tz_n>

        Number of Markers   - 1 byte
        Out of Volume       - 1 byte per 8 markers
        Tx, Ty, Tz          - 4 bytes each per marker
    """
    def __init__(self, buffer, options: int):
        # initialize component members
        self.num_markers = 0

        # initialize BX Component
        super().__init__(buffer, options)

    def __str__(self):
        out = ""
        for m in range(self.num_markers):
            out += str(self.get_marker(m)) + "\n"
        return out

    def parse(self, buffer):
        # if the BX command options include 'Stray Marker Data', parse the 3D positions of stray passive markers
        if self.is_option(ReplyOption.StrayPassive):
            # Number of Markers - 1 byte
            self.num_markers = unpack_int(buffer, 1)

            # if the number of markers is zero, we are done
            if self.num_markers > 0:
                # Out of Volume - 1 byte/8 markers (1 bit per marker)
                # reply size = (number of markers)/8, rounded up to the nearest integer
                reply_size = math.ceil(self.num_markers / 8)
                oov_bytes = unpack_bytes(buffer, reply_size)

                # Txn, Tyn, Tzn - 4 bytes each. Position of the nth marker
                for m in range(self.num_markers):
                    tx = unpack_float(buffer)
                    ty = unpack_float(buffer)
                    tz = unpack_float(buffer)
                    oov_bytes_dim = divmod(m, 8)
                    byte = oov_bytes_dim[0]
                    bit = oov_bytes_dim[1]
                    oov = (oov_bytes[-(byte+1)] >> bit) & 0x01
                    # create a StrayPassiveMarker with the 3d position and out of volume status
                    # extended marker information will be added later if Reply Option 2000 is specified
                    self.add_data(StrayPassiveMarker(NDPosition(tx, ty, tz), oov, 0))

                # Reply Option 2000 can be used in conjunction with Reply Option 1000
                #   <Reply Option 2000 Data> = <extended marker information status>
                if self.is_option(ReplyOption.StrayPassiveExtended):
                    # extended marker information status
                    # 4-bits / stray marker
                    # reply size = (number of markers)/2, rounded up to the nearest integer
                    reply_size = math.ceil(self.num_markers / 2)
                    for b in range(reply_size):
                        marker_status_byte = unpack_uint(buffer, 1)
                        self.data[b*2].extended_marker_status = (marker_status_byte >> 4) & 0x0F
                        self.data[b*2+1].extended_marker_status = marker_status_byte & 0x0F

    def get_marker(self, index):
        """ Obtain the desired stray passive marker """
        try:
            return self.data[index]
        except IndexError as err:
            raise NDError(NDStatusCode.USE_ERROR, f"Invalid index ({index}) specified", self) from err


class BXSystemStatus(BXComponent):
    """ Contains System Status

    BX System Status
        System Status   - 2 bytes

        bit 0   System communication syncronization error
        bit 1   reserved
        bit 2   reserved
        bit 3   Recoverable system processing exception
        bit 4   reserved
        bit 5   reserved
        bit 6   Some port handle has become occupied
        bit 7   Some port handle has become unoccupied
        bit 8   Diagnostic pending
        bit 9   Temperature. System is not within operating temperature range
        bit 10  Hardware configuration changed
        bit 11  reserved
        bit 12  reserved
        bit 13  reserved
        bit 14  reserved
        bit 15  reserved
    """
    def __init__(self, buffer):
        # initialize BX Component
        super().__init__(buffer)

    def __str__(self):
        out = ""
        if self.synch_error:
            out += "Synchronization Error\n"
        if self.processing_exception:
            out += "Processing Exception\n"
        if self.handle_occupied:
            out += "Handle Occupied\n"
        if self.handle_unoccupied:
            out += "Handle Unoccupied\n"
        if self.diagnostic_pending:
            out += "Diagnostic Pending\n"
        if self.temperature_warning:
            out += "Temperature outside operating range\n"
        if self.config_changed:
            out += "Hardware configuration changed\n"
        if self.ok:
            out += "OK\n"
        return out

    def parse(self, buffer):
        # System Status - 2 bytes
        self.data = unpack_uint(buffer, 2)

    @property
    def status(self):
        return self.data

    def is_status(self, status):
        return (self.status & status) > 0

    @property
    def ok(self):
        return self.data == 0

    @property
    def synch_error(self):
        return self.is_status(SystemStatus.SynchError)

    @property
    def processing_exception(self):
        return self.is_status(SystemStatus.ProcessingException)

    @property
    def handle_occupied(self):
        return self.is_status(SystemStatus.HandleOccupied)

    @property
    def handle_unoccupied(self):
        return self.is_status(SystemStatus.HandleUnoccupied)

    @property
    def diagnostic_pending(self):
        return self.is_status(SystemStatus.Diagnostic)

    @property
    def temperature_warning(self):
        return self.is_status(SystemStatus.Temperature)

    @property
    def config_changed(self):
        return self.is_status(SystemStatus.ConfigChange)
