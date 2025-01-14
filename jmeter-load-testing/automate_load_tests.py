import os
import time
import subprocess
import shutil

# List of filenames
list1 = ['no-attacker.jmx', 'ddos-5x.jmx', 'ddos-10x.jmx', 'ddos-20x.jmx', 'yoyo-5x.jmx', 'yoyo-10x.jmx', 'yoyo-20x.jmx']  # Replace with your actual filenames
list2 = ['250113_no_attacker', '250113_ddos_5x', '250113_ddos_10x','250113_ddos_20x', '250113_yoyo_5x', '250113_yoyo_10x', '250113_yoyo_20x']  # Replace with your actual output directories

# Ensure the lists are of the same length
if len(list1) != len(list2):
    raise ValueError("Both lists must have the same number of elements.")

# Get the current directory
script_dir = os.getcwd()

while True:
    for file1, file2 in zip(list1, list2):
        # Construct the full paths
        result_file = os.path.join(script_dir, 'results.jtl')
        output_dir = os.path.join(script_dir, file2)
        script_file = os.path.join(script_dir, 'scripts', 'sigmetrics-scripts', file1)

        # Command 1: Run the JMeter command
        jmeter_command = [
            'C:\\NISLAB\\apache-jmeter-5.6.3\\bin\\jmeter.bat', '-n', '-t', script_file, 
            '-l', 'results.jtl', '-e', '-o', output_dir
        ]
        subprocess.run(jmeter_command)

        # Command 2: Move results.jtl to the output directory if it exists
        if os.path.exists(result_file):
            shutil.move(result_file, output_dir)

    # Wait for 2.5 hours (in seconds)
    time.sleep(2.5 * 60 * 60)