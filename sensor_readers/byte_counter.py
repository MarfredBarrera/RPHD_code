# Count bytes in a .hex file
with open("raw_serial_bytes.hex", "r") as f:
    hex_str = f.read().strip()
    # Remove any whitespace or newlines
    hex_str = ''.join(hex_str.split())
    num_bytes = len(hex_str) // 2
    print(f"Number of bytes: {num_bytes}")