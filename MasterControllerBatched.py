import subprocess
import os
import time

# Command to script path map
COMMANDS = {
    "platform": os.path.join("stewart", "stewart_displacement1.py"),
    "insert": os.path.join("rail", "insert-cw.py"),
    "retract": os.path.join("rail", "retract-ccw.py"),
    "roll": os.path.join("dynamixel", "rolled.py")
}

def run_script(script_path, args=None):
    try:
        cmd = ["python", script_path]
        if args:
            cmd += args
        print(f"Running: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        process.wait()
    except KeyboardInterrupt:
        print("\nEmergency stop activated. Terminating script...")
        process.terminate()
        process.wait()
    print("Returned to Master menu.\n")

def handle_command(command_line):
    parts = command_line.strip().split()
    if not parts:
        return

    command = parts[0].lower()
    args = parts[1:]

    if command == "wait":
        if len(args) != 1 or not args[0].replace('.', '', 1).isdigit():
            print("Usage for wait: wait <seconds>")
            return
        wait_time = float(args[0])
        print(f"Waiting for {wait_time} seconds...")
        time.sleep(wait_time)
        return

    if command not in COMMANDS:
        print(f"Invalid command: {command}")
        return

    script_path = COMMANDS[command]

    if command == "platform":
        if len(args) not in (2, 3):
            print("Usage: platform <port> <csv_file> [home|exit]")
            return
        port = args[0]
        csv_file = args[1]
        post_action = args[2] if len(args) == 3 else "exit"
        run_script(script_path, [port, "disp", csv_file, post_action])

    elif command in ("insert", "retract"):
        if len(args) != 1:
            print(f"Usage: {command} <displacement>")
            return
        direction = "in" if command == "insert" else "out"
        displacement = args[0]
        run_script(script_path, [direction, displacement])

    elif command == "roll":
        if len(args) != 2:
            print("Usage: roll <angle> <speed>")
            return
        run_script(script_path, args)

def run_batch(file_path):
    if not os.path.exists(file_path):
        print(f"Batch file '{file_path}' not found.")
        return

    print(f"Running batch file: {file_path}")
    with open(file_path, "r") as file:
        raw_lines = [line.strip() for line in file if line.strip() and not line.strip().startswith("#")]

    def expand_loops(lines):
        i = 0
        expanded = []
        loop_stack = []

        while i < len(lines):
            line = lines[i]
            if line.startswith("start loop"):
                parts = line.split()
                if len(parts) != 3 or not parts[2].isdigit():
                    raise ValueError(f"Invalid loop syntax at line: {line}")
                loop_count = int(parts[2])
                loop_stack.append((loop_count, []))
            elif line == "end loop":
                if not loop_stack:
                    raise ValueError("Unexpected 'end loop' with no matching 'start loop'")
                loop_count, block = loop_stack.pop()
                expanded_block = block * loop_count
                if loop_stack:
                    loop_stack[-1][1].extend(expanded_block)
                else:
                    expanded.extend(expanded_block)
            else:
                if loop_stack:
                    loop_stack[-1][1].append(line)
                else:
                    expanded.append(line)
            i += 1

        if loop_stack:
            raise ValueError("Missing 'end loop' for a 'start loop'")
        return expanded

    try:
        expanded_lines = expand_loops(raw_lines)
        for line in expanded_lines:
            print(f">> Executing: {line}")
            handle_command(line)
    except ValueError as e:
        print(f"Error in batch file: {e}")

def main():
    print("=== Master Control Ready ===")
    print("Available commands: 'platform', 'insert', 'retract', 'roll', or 'batch <filename>'")
    print("Use 'wait <seconds>' to pause. Use loops with 'start loop <N>' ... 'end loop'")
    print("Type 'exit' to quit.")

    while True:
        user_input = input(">> ").strip()
        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Exiting Master Control.")
            break

        elif user_input.startswith("batch "):
            _, file_path = user_input.split(maxsplit=1)
            run_batch(file_path)

        else:
            parts = user_input.split()
            command = parts[0].lower()
            if command == "platform" and len(parts) == 1:
                port = input("Enter the port (e.g., COMX or /dev/ttyUSBX): ").strip()
                csv_file = input("Enter the path to the CSV file: ").strip()
                post_action = input("Post-action after motion [home/exit]: ").strip().lower() or "exit"
                handle_command(f"platform {port} {csv_file} {post_action}")
            elif command in ("insert", "retract") and len(parts) == 1:
                distance = input("Enter displacement: ").strip()
                handle_command(f"{command} {distance}")
            elif command == "roll" and len(parts) == 1:
                angle = input("Enter angle: ").strip()
                speed = input("Enter speed: ").strip()
                handle_command(f"roll {angle} {speed}")
            else:
                handle_command(user_input)

if __name__ == "__main__":
    main()
