import os
import time
import subprocess
import shutil

# List of filenames
list1 = [
    # 'no-attacker.jmx',
    # 'ddos-5x.jmx',
    # 'ddos-10x.jmx',
    # 'ddos-20x.jmx',
    # 'yoyo-5x.jmx',
    # 'yoyo-10x.jmx',
    # 'yoyo-20x.jmx',
    # 'state-aware-5x.jmx',
    # 'state-aware-10x.jmx',
    # 'state-aware-20x.jmx'
    # 'ddos-20x-sanity-check.jmx'
    'ddos-20x-random-seed.jmx',
    'ddos-20x-constant-seed.jmx',
    # 'ddos-20x-random-seed.jmx',
    # 'ddos-20x-constant-seed.jmx'
]
list2 = [
    # '250119_no_attacker',
    # '250119_ddos_5x',
    # '250119_ddos_10x',
    # '250119_ddos_20x',
    # '250119_yoyo_5x',
    # '250119_yoyo_10x',
    # '250119_yoyo_20x',
    # '250119_state_aware_5x',
    # '250119_state_aware_10x',
    # '250119_state_aware_20x'
    # '250120_ddos_20x_sanity_check_v2'
    # '250120_ddos_20x_random_seed_default_hpa',
    # '250120_ddos_20x_constant_seed_default_hpa',
    '250120_ddos_20x_random_seed_randomized_hpa',
    '250120_ddos_20x_constant_seed_randomized_hpa',
]

# Ensure the lists are of the same length
if len(list1) != len(list2):
    print(len(list1))
    print(len(list2))
    raise ValueError("Both lists must have the same number of elements.")

# Get the current directory
script_dir = os.getcwd()

i = 0
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
    print(F'-------------TEST {i} COMPLETE!-------------')
    i+=1

    # change hpa if 2 default tests have ran
    # if i == 2:
    #     print('-------------ATTENTION! CHANGING HPA!-------------')
    #     subprocess.run([
    #         r'C:\Program Files\Docker\Docker\resources\bin\kubectl.exe',
    #         'apply',
    #         '-f',
    #         r'C:\NISLAB\teastore\teastore-hpa-randomized.yaml'
    #     ], check=True)

    # Wait for scale-down
    time.sleep(600) # 10 minutes for 'cooldown'
