# NDConnection.py
# NDConnection python class
# NDConnection is a generic connection method for communication with devices

# import standard libraries
from abc import ABC, abstractmethod

# import ndtrack
from ndtrack.ndtypes.NDError import *


class NDConnection(ABC):
    """ abstract class defining a connection to a device """

    @abstractmethod
    def connect(self):
        """ connect to the device """
        return False

    @abstractmethod
    def is_connected(self):
        """ indicates if connection is open """
        return False

    def assert_is_connected(self):
        """ ensure that the connection is open """
        if not self.is_connected():
            raise NDError(NDStatusCode.USE_ERROR, 'Device is not connected', self)

    @abstractmethod
    def close(self):
        """ close the connection to the device """
        return False

    @abstractmethod
    def send(self, data):
        """
        send data through the connection

        Parameters:
        data: data to be sent
        """
        return False

    @abstractmethod
    def recv(self, num_bytes):
        """
        receive data from the connection

        Parameters:
        num_bytes: number of bytes to read from the connection

        Returns:
        data: data received from the connection
        """
        return False
