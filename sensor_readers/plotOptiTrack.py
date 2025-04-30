import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Load data from the CSV file
file_path = 'optitrack_data.csv'  # Replace with the actual path to your CSV file
data = pd.read_csv(file_path, skiprows=7)  # Skip the first 6 rows of metadata

# Extract relevant columns
time = data['Time (Seconds)']  # Time column
rot_x = data.iloc[:, 2]  # X position
rot_y = data.iloc[:, 3]  # Y position
rot_z = data.iloc[:, 4]  # Z position
x = data.iloc[:, 5]
y = data.iloc[:, 6]
z = data.iloc[:, 7]


time = np.array(time) - time[0]  # Normalize time to start from 0
time_differences = np.diff(time)  # Calculate differences between consecutive timestamps
avg_time_difference = np.mean(time_differences)  # Average of the time differences
achieved_frequency = 1 / avg_time_difference  # Invert the average to get the frequency
print(f"Achieved Sampling Frequency: {achieved_frequency:.2f} Hz")

# Create a figure and axes for the plots
fig, axs = plt.subplots(2, 1, figsize=(10, 8))

# Plot position (x, y, z) over time
axs[0].plot(time, x, label='x', color='r')
axs[0].plot(time, y, label='y', color='g')
axs[0].plot(time, z, label='z', color='b')
axs[0].set_title('Position')
axs[0].set_xlabel('Time [s]')
axs[0].set_ylabel('Position [mm]')
axs[0].legend()
axs[0].grid(True)

# Plot orientation (roll, pitch, yaw) over time
axs[1].plot(time, rot_x, label='Rot X', color='r')
axs[1].plot(time, rot_y, label='Rot y', color='g')
axs[1].plot(time, rot_z, label='Rot z', color='b')
axs[1].set_title('Rotation')
axs[1].set_xlabel('Time [s]')
axs[1].set_ylabel('Orientation [degrees]')
axs[1].legend()
axs[1].grid(True)

# Adjust layout and show the plot
plt.tight_layout()
plt.show()