# NDStatus.py
# NDI Status
# Class used to maintain status and status information

# import standard libraries
from enum import IntEnum, unique

# import NDTypes libraries
from ndtrack.ndtypes.NDLog import *


@unique
class NDStatusCode(IntEnum):
    """ NDStatusCode enumerator
        Enumerated list of NDI Status Codes
        0 is OKAY
        >0 is WARNING
        <0 is ERROR
    """
    OKAY = 0
    WARNING = 1
    TIMEOUT = 10
    ERROR = -1
    SYSTEM_ERROR = -2
    FILE_ERROR = -3
    COM_ERROR = -4
    PARAM_ERROR = -5
    USE_ERROR = -10
    IMPLEMENTATION_ERROR = -99


class NDStatus:
    """ Status information
        A status contains a status state, code and status information.
    """

    def __init__(self, state=NDStatusCode.OKAY, code=0, message=""):
        self._state = state
        self.code = code
        self._message = message

    def __str__(self):
        status_string = "{}: {}".format(self._translation(), self.info)
        return status_string

    def __eq__(self, other):
        return self.value == other

    @property
    def value(self):
        return self._state

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, val):
        self._code = val

    @property
    def info(self):
        return self._message

    def _translation(self) -> str:
        status_str = {NDStatusCode.OKAY: '[OK]',
                      NDStatusCode.WARNING: '[WRN]',
                      NDStatusCode.ERROR: '[ERR]',
                      NDStatusCode.SYSTEM_ERROR: '[ERR_S]',
                      NDStatusCode.FILE_ERROR: '[ERR_F]',
                      NDStatusCode.COM_ERROR: '[ERR_C]',
                      NDStatusCode.PARAM_ERROR: '[ERR_P]',
                      NDStatusCode.USE_ERROR: '[ERR_U]',
                      NDStatusCode.IMPLEMENTATION_ERROR: '[ERR_I]'
                      }
        try:
            return status_str[self.value]
        except KeyError:
            # unknown error code
            return '[   ]'

    def is_ok(self):
        return self.value == NDStatusCode.OKAY

    def is_warning(self):
        return self.value == NDStatusCode.WARNING

    def is_error(self):
        return not self.is_ok() and not self.is_warning()

    def log(self):
        logging.info(str(self))


class NDStatusOK(NDStatus):
    """ OK Status """

    def __init__(self, message=""):
        super().__init__(NDStatusCode.OKAY, 0, message)


class NDStatusError(NDStatus):
    """ Error status """

    def __init__(self, code=0, message=""):
        super().__init__(NDStatusCode.ERROR, code, message)


class NDStatusWarning(NDStatus):
    """ Warning status """

    def __init__(self, code=0, message=""):
        super().__init__(NDStatusCode.WARNING, code, message)
