import serial
import time

# Replace 'COM3' with the correct port (e.g., '/dev/ttyACM0' or '/dev/cu.usbmodemXXX')
arduino = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)  # Give Arduino time to reset after opening port

start_time = time.time()
while time.time() - start_time < 60:
    # Toggle HIGH
    arduino.write(b'H')
    print("Pin D5 set HIGH")
    time.sleep(3)

    # Toggle LOW
    arduino.write(b'L')
    print("Pin D5 set LOW")
    time.sleep(3)

arduino.close()
