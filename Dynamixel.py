import serial

SERIAL_PORT = "/dev/ttyACM0"  # Adjust if different
BAUDRATE = 115200

def send_angle(angle):
    with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=2) as ser:
        ser.flush()
        ser.write(f"{angle}\n".encode())
        response = ser.readline().decode().strip()
        print("Response from OpenRB:", response)

def main():
    while True:
        try:
            angle = input("Enter angle (0-360, or 'q' to quit): ")
            if angle.lower() == 'q':
                break
            angle_val = int(angle)
            if 0 <= angle_val <= 360:
                send_angle(angle_val)
            else:
                print("Please enter a value between 0 and 360.")
        except ValueError:
            print("Invalid input.")

if __name__ == "__main__":
    main()
