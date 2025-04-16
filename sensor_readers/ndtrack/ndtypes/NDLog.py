# NDLog.py
# Definitions used for logging 

# import standard libraries
from enum import IntEnum
import logging


# additional log levels
class NDLogLevel(IntEnum):
    Debug = logging.DEBUG           # Debug messages
    Communications = 12             # Communications with the tracking system
    API = 15                        # API function calls
    Info = logging.INFO             # Informational log messages
    Test = 25                       # Test suite messages
    Warning = logging.WARNING       # Warnings
    Error = logging.ERROR           # Errors
    Critical = logging.CRITICAL     # Critical Error


def main():
    logging.addLevelName(NDLogLevel.Communications, "COMM")
    print(logging.getLevelName(NDLogLevel.Communications))
    logging.addLevelName(NDLogLevel.API, "API ")
    print(logging.getLevelName(NDLogLevel.API))
    logging.addLevelName(NDLogLevel.API, "TEST")
    print(logging.getLevelName(NDLogLevel.Test))


if __name__ == "__main__":
    main()
