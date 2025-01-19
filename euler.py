import pandas as pd
import numpy as np

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