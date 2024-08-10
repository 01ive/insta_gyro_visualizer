'''
float Accelerometer_Sensor::getRotationFromAccelX(){
    float rotation_x;
    rotation_x = (atan2(this->_accel.acceleration.y, this->_accel.acceleration.z)) * RAD_TO_DEG;
    if (rotation_x <= 360 && rotation_x >= 180) {
    rotation_x = 360 - rotation_x;
    }
    return rotation_x;
}

float Accelerometer_Sensor::getRotationFromAccelY(){
    float rotation_y;
    rotation_y = atan(-this->_accel.acceleration.x / sqrt(pow(this->_accel.acceleration.y, 2) + pow(this->_accel.acceleration.z, 2))) * RAD_TO_DEG;
    if (rotation_y <= 360 && rotation_y >= 180) {
    rotation_y = 360 - rotation_y;
    }
    return rotation_y;
}

float Accelerometer_Sensor::getRotationFromGyroX(){
    float sampling_period, rotation_x;

    sampling_period = this->_gyro.timestamp - this->_previous_gyro_x.timestamp;

    rotation_x = this->_gyro.gyro.x * RAD_TO_DEG * sampling_period / 1000;
    if(abs(rotation_x) > 0.1) {
        rotation_x += this->_previous_gyro_x.orientation.x;
        this->_previous_gyro_x.orientation.x = rotation_x;
        this->_previous_gyro_x.timestamp = this->_gyro.timestamp;
    }

    return rotation_x;
}

float Accelerometer_Sensor::getRotationFromGyroY(){
    float sampling_period, rotation_y;

    sampling_period = this->_gyro.timestamp - this->_previous_gyro_y.timestamp;

    rotation_y = this->_gyro.gyro.y * RAD_TO_DEG * sampling_period / 1000;
    if(abs(rotation_y) > 0.1) {
        rotation_y += this->_previous_gyro_x.orientation.y;
        this->_previous_gyro_y.orientation.y = rotation_y;
        this->_previous_gyro_y.timestamp = this->_gyro.timestamp;
    }

    return rotation_y;
}

float Accelerometer_Sensor::getRotationFromGyroZ(){
    float sampling_period, rotation_z;

    sampling_period = this->_gyro.timestamp - this->_previous_gyro_z.timestamp;

    rotation_z = this->_gyro.gyro.z * RAD_TO_DEG * sampling_period / 1000;
    if(abs(rotation_z) > 0.1) {
        rotation_z += this->_previous_gyro_z.orientation.z;
        this->_previous_gyro_z.orientation.z = rotation_z;
        this->_previous_gyro_z.timestamp = this->_gyro.timestamp;
    }

    return rotation_z;
}
'''

'''
// Calculating Roll and Pitch from the accelerometer data
  Roll = (atan(AccY / sqrt(pow(AccX, 2) + pow(AccZ, 2))) * 180 / PI) ;

  Pitch = (atan(-1 * AccX / sqrt(pow(AccY, 2) + pow(AccZ, 2))) * 180 / PI); 
'''

'''
http://samselectronicsprojects.blogspot.com/2014/07/getting-roll-pitch-and-yaw-from-mpu-6050.html

    Roll = atan2(Y, Z) * 180/PI;
    Pitch = atan2(X, sqrt(Y*Y + Z*Z)) * 180/PI;

// Calculate Pitch, Roll and Yaw
  pitch = pitch + norm.YAxis * timeStep;
  roll = roll + norm.XAxis * timeStep;
  yaw = yaw + norm.ZAxis * timeStep;

  X pitch
  Y roll
  Z yaw

  1034.6 - 25.691 = 1008.909

  16:48 => 1008

  30 i/s => 1 image 33ms 0.033

  https://atadiat.com/en/e-towards-understanding-imu-basics-of-accelerometer-and-gyroscope-sensors/
  
'''

def low_pass(data, filter):
    for i in range(1, len(data)):
        data[i] = filter*data[i-1] + (1-filter)*data[i]
    return data

def remove_bias(data):
    bias_filter = np.pi / 24
    medium_last = data[0]
    bias = 0
    for i in range(1, len(data)):
        if(np.abs(data[i] - medium_last) < bias_filter):
            bias = np.abs(medium_last)
            medium_last = 0.99*medium_last + 0.01*data[i]
        else:
            pass
        data[i] = data[i] - np.sign(data[i]) * bias

    return data

FRAME_RATE = 0.03
SAMPLING_FILTER = 5
IMU_SAMPLING_PERIOD = 0.002

import pandas as pd
import plotly.express as px
import numpy as np

csv_file_name = 'VID_20240530_173115_003.csv'

pd.options.plotting.backend = "plotly"

accelerometer_table = pd.read_csv(csv_file_name, sep='\t', index_col=0)

# accelerometer_table.drop(accelerometer_table.columns[0], axis='columns', inplace=True)
# Calculate time starting to 0
accelerometer_table['Time'] = accelerometer_table['Time'].apply(lambda x: x-accelerometer_table['Time'][0])
accelerometer_table['Time delta'] = accelerometer_table['Time'] - accelerometer_table['Time'].shift()
accelerometer_table['Time delta'] = accelerometer_table['Time delta'].shift(-1, fill_value=0)

# Low pass filter
accelerometer_table['Rot X'] = low_pass(accelerometer_table['Rot X'], 0.99)
accelerometer_table['Rot Y'] = low_pass(accelerometer_table['Rot Y'], 0.99)
accelerometer_table['Rot Z'] = low_pass(accelerometer_table['Rot Z'], 0.99)

# Rotation from rotation speed sensor
accelerometer_table['Rotation X'] = accelerometer_table['Rot X'] * accelerometer_table['Time delta'] # * 180 / np.pi
accelerometer_table['Rotation Y'] = accelerometer_table['Rot Y'] * accelerometer_table['Time delta'] # * 180 / np.pi
accelerometer_table['Rotation Z'] = accelerometer_table['Rot Z'] * accelerometer_table['Time delta'] # * 180 / np.pi
accelerometer_table['Rotation X'] = accelerometer_table['Rotation X'].cumsum()
accelerometer_table['Rotation Y'] = accelerometer_table['Rotation Y'].cumsum()
accelerometer_table['Rotation Z'] = accelerometer_table['Rotation Z'].cumsum()

# Remove bias
accelerometer_table['Rotation X org'] = accelerometer_table['Rotation X']
accelerometer_table['Rotation X'] = remove_bias(accelerometer_table['Rotation X'])
accelerometer_table['Rotation Y org'] = accelerometer_table['Rotation Y']
accelerometer_table['Rotation Y'] = remove_bias(accelerometer_table['Rotation Y'])
accelerometer_table['Rotation Z org'] = accelerometer_table['Rotation Z']
accelerometer_table['Rotation Z'] = remove_bias(accelerometer_table['Rotation Z'])

# Rotation angle in radians between -pi and pi
accelerometer_table['Rotation X angle'] = accelerometer_table['Rotation X'].apply(lambda x: x if np.abs(x) <= np.pi else x - np.sign(x) * 2*np.pi)
accelerometer_table['Rotation Y angle'] = accelerometer_table['Rotation Y'].apply(lambda x: x if np.abs(x) <= np.pi else x - np.sign(x) * 2*np.pi)
accelerometer_table['Rotation Z angle'] = accelerometer_table['Rotation Z'].apply(lambda x: x if np.abs(x) <= np.pi else x - np.sign(x) * 2*np.pi)

# Acc
accelerometer_table['roll acc X 2D'] = np.arctan2(accelerometer_table['Acc Y'], accelerometer_table['Acc Z']) # * 180 / np.pi
accelerometer_table['roll acc Y 2D'] = np.arctan2(accelerometer_table['Acc Z'], accelerometer_table['Acc X']) # * 180 / np.pi
accelerometer_table['roll acc Z 2D'] = np.arctan2(accelerometer_table['Acc X'], accelerometer_table['Acc Y']) # * 180 / np.pi


# accelerometer_table['pich acc X 3D'] = np.arctan2(accelerometer_table['Acc X'], np.sqrt(
#                                     np.power(accelerometer_table['Acc Y'], 2) + 
#                                     np.power(accelerometer_table['Acc Z'], 2) )  )
# accelerometer_table['pich acc Y 3D'] = np.arctan2(accelerometer_table['Acc Z'], np.sqrt(
#                                     np.power(accelerometer_table['Acc Y'], 2) + 
#                                     np.power(accelerometer_table['Acc X'], 2) )  )
# accelerometer_table['pich acc Z 3D'] = np.arctan2(accelerometer_table['Acc Y'], np.sqrt(
#                                     np.power(accelerometer_table['Acc X'], 2) + 
#                                     np.power(accelerometer_table['Acc Z'], 2) )  )

# accelerometer_table['pich acc Y 3D'] = accelerometer_table['pich acc Y 3D'].apply(lambda x: x if x>=0 else x+2*np.pi )


# accelerometer_table['tan X'] = np.arctan2(accelerometer_table['Acc X'], np.sign(accelerometer_table['Acc Y']) * np.sqrt(
#                                     np.power(accelerometer_table['Acc Y'], 2) + 
                                    # np.power(accelerometer_table['Acc Z'], 2) )  )
# accelerometer_table['tan Y'] = np.arctan2(accelerometer_table['Acc Z'], - np.sign(accelerometer_table['Acc Y']) * np.sqrt(
#                                     np.power(accelerometer_table['Acc Y'], 2) + 
#                                     np.power(accelerometer_table['Acc X'], 2) )  )
# accelerometer_table['tan Z'] = np.arctan2(accelerometer_table['Acc Y'], np.sign(accelerometer_table['Acc Z']) * np.sqrt(
#                                     np.power(accelerometer_table['Acc X'], 2) + 
#                                     np.power(accelerometer_table['Acc Z'], 2) )  )


# accelerometer_table['pich acc X 3D'] = accelerometer_table['pich acc X 3D'].cumsum()
# accelerometer_table['pich acc Y 3D'] = accelerometer_table['pich acc Y 3D'].cumsum()
# accelerometer_table['pich acc Z 3D'] = accelerometer_table['pich acc Z 3D'].cumsum()

# ref_acc = 'pich acc Y 3D'
# ref_acc = 'roll acc Y 2D'

# accelerometer_table['filtered Y'] = accelerometer_table[ref_acc]
# accelerometer_table.loc[0]['filtered Y'] = accelerometer_table.loc[0][ref_acc]
# for i in range(1, len(accelerometer_table)):
#     accelerometer_table.loc[i]['filtered Y'] = 0.95*accelerometer_table.loc[i-1]['filtered Y'] + 0.05*accelerometer_table.loc[i][ref_acc]
#     # accelerometer_table.loc[i]['filtered Y'] /= np.pi
#     # accelerometer_table.loc[i]['filtered Y'] *= accelerometer_table.loc[i]['roll acc Y 2D']
#     # accelerometer_table.loc[i]['roll rot Y angle'] = accelerometer_table.loc[i]['roll rot Y angle'] if np.abs(accelerometer_table.loc[i]['roll rot Y angle'] - accelerometer_table.loc[i-1]['roll rot Y angle']) > np.pi/45 else accelerometer_table.loc[i-1]['roll rot Y angle']
#     accelerometer_table.loc[i]['filtered Y'] = 0.5*accelerometer_table.loc[i]['filtered Y'] + 0.5*accelerometer_table.loc[i]['roll rot Y angle']

nb_sample = SAMPLING_FILTER

# filtered_accelerometer_table = pd.DataFrame(columns=accelerometer_table.columns)

# for i in range(0, len(accelerometer_table), nb_sample):
#     end_of_zone = i+nb_sample
#     if end_of_zone > len(accelerometer_table):
#         end_of_zone = len(accelerometer_table)-1

#     filtered_accelerometer_table.loc[i] = accelerometer_table[i:end_of_zone].sum() / nb_sample
#     filtered_accelerometer_table.loc[i]['Time'] = accelerometer_table.iloc[end_of_zone]['Time']

# filtered_accelerometer_table.set_index(filtered_accelerometer_table.columns[0], inplace=True)
# graph = filtered_accelerometer_table.plot()

# Use time col as index
accelerometer_table = accelerometer_table.set_index('Time')

graph = accelerometer_table.plot()
graph.show()
graph.write_html(csv_file_name.split('.')[0] + '.html')

# accelerometer_table = filtered_accelerometer_table

# pitch = 0
# roll = 0
# yaw = 0

# size = len(accelerometer_table)

# blocks = [index for index in range(size) if index%100000 == 0]

# for block in range(len(blocks)):
#     if block == len(blocks)-1:
#         graph = accelerometer_table.iloc[blocks[block]:].plot()
#     else:
#         graph = accelerometer_table.iloc[blocks[block]:blocks[block+1]].plot()
#     graph.show()

# graph = accelerometer_table.plot()
# graph.show()

pass 