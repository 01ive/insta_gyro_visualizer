import sys
import pandas as pd
import plotly.express as px
import numpy as np

pd.options.plotting.backend = "plotly"

process_accelerometer_data = False


''' Functions '''
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

def compute_data(csv_file_name):
    accelerometer_table = pd.read_csv(csv_file_name, sep='\t', index_col=0)

    # Calculate time starting to 0
    accelerometer_table['Time'] = accelerometer_table['Time'].apply(lambda x: x-accelerometer_table['Time'][0])
    accelerometer_table['Time delta'] = accelerometer_table['Time'] - accelerometer_table['Time'].shift()
    accelerometer_table['Time delta'] = accelerometer_table['Time delta'].shift(-1, fill_value=0)

    # Low pass filter on Rotation sensor
    accelerometer_table['Rot X'] = low_pass(accelerometer_table['Rot X'], 0.99)
    accelerometer_table['Rot Y'] = low_pass(accelerometer_table['Rot Y'], 0.99)
    accelerometer_table['Rot Z'] = low_pass(accelerometer_table['Rot Z'], 0.99)

    # Calulate rotation from rotation speed sensor
    accelerometer_table['Rotation X'] = accelerometer_table['Rot X'] * accelerometer_table['Time delta'] # * 180 / np.pi
    accelerometer_table['Rotation Y'] = accelerometer_table['Rot Y'] * accelerometer_table['Time delta'] # * 180 / np.pi
    accelerometer_table['Rotation Z'] = accelerometer_table['Rot Z'] * accelerometer_table['Time delta'] # * 180 / np.pi
    accelerometer_table['Rotation X'] = accelerometer_table['Rotation X'].cumsum()
    accelerometer_table['Rotation Y'] = accelerometer_table['Rotation Y'].cumsum()
    accelerometer_table['Rotation Z'] = accelerometer_table['Rotation Z'].cumsum()

    # Remove bias
    accelerometer_table['Rotation X'] = remove_bias(accelerometer_table['Rotation X'])
    accelerometer_table['Rotation Y'] = remove_bias(accelerometer_table['Rotation Y'])
    accelerometer_table['Rotation Z'] = remove_bias(accelerometer_table['Rotation Z'])

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
        accelerometer_table['ACC rotation Z angle 3D'] = np.arctan2(accelerometer_table['Acc Y'], np.sqrt(
                                            np.power(accelerometer_table['Acc X'], 2) + 
                                            np.power(accelerometer_table['Acc Z'], 2) )  )

    # Use time col as index
    accelerometer_table = accelerometer_table.set_index('Time')
    # Display graph
    graph = accelerometer_table.plot()
    graph.show()
    graph.write_html(csv_file_name.split('.')[0] + '.html')

    # Generate json file
    accelerometer_table.filter(['Rotation X', 'Rotation Y', 'Rotation Z'], axis=1).reset_index().to_json(csv_file_name.split('.')[0] + '.json', orient='records', indent=2)


if __name__ == "__main__":
    csv_file_name = sys.argv[1]

    compute_data(csv_file_name)