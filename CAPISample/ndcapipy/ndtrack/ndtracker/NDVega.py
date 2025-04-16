# NDVega.py
# NDVega python class
# NDVega is an NDTracker that communicates with the Vega Tracking System

# import standard libraries
import sys

# import ndtrack
from ndtrack.ndtracker.NDPolaris import *
from ndtrack.capi.reply import *
from ndtrack.datafile.NDDataFile6D import NDDataFile6D
from ndtrack.ndtracker.support import SampleHandler
from ndtrack.ndtracker.trackable.NDPolarisTool import NDVegaMarker, NDPolarisTool


class NDVega(NDPolaris):
    """ NDVega is an NDTracker that uses the NDI Combined API to communicate
        with an NDI Vega optical tracker.
    """

    def __init__(self):
        super().__init__()  # initialize as NDCAPITracker
        self.name = "NDVega"  # default Vega name

        # load configuration from file
        self._load_config()

        # 6D data file
        self._recording6D = NDDataFile6D()

    #####################################################################
    # Vega implementation of NDTracker
    # override NDTracker functions specific for NDVega

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
        if self.is_streaming():
            # if in streaming mode, data will be sent continuously. obtain the next BX2 response
            with self._comm_lock:
                try:
                    response = self.receive_response()
                except NDError as err:
                    raise NDError(err.code, "Unable to obtain streaming data", self) from err
        else:
            # if not in streaming mode, actively request a frame of data
            response = self.send_command("BX2 --3d=all")

        # parse BX2 response
        try:
            reply = ReplyBX2(response)
        except NDError as err:
            raise NDError(err.code, "Error parsing BX2 response", self) from err

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

    def image_capture(self, options=""):
        """ Capture an image
        Override the NDPolaris image_capture, which uses VSNAP and VGET

        Args:
            options:    VCAP options
        """
        # if the option passed in VSNAP, use the old VSNAP/VGET method of image capture
        if "VSNAP" in options or "VGET" in options or "V1" in options:
            return super().image_capture(options)

        if "VCAP" not in options:
            response = self.send_command(f"VCAP {options}")
        else:
            response = self.send_command(options)

        reply = ReplyVCAP(response)
        if response == "OKAYA896\r":
            return reply.is_ok()

        # Iterates through each frame component
        for frame_component in reply.data.data:
            # Iterates through each frame item
            for frame_item in frame_component.data:
                # Appends the Image data to the images array containing all the captured images from VCAP
                if frame_component.type == ComponentType.Image:
                    self._images.append(frame_item.image)

        # Stores the data on the captured images
        self._image_data = reply.data

        return reply.is_ok()

    def add_wireless_tools(self, sroms: list):
        """
        Adds a list of new wireless tools to the NDVega Tracker and loads them onto the PSU
        The tools are added to the list of devices that the Tracker contains as well

        Args:
            sroms: A list of rom files for the passive tools that should be loaded
        """
        current_tool_ids = [device.id for device in self._devices.devices]
        self._devices.load_wireless(sroms)
        self._devices.initialize()
        self._devices.enable()

        for device in self._devices.devices:
            if device.id not in current_tool_ids:
                self._num_wireless_tools += 1
                self.tools.append(NDPolarisTool(device.id))

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

    def update(self, reply: ReplyBX2):
        """ Update NDVega with data received from system

        Args:
            reply: BX2 reply received from system
        """
        with self.data_lock:
            self.markers = []
            gb = reply.data
            # for each frame in the reply
            for frame_component in gb.data:
                # iterate through each frame item
                for frame_item in frame_component.data:
                    # update frame number
                    self.frame_num = frame_item.frame_number
                    for data_payload in frame_item.data:
                        # data payload contain data components
                        for data_component in data_payload.data:
                            # populate the tracked items based on component type
                            if data_component.type == ComponentType.comp6D:
                                # data component contains tool data
                                # sub-components are Component6D objects
                                for component in data_component.data:
                                    self.update_tool(component.port_handle, component.pose, component.status)
                            elif data_component.type == ComponentType.comp3D:
                                # data component contains tool marker data
                                # sub-components are Component3D objects
                                for component in data_component.data:
                                    self.update_tool_markers(component)
                            elif data_component.type == ComponentType.comp3DError:
                                # data component contains tool marker errors
                                # sub-components are ComponentMarkerError objects
                                for component in data_component.data:
                                    self.update_tool_marker_errors(component)
                            elif data_component.type == ComponentType.comp1D:
                                # Component1D contains button data
                                pass
                            elif data_component.type == ComponentType.Alert:
                                # ComponentAlert contains alert data
                                pass