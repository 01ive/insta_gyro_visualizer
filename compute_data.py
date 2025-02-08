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

calibration = False

''' Functions '''
def read_json_file(json_file_name, filtering_query=None):
    logging.info("Start computing data from file: " + json_file_name)

    # Generate csv file
    csv_file_name = json_file_name.split('.')[0] + '.csv'

    if os.path.exists(csv_file_name):
        logging.info("CSV file already exists: " + csv_file_name)
        accelerometer_table = pd.read_csv(csv_file_name, sep='\t', index_col=0)
        
        if filtering_query is not None:
            logging.info("Filtering data using query: " + filtering_query)
            accelerometer_table.query(filtering_query, inplace=True)
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
    data_from_video_table = pd.read_json(json.dumps(data_from_video), orient='index')

    logging.info("Generate columns")
    accelerometer_table = pd.DataFrame()
    accelerometer_table['Time'] = data_from_video_table['TimeCode'].apply(lambda x: float(x))
    accelerometer_table['Time'] = accelerometer_table['Time'].apply(lambda x: x-accelerometer_table['Time'][0]) # Calculate time starting to 0
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

def compute_gyro(accelerometer_table):
    accelerometer_table['Time delta'] = accelerometer_table['Time'] - accelerometer_table['Time'].shift(fill_value=0)

    # Processing gyro data
    q = accelerometer_table.apply(lambda x: quaternion.update_quaternion_with_gyro(None, np.array([x['Rot X'], x['Rot Y'], x['Rot Z']]), x['Time delta']), axis=1)
    accelerometer_table['Gyro w'] = q.apply(lambda x: x[0])
    accelerometer_table['Gyro x'] = q.apply(lambda x: x[1])
    accelerometer_table['Gyro y'] = q.apply(lambda x: x[2])
    accelerometer_table['Gyro z'] = q.apply(lambda x: x[3])

    # Generate position from in Euler format
    accelerometer_table['Euler'] = accelerometer_table.apply(lambda x: quaternion.quaternion_to_euler(np.array([x['Gyro w'], x['Gyro x'], x['Gyro y'], x['Gyro z']])), axis=1)
    accelerometer_table['Yaw'] = accelerometer_table.apply(lambda x: x['Euler'][0], axis=1)
    accelerometer_table['Roll'] = accelerometer_table.apply(lambda x: x['Euler'][1], axis=1)
    accelerometer_table['Pich'] = accelerometer_table.apply(lambda x: x['Euler'][2], axis=1)
    del(accelerometer_table['Euler'])
    
    return accelerometer_table

def compute_acc(accelerometer_table):
    # Smooth accelerometer data (low pass filter)
    accelerometer_table = low_pass_filter(accelerometer_table, ['Acc X', 'Acc Y', 'Acc Z'], window=50)
    accelerometer_table = normalize_data(accelerometer_table)

    q = accelerometer_table.apply(lambda x: quaternion.accelerometer_to_quaternion(x['Acc X'], x['Acc Y'], x['Acc Z']), axis=1)
    accelerometer_table['Acc w'] = q.apply(lambda x: x[0])
    accelerometer_table['Acc x'] = q.apply(lambda x: x[1])
    accelerometer_table['Acc y'] = q.apply(lambda x: x[2])
    accelerometer_table['Acc z'] = q.apply(lambda x: x[3])

    # Generate position from in Euler format
    accelerometer_table['Euler'] = accelerometer_table.apply(lambda x: quaternion.quaternion_to_euler(np.array([x['Acc w'], x['Acc x'], x['Acc y'], x['Acc z']])), axis=1)
    accelerometer_table['Acc Yaw'] = accelerometer_table.apply(lambda x: x['Euler'][0], axis=1)
    accelerometer_table['Acc Roll'] = accelerometer_table.apply(lambda x: x['Euler'][1], axis=1)
    accelerometer_table['Acc Pich'] = accelerometer_table.apply(lambda x: x['Euler'][2], axis=1)
    del(accelerometer_table['Euler'])

    return accelerometer_table

def compute_kalman_filter(accelerometer_table):
    # Calibration
    delta_acc_w = 1.0    #   delta_acc_w = 0.00017
    delta_acc_x = 0.01       #   delta_acc_x = 0.0
    delta_acc_y = 0.005    #   delta_acc_y = -0.0085
    delta_acc_z = 0.005    #   delta_acc_z = -0.00065
    delta_gyro_w = 1.0  #   delta_gyro_w = -0.00023
    delta_gyro_x = 0.002  #   delta_gyro_x = 0.0207
    delta_gyro_y = 0.003  #   delta_gyro_y = -0.00269
    delta_gyro_z = 0.004  #   delta_gyro_z = 0.00446
    if calibration:
        logging.info("Calibration")
        cal_table = accelerometer_table[accelerometer_table['Time'] < 7]
        cal_table = cal_table[cal_table['Time'] > 0.05]
        delta_time = cal_table['Time'].iloc[-1] - cal_table['Time'].iloc[0]
        delta_acc_w = cal_table['Acc w'].iloc[-1] - cal_table['Acc w'].iloc[0]
        delta_acc_x = cal_table['Acc x'].iloc[-1] - cal_table['Acc x'].iloc[0]
        delta_acc_y = cal_table['Acc y'].iloc[-1] - cal_table['Acc y'].iloc[0]
        delta_acc_z = cal_table['Acc z'].iloc[-1] - cal_table['Acc z'].iloc[0]
        delta_gyro_w = cal_table['Gyro w'].iloc[-1] - cal_table['Gyro w'].iloc[0]
        delta_gyro_x = cal_table['Gyro x'].iloc[-1] - cal_table['Gyro x'].iloc[0]
        delta_gyro_y = cal_table['Gyro y'].iloc[-1] - cal_table['Gyro y'].iloc[0]
        delta_gyro_z = cal_table['Gyro z'].iloc[-1] - cal_table['Gyro z'].iloc[0]
        logging.info("Calibration data: delta_time = " + str(delta_time) + ", delta_acc_w = " + str(delta_acc_w) + ", delta_acc_x = " + str(delta_acc_x) + ", delta_acc_y = " + str(delta_acc_y) + ", delta_acc_z = " + str(delta_acc_z) + ", delta_gyro_w = " + str(delta_gyro_w) + ", delta_gyro_x = " + str(delta_gyro_x) + ", delta_gyro_y = " + str(delta_gyro_y) + ", delta_gyro_z = " + str(delta_gyro_z))   

    #Apply Kalman filter
    P_new = np.eye(4) * 0.03  # Covariance initiale

    R_gyro = np.eye(4) * np.array([delta_gyro_w, delta_gyro_x, delta_gyro_y, delta_gyro_z])  # Incertitude gyroscope
    R_acc = np.eye(4) * np.array([delta_acc_w, delta_acc_x, delta_acc_y, delta_acc_z]) # Incertitude accéléromètre
    progress_bar = Bar("Processing Kalman filter", max=len(accelerometer_table.index))
    for index in accelerometer_table.index:
        q_gyro = np.array([accelerometer_table['Gyro w'][index], accelerometer_table['Gyro x'][index], accelerometer_table['Gyro y'][index], accelerometer_table['Gyro z'][index]])
        q_acc = np.array([accelerometer_table['Acc w'][index], accelerometer_table['Acc x'][index], accelerometer_table['Acc y'][index], accelerometer_table['Acc z'][index]])
        q, P_new = quaternion.kalman_filter_quaternion(P_new, q_gyro, q_acc, R_gyro, R_acc)
        accelerometer_table.loc[index, 'Kalman w'] = q[0]
        accelerometer_table.loc[index, 'Kalman x'] = q[1]
        accelerometer_table.loc[index, 'Kalman y'] = q[2]
        accelerometer_table.loc[index, 'Kalman z'] = q[3]
        progress_bar.next()
    progress_bar.finish()
    logging.debug("Kalman filter done. Covariance finale = " + str(P_new))
    # Generate position from in Euler format
    accelerometer_table['Euler'] = accelerometer_table.apply(lambda x: quaternion.quaternion_to_euler(np.array([x['Kalman w'], x['Kalman x'], x['Kalman y'], x['Kalman z']])), axis=1)
    accelerometer_table['Kalman Yaw'] = accelerometer_table.apply(lambda x: x['Euler'][0], axis=1)
    accelerometer_table['Kalman Roll'] = accelerometer_table.apply(lambda x: x['Euler'][1], axis=1)
    accelerometer_table['Kalman Pich'] = accelerometer_table.apply(lambda x: x['Euler'][2], axis=1)
    del(accelerometer_table['Euler'])

    return accelerometer_table

def low_pass_filter(accelerometer_table, columns, window=10):
    # Smooth accelerometer data (low pass filter)
    for c in columns:
        accelerometer_table[c] = accelerometer_table[c].rolling(window=window, min_periods=1).mean()
    return accelerometer_table

def normalize_data(accelerometer_table):
    # Normalize accelerometer data
    accelerometer_norm = np.sqrt(np.power(accelerometer_table['Acc X'], 2) + np.power(accelerometer_table['Acc Y'], 2) + np.power(accelerometer_table['Acc Z'], 2))
    accelerometer_table['Acc X'] = accelerometer_table['Acc X'] / accelerometer_norm
    accelerometer_table['Acc Y'] = accelerometer_table['Acc Y'] / accelerometer_norm
    accelerometer_table['Acc Z'] = accelerometer_table['Acc Z'] / accelerometer_norm
    return accelerometer_table

def generate_json(df, json_file_name):
    df.columns = ['Time', 'w', 'x', 'y', 'z']
    df.filter(['Time', 'w', 'x', 'y', 'z'], axis=1).to_json(json_file_name, orient='records', indent=2)

def save_file(accelerometer_table, json_file_name, display_graph=False):
    logging.info("Save data to files")
    
    # Generate json file for gyro data only
    generate_json(accelerometer_table[['Time', 'Gyro w', 'Gyro x', 'Gyro y', 'Gyro z']], json_file_name.split('.')[0] + '_gyro.json')
    logging.info("Json file generated for gyroscope data")

    # Generate json file for acc data only
    generate_json(accelerometer_table[['Time', 'Acc w', 'Acc x', 'Acc y', 'Acc z']], json_file_name.split('.')[0] + '_acc.json')
    logging.info("Json file generated for accelerometer data")

    # Generate json file for kalman data only
    generate_json(accelerometer_table[['Time', 'Kalman w', 'Kalman x', 'Kalman y', 'Kalman z']], json_file_name.split('.')[0] + '_kalman.json')
    logging.info("Json file generated for kalman data")

    # Display graph
    # Remove unused data
    del(accelerometer_table['Acc w'])
    del(accelerometer_table['Acc x'])
    del(accelerometer_table['Acc y'])
    del(accelerometer_table['Acc z'])
    del(accelerometer_table['Gyro w'])
    del(accelerometer_table['Gyro x'])
    del(accelerometer_table['Gyro y'])
    del(accelerometer_table['Gyro z'])
    del(accelerometer_table['Kalman w'])
    del(accelerometer_table['Kalman x'])
    del(accelerometer_table['Kalman y'])
    del(accelerometer_table['Kalman z'])

    # Use time col as index
    accelerometer_table = accelerometer_table.set_index('Time')

    graph = accelerometer_table.plot()
    if display_graph: graph.show()
    html_file_name = json_file_name.split('.')[0] + '.html'
    graph.write_html(html_file_name)
    logging.info("Html file generated: " + html_file_name)

def compute(json_file_name, filtering_query=None):
    # Manage pickle file to save intermediate results from accelerometers and gyroscope
    pkl_file_name = json_file_name.split('.')[0] + '.pkl'
    if not os.path.exists(pkl_file_name):
        # Read json file (exiftool output)
        data_df = read_json_file(json_file_name, filtering_query)

        # Compute accelerometer data using quaternions
        data_df = compute_acc(data_df)

        # Compute gyroscope data using quaternions
        data_df = compute_gyro(data_df)

        # Save results as pickle file
        data_df.to_pickle(json_file_name.split('.')[0] + '.pkl')
    else:
        logging.info("Pickle file from previous precessing found: " + pkl_file_name)
        # Load pickle file
        data_df = pd.read_pickle(json_file_name.split('.')[0] + '.pkl')
        if filtering_query is not None:
            logging.info("Filtering data using query: " + filtering_query)
            data_df.query(filtering_query, inplace=True)

    # Process Kalman filter
    data_df = compute_kalman_filter(data_df)

    json_file_name = json_file_name.split('.')[0] + '_compute.json'
    save_file(data_df, json_file_name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Argument 1 is json file name to process
    json_file_name = sys.argv[1]

    compute(json_file_name, 'Time > 80 and Time < 85')

