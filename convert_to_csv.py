import sys
import pandas as pd
import re

txt_file_name = sys.argv[1]

video_data = open(txt_file_name, 'r')

points = list()

# Search begining of information
lines = video_data.readlines()
for line in lines:
    if line.find("Accelerometer") != -1:
        start_of_data = lines.index(line) - 1
        break

# Prepare dataframe
accelerometer_table = pd.DataFrame(columns=['Time', 'Acc X', 'Acc Y', 'Acc Z', 'Rot X', 'Rot Y', 'Rot Z'])
new_line = list()

# Read data in the order Time Code / Accelerometer / AngularVelocity   
for line in lines[start_of_data:]:
    if line.startswith("TimeCode"):
        s = re.search('\w+:\s([\w\.]+)', line)
        time_code = float(s.group(1))
        new_line.append(time_code)
    elif line.startswith("Accelerometer"):
        s = re.search('\w+:\s([\w\.-]+)\s([\w\.-]+)\s([\w\.-]+)', line)
        acc_x = float(s.group(1))
        acc_y = float(s.group(2))
        acc_z = float(s.group(3))
        new_line.append(acc_x)
        new_line.append(acc_y)
        new_line.append(acc_z)
    elif line.startswith("AngularVelocity"):
        s = re.search('\w+:\s([\w\.-]+)\s([\w\.-]+)\s([\w\.-]+)', line)
        ang_x = float(s.group(1))
        ang_y = float(s.group(2))
        ang_z = float(s.group(3))
        new_line.append(ang_x)
        new_line.append(ang_y)
        new_line.append(ang_z)
        accelerometer_table.loc[len(accelerometer_table)] = new_line
        new_line = list()
        print(time_code, end='\t')
    else:
        break

accelerometer_table.to_csv(txt_file_name.split('.')[0] + '.csv', sep='\t')
