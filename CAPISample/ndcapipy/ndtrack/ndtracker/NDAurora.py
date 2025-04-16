# NDAurora.py
# NDAurora python class
# NDAurora is an NDTracker that communicates with the Aurora Systems

from ndtrack.ndtracker.NDCAPITracker import *
from ndtrack.capi.reply import *
from ndtrack.datafile.NDDataFile6D import NDDataFile6D
from ndtrack.ndtracker.trackable.NDAuroraTool import NDAuroraTool

class NDAurora(NDCAPITracker, ABC):
    """ NDAurora is an NDTracker that uses the NDI Combined API to communicate
        with an NDI Aurora electro-magnetic tracker.
    """

    def __init__(self):
        super().__init__()  # initialize as NDCAPITracker
        self.name = "NDAurora"  # default Aurora name

        # load configuration from file
        self._load_config()

        # 6D data file
        self._recording6D = NDDataFile6D()
    
    #####################################################################
    # Communication methods.
    # Implement Aurora protocol.

    def set_param(self, param, value):
        """ Issue a 'SET' command for the specified parameter using the indicated value

        Args:
            param: parameter to set
            value: new value for the parameter

        Returns:

        """
        response = self.send_command("SET " + param + "=" + value)
        reply = ReplySET(response)
        return reply.is_ok()

    def get_param(self, param):
        """ Issue a `GET` comand for the specified parameter
            parse the response
        """
        response = self.send_command("GET " + param)
        return ReplyGET(response)

    def get_info(self, info):
        """ Issue a `getinfo` command for the specified parameter,
            parse the response
        """
        response = self.send_command("getinfo " + info)
        reply = ReplyGETINFO(response)
        return reply.is_ok()

    #####################################################################
    # Aurora implementation of NDTracker
    # override NDTracker functions specific for NDAurora

    def _do_initialize(self):
        """ @override NDTracker::_do_initialize
            Implementation of initialization for NDAurora
            Call the NDCAPITracker parent `_do_initialize`,
            then configure based on the configuration settings
        """
        try:
            super()._do_initialize()
        except NDError as err:
            raise NDError(NDStatusCode.SYSTEM_ERROR, "Error initializing Aurora device", self) from err

        # set the parameters specified in the config file
        if "Param" in self._config.sections():
            for param in self._config.options("Param"):
                self.set_param(param, self._config.get("Param", param))

        # read the information of interest
        parameters = ["Features.Hardware.Serial Number",
                      "Features.Firmware.Version",
                      "Param.Tracking.Selected Volume",
                      "Param.Tracking.Frame Frequency",
                      "Param.Tracking.Track Frequency"]
        for param in parameters:
            logging.info(self.get_param(param))

        # after initialization, create the tool objects being tracked
        # use the device handle ids identified for tracked devices during initialization
        self.tools = []
        for device in self._devices.devices:
            self.tools.append(NDAuroraTool(device.id))
            
    def _get_next_data_frame(self):
        """ @override NDTracker::_get_next_data_frame
            Implementation of data retrieval for NDAurora
            Request and parse one frame of data.
        """
        
        response = self.send_command("BX 0801")

        # parse BX response
        try:
            reply = ReplyBX(response, 0x0801 )
        except NDError as err:
            raise NDError(err.code, "Error parsing BX response", self) from err

        # update the system data
        self.update(reply)

        # if recording, write data to file
        if self._recording6D.is_open:
            # 6d data from tools
            data_6d = [tool.pose for tool in self.tools]
            self._recording6D.write(data_6d, self.frame_num)
            
    def _do_recording_start(self):
        """ @override NDTracker::_do_recording_start
        """

        # if no tools are being tracked, there is nothing to record
        if self.num_tools == 0:
            logging.error("Recording requested but no tools are being tracked")
            return False

        # open data files for writing
        self._recording6D.initialize(self.num_devices)
        self._recording6D.open_write(self._recording_filename_6d)
        return True
    

    def _do_recording_stop(self):
        """ @override NDTracker::_do_recording_stop
        """
        # close the data files
        self._recording6D.close()
        

    def _do_start_streaming(self):
        raise Exception( "Aurora does not support streaming" )

    def _do_stop_streaming(self):
        raise Exception( "Aurora does not support streaming" )
    
    def _do_reset(self):
        """ @override NDTracker::_do_reset
            Reset the Combined API tracker.
        """
        # remember if the system was previously initialized
        was_initialized = self.is_initialized()
        
        # serial break
        self._connection.serialBreak()

        try:
            # send `RESET ` command and parse the response
            response = self.receive_response()
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

    def get_tool(self, port_handle: int):
        """ find the tool associated with the specified port handle

        Returns:
            NDAuroraTool associated with port_handle
        """
        for tool in self.tools:
            if tool.id == port_handle:
                return tool

        # no tool found for this port handle, create the new tool
        self.tools.append(NDAuroraTool(port_handle))
        return self.tools[-1]

    def update_tool(self, handle, pose, status):
        """ Update the status and pose of a Vega tool.
        If the tool is not found on the tools list, add it to the list

        Args:
            handle: port handle for the tool
            pose:   updated tool pose
            status: updated tool status
        """
        # find the tool based on port handle and update with the tool data
        tool = self.get_tool(handle)
        # update the tool with the new tool data
        tool.update(pose, status)

    def update(self, reply: ReplyBX):
        """ Update NDAurora with data received from system

        Args:
            reply: BX reply received from system
        """
        with self.data_lock:
            # The reply data is a BX object
            bxFrame = reply.data
            for bxTool in bxFrame.data:
                #print("handle=%d, status=%d, port_status=0x%x, frame=%d" %(bxTool.handle, bxTool.handle_status, bxTool.port_status, bxTool.frame_number))
                self.update_tool( bxTool.handle, bxTool.pose, bxTool.handle_status)
                self.frame_num = bxTool.frame_number