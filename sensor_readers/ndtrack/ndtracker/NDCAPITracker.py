# NDCAPITracker.py
# NDCAPITracker python class
# NDCAPITracker is an NDTracker that communicates with a Combined API Tracking System

# import standard libraries
from socket import timeout

# import ndtrack
from ndtrack.comm.NDSerial import NDSerial
from ndtrack.comm.NDSocket import NDSocket
from ndtrack.ndtracker.NDTracker import *
from ndtrack.ndtracker.NDEvent import *
from ndtrack.capi.devices import CAPIDevices
from ndtrack.capi.reply import *


class NDCAPITracker(NDTracker, ABC):
    """ NDCAPITracker is an NDTracker that communicates using NDI Combined API
        Trackers that use Combined API include
        Polaris (Spectra, Vicra, Vega) and Aurora

        CAPI Trackers communicate using either socket or serial connection
        The CAPI protocol contains ASCII and Binary components
    """

    def __init__(self):
        super().__init__()                      # initialize as NDTracker
        self.name = "NDCAPITracker"             # default CAPITracker name
        self._connection = None                 # NDConnection to tracker
        self._devices = CAPIDevices(self)       # devices used by this tracker
        self._num_wireless_tools = 0            # number of wireless tools

    @property
    def num_devices(self):
        return len(self._devices)

    #####################################################################
    # NDI Combined API implementation of NDTracker
    # override NDTracker functions specific for CAPITracker

    def _do_connect(self):
        """ @override NDDataSource::_do_connect
            Connect to Combined API tracker.
            Use previously specified connection.
        """
        # ensure that the connection has been previously specified
        if self._connection is None:
            raise NDError(NDStatusCode.USE_ERROR, "Connection not specified", self)

        # open a connection to the system
        self.publish_event(NDEventCode.CONNECTING, f"{self.name} connecting to {self._connection}")
        try:
            return self._connection.connect()
        except NDError as err:
            raise NDError(err.code, f"Unable to establish connection to {self.name}", self) from err

    def _do_reset(self):
        """ @override NDTracker::_do_reset
            Reset the Combined API tracker.
        """
        # remember if the system was previously initialized
        was_initialized = self.is_initialized()

        try:
            # send `RESET ` command and parse the response
            response = self.send_command('RESET ')
            reply = ReplyRESET(response)
        except NDError as err:
            raise NDError(err.code, f"Error resetting {self.name}. Unable to send RESET", self) from err

        if reply.is_error():
            raise NDError(NDStatusCode.SYSTEM_ERROR, f"Error resetting {self.name}. RESET returned {reply.status.code}", self)

        # reset completed successfully
        if was_initialized:
            # re-initialize the system
            return self.initialize()
        else:
            # success
            return True

    def _do_initialize(self):
        """ @override NDDataSource::_do_initialize
            Initialize the tracker and activate device ports
        """
        try:
            # send `INIT ` command and parse the response
            response = self.send_command('INIT ')
            reply = ReplyINIT(response)
        except NDError as err:
            raise NDError(NDStatusCode.SYSTEM_ERROR, f"Error initializing {self.name}. Unable to send INIT", self) from err

        if reply.is_error():
            raise NDError(NDStatusCode.SYSTEM_ERROR, f"Error initializing {self.name}. INIT returned {reply.status.code}", self)

        # activate ports
        try:
            # free unused devices
            self._devices.free()

            # load wired tools before attempting to load wireless tools
            self._devices.load_and_initialize_wired(self._config)

            # load wireless tools
            try:
                self._num_wireless_tools = self._config.getint(self.name, 'WirelessTools')
            except configparser.Error:
                # 'WirelessTools' section not found in config file
                self._num_wireless_tools = 0

            wireless_sroms = []
            for tool in range(self._num_wireless_tools):
                srom = self._config.get("WirelessTool_{:02}".format(tool + 1), "srom")
                wireless_sroms.append(srom)
            self._devices.load_wireless(wireless_sroms)

            # initialize new devices
            self._devices.initialize()

            # enable all devices
            self._devices.enable()
        except NDError as err:
            raise NDError(err.code, "Error initializing {}. Unable to activate ports.".format(self.name), self) from err

    def _do_start_tracking(self):
        """ @override NDTracker::_do_start_tracking
            Start tracking mode
        """
        # send TSTART command
        response = self.send_command("TSTART ")
        reply = ReplyTSTART(response)
        return reply.is_ok()

    def _do_stop_tracking(self):
        """ @override NDTracker::_do_stop_tracking
            Stop tracking mode
        """
        # send TSTOP command
        response = self.send_command("TSTOP ")
        reply = ReplyTSTOP(response)
        return reply.is_ok()

    def _do_disconnect(self):
        """ @override NDTracker::_do_disconnect
            Close the connection to the tracker
        """
        # close the connection
        return self._connection.close()

    #####################################################################
    # Communication methods.
    # Implement NDI Combined API protocol.

    def send_command(self, command, wait_for_response=True):
        """ Send a command to the connected device and return the response

            Parameters:
            command (string): The command to send
            wait (bool): Indicates wether to wait for the response

            Returns:
            response (string): The response received from the system
        """
        # send the command
        logging.log(NDLogLevel.Communications, f"> {command}")
        # append end of line delimiter, if necessary
        if command[-1] != '\r':
            command += '\r'

        # send the command via the established connection
        response = None
        with self._comm_lock:
            try:
                self._connection.send(command)
            except NDError as err:
                raise NDError(err.code, f"Error sending command: {command}", self) from err

            # receive the response
            if wait_for_response:
                try:
                    response = self.receive_response()
                except NDError as err:
                    raise NDError(err.code, "Response not available", self) from err

        if type(response) == bytearray:
            logging.log(NDLogLevel.Communications, f"< {len(response)} bytes")
        else:
            logging.log(NDLogLevel.Communications, f"< {response}")
        return response

    def receive(self, num_bytes):
        """ Receive specified number of bytes from the established connection

            Parameters:
            num_bytes (int): The number of bytes to receive
        """
        # receive the specified number of bytes from the established connection
        return self._connection.recv(num_bytes)

    def get_log_response(self):
        """ Receive get log response from the connected device """
        # buffer contains the data received from the device
        buffer = bytearray()

        # receive all header, length, and header CRC
        buffer.extend(bytearray(self.receive(6)))
        while True:
            try:
                data = bytearray(self.receive(1))
            except timeout:
                # if the connection times out there is no more data to read
                break

            # add the newly received data to the data buffer
            buffer.extend(data)

        return ReplyGETLOG(buffer)

    def receive_response(self):
        """ Receive response from the connected device """
        # buffer contains the data received from the device
        buffer = bytearray()

        # continue reading data until a complete response is received
        # if the data is in ascii, a complete response ends in '\r'
        # if the data is in binary, header specifies the length of the response
        while True:
            # receive data from the system
            try:
                data = bytearray(self.receive(1))
            except timeout:
                # if the connection times out,
                # try again since we are expecting a response
                continue

            # add the newly received data to the data buffer
            buffer.extend(data)

            # all messages contain a minimum of 2 bytes (CRC16)
            if len(buffer) < 2:
                continue

            # if the data received is '\r' (ascii code 13), it indicates the end of an ascii message
            if buffer[-1] == 13:
                # ASCII message received
                ascii_response = buffer.decode("ascii")
                return ascii_response

            elif buffer[1] == 0xA5 and buffer[0] == 0xC4:
                # Generic binary response received. Starts with sequence A5C4
                # all binary data is formatted in little endian
                # A5C4llllccccd..dCCCC
                # where A5C4 is the start sequence      (2 bytes)
                #       llll is the response length n   (2 bytes)
                #       cccc is the response CRC16      (2 bytes)
                #       d..d is the response data       (n bytes)
                #       CCCC is the data CRC16      (2 bytes)

                # receive the header (data length and header CRC16)
                buffer.extend(bytearray(self.receive(4)))
                data_length = (buffer[3] << 8) + buffer[2]
                sleep(0.0001)
                # receive the complete message data length
                buffer.extend(self.receive(data_length))
                # receive the data CRC
                buffer.extend(self.receive(2))
                return buffer

            elif buffer[1] == 0xA5 and buffer[0] == 0xC8:
                # Extended binary response received. Starts with sequence A5C8
                # all binary data is formatted in little endian
                # A5C8lllllllld..d
                # where A5C8 is the start sequence      (2 bytes)
                #       llllllll is the data length n   (4 bytes)

                # receive the header (data length)
                buffer.extend(bytearray(self.receive(4)))
                data_length = (((((buffer[5] << 8) + buffer[4]) << 8) + buffer[3]) << 8) + buffer[2]

                # read the complete message
                received_total = 0
                while received_total < data_length:
                    receive_data = self.receive(data_length)
                    received_total += len(receive_data)
                    buffer.extend(receive_data)

                return buffer

            elif buffer[1] == 0xB5 and buffer[0] == 0xD4:
                # Stream binary response received. Starts with sequence D4B5
                # all binary data is formatted in little endian
                # D4B5lllls...scccc
                # where D4B5 is the little endian representation of the BX Stream messsage
                #       llll is the stream ID length (2 bytes)
                #       s..s is the Stream ID (n bytes)
                #       cccc is the header CRC16 (2 bytes)

                # receive stream ID length
                buffer.extend(bytearray(self.receive(2)))
                id_length = (buffer[3] << 8) + buffer[2]

                # receive ID and header CRC
                buffer.extend(bytearray(self.receive(id_length)))
                buffer.extend(bytearray(self.receive(2)))

                # clear the buffer and prepare to receive binary response
                buffer = bytearray()
                continue

    #####################################################################
    # NDCAPITracker actions

    def set_connection(self, connection):
        """ Specify the connection parameters
            The tracker can connect via Socket or Serial connection

            Parameters:
            connection (string) :   string specifying the connection
                                    connection to COM or /dev/ creates a serial connection
                                    connection to IP Address or Local Device name creates a socket connection
        """
        if connection.upper().startswith("COM") or connection.startswith("/dev/"):
            # COM Port has been specified, create a serial connection
            self._connection = NDSerial(connection)
        else:
            # This is a TCP connection, create a socket Connection
            # if the IP Address starts with a letter, append ".local" at the end, if not already included
            ip_address = connection
            if not ip_address[0].isdecimal() and ".local" not in ip_address:
                ip_address += ".local"
            # setup the connection to the specified IP Address, port 8765
            self._connection = NDSocket(ip_address, 8765)
