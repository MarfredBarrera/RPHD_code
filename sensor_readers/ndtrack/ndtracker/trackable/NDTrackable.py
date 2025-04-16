# NDTrackable.py
# Definition of NDI Trackable devices in python
# Implementation of abstract NDTrackable python class

from ndtrack.ndtypes.NDDataTypes import *


class NDTrackable(ABC):
    def __init__(self):
        # Assume that trackable object have a Pose (position and orientation)
        # the `data` member may be overloaded by subclasses of NDTrackable
        # using the specific NDDataType that represents the trackable object
        self.data = NDPose()

        self.id = None
        self.status = 0

    def __str__(self):
        if self.is_missing:
            return f"{self.name}: MISSING"
        else:
            return f"{self.name}: {self.data}"

    @property
    @abstractmethod
    def name(self):
        return "Item"

    @property
    def is_missing(self):
        return self.data.is_missing()


class NDMarker(NDTrackable):
    def __init__(self):
        super().__init__()
        # NDMarkers have 3D position initialized to MISSING
        self.update(NDPosition())

    def update(self, pos: NDPosition, status=0):
        # update the position of the marker
        self.data = pos
        self.status = status

    def __str__(self):
        return super().__str__() + " status=%s" % (self.status)

    @property
    @abstractmethod
    def name(self):
        # default name of a marker
        # child classes that override NDMarker should override this method
        return "Marker"

    @property
    def pos(self):
        # return the position of the marker, which is stored in the `data` member
        return self.data


class NDTool(NDTrackable):
    def __init__(self):
        super().__init__()

        # list of markers that make up the tool
        self.markers = []

    def __str__(self):
        if self.is_missing:
            return "%s: MISSING status=0x%02x" % (self.name, self.status )# f"{self.name}: MISSING"
        else:
            return "%s: %s status=0x%02x%s" % (self.name, self.data, self.status, self.markers_str) # f"{self.name}: {self.data} status=0x%x" + f"{self.markers_str}"

    @property
    def markers_str(self):
        out = ""
        for m in self.markers:
            out += f"\n\t{m}"
        return out

    def update(self, pose: NDPose, status: int):
        # update the pose of the tool
        self.data = pose
        self.status = status

    @property
    @abstractmethod
    def name(self):
        # default name of a tool
        # child classes that override NDTool should override this method
        return "Tool"

    @property
    def pose(self):
        # return the pose of the tool, which is stored in the `data` member
        return self.data
