# NDSpectra.py
# NDSpectra python class
# NDSpectra is an NDTracker that communicates with the Vicra or Spectra Tracking System

# import standard libraries
import sys

# import ndtrack
from ndtrack.ndtracker.NDPolaris import *
from ndtrack.capi.reply import *
from ndtrack.datafile.NDDataFile6D import NDDataFile6D
from ndtrack.ndtracker.support import SampleHandler
from ndtrack.ndtracker.trackable.NDPolarisTool import NDVegaMarker, NDPolarisTool


class NDSpectra(NDPolaris):
    """ NDVega is an NDTracker that uses the NDI Combined API to communicate
        with an NDI Vega optical tracker.
    """

    def __init__(self):
        super().__init__()  # initialize as NDCAPITracker
        self.name = "NDSpectra"  # default Vega name

        # load configuration from file
        self._load_config()

        # 6D data file
        self._recording6D = NDDataFile6D()

    #####################################################################
    # Spectra/Vicra implementation of NDTracker
    # override NDTracker functions specific for NDSpectra

    def _do_initialize(self):
        """ @override NDCAPITracker::_do_initialize
            After standard CAPI initialization, initalize NDVega tools
        """
        super()._do_initialize()

        # after initialization, create the tool objects being tracked
        # use the device handle ids identified for tracked devices during initialization
        self.tools = []
        for device in self._devices.devices:
            self.tools.append(NDPolarisTool(device.id))

    def _get_next_data_frame(self):
        """ @override NDTracker::_get_next_data_frame
            Implementation of data retrieval for NDVega
            Request and parse one frame of data.
        """
        # request a frame of data
        response = self.send_command("BX 080B")

        # parse BX response
        try:
            reply = ReplyBX(response, 0x080B )
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

    def get_tool(self, port_handle: int):
        """ find the tool associated with the specified port handle

        Returns:
            NDVegaTool associated with port_handle
        """
        for tool in self.tools:
            if tool.id == port_handle:
                return tool

        # no tool found for this port handle, create the new tool
        self.tools.append(NDPolarisTool(port_handle))
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

    def free_port_handles(self):
        """
        Removes wireless tools that have been loaded and frees their port handles
        """
        # TODO: Safely free port handles to remove specified tools from the tracker
        #  Make sure to remove the device as well as the NDVegaTool from the Tools list
        # self._devices.free()
        pass

    def add_stray_marker(self, index, pos, status):
        self.markers.append(NDVegaMarker(index))
        self.markers[-1].update(pos, status)

    def update_tool_markers(self, tool_data: Component3D):
        """ Update the status and position of Vega tool markers.

        Args:
            tool_data: Component3D for a specific tool. Contains marker status and positions from BX2 reply
        """
        # Stray markers are indicated under port handle "-1" (0xFFFF)
        if tool_data.port_handle & 0xFFFF == 0xFFFF:
            for marker in tool_data.data:
                self.add_stray_marker(marker.index, marker.pos, marker.status)
            return

        tool = self.get_tool(tool_data.port_handle)
        for marker_data in tool_data.data:
            marker = tool.get_marker(marker_data.index)
            marker.update(marker_data.pos, marker_data.status)

    def update_tool_markers(self, tool_markers: BXToolMarkers ):
        """ Update the status and position of Polaris tool markers.

        Args:
            tool_markers: BXToolMarkers for a specific tool. Contains marker status and positions from BX reply
        """
        
        # Stray markers are indicated under port handle "-1" (0xFFFF)
        if tool_markers.handle & 0xFFFF == 0xFFFF:
            for marker in tool_markers.data:
                self.add_stray_marker(marker.index, marker.pos, marker.status)
            return

        tool = self.get_tool(tool_markers.handle)
        index = 0
        for marker_data in tool_markers.data:
            # marker_data is a bx.ToolMarker
            marker = tool.get_marker(index)
            marker.update(marker_data.position, marker_data.status)
            index += 1

    def update_tool_marker_errors(self, tool_data: ComponentMarkerError):
        """ Update the status and position of Vega tool markers.

        Args:
            tool_data: ComponentMarkerError for a specific tool. Contains marker errors from BX2 reply
        """
        if tool_data.port_handle & 0xFFFF == 0xFFFF:
            return
        
        tool = self.get_tool(tool_data.port_handle)
        
        for marker_error_data in tool_data.data:
            marker = tool.get_marker(marker_error_data.index)
            marker.updateError(marker_error_data.error)

    def update(self, reply: ReplyBX):
        """ Update NDSpectra with data received from system

        Args:
            reply: BX reply received from system
        """
        with self.data_lock:
            # The reply data is a BX object
            bxFrame = reply.data
            for bxTool in bxFrame.data:
                self.update_tool( bxTool.handle, bxTool.pose, bxTool.handle_status)
                self.frame_num = bxTool.frame_number
                
                # markers
                if not bxTool.markers == None:
                    self.update_tool_markers( bxTool.markers )