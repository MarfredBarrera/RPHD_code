import subprocess
import os
import time
import threading

# Command to script path map
COMMANDS = {
    "platform": os.path.join("stewart", "stewart_displacement1.py"),
    "insert": os.path.join("rail", "insert-cw.py"),
    "retract": os.path.join("rail", "retract-ccw.py"),
    "roll": os.path.join("dynamixel", "rolled.py")
}

def run_script(script_path, args=None):
    def _run():
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
    
    thread = threading.Thread(target=_run)
    thread.start()
    return thread

def evaluate_condition(condition_line):
    parts = condition_line.strip().split()
    if len(parts) < 2:
        return False
    keyword, target = parts[0], " ".join(parts[1:])
    if keyword == "exists":
        return os.path.exists(target)
    # Extend here for other condition types if needed
    return False

def run_parallel_block(lines):
    threads = []
    for line in lines:
        print(f">> [Parallel] Executing: {line}")
        thread = handle_command(line, return_thread=True)
        if thread:
            threads.append(thread)
    for t in threads:
        t.join()

def handle_command(command_line, return_thread=False):
    parts = command_line.strip().split()
    if not parts:
        return None

    command = parts[0].lower()
    args = parts[1:]

    if command == "wait":
        if len(args) != 1 or not args[0].replace('.', '', 1).isdigit():
            print("Usage for wait: wait <seconds>")
            return None
        wait_time = float(args[0])
        print(f"Waiting for {wait_time} seconds...")
        time.sleep(wait_time)
        return None

    if command not in COMMANDS:
        print(f"Invalid command: {command}")
        return None

    script_path = COMMANDS[command]

    thread = None
    if command == "platform":
        if len(args) not in (2, 3):
            print("Usage: platform <port> <csv_file> [home|exit]")
            return None
        port = args[0]
        csv_file = args[1]
        post_action = args[2] if len(args) == 3 else "exit"
        thread = run_script(script_path, [port, "disp", csv_file, post_action])

    elif command in ("insert", "retract"):
        if len(args) != 1:
            print(f"Usage: {command} <displacement>")
            return None
        direction = "in" if command == "insert" else "out"
        displacement = args[0]
        thread = run_script(script_path, [direction, displacement])

    elif command == "roll":
        if len(args) != 2:
            print("Usage: roll <angle> <speed>")
            return None
        thread = run_script(script_path, args)

    if thread and not return_thread:
        thread.join()
        return None
    return thread

def run_batch(file_path):
    if not os.path.exists(file_path):
        print(f"Batch file '{file_path}' not found.")
        return

    print(f"Running batch file: {file_path}")
    with open(file_path, "r") as file:
        raw_lines = [line.strip() for line in file if line.strip() and not line.strip().startswith("#")]

def expand_blocks(lines):
    def parse_block(block_lines):
        i = 0
        expanded = []

        while i < len(block_lines):
            line = block_lines[i]

            if line.startswith("start loop"):
                parts = line.split()
                if len(parts) != 3 or not parts[2].isdigit():
                    raise ValueError(f"Invalid loop syntax at line: {line}")
                count = int(parts[2])
                i += 1
                nested = []
                depth = 1
                while i < len(block_lines):
                    if block_lines[i].startswith("start loop"):
                        depth += 1
                    elif block_lines[i] == "end loop":
                        depth -= 1
                        if depth == 0:
                            break
                    nested.append(block_lines[i])
                    i += 1
                if depth != 0:
                    raise ValueError("Missing 'end loop' for a 'start loop'")
                expanded.extend(parse_block(nested) * count)
                i += 1
                continue

            elif line.startswith("if ") or line.startswith("unless "):
                is_unless = line.startswith("unless ")
                condition = " ".join(line.split()[1:])
                result = evaluate_condition(condition)
                if is_unless:
                    result = not result
                i += 1
                nested = []
                depth = 1
                while i < len(block_lines):
                    if block_lines[i].startswith("if ") or block_lines[i].startswith("unless "):
                        depth += 1
                    elif block_lines[i] in ("end if", "end unless"):
                        depth -= 1
                        if depth == 0:
                            break
                    nested.append(block_lines[i])
                    i += 1
                if depth != 0:
                    raise ValueError("Missing 'end if' or 'end unless'")
                if result:
                    expanded.extend(parse_block(nested))
                i += 1
                continue

            elif line == "parallel:":
                i += 1
                nested = []
                while i < len(block_lines) and block_lines[i] != "end parallel":
                    nested.append(block_lines[i])
                    i += 1
                if i == len(block_lines):
                    raise ValueError("Missing 'end parallel' for a 'parallel:' block")
                expanded.append(("parallel", parse_block(nested)))
                i += 1
                continue

            else:
                expanded.append(line)
                i += 1

        return expanded

    return parse_block(lines)


    try:
        expanded_lines = expand_blocks(raw_lines)
        for line in expanded_lines:
            if isinstance(line, tuple) and line[0] == "parallel":
                run_parallel_block(line[1])
            else:
                print(f">> Executing: {line}")
                handle_command(line)
    except ValueError as e:
        print(f"Error in batch file: {e}")

def main():
    print("=== Master Control Ready ===")
    print("Available commands: 'platform', 'insert', 'retract', 'roll', or 'batch <filename>'")
    print("Use 'wait <seconds>' to pause. Use loops with 'start loop <N>' ... 'end loop'")
    print("Use 'parallel:' ... 'end parallel' for concurrent commands")
    print("Use 'if exists <file>' ... 'end if' and 'unless exists <file>' ... 'end unless' for conditionals")
    print("Type 'exit' to quit.")

    while True:
        try:
            user_input = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Master Control.")
            break

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
