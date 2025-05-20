import subprocess
import os


# Map commands to script paths
COMMANDS = {
    "platform": os.path.join("stewart", "stewart_displacement.py"),
    "rail": os.path.join("rail", "code.py"),
    "roll": os.path.join("dynamixel", "Dynamixels.py")
}


def run_script(script_path, args=None):
    try:
        cmd = ["python", script_path]
        if args:
            cmd += args


        # Start the subprocess
        process = subprocess.Popen(cmd)
        print("Script running. Press Ctrl+C to stop.")
        process.wait()
    except KeyboardInterrupt:
        print("\nEmergency stop activated. Terminating script...")
        process.terminate()
        process.wait()
    print("Returned to Master menu.\n")


def main():
    print("=== Master Control Ready ===")
    print("Available commands: 'platform', 'rail', 'roll'")
    print("Type 'exit' to quit.")


    while True:
        user_input = input(">> ").strip().lower()


        if user_input == "exit":
            print("Exiting Master Control.")
            break
        elif user_input in COMMANDS:
            script_path = COMMANDS[user_input]


            if user_input == "platform":
                port = input("Enter the port (e.g., COMX if windows or /dev/ttyUSBX if linux): ").strip()
                csv_file = input("Enter the path to the CSV file: ").strip()
                args = [port, "disp", csv_file]
                run_script(script_path, args)
            else:
                run_script(script_path)
        else:
            print("Invalid command. Try: 'platform', 'rail', or 'roll'.")


if __name__ == "__main__":
    main()


