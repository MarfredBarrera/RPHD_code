import serial
import sys

SERIAL_PORT = "/dev/ttyACM0"  # Adjust to match your port
BAUDRATE = 115200

def send_command(angle, speed):
    with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=2) as ser:
        ser.flush()
        command = f"{angle},{speed}\n"
        ser.write(command.encode())

        response = ser.readline().decode().strip()
        print("Response from OpenRB:", response)

def main():
    if len(sys.argv) != 3:
        print("Usage: python Dynamixels.py <relative_angle> <speed>")
        print("Example: python Dynamixels.py 90 300  → rotate +90° at speed 300")
        print("         python Dynamixels.py -45 500 → rotate -45° at speed 500")
        sys.exit(1)

    try:
        angle = int(sys.argv[1])   # Allow negative and positive values
        speed = int(sys.argv[2])   # Speed range: 0–1023

        if -360 <= angle <= 360 and 0 <= speed <= 1023:
            send_command(angle, speed)
        else:
            print("Angle must be between -360 and 360, speed must be 0–1023.")
            sys.exit(1)

    except ValueError:
        print("Invalid input. Please provide two integers: <angle> <speed>")
        sys.exit(1)

if __name__ == "__main__":
    main()
