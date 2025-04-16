# NDSerial.py
# NDSerial python class
# NDSerial implements serial communication with NDI devices

# import standard libraries
import serial

# import comm
from ndtrack.comm.NDConnection import *


class NDSerial(NDConnection):
    """ NDSerial implements an NDConnection that communicates to devices
        using a serial port
    """

    def __init__(self, connection):
        """
        NDSerial initialization

        Parameters:
        connection (string): Connection information. Specifies COM Port
        """
        self._port = None
        self._com_port = None
        if connection.upper().startswith("COM") or connection.startswith("/dev/"):
            # set connection to use the specified COM Port
            self._com_port = connection

    def __str__(self):
        """ display serial connection information """
        return self._com_port

    def connect(self) -> bool:
        """ Open the connection to the device

        Returns:

        """
        try:
            self._port = serial.Serial(self._com_port, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=3000, rtscts=True, interCharTimeout=None)
        except Exception as err:
            raise NDError(NDStatusCode.COM_ERROR, f"Unable to connect to {self._com_port}", self) from err
        
        # Send a serial break
        self._port.send_break(0.25)
        # Wait for the reset response
        self._port.read(10)
        # connection completed successfully
        return True

    def is_connected(self) -> bool:
        """ Indicates if connection is established """
        return self._port is not None

    def close(self):
        """ Close the connection """
        if not self.is_connected():
            return

        self._port.close()
        self._port = None

    def send(self, data):
        """ Send the specified data to the device """
        self.assert_is_connected()
        self._port.write(data.encode("ascii"))

    def recv(self, num_bytes=32768):
        """ Receive data from the device """
        self.assert_is_connected()
        return self._port.read(num_bytes)
    
    def serialBreak(self):
        """ Send a serial break """
        self._port.send_break(0.25)
