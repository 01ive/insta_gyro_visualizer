import pandas as pd
import re

'''
exiftool -m -TimeCode -Accelerometer -AngularVelocity -g -api largefilesupport -S -ee /mnt/d/video/Parapente\ 2024/cantal/VID_20240414_174251_002.insv
'''

'''
Time Code                       : 1034.591
Accelerometer                   : -0.2001953125 -0.9560546875 0.2783203125
Angular Velocity                : 0.0181094954125388 0.00426105774412678 -0.0117179087963486
'''

txt_file_name = 'VID_20240530_173115_003.txt'

video_data = open(txt_file_name, 'r')

points = list()

lines = video_data.readlines()
for line in lines:
    if line.find("Accelerometer") != -1:
        start_of_data = lines.index(line) - 1
        break

accelerometer_table = pd.DataFrame(columns=['Time', 'Acc X', 'Acc Y', 'Acc Z', 'Rot X', 'Rot Y', 'Rot Z'])
new_line = list()

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

'''
Roll = (atan(AccY / sqrt(pow(AccX, 2) + pow(AccZ, 2))) * 180 / PI) ;
Pitch = (atan(-1 * AccX / sqrt(pow(AccY, 2) + pow(AccZ, 2))) * 180 / PI);
'''