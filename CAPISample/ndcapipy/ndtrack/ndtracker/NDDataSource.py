# NDDataSource.py
# Definition of NDDataSource python class
# An NDDataSource is a generic source of data and contains basic functionality.
# Specific data sources include trackers (Optotrak, Vega, etc.) and data files

# import standard libraries
from abc import abstractmethod, ABC
import configparser
import logging

# import ndtrack libraries
from ndtrack.ndtypes.NDError import *
from ndtrack.ndtracker.NDEvent import *


class NDDataSource(ABC):
    """ NDDataSource
        A source of data used by NDI.
        Examples of data sources are NDI tracking systems, data files,
        third party devices.
        NDI data sources inherit from this class.
    """
    def __init__(self):
        # subclasses should specify the values for these variables
        self.name = "NDDataSource"                  # data source name
        self._status = NDStatusOK()                 # system status is OK

        # data
        self.frame_num = 0                          # frame number
        self.num_3D = 0                             # number of 3D objects
        self.data_3D = []                           # NDPosition 3D data objects

        # status variables
        self._is_connected = False                  # is data source connected
        self._is_initialized = False                # is data source initialized

        # list of listeners to events
        self._event_listeners = []                  # event listeners will be invoked when a generic event occurs

        # configuration
        self._config = configparser.ConfigParser()  # configuration (.ini)
        self._config.optionxform = str              # preserve case sensitivity for config options

    def __str__(self):
        """ string representation of NDDataSource
            An NDDataSource is displayed as <name> <version> (<state>)
        """
        return "{} ({})".format(self.name, self._get_state())

    def _get_state(self):
        """ string representation of the state of the NDDataSource """
        if self._is_initialized:
            return "Initialized"
        if self._is_connected:
            return "Connected"
        return "Idle"

    def _load_config(self):
        """ load configuration from file
            The configuration file for an NDDataSource subclass is "<name>.ini"
            where <name> is the name of the class as definded in self.name
        """
        try:
            self._config_file = self.name + ".ini"
            self._config.read(self._config_file)
        except Exception as err:
            raise NDError(f"Unable to read configuration file {self._config_file}", self) from err
        #if the _config.read() call does not find a file, it will not throw an exception.
        if self._config.sections() == []:
            logging.warning("WARNING: no .ini file was found.")


    def publish_event(self, event_id, msg=""):
        """ event handler
            send the specified event to all registered listeners
        """
        ev = NDEvent(self, event_id, msg)
        for f in self._event_listeners:
            f(ev)

    #####################################################################
    # NDDataSource abstract methods.
    # NDDataSource subclasses must override these functions

    @abstractmethod
    def _do_connect(self):
        """ Abstract method _do_connect
            Perform connection to data source.
            Subclasses must override `_do_connect`
            to connect to the data source
        """
        pass

    @abstractmethod
    def _do_initialize(self):
        """ Abstract method _do_initialize
            Perform data source initializaiton.
            Subclasses should override `_do_initialize`
            to perform data source initialization.
        """
        pass

    @abstractmethod
    def _do_disconnect(self):
        """ Abstract method _do_disconnect
            Perform disconnection from the data source.
            Subclasses must override `_do_disconnect`
            to disconnect from the data source.
        """
        pass

    #####################################################################
    # NDDataSource configuration methods

    def set(self, option, value):
        """ NDDataSource set
        Set the specified value to the indicated option
        [<Device Section>]
        option = value

        Args:
            option: key whose value is to be set
            value: value to which the key is set
        """
        self._config.set(self.name, option, value)

    def get(self, option, default=""):
        """ NDDataSource get
        Get the value of the indicated option
        [<Device Section>]
        option = value

        Args:
            option: key whose value is being queried
            default: default value to use if the option is not stored in the main device section

        Returns:
            the value of option in the main device section. if option is not found, return the default value
        """
        try:
            value = self._config.get(self.name, option)
        except configparser.Error:
            # if the configuration file is not found or if the configuration section is not found, an exception occurs
            # use the default value
            value = default

        return value

    #####################################################################
    # NDDataSource actions.
    # Available actions for all NDDataSource subclasses

    def connect(self):
        """ NDDataSource connect
            connect is used to connect to the data source.
            Update data source state to connected but not initialized.
            Subclasses must implement `_do_connect` to perform connection
        """
        # perform connection to data source
        # NDDataSource subclasses must override `_do_connect`
        try:
            self._do_connect()
        except NDError as err:
            raise NDError(err.code, f"Error connecting to {self.name}", self) from err

        # update state to `connected` and 'not initialized'
        self._is_connected = True
        self._is_initialized = False
        self.publish_event(NDEventCode.CONNECTED, "{} connected".format(self.name))
        return True

    def assert_is_connected(self):
        """ Confirm that the data source is connected and raise an exception if it is not """
        if not self.is_connected():
            raise NDError(NDStatusCode.USE_ERROR, "{} is is not connected".format(self.name), self)
        return True

    def disconnect(self):
        """ NDDataSource disconnect
            disconnect is used to detach from the data source.
            Update data source state to disconnected.
            Subclasses must implement `_do_disconnect` to perform disconnect
        """
        # if not connected, there is nothing to do
        if not self.is_connected():
            return True

        # update state to 'not initialized' and 'not connected'
        self._is_connected = False
        self._is_initialized = False
        self.publish_event(NDEventCode.DISCONNECT, "{} disconnected".format(self.name))

        # perform disconnection from data source
        # NDDataSource subclasses must override `_do_disconnect`
        try:
            self._do_disconnect()
        except NDError as err:
            raise NDError(err.code, f"Error disconnecting from {self.name}", self) from err

    def initialize(self):
        """ NDDataSource initialize
            initialize is used to set up the data source after it is connected.
            Subclasses must implement `_do_initialize` to perform initialization
        """
        self.assert_is_connected()

        try:
            # if the system is not connected, it cannot be initialized at this time
            # perform initialization of data source
            # NDDataSource subclasses must override `_do_initialize`
            self._do_initialize()
        except NDError as err:
            raise NDError(err.code, f"Error initializing {self.name}", self) from err

        # update state to 'initialized'
        self._is_initialized = True
        self.publish_event(NDEventCode.INITIALIZE, "{} initialized".format(self.name))
        return True

    def add_event_listener(self, cb):
        """ Add an event listener.
            Event listeners will be called whenever an event occurs
        """
        self._event_listeners.append(cb)

    #####################################################################
    # NDDataSource state functions

    def is_connected(self):
        """ Indicate if the data source is Connected """
        return self._is_connected

    def is_initialized(self):
        """ Indicate if the data source has been initialized """
        return self._is_initialized
