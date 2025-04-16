# devices.py
# CAPIDevices contains a list of CAPIDevice used to track tools using CAPI Tracker

# import capi
from ndtrack.capi.reply import *


class CAPIDevice:
    """
    CAPIDevice describes a device tracked by a CAPITracker
    """
    def __init__(self, ph_id, tracker=None):
        """
        Initialize the CAPIDevice

        Parameters
        ph_id   - Port Handle ID associated with this device by the tracker.
        tracker - CAPITracker using this device.
        """
        self.id = ph_id
        self._tracker = tracker
        self._status = 0            # status OK
        self._tooltype = None       # unknown tool type

    def __str__(self):
        return f"Device_{self.id}: Type {self._tooltype} ({self._status})"

    def assert_tracker(self):
        """ Confirm that the tracker has been specified """
        if self._tracker is None:
            raise NDError(NDStatusCode.USE_ERROR, "Tracker must be specified", self)

    def get_info(self):
        """ Get device information from the system using PHINF command """
        self.assert_tracker()
        response = self._tracker.send_command(f"PHINF {self.id:02X}0001")
        reply = ReplyPHINF(response)
        return reply.status

    def load_srom(self, rom_file):
        """ Load the specified srom file """
        self.assert_tracker()

        # read the rom file into memory
        with open(rom_file, 'rb') as f:
            buff = f.read()
            buff = bytearray(buff)

        # write data to the tool description section of the virtual SROM
        addr = 0
        while addr < len(buff):
            cmd = f"PVWR {self.id:02X}{addr:04X}"
            for i in range(64):
                try:
                    cmd += f"{buff[addr]:02X}"
                    addr += 1
                except IndexError:
                    cmd += f"{0:02X}"
            response = self._tracker.send_command(cmd)
            reply = ReplyPVWR(response)
            if reply.is_error():
                raise NDError(NDStatusCode.FILE_ERROR, f"ERROR {reply.error_code}Error writing tool definition", self)

    def free(self):
        """ Free the port handle using PHF command """
        self.assert_tracker()
        response = self._tracker.send_command(f"PHF {self.id:02X}")
        reply = ReplyPHF(response)
        if reply.is_error():
            raise NDError(NDStatusCode.SYSTEM_ERROR, f"Unable to free port handle {self.id}", self)

    def initialize(self):
        """ Initialize the port handle using PINIT command """
        self.assert_tracker()
        response = self._tracker.send_command(f"PINIT {self.id:02X}")
        reply = ReplyPINIT(response)
        if reply.is_error():
            raise NDError(NDStatusCode.SYSTEM_ERROR, f"Unable to initialize port handle {self.id}", self)
        self.get_info()

    def enable(self):
        """ Enable the port handle using PENA command """
        self.assert_tracker()
        response = self._tracker.send_command(f"PENA {self.id:02X}{'D'}")
        reply = ReplyPENA(response)
        if reply.is_error():
            raise NDError(NDStatusCode.SYSTEM_ERROR, f"Unable to initialize port handle {self.id}", self)
        self.get_info()


class CAPIDevices:
    """
    CAPIDevices maintains the list of devices associated with a CAPI Tracker
    """
    def __init__(self, tracker=None):
        self._tracker = tracker
        self.devices = []

    def __str__(self):
        out_str = f"{len(self)} Devices:\n"
        for device in self.devices:
            out_str += f"{device}\n"
        return out_str

    def __len__(self):
        return len(self.devices)

    def _get_device(self, ph_id):
        """
        Get the device with the specified port handle ID

        Parameters:
        ph_id (int): Port Handle ID

        Return:
        device (CAPIDevice): Device associated with the specified ID, or None if it does not exist
        """
        # Iterate through the devices to find the desired device
        for device in self.devices:
            if ph_id == device.id:
                return device
        # no device was found with the desired port handle ID
        return None

    def _get_new_device(self, ph_id):
        """
        Create a new device with the specified port handle ID, if one does not already exist

        Parameters:
        ph_id (int): Port Handle ID

        Return:
        device (CAPIDevice): Device associated with the specified ID
        """
        device = self._get_device(ph_id)
        if not device:
            device = CAPIDevice(ph_id, self._tracker)
            self.devices.append(device)
        return device

    def phsr(self, mode):
        """
        Request the number of assigned port handles and the port status for each one

        Parameters:
        mode (int): search mode
                    0 Reports all allocated port handles
                    1 Reports port handles that need to be freed
                    2 Reports port handles that are occupied, but not initialized or enabled
                    3 Reports port handles that are occupied and initialized, but not enabled
                    4 Reports enabled port handles

        Returns:
        ph_list (list of int): list of port handles
        """
        response = self._tracker.send_command(f"PHSR {mode:02}")
        reply = ReplyPHSR(response)
        return reply.data

    def phinf(self, mode=0):
        """
        Request information about the port handle from the PSU using the 'PHSR' and 'PHINF' api commands. Returns the
        raw PHINF response without parsing.

        TODO: Expand by defining a ReplyPHINF class that can parse and understand all possible responses from PHINF

        Parameters:
        mode (int): specifies which information will be returned:
                    0 Tool information (default)
                    2 Wired tool electrical information
                    4 Tool part number
                    8 Switch and Visible LED information
                    10 Tool marker type and wavelength
                    20 Physical Port location

        returns:
        ph_inflist: list of tuples with (port_handle, <PHINF status>)
        """
        ph_inflist = []
        port_handles = self.phsr(0)
        for port_handle in port_handles:
            response = self._tracker.send_command(f"PHINF {port_handle[0]:02}{mode:04}")
            ph_inflist.append((port_handle[0], response))
        return ph_inflist

    def assert_tracker(self):
        """ Confirm that the tracker has been specified """
        if self._tracker is None:
            raise NDError(NDStatusCode.USE_ERROR, "Tracker must be specified", self)

    def free(self):
        """ Free port handles """
        self.assert_tracker()
        # PHSR 01 - Report port handles that need to be freed
        try:
            ph_list = self.phsr(1)
            for (ph_id, ph_status) in ph_list:
                device = self._get_device(ph_id)
                if device:
                    # free the specified port handle and remove it from the devices list
                    device.free()
                    self.devices.remove(device)
        except NDError as err:
            raise NDError(err.code, f"Unable to free port handles", self) from err

    def initialize(self):
        """ Initialize port handles """
        self.assert_tracker()
        # PHSR 02 - Report port handles that are occupied, but not initialized or enabled
        try:
            ph_list = self.phsr(2)
            for (ph_id, ph_status) in ph_list:
                device = self._get_new_device(ph_id)
                if device:
                    device.initialize()
        except NDError as err:
            raise NDError(err.code, f"Unable to initialize port handles", self) from err

    def enable(self):
        """ Enable port handles """
        self.assert_tracker()
        # PHSR 03 - Report port handles that are occupied and initialized, but not enabled
        try:
            ph_list = self.phsr(3)
            for (ph_id, ph_status) in ph_list:
                device = self._get_new_device(ph_id)
                if device:
                    device.enable()
        except NDError as err:
            raise NDError(err.code, f"Unable to enable port handles", self) from err

    def load_wireless(self, rom_files):
        """
        Load wireless devices using the specified ROM files

        Parameters:
        rom_files (string list): list of ROM files to load
        """
        self.assert_tracker()
        for rom in rom_files:
            # request a port handle
            response = self._tracker.send_command('PHRQ *********1****')
            reply = ReplyPHRQ(response)
            ph_id = reply.data

            # create a new device using the specified port handle
            device = self._get_new_device(ph_id)
            if device:
                device.load_srom(rom)

    def load_and_initialize_wired(self, config_file):
        """
        Load and initialize all wired tools. Wired tools must be connected to an SCU and that SCU must be specified in
        the PSU's 'Connect.SCU Hostname' parameter. Any active wired tool that does not have an embedded SROM must have
        the path to the SROM file specified in the appropiate ini file

        The workflow used for loading the active wired tools is:
        -Use PHINF 20 to get a list of all port handles and the physical ports that they are connected to.
        -Call PINIT on each port handle
        -If PINIT returns OKAY, the port handle is associated with an active wired tool with an embedded SROM
        -If PINIT fails with ERROR1E,the port handle is associated with an active wired tool without an embedded SROM
            -Read the srom file for the physical port from the .ini file
            -load the srom file
            -call PINIT again. Throw an error if it does not return an OKAY response.
        Parameters:
        config_file:
        """

        self.assert_tracker()
        port_handles_physical_port_information = self.phinf(20)
        for port_handle in port_handles_physical_port_information:
            device = self._get_new_device(port_handle[0])
            # device will be NULL if there is already a device that is associated with that port handle
            if device:
                # Attempt to use PINIT on each port_handle
                response = self._tracker.send_command(f"PINIT {port_handle[0]:02X}")
                # ERROR1E is the expected error that will occur
                # reply = ReplyPINIT(response)
                # ERROR1EDCC3/r is the expected response when attempting to initialize a port handle associated with an
                # active wired tool that does not have an embedded response
                if response == 'ERROR1EDCC3\r':
                    # Get the srom associated with the port from the config .ini file
                    # The response from phinf is formatted as:
                    # <4 bytes representing the tool location><4 reserved bytes><4 bytes for CRC16>
                    # E.g. in a sample response 'STB-0   000100D840\r'
                    # 0001 represents the physical port used by the tool.
                    srom = config_file.get("WiredTool_Port" + port_handle[1].split(" ")[-1][3], "srom")
                    device.load_srom(srom)
                    device.initialize()
                elif response != 'OKAYA896\r':
                    #TODO can't convert int to string
#f"{indent}Tool_{self.port_handle} ({self.num_items} buttons)\n"
                    raise NDError(NDStatusCode.SYSTEM_ERROR,  f"Unable to initialize port handle {port_handle[0]}")


def main():
    # set up to log everything
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s : %(levelname)s : %(message)s')
    logging.addLevelName(NDLogLevel.Test, "TEST")
    logging.log(NDLogLevel.Test, "CAPI devices")

    device = CAPIDevice(1)
    logging.info(f"Device ID: {device.id}")

    devices_list = CAPIDevices()
    print(devices_list)


if __name__ == "__main__":
    main()
