# gbf.py
# General Binary Format (GBF) classes
# The NDI GBF is used in CAPI commands to contain tracking and video data.

# import standard libraries
from time import ctime

# import NDI libraries
from ndtrack.ndtypes.NDDataTypes import *

from ndtrack.capi.packer import *
from ndtrack.capi.defines import *

# binary reply start sequence
ND_BIN_STARTSEQ = 0xA5C4            # standard binary reply start sequence
ND_BIN_STARTSEQ_EXT = 0xA5C8        # extended binary reply start sequence


class GBFComponent(ABC):
    """ A binary response component.
        Components contain a list of data
        Each data component is istelf an GBFComponent
    """
    def __init__(self, buffer):
        # initialize component information to 'NONE'
        self.type = ComponentType.NONE
        self.version = 0

        # initialize data list
        self.data = []

        # parse the buffer
        # store the parsed data into self.data
        self.parse(buffer)

    def __str__(self):
        return self.str()

    @abstractmethod
    def parse(self, buffer):
        """
            parse the buffer and store data components in self.data
            override this method to parse component data
        """
        pass

    def str(self, indent=""):
        """
            default string representation contains only data
            override this method to write specific component data
        """
        return self.str_data(indent)

    def str_data(self, indent=""):
        """ string representation of the component data """
        out_str = ""
        for c in self.data:
            out_str += c.str(indent)
        return out_str

    def add_data(self, new_data):
        """ add a data component to the data list """
        self.data.append(new_data)

    @property
    def has_data(self):
        """ indicates if this component has data """
        return len(self.data) > 0

    @property
    def component_data(self):
        """ The data list contains one single data item with the specific component information """
        if self.has_data:
            return self.data[0]
        else:
            return self.data


class GeneralBinaryPayload(GBFComponent):
    """ A binary response component formatted in the General Binary Format

        The General Binary Component contains
            - Version                   2 Bytes
            - Component count           2 Bytes
            - Component data            size dependent on component type
    """
    def __init__(self, buffer):
        self.num_components = 0
        super().__init__(buffer)

    def parse(self, buffer):
        # read the GBF version, which describes the format of the data
        self.version = unpack_int(buffer)
        self.num_components = unpack_int(buffer)

        # for each component, parse the component and add data to this object
        for c in range(self.num_components):
            component = DataComponent(buffer)
            if component.type != ComponentType.NONE:
                self.add_data(component)


class DataComponent(GBFComponent):
    """ A data component formatted in the General Binary Format

        The Data Component contains
            - Data Component Types      2 Bytes
            - Data Component Size       4 Bytes
            - Item Format Option        2 Bytes
            - Item Count                4 Bytes
    """
    def __init__(self, buffer):
        self.size = 0
        self.item_format = 0
        self.item_count = 0
        super().__init__(buffer)

    def parse(self, buffer):
        try:
            # Data Component Type
            self.type = ComponentType(unpack_int(buffer))
        except ValueError:
            # data from the system sometimes contains random invalid data
            # if this is an unknown ComponentType, return
            self.type = ComponentType.NONE
            self.size = unpack_int(buffer, 4)
            unpack_bytes(buffer, self.size - 6)     # 6 bytes have already been read (type, size)
            return

        # Data Component Size
        self.size = unpack_int(buffer, 4)
        # Item Format Option
        self.item_format = unpack_int(buffer)
        # Item Count
        self.item_count = unpack_int(buffer, 4)

        # for each item, add data based on the item type
        for f in range(self.item_count):
            if self.type == ComponentType.Frame:
                self.add_data(FrameItem(buffer))
            elif self.type == ComponentType.comp1D:
                self.add_data(Component1D(buffer))
            elif self.type == ComponentType.comp3D:
                self.add_data(Component3D(buffer))
            elif self.type == ComponentType.comp6D:
                self.add_data(Component6D(buffer))
            elif self.type == ComponentType.Image:
                self.add_data(ComponentImage(buffer))
            elif self.type == ComponentType.Alert:
                self.add_data(ComponentAlert(buffer))
            elif self.type == ComponentType.comp3DError:
                self.add_data(ComponentMarkerError(buffer))

    def str(self, indent=""):
        out_str = f"{indent}{self.type}: {self.item_count} items\n"
        if self.has_data:
            out_str += self.str_data(indent + "  ")
        return out_str


class ComponentButton(GBFComponent):
    """ Button component formatted in the General Binary Format
        1 byte for each button
    """
    def __init__(self, button_id, buffer):
        self._id = button_id
        super().__init__(buffer)

    def parse(self, buffer):
        self.add_data(unpack_int(buffer, 1))

    def str(self, indent=""):
        return f"{indent}B_{self._id}: {self.component_data}\n"


class Component1D(GBFComponent):
    """ 1D Data component formatted in the General Binary Format
    """
    def __init__(self, buffer):
        self.port_handle = 0
        self.num_items = 0
        super().__init__(buffer)

    def parse(self, buffer):
        # 1 byte    (int) tool handle
        self.port_handle = unpack_int(buffer)
        # 1 byte    (int) # number of buttons
        self.num_items = unpack_int(buffer)
        for i in range(self.num_items):
            self.add_data(ComponentButton(i + 1, buffer))

    def str(self, indent=""):
        out_str = f"{indent}Tool_{self.port_handle} ({self.num_items} buttons)\n"
        if self.has_data:
            out_str += self.str_data(indent + "  ")
        return out_str


class Item3D(GBFComponent):
    """ 3D Data item formatted in the General Binary Format

        Each 3D Data item contains
            - Status                    1 byte
            - -reserved-                1 byte
            - Marker Index              2 bytes
            - X                         4 bytes
            - Y                         4 bytes
            - Z                         4 bytes
    """
    def __init__(self, buffer):
        self.status = 0
        self.index = 0
        super().__init__(buffer)

    def parse(self, buffer):
        # 1 byte    (int) marker status
        self.status = Status3D(unpack_int(buffer, 1))
        # 1 byte    -reserved-
        unpack_int(buffer, 1)
        # 2 bytes   (int) marker index
        self.index = unpack_int(buffer)

        # set position to MISSING
        pos = NDPosition()

        # if the Item3D is not MISSING, the next 12 bytes contain the position
        if self.status != Status3D.Missing:
            # 4 bytes   (float) X position
            x = unpack_float(buffer)
            # 4 bytes   (float) Y position
            y = unpack_float(buffer)
            # 4 bytes   (float) Z position
            z = unpack_float(buffer)
            pos = NDPosition(x, y, z)

        # Item3D component data consists of one NDPosition
        self.add_data(pos)

    @property
    def pos(self):
        # Item3D component data contains the 3D position of the object
        return self.component_data

    def str(self, indent=""):
        return f"{indent}Marker_{self.index} ({self.status:13}): {self.component_data}\n"


class Component3D(GBFComponent):
    """ 3D Data Component formatted in the General Binary Format

        Each 3D Component contains
            - Tool Handle               2 bytes
            - Number of 3Ds             2 bytes
            - 3D Data Items             16 bytes per item
    """
    def __init__(self, buffer):
        self.port_handle = 0
        self.num_items = 0
        super().__init__(buffer)

    def parse(self, buffer):
        # 2 bytes   (int) tool handle
        self.port_handle = unpack_int(buffer)
        # 2 bytes   (int) number of 3D items
        self.num_items = unpack_int(buffer)

        # Component3D component data consists of num_items Item3D components
        for i in range(self.num_items):
            self.add_data(Item3D(buffer))

    def str(self, indent=""):
        out_str = f"{indent}Tool_{self.port_handle} ({self.num_items} markers)\n"
        if self.has_data:
            out_str += self.str_data(indent + "  ")
        return out_str
    
class ItemMarkerError(GBFComponent):
    """ 3D Marker error item formatted in the General Binary Format

        Each 3D Data item contains
            - Marker Index              2 bytes
            - Marker error              4 bytes
    """
    def __init__(self, buffer):
        self.index = 0
        super().__init__(buffer)

    def parse(self, buffer):
        # 2 bytes   (int) marker index
        self.index = unpack_int(buffer)

        # 4 bytes (float) marker error
        error = unpack_float(buffer)

        # ItemMarkerError component data consists of one error
        self.add_data(error)

    @property
    def error(self):
        # ItemMarkerError component data contains the marker error of the object
        return self.component_data

    def str(self, indent=""):
        return f"{indent}Marker_{self.index}: {self.component_data}\n"

class ComponentMarkerError(GBFComponent):
    """ 3D Marker Error Component formatted in the General Binary Format

        Each 3D Error Component contains
            - Tool Handle               2 bytes
            - Number of errors          2 bytes
            - 3D Error Items            2-byte short for marker index, 4-byte float error
    """
    def __init__(self, buffer):
        self.port_handle = 0
        self.num_items = 0
        super().__init__(buffer)

    def parse(self, buffer):
        # 2 bytes   (int) tool handle
        self.port_handle = unpack_int(buffer)
        # 2 bytes   (int) number of 3D items
        self.num_items = unpack_int(buffer)

        # ComponentMarkerError component data consists of num_items ItemMarkerError components
        for i in range(self.num_items):
            self.add_data(ItemMarkerError(buffer))

    def str(self, indent=""):
        out_str = f"{indent}Tool_{self.port_handle} ({self.num_items} marker errors)\n"
        if self.has_data:
            out_str += self.str_data(indent + "  ")
        return out_str

class Component6D(GBFComponent):
    """ 6D Data component formatted in the General Binary Format

        Each 6D Component contains
            - Tool handle               2 Bytes
            - Status                    2 Bytes
                status bits 0-7 provide the error code
                status bit  8   indicates if transform is MISSING
                status bits 13-15 indicate which face is being tracked
            - Q0                        4 Bytes
            - Qx                        4 Bytes
            - Qy                        4 Bytes
            - Qz                        4 Bytes
            - Tx                        4 Bytes
            - Ty                        4 Bytes
            - Tz                        4 Bytes
            - Error                     4 Bytes
    """
    def __init__(self, buffer):
        self.port_handle = 0
        self.status = 0
        super().__init__(buffer)

    def parse(self, buffer):
        # 2 bytes   (int) tool handle
        self.port_handle = unpack_int(buffer)
        # 2 bytes   (int) status bytes
        self.status = unpack_int(buffer)
        if self.is_missing:
            # if MISSING, there is no pose data. Set pose to MISSING
            self.add_data(NDPose())
        else:
            # if VALID, the pose data follows. Add pose to the component data
            q0 = unpack_float(buffer)
            qx = unpack_float(buffer)
            qy = unpack_float(buffer)
            qz = unpack_float(buffer)
            tx = unpack_float(buffer)
            ty = unpack_float(buffer)
            tz = unpack_float(buffer)
            err_val = unpack_float(buffer)
            self.add_data(NDPose([q0, qx, qy, qz, tx, ty, tz], err=err_val))

    @property
    def pose(self):
        return self.component_data

    @property
    def is_missing(self):
        """ Port/Tool Status contains information about the status of the 6D Component
        Status is a 2 byte field and is interpreted as follows:
            Bit 8   - Transform missing
        """
        return (self.status & 0x0100) == 0x0100

    def str(self, indent=""):
        return f"{indent}Tool_{self.port_handle} ({self.status:12}): {self.pose}\n"


class ComponentImage(GBFComponent):
    def __init__(self, buffer):
        self.item_type = 0
        self.sensor = 0
        self.frame_index = 0
        self.frame_number = 0
        self.trigger_threshold = 0.0
        self.background_threshold = 0.0
        self.exposure = 0
        self.stride = 0
        self.image_depth = 0
        self.image_X = 0
        self.image_Y = 0
        self.image_width = 0
        self.image_height = 0
        self.meta_data_len = 0
        self.meta_data = ""
        self.image = None
        super().__init__(buffer)

    def parse(self, buffer):
        # 1 byte    item type
        self.item_type = unpack_int(buffer, 1)
        # 1 byte    sensor
        self.sensor = unpack_int(buffer, 1)
        # 1 byte    frame type
        self.type = FrameType(unpack_int(buffer, 1))
        # 1 byte    frame index
        self.frame_index = unpack_int(buffer, 1)
        # 4 bytes   frame number
        self.frame_number = unpack_int(buffer, 4)
        # 4 bytes   trigger threshold
        self.trigger_threshold = unpack_float(buffer)
        # 4 bytes   background threshold
        self.background_threshold = unpack_float(buffer)
        # 2 bytes   exposure
        self.exposure = unpack_int(buffer, 2)
        # 1 byte    stride
        self.stride = unpack_int(buffer, 1)
        # 1 byte    image depth - bits per pixel
        self.image_depth = unpack_int(buffer, 1)
        # 8 bytes   image area - X, Y, Width, Height
        self.image_X = unpack_int(buffer, 2)
        self.image_Y = unpack_int(buffer, 2)
        self.image_width = unpack_int(buffer, 2)
        self.image_height = unpack_int(buffer, 2)
        # 4 bytes   metadata length
        self.meta_data_len = unpack_int(buffer, 4)
        # M bytes   metadata
        self.meta_data = unpack_char(buffer, self.meta_data_len)
        # Image
        image_size = self.image_width * self.image_height

        # Parse the data based on the item type (RAW, PGM, TIFF, JPEG)
        if self.item_type == 0:
            # 0 = RAW format
            if self.image_depth > 8:
                # TODO: Determine if this is the way that we want to receive colour images
                # handle colour images (2 bytes per pixel)
                image_size = image_size * 2
            else:
                # image size is based on depth
                image_size = image_size / (8 / self.image_depth)
            self.image = unpack_bytes(buffer, image_size)
        elif self.item_type == 1:
            # 1 = PGM format
            # PGM header
            pgm_header = unpack_string(buffer)  # read until \n. should be P5 or P2 for PGM files
            self.image = bytearray(pgm_header.encode("ascii"))
            # PGM files contain string data first
            # The first string is 'NDCAM' and the last string is '65535'
            pgm_info = []
            while True:
                s = unpack_string(buffer)
                pgm_info.append(s)
                self.image += bytearray(s.encode("ascii"))
                if s.endswith("  65535\n" or "  255\n" or "  15\n" or "  3\n" or "  1\n"):
                    break

            # the actual image follows. Each pixel is 2 bytes
            image_size = image_size * 2
            self.image += unpack_bytes(buffer, image_size)
        elif self.item_type == 2:
            # 2 = TIFF format
            # TODO: Parse TIFF format
            pass
        elif self.item_type == 3:
            # 3 = JPEG format
            # TODO: Parse JPEG format
            pass
        else:
            pass

    def str(self, indent=""):
        if self.image is None:
            img = "no img"
        else:
            img = f"img of size {len(self.image)}"
        return f"{indent}{self.type}:{self.frame_number}: " \
               f"{self.item_type}:{self.sensor}:{self.frame_index}:" \
               f"{self.trigger_threshold}:{self.background_threshold}:{self.exposure}:{self.stride}:" \
               f"{self.image_depth}:{self.image_X}:{self.image_Y}:{self.image_width}:{self.image_height}:" \
               f"{self.meta_data_len}:{self.meta_data}:{img}"


class ComponentAlert(GBFComponent):
    """ System Alert Component formatted in the General Binary Format
        Contains all current system faults, alerts, and events.

        Each Alert Component contains:
            - Types                     1 Byte
            - -reserved-                1 Byte
            - Code                      2 Bytes
    """
    def __init__(self, buffer):
        self.code = 0
        super().__init__(buffer)

    def parse(self, buffer):
        # 1 byte    alert type
        self.type = SystemAlertType(unpack_int(buffer, 1))
        # 1 byte    -reserved-
        unpack_int(buffer, 1)
        # 1 byte    alert code
        if self.type == SystemAlertType.Fault:
            self.code = FaultCode(unpack_int(buffer))
        elif self.type == SystemAlertType.Alert:
            self.code = AlertCode(unpack_int(buffer))
        elif self.type == SystemAlertType.Event:
            self.code = EventCode(unpack_int(buffer))
        else:
            self.code = unpack_int(buffer)

    def str(self, indent=""):
        return f"{indent}{self.type}: {self.code}\n"


class FrameItem(GBFComponent):
    """ A frame item formatted in the General Binary Format

        The Frame Item contains
            - Frame Type                1 Byte
            - Frame Sequence Index      1 Byte
            - Frame Status              2 Bytes
            - Frame Number              4 Bytes
            - timestamp_S               8 Bytes
            - data                      general binary payload
    """
    def __init__(self, buffer):
        self.index = 0
        self.status = 0
        self.frame_number = 0
        self.timestamp_S = 0
        self.timestamp_nS = 0
        super().__init__(buffer)

    def parse(self, buffer):
        # 1 byte    (int) Frame Type
        self.type = FrameType(unpack_int(buffer, 1))
        # 1 byte    (int) Frame Sequence Index
        self.index = unpack_int(buffer, 1)
        # 2 bytes   (int) Frame Status
        self.status = unpack_int(buffer)
        # 4 bytes   (int) Frame Number
        self.frame_number = unpack_int(buffer, 4)
        # 4 bytes   (int) Timestamp (seconds)
        self.timestamp_S = unpack_int(buffer, 4)
        # 4 bytes   (int) Timestamp (nanoseconds)
        self.timestamp_nS = unpack_int(buffer, 4)

        # parse the frame item payload. Frame data is formatted in GBF
        self.add_data(GeneralBinaryPayload(buffer))

    def str(self, indent=""):
        out_str = f"{indent}{self.type} Frame ({ctime(self.timestamp_S)}) - {self.frame_number}: {self.status}\n"
        out_str += self.str_data(indent + "  ")
        return out_str
