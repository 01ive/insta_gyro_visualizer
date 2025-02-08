import sys
import os
import pandas as pd
import numpy as np
import logging
import json

import quaternion

pd.options.plotting.backend = "plotly"

calibration = True

''' Functions '''
def read_json_file(json_file_name, filtering_query=None, force=False):
    logging.info("Start computing data from file: " + json_file_name)

    # Generate csv file
    csv_file_name = json_file_name.split('.')[0] + '.csv'

    if os.path.exists(csv_file_name) and not force:
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
    accelerometer_table.loc[:, 'Time'] = accelerometer_table['Time'].apply(lambda x: x-accelerometer_table['Time'][0]) # Calculate time starting to 0
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
    result = pd.DataFrame()
    result['Time delta'] = accelerometer_table['Time'] - accelerometer_table['Time'].shift(fill_value=0)

    # Processing gyro data
    q_init = np.array([1, 0, 0, 0]) # Quaternion initial
    q = pd.concat([accelerometer_table, result], axis=1).apply(lambda x: quaternion.update_quaternion_with_gyro(q_init, np.array([x['Rot X'], x['Rot Y'], x['Rot Z']]), x['Time delta']), axis=1)
    result['Gyro w'] = q.apply(lambda x: x[0])
    result['Gyro x'] = q.apply(lambda x: x[1])
    result['Gyro y'] = q.apply(lambda x: x[2])
    result['Gyro z'] = q.apply(lambda x: x[3])

    # Generate position from in Euler format
    euler = result.apply(lambda x: quaternion.quaternion_to_euler(np.array([x['Gyro w'], x['Gyro x'], x['Gyro y'], x['Gyro z']])), axis=1)
    result['Yaw'] = euler.apply(lambda x: x[0])
    result['Roll'] = euler.apply(lambda x: x[1])
    result['Pich'] = euler.apply(lambda x: x[2])
    
    return result

def compute_acc(accelerometer_table):
    # Smooth accelerometer data (low pass filter)
    result = low_pass_filter(accelerometer_table, window=50)
    result = normalize_data(result)

    q = result.apply(lambda x: quaternion.accelerometer_to_quaternion(x['Acc X'], x['Acc Y'], x['Acc Z']), axis=1)
    result['Acc w'] = q.apply(lambda x: x[0])
    result['Acc x'] = q.apply(lambda x: x[1])
    result['Acc y'] = q.apply(lambda x: x[2])
    result['Acc z'] = q.apply(lambda x: x[3])

    # Generate position from in Euler format
    euler = result.apply(lambda x: quaternion.quaternion_to_euler(np.array([x['Acc w'], x['Acc x'], x['Acc y'], x['Acc z']])), axis=1)
    result['Acc Yaw'] = euler.apply(lambda x: x[0])
    result['Acc Roll'] = euler.apply(lambda x: x[1])
    result['Acc Pich'] = euler.apply(lambda x: x[2])

    result.drop(result[['Acc X', 'Acc Y', 'Acc Z']], axis=1, inplace=True)

    return result

def compute_kalman_filter(accelerometer_table, calibration=False):
    result = pd.DataFrame()
    if calibration:
        logging.info("Calibration activated")
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
        logging.debug("Calibration data: delta_time = " + str(delta_time))
        logging.debug("Calibration delta_acc_w  = " + str(delta_acc_w))
        logging.debug("Calibration delta_acc_x  = " + str(delta_acc_x))
        logging.debug("Calibration delta_acc_y  = " + str(delta_acc_y))
        logging.debug("Calibration delta_acc_z  = " + str(delta_acc_z))
        logging.debug("Calibration delta_gyro_w = " + str(delta_gyro_w))
        logging.debug("Calibration delta_gyro_x = " + str(delta_gyro_x))
        logging.debug("Calibration delta_gyro_y = " + str(delta_gyro_y))
        logging.debug("Calibration delta_gyro_z = " + str(delta_gyro_z))
    else:
        logging.info("No calibration, using default values")
        delta_acc_w = 1.0     #   delta_acc_w = 0.00017
        delta_acc_x = 0.01    #   delta_acc_x = 0.0
        delta_acc_y = 0.005   #   delta_acc_y = -0.0085
        delta_acc_z = 0.005   #   delta_acc_z = -0.00065
        delta_gyro_w = 1.0    #   delta_gyro_w = -0.00023
        delta_gyro_x = 0.002  #   delta_gyro_x = 0.0207
        delta_gyro_y = 0.003  #   delta_gyro_y = -0.00269
        delta_gyro_z = 0.004  #   delta_gyro_z = 0.00446

    # Calculate Kalman constants
    P_init = np.eye(4) * 0.03  # Covariance initiale
    R_gyro = np.eye(4) * np.array([delta_gyro_w, delta_gyro_x, delta_gyro_y, delta_gyro_z])  # Incertitude gyroscope
    R_acc = np.eye(4) * np.array([delta_acc_w, delta_acc_x, delta_acc_y, delta_acc_z]) # Incertitude accéléromètre

    # calculate Kalman filter
    q = accelerometer_table.apply(lambda x: quaternion.kalman_filter_quaternion( P_init,
                                                                                 [x['Gyro w'], x['Gyro x'], x['Gyro y'], x['Gyro z']], 
                                                                                 [x['Acc w'], x['Acc x'], x['Acc y'], x['Acc z']], 
                                                                                 R_gyro, R_acc ), 
                                    axis=1)
    result['Kalman w'] = q.apply(lambda x: x[0])
    result['Kalman x'] = q.apply(lambda x: x[1])
    result['Kalman y'] = q.apply(lambda x: x[2])
    result['Kalman z'] = q.apply(lambda x: x[3])

    # Generate position from in Euler format
    euler = result.apply(lambda x: quaternion.quaternion_to_euler(np.array([x['Kalman w'], x['Kalman x'], x['Kalman y'], x['Kalman z']])), axis=1)
    result['Kalman Yaw'] = euler.apply(lambda x: x[0])
    result['Kalman Roll'] = euler.apply(lambda x: x[1])
    result['Kalman Pich'] = euler.apply(lambda x: x[2])

    return result

def low_pass_filter(accelerometer_table, window=10):
    # Smooth accelerometer data (low pass filter)
    return accelerometer_table.rolling(window=window, min_periods=1).mean()

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
    accelerometer_table.drop(accelerometer_table[['Acc w', 'Acc x', 'Acc y', 'Acc z', 'Gyro w', 'Gyro x', 'Gyro y', 'Gyro z', 'Kalman w', 'Kalman x', 'Kalman y', 'Kalman z']], axis=1, inplace=True)

    # Use time col as index
    accelerometer_table = accelerometer_table.set_index('Time')

    graph = accelerometer_table.plot()
    if display_graph: graph.show()
    html_file_name = json_file_name.split('.')[0] + '.html'
    graph.write_html(html_file_name)
    logging.info("Html file generated: " + html_file_name)

def compute(json_file_name, filtering_query=None, calibration=False, force=False):
    # Manage pickle file to save intermediate results from accelerometers and gyroscope
    pkl_file_name = json_file_name.split('.')[0] + '.pkl'
    if not os.path.exists(pkl_file_name) or force:
        # Read json file (exiftool output)
        data_df = read_json_file(json_file_name, filtering_query, force)

        # Compute accelerometer data using quaternions
        data_acc = compute_acc(data_df[['Acc X', 'Acc Y', 'Acc Z']])
        data_df = pd.concat([data_df, data_acc], axis=1)

        # Compute gyroscope data using quaternions
        data_gyro = compute_gyro(data_df[['Time','Rot X', 'Rot Y', 'Rot Z']])
        data_df = pd.concat([data_df, data_gyro], axis=1)

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
    data_kalman = compute_kalman_filter(data_df, calibration)
    data_df = pd.concat([data_df, data_kalman], axis=1)

    json_file_name = json_file_name.split('.')[0] + '_compute.json'
    save_file(data_df, json_file_name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Argument 1 is json file name to process
    json_file_name = sys.argv[1]

    # compute(json_file_name, 'Time > 80 and Time < 85')
    compute(json_file_name)

