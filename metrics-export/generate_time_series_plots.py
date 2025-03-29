"""
Generate plots off of all .csv files in the target directory.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
from glob import glob


def format_title(filename):
    filename = filename.split("\\")[-1]
    # Remove .csv extension
    filename = filename.replace(".csv", "")

    # Split into tokens
    tokens = filename.split("_")

    # Remove date
    tokens = tokens[1:]

    # Handle first token special cases
    if tokens[0].lower() == "bursty":
        tokens[0] = "Bursty Customer"
    elif tokens[0].lower() == "onoff":
        tokens[0] = "On/Off Customer"
    elif tokens[0].lower() == "Random":
        tokens[0] = "Random Customer"
    else:
        tokens[0] = tokens[0].capitalize()

    # Capitalize remaining tokens if they start with a letter
    seen_attack_type = False  # add 'Attacker' token
    for i in range(1, len(tokens)):
        if tokens[i][0].isalpha():
            tokens[i] = tokens[i].capitalize()
        elif not seen_attack_type and tokens[i][0].isnumeric():
            tokens[i] = f"Attacker {tokens[i]}"
            seen_attack_type = True

    # Format the time unit token
    last_token = tokens[-1]
    if last_token[-1] in ["m", "h"]:
        number = last_token[:-1]
        unit = last_token[-1]
        tokens[-1] = f"({number}{unit})"

    tokens.append(", Default Autoscaling")

    return " ".join(tokens)


# Get all CSV files in the current directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Create a pattern to match directories starting with '25'
dir_pattern = os.path.join(script_dir, "25*")
print(dir_pattern)

# List to store all found CSV files
csv_files = []

# Find all directories that start with '25'
matching_dirs = [d for d in glob(dir_pattern) if os.path.isdir(d)]
print(matching_dirs)

# Search each matching directory for CSV files
for directory in matching_dirs:
    # Use recursive glob to find all CSV files in this directory and its subdirectories
    pattern = os.path.join(directory, "*.csv")
    print(pattern)
    # Use recursive=True to search through subdirectories
    files = glob(pattern, recursive=True)
    print(files)
    csv_files.extend(files)
print(csv_files)

# Create a directory for plots if it doesn't exist
plots_dir = "plots"
if not os.path.exists(plots_dir):
    os.makedirs(plots_dir)

# Create plots for each CSV file
for csv_file in csv_files:

    # Read the CSV file with header
    data = pd.read_csv(csv_file)

    # Get column names
    x_col = data.columns[0]
    y_col = data.columns[1]

    # Convert the x-axis to datetime
    data[x_col] = pd.to_datetime(data[x_col])

    # Calculate elapsed time in minutes from the first timestamp
    data["Elapsed Minutes"] = (
        data[x_col] - data[x_col].iloc[0]
    ).dt.total_seconds() / 60

    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.plot(
        data["Elapsed Minutes"], data[y_col], marker=".", markersize=3, linestyle="-"
    )
    plt.title(format_title(csv_file))
    plt.xlabel("Elapsed Time (minutes)")
    plt.ylabel(y_col)

    # Set x-axis limits from 0 to 120 minutes
    plt.xlim(0, 120)

    # Set ticks every 10 minutes
    plt.xticks(range(0, 121, 10))

    # Save the plot with tight layout
    plt.tight_layout()
    plt.savefig(f"{csv_file[:-4]}.png")
    plt.close()
