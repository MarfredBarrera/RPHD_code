import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse

def get_sec(time_str):
    """Get seconds from time."""
    h, m, s = time_str.split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)

def decode_binary(binary_msg, bias):
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

def decode_ascii(row, bias):
    """
    Decode ASCII data into force and torque values.
    :param row: A row of force/torque values from the CSV file.
    :param bias: List of biases for [Fx, Fy, Fz, Tx, Ty, Tz].
    :return: List of forces and torques in the format [Fx, Fy, Fz, Tx, Ty, Tz].
    """

    # Scaling factors (adjust based on your sensor's calibration)
    counts_to_force = 2.4227  # Example: counts per Newton for force
    counts_to_torque = 110.97  # Example: counts per Newton-meter for torque

    
    # Convert the row to a list of floats
    values = row.astype(float).tolist()


    # Apply biases and return the decoded forces and torques
    return [
        (values[0])/counts_to_force  - bias[0],  # Fx
        (values[1])/counts_to_force - bias[1],  # Fy
        (values[2])/counts_to_force - bias[2],  # Fz
        (values[3])/counts_to_torque - bias[3],  # Tx
        (values[4])/counts_to_torque - bias[4],  # Ty
        (values[5])/counts_to_torque - bias[5],  # Tz
    ]
    


def plot_ati_data(file_path, mode='ascii'):
    # Load the data from the .npy file
    data = pd.read_csv(file_path, header=1)

    time = data.iloc[:, 0]


    # Determine if the data is binary or ASCII
    if mode =='ascii':
        # ASCII data
        data_column = data.iloc[:, 2:8]
        bias_columns = data.iloc[:, 8:14]  # Assuming biases are in columns 8 to 13
        print("Detected ASCII data format.")
        forces_torques = [
            decode_ascii(data_column.iloc[i], bias_columns.iloc[i].astype(float).tolist())
            for i in range(len(data))
        ]
    else:
        # Binary data
        print("Detected binary data format.")
        data_column = data.iloc[:, 1]
        biases = data.iloc[:, 2:8].values
        binary = [bytes.fromhex(entry) for entry in data_column]
        forces_torques = [decode_binary(entry, bias) for entry, bias in zip(binary, biases)]
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



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot ATI data from CSV file.')
    parser.add_argument("file_path", help="Path to the CSV file.")
    parser.add_argument("--mode", choices=["ascii", "binary"], default="ascii",
                        help="Data format: 'ascii' or 'binary'. Default is 'ascii'.")
    
    args = parser.parse_args()


    plot_ati_data(args.file_path, args.mode)  # -------CHANGE FILENAME----------
