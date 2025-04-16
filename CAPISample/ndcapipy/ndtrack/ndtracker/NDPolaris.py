# NDPolaris.py
# NDPolaris python class
# NDPolaris is an NDTracker that communicates with the Polaris Family Systems

from ndtrack.ndtracker.NDCAPITracker import *
from ndtrack.ndtracker.trackable.NDPolarisTool import *


class NDPolaris(NDCAPITracker, ABC):
    """ NDPolaris is an NDTracker that uses the NDI Combined API to communicate
        with an NDI Polaris optical tracker.
    """

    def __init__(self):
        super().__init__()  # initialize as NDCAPITracker
        self.name = "NDPolaris"  # default Polaris name

        self._image_data = None  # image information captured using VSNAP/VGET or VCAP commands
        self._images = []  # image bytes captured using VSNAP/VGET or VCAP commands
        self._images = []  # image bytes captured using VSNAP/VGET or VCAP commands

    #####################################################################
    # Communication methods.
    # Implement Polaris protocol.

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

    def get_image_data(self):
        """
            Returns a dictionary containing the array of captured imaged from VCAP or VSNAP and VGET
            As well as the relevant information relating to those images
        """
        return {"Image Info": self._image_data, "Raw Images": self._images}

    def image_capture(self, options=""):
        """ Capture an image
        Uses VSNAP and VGET for image capture
        This is the version 1 method of capturing images
        The options parameter must include the name of the command followed by the capture options for that command
        Old Commands have custom options not in the API guide for testing purposes
            --rows              specifies the number of rows of data to retrieve default value is 1
            --startcolumn       Indicates the first column to retrieve (Optional)
            --endcolumn         Indicated the last column to retrieve (Optional)
            --stride            Indicates the stride count to use from the start to end column (Optional)

        Eg how to call the method:
            vega.image_capture("V1 --rows=100 --startcolumn=0 --endcolumn=25 --stride=0")

        See api guide for valid values
        """

        rows = 1
        startcolumn = None
        endcolumn = None
        stride = None

        for option in ("%s " % options).split('--'):
            if "rows" in option:
                rows = option[option.index('=') + 1:-1]
            elif "startcolumn" in option:
                startcolumn = option[option.index('=') + 1:-1]
            elif "endcolumn" in option:
                endcolumn = option[option.index('=') + 1:-1]
            elif "stride" in option:
                stride = option[option.index('=') + 1:-1]
            elif "VSNAP" in option or "VGET" in option or "V1" in option:
                pass
            else:
                raise ValueError('Incorrect VSNAP/VGET Option: --%s' % option)

        response = self.send_command("VSNAP")
        reply = ReplyVSNAP(response)
        if reply.is_error():
            return reply.is_error()

        (frame_number, frames_data) = reply.data  # data received from VSNAP command
        vget_reply = self.get_param("Cmd.VGet.*")
        vget_info = vget_reply.data
        color_depth = int(vget_info["Cmd.VGet.Color Depth"])  # intensity for each pixel is given by x bits of data
        num_rows = int(vget_info["Cmd.VGet.Sensor.Height"])  # number of sensor rows
        num_columns = hex(int(vget_info["Cmd.VGet.Sensor.Width"])-1)  # number of sensor columns
        num_columns = num_columns[num_columns.find('x')+1:]
        sensors = [0, 1]  # 0 = left sensor, 1 = right sensor

        self._images = []
        self._image_data = []
        for sensor in sensors:
            frame_index = 0
            frame_data = []
            for frame in frames_data:
                (frame_type, exposure_times) = frame

                data = f"{frame_type}:{frame_number}:{sensor}"
                self._image_data.append(data)

                if frame_type == 0x0F:
                    # A frame_type value of 0F indicates a frame that is used only for timing purposes,
                    # and contains no useful data
                    pass
                else:
                    if startcolumn is None:
                        start_column = 0
                    if endcolumn is None:
                        end_column = num_columns
                    if stride is None:
                        stride = 1

                    buffer_data = bytearray()
                    for row in range(int(rows)):
                        hexrow = hex(row)
                        hexrow = hexrow[hexrow.find('x')+1:]

                        vget_command = f"VGET {str(hexrow).zfill(4)}{str(sensor).zfill(2)}{str(frame_index).zfill(2)}" \
                                       f"{str(start_column).zfill(4)}{str(end_column).zfill(4)}{str(stride).zfill(2)}"
                        response = self.send_command(vget_command)
                        reply = ReplyVGET(response)
                        buffer_data.extend(reply.data)
                    frame_index = frame_index + 1
                    frame_data.append(buffer_data)

            self._images.extend(frame_data)

        return reply.is_ok()

    #####################################################################
    # Polaris implementation of NDTracker
    # override NDTracker functions specific for NDPolaris

    def _do_initialize(self):
        """ @override NDTracker::_do_initialize
            Implementation of initialization for NDPolaris
            Call the NDCAPITracker parent `_do_initialize`,
            then configure based on the configuration settings
        """
        try:
            super()._do_initialize()
        except NDError as err:
            raise NDError(NDStatusCode.SYSTEM_ERROR, "Error initializing Polaris device", self) from err

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

    def _do_start_streaming(self):
        """ @override NDTracker::_do_start_streaming
            Start streaming mode
        """
        # send STREAM command
        response = self.send_command("STREAM BX2 --6d=tools --3d=all")
        reply = ReplySTREAM(response)
        return reply.is_ok()

    def _do_stop_streaming(self):
        """ @override NDTracker::_do_stop_streaming
            Stop streaming mode
        """
        # send STREAM command
        # do not wait for reply since the system is in tracking mode and
        # there may be other data in the queue
        response = self.send_command("USTREAM BX2 --6d=tools --3d=all")
        reply = ReplyUSTREAM(response)
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
