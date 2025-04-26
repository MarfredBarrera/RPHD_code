import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def get_sec(time_str):
    """Get seconds from time."""
    h, m, s = time_str.split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)

def decode_force_torque(binary_msg, bias):
    """
    Decode binary data into force and torque values.
    :param binary_msg: Binary message in the format:
                       <error><Fx high><Fx low><Fy high><Fy low><Fz high><Fz low>
                       <Tx high><Tx low><Ty high><Ty low><Tz high><Tz low>
    :return: List of forces and torques in the format [Fx, Fy, Fz, Tx, Ty, Tz]
    """
    # Scaling factors (adjust based on your sensor's calibration)
    counts_to_force = 2.4227  # Example: counts per Newton for force
    counts_to_torque = 110.97  # Example: counts per Newton-meter for torque

    # Ensure the binary message is at least 13 bytes long
    if len(binary_msg) < 13:
        raise ValueError("Binary message is too short to decode.")
    
    # Extract high and low bytes for each value and combine them
    fx = int.from_bytes(binary_msg[1:3], byteorder='big', signed=True) / counts_to_force
    fy = int.from_bytes(binary_msg[3:5], byteorder='big', signed=True) / counts_to_force
    fz = int.from_bytes(binary_msg[5:7], byteorder='big', signed=True) / counts_to_force
    tx = int.from_bytes(binary_msg[7:9], byteorder='big', signed=True) / counts_to_torque
    ty = int.from_bytes(binary_msg[9:11], byteorder='big', signed=True) / counts_to_torque
    tz = int.from_bytes(binary_msg[11:13], byteorder='big', signed=True) / counts_to_torque

    # Apply biases and return the decoded forces and torques
    return [
        fx - bias[0],
        fy - bias[1],
        fz - bias[2],
        tx - bias[3],
        ty - bias[4],
        tz - bias[5]
    ]
    # return [
    #     fx,
    #     fy,
    #     fz,
    #     tx,
    #     ty,
    #     tz
    # ]
    


def plot_ati_data(file_path):
    # Load the data from the .npy file
    data = pd.read_csv(file_path, header=1)

    time = data.iloc[:,0]
    binary = [bytes.fromhex(entry) for entry in data.iloc[:,1]]
    biases = (data.iloc[:,2:8].values)

    # Decode forces and torques
    forces_torques = [decode_force_torque(entry, bias) for entry, bias in zip(binary, biases)]
    forces_torques = np.array(forces_torques)  # Convert to a NumPy array for easier plotting

    time_differences = np.diff(time)  # Calculate differences between consecutive timestamps
    avg_time_difference = np.mean(time_differences)  # Average of the time differences
    achieved_frequency = 1 / avg_time_difference  # Invert the average to get the frequency
    print(f"Achieved Sampling Frequency: {achieved_frequency:.2f} Hz")
    
    # Normalize time to start from 0
    time = np.array(time) - time[0]

    # Extract forces and torques
    fx, fy, fz, tx, ty, tz = forces_torques.T  # Transpose to separate columns
    # Plot forces
    plt.figure(figsize=(10, 8))
    plt.subplot(2, 1, 1)
    plt.title('Force vs Time')
    plt.plot(time, fx, '-r', linewidth=2, label='F_x')
    plt.plot(time, fy, '-g', linewidth=2, label='F_y')
    plt.plot(time, fz, '-b', linewidth=2, label='F_z')
    plt.xlabel('Time [s]')
    plt.ylabel('Force [N]')
    plt.ylim([-30, 30])
    plt.legend(fontsize=12)
    plt.grid(True)

    # Plot torques
    plt.subplot(2, 1, 2)
    plt.title('Torque vs Time')
    plt.plot(time, tx, '-c', linewidth=2, label='T_x')
    plt.plot(time, ty, '-m', linewidth=2, label='T_y')
    plt.plot(time, tz, '-k', linewidth=2, label='T_z')
    plt.xlabel('Time [s]')
    plt.ylabel('Torque [Nm]')
    plt.ylim([-1, 1])
    plt.legend(fontsize=12)
    plt.grid(True)

    # Show the plots
    plt.tight_layout()
    plt.show()

plot_ati_data('ATI_data.csv')  # -------CHANGE FILENAME----------


# # Load the CSV file into a DataFrame
# data = pd.read_csv('ascii_data.csv')  # -------CHANGE FILENAME----------

# # Extract specific columns by index
# time = data.iloc[:, 0].apply(get_sec)  # First column (column 1)
# fx = data.iloc[:, 1]    # Second column (column 2)
# fy = data.iloc[:, 2]
# fz = data.iloc[:, 3]
# tx = data.iloc[:, 4]
# ty = data.iloc[:, 5]
# tz = data.iloc[:, 6]

# time = np.array(time) - time[0]  # Normalize time to start from 0
# time_differences = np.diff(time)  # Calculate differences between consecutive timestamps
# avg_time_difference = np.mean(time_differences)  # Average of the time differences
# achieved_frequency = 1 / avg_time_difference  # Invert the average to get the frequency
# print(f"Achieved Sampling Frequency: {achieved_frequency:.2f} Hz")


# time = time - time[0]  # Normalize time to start from 0

# # Define the index range to exclude the first 5 seconds
# index = time >= 5  # This creates a boolean mask where time >= 5

# # Plotting Force vs Time
# plt.figure(figsize=(10, 8))

# # Subplot 1: Force vs Time
# plt.subplot(2, 1, 1)
# plt.title('Force vs Time')
# plt.plot(time[index], fx[index], '-r', linewidth=2, label='F_x')
# plt.plot(time[index], fy[index], '-g', linewidth=2, label='F_y')
# plt.plot(time[index], fz[index], '-b', linewidth=2, label='F_z')
# plt.xlabel('Time [s]')
# plt.ylabel('Force [N]')
# plt.legend(fontsize=12)
# plt.grid(True)
# plt.ylim([-30, 30])
# plt.xticks(fontsize=12)
# plt.yticks(fontsize=12)

# # Subplot 2: Torque vs Time
# plt.subplot(2, 1, 2)
# plt.title('Torque vs Time')
# plt.plot(time[index], tx[index], '-c', linewidth=2, label='T_x')
# plt.plot(time[index], ty[index], '-m', linewidth=2, label='T_y')
# plt.plot(time[index], tz[index], '-k', linewidth=2, label='T_z')
# plt.xlabel('Time [s]')
# plt.ylabel('Torque [N]')
# plt.legend(fontsize=12)
# plt.grid(True)
# plt.ylim([-1, 1])
# plt.xticks(fontsize=12)
# plt.yticks(fontsize=12)

# # Adjust layout and show the plot
# plt.tight_layout()
# plt.show()