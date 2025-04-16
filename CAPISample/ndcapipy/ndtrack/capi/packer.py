"""
Data packing utilities used for converting from data bytes to other data types

Examples:
    hex_value = ascii_to_hex(bytes)
    unpack_bytes(buffer, num_bytes)
    unpack_char(buffer, num_chars)
"""

# import standard libraries
import struct


def ascii_to_hex(buffer, n=2):
    """ Literal conversion of ASCII characters into hexadecimal values.
    Assumes buffer is a list of characters.
    Since lists are mutable, the original buffer passed into this function will be affected.

    Args:
        buffer: list of characters to be converted
        n: number of characters to convert

    Returns:
        hexidecimal representation of the first n bytes in buffer
    """
    h = 0
    for i in range(n):
        ch = ord(buffer.pop(0))
        # Convert hex ASCII digits to values to add to the final value.
        if (ch >= ord('0')) and (ch <= ord('9')):
            ch -= ord('0')
        elif (ch >= ord('A')) and (ch <= ord('F')):
            ch = 0x0000000A + (ch - ord('A'))
        elif (ch >= ord('a')) and (ch <= ord('f')):
            ch = 0x0000000A + (ch - ord('a'))
        else:
            # This is a non-hex character; the input is invalid.
            return 0
        h |= (ch << (4 * (n - 1 - i)))
    return h


def unpack_bytes(buffer, n=1) -> bytes:
    """ Pop n number of bytes from buffer and return them.
    Buffer is a bytearray. Since bytearrays are mutable, the original buffer passed into this function will be affected.

    Args:
        buffer: bytearray containing packed data
        n: number of bytes to return

    Returns:
        the fist n bytes of buffer
    """
    if n < 0 or len(buffer) < n:
        raise IndexError("Index out of range in unpack_bytes()")
    return_bytes = buffer[:n]
    del buffer[:n]
    return return_bytes


def unpack_char(buffer, n=1) -> str:
    """ Pop n number of characters from buffer and return them.
    Buffer is a bytearray. Since bytearrays are mutable, the original buffer passed into this function will be affected.

    Args:
        buffer: bytearray containing packed data
        n: number of characters to return

    Returns:
        the first n characters of buffer
    """
    if n < 0 or len(buffer) < n:
        raise IndexError("Index out of range in unpack_char()")

    return_char = ""
    for i in range(n):
        return_char += chr(buffer.pop(0))
    return return_char


def unpack_string(buffer) -> str:
    """ Pop characters from buffer until \n is encountered
    Buffer is a bytearray. Since bytearrays are mutable, the original buffer passed into this function will be affected.
    """
    return_str = ""
    while len(buffer) > 0:
        return_str += unpack_char(buffer, 1)
        if return_str[-1] == '\n':
            return return_str


def unpack_int(buffer, n=2) -> int:
    """ Pop n bytes from buffer and interpret them as an integer. Integer may be 2-4 bytes.
    Buffer is a bytearray. Since bytearrays are mutable, the original buffer passed into this function will be affected.
    Data is stored in little-endian format.

    Args:
        buffer: bytearray containing packed data
        n: number of bytes to unpack

    Returns:
        the first n bytes of the buffer, interpreted as an integer
    """
    if n < 1 or n > 4 or len(buffer) < n:
        raise IndexError("Index out of range in unpack_int()")

    # first byte
    a = buffer.pop(0)
    b = 0
    c = 0
    d = 0

    if n == 1:
        pass
    if n >= 2:
        b = buffer.pop(0)
    if n >= 3:
        c = buffer.pop(0)
    if n >= 4:
        d = buffer.pop(0)

    # data is stored in little-endian format
    return struct.unpack('<i', bytes([a, b, c, d]))[0]


def unpack_uint(buffer, n=2) -> int:
    """ Pop n bytes from buffer and interpret them as an unsigned integer. Integer may be 2-4 bytes.
    Buffer is a bytearray. Since bytearrays are mutable, the original buffer passed into this function will be affected.
    Data is stored in little-endian format.

    Args:
        buffer: bytearray containing packed data
        n: number of bytes to unpack

    Returns:
        the first n bytes of the buffer, interpreted as an unsigned integer
    """
    if n < 1 or n > 4 or len(buffer) < n:
        raise IndexError("Index out of range in unpack_uint()")

    # first byte
    a = buffer.pop(0)
    b = 0
    c = 0
    d = 0

    if n == 1:
        pass
    if n >= 2:
        b = buffer.pop(0)
    if n >= 3:
        c = buffer.pop(0)
    if n >= 4:
        d = buffer.pop(0)

    # data is stored in little-endian format
    return struct.unpack('<I', bytes([a, b, c, d]))[0]


def unpack_float(buffer) -> float:
    """ Pop 4 bytes from buffer and interpret them as float.
    Buffer is a bytearray. Since bytearrays are mutable, the original buffer passed into this function will be affected.
    Data is stored in little-endian format.

    Args:
        buffer: bytearray containing packed data

    Returns:
        the first n bytes of the buffer, interpreted as a float
    """
    if len(buffer) < 4:
        raise IndexError("Index out of range in unpack_float()")

    a = buffer.pop(0)
    b = buffer.pop(0)
    c = buffer.pop(0)
    d = buffer.pop(0)

    # data is stored in little-endian format
    return struct.unpack('<f', bytes([a, b, c, d]))[0]
