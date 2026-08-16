import os
import glob
import pandas as pd


def convert_csv_to_json(csv_folder="."):
    # Find all CSV files in the specified directory
    csv_files = glob.glob(os.path.join(csv_folder, "*.csv"))

    if not csv_files:
        print("No CSV files found.")
        return

    for file_path in csv_files:
        # Read the CSV file
        df = pd.read_csv(file_path)

        # Generate output JSON file path with the same base name
        json_path = os.path.splitext(file_path)[0] + ".json"

        # Convert and save as formatted JSON (records format)
        df.to_json(json_path, orient="records", indent=4)
        print(f"Successfully converted: '{file_path}' -> '{json_path}'")


if __name__ == "__main__":
    convert_csv_to_json()