# sample.py
# sample application for tracking data from an Aurora or Polaris system

import argparse
from time import sleep
from ndtrack.ndtracker.NDCAPITracker import NDCAPITracker
from ndtrack.ndtracker.NDAurora import NDAurora
from ndtrack.ndtracker.NDPolaris import NDPolaris
from ndtrack.ndtracker.NDVega import NDVega
from ndtrack.ndtracker.NDSpectra import NDSpectra
import logging


class DataHandler:
    def __init__(self):
        self._name = "Data Handler"

    def on_data_frame(self, tracker):
        """ callback function when a data frame event occurs
        If this function is registered with a tracker using `add_data_listener`,
        the tracker will call the function every time it receives a data frame.
        """
        with tracker.data_lock:
            # display 6D data
            print(f"{self._name}: Frame {tracker.frame_num}: {tracker.num_tools} Tools")
            for i, tool in enumerate(tracker.tools, 1):
                print(f"RB_{i}: {tool}")


class EventHandler:
    def __init__(self):
        self._name = "Event"

    def on_event(self, event):
        """ callback frunction when a tracker event occurs
        If this function is registered with a tracker using `add_event_listener`,
        the tracker will call the function every time an event ocurrs.
        """
        if event.is_error():
            print(f"ERROR: {str(event)}")
        else:
            print(f"{self._name}: {str(event)}")

class NDUnknownSystem(NDCAPITracker):
    """ Describes a type of NDI system that uses the Combined API
    But the type of NDI CAPI system is unknown: might be Polaris or Aurora
    Used to connect and send APIREV and VER 4 commands to determine the system
    """
    def _do_recording_start(self): pass
    def _do_recording_stop(self): pass
    def _do_start_streaming(self): pass
    def _do_stop_streaming(self): pass
    def _get_next_data_frame(self): pass

def main():
    # Uncomment the next line to add logging
    # logging.basicConfig(level=logging.DEBUG, format="%(asctime)s : %(levelname)s : %(message)s")

    parser = argparse.ArgumentParser()
    parser.add_argument( "connection", help="Connection (e.g. COM7 or P9-01234)")
    parser.add_argument( "-l", "--load", nargs='*', help="Polaris wireless tool SROM filename (e.g. 8700339.rom)")
    parser.add_argument( "-t", "--time", default=5, help="Length of time to track")
    parser.add_argument( "-p", "--port", default=8765, help="Port to connect to on socket" )
    args = parser.parse_args()
    
    # use generic CAPI tracker object
    ndiDevice = NDUnknownSystem()
    ndiDevice.set_connection(args.connection)
    
    if not ndiDevice.connect():
        print( "Connection failed." )
        exit -1

    # find out what this is by sending APIREV and VER commands
    api = ndiDevice.send_command("APIREV ", True)
    # take off crc and \r
    endIndex = len(api) - 5
    api = api[0:endIndex]
    print( "API %s" % (api))
    
    reply = ndiDevice.send_command("VER 4", True)
    # take off crc and \r
    endIndex = len(reply) - 5
    print( "Connected to %s" % (reply[0:endIndex]))
    
    # first letter of API tells you what kind of product family
    isOptical = api[0] == "G"
    isEM = api[0] == "D"
    
    # Disconnect, will reconnect when we know what it is
    ndiDevice.disconnect()
    
    # this sample doesn't support anything else
    if isOptical:
        # Determine if Vega/Lyra or earlier from major revision of API (G.003 is Vega/Lyra API)
        if api[2:5] == "003":
            ndiDevice = NDVega()
        else:
            # Spectra or Vicra
            ndiDevice = NDSpectra()
    elif isEM:
        ndiDevice = NDAurora()
    else:
        print( "Unsupported device type.")
        exit -1
    
    # Now we have a new system object, we can re-connect and do more
    
    # data and event handlers for NDI system
    data_handler = DataHandler()
    event_handler = EventHandler()
    # add data listener. Function will be called for each frame of data
    ndiDevice.add_data_listener(data_handler.on_data_frame)
    # add event listener. Function will be called for each event
    ndiDevice.add_event_listener(event_handler.on_event)

    print("Connecting to %s %s" % ( ndiDevice, args.connection ))
    
    # Establish connection
    ndiDevice.set_connection(args.connection)
    if not ndiDevice.connect():
        print( "Connection failed." )
        exit -1
    
    # Reset (not always necessary, may help with serial devices)
    ndiDevice.reset()

    # initialize the system
    ndiDevice.initialize()
    
    # If this is a Polaris, and there are wireless tools to load
    if not args.load == None and len(args.load) > 0 and isinstance( ndiDevice, NDPolaris):
        # Load all of the specified wireless tool definitions into the Polaris system
        ndiDevice.add_wireless_tools( args.load )

    # start tracking
    ndiDevice.start_tracking()
    sleep(float(0.25))

    # record data for the specified length of time (-t)
    ndiDevice.start_recording()
    sleep(float(args.time))
    ndiDevice.stop_recording()

    ndiDevice.stop_tracking()

    # disconnect from the NDI system
    ndiDevice.disconnect()
    
    exit

if __name__ == "__main__":
    main()