import pandas as pd
import numpy as np

def main():
    input_file = input("Enter the path to the CSV file: ").strip().strip('"')

    try:
        # Define correct column names (only 6 columns you need)
        column_names = [
            "Rotation X", "Rotation Y", "Rotation Z",
            "Position X", "Position Y", "Position Z"
        ]

        # Read file, skip first 8 lines, take columns 2 to 7 (after Frame and Time)
        df = pd.read_csv(
            input_file,
            skiprows=8,
            usecols=range(2, 8),
            names=column_names
        )

        # Compute differences: new_row[i] = old[i] - old[i-1]
        diff_df = df.diff()

        # Set first and last row to zeros
        diff_df.iloc[0] = 0
        diff_df.iloc[-1] = 0

        # Reset index
        diff_df = diff_df.reset_index(drop=True)

        # Ask for output file name
        output_file = input("Enter output file name (default: difference_output.csv): ").strip()
        if not output_file:
            output_file = "difference_output.csv"
        elif not output_file.lower().endswith(".csv"):
            output_file += ".csv"

        # Save only the transformed difference data
        diff_df.to_csv(output_file, index=False)
        print(f"\n✅ Frame-to-frame difference CSV saved as: {output_file}")

    except FileNotFoundError:
        print("❌ Error: File not found. Check the file path.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
