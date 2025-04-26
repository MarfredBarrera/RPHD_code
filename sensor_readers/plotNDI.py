import csv
import matplotlib.pyplot as plt
import numpy as np
import datetime

def get_sec(time_str):
    """Get seconds from time."""
    h, m, s = time_str.split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)

def decode_binary(hex_data):
    """Decode binardy data from hex string"""
    return bytes.fromhex(hex_data)

def plot_xyz_positions(file_path):
    # Initialize lists to store data
    timestamps = []
    x_positions = []
    y_positions = []
    z_positions = []

    # Read the CSV file
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Skip the header row

        for row in reader:
            try:
                # Skip rows with "MISSING" values
                if "MISSING" in row:
                    continue


                # Parse the timestamp (hr:min:sec) into a datetime object
                secs = get_sec(row[0])
                timestamps.append(secs)  # Store the datetime object

                # Extract X, Y, Z positions
                x_positions.append(float(row[6]))  # X position
                y_positions.append(float(row[7]))  # Y position
                z_positions.append(float(row[8]))  # Z position

            except ValueError:
                # Skip rows with invalid data
                continue
    timestamps = np.array(timestamps) - timestamps[0]  # Normalize time to start from 0
    time_differences = np.diff(timestamps)  # Calculate differences between consecutive timestamps
    avg_time_difference = np.mean(time_differences)  # Average of the time differences
    achieved_frequency = 1 / avg_time_difference  # Invert the average to get the frequency
    print(f"Achieved Sampling Frequency: {achieved_frequency:.2f} Hz")
    # print(timestamps)
    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, x_positions, label='X Position', color='r')
    plt.plot(timestamps, y_positions, label='Y Position', color='g')
    plt.plot(timestamps, z_positions, label='Z Position', color='b')

    # Add labels and legend
    plt.xlabel('Time [s]')
    plt.ylabel('Position [mm]')
    plt.title('X, Y, Z Positions Over Time')
    plt.legend()
    # plt.xticks(rotation=45, fontsize=8)  # Rotate x-axis labels for better readability
    plt.tight_layout()

    # Show the plot
    plt.show()

# Filepath to the CSV file
file_path = r".\recording\NDI_test_n6d.csv"
plot_xyz_positions(file_path)