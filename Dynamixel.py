import serial
import sys

SERIAL_PORT = "/dev/ttyACM0"  # Adjust for your system
BAUDRATE = 115200

def send_command(angle, speed):
    with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=2) as ser:
        ser.flush()
        command = f"{angle},{speed}\n"
        ser.write(command.encode())

        response = ser.readline().decode().strip()
        print("Response from OpenRB:", response)

def main():
    if len(sys.argv) == 3:
        try:
            angle = int(sys.argv[1])
            speed = int(sys.argv[2])

            if 0 <= angle <= 360 and 0 <= speed <= 1023:
                send_command(angle, speed)
            else:
                print("Angle must be 0–360, speed must be 0–1023.")
        except ValueError:
            print("Invalid arguments. Provide two integers: angle speed")
        return

    # Manual input mode
    while True:
        try:
            user_input = input("Enter angle,speed (e.g., 180,300) or 'q' to quit: ").strip()
            if user_input.lower() == 'q':
                break

            if ',' in user_input:
                angle_str, speed_str = user_input.split(',', 1)
                angle = int(angle_str)
                speed = int(speed_str)

                if 0 <= angle <= 360 and 0 <= speed <= 1023:
                    send_command(angle, speed)
                else:
                    print("Angle must be 0–360, speed must be 0–1023.")
            else:
                print("Invalid format. Use angle,speed (e.g., 180,300)")
        except ValueError:
            print("Invalid input. Make sure to enter two integers separated by a comma.")

if __name__ == "__main__":
    main()
