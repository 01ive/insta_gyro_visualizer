import sys
import os
import pandas as pd
import plotly.express as px
import numpy as np
import logging
import json

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
    data_from_video_table = pd.DataFrame(columns=data_from_video[list(data_from_video.keys())[0]].keys())
    for item in data_from_video:
        data_from_video_table.loc[item] = data_from_video[item]
    
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

    q = np.array([1, 0, 0, 0])  # Quaternion initial

    for index in accelerometer_table.index:
        # Mise à jour avec le gyroscope
        gyro_data = np.array([accelerometer_table['Rot X'][index], accelerometer_table['Rot Y'][index], accelerometer_table['Rot Z'][index]])
        q = quaternion.update_quaternion_with_gyro(q, gyro_data, accelerometer_table['Time delta'][index])

        accelerometer_table.loc[index, 'w'] = q[0]
        accelerometer_table.loc[index, 'x'] = q[1]
        accelerometer_table.loc[index, 'y'] = q[2]
        accelerometer_table.loc[index, 'z'] = q[3]

    return accelerometer_table

def save_file(accelerometer_table, json_file_name):
    logging.info("Save data to file: " + json_file_name)
    
    # Use time col as index
    accelerometer_table = accelerometer_table.set_index('Time')

    # Display graph
    graph = accelerometer_table.plot()
    graph.show()
    html_file_name = json_file_name.split('.')[0] + '.html'
    graph.write_html(html_file_name)
    logging.info("Html file generated: " + html_file_name)

    # Generate json file
    json_file_name = json_file_name.split('.')[0] + '.json'
    accelerometer_table.filter(['w', 'x', 'y', 'z'], axis=1).reset_index().to_json(json_file_name, orient='records', indent=2)
    logging.info("Json file generated: " + json_file_name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    json_file_name = sys.argv[1]

    data = read_json_file(json_file_name)

    result = compute_data(data)

    json_file_name = json_file_name.split('.')[0] + '_compute.json'
    save_file(result, json_file_name)

