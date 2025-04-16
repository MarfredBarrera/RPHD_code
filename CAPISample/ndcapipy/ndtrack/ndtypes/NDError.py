# error.py
# Definition of ndtrack error

# import standard libraries
import inspect
import traceback

# import NDTypes libraries
from ndtrack.ndtypes.NDStatus import *


class NDError(Exception):
    """ Exception raised when an error is encountered

    Properties:
        code: code associated with this error (default: ERROR)

    NDError exceptions are to be raised when an error is encountered in NDTrack.
    When an NDError exception is caught, raising a new NDError 'from'
    the original NDError will append the original error information,
    creating a thorough log of the error including the function stack.
    """
    def __init__(self, error_code, message, source=None):
        self._status = NDStatusError()
        self._code = error_code
        self._msg = message

        # function where exception occurred
        caller = inspect.stack()[1].function

        if source is None:
            # source not known, use the calling function
            self._fn = caller
        elif isinstance(source, str):
            # source described as a string, use the description
            self._fn = source
        else:
            # source is a class, use class_name::calling_function
            self._fn = f"{type(source).__name__}::{caller}"

    def __str__(self):
        return f"NDError [{self.code}] :\r\n\t{self.str}"

    @property
    def str(self):
        """ String representation of the error

        If this exception derives from another exception, that exception's string will be appended to the
        message associated with this exception.
        """

        if self.__cause__ is None:
            # no known cause, just use the specified message
            msg = self._msg
        else:
            # append the error message to any messages from a previous cause
            if isinstance(self.__cause__, NDError):
                msg = f"{self._msg}\r\n\t{self.__cause__.str}"
            else:
                # if this is a system exception, use format_exception to get ExceptionType: Exception Message
                emsg = traceback.format_exception(None, self.__cause__, self.__cause__.__traceback__, 1, False)[-1][:-1]
                msg = f"{self._msg}\r\n\t{emsg}"

        # return the error information in string format
        return f"{self._fn} : {msg}"

    @property
    def code(self):
        """ Error code associated with this exception """
        # return the error code
        return self._code
