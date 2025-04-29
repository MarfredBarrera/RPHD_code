# NDTracker.py
# Definition of NDTracker python class
# An NDTracker is an NDDataSource with a physical component
# e.g. Optotrak, Vega

# import standard libraries
import threading
from datetime import datetime
from time import sleep
import time

# import ndtrack
from ndtrack.ndtracker.NDDataSource import *
from ndtrack.ndtracker.NDEvent import *


class NDTracker(NDDataSource, ABC):
    """ NDITracker
        An NDI tracking device. Used to track 3D and 6D objects in space.
        Examples of NDITracker are Optotrak, Vega, Aurora
        NDI tracking devices subclass from this class
    """

    def __init__(self):
        super().__init__()                  # initialize as NDDataSource

        # subclasses should specify the values for these variables
        self.name = "NDTracker"             # default Tracker name

        # status variables
        self._is_tracking = False           # is tracker in tracking mode
        self._is_streaming = False          # is tracker in streaming mode
        self._is_recording = False          # is tracker recording to file
        self._is_paused = False             # is tracker paused

        # filenames used when recording data to file
        self._recording_filename_6d = "data6d.csv"
        self._recording_filename_3d = "data3d.csv"

        # list of listeners to data events
        self._data_listeners = []           # data listeners will be invoked when new data is observed

        # access lock
        self.data_lock = threading.Lock()  # used to lock access to data
        self._comm_lock = threading.Lock()  # used to lock access while communicating to the tracker

        # thread variables
        self._tracking_thread = None

        # tools being tracked
        self.tools = []

        # markers being tracked
        self.markers = []

    @property
    def num_tools(self):
        return len(self.tools)

    @property
    def num_markers(self):
        return len(self.markers)

    def _get_state(self):
        """ string representation of the state of the NDTracker """
        # NDTracker has a 'tracking' state
        # If not tracking, use NDDataSource to determine the state
        if self._is_paused:
            return "Paused"
        if self._is_recording:
            return "Recording"
        if self._is_streaming:
            return "Streaming"
        if self._is_tracking:
            return "Tracking"
        return super()._get_state()

    def disconnect(self):
        """ NDTracker disconnect. Overrides NDDataSource disconnect.
            disconnect is used to end communication with the tracker.
            Ensure that tracker recording is complete before disconnecting.
        """
        # if the system is tracking, stop tracking before disconnecting
        if self.is_tracking():
            self.stop_tracking()

        return super().disconnect()

    def _track(self):
        """ Tracking Thread
            This function will run in a separate thread while the tracker
            is tracking. Continuously request data from the tracking system
            and store the data in the member functions.
            Subclasses must implement the `_get_next_data_frame` function.
        """
        # this thread will request data from the tracker until tracking stops
        self._is_tracking = True
        while self.is_tracking() and not self.is_paused():
            try:
                self._get_next_data_frame()
            except NDError as err:
                # this task is running in a separate thread
                # in order to let the main thread know that an error has occurred,
                # set the NDTracker status to NDStatusError
                self._status = NDStatusError(err.code, err.str)
                # report to listeners that an error has occurred
                self.publish_event(NDEventCode.ERROR, f"\r\n\t{err.str}")

            # inform the data listeners that a new frame of data is available
            for f in self._data_listeners:
                f(self)

    #####################################################################
    # NDTracker abstract methods.
    # NDTracker subclasses must override these functions

    @abstractmethod
    def _do_reset(self):
        """ Peform a reset specific to the tracker
            Subclasses must override `_do_reset`
            to reset the tracking device
        """
        pass

    @abstractmethod
    def _do_start_tracking(self):
        """ Perform start tracking specific to the tracker
            Subclasses must override `_do_start_tracking`
            to put the tracking device in tracking mode
        """
        pass

    @abstractmethod
    def _do_stop_tracking(self):
        """ Perform stop tracking specific to the tracker
            Subclasses must override `_do_start_tracking`
            to take the tracking device out of tracking mode
        """
        pass

    @abstractmethod
    def _do_start_streaming(self):
        """ Perform start streaming specific to the tracker
            Subclasses must override `_do_start_streaming`
            to put the tracking system in streaming mode
        """
        pass

    @abstractmethod
    def _do_stop_streaming(self):
        """ Perform start streaming specific to the tracker
            Subclasses must override `_do_stop_streaming`
            to take the tracking system out of streaming mode
        """
        pass

    @abstractmethod
    def _do_recording_start(self):
        """ Prepare data files for recording.
            Subclasses must override `_do_recording_start`
            to open data files and write file headers.
        """
        pass

    @abstractmethod
    def _do_recording_stop(self):
        """ End data file recording.
            Subclasses must override `_do_recording_stop`
            to stop the recording process, write file footers, clean up files.
        """
        pass

    @abstractmethod
    def _get_next_data_frame(self):
        """ Get the next frame of data from the tracking system.
            Subclasses must override `_get_next_data_frame`
            to obtain one frame of data.

            Data should be stored in the member variables:
                self.frame_num
                self.num_3D
                self.data_3D
                self.tools
        """
        pass

    #####################################################################
    # NDTracker actions
    # Available actions for all NDTracker subclasses

    def reset(self):
        """ Reset
            Reset the tracking system.
            Subclasses must override `_do_reset` to perform reset
        """
        # if the system is not connected, it cannot reset
        self.assert_is_connected()

        try:
            # ensure the system is not recording
            self.stop_recording()
            # ensure the system is not tracking
            self.stop_tracking()
            # perform reset specific to the tracker
            # NDTracker subclasses must override `_do_reset`
            self._do_reset()
        except NDError as err:
            raise NDError(err.code, f"Error resetting {self.name}", self) from err

        # reset completed successfully
        self.publish_event(NDEventCode.RESET, "{} reset complete".format(self.name))
        return True

    def start_tracking(self):
        """ Start Tracking
            Used to start obtaining data from the tracking system.
            Starts a tracking thread that will continously request data from
            the tracker until tracking is stopped.
            Subclasses must override `_do_start_tracking` to perform tracking start
            Update tracker state to tracking
        """
        # if the system is not connected, it cannot start tracking
        self.assert_is_connected()

        # if the tracker is not initialized, initialize before tracking starts
        if not self.is_initialized():
            self.initialize()

        # perform tracking start specific to the tracker
        # NDTracker subclasses must override `_do_start_tracking`
        try:
            self._do_start_tracking()
        except NDError as err:
            raise NDError(err.code, f"Error starting tracking with {self.name}", self) from err

        # start tracking thread
        # this will start requesting data from the tracker
        self._tracking_thread = threading.Thread(target=self._track)
        self._tracking_thread.start()
        self.publish_event(NDEventCode.TRACKING_START, "{} tracking started".format(self.name))
        return True

    def pause_tracking(self):
        """ Indicate that the tracker has been paused """
        self._is_paused = True

    def unpause_tracking(self):
        """ Indicate that the tracker has been unpaused """
        self._is_paused = False

    def start_streaming(self):
        """ Start Streaming
            Used to put the tracking system into streaming mode.
            In streaming mode, the tracker will push every frame of data instead
            of waiting for a data request.
            Subclasses must override `_do_start_streaming` to perform streaming start
        """
        # if the system is not tracking, it cannot be put into streaming mode
        self.assert_is_tracking()

        # indicate that system is entering streaming mode
        # this will cause the tracking thread to stop directly asking for data frames
        self._is_streaming = True

        try:
            self._do_start_streaming()
        except NDError as err:
            self._is_streaming = False
            raise NDError(err.code, f"Error starting streaming with {self.name}", self) from err

        return self.is_streaming()

    def stop_streaming(self):
        """ Stop Streaming
            Used to take the tracking system out of streaming mode.
            In streaming mode, the tracker will push every frame of data instead
            of waiting for a data request.
            Subclasses must override `_do_stop_streaming` to perform streaming start
        """
        # if the system is not streaming, there is nothing to do
        if not self.is_streaming():
            return True

        # indicate that streaming has stopped
        self._is_streaming = False

        try:
            self._do_stop_streaming()
        except NDError as err:
            raise NDError(err.code, f"Error stopping streaming with {self.name}", self) from err

        # successfully stopped streaming
        return True

    def assert_is_tracking(self):
        """ Confirm that the tracker is connected and tracking.
            raise an exception if it is not
        """
        # if the system is not connected, it cannot be tracking
        if not self.assert_is_connected():
            return False

        if not self.is_tracking():
            raise NDError(NDStatusCode.USE_ERROR, "{} is is not connected".format(self.name), self)

        # system is in tracking mode
        return True

    def stop_tracking(self):
        """ Stop Tracking
            Used to stop obtaining data from the tracking system.
            Subclasses must override `_do_stop_tracking` to perform tracking stop
            Update tracker state to connected but not tracking.
        """
        # if not tracking, there is nothing to do
        if not self.is_tracking():
            return True

        # if tracker is recording, stop recording
        if self.is_recording():
            self.stop_recording()

        # if tracker is streaming, stop streaming
        if self.is_streaming():
            self.stop_streaming()

        # stop tracking data from the tracker
        self.unpause_tracking()
        self._is_tracking = False

        # Wait for tracking thread to complete
        self._tracking_thread.join()

        # perform tracking stop specific to the tracker
        # NDTracker subclasses must override `_do_stop_tracking`
        try:
            self._do_stop_tracking()
        except NDError as err:
            raise NDError(err.code, f"Error stopping tracking with {self.name}", self) from err

        # successfully stopped tracking
        self.publish_event(NDEventCode.TRACKING_STOP, "{} tracking stopped".format(self.name))
        return True

    def start_recording(self, filename="--default--"):
        """ Start recording data to the specified file
            Prepare the tracking system to record data if the system is ready.
            Subclasses must override `_do_recording_start` to perform recording start
            Update tracker state to recording
        """
        # if not connected or tracking, recording is not an option
        self.assert_is_tracking()

        # if filename is not specified, use the configured filename
        if filename == "--default--":
            filename = self.get("DataFileName", filename)

        # if the filename is not specified or configured, use a default filename
        if filename == "--default--":
            # there is no filename specified in the configuration, create a filename
            # the default filename is the device name and data and time
            now = time.perf_counter()
            filename = f"recording/{self.name}_{now}"

        # the recording data file format is part of the configuration
        # options include "csv" - default. text comma separated data file
        #                 "ndi" - binary NDI Floating Point data file
        recording_format = self.get("DataFileFormat", "csv")

        # the recording format indicates what type of data file to record.
        # by setting the file name with the appropriate file extension, the appropriate file type will be created
        self._recording_filename_6d = f"{filename}_n6d.csv"
        self._recording_filename_3d = f"{filename}_n3d.csv"

        # start recording specific to the tracker
        # NDTracker subclasses must override `_do_recording_start`
        try:
            logging.info(f"Recording data to {filename}")
            self._do_recording_start()
        except NDError as err:
            raise NDError(err.code, f"Error starting recording for {self.name}", self) from err

        # start recording
        self._is_recording = True
        self.publish_event(NDEventCode.RECORDING_START, "{} recording started".format(self.name))
        return True

    def stop_recording(self):
        """ Stop recording data
            End all data recordings.
            Subclasses must override `_do_recording_stop` to perform recording stop
            Update tracker state to tracking but not recording
        """
        # if not recording, there is nothing to do
        if not self.is_recording():
            return True

        # stop recording specific to the tracker
        # NDTracker subclasses must override `_do_recording_stop`
        try:
            self._do_recording_stop()
        except NDError as err:
            raise NDError(err.code, f"Error stopping recording for {self.name}", self) from err

        # update recording status
        self.publish_event(NDEventCode.RECORDING_STOP, "{} recording stopped".format(self.name))
        self._is_recording = False
        return True

    def add_data_listener(self, cb):
        """ Add a data listener.
            Data listeners will be called whenever a new frame of data
            is obtained by the tracker
        """
        self._data_listeners.append(cb)

    #####################################################################
    # NDTracker state functions

    def is_tracking(self):
        """ Indicate if the tracker is in tracking mode """
        return self._is_tracking

    def is_streaming(self):
        """ Indicate if the tracker is in streaming mode """
        return self._is_streaming

    def is_recording(self):
        """ Indicate if the tracker is in recording mode """
        return self._is_recording

    def is_paused(self):
        """ Indicate if the track has been paused """
        return self._is_paused
