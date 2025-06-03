"""
Author: Konstantinos Angelopoulos
Date: 04/02/2020
All rights reserved.
Feel free to use and modify and if you like it give it a star.

Use on Linux or Windows only for Python 3.4.x+ (Tested for Python 3.6.8).
Simply read ascii or binary and translate to force (N) and torque (Nm).
"""
import serial
import time
import os
from optparse import OptionParser
import keyboard
from datetime import datetime
import numpy as np


class Sensor(object):

    def __init__(self, port, mode='ascii'):
        """
        Initialize the connection to the ATI FT controller
        :param port: COM port that the sensor is connected on
        :param mode: communication mode (ascii or binary)
        :return None
        """
        print('[ATI FT SENSOR]: Connecting via serial...')
        try:
            count = 0
            self._bias = [.0, .0, .0, .0, .0, .0]  # Store value to bias forces and torques
            self.reset_time = None
            self._mode = mode.lower()
            # Initialize connection
            self.connection = serial.Serial(port, timeout=1, baudrate=38400, parity='N', stopbits=1)
            # if os.name == 'nt':
            #     pass
            # else:
                # self.connection.open()  # Only for linux
            
            print('[ATI FT SENSOR]: Connected.')

            # Initialise Sensor
            self.initialise()
            while not self.start():
                count = count + 1
                self.initialise()
                if count == 20:
                    print('[ATI FT SENSOR]: Initialising... ')

            self.last_access = time.time()
            self.last_value = []
            print('[ATI FT SENSOR]: Started...')
        except Exception as e:
            print('[ATI FT SENSOR]: ATI FT Sensor not connected... \n {}'.format(e))

    def read(self):
        """
        The read string from the sensor is in format as bytes in binary mode:
        b'\x00\xff\x93\xff\x98\xfei\xff\xbb\x00\x06\xff\xdb\x06\r\n>QS'
        the first value \x00 is an error id that shows that everything is fine if its zero
        or that there is a problem if its not. The other 12 bytes must be paired to compute the counts,
        thus, \xff\x93 is the count for force in x axis \xff\x98 is the count in y axis and so on.
        These values are counts and must be divided properly according to the calibration (see counts_2_force function below).
        The /x06 is the <ACK> command, the /r is to match the carriage return and /n to make new line.
        :return bytes in format b'\x00\xff\x93\xff\x98\xfei\xff\xbb\x00\x06\xff\xdb\x06\r\n>QS'
        """
        if self._mode == 'binary':
            # # read message in bytes
            # read = self.connection.read(19)
            # # Check if sensor has started
            # while len(read) < 1 or read[0] != 0 or len(read) < 11 or read[-1] != 83:
            #     while not self.start():
            #         print('[ATI FT SENSOR]: Fixing Sequence')
            #     read = self.connection.read(19)

            # # # self.last_value = read
            # # # self.last_access = time.time()
            # return read

            buffer = b''

            while True:
                # Read a chunk of data from the sensor
                buffer += self.connection.read(65)  # Read a larger chunk to handle multiple messages

                # Process all valid messages in the buffer
                while len(buffer) >= 14:  # Ensure we have at least one full message and the next start byte
                    # Check if the first byte is 0x00
                    if buffer[0] == 0x00:
                        # Check if the 14th byte (start of the next message) is also 0x00
                        if buffer[13] == 0x00:
                            # Extract the valid message
                            message = buffer[:13]

                            # Remove the processed message from the buffer
                            buffer = buffer[13:]

                            # Return the valid message
                            return message
                        else:
                            # If the 14th byte is not 0x00, discard the first byte and resynchronize
                            buffer = buffer[1:]
                    else:
                        # If the first byte is not 0x00, discard it and resynchronize
                        buffer = buffer[1:]

                # If the buffer grows too large without finding a valid message, reset it
                if len(buffer) > 100:
                    print("[ATI FT SENSOR]: Buffer overflow, resetting buffer.")
                    buffer = b''


        else:
            """
            The read string from the sensor is in format as bytes in ascii form:
            b'0,  -102,   -99,  -225,   -20,    39,   -39\r\n'
            the first value 0 is an error id that shows that everything is fine if its zero
            or that there is a problem if its not. The other 6 ascii characters are the counts for each value,
            thus, -102 is the counts for force in x axis -99 is the counts in y axis and so on.
            These values are counts and must be divided properly according to the calibration (see counts_2_force function below). 
            The /r is to match the carriage return and /n to make new line.
            :return bytes in format b'0,  -102,   -99,  -225,   -20,    39,   -39'
            """
            read = self.connection.read(45)
            # while int(read.decode()[0]) != 0:
            while str(read)[2] != '0':
                while not self.start():
                    print('[ATI FT SENSOR]: Fixing Sequence')
                read = self.connection.read(45)
            return read[:-2].decode().split(',')

    def start(self):
        """
        Start Query string output reading from the sensor
        :return: Boolean
        """
        if self._mode == 'binary':
            self.connection.write(b'QS\r')
            msg_start = self.connection.read(5)
            # print(msg_start, len(msg_start))
            if len(msg_start) == 5 or str(msg_start)[2:4] == 'QS':
                return True
            else:
                return False
        else:
            self.connection.write(b'QS\r')
            msg_start = self.connection.read(5)
            if len(msg_start) == 5 and msg_start[0:2].decode() == 'QS':
                return True
            else:
                return False

    def stop(self):
        """
        Stop query output from sensor and close connection
        :return: bytes in format '\r\n\rn>'
        """
        self.connection.write(b'\r')
        self.connection.flushInput()
        self.connection.flush()
        msg_stop = self.connection.read(5)
        while msg_stop != b'\r\n\r\n>':
            self.connection.write(b'\r')
            self.connection.flushInput()
            self.connection.flush()
            msg_stop = self.connection.read(5)
        return msg_stop

    def initialise(self):
        """
        Reset connection and initialize mode before starting to pull data
        :return: None
        """
        current_time = time.time()
        if self.reset_time is not None:
            if current_time - self.reset_time < 2:
                self.reset_time = current_time
                return
        self.reset_time = current_time
        # print('FTSensor.reset(): Resetting at time', time.ctime())
        # Reset the sensor
        msg_stop = self.stop()
        # print(msg_stop)
        if self._mode == 'ascii':
            # Setup communication for binary output.
            self.connection.write(b'CD A\r')
            msg_reset = self.connection.read(11)
            # print(msg_reset)
            # Perform a moving average of 16 sensor data samples.
            self.connection.write(b'SA 16\r')
            msg_reset = self.connection.read(12)
            # print(msg_reset)
            # Sensor sampling Frequency allows optimizing for faster output when using CF.
            self.connection.write(b'SF\r')
            msg_reset = self.connection.read(15)
            # print(msg_reset)
            # Controls automatic SF optimization for RS-232 output.
            self.connection.write(b'CF\r')
            msg_reset = self.connection.read(31)
            # print(msg_reset)
            # Setup communication for Resolved force/torque data output (Default).
            self.connection.write(b'CD R\r')
            msg_reset = self.connection.read(11)
            # print(msg_reset)
            # Controls automatic SF optimization for RS-232 output.
            self.connection.write(b'CF 1\r')
            msg_reset = self.connection.read(11)
            # print(msg_reset)
            # Sensor sampling Frequency allows optimizing for faster output when using CF.
            self.connection.write(b'SF 1000\r')
            msg_reset = self.connection.read(15)
            # print(msg_reset)
            # self.zero_bias()
            # Removes all previously stored biases from buffer.
            self.connection.write(b'SZ\r')
            msg_reset = self.connection.read(9)
            # print(msg_reset)
        else:
            # Setup communication for binary output.
            self.connection.write(b'CD B\r')
            msg_reset = self.connection.read(11)
            # print(msg_reset)
            # Perform a moving average of 16 sensor data samples.
            self.connection.write(b'SA 16\r')
            msg_reset = self.connection.read(12)
            # print(msg_reset)
            # Sensor sampling Frequency allows optimizing for faster output when using CF.
            self.connection.write(b'SF\r')
            msg_reset = self.connection.read(14)
            # print(msg_reset)
            # Controls automatic SF optimization for RS-232 output.
            self.connection.write(b'CF\r')
            msg_reset = self.connection.read(31)
            # print(msg_reset)
            # Setup communication for Resolved force/torque data output (Default).
            self.connection.write(b'CD R\r')
            msg_reset = self.connection.read(11)
            # print(msg_reset)
            # Controls automatic SF optimization for RS-232 output.
            self.connection.write(b'CF 1\r')
            msg_reset = self.connection.read(11)
            # print(msg_reset)
            # Sensor sampling Frequency allows optimizing for faster output when using CF.
            self.connection.write(b'SF\r')
            msg_reset = self.connection.read(13)
            # print(msg_reset)
            # self.zero_bias()
            # Removes all previously stored biases from buffer.
            self.connection.write(b'SZ\r')
            msg_reset = self.connection.read(9)
            # print(msg_reset)

    def zero_bias(self):
        """
        Performs a Sensor Bias. Stores bias reading in a 3-level buffer.
        ========== DONT USE, USE sensor_bias below
        :return None
        """
        # print('Sensor Biasing')
        self.connection.write(b'SB\r')
        msg_reset = self.connection.read(4)
        print(f'[ATI FT SENSOR]: {msg_reset}')

    def sensor_bias(self, _forces):
        """
        Performs a sensor force and torque bias
        :param _forces: list of forces in format [fx, fy, fz, tx, ty, tz] to subtract from measured values
        :return: None
        """
        self._bias = _forces

    def sensor_unbias(self):
        """
        Performs a sensor force and torque unbias
        :return: None
        """
        self._bias = [0, 0, 0, 0, 0, 0]

    def counts_2_force_torque(self, msg_binary, unbiased=False):
        """
        For different FT sensor counts see /ATI_FT/Calibration/ATI_FT_commands_manual.pdf
        For Nano25 and SI-125-3 Calibration Specifications
        counts force = 192
        counts torque = 10560
        Transform measured counts to forces and torques
        :param msg_binary: binary message in format b'\x00\xff\x93\xff\x98\xfei\xff\xbb\x00\x06\xff\xdb\x06\r\n>QS' pulled from the sensor
        :param unbiased: flag to return unbiased or biased force torque values
        :return list of forces and torques in format [fx, fy, fz, tx, ty, tz]
        """
        counts_force = 2.4227  # for Gamma FT sensor and SI-65-5 Calibration Specifications
        counts_torque = 110.97  # for Gamma FT sensor and SI-65-5 Calibration Specifications
        if self._mode == 'binary':
            msg_binary = binary_2_counts(msg_binary)
            fx = msg_binary[0] + msg_binary[1]
            fy = msg_binary[2] + msg_binary[3]
            fz = msg_binary[4] + msg_binary[5]
            tx = msg_binary[6] + msg_binary[7]
            ty = msg_binary[8] + msg_binary[9]
            tz = msg_binary[10] + msg_binary[11]
            if unbiased:
                return [fx / counts_force, fy / counts_force, fz / counts_force, tx / counts_torque, ty / counts_torque, tz / counts_torque]
            return [-(fx / counts_force - self._bias[0]), -(fy / counts_force - self._bias[1]), fz / counts_force - self._bias[2], -(tx / counts_torque - self._bias[3]), -(ty / counts_torque - self._bias[4]), tz / counts_torque - self._bias[5]]
        else:
            fx = int(msg_binary[1])/counts_force
            fy = int(msg_binary[2])/counts_force
            fz = int(msg_binary[3])/counts_force
            tx = int(msg_binary[4])/counts_torque
            ty = int(msg_binary[5])/counts_torque
            tz = int(msg_binary[6])/counts_torque
            if unbiased:
                return [fx, fy, fz, tx, ty, tz]
            return [-(fx - self._bias[0]), -(fy - self._bias[1]), fz - self._bias[2], -(tx - self._bias[3]), -(ty - self._bias[4]), tz - self._bias[5]]

# file_initialized = False
def record_data(sensor, data, filename="ascii_data.csv"):
    """
    Records the collected ASCII data into a CSV file.
    :param data: List of data to record (e.g., forces and torques).
    :param filename: Name of the file to save the data.
    :param overwrite: Whether to overwrite the file if it already exists.
    """

    # Check if the file exists and overwrite it
    if os.path.exists(filename):
        os.remove(filename)  # Delete the existing file

    # Write the header
    with open(filename, "w") as file:
        file.write("Time,Hex Data,fxBias,fyBias,fxBias,txBias,tyBias,tzBias\n")  # Write header

    # Append data to the file
    with open(filename, "a") as file:
        for row in data:
            # Convert the row into a comma-separated string
            time_str = str(row[0])  # Timestamp
            if sensor._mode == 'binary':
                data_str = str(row[1])  # Hexadecimal data
            else:
                data_str = ",".join(map(str, row[1]))

            bias_str = ",".join(map(str, row[2]))  # Convert bias list to a comma-separated string

            # Write the formatted string to the file
            file.write(f"{time_str},{data_str},{bias_str}\n")

def check_device_on_port(port):
    """
    Check if a device exists on the specified COM port.
    :param port: COM port to check (e.g., 'COM1')
    :return: True if a device exists, False otherwise
    """
    try:
        with serial.Serial(port, timeout=1) as ser:
            print(f"[CHECK]: Device found on {port}.")
            return True
    except serial.SerialException:
        print(f"[CHECK]: No device found on {port}.")
        return False




# Format to accommodate for extra bytes in message and exception
def binary_2_counts(binary_msg):
    """
    Convert to string
    _binary_msg = binary_msg[1:-4]
    Split message and check if there are more digits
    :param binary_msg: binary message in format b'\x00\xff\x93\xff\x98\xfei\xff\xbb\x00\x06\xff\xdb\x06\r\n>QS' pulled from the sensor
    :return list with forces and torques in format [fx, fy, fz, tx, ty, tz]
    """
    flag_check = str(binary_msg).split('\\')[2:]
    counter = 0
    if flag_check[-1] == "n>QS'":
        flag_check = flag_check[:-2]
    if len(flag_check) < 13:
        return binary_msg[1:13]
    check = [(len(x) > 3) for x in flag_check[:12]]
    # If no more byte found return
    if True not in check and len(binary_msg[1:]) >= 12:
        return binary_msg[1:13]
    for i in check:
        if i:
            counter += 1
    if len(flag_check) < 12 or len(flag_check) + counter < 12:
        return [binary_msg[1], binary_msg[2], binary_msg[3], binary_msg[4], binary_msg[5], binary_msg[6], binary_msg[7], binary_msg[8], binary_msg[9], binary_msg[10], binary_msg[11], binary_msg[12]]
    try:
        # If more digits were found calculate new message
        f, j = [], 0
        for i in range(1, len(binary_msg)):
            # account for the number of shifts to the right
            if len(f) > 11:
                break
            if check[i - 1]:
                f.append(binary_msg[i + j] + binary_msg[i + j + 1])
                # Shift to right by two
                j += 1
                continue
            f.append(binary_msg[i + j])
        return f
    except Exception:
        print(f'[ATI FT SENSOR]: {e}')
        # print(_binary_msg[0], _binary_msg[1], _binary_msg[2], _binary_msg[3], _binary_msg[4], _binary_msg[5], _binary_msg[6], _binary_msg[7], _binary_msg[8], _binary_msg[9], _binary_msg[10], _binary_msg[11])
        return [binary_msg[1], binary_msg[2], binary_msg[3], binary_msg[4], binary_msg[5], binary_msg[6], binary_msg[7], binary_msg[8], binary_msg[9], binary_msg[10], binary_msg[11], binary_msg[12]]

def decode_force_torque(binary_msg):
    """
    Decode binary data into force and torque values.
    :param binary_msg: Binary message in the format:
                       <error><Fx high><Fx low><Fy high><Fy low><Fz high><Fz low>
                       <Tx high><Tx low><Ty high><Ty low><Tz high><Tz low>
                       in hexadecimal format
    :return: List of forces and torques in the format [Fx, Fy, Fz, Tx, Ty, Tz]
    """
    # Scaling factors (adjust based on your sensor's calibration)
    counts_to_force = 2.4227  # Example: counts per Newton for force
    counts_to_torque = 110.97  # Example: counts per Newton-meter for torque

    # Ensure the binary message is at least 13 bytes long
    if len(binary_msg) < 13:
        raise ValueError("Binary message is too short to decode.")
    
    # Extract high and low bytes for each value and combine them
    fx = int.from_bytes(binary_msg[1:3], byteorder='big', signed=True) / counts_to_force
    fy = int.from_bytes(binary_msg[3:5], byteorder='big', signed=True) / counts_to_force
    fz = int.from_bytes(binary_msg[5:7], byteorder='big', signed=True) / counts_to_force
    tx = int.from_bytes(binary_msg[7:9], byteorder='big', signed=True) / counts_to_torque
    ty = int.from_bytes(binary_msg[9:11], byteorder='big', signed=True) / counts_to_torque
    tz = int.from_bytes(binary_msg[11:13], byteorder='big', signed=True) / counts_to_torque

    return [
        fx,
        fy,
        fz,
        tx,
        ty,
        tz
    ]
    

if __name__ == '__main__':
    """ Test functionality """
    from optparse import OptionParser
    import argparse
    import time
    # import keyboard
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['binary', 'ascii'], default='ascii',help='communication mode: binary or ascii')

    args = parser.parse_args()

    ATI_port = 'COM1'# Change to your port
    LED_port = 'COM13'  # Change to your Arduino port

    # Check if a device exists on COM1
    if not check_device_on_port(ATI_port) or not check_device_on_port(LED_port):
        print("Missing device. Please check connections and port settings...")
        exit(1)    

    arduino = serial.Serial(LED_port, 9600, timeout=1)
    time.sleep(2)  # Give Arduino time to reset after opening port

    
    daq = Sensor(ATI_port, mode=args.mode)  # for linux probably /dev/ttyUSB0, use dmesg | grep tty to find the port


    start_time = time.perf_counter()
    # initialize array to store data
    data = []

    try:

        arduino.write(b'H')
        while True:
            try:
                _msg = daq.read()
                current_time = time.perf_counter()

                # store forces and torques
                if daq._mode == 'binary': # if using binary, store f/t data as hex string
                    data.append((current_time, _msg.hex(), daq._bias))
                else: # if using ascii, store f/t data as list of floats
                    data.append((current_time, _msg, daq._bias))
                
                # Bias Sensor
                if time.perf_counter() - start_time <= 2:
                    if daq._mode =='binary': # if using binary, decode the message to get f/t for biasing
                        forces = decode_force_torque(_msg)
                    else: # if using ascii, calculate f/t from counts
                        forces = daq.counts_2_force_torque(_msg, unbiased=True)
                    daq.sensor_bias(forces)
                    # print(f'Biased: {daq._bias}')


            except Exception as e:
                print(e)
    except KeyboardInterrupt:
        daq.stop()
        daq.connection.close()
        print('Connection closed...')

        arduino.write(b'L')
        arduino.close()
        # print(data)
        record_data(daq, data, filename="ATI_data.csv")
        exit(0)