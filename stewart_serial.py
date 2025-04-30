import serial
import sys
import time
import math
import csv
import threading

def connect_serial(port):
    try:
        ser = serial.Serial(port, 115200, timeout=0.1)
        print("Serial open OK")
        return ser
    except serial.SerialException as e:
        print(f"Failed to open serial port {port}: {e}")
        sys.exit(1)

def send_command(ser, cmd, sleep_time=0.0083):
    ser.write(cmd.encode())
    print(f"Sent: {cmd}")
    time.sleep(sleep_time)
    ser.reset_input_buffer()

def home(ser):
    print("Sending home command...")
    send_command(ser, "h;", sleep_time=0.5)

def wait_for_enter(stop_flag):
    input("Press Enter to stop motion and go home...\n")
    stop_flag.append(True)

def csv_motion(ser, filename):
    try:
        with open(filename, 'r', encoding='utf-8-sig') as csvfile:
            reader = list(csv.reader(csvfile))
            stop_flag = []
            threading.Thread(target=wait_for_enter, args=(stop_flag,), daemon=True).start()

            print(f"Starting CSV motion from '{filename}' with {len(reader) - 1} rows.")

            for i, row in enumerate(reader[1:], start=2):  # Skip header
                if stop_flag and stop_flag[0]:
                    print("Motion interrupted by user.")
                    break

                print(f"Row {i} raw: {row}")

                if len(row) != 6:
                    print(f"Skipping row {i}: Expected 6 columns, got {len(row)}")
                    continue

                try:
                    # Clean each value
                    clean = lambda val: float(val.strip().replace('\ufeff', '').replace('\xa0', ''))
                    roll = clean(row[0])
                    pitch = clean(row[1])
                    yaw = clean(row[2])
                    x = clean(row[3])
                    y = clean(row[4])
                    z = clean(row[5])
                except Exception as e:
                    print(f"Skipping row {i}: Cannot convert to float — {e}")
                    continue

                cmd = f"t {x:.2f} {y:.2f} {z:.2f} {roll:.2f} {pitch:.2f} {yaw:.2f};"
                print(f"Row {i}: Sending command: {cmd}")
                send_command(ser, cmd)

            print("CSV motion complete.")
            home(ser)

    except FileNotFoundError:
        print(f"CSV file '{filename}' not found.")
        sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("Usage: python stewart_serial.py [PORT] [MODE] (CSV_FILENAME if mode=csv)")
        print("Modes: csv")
        sys.exit(1)

    port = sys.argv[1]
    mode = sys.argv[2].lower()

    ser = connect_serial(port)
    time.sleep(1)
    home(ser)

    if mode == 'csv':
        if len(sys.argv) < 4:
            print("CSV filename required for 'csv' mode.")
            sys.exit(1)
        csv_motion(ser, sys.argv[3])
    else:
        print("Unknown mode. Use 'csv'.")
        sys.exit(1)

    if ser is not None:
        ser.close()
        print("Serial port closed.")

if __name__ == "__main__":
    main()
