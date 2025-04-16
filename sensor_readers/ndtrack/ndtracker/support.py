# support.py
# Support functions for ndtrack

# import standard libraries
import logging


class SampleHandler:
    def __init__(self):
        self._name = "Sample"

    def on_event(self, event):
        """ callback frunction when a tracker event occurs
        If this function is registered with a tracker using `add_event_listener`,
        the tracker will call the function every time an event ocurrs.
        """
        if event.is_error():
            logging.error(str(event))
        else:
            logging.info(f"{self._name}: {str(event)}")

    def on_data_frame(self, tracker):
        """ callback function when a data frame event occurs
        If this function is registered with a tracker using `add_data_listener`,
        the tracker will call the function every time it receives a data frame.
        """
        with tracker.data_lock:
            # display tools
            logging.info(f"{self._name}: Frame {tracker.frame_num}: "
                         f"{tracker.num_tools} Tools, {tracker.num_markers} Markers")
            for tool in tracker.tools:
                logging.info(str(tool))
            # display markers
            for marker in tracker.markers:
                logging.info(str(marker))
            print("\n")
