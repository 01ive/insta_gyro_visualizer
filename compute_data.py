import sys
import pandas as pd
import plotly.express as px
import numpy as np
import logging

from progress.bar import Bar

pd.options.plotting.backend = "plotly"

process_accelerometer_data = False

rotation_low_pass = False
acceleration_low_pass = False
rotation_bias_processing = False

Kalman_filter_processing = False

''' Functions '''
def low_pass(data, filter):
    progress_bar = Bar("Low pass " + data.name, max=len(data))
    for i in range(1, len(data)):
        data[i] = filter*data[i-1] + (1-filter)*data[i]
        progress_bar.next()
    progress_bar.finish()
    return data

def remove_bias(data):
    bias_filter = np.pi / 13
    medium_last = data[0]
    bias = 0

    progress_bar = Bar("Remove bias " + data.name, max=len(data))

    for i in range(1, len(data)):
        if(np.abs(data[i] - medium_last) < bias_filter):
            bias = np.abs(medium_last)
            medium_last = 0.99*medium_last + 0.01*data[i]
        else:
            pass
        data[i] = data[i] - np.sign(data[i]) * bias
        progress_bar.next()
    
    progress_bar.finish()
    return data

def Kalman_filter(data):
    # Initialisation des variables
    theta_est = 0.0  # Angle estimé initial
    P = 1.0  # Covariance initiale
    Q = 0.001  # Bruit du processus (modèle dynamique)
    R = 0.1   # Bruit de mesure (capteur)

    accel_data = data['ACC rotation Y angle 2D']
    gyro_data = data['Rot Y']
    dt = data['Time delta']
    data['Kalman filter Y'] = 0.0

    # Filtre de Kalman
    for i in data.index:
        # Étape de prédiction
        theta_pred = theta_est + gyro_data[i] * dt[i]
        P_pred = P + Q
        
        # Calcul du gain de Kalman
        K = P_pred / (P_pred + R)
        
        # Mise à jour de l'estimation
        theta_est = theta_pred + K * (accel_data[i] - theta_pred)
        P = (1 - K) * P_pred

        data.loc[i, 'Kalman filter Y'] = theta_est

    return data


def compute_data(csv_file_name):
    logging.info("Start computing data from file: " + csv_file_name)

    accelerometer_table = pd.read_csv(csv_file_name, sep='\t', index_col=0)

    # Calculate time starting to 0
    accelerometer_table['Time'] = accelerometer_table['Time'].apply(lambda x: x-accelerometer_table['Time'][0])
    accelerometer_table['Time delta'] = accelerometer_table['Time'] - accelerometer_table['Time'].shift(fill_value=0)

    if acceleration_low_pass:
        logging.info("Low pass filter calculation")
        accelerometer_table['Acc X'] = low_pass(accelerometer_table['Acc X'], 0.99)
        accelerometer_table['Acc Y'] = low_pass(accelerometer_table['Acc Y'], 0.99)
        accelerometer_table['Acc Z'] = low_pass(accelerometer_table['Acc Z'], 0.99)

    # Low pass filter on Rotation sensor
    if rotation_low_pass:
        logging.info("Low pass filter calculation")
        accelerometer_table['Rot X'] = low_pass(accelerometer_table['Rot X'], 0.99)
        accelerometer_table['Rot Y'] = low_pass(accelerometer_table['Rot Y'], 0.99)
        accelerometer_table['Rot Z'] = low_pass(accelerometer_table['Rot Z'], 0.99)

    # Calulate rotation from rotation speed sensor
    accelerometer_table['Rotation X'] = accelerometer_table['Rot X'] * accelerometer_table['Time delta']
    accelerometer_table['Rotation Y'] = accelerometer_table['Rot Y'] * accelerometer_table['Time delta']
    accelerometer_table['Rotation Z'] = accelerometer_table['Rot Z'] * accelerometer_table['Time delta']

    # accelerometer_table['Rotation X'] = accelerometer_table['Rotation X'].apply(lambda x: 0 if np.abs(x) <= 0.001 else x)
    # accelerometer_table['Rotation Y'] = accelerometer_table['Rotation Y'].apply(lambda x: 0 if np.abs(x) <= 0.001 else x)
    # accelerometer_table['Rotation Z'] = accelerometer_table['Rotation Z'].apply(lambda x: 0 if np.abs(x) <= 0.001 else x)


    # window = 10
    # level = 0.001
    # accelerometer_table['Rotation X filtered'] = accelerometer_table['Rotation X'].rolling(window=window, min_periods=1).mean()
    # accelerometer_table['Rotation X filtered'] = np.abs(accelerometer_table['Rotation X filtered']) > level 
    # accelerometer_table['Rotation X filtered'] = accelerometer_table['Rotation X'] * accelerometer_table['Rotation X filtered']
    # accelerometer_table['Rotation X'] = accelerometer_table['Rotation X filtered'].cumsum()

    # accelerometer_table['Rotation Y filtered'] = accelerometer_table['Rotation Y'].rolling(window=window, min_periods=1).mean()
    # accelerometer_table['Rotation Y filtered'] = np.abs(accelerometer_table['Rotation Y filtered']) > level 
    # accelerometer_table['Rotation Y filtered'] = accelerometer_table['Rotation Y'] * accelerometer_table['Rotation Y filtered']
    # accelerometer_table['Rotation Y'] = accelerometer_table['Rotation Y filtered'].cumsum()

    # accelerometer_table['Rotation Z filtered'] = accelerometer_table['Rotation Z'].rolling(window=window, min_periods=1).mean()
    # accelerometer_table['Rotation Z filtered'] = np.abs(accelerometer_table['Rotation Z filtered']) > level 
    # accelerometer_table['Rotation Z filtered'] = accelerometer_table['Rotation Z'] * accelerometer_table['Rotation Z filtered']
    # accelerometer_table['Rotation Z'] = accelerometer_table['Rotation Z filtered'].cumsum()

    accelerometer_table['Rotation X'] = accelerometer_table['Rotation X'].cumsum()
    accelerometer_table['Rotation Y'] = accelerometer_table['Rotation Y'].cumsum()
    accelerometer_table['Rotation Z'] = accelerometer_table['Rotation Z'].cumsum()

    # Remove bias
    if rotation_bias_processing:
        logging.info("Removing bias")
        remove_bias(accelerometer_table['Rotation X'])
        remove_bias(accelerometer_table['Rotation Y'])
        remove_bias(accelerometer_table['Rotation Z'])

    # Rotation angle in radians between -pi and pi
    accelerometer_table['Rotation X angle'] = accelerometer_table['Rotation X'].apply(lambda x: x if np.abs(x) <= np.pi else x - np.sign(x) * 2*np.pi)
    accelerometer_table['Rotation Y angle'] = accelerometer_table['Rotation Y'].apply(lambda x: x if np.abs(x) <= np.pi else x - np.sign(x) * 2*np.pi)
    accelerometer_table['Rotation Z angle'] = accelerometer_table['Rotation Z'].apply(lambda x: x if np.abs(x) <= np.pi else x - np.sign(x) * 2*np.pi)

    if process_accelerometer_data:
        # Calculate rotation angle from accelerator sensor
        accelerometer_table['ACC rotation X angle 2D'] = np.arctan2(accelerometer_table['Acc Y'], accelerometer_table['Acc Z'])
        accelerometer_table['ACC rotation Y angle 2D'] = np.arctan2(accelerometer_table['Acc Z'], accelerometer_table['Acc X'])
        accelerometer_table['ACC rotation Z angle 2D'] = np.arctan2(accelerometer_table['Acc X'], accelerometer_table['Acc Y'])

        accelerometer_table['ACC rotation X angle 3D'] = np.arctan2(accelerometer_table['Acc X'], np.sqrt(
                                            np.power(accelerometer_table['Acc Y'], 2) + 
                                            np.power(accelerometer_table['Acc Z'], 2) )  )
        accelerometer_table['ACC rotation Y angle 3D'] = np.arctan2(accelerometer_table['Acc Z'], np.sqrt(
                                            np.power(accelerometer_table['Acc Y'], 2) + 
                                            np.power(accelerometer_table['Acc X'], 2) )  )
        accelerometer_table['ACC rotation Z angle 3D'] = np.arctan2(-accelerometer_table['Acc Y'], np.sqrt(
                                            np.power(accelerometer_table['Acc X'], 2) + 
                                            np.power(accelerometer_table['Acc Z'], 2) )  )

    if Kalman_filter_processing:
        logging.info("Kalman filter calculation")
        accelerometer_table = Kalman_filter(accelerometer_table)

    # Use time col as index
    accelerometer_table = accelerometer_table.set_index('Time')
    # Display graph
    graph = accelerometer_table.plot()
    graph.show()
    html_file_name = csv_file_name.split('.')[0] + '.html'
    graph.write_html(html_file_name)
    logging.info("Html file generated: " + html_file_name)

    # Generate json file
    json_file_name = csv_file_name.split('.')[0] + '.json'
    accelerometer_table.filter(['Rotation X', 'Rotation Y', 'Rotation Z'], axis=1).reset_index().to_json(json_file_name, orient='records', indent=2)
    logging.info("Json file generated: " + json_file_name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    csv_file_name = sys.argv[1]

    compute_data(csv_file_name)