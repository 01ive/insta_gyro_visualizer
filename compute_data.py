import sys
import os
import pandas as pd
import plotly.express as px
import numpy as np
import logging
import json

from progress.bar import Bar

import quaternion

pd.options.plotting.backend = "plotly"


''' Functions '''
def read_json_file(json_file_name):
    logging.info("Start computing data from file: " + json_file_name)

    # Generate csv file
    csv_file_name = json_file_name.split('.')[0] + '.csv'

    if os.path.exists(csv_file_name):
        logging.info("CSV file already exists: " + csv_file_name)
        accelerometer_table = pd.read_csv(csv_file_name, sep='\t', index_col=0)
        return accelerometer_table

    logging.info("CSV file not found, generating it")
    with open(json_file_name) as f:
        data_from_video = json.load(f)
    
    # Remove unused data
    logging.info("Remove unused data")
    data_from_video = data_from_video[0]
    key = list(data_from_video.keys()).copy()
    for item in key:
        if (len(data_from_video[item]) == 1) or item == 'SourceFile':
            del(data_from_video[item])

    # Convert to pandas dataframe
    logging.info("Convert to pandas dataframe")
    progress_bar = Bar("Processing data", max=len(data_from_video))
    data_from_video_table = pd.DataFrame(columns=data_from_video[list(data_from_video.keys())[0]].keys())
    for item in data_from_video:
        data_from_video_table.loc[item] = data_from_video[item]
        progress_bar.next()
    progress_bar.finish()

    logging.info("Generate columns")
    accelerometer_table = pd.DataFrame()
    accelerometer_table['Time'] = data_from_video_table['TimeCode'].apply(lambda x: float(x))
    accelerometer_table['Acc X'] = data_from_video_table['Accelerometer'].apply(lambda x: float(x.split(' ')[0]))
    accelerometer_table['Acc Y'] = data_from_video_table['Accelerometer'].apply(lambda x: float(x.split(' ')[1]))
    accelerometer_table['Acc Z'] = data_from_video_table['Accelerometer'].apply(lambda x: float(x.split(' ')[2]))
    accelerometer_table['Rot X'] = data_from_video_table['AngularVelocity'].apply(lambda x: float(x.split(' ')[0]))
    accelerometer_table['Rot Y'] = data_from_video_table['AngularVelocity'].apply(lambda x: float(x.split(' ')[1]))
    accelerometer_table['Rot Z'] = data_from_video_table['AngularVelocity'].apply(lambda x: float(x.split(' ')[2]))

    # Generate csv file
    accelerometer_table.reset_index().filter(['Time', 'Acc X', 'Acc Y', 'Acc Z', 'Rot X', 'Rot Y', 'Rot Z'], axis=1).to_csv(csv_file_name, sep='\t')
    logging.info("CSV file generated: " + csv_file_name)

    return accelerometer_table

def compute_data(accelerometer_table):
    # Calculate time starting to 0
    accelerometer_table['Time'] = accelerometer_table['Time'].apply(lambda x: x-accelerometer_table['Time'][0])
    accelerometer_table['Time delta'] = accelerometer_table['Time'] - accelerometer_table['Time'].shift(fill_value=0)

    q = np.array([1, 0, 0, 0]) # Quaternion initial
    progress_bar = Bar("Processing data", max=len(accelerometer_table.index))
    for index in accelerometer_table.index:
        # Mise à jour avec le gyroscope
        gyro_data = np.array([accelerometer_table['Rot X'][index], accelerometer_table['Rot Y'][index], accelerometer_table['Rot Z'][index]])

        q = quaternion.update_quaternion_with_gyro(q, gyro_data, accelerometer_table['Time delta'][index])

        accelerometer_table.loc[index, 'w'] = q[0]
        accelerometer_table.loc[index, 'x'] = q[1]
        accelerometer_table.loc[index, 'y'] = q[2]
        accelerometer_table.loc[index, 'z'] = q[3]
        progress_bar.next()

    progress_bar.finish()

    # Generate position from in Euler format
    accelerometer_table['Euler'] = accelerometer_table.apply(lambda x: quaternion.quaternion_to_euler(np.array([x['w'], x['x'], x['y'], x['z']])), axis=1)
    accelerometer_table['Yaw'] = accelerometer_table.apply(lambda x: x['Euler'][0], axis=1)
    accelerometer_table['Roll'] = accelerometer_table.apply(lambda x: x['Euler'][1], axis=1)
    accelerometer_table['Pich'] = accelerometer_table.apply(lambda x: x['Euler'][2], axis=1)
    del(accelerometer_table['Euler'])
    
    return accelerometer_table

def low_pass_filter(accelerometer_table, columns, window=10):
    # Smooth accelerometer data (low pass filter)
    for c in columns:
        accelerometer_table[c] = accelerometer_table[c].rolling(window=window, center=False).mean()
    return accelerometer_table

def normalize_data(accelerometer_table):
    # Normalize accelerometer data
    # return data / np.linalg.norm(data)
    accelerometer_norm = np.sqrt(np.power(accelerometer_table['Acc X'], 2) + np.power(accelerometer_table['Acc Y'], 2) + np.power(accelerometer_table['Acc Z'], 2))
    accelerometer_table['Acc X'] = accelerometer_table['Acc X'] / accelerometer_norm
    accelerometer_table['Acc Y'] = accelerometer_table['Acc Y'] / accelerometer_norm
    accelerometer_table['Acc Z'] = accelerometer_table['Acc Z'] / accelerometer_norm
    return accelerometer_table

def process_accelerometer_data(accelerometer_table):
    # Smooth accelerometer data (low pass filter)
    accelerometer_table['Acc X'] = accelerometer_table['Acc X'].rolling(window=10, center=False).mean()
    accelerometer_table['Acc Y'] = accelerometer_table['Acc Y'].rolling(window=10, center=False).mean()
    accelerometer_table['Acc Z'] = accelerometer_table['Acc Z'].rolling(window=10, center=False).mean()

    # Normalize accelerometer data
    accelerometer_norm = np.sqrt(np.power(accelerometer_table['Acc X'], 2) + np.power(accelerometer_table['Acc Y'], 2) + np.power(accelerometer_table['Acc Z'], 2))
    accelerometer_table['Acc X'] = accelerometer_table['Acc X'] / accelerometer_norm
    accelerometer_table['Acc Y'] = accelerometer_table['Acc Y'] / accelerometer_norm
    accelerometer_table['Acc Z'] = accelerometer_table['Acc Z'] / accelerometer_norm

    # Calculate rotation angle from accelerator sensor
    # Roll is around Y axis
    accelerometer_table['Acc Pitch'] = np.arctan2(accelerometer_table['Acc Z'], accelerometer_table['Acc X'])
    
    # Picth is around Z axis and gravity impacts X and Z axis
    accelerometer_table['Acc Roll'] = np.arctan2(accelerometer_table['Acc Z'], np.sqrt(
                                        np.power(accelerometer_table['Acc X'], 2) + 
                                        np.power(accelerometer_table['Acc Y'], 2) )  )
    
    # Compute coefficients for sin and cos
    cr = np.cos(accelerometer_table['Acc Roll'] / 2)
    cp = np.cos(accelerometer_table['Acc Pitch'] / 2)
    sr = np.sin(accelerometer_table['Acc Roll'] / 2)
    sp = np.sin(accelerometer_table['Acc Pitch'] / 2)
    cy = 1
    sy = 0

    # Calcul des quaternions
    accelerometer_table['Acc w'] = cr * cp * cy + sr * sp * sy
    accelerometer_table['Acc x'] = sr * cp * cy - cr * sp * sy
    accelerometer_table['Acc y'] = cr * sp * cy + sr * cp * sy
    accelerometer_table['Acc z'] = cr * cp * sy - sr * sp * cy

    return accelerometer_table

def save_file(accelerometer_table, json_file_name, display_graph=False):
    logging.info("Save data to file: " + json_file_name)
    
    # Use time col as index
    accelerometer_table = accelerometer_table.set_index('Time')

    # Generate json file
    accelerometer_table.filter(['w', 'x', 'y', 'z'], axis=1).reset_index().to_json(json_file_name, orient='records', indent=2)

    accelerometer_table['w'] = accelerometer_table['Acc w']
    accelerometer_table['x'] = accelerometer_table['Acc x']
    accelerometer_table['y'] = accelerometer_table['Acc y']
    accelerometer_table['z'] = accelerometer_table['Acc z']
    accelerometer_table.filter(['w', 'x', 'y', 'z'], axis=1).reset_index().to_json(json_file_name.split('.')[0] + '_acc.json', orient='records', indent=2)
    logging.info("Json file generated: " + json_file_name)

    # Display graph
    del(accelerometer_table['Acc w'])
    del(accelerometer_table['Acc x'])
    del(accelerometer_table['Acc y'])
    del(accelerometer_table['Acc z'])
    del(accelerometer_table['w'])
    del(accelerometer_table['x'])
    del(accelerometer_table['y'])
    del(accelerometer_table['z'])

    graph = accelerometer_table.plot()
    if display_graph: graph.show()
    html_file_name = json_file_name.split('.')[0] + '.html'
    graph.write_html(html_file_name)
    logging.info("Html file generated: " + html_file_name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    json_file_name = sys.argv[1]

    data = read_json_file(json_file_name)

    # Process accelerometer data to get orientation
    # data = process_accelerometer_data(data)
    
    # new method
    # Smooth accelerometer data (low pass filter)
    data = low_pass_filter(data, ['Acc X', 'Acc Y', 'Acc Z'], window=20)
    data = normalize_data(data)
    progress_bar = Bar("Processing Acc data", max=len(data.index))
    for index in data.index:
        q = quaternion.accelerometer_to_quaternion(data['Acc X'][index], data['Acc Y'][index], data['Acc Z'][index])
        data.loc[index, 'Acc w'] = q[0]
        data.loc[index, 'Acc x'] = q[1]
        data.loc[index, 'Acc y'] = q[2]
        data.loc[index, 'Acc z'] = q[3]
        progress_bar.next()
    progress_bar.finish()

    # Generate position from in Euler format
    data['Euler'] = data.apply(lambda x: quaternion.quaternion_to_euler(np.array([x['Acc w'], x['Acc x'], x['Acc y'], x['Acc z']])), axis=1)
    data['Acc Yaw'] = data.apply(lambda x: x['Euler'][0], axis=1)
    data['Acc Roll'] = data.apply(lambda x: x['Euler'][1], axis=1)
    data['Acc Pich'] = data.apply(lambda x: x['Euler'][2], axis=1)
    del(data['Euler'])

    # Compute gyroscope data using quaternions
    result = compute_data(data)

    json_file_name = json_file_name.split('.')[0] + '_compute.json'
    save_file(result, json_file_name, True)

