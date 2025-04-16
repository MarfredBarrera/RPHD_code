# reply.py
# NDI Combined API Reply

# import standard python libraries
from copy import copy

# import CAPI
from ndtrack.capi.error import WarningText, ErrorText
from ndtrack.capi.bx import *
from ndtrack.capi.gbf import *


class CAPIReply(ABC):
    """ Reply obtained from NDI CAPI System """

    def __init__(self, response):
        """ CAPIReply will parse a response from the NDI tracking system, producing a parsed object of the
        appropriate type in self.data

        Args:
            response: data received from the NDI tracking system
        """
        # by default, assume error until the response is not properly parsed. Set status to Error
        self.status = NDStatusError()

        if isinstance(response, bytes):
            # the parsing functions expect a bytearray
            # bytearrays are mutable objects and will thus be affected
            byte_data = bytearray(response)
        elif isinstance(response, bytearray):
            byte_data = response
        elif isinstance(response, str):
            byte_data = response
        else:
            raise NDError(NDStatusCode.USE_ERROR, "Data in the format provided is not supported", self)

        # each CAPIReply subclass must override the `parse` function and store data into self.data
        self.data = None
        self.parse(byte_data)

    def __str__(self):
        # self.data contains the parsed response
        return f"{self.status}: {self.data}"

    def is_ok(self):
        """ indicates if the reply is OK """
        return self.status.is_ok()

    def is_warning(self):
        """ indicates if the reply results in a WARNING """
        return self.status.is_warning()

    def is_error(self):
        """ indicates an error in the reply """
        return self.status.is_error()

    @property
    def error_code(self):
        return self.status.code

    @abstractmethod
    def do_parse(self):
        """ Perform parsing for the specific reply
            CAPIReply subclasses must override the `do_parse` function
        """
        pass

    def parse(self, response):
        """ Parse the reply response
            Check for error and if not error, perform reply specific parsing
        """
        if isinstance(response, str):
            # by default, store the reply's data as the response without the CRC16
            self.data = response[:-5]

            # if the reply is `ERROR`, parse the error and return
            if self.data.startswith("ERROR"):
                code = self.data[5:7]
                error_msg = ErrorText[code]
                logging.error(f"ERROR {code}: {error_msg}")
                self.status = NDStatusError(code, error_msg)
                return
        else:
            self.data = response

        # perform the reply specific parsing
        # CAPIReply subclasses must override the `do_parse` function
        self.do_parse()


class ASCIIReply(CAPIReply, ABC):
    """ CAPI reply in ascii format
        ASCII replies are formatted in the general ASCII format:
            <DATA><CRC16<CR>

        Before calling do_parse(), self.data contains the system response without the CRC16
    """
    pass


class OKAYReply(ASCIIReply, ABC):
    """ Reply obtained from the system where OKAY is expected
        OKAY<CRC16><CR>
    """

    def do_parse(self):
        # ASCIIReply self.data contains the response without the CRC16
        if self.data == "OKAY":
            self.status = NDStatusOK()


class OKAYWARNReply(ASCIIReply, ABC):
    """ Reply obtained from the system where OKAY or WARNING is expected
        OKAY <CRC16><CR>
        or
        WARNINGxx<CRC16><CR> (where xx = warning code)
    """

    def do_parse(self):
        # ASCIIReply self.data contains the response without the CRC16
        if self.data.startswith("OKAY"):
            self.status = NDStatusOK()
        elif self.data.startswith("WARNING"):
            # WARNING response contains a warning code
            code = self.data[7:9]
            self.status = NDStatusWarning(code, WarningText[code])


class BINReply(CAPIReply, ABC):
    """ CAPI reply in binary format
        Binary replies are formatted in the GeneralBinaryFormat
    """

    def __init__(self, response):
        """ CAPI Binary replies contain a start sequence, reply length, header CRC and data CRC

        Args:
            response: data received from device in response to a command
        """
        super().__init__(response)

        self.start_sequence = None
        self.reply_len = 0
        self.header_crc = None
        self.data_crc = None

    def parse_header(self, buffer):
        """ Parse the header of the binary reply to determine the exact reply format

        Args:
            buffer: header of data received from device

        Returns:
            OK status if header is successfully parsed
        """
        # read the start sequence, which describes the format of the header
        #   Reply length  2 Bytes
        #   Header CRC    2 Bytes
        #   Reply Length  4 Bytes
        try:
            self.start_sequence = unpack_int(buffer)
        except AttributeError as err:
            raise NDError(NDStatusCode.COM_ERROR, f"Unable to parse response buffer {buffer}", self) from err

        if self.start_sequence == ND_BIN_STARTSEQ:
            # Found standard binary start sequence
            self.reply_len = unpack_int(buffer)
            self.header_crc = unpack_int(buffer)
        elif self.start_sequence == ND_BIN_STARTSEQ_EXT:
            # Found extended binary start sequence
            self.reply_len = unpack_int(buffer, 4)
        else:
            self.status = NDStatusError("Response start sequence is not recognized")
            raise NDError(NDStatusCode.SYSTEM_ERROR, "Response start sequence is not recognized", self)

        return NDStatusOK()

    def parse_footer(self, buffer):
        """ Parse the footer of the binary reply. That includes the data CRC, depending on the format

        Args:
            buffer: footer of data received from device.

        Returns:
            OK status if footer is successfully parsed
        """
        # read the data CRC, if required
        if self.start_sequence == ND_BIN_STARTSEQ:
            # if the reply is in standard binary format, a data CRC is included
            #   Data CRC      2 Bytes
            self.data_crc = unpack_int(buffer)

        return NDStatusOK()


class ReplyBEEP(ASCIIReply):
    """ Reply obtained from BEEP command
        <Beep Status><CRC16><CR>
    """

    def do_parse(self):
        # ASCIIReply self.data contains the response without the CRC16
        if self.data.startswith("1"):
            # success
            self.status = NDStatusOK()
        elif self.data.startswith("0"):
            # system is busy beeping
            self.status = NDStatusWarning()


class ReplyBX(BINReply):
    """ Reply obtained from BX command

        <Start Sequence><Reply Length><Header CRC><01 (Number of Handles)>
        <Handle 1><Handle 1 Status><Reply Opt 0001 Data>...<Reply OPt 0008 Data>
        ...
        <Handle n><Handle n Status><Reply Opt 0001 Data>...<Reply Opt 0008 Data>
        <Reply Option 1000 Data>
        <System Status><CRC16>
    """
    def __init__(self, response, options=0x0001):
        # store options selected for use during parsing
        self._options = options

        super().__init__(response)

    def do_parse(self):
        # copy the response data
        buffer = copy(self.data)

        # parse the BX response
        self.parse_header(buffer)
        self.data = BX(buffer, self._options)
        self.parse_footer(buffer)

        # success
        self.status = NDStatusOK()


class ReplyBX2(BINReply):
    """ Reply obtained from BX2 command

        <Start Sequence><2 byte Reply Length>
            <Header CRC><GBF Version> <Component Count><Frame Component 1>...<Frame Component N><Data CRC>
        OR
        <Extended Binary Start Sequence><4 byte Reply Length>
            <GBF Version><Component Count><Frame Component 1>...<Frame Component N>
    """

    def do_parse(self):
        # copy the response data
        buffer = copy(self.data)

        # parse the general binary response
        self.parse_header(buffer)
        self.data = GeneralBinaryPayload(buffer)
        self.parse_footer(buffer)

        # success
        self.status = NDStatusOK()


class ReplyCOMM(OKAYReply):
    """ Reply obtained from COMM command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyDFLT(OKAYReply):
    """ Reply obtained from DFLT command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyDSTART(OKAYReply):
    """ Reply obtained from DSTART command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyDSTOP(OKAYReply):
    """ Reply obtained from DSTOP command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyECHO(ASCIIReply):
    """ Reply obtained from ECHO command
        <echo of command><CRC16<CR>
    """

    def __init__(self, response, expected):
        # store the command sent
        self._expected = expected
        super().__init__(response)

    def do_parse(self):
        # ASCIIReply self.data contains the response without the CRC16
        # the response must be an echo of the command
        if self.data.startswith(self._expected):
            # success
            self.status = NDStatusOK()
        else:
            logging.error(f"ECHO expecting '{self._expected}' but received '{self.data}'")


class ParametersReply(ASCIIReply, ABC):
    """ Reply obtained from GET or GETINFO commands

        <User Parameter Name>=<info><LF> (for each parameter)
        <CRC16><CR>
    """

    def do_parse(self):
        # ASCIIReply self.data contains the response without the CRC16

        # copy the response data
        buffer = copy(self.data)

        # parse the responses.
        # dictionary containing <User Parameter Name>=<value> pairs
        self.data = {}
        # start index for the next user parameter
        start = 0

        # search the buffer for `=`, which separates the <User Parameter Name> and <value>
        sep = buffer.find('=', start)
        while sep > 0:
            # <User Parameter Name>
            user_parameter = buffer[start:sep]
            # find the <LF>
            next_item_idx = buffer.find('\n', sep)
            if next_item_idx > 0:
                # found <LF>
                value = buffer[sep + 1:next_item_idx]

                # find the next instance of `=`
                start = next_item_idx + 1
                sep = buffer.find('=', start)
            else:
                # did not find <LF>. This is the last parameter.
                value = buffer[sep + 1:]

                # all parameters have been parsed
                sep = 0

            # add <User Parameter Name>:<Value> to the dictionary
            self.data[user_parameter] = value

        # success
        self.status = NDStatusOK()


class ReplyGET(ParametersReply):
    """ Reply obtained from GET command
        <User Parameter Name>=<value><LF> (repeated for each user parameter name, but no LF after the last parameter)
        <CRC16><CR>
    """
    pass


class ReplyGETINFO(ParametersReply):
    """ Reply obtained from GETINFO command
        <User Parameter Name>=<Value>;<Type>;<Attribute>;<Minimum>;<Maximum>;<Enumeration>;<Description><LF>
        (repeated for each user parameter, but no LF after last parameter)
        <CRC16><CR>
    """
    pass


class ReplyGETLOG(BINReply):
    """ Reply obtained from GETLOG command
        response is in the generic binary format
        <Header><Length><Header CRC><Data><Data CRC>
    """

    def do_parse(self):
        # copy the response data
        buffer = copy(self.data)

        # parse the general binary response
        self.parse_header(buffer)
        # data
        self.data = unpack_char(buffer, self.reply_len)
        # data CRC
        self.parse_footer(buffer)

        # success
        self.status = NDStatusOK()


class ReplyINIT(OKAYWARNReply):
    """ Reply obtained from INIT command
        Reply is OKAY or ERROR or WARNING06. Use OKAYWARNReply
    """
    pass


class ReplyIRATE(OKAYReply):
    """ Reply obtained from IRATE command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyIRED(OKAYReply):
    """ Reply obtained from IRED command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyLED(OKAYReply):
    """ Reply obtained from LED command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyPDIS(OKAYReply):
    """ Reply obtained from PDIS command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyPENA(OKAYWARNReply):
    """ Reply obtained from PENA command
        Reply is OKAY or WARNING or ERROR. Use OKAYWARNReply
    """
    pass


class ReplyPFSEL(OKAYReply):
    """ Reply obtained from PFSEL command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyPHF(OKAYReply):
    """ Reply obtained from PHF command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyPHINF(OKAYReply):
    """ Reply obtained from PHINF command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyPHRQ(ASCIIReply):
    """ Reply obtained from PHRQ command
        <Port Handle><CRC16><CR>
    """

    def do_parse(self):
        # ASCIIReply self.data contains the response without the CRC16
        buffer = list(self.data)
        # self.data contains ph_id
        self.data = ascii_to_hex(buffer)

        # success
        self.status = NDStatusOK()


class ReplyPHSR(ASCIIReply):
    """ Reply obtained from PHSR command
        2 hex characters    Number of port handles
        for each port handle
            2 hex characters    Port Handle
            3 hex characters    Port Handle Status

        self.data will contain a list of tuples (port_handle, port_handle_status) if size num_port_handles
    """

    def do_parse(self):
        buffer = list(self.data)
        self.data = []
        # 2 hex characters  Number of port handles
        num_ph = ascii_to_hex(buffer)

        for ph in range(num_ph):
            # 2 hex characters  Port Handle ID
            port_handle = ascii_to_hex(buffer)
            # 3 hex characters  Port Handle Status
            status = ascii_to_hex(buffer, 3)
            self.data.append((port_handle, status))

        # success
        self.status = NDStatusOK()


class ReplyPINIT(OKAYWARNReply):
    """ Reply obtained from PINIT command
        Reply is OKAY of WARNING or ERROR. Use OKAYWARNReply
    """
    # deprecated
    pass


class SROMDataReply(ASCIIReply, ABC):
    """ Reply obtained from one of the SROM read commands (PPRD, PURD)
        Reply is 64 bytes of data (128 hexadecimal characters)
    """

    def do_parse(self):
        buffer = copy(self.data)

        # 64 hex characters  Number of port handles
        self.data = bytearray()
        for i in range(64):
            self.data.append(buffer[i])

        # success
        self.status = NDStatusOK()


class ReplyPPRD(SROMDataReply):
    """ Reply obtained from PPRD command
        Reply is SROM Data. Use SROMDataReply
    """
    pass


class ReplyPPWR(OKAYReply):
    """ Reply obtained from PPWR command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyPSEL(OKAYReply):
    """ Reply obtained from PSEL command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyPSRCH(ASCIIReply):
    """ Reply obtained from PSRCH command
        Reply is a list of valid SROM device IDs for the specified wired tool or GPIO device
        <Number of SROM devices><SROM device 1 ID><SROM device 2 ID>...<SROM device 7 ID><CRC16><CR>
    """

    def do_parse(self):
        buffer = copy(self.data)

        # 1 character - number of SROM devices
        num_devices = int(buffer[0])

        devices = []
        device_start = 1
        for dev in range(num_devices):
            device_end = device_start + 16
            devices.append(buffer[device_start:device_end])
            device_start = device_end + 1

        self.data = (num_devices, devices)

        # success
        self.status = NDStatusOK()


class ReplyPURD(SROMDataReply):
    """ Reply obtained from PURD command
        Reply is SROM Data. Use SROMDataReply
    """
    pass


class ReplyPUWR(OKAYReply):
    """ Reply obtained from PUWR command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyPVWR(OKAYReply):
    """ Reply obtained from PVWR command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyRESET(ASCIIReply):
    """ Reply obtained from RESET command
        RESET<CRC16><CR>
    """

    def do_parse(self):
        # ASCIIReply self.data contains the response without the CRC16
        if self.data.startswith("RESET"):
            self.status = NDStatusOK()


class ReplySAVE(OKAYReply):
    """ Reply obtained from SAVE command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplySET(OKAYReply):
    """ Reply obtained from SET command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplySTREAM(OKAYReply):
    """ Reply obtained from STREAM command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplySYSLOG(OKAYReply):
    """ Reply obtained from SYSLOG command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyTCTST(ASCIIReply):
    """ Reply obtained from TCTST command
        Reply is 2 hexadecimal characters per marker containing the electrical current of the markers
        <Marker A Current><Marker B Current>...<Marker T Current><CRC16><CR>
    """

    def do_parse(self):
        buffer = list(self.data)

        # markers are labeled A to T
        markers = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T"]
        self.data = []
        for _ in markers:
            self.data.append(ascii_to_hex(buffer))

        # success
        self.status = NDStatusOK()


class ReplyTSTART(OKAYReply):
    """ Reply obtained from TSTART command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyTSTOP(OKAYReply):
    """ Reply obtained from TSTOP command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyTTCFG(OKAYReply):
    """ Reply obtained from TTCFG command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyUSTREAM(OKAYReply):
    """ Reply obtained from USTREAM command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyVCAP(BINReply):
    """ Reply obtained from VCAP command
    Reply is General Binary
    """

    def do_parse(self):
        # if command specified to only capture the image and not return it
        if self.data == "OKAY":
            self.status = NDStatusOK()

        else:
            # copy the response data
            buffer = copy(self.data)

            # parse the general binary response
            self.parse_header(buffer)
            self.data = GeneralBinaryPayload(buffer)
            self.parse_footer(buffer)

            # success
            self.status = NDStatusOK()


class ReplyVER(ASCIIReply):
    """ Reply obtained from VER command
        options:
            0 - System Control Processor
            1 - Reserved
            2 - Reserved
            3 - System Control Unit Processor, only supported by hybrid systems
            4 - System Control Unit Processor, with enhanced revision numbering

        options 0, 3, 4:
        <Type of Firmware><LF>
        <NDI Serial Number><LF>
        <Characterization Date><LF>        (only for option 0 and 4)
        <Freeze Tag><LF>
        <Freeze Date><LF>
        <Copyright Information><LF>
        <CRC16><CR>

        option 5:
        <Combined Firmware Revision>
    """

    def __init__(self, response, option=-1):
        # valid options
        if option not in [0, 3, 4, 5]:
            raise NDError(NDStatusCode.USE_ERROR, f"Invalid option sent to VER command ({option})", self)

        # store option selected for use during parsing
        self._option = option

        super().__init__(response)

    def do_parse(self):
        buffer = copy(self.data)

        # Dictionary of (token, value)
        self.data = {}

        if self._option == 5:
            # Reply option 5 contains different information
            # <combined firmware rev>
            # Combined Firmware Revision
            self.data["combined_firmware"] = buffer[:3]
        else:
            if self._option == 0 or self._option == 4:
                tokens = ["fw_type", "serial_number", "char_date", "freeze_tag", "freeze_date", "copyright"]
            elif self._option == 3:
                tokens = ["fw_type", "serial_number", "freeze_tag", "freeze_date", "copyright"]
            else:
                raise NDError(NDStatusCode.USE_ERROR, f"Invalid option sent to VER command ({self._option})")

            start = 0
            for token in tokens:
                end = buffer.find('\n', start)
                self.data[token] = buffer[start:end]
                start = end + 1

        # success
        self.status = NDStatusOK()


class ReplyVGET(BINReply):
    def do_parse(self):
        # copy the response data
        buffer = copy(self.data)

        # parse VGET header
        self.start_sequence = unpack_int(buffer)
        self.reply_len = unpack_int(buffer)
        self.header_crc = unpack_int(buffer)

        # parse the general binary response
        self.data = unpack_bytes(buffer, int(self.reply_len))
        # data CRC
        self.parse_footer(buffer)
        # success
        self.status = NDStatusOK()


class ReplyVSEL(OKAYReply):
    """ Reply obtained from VSEL command
        Reply is OKAY or ERROR. Use OKAYReply
    """
    pass


class ReplyVSNAP(ASCIIReply):
    """ Reply obtained from VSNAP command
        Frame Number            8 hexadecimal characters
        Number of Frames        2 hexadecimal characters
        Number of Sensors       2 hexadecimal characters
        for each frame,
            Frame Type          2 hexadecimal characters
            for each sensor,
                Exposure Time   4 hexadecimal characters
    """
    def do_parse(self):
        # ASCIIReply self.data contains the response without the CRC16
        buffer = list(self.data)

        # 8 hex characters  Frame Number
        frame_number = ascii_to_hex(buffer, 8)

        # 2 hex characters  Number of frames
        num_frames = ascii_to_hex(buffer, 2)
        # 2 hex characters  Number of sensors
        num_sensors = ascii_to_hex(buffer, 2)

        # for each frame, get the frame information
        frames_data = []
        for frame in range(num_frames):
            frame_type = ascii_to_hex(buffer, 2)

            # each frame contains exposure time for each sensor
            exposure_times = []
            for sensor in range(num_sensors):
                exposure_times.append(ascii_to_hex(buffer, 4))

            frames_data.append((frame_type, exposure_times))

        # self.data contains
        # frame_number      frame number for captured image
        # frames_data       array of data for each frame. Each frame contains: (frame_type, exposure_times))
        #   frame_type      type of data for this frame (defined in Cmd.VSnap.Frame Types)
        #   exposure_times  array of exposure times for each sensor
        self.data = (frame_number, frames_data)

        # success
        self.status = NDStatusOK()


def main():
    # set up to log everything
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s : %(levelname)s : %(message)s')

    reply = ReplyBX(sample_bx)
    print(reply)

    sample_data = [sample_6d, sample_6d_alert, sample_3d, sample_1d, from_system]
    for response in sample_data:
        # display the response in string format
        # convert each byte into its hexadecimal representation
        response_str = ""
        for b in response:
            response_str += f"{b:02X} "
        print(response_str)

        # parse the BX2 reply
        reply = ReplyBX2(response)
        print(reply)

    replies = [ReplyVER(ver_response_4, 4),
               ReplyVER(ver_response_5, 5)]
    for r in replies:
        print(r)


if __name__ == "__main__":
    main()
