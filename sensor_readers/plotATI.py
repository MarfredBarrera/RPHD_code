import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def get_sec(time_str):
    """Get seconds from time."""
    h, m, s = time_str.split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)

# Load the CSV file into a DataFrame
data = pd.read_csv('ascii_data.csv')  # -------CHANGE FILENAME----------

# Extract specific columns by index
time = data.iloc[:, 0].apply(get_sec)  # First column (column 1)
fx = data.iloc[:, 1]    # Second column (column 2)
fy = data.iloc[:, 2]
fz = data.iloc[:, 3]
tx = data.iloc[:, 4]
ty = data.iloc[:, 5]
tz = data.iloc[:, 6]

time = np.array(time) - time[0]  # Normalize time to start from 0
time_differences = np.diff(time)  # Calculate differences between consecutive timestamps
avg_time_difference = np.mean(time_differences)  # Average of the time differences
achieved_frequency = 1 / avg_time_difference  # Invert the average to get the frequency
print(f"Achieved Sampling Frequency: {achieved_frequency:.2f} Hz")


time = time - time[0]  # Normalize time to start from 0

# Define the index range to exclude the first 5 seconds
index = time >= 5  # This creates a boolean mask where time >= 5

# Plotting Force vs Time
plt.figure(figsize=(10, 8))

# Subplot 1: Force vs Time
plt.subplot(2, 1, 1)
plt.title('Force vs Time')
plt.plot(time[index], fx[index], '-r', linewidth=2, label='F_x')
plt.plot(time[index], fy[index], '-g', linewidth=2, label='F_y')
plt.plot(time[index], fz[index], '-b', linewidth=2, label='F_z')
plt.xlabel('Time [s]')
plt.ylabel('Force [N]')
plt.legend(fontsize=12)
plt.grid(True)
plt.ylim([-30, 30])
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

# Subplot 2: Torque vs Time
plt.subplot(2, 1, 2)
plt.title('Torque vs Time')
plt.plot(time[index], tx[index], '-c', linewidth=2, label='T_x')
plt.plot(time[index], ty[index], '-m', linewidth=2, label='T_y')
plt.plot(time[index], tz[index], '-k', linewidth=2, label='T_z')
plt.xlabel('Time [s]')
plt.ylabel('Torque [N]')
plt.legend(fontsize=12)
plt.grid(True)
plt.ylim([-1, 1])
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

# Adjust layout and show the plot
plt.tight_layout()
plt.show()