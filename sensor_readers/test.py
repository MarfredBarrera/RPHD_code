import pandas as pd

file_path = 'ATI_data.csv'
data = pd.read_csv(file_path, header=1)  # Use header=None if the CSV file has no header row

# Extract the relevant columns for force/torque values
time_column = data.iloc[:, 0]  # First column is the timestamp
force_torque_columns = data.iloc[:, 2:8]  # Columns 2 to 7 contain the force/torque values
bias_columns = data.iloc[:, 8:14]  # Columns 8 to 13 contain the biases

def decode_ascii(row, bias):
    """
    Decode ASCII data into force and torque values.
    :param row: A row of force/torque values from the CSV file.
    :param bias: List of biases for [Fx, Fy, Fz, Tx, Ty, Tz].
    :return: List of forces and torques in the format [Fx, Fy, Fz, Tx, Ty, Tz].
    """
    # Convert the row to a list of floats
    values = row.astype(float).tolist()

    # Apply biases and return the decoded forces and torques
    return [
        values[0] - bias[0],  # Fx
        values[1] - bias[1],  # Fy
        values[2] - bias[2],  # Fz
        values[3] - bias[3],  # Tx
        values[4] - bias[4],  # Ty
        values[5] - bias[5],  # Tz
    ]

# Example usage
# bias = bias_columns.iloc[0].astype(float).tolist()  # Extract biases for the first row
print(force_torque_columns.iloc[0].astype(float).tolist())  # Print the first row of force/torque values