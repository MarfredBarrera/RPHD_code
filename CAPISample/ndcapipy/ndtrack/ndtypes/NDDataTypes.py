# NDDataTypes.py
# Data Types used by ndtrack
# Allows all data to be stored in a common data type

# import standard libraries
from abc import ABC, abstractmethod
from typing import Union, Optional
import numpy as np

# import NDI libraries
from ndtrack.ndtypes.NDError import *

# ndlib constants
BAD_FLOAT = -3.697314E28  # representation of MISSING value
MAX_NEGATIVE = -3.0E28  # used to determine if values are MISSING


def ndi_missing_value():
    """ Return the value devined by NDI as MISSING """
    return BAD_FLOAT


def ndi_is_missing(item) -> bool:
    """ Indicate if the specified item is MISSING
        MISSING is defined as BAD_FLOAT, which is less than MAX_NEGATIVE

    Args:
        item:  floating point item to be checked

    Returns:
        True if the item is BAD_FLOAT, which indicates a MISSING value
    """
    return np.isnan(item) or item < MAX_NEGATIVE


class NDDataType(ABC):
    """ NDDataType
        A data type used by NDI.
        NDI data types subclass from this class.
        Can be instatiated using values, lists or a string.

        All data is stored in the list self.data
        Subclasses of NDDataType must interpret self.data appropriately

        NDI data types typically contain a measurement error (meas_err)
    """

    def __init__(self, data: Union[np.array, list], err: Optional[float] = 0.0):
        """ Initialize NDDataType
            All ND data types hold their data in a list (data)
            ND data types typically contain a measurement error (meas_err)

        Args:
            data: numpy array of floating point values
            err: measurement error
        """
        if isinstance(data, list):
            # allow initialization using a python list
            self.data = np.array(data)
        else:
            # data must be a numpy array
            self.data = data
        self.meas_err = err

        # equal to within 1/2 micron
        self._eq_tolerance = 0.0005

    def __str__(self):
        return self.to_str()

    def to_str(self, indent: Optional[str] = "") -> str:
        """ Provide a string representation of NDDataType
            All ND data types can be displayed as a string of float values
            If the values are MISSING, display the string 'MISSING'

        Args:
            indent: Indentation to precede this string. No indentation by default

        Returns:
            The string representation of this object
        """
        out_str = ""
        for item in self.data:
            if ndi_is_missing(item):
                out_str += f"{indent}{'MISSING':>10}"
            else:
                out_str += f"{indent}{item:10.3f}"
        out_str += f"{self.meas_err:10.3f}"
        return out_str

    def __eq__(self, other):
        """ Compare two NDDataTypes
            Distance between the two objects is less than the tolerance
        """
        if other is None:
            # if comparing to None, this is not equivalent
            return False
        if self.is_missing() and other.is_missing():
            # if both objects are MISSING, they are equivalent
            return True
        if self.is_missing() or other.is_missing():
            # if one object is MISSING but the other is not, they are not equivalent
            return False

        # objects are equivalent if the distance between them is less than the tolerance
        return self.distance(other) < self._eq_tolerance

    @abstractmethod
    def distance(self, other) -> float:
        """ Compute the distance between this and other """
        pass

    @property
    def data(self):
        """ Access to data member """
        return self._data

    @data.setter
    def data(self, value: np.array):
        """ Setter for data member """
        self._data = value

    def csv(self):
        """ Provide a comma separated representation of NDDataType
            The csv representation of an NDDataType contains the data

        Returns:
        string      comma separated string containing data
        """
        out_str = ""
        for item in self.data:
            if ndi_is_missing(item):
                out_str += "{},".format("MISSING")
            else:
                out_str += "{:.3f},".format(item)
        # return the concatenated string, removing the final comma
        return out_str[:-1]

    @classmethod
    def from_string(cls, data_string: str):
        """ Create an NDDataType derived object of the specified class
            The data for the object is parsed from the specified string

        Args:
            cls: class of the desired object
            data_string: comma separated string containing the data e.g. NDPosition("1,2,3")

        Returns:
            object of class specified by `cls`
        """
        str_data = data_string.split(',')
        data = [float(i) for i in str_data]
        obj = cls(data)
        return obj

    def is_missing(self):
        """ Indicate if this object contains MISSING data
            If any data item of data is MISSING,
            the entire object is said to be MISSING

        Returns:
        True if any data item is this object is MISSING
        """
        for item in self.data:
            if ndi_is_missing(item):
                return True
        return False

    def is_valid(self):
        """ Indicate if this object contains VALID data
            If an object is NOT MISSING, then it is VALID

        Returns:
        True if all data items in this object are VALID
        """
        return not self.is_missing()

    def set_missing(self):
        """ Set all data items to MISSING
            And set the measurement error to zero
        """
        # replace all of the data with BAD_FLOAT to indicate MISSING
        self.data = np.array([ndi_missing_value()] * len(self.data))
        self.meas_err = 0.0


class NDPosition(NDDataType):
    """ NDPosition
        Describes the position of an object in 3D space

        self.data contains a numpy array of 3 elements [x y z]
    """

    def __init__(self, x: Optional[Union[float, list]] = BAD_FLOAT, y: float = BAD_FLOAT, z: float = BAD_FLOAT,
                 err: float = 0.0):
        """ Initialize an NDPosition as an NDDataType
            NDPosition contains 3D coordinates for an object in 3D space,
            and a measurement error

        Args:
            x: X coordinate of the object in 3D space
            y: Y coordinate of the object in 3D space
            z: Z coordinate of the object in 3D space
            err: measurement error
        """
        if isinstance(x, list) or isinstance(x, np.ndarray):
            # allow NDPosition to be initialized using a list or numpy array
            # the list must contain 3 items [x,y,z]
            if len(x) != 3:
                raise NDError(NDStatusCode.USE_ERROR, "NDPosition requires 3 values (x, y, z)", self)
            # the default init function will convert list to numpy array if necessary
            super().__init__(x, err)
        else:
            # initialize NDPosition numpy array
            super().__init__([x, y, z], err)

    def __neg__(self):
        """ Negative of this NDPosition

        Returns:
            NDPosition. Position with -x, -y, -z
        """
        if self.is_missing():
            return self

        return NDPosition(-self.x, -self.y, -self.z)

    def __add__(self, other):
        """ Add a NDPosition to this one

        Returns:
            NDPosition. Sum of self and other. If either is MISSING, return MISSING
        """
        if self.is_missing():
            return self
        if other.is_missing():
            return other

        return NDPosition(self.data + other.data)

    def __sub__(self, other):
        """ Subtract other NDPosition from this one

        Returns:
            NDPosition. self - other. If either is MISSING, return MISSING
        """
        return self + (-other)

    @property
    def x(self):
        """ Accessor for the X coordinate of the object
            self.data contains numpy array of 3 elements [x y z]

        Returns:
        float   -- X coordinate of the object in 3D space
        """
        return self.data[0]

    @x.setter
    def x(self, value):
        self.data[0] = value

    @property
    def y(self):
        """ Accessor for the Y coordinate of the object
            self.data contains numpy array of 3 elements [x y z]

        Returns:
        float   -- Y coordinate of the object in 3D space
        """
        return self.data[1]

    @y.setter
    def y(self, value):
        self.data[1] = value

    @property
    def z(self):
        """ Access to the Z coordinate of the object
            self.data contains numpy array of 3 elements [x y z]

        Returns:
        float   -- Z coordinate of the object in 3D space
        """
        return self.data[2]

    @z.setter
    def z(self, value):
        self.data[2] = value

    def len(self):
        """ Compute the distance between the origin and this NDPosition

        Returns:
        float   -- length of vector from origin to NDPosition
        """
        if self.is_missing():
            return ndi_missing_value()

        return np.sqrt(np.sum(self.data ** 2))

    def distance(self, other) -> float:
        """ Return the distance between this NDPosition and another NDPosition
            Eucledian distance = sqrt((x1-x2)^2 + (y1-y2)^2 + (z1-z2)^2)

        Returns:
        float   -- distance from self to other
        """
        if self.is_missing() or other.is_missing():
            return ndi_missing_value()

        # distance between two 3D points
        # square root of the sum of the squares of the differences between corresponding coordinates
        return np.sqrt(np.sum((self.data - other.data) ** 2))

    def dot(self, other):
        """ Compute the dot product between this NDPosition and other NDPosition
            Dot product = sum of product of each component

        Returns:
        float   -- dot product between self and other
        """
        if self.is_missing() or other.is_missing():
            return ndi_missing_value()

        # compute dot product using numpy
        return np.dot(self.data, other.data)

    def cross(self, other):
        """ Compute the cross product between this NDPosition and other NDPosition
            Cross product = vector perpendicular to plane described two vectors

        Returns:
        NDPosition  -- cross product between self and other
        """
        if self.is_missing():
            return self
        if other.is_missing():
            return other

        # compute the cross product using numpy
        return NDPosition(list(np.cross(self.data, other.data)))


class NDRotation(NDDataType):
    """ NDRotation
        Describes a rotation of an object
        The data is maintained in quaternion format,
        but may be acquired in other formats (euler, matrix)

        self.data contains a numpy array of 4 elements
        [q0 qx qy qz]
    """

    def __init__(self, q0: Optional[Union[float, list]] = BAD_FLOAT,
                 qx: float = BAD_FLOAT, qy: float = BAD_FLOAT, qz: float = BAD_FLOAT, err: float = 0.0):
        """ Initialize an NDRotation as an NDDataType
            NDRotation contains quaternion representation of a rotation
            and a measurement error

        Args:
            q0:  q0 parameter of quaternion rotation
            qx:  qx parameter of quaternion rotation
            qy:  qy parameter of quaternion rotation
            qz:  qz parameter of quaternion rotation
            err:  measurement error
        """
        if isinstance(q0, list) or isinstance(q0, np.ndarray):
            # allow NDRotation to be initialized using a list
            # the list must contain 4 items [q0,qx,qy,qz]
            # the default init function will convert list to numpy array
            if len(q0) != 4:
                raise NDError(NDStatusCode.USE_ERROR, "NDRotation requires 4 values (q0, qx, qy, qz)", self)
            super().__init__(q0, err)
        else:
            # initialize NDRotation
            super().__init__(np.array([q0, qx, qy, qz]), err)

        # equivalence tolerance is within 0.025 radians
        self._eq_tolerance = 0.025

        # normalize the quaternion
        self._normalize()

    def __mul__(self, other):
        """ combine rotations

        Args:
            other: NDRotation to combine with this one

        Returns:
            NDRotation. Combine self and other rotations. If either is MISSING, return MISSING
        """
        if self.is_missing():
            return self
        if other.is_missing():
            return other

        aw = self.q0
        ax = self.qx
        ay = self.qy
        az = self.qz
        bw = other.q0
        bx = other.qx
        by = other.qy
        bz = other.qz
        return NDRotation(-ax * bx - ay * by - az * bz + aw * bw,
                          ax * bw + ay * bz - az * by + aw * bx,
                          -ax * bz + ay * bw + az * bx + aw * by,
                          ax * by - ay * bx + az * bw + aw * bz)

    def _normalize(self):
        """ Normalize the quaternion
            This ensures mathematical functions on the quaternions are accurate
        """
        if self.is_missing():
            return False

        # compute the denominator
        norm = np.sqrt(np.sum(self.data ** 2))
        # if the denominator is close to zero, set to zero rotation
        if np.isclose(norm, 0.0):
            self.data = np.array([1.0, 0.0, 0.0, 0.0])
        else:
            # ensure that q0 is positive
            if self.q0 < 0.0:
                norm = -norm

            # compute the normalized data elements
            self.data = self.data / norm

    def distance(self, other):
        """ Return the angle between the rotation vector of this NDRotation and other NDRotation
        """
        if self.is_missing() or other.is_missing():
            return ndi_missing_value()

        # compute the dot product
        # cosine of the angle between two vectors is
        # equal to the dot product of the vectors divided by the product of vector magnitude
        angle = 2 * np.arccos(np.clip(np.dot(self.data, other.data), -1.0, 1.0))
        return angle

    def rotate_point(self, point):
        """ Rotate the specified point using this rotation

        Returns:
        NDPosition  -- point rotated by self
        """
        if self.is_missing() or point.is_missing():
            return NDPosition()

        # compute cross product of the rotation vector and the point
        rot = NDPosition(self.qx, self.qy, self.qz)
        cross = rot.cross(point)
        # compute the rotation
        rotated = NDPosition(point.x + 2.0 * (self.q0 * cross.x + self.qy * cross.z - self.qz * cross.y),
                             point.y + 2.0 * (self.q0 * cross.y + self.qz * cross.x - self.qx * cross.z),
                             point.z + 2.0 * (self.q0 * cross.z + self.qx * cross.y - self.qy * cross.x))
        return rotated

    @property
    def q0(self):
        """ Accessor for the q0 component of the rotation
            self.data contains numpy array of 4 elements [q0 qx qy qz]

        Returns:
        float   -- q0 component of quaternion rotation
        """
        return self.data[0]

    @property
    def qx(self):
        """ Accessor for the qx component of the rotation
            self.data contains numpy array of 4 elements [q0 qx qy qz]

        Returns:
        float   -- qxx component of quaternion rotation
        """
        return self.data[1]

    @property
    def qy(self):
        """ Accessor for the qy component of the rotation
            self.data contains numpy array of 4 elements [q0 qx qy qz]

        Returns:
        float   -- qy component of quaternion rotation
        """
        return self.data[2]

    @property
    def qz(self):
        """ Accessor for the qz component of the rotation
            self.data contains numpy array of 4 elements [q0 qx qy qz]

        Returns:
        float   -- qz component of quaternion rotation
        """
        return self.data[3]


class NDPose(NDDataType):
    """ NDPose
        Describes 6D pose, made up of position and orientation

        self.data contains a numpy array of 7 elements
        [q0 qx qy qz x y z]
    """

    def __init__(self, pos: Optional[Union[NDPosition, list]] = NDPosition(), rot=NDRotation(), err=0.0):
        if isinstance(pos, list) or isinstance(pos, np.ndarray):
            # allow NDPose to be initialized using a list
            # the list must contain 7 items [q0,qx,qy,qz,x,y,z]
            # the default init function will convert list to numpy array
            if len(pos) != 7:
                raise NDError(NDStatusCode.USE_ERROR, "NDPose requires 7 values (q0, qx, qy, qz, x, y, z)", self)
            super().__init__(pos, err)
        else:
            # initialize NDPose
            super().__init__(np.concatenate((rot.data, pos.data)), err)

    def __eq__(self, other):
        return self.pos == other.pos and self.rot == other.rot

    def __mul__(self, other):
        """ combine NDPose

        Args:
            other:  NDPose to combine with this one

        Returns:
            NDPose. Multiplication of self and other. If either is MISSING, return MISSING
        """
        if self.is_missing():
            return self
        if other.is_missing():
            return other

        rot12 = self.rot.data
        rot23 = other.rot.data
        rot_a = (rot23[0] + rot23[1]) * (rot12[0] + rot12[1])
        rot_b = (rot23[3] - rot23[2]) * (rot12[2] - rot12[3])
        rot_c = (rot23[1] - rot23[0]) * (rot12[2] + rot12[3])
        rot_d = (rot23[2] + rot23[3]) * (rot12[1] - rot12[0])
        rot_e = (rot23[1] + rot23[3]) * (rot12[1] + rot12[2])
        rot_f = (rot23[1] - rot23[3]) * (rot12[1] - rot12[2])
        rot_g = (rot23[0] + rot23[2]) * (rot12[0] - rot12[3])
        rot_h = (rot23[0] - rot23[2]) * (rot12[0] + rot12[3])
        rot13 = NDRotation(rot_b + (-rot_e - rot_f + rot_g + rot_h) / 2.0,
                           rot_a - (rot_e + rot_f + rot_g + rot_h) / 2.0,
                           -rot_c + (rot_e - rot_f + rot_g - rot_h) / 2.0,
                           -rot_d + (rot_e - rot_f - rot_g + rot_h) / 2.0)

        rotated = other.rot.rotate_point(self.pos)
        combined = rotated + other.pos
        return NDPose(combined, rot13)

    def csv(self):
        """ Provide a comma separated representation of NDPose

        Returns:
        string      comma separated string containing data and meas_err
        """
        out_str = super().csv()
        # append the measurement error
        out_str += ",{:.3f}".format(self.meas_err)
        return out_str

    @property
    def pos(self):
        """ Accessor for the position component of the pose
            self.data contains numpy array of 7 elements [q0 qx qy qz x y z]

        Returns:
        NDPosition  -- position component of pose
        """
        return NDPosition(self.data[4:], self.meas_err)

    @property
    def rot(self):
        """ Accessor for the transformation component of the pose
            self.data contains list of 7 elements [q0,qx,qy,qz,x,y,z]

        Returns:
        NDRotation  -- transformation component of pose
        """
        return NDRotation(self.data[:4])

    def distance(self, other):
        """ Distance between two poses is the positional distance """
        return self.pos.distance(other.pos)
