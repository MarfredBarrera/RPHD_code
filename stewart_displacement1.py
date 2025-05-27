import serial
import sys
import time
import csv
import threading
from datetime import datetime

# Connect to the serial port
def connect_serial(port):
    try:
        ser = serial.Serial(port, 115200, timeout=0.1)
        print(f"Connected to serial port: {port}")
        return ser
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {port} — {e}")
        sys.exit(1)

# Send a command to the Stewart platform
def send_command(ser, cmd, delay=0.0083):
    ser.write(cmd.encode())
    print(f"Sent: {cmd.strip()}")
    time.sleep(delay)
    ser.reset_input_buffer()

# Home the Stewart platform
def home_platform(ser):
    print("Homing Stewart platform...")
    send_command(ser, "h;", delay=0.5)

# Thread function to allow stopping motion by pressing Enter
def wait_for_stop(stop_flag):
    input("Press Enter to stop motion and hold position...\n")
    stop_flag.append(True)

# Run displacement-based motion using a CSV file
def run_displacement_motion(ser, csv_file_path):
    try:
        with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = list(csv.reader(csvfile))
    except FileNotFoundError:
        print(f"Error: File '{csv_file_path}' not found.")
        sys.exit(1)

    log_file = f"motion_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    stop_flag = []

    threading.Thread(target=wait_for_stop, args=(stop_flag,), daemon=True).start()

    try:
        with open(log_file, 'w', newline='', encoding='utf-8') as logfile:
            logger = csv.writer(logfile)
            logger.writerow([
                "Frame", "Time (s)",
                "X", "Y", "Z", "Roll", "Pitch", "Yaw",
                "dX", "dY", "dZ", "dRoll", "dPitch", "dYaw"
            ])

            print(f"Logging motion to: {log_file}")
            print(f"Executing {len(reader)} displacement commands from CSV...")

            start_time = time.time()
            pose = [0.0] * 6  # [Roll, Pitch, Yaw, X, Y, Z]

            for frame, row in enumerate(reader, start=1):
                if stop_flag:
                    print("Motion stopped by user.")
                    break

                if len(row) != 6:
                    print(f"Skipping row {frame}: expected 6 values, got {len(row)}")
                    continue

                try:
                    dRoll, dPitch, dYaw, dX, dY, dZ = [float(val.strip()) for val in row]
                except ValueError as e:
                    print(f"Skipping row {frame}: invalid float — {e}")
                    continue

                # Update current pose
                pose[0] += dRoll
                pose[1] += dPitch
                pose[2] += dYaw
                pose[3] += dX
                pose[4] += dY
                pose[5] += dZ

                # Format and send command
                command = f"t {pose[3]:.2f} {pose[4]:.2f} {pose[5]:.2f} {pose[0]:.2f} {pose[1]:.2f} {pose[2]:.2f};"
                send_command(ser, command)

                # Log data
                timestamp = time.time() - start_time
                logger.writerow([
                    frame, f"{timestamp:.3f}",
                    f"{pose[3]:.2f}", f"{pose[4]:.2f}", f"{pose[5]:.2f}",
                    f"{pose[0]:.2f}", f"{pose[1]:.2f}", f"{pose[2]:.2f}",
                    f"{dX:.2f}", f"{dY:.2f}", f"{dZ:.2f}",
                    f"{dRoll:.2f}", f"{dPitch:.2f}", f"{dYaw:.2f}"
                ])

        print("Motion complete. Platform is holding last position.")

        # Prompt user to home manually
        while True:
            cmd = input("Type 'home' to send platform to home position, or 'exit' to quit: ").strip().lower()
            if cmd == 'home':
                home_platform(ser)
                break
            elif cmd == 'exit':
                break

    except Exception as e:
        print(f"Unexpected error during motion: {e}")
        sys.exit(1)

# Main entry point
def main():
    if len(sys.argv) < 3:
        print("Usage: python stewart_displacement.py [PORT] [MODE] [CSV_FILE (optional)]")
        sys.exit(1)

    port = sys.argv[1]
    mode = sys.argv[2].lower()

    ser = connect_serial(port)
    time.sleep(1)
    home_platform(ser)

    try:
        if mode == "disp":
            if len(sys.argv) >= 4:
                csv_file = sys.argv[3]
            else:
                csv_file = input("Enter the CSV filename to run displacement motion: ").strip()
            run_displacement_motion(ser, csv_file)
        else:
            print(f"Unknown mode '{mode}'. Only 'disp' is supported.")
            sys.exit(1)
    finally:
        if ser:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
