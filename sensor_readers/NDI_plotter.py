import csv
import matplotlib.pyplot as plt

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

                # Extract X, Y, Z positions
                timestamps.append(row[0])  # Timestamp
                x_positions.append(float(row[6]))  # X position
                y_positions.append(float(row[7]))  # Y position
                z_positions.append(float(row[8]))  # Z position

            except ValueError:
                # Skip rows with invalid data
                continue

    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, x_positions, label='X Position', color='r')
    plt.plot(timestamps, y_positions, label='Y Position', color='g')
    plt.plot(timestamps, z_positions, label='Z Position', color='b')

    # Add labels and legend
    # plt.xlabel('Timestamp')
    plt.gca().axes.xaxis.set_visible(False)
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
