import os
import time
import subprocess
import shutil

# List of filenames
list1 = ['no-attacker.jmx',
         'ddos-5x.jmx',
         'ddos-10x.jmx',
         'ddos-20x.jmx',
         'yoyo-5x.jmx',
         'yoyo-10x.jmx',
         'yoyo-20x.jmx',
         'state-aware-5x.jmx',
         'state-aware-10x.jmx',
         'state-aware-20x.jmx']
list2 = ['250114_no_attacker',
         '250114_ddos_5x',
         '250114_ddos_10x',
         '250114_ddos_20x',
         '250114_yoyo_5x',
         '250114_yoyo_10x',
         '250114_yoyo_20x',
         '250114_state_aware_5x',
         '250114_state_aware_10x',
         '250114_state_aware_20x']

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

        # Wait for scale-down
        time.sleep(60 * 60 * 2.25) # 2 hours and 15 minutes for 'cooldown'