import os
import time
import subprocess
import shutil

# List of filenames
list1 = [
    # 'state-aware-sanity-check.jmx'
    # 'no-attacker.jmx',
    # 'ddos-5x.jmx',
    # 'ddos-10x.jmx',
    # 'ddos-20x.jmx',
    # 'yoyo-5x.jmx',
    # 'yoyo-10x.jmx',
    # 'yoyo-20x.jmx',
    # 'state-aware-5x.jmx',
    'state-aware-10x.jmx',
    'state-aware-20x.jmx'
]
list2 = [
    # '250116_state_aware_sanity_check'
    # '250116_no_attacker',
    # '250116_ddos_5x',
    # '250116_ddos_10x',
    # '250116_ddos_20x',
    # '250116_yoyo_5x',
    # '250116_yoyo_10x',
    # '250116_yoyo_20x',
    # '250115_state_aware_5x',
    '250115_state_aware_10x',
    '250115_state_aware_20x'
]

# Ensure the lists are of the same length
if len(list1) != len(list2):
    print(len(list1))
    print(len(list2))
    raise ValueError("Both lists must have the same number of elements.")

# Get the current directory
script_dir = os.getcwd()

for file1, file2 in zip(list1, list2):
    # Construct the full paths
    result_file = os.path.join(script_dir, 'results.csv')
    output_dir = os.path.join(script_dir, file2)
    script_file = os.path.join(script_dir, 'scripts', 'sigmetrics-scripts', file1)

    # Command 1: Run the JMeter command
    jmeter_command = [
        'C:\\NISLAB\\apache-jmeter-5.6.3\\bin\\jmeter.bat', '-n', '-t', script_file, 
        '-l', 'results.csv', '-e', '-o', output_dir
    ]
    subprocess.run(jmeter_command)

    # Command 2: Move results.jtl to the output directory if it exists
    if os.path.exists(result_file):
        shutil.move(result_file, output_dir)

    # Wait for scale-down
    time.sleep(600) # 10 minutes for 'cooldown'