import os
import time
import subprocess
import shutil

# List of filenames
script_list = [
    # "random-yoyo-5x.jmx",
    # "random-yoyo-10x.jmx",
    # "random-yoyo-20x.jmx",
    # "random-state-aware-5x.jmx",
    # "random-state-aware-10x.jmx",
    # "random-state-aware-20x.jmx",
    # "random-sliding-window-5x.jmx",
    # "random-sliding-window-10x.jmx",
    # "random-sliding-window-20x.jmx",
    "onoff-yoyo-5x.jmx",
    "onoff-yoyo-10x.jmx",
    "onoff-yoyo-20x.jmx",
    "onoff-yoyo-overlap-5x.jmx",
    "onoff-yoyo-overlap-10x.jmx",
    "onoff-yoyo-overlap-20x.jmx",
    "onoff-state-aware-5x.jmx",
    "onoff-state-aware-10x.jmx",
    "onoff-state-aware-20x.jmx",
    "onoff-sliding-window-5x.jmx",
    "onoff-sliding-window-10x.jmx",
    "onoff-sliding-window-20x.jmx",
    "bursty-yoyo-5x.jmx",
    "bursty-yoyo-10x.jmx",
    "bursty-yoyo-20x.jmx",
    "bursty-state-aware-5x.jmx",
    "bursty-state-aware-10x.jmx",
    "bursty-state-aware-20x.jmx",
    "bursty-sliding-window-5x.jmx",
    "bursty-sliding-window-10x.jmx",
    "bursty-sliding-window-20x.jmx",
]
output_dir_list = [
    # "250325_random_yoyo_5x_sanity_check_v2_batch",
    # "250325_random_yoyo_10x",
    # "250325_random_yoyo_20x",
    # "250325_random_state_aware_5x",
    # "250325_random_state_aware_10x",
    # "250325_random_state_aware_20x",
    # "250323_sliding_window_5x_v2",
    # "250323_sliding_window_10x_v2",
    # "250323_sliding_window_20x_v2",
    "250326_onoff_yoyo_5x",
    "250326_onoff_yoyo_10x",
    "250326_onoff_yoyo_20x",
    "250326_onoff_yoyo_overlap_5x",
    "250326_onoff_yoyo_overlap_10x",
    "250326_onoff_yoyo_overlap_20x",
    "250326_onoff_state_aware_5x",
    "250326_onoff_state_aware_10x",
    "250326_onoff_state_aware_20x",
    "250326_onoff_sliding_window_5x",
    "250326_onoff_sliding_window_10x",
    "250326_onoff_sliding_window_20x",
    "250326_bursty_yoyo_5x",
    "250326_bursty_yoyo_10x",
    "250326_bursty_yoyo_20x",
    "250326_bursty_state_aware_5x",
    "250326_bursty_state_aware_10x",
    "250326_bursty_state_aware_20x",
    "250326_bursty_sliding_window_5x",
    "250326_bursty_sliding_window_10x",
    "250326_bursty_sliding_window_20x",
]

# Ensure the lists are of the same length
if len(script_list) != len(output_dir_list):
    print(len(script_list))
    print(len(output_dir_list))
    raise ValueError("Both lists must have the same number of elements.")

# Get the current directory
script_dir = os.getcwd()

i = 1
for file1, file2 in zip(script_list, output_dir_list):
    # Construct the full paths
    result_file = os.path.join(script_dir, "results.csv")
    output_dir = os.path.join(script_dir, file2)
    script_file = os.path.join(
        script_dir, "scripts", "sigmetrics-revision-scripts", file1
    )

    # Command 1: Run the JMeter command
    jmeter_command = [
        "C:\\NISLAB\\apache-jmeter-5.6.3\\bin\\jmeter.bat",
        "-n",
        "-t",
        script_file,
        "-l",
        f"results.csv",
        "-e",
        "-o",
        output_dir,
    ]
    subprocess.run(jmeter_command)

    # Command 2: Move results.jtl to the output directory if it exists
    if os.path.exists(result_file):
        shutil.move(result_file, output_dir)
    print(f"-------------TEST {i} COMPLETE!-------------")
    i += 1

    # change hpa to randomized if 2 default tests have ran
    # if i == 2:
    #     print('-------------ATTENTION! CHANGING HPA!-------------')
    #     subprocess.run([
    #         r'C:\Program Files\Docker\Docker\resources\bin\kubectl.exe',
    #         'apply',
    #         '-f',
    #         r'C:\NISLAB\teastore\teastore-hpa-randomized.yaml'
    #     ], check=True)

    # Wait for scale-down
    time.sleep(600)  # 10 minutes for 'cooldown'
