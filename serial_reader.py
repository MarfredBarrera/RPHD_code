import serial
import threading
from time import sleep

def read_serial(ser):
    try:
        while True:
            line = ser.readline().decode('utf-8').strip()
            if line:
                print(line)  # Print received data

    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nSerial reading stopped by user.")

def write_serial(ser):
    try:
        while True:
            command = input("Enter command: ")
            ser.write(command.encode('utf-8') + b'\n')
            ser.reset_output_buffer()  # Clear outout buffer

            # sleep(0.1)  # Wait for the command to be sent
    except KeyboardInterrupt:
        print("\nCommand sending stopped by user.")

def main(port='COM1', baudrate=38400):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Connected to {port} at {baudrate} baud")
        
        # Start threads for reading and writing
        write_thread = threading.Thread(target=write_serial, args=(ser,), daemon=True)
        write_thread.start()

        read_thread = threading.Thread(target=read_serial, args=(ser,), daemon=True)
        read_thread.start()

        # Keep the main thread alive while the other threads are running
        write_thread.join()
        read_thread.join() 
               
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()