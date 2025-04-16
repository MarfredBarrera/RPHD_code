# NDSocket.py
# NDSocket python class
# NDSocket implements socket communications with NDI devices

# import standard libraries
import socket
from ndtrack.comm.NDConnection import *


class NDSocket(NDConnection):
    """ NDSocket implements an NDConnection that communicates to devices
        using a TCP Socket
    """

    def __init__(self, ip_address, ip_port):
        """
        NDSocket initialization

        Parameters:
        connection (string): Connection information. Specifies IP Address
        """
        self._sock = None
        self._ip_address = ip_address
        self._ip_port = ip_port

    def __str__(self):
        """ display socket connection information """
        if self._sock is None:
            # socket is not connected. return IP address and port
            return "{}:{}".format(self._ip_address, self._ip_port)
        else:
            # socket is connected. return socket string
            return str(self._sock)

    def connect(self, num_retries=3):
        """ Open the connection to the device """
        if self.is_connected():
            # already connected, nothing else to do
            return True

        except_err = None
        for attempt in range(num_retries):
            try:
                # open socket using TCP streaming protocol
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.connect((self._ip_address, self._ip_port))

                # set timeout to an arbitrarily small value (1/4 seconds)
                self._sock.settimeout(0.25)
            except Exception as err:
                except_err = err
            else:
                # success
                break
        else:
            # failed after all retry attempts
            raise NDError(NDStatusCode.COM_ERROR, f"Error connecting {self._ip_address}:{self._ip_port}", self) \
                from except_err

        # connection completed successfully
        return True

    def is_connected(self):
        """ Indicates if connection is established """
        return self._sock is not None

    def close(self):
        """ Close the connection """
        if not self.is_connected():
            # not connected, nothing else to do
            return True

        # close the socket connection
        self._sock.close()
        self._sock = None

        # close completed successfully
        return True

    def send(self, data):
        """ Send the specified data to the device """
        self.assert_is_connected()
        self._sock.send(data.encode("ascii"))

    def recv(self, num_bytes=32768):
        """ Receive data from the device """
        self.assert_is_connected()
        return self._sock.recv(num_bytes)


class NDSocketUDP(NDSocket):
    def __init__(self, ip_port):
        """
        NDSocketUDP initialization

        Parameters:
        ip_port     port number where data is to be published
        """
        super().__init__("", ip_port)

    def connect(self, **kwargs):
        """ Connect to UDP device """
        # open a socket using UDP protocol
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.bind(("", self._ip_port))

        # set timeout arbitrarily to 1s
        self._sock.settimeout(1)

    def recv(self, num_bytes=32768):
        """ Receive data from the device """
        self.assert_is_connected()
        try:
            data, address = self._sock.recvfrom(num_bytes)
        except socket.timeout as err:
            raise NDError(NDStatusCode.TIMEOUT, f"Timeout receiving data from port:{self._ip_port}", self) from err
        else:
            return data
